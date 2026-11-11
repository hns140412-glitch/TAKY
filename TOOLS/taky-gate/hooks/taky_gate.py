#!/usr/bin/env python3
"""TAKY guide: PreToolUse hook that steers Claude onto the right path instead of stopping the USER.

Design (v0.2, after Taky's 2026-11-07 review "유도, 차단 아님 / USER != DEBUGGER"):

  pass     nothing risky                                   -> no output, normal permissions
  granted  risky, but the USER granted this kind of work    -> allowed silently, use is logged
           once for this work unit (taky_grant.py)
  rewrite  a safer form of the same intent exists          -> updatedInput + additionalContext,
           (netlify site from routes, stash before reset,      no prompt to anyone
           rm -> move to .taky/trash)
  guide    no safe rewrite and no grant                    -> deny with the correct route, sent to
                                                              CLAUDE (not a USER prompt). Claude
                                                              batches what it needs into ONE ask.

This hook never returns "ask", so it never opens an approval dialog by itself.
After the same command has been guided twice, the guidance says to stop retrying and
report (savvy-flow: "Cap at two return rounds per task; after that, re-plan or ask").

Standard library only. No network.
"""
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys

PAID_HOSTS = ("api.openai.com", "api.anthropic.com", "api.elevenlabs.io", "generativelanguage.googleapis.com",
              "api.replicate.com", "api.stability.ai", "api.runwayml.com", "api.fal.ai")

MCP_RULES = [
    (re.compile(r"^mcp__github__merge_pull_request$"), "merge", "PR 병합"),
    (re.compile(r"^mcp__github__enable_pr_auto_merge$"), "merge", "자동 병합 켜기"),
    (re.compile(r"^mcp__github__(push_files|create_or_update_file|delete_file)$"), "push", "원격 저장소 직접 쓰기"),
    (re.compile(r"^mcp__ElevenLabs__creative_(generate_\w+|edit_image|design_voice|run_flow_nodes|generate_in_flow|transcribe_audio)$"),
     "paid", "ElevenLabs 크레딧 사용"),
]

GATE = {"push": "ROUTE", "merge": "ROUTE", "deploy": "ROUTE", "prod": "ROUTE", "paid": "COST",
        "destroy": "KEY"}

HOW_TO_GRANT = ("필요한 승인을 모아서 USER에게 한 번에 요청한다. USER가 '승인 push,deploy 2h'처럼 한 줄로 답하면 "
                "그 작업 단위 동안 같은 종류는 다시 묻지 않는다.")


def taky_home():
    """Shared state lives outside the repos so it never shows up in git status."""
    return os.environ.get("TAKY_HOME") or os.path.join(os.path.expanduser("~"), ".taky")


def run(args, cwd, timeout=5):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""


def root_of(event):
    return os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def now():
    return dt.datetime.now(dt.timezone.utc)


def active_grants(root):
    out = []
    for g in load_json(os.path.join(taky_home(), "grants.json"), {"grants": []}).get("grants", []):
        try:
            if dt.datetime.fromisoformat(g["expires"]) > now():
                out.append(g)
        except Exception:
            continue
    return out


def granted(root, kind):
    return next((g for g in active_grants(root) if kind in g.get("kinds", []) or "all" in g.get("kinds", [])), None)


