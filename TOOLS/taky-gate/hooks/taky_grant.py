#!/usr/bin/env python3
"""TAKY grant: UserPromptSubmit hook. One USER line approves a whole work unit.

Only the USER's own typed prompt reaches this hook, so Claude cannot write a grant by
itself through this path. Format (one line, anywhere in the prompt):

    승인 push,deploy 2h        approve push and draft deploy for 2 hours
    승인 merge,prod 30m        approve PR merge and production deploy for 30 minutes
    승인 전부 1h               everything except the hard rules (wrong netlify site, broad rm)
    승인 취소                  revoke every active grant

Kinds: push, merge, deploy (draft/preview), prod (production), paid, destroy, all(전부).
Default duration 2h, cap 12h. Writes ~/.taky/grants.json (TAKY_HOME overrides) and echoes the grant
back to Claude as additionalContext so the work continues without further prompts.
"""
import datetime as dt
import json
import os
import re
import sys

KINDS = {"push", "merge", "deploy", "prod", "paid", "destroy", "all"}
ALIAS = {"전부": "all", "모두": "all", "배포": "deploy", "운영": "prod", "병합": "merge", "유료": "paid", "삭제": "destroy"}
LINE = re.compile(r"(?:^|\n)\s*(?:승인|approve)\s+([^\n]+)", re.IGNORECASE)
DUR = re.compile(r"^(\d+)\s*(m|h|분|시간)$")


def parse(prompt):
    m = LINE.search(prompt or "")
    if not m:
        return None
    words = m.group(1).replace(",", " ").split()
    if words and words[0] in ("취소", "revoke"):
        return {"revoke": True}
    kinds, minutes = [], 120
    for w in words:
        d = DUR.match(w)
        if d:
            n = int(d.group(1))
            minutes = n if d.group(2) in ("m", "분") else n * 60
            continue
        k = ALIAS.get(w, w.lower())
        if k in KINDS:
            kinds.append(k)
    if not kinds:
        return None
    return {"kinds": sorted(set(kinds)), "minutes": max(5, min(minutes, 720))}


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    g = parse(event.get("prompt", ""))
    if not g:
        return 0
    home = os.environ.get("TAKY_HOME") or os.path.join(os.path.expanduser("~"), ".taky")
    path = os.path.join(home, "grants.json")
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        data = {"grants": []}
    now = dt.datetime.now(dt.timezone.utc)
    if g.get("revoke"):
        data["grants"] = []
        msg = "[TAKY] USER가 모든 승인을 취소했다. 이후 push/병합/배포/유료/삭제는 다시 안내 대상이다."
    else:
        gid = "G" + now.strftime("%m%d%H%M%S")
        data["grants"].append({"id": gid, "kinds": g["kinds"], "by": "USER prompt",
                               "session": str(event.get("session_id", ""))[:12],
                               "granted": now.isoformat(timespec="seconds"),
                               "expires": (now + dt.timedelta(minutes=g["minutes"])).isoformat(timespec="seconds")})
        msg = (f"[TAKY] USER 승인 {gid}: {', '.join(g['kinds'])} · {g['minutes']}분. 이 범위의 호출은 다시 묻지 않는다. "
               "범위 밖(다른 종류, 잘못된 netlify 사이트, 프로젝트 밖 삭제)은 여전히 안내 대상이다. 사용 내역은 ~/.taky/delta에 남는다.")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
