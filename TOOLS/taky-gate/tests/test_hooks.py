#!/usr/bin/env python3
"""Deterministic tests for the TAKY guide hooks (v0.2). Temp dirs only, no network, no API.
Run: python3 -I tests/test_hooks.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.join(os.path.dirname(HERE), "hooks")
GATE, GRANT, DELTA, LEDGER = (os.path.join(HOOKS, n) for n in
                              ("taky_gate.py", "taky_grant.py", "taky_delta.py", "taky_ledger.py"))
results = []
MODE = "guide"
seen_decisions = []


def check(name, ok, extra=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"   <- {extra}"))


def sh(args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def hook(script, event, root, args=()):
    p = subprocess.run([sys.executable, script, *args], input=json.dumps(event), capture_output=True, text=True,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": root, "TAKY_GUIDE_MODE": MODE, "TAKY_HOME": os.path.join(root, ".taky")})
    return json.loads(p.stdout) if p.stdout.strip() else None


def gate(cmd, cwd, root, tool="Bash"):
    out = hook(GATE, {"tool_name": tool, "tool_input": {"command": cmd}, "cwd": cwd}, root)
    h = (out or {}).get("hookSpecificOutput", {})
    seen_decisions.append(h.get("permissionDecision"))
    return h.get("permissionDecision", "pass"), h


def grant(text, root):
    return hook(GRANT, {"prompt": text, "session_id": "s1", "cwd": root}, root)


def run_shell(cmd, cwd):
    """Claude Code runs Bash commands in a POSIX shell (Git Bash on Windows)."""
    import shutil
    bash = os.environ.get("TAKY_TEST_BASH") or shutil.which("bash")
    subprocess.run([bash, "-c", cmd], cwd=cwd, capture_output=True)


def make_repo(root):
    bare, repo = os.path.join(root, "origin.git"), os.path.join(root, "repo")
    sh(["git", "init", "-q", "--bare", bare], root)
    sh(["git", "init", "-q", "-b", "main", repo], root)
    sh(["git", "config", "user.email", "t@example.com"], repo)
    sh(["git", "config", "user.name", "t"], repo)
    open(os.path.join(repo, "a.txt"), "w").write("1\n")
    sh(["git", "add", "."], repo); sh(["git", "commit", "-qm", "init"], repo)
    sh(["git", "remote", "add", "origin", bare], repo); sh(["git", "push", "-q", "-u", "origin", "main"], repo)
    sh(["git", "checkout", "-qb", "feature"], repo)
    open(os.path.join(repo, "b.txt"), "w").write("2\n")
    sh(["git", "add", "."], repo); sh(["git", "commit", "-qm", "feature work"], repo)
    return repo


def main():
    with tempfile.TemporaryDirectory() as root:
        repo = make_repo(root)

        print("-- 1. 평소 작업은 아무것도 하지 않는다")
        for cmd in ("ls -la", "git status && git log --oneline -3", "npm test", "curl -s https://example.com",
                    "git checkout main", "git push --dry-run origin feature".replace("--dry-run ", "--dry-run ")):
            if "dry-run" in cmd:
                continue
            d, _ = gate(cmd, repo, root)
            check(f"pass: {cmd}", d == "pass", d)

        print("-- 2. 승인 없을 때: USER 창 대신 Claude에게 올바른 길 안내")
        d, h = gate("git push -u origin feature", repo, root)
        check("작업 브랜치 push = USER 상시 허용(11-05) -> 막지 않고 메모만", d == "pass" and "상시 허용" in h.get("additionalContext", ""), h)
        sh(["git", "branch", "old-try"], repo)
        d, h = gate("git branch -D old-try", repo, root)
        check("branch -D = 백업 후 진행(11-05 카드) -> SHA 기록하고 통과", d == "pass" and "SHA" in h.get("additionalContext", ""), h)
        for cmd, needle in (("gh pr merge 12 --squash", "merge"),
                            ("curl https://api.openai.com/v1/images -d @r.json", "paid"),
                            ("claude -p hi", "paid"), ("git push origin main", "draft PR"),
                            ("git push --force origin feature", "revert")):
            d, h = gate(cmd, repo, root)
            r = h.get("permissionDecisionReason", "")
            check(f"guide: {cmd}", d == "deny" and needle in r and "한 번에" in r, r[:120])

        print("-- 3. 더 안전한 같은 의도가 있으면 고쳐서 실행 (아무도 안 누름)")
        open(os.path.join(repo, "a.txt"), "w").write("dirty work\n")
        open(os.path.join(repo, "new.txt"), "w").write("untracked\n")
        d, h = gate("git reset --hard", repo, root)
        new = h.get("updatedInput", {}).get("command", "")
        check("rewrite: dirty reset --hard -> stash first", d == "allow" and new.startswith("git stash push -u"), new)
        run_shell(new, repo)
        stash = sh(["git", "stash", "list"], repo)
        sh(["git", "stash", "apply", "-q"], repo)
        kept = open(os.path.join(repo, "a.txt")).read() == "dirty work\n" and os.path.exists(os.path.join(repo, "new.txt"))
        check("실행 검증: reset 후에도 미커밋 변경을 stash에서 그대로 복구", "taky-guard" in stash and kept, stash)

        os.makedirs(os.path.join(repo, "build"))
        open(os.path.join(repo, "build", "x.js"), "w").write("x")
        d, h = gate("rm -rf build", repo, root)
        new = h.get("updatedInput", {}).get("command", "")
        check("rewrite: rm -rf build -> .taky/trash로 이동", d == "allow" and " mv " in f" {new} ", new)
        run_shell(new, repo)
        trashed = any("x.js" in fs for _r, _d, fs in os.walk(os.path.join(root, ".taky", "trash")))
        check("실행 검증: build는 사라졌고 휴지통에 x.js가 있다", not os.path.exists(os.path.join(repo, "build")) and trashed)

        os.makedirs(os.path.join(root, ".taky"), exist_ok=True)
        json.dump({"netlify": {"repo": "a92a3444"}}, open(os.path.join(root, ".taky", "routes.json"), "w"))
        d, h = gate("netlify deploy --dir dist", repo, root)
        r = h.get("permissionDecisionReason", "")
        check("netlify: 등록된 사이트를 찾아 고친 명령을 안내 (배포 승인 전)", d == "deny" and "--site a92a3444" in r, r[:140])

        print("-- 4. USER 한 줄 승인 = 작업 단위 전체")
        out = grant("이 작업 진행해\n승인 push,deploy 1h", root)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        check("grant: '승인 push,deploy 1h' 기록 + Claude에게 알림", "push, deploy" in ctx or "deploy, push" in ctx, ctx)
        pushes = [gate(c, repo, root)[0] for c in ("git push -u origin feature", "git push origin feature", "git push")]
        check("push 3번 = 묻지도 막지도 않음", all(p == "pass" for p in pushes), pushes)
        d, h = gate("netlify deploy --dir dist", repo, root)
        new = h.get("updatedInput", {}).get("command", "")
        check("grant 후 netlify: --site 붙여 바로 실행", d == "allow" and new.endswith("--site a92a3444"), new)
        d, _ = gate("gh pr merge 12", repo, root)
        check("grant 범위 밖(merge)은 여전히 안내", d == "deny")
        d, _ = gate("git push origin main", repo, root)
        check("grant push여도 main 직접 push는 'prod' 범위라 안내", d == "deny")
        d, _ = gate("netlify deploy --dir dist --site a92a3444", repo, root)
        check("grant(deploy) 범위 draft 배포 -> 통과", d == "pass")
        log = "".join(open(os.path.join(root, ".taky", "delta", f), encoding="utf-8").read() for f in os.listdir(os.path.join(root, ".taky", "delta")))
        check("승인 사용 내역이 delta에 남는다", log.count("grant_use") >= 1)

        print("-- 5. 승인으로도 못 여는 고정 규칙")
        grant("승인 전부 1h", root)
        for cmd in ("rm -rf /", "rm -rf ..", ):
            d, _ = gate(cmd, repo, root)
            check(f"hard: {cmd}", d == "deny")
        os.remove(os.path.join(root, ".taky", "routes.json"))
        d, h = gate("netlify deploy --prod --dir dist", repo, root)
        check("hard: 사이트를 모르는 netlify deploy", d == "deny" and "routes.json" in h.get("permissionDecisionReason", ""))
        grant("승인 취소", root)
        d, _ = gate("gh pr merge 7", repo, root)
        check("승인 취소 후 다시 안내 대상", d == "deny")

        print("-- 6. 반복 상한 (savvy-flow: 두 번 돌려보낸 뒤엔 보고)")
        for _ in range(2):
            gate("gh pr merge 99", repo, root)
        _, h = gate("gh pr merge 99", repo, root)
        check("3번째 같은 시도 -> 'USER에게 한 번에 보고' 지시", "한 번에 보고" in h.get("permissionDecisionReason", ""))

        print("-- 7. MCP 도구")
        d, _ = gate("", repo, root, tool="mcp__github__merge_pull_request")
        check("MCP merge 승인 없음 -> 안내", d == "deny")
        d, _ = gate("", repo, root, tool="mcp__github__get_file_contents")
        check("MCP 조회 -> 통과", d == "pass")
        grant("승인 paid 30m", root)
        d, _ = gate("", repo, root, tool="mcp__ElevenLabs__creative_generate_speech")
        check("MCP ElevenLabs 생성, paid 승인 후 -> 통과", d == "pass")

        print("-- 7b. Claude가 승인 기록을 스스로 만들 수 없다")
        out = hook(GATE, {"tool_name": "Write", "tool_input": {"file_path": f"{root}/.taky/grants.json", "content": "{}"}, "cwd": repo}, root)
        check("Write .taky/grants.json -> 거부", (out or {}).get("hookSpecificOutput", {}).get("permissionDecision") == "deny")
        d, _ = gate(f"echo '{{}}' > {root}/.taky/grants.json", repo, root)
        check("Bash로 grants.json 쓰기 -> 거부", d == "deny")
        out = hook(GATE, {"tool_name": "Write", "tool_input": {"file_path": f"{repo}/README.md"}, "cwd": repo}, root)
        check("일반 파일 Write -> 통과", out is None)

        print("-- 8. 이 훅은 승인 창(ask)을 절대 띄우지 않는다")
        check(f"전체 {len(seen_decisions)}회 호출 중 'ask' 0회", "ask" not in seen_decisions)

        print("-- 9. DELTA 수집기와 DONE 원장")
        hook(DELTA, {"tool_name": "Edit", "tool_input": {"file_path": f"{repo}/a.txt"}, "session_id": "s1"}, root)
        hook(DELTA, {"tool_name": "Bash", "tool_input": {"command": "ls"}, "session_id": "s1"}, root)
        led = os.path.join(root, ".taky", "ledger.json")
        json.dump({"items": [{"id": "CUR-006", "claim": "phone login", "kind": "inference", "state": "VERIFIED",
                              "priority": "must", "evidence": []}]}, open(led, "w"))
        out = hook(LEDGER, {"cwd": root}, root, args=("--stop-hook",))
        check("DONE: 증거 없는 VERIFIED 추론은 Claude에게 한 번 되돌림", out and out.get("decision") == "block")
        out = hook(LEDGER, {"cwd": root, "stop_hook_active": True}, root, args=("--stop-hook",))
        check("DONE: 같은 턴에 두 번은 안 막음", out is None)

        print("-- 10. 관찰 모드(기본): 아무것도 막거나 고치지 않고 기록만")
        global MODE
        MODE = "observe"
        outs = [hook(GATE, {"tool_name": "Bash", "tool_input": {"command": c}, "cwd": repo}, root)
                for c in ("gh pr merge 5", "rm -rf build2", "netlify deploy")]
        check("observe: 출력 0건 (세션에 영향 없음)", all(o is None for o in outs), outs)
        log = "".join(open(os.path.join(root, ".taky", "delta", f), encoding="utf-8").read() for f in os.listdir(os.path.join(root, ".taky", "delta")))
        check("observe: 했을 판단 3건이 delta에 기록", log.count('"observe"') >= 3)
        MODE = "guide"

    fails = results.count(False)
    print(f"\n{len(results) - fails}/{len(results)} PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