def log(root, rec):
    try:
        d = os.path.join(taky_home(), "delta")
        os.makedirs(d, exist_ok=True)
        rec["project"] = root
        rec["ts"] = now().strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(os.path.join(d, now().strftime("%Y%m%d") + ".jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def guide_count(root, command):
    """How many times this exact command was already guided (bounded retry)."""
    path = os.path.join(taky_home(), "guided.json")
    data = load_json(path, {})
    key = hashlib.sha1(command.strip().encode()).hexdigest()[:16]
    data[key] = data.get(key, 0) + 1
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass
    return data[key]


HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def mask_heredocs(command):
    """Heredoc bodies are file content, not commands: blank them out (same length, newlines kept) so
    'cat > run.sh <<EOF ... rm -rf x ... EOF' is neither refused nor rewritten. Offsets stay valid."""
    out, i = command, 0
    while True:
        m = HEREDOC.search(out, i)
        if not m:
            return out
        start = out.find("\n", m.end())
        if start < 0:
            return out
        end = re.compile(r"^\t*" + re.escape(m.group(2)) + r"[ \t]*$", re.M).search(out, start + 1)
        stop = end.start() if end else len(out)
        out = out[:start] + re.sub(r"[^\n]", " ", out[start:stop]) + out[stop:]
        i = (end.end() if end else len(out))


def segments(command):
    """(words, cd-target, raw text) per simple command. raw is kept so a rewrite can replace
    exactly that piece of a chained command and leave the rest (and shell variables) untouched."""
    out, move = [], None
    for raw in re.split(r"&&|\|\||;|\||\n", command):
        try:
            words = shlex.split(raw.strip())
        except ValueError:
            words = raw.strip().split()
        while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
            words.pop(0)  # leading VAR=value
        while words and words[0] in ("sudo", "command", "exec", "env", "nohup", "time"):
            words.pop(0)
        if not words:
            continue
        if words[0] in ("cd", "pushd") and len(words) > 1:
            move = words[1]
            continue
        out.append((words, move, raw.strip()))
    return out


def resolve(cwd, move):
    if not move:
        return cwd
    p = os.path.expanduser(move)
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(cwd, p))


def dirty(cwd):
    return [l for l in run(["git", "status", "--porcelain"], cwd).splitlines() if l.strip()]


def analyse(words, cwd, root):
    """One finding dict or None. Keys: kind, label, action(rewrite|guide), new(words), why, route."""
    head = os.path.basename(words[0]).lstrip("\\")
    args = words[1:]
    if head == "git":
        i, gdir = 0, cwd
        while i < len(args) and args[i].startswith("-"):
            if args[i] == "-C" and i + 1 < len(args):
                gdir = resolve(cwd, args[i + 1]); i += 2
            elif args[i] == "-c":
                i += 2
            else:
                i += 1
        sub, rest = (args[i] if i < len(args) else ""), args[i + 1:]
        if sub == "push":
            force = any(a in ("-f", "--force") or a.startswith("--force") or a.startswith("+") for a in rest)
            branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], gdir)
            pos = [a for a in rest if not a.startswith("-")]
            to_main = any(a.split(":")[-1] in ("main", "master") for a in pos[1:]) or \
                (branch in ("main", "master") and len(pos) <= 1)
            if to_main or force:
                return {"kind": "prod" if to_main else "destroy", "label": "main 직접 push" if to_main else "강제 push",
                        "action": "guide",
                        "route": "작업 브랜치에 push하고 draft PR을 연다. main 반영은 PR 병합으로만 한다." if to_main
                        else "강제 push 대신 새 커밋으로 되돌리거나(git revert) 새 브랜치로 push한다."}
            # USER standing rule (CURRENT, 2026-11-05): git push is always allowed except main, force,
            # and pushes that trigger a Netlify deploy. Branch pushes pass; a Netlify-linked repo gets a note.
            ahead = run(["git", "log", "--oneline", "HEAD", "--not", "--remotes"], gdir).splitlines()
            top = run(["git", "rev-parse", "--show-toplevel"], gdir) or gdir
            linked = os.path.exists(os.path.join(top, "netlify.toml")) or os.path.isdir(os.path.join(top, ".netlify"))
            note = f"[TAKY] git push ({branch}, 새 커밋 {len(ahead)}개): USER 상시 허용 범위(작업 브랜치)."
            if linked:
                note += " 이 저장소는 Netlify에 연결돼 있다. 브랜치 배포가 켜져 있으면 이 push가 배포를 만든다. 배포가 생기면 보고에 적는다."
            return {"kind": "push", "label": "git push", "action": "note", "note": note}
        if sub == "merge" and run(["git", "rev-parse", "--abbrev-ref", "HEAD"], gdir) in ("main", "master"):
            return {"kind": "merge", "label": "main에서 git merge", "action": "guide",
                    "route": "main 반영은 PR로만 한다."}
        discard = (sub == "reset" and "--hard" in rest) or \
                  (sub in ("checkout", "restore") and ("." in rest) and "--staged" not in rest)
        if discard and dirty(gdir):
            stamp = now().strftime("%Y%m%dT%H%M%SZ")
            pre = ["git"] + (["-C", gdir] if gdir != cwd else []) + ["stash", "push", "-u", "-m", f"taky-guard {stamp}"]
            return {"kind": "destroy", "label": f"git {sub} (미커밋 변경 {len(dirty(gdir))}개)", "action": "rewrite",
                    "prefix": pre,
                    "why": f"미커밋 변경을 먼저 stash('taky-guard {stamp}')에 보관한 뒤 실행했다. 복구: git stash list → git stash apply."}
        if sub == "clean" and any(a.startswith("-") and "f" in a for a in rest) and \
                run(["git", "clean", "-n"] + [a for a in rest if a.startswith("-") and a not in ("-f", "--force")], gdir):
            return {"kind": "destroy", "label": "git clean (추적 안 된 파일 삭제)", "action": "guide",
                    "route": "지울 대상을 git clean -n으로 확인하고, 필요하면 .taky/trash로 옮긴다(mv). 원본 삭제는 하지 않는다."}
        if sub == "branch" and "-D" in rest:
            # USER card 2026-11-05: deleting a branch that has a backup proceeds without asking.
            # The backup here is the tip SHA, recorded before the delete (recoverable with git branch <name> <sha>).
            names = [a for a in rest if not a.startswith("-")]
            shas = {n: run(["git", "rev-parse", n], gdir) for n in names}
            return {"kind": "destroy", "label": "git branch -D", "action": "note", "backup": shas,
                    "note": "[TAKY] 브랜치 삭제 전 끝 SHA를 ~/.taky/delta에 백업했다: " +
                            ", ".join(f"{n}={v[:12]}" for n, v in shas.items()) + ". 복구: git branch <이름> <SHA>"}
        return None
    if head == "gh" and args[:2] == ["pr", "merge"]:
        return {"kind": "merge", "label": "gh pr merge", "action": "guide", "route": "PR 병합은 승인 범위 'merge'다."}
    if head == "gh" and args[:2] == ["repo", "delete"]:
        return {"kind": "destroy", "label": "gh repo delete", "action": "guide", "route": "저장소 삭제는 USER가 직접 한다."}
    if head in ("netlify", "ntl") and "deploy" in args:
        prod = "--prod" in args or "--prod-if-unlocked" in args
        has_site = any(w in ("--site", "-s") or w.startswith("--site=") for w in args)
        if not has_site:
            routes = load_json(os.path.join(taky_home(), "routes.json"), {}).get("netlify", {})
            site = next((sid for d, sid in sorted(routes.items(), key=lambda kv: -len(kv[0]))
                         if os.path.normpath(cwd).endswith(os.path.normpath(d)) or os.path.normpath(cwd) == os.path.normpath(os.path.join(root, d))), None)
            if site:
                return {"kind": "prod" if prod else "deploy", "label": "netlify deploy", "action": "rewrite",
                        "add": ["--site", site],
                        "why": f".taky/routes.json에서 이 폴더의 사이트({site})를 찾아 --site를 붙였다. .netlify 링크는 믿지 않는다."}
            return {"kind": "deploy", "label": "netlify deploy (--site 없음)", "action": "guide", "hard": True,
                    "route": "폴더의 .netlify 링크는 다른 사이트를 가리킬 수 있다(2026-11-07 오배포). "
                             "--site <id>를 붙이거나 .taky/routes.json의 netlify에 '폴더: 사이트ID'를 등록한다."}
        return {"kind": "prod" if prod else "deploy", "label": "netlify 운영 배포" if prod else "netlify draft 배포",
                "action": "guide", "route": f"배포는 승인 범위 '{'prod' if prod else 'deploy'}'다."}
    if head in ("vercel", "firebase", "wrangler") or (head == "npm" and args[:1] == ["publish"]):
        if head != "firebase" or "deploy" in args:
            return {"kind": "prod", "label": f"{head} 배포/게시", "action": "guide", "route": "배포는 승인 범위 'prod'다."}
    if head == "rm" and any(a.startswith("-") and "r" in a.lower() for a in args):
        targets = [a for a in args if not a.startswith("-")]
        paths = [resolve(cwd, t) for t in targets]
        inside = all(p.startswith(os.path.normpath(root) + os.sep) for p in paths) and paths
        if not inside or any(t in ("*", ".", "..") for t in targets):
            return {"kind": "destroy", "label": "rm -r (프로젝트 밖 또는 광범위)", "action": "guide", "hard": True,
                    "route": "프로젝트 폴더 안의 구체적인 경로만 지운다. 넓은 삭제는 USER가 직접 한다."}
        trash = os.path.join(taky_home(), "trash", now().strftime("%Y%m%dT%H%M%SZ"))
        return {"kind": "destroy", "label": "rm -r", "action": "rewrite", "trash": trash,
                "why": f"삭제 대신 {trash} 로 옮겼다. 확인 후 비우는 것은 USER 몫이다."}
    joined = " ".join(words)
    if head in ("curl", "wget", "http", "https", "xh") and any(h in joined for h in PAID_HOSTS):
        host = next(h for h in PAID_HOSTS if h in joined)
        return {"kind": "paid", "label": f"유료 API ({host})", "action": "guide",
                "route": "무료·로컬 경로가 있으면 그것을 쓴다. 없으면 예상 비용과 함께 승인 범위 'paid'로 묶는다."}
    if head == "codex" and args[:1] == ["exec"]:
        # USER card 2026-11-11: Codex verification calls are standing-approved. codex exec defaults to a
        # read-only sandbox; a write-capable run is implementation work and stays in the 'paid' scope.
        flat = " ".join(args)
        writes = ("--full-auto" in args or "--dangerously-bypass-approvals-and-sandbox" in args or
                  re.search(r"(?:-s|--sandbox)[ =](?:workspace-write|danger-full-access)", flat) or
                  re.search(r"sandbox_mode\s*=\s*['\"]?(?:workspace-write|danger-full-access)", flat))
        if not writes:
            return {"kind": "verify", "label": "codex exec (읽기 전용 검증)", "action": "note",
                    "note": "[TAKY] Codex 검증 호출(읽기 전용): USER 상시 허용(2026-11-11). 사용 기록만 남긴다."}
        return {"kind": "paid", "label": "codex exec (쓰기 가능 실행)", "action": "guide",
                "route": "쓰기 가능한 Codex 실행은 구현 작업이라 승인 범위 'paid'다. 검증만이면 읽기 전용(-s read-only)으로 돌린다."}
    if head == "claude" and ("-p" in words or "--print" in words):
        return {"kind": "paid", "label": f"{head} 사용량 호출", "action": "guide", "route": "사용량 소모는 승인 범위 'paid'다."}
    return None


RM_RAW = re.compile(r"^(?:(?:sudo|command|exec|env|nohup|time)\s+)*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*\S*rm((?:\s+-\S*)+)\s+(.+)$", re.S)


def trash_form(raw, trash):
    """Same targets, moved instead of deleted. Targets stay unquoted so $VAR and globs expand exactly
    as they would have for rm. Missing targets are skipped (rm -f semantics), one fresh numbered folder per
    target avoids name clashes (also with an earlier move in the same second), and the block always succeeds like rm -rf does."""
    m = RM_RAW.match(raw)
    targets = m.group(2) if m else ""
    t = shlex.quote(trash)
    return (f"{{ _taky_i=0; for _taky_p in {targets}; do "
            f"if [ -e \"$_taky_p\" ] || [ -L \"$_taky_p\" ]; then _taky_i=$((_taky_i+1)); "
            f"while [ -e {t}/$_taky_i ]; do _taky_i=$((_taky_i+1)); done; "
            f"mkdir -p {t}/$_taky_i && mv -- \"$_taky_p\" {t}/$_taky_i/; fi; done; true; }}")


def respond(decision=None, reason=None, updated=None, context=None):
    hso = {"hookEventName": "PreToolUse"}
    if decision:
        hso["permissionDecision"] = decision
    if reason:
        hso["permissionDecisionReason"] = reason
    if updated is not None:
        hso["updatedInput"] = updated
    if context:
        hso["additionalContext"] = context
    return {"hookSpecificOutput": hso}


def decide(event):
    tool, root = event.get("tool_name", ""), root_of(event)
    cwd = event.get("cwd") or root
    ti = event.get("tool_input") or {}
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        target = str(ti.get("file_path") or ti.get("notebook_path") or "")
        if os.path.basename(target) == "grants.json":
            return respond("deny", "[TAKY KEY] 승인 기록(~/.taky/grants.json)은 USER가 입력한 '승인 ...' 한 줄로만 생긴다. "
                                   "Claude는 이 파일을 쓰지 않는다. 필요한 승인을 USER에게 한 번에 요청한다.")
        return None
    if tool != "Bash":
        for rx, kind, label in MCP_RULES:
            if rx.match(tool):
                g = granted(root, kind)
                if g:
                    log(root, {"kind": "grant_use", "grant": g.get("id"), "tool": tool})
                    return respond(context=f"[TAKY] '{kind}' 승인({g.get('id')}) 범위로 진행: {label}")
                return respond("deny", f"[TAKY {GATE[kind]} 안내] {label}: 승인 범위 '{kind}'가 없다. {HOW_TO_GRANT}")
        return None

    cmd = str(ti.get("command", ""))
    if "grants.json" in cmd and re.search(r">|\btee\b|\bmv\b|\bcp\b|\bsed\s+-i|\bpython|\bnode", cmd):
        return respond("deny", "[TAKY KEY] 승인 기록(~/.taky/grants.json)은 USER의 '승인 ...' 입력으로만 바뀐다.")
    masked = mask_heredocs(cmd)
    segs = segments(masked)
    findings = [(f, w, m, raw) for w, m, raw in segs if (f := analyse(w, resolve(cwd, m), root))]
    if not findings:
        return None
    # rm -r inside a chained command: replace only that piece with the trash form, keep the rest.
    # (Before: the whole chain was refused with "run it separately", 7 of 9 RENDER observe events, 2026-11-11.)
    moved, spots, pos = [], [], 0
    for f, words, move, raw in findings:
        at = masked.find(raw, pos)
        if at < 0:
            continue
        pos = at + len(raw)
        if f["action"] == "rewrite" and "trash" in f and RM_RAW.match(raw):
            spots.append((at, raw, trash_form(raw, f["trash"])))
            moved.append(f)
    new_cmd = cmd
    for at, raw, rep in reversed(spots):
        new_cmd = new_cmd[:at] + rep + new_cmd[at + len(raw):]
    findings = [x for x in findings if x[0] not in moved]
    if moved and not any(f["action"] != "note" for f, *_ in findings):
        notes = []
        for f, *_ in findings:
            log(root, {"kind": "note", "command": cmd[:200]})
            notes.append(f["note"])
        log(root, {"kind": "rewrite", "from": cmd[:200], "to": new_cmd[:300]})
        return respond("allow", f"[TAKY 유도] rm -r {len(moved)}곳 → 휴지통 이동으로 바꿔 실행", {**ti, "command": new_cmd},
                       "\n".join([f"[TAKY] {moved[0]['why']}"] + notes))
    if moved:
        cmd = new_cmd
    contexts, guides = [], []
    single = len(segs) == 1
    for f, words, move, _raw in findings:
        if f["action"] == "note":
            log(root, {"kind": "note", "command": cmd[:200], **({"backup": f["backup"]} if "backup" in f else {})})
            contexts.append(f["note"])
            continue
        g = None if f.get("hard") else granted(root, f["kind"])
        if g and f["action"] == "guide":
            log(root, {"kind": "grant_use", "grant": g.get("id"), "command": cmd[:200]})
            contexts.append(f"[TAKY] '{f['kind']}' 승인({g.get('id')}) 범위로 진행: {f['label']}")
            continue
        if f["action"] == "rewrite" and single:
            if "prefix" in f:
                new = " ".join(shlex.quote(x) for x in f["prefix"]) + " && " + cmd
            else:
                new = cmd + " " + " ".join(shlex.quote(x) for x in f["add"])
            if f["kind"] in ("deploy", "prod") and not granted(root, f["kind"]):
                guides.append((f, f"{f['why']} 고친 명령: {new} · 배포 자체는 승인 범위 '{f['kind']}'가 필요하다."))
                continue
            log(root, {"kind": "rewrite", "from": cmd[:200], "to": new[:300]})
            return respond("allow", f"[TAKY 유도] {f['label']} → 안전한 형태로 바꿔 실행", {**ti, "command": new},
                           f"[TAKY] {f['why']}")
        if f["action"] == "rewrite":
            guides.append((f, "여러 단계 명령이라 아직 실행하지 않았다. 이 단계만 따로 실행하면 TAKY가 안전한 형태로 바꿔 실행한다."))
            continue
        guides.append((f, f["route"]))
    if not guides:
        if moved:
            log(root, {"kind": "rewrite", "from": ti.get("command", "")[:200], "to": cmd[:300]})
            return respond("allow", f"[TAKY 유도] rm -r {len(moved)}곳 → 휴지통 이동으로 바꿔 실행", {**ti, "command": cmd},
                           "\n".join([f"[TAKY] {moved[0]['why']}"] + contexts))
        return respond(context="\n".join(contexts)) if contexts else None
    n = guide_count(root, cmd)
    lines = [f"[TAKY {GATE[f['kind']]} 안내 · {f['kind']}] {f['label']}: {r}" for f, r in guides]
    if any(not f.get("hard") for f, _ in guides):
        lines.append(HOW_TO_GRANT)
    if n > 2:
        lines.append(f"이 명령은 이미 {n - 1}번 안내됐다. 더 시도하지 말고 지금까지 한 일, 막힌 이유, 선택지를 USER에게 한 번에 보고한다.")
    return respond("deny", "\n".join(lines))


def mode():
    """observe (default): only record what the guide would do. guide: act on it.
    Set with the env var TAKY_GUIDE_MODE or the file ~/.taky/guide-mode (one word)."""
    m = os.environ.get("TAKY_GUIDE_MODE", "")
    if not m:
        try:
            m = open(os.path.join(taky_home(), "guide-mode"), encoding="utf-8").read()
        except Exception:
            m = ""
    return "guide" if m.strip().lower() == "guide" else "observe"


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    try:
        out = decide(event)
    except Exception:
        return 0  # a broken guide must never break the session; normal permissions still apply
    if not out:
        return 0
    if mode() == "observe":
        h = out["hookSpecificOutput"]
        log(root_of(event), {"kind": "observe", "tool": event.get("tool_name"),
                             "command": str((event.get("tool_input") or {}).get("command", ""))[:200],
                             "would": h.get("permissionDecision") or "context",
                             "rewrite": (h.get("updatedInput") or {}).get("command"),
                             "reason": (h.get("permissionDecisionReason") or h.get("additionalContext") or "")[:300]})
        return 0
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
