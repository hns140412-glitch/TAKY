#!/usr/bin/env python3
"""TAKY evidence ledger + DONE gate.

Two ideas borrowed and fitted to TAKY:
- REA (morluto/rea): "every conclusion must distinguish observations, inferences
  and unknowns", and each finding carries its evidence and limits.
- replica-diff parity.py (Jakeschincariol/replica-skill): weighted must/should/could
  score; missing must-haves means "not shippable", and it says so.

TAKY's STATE GATE ladder is the state field:
  CHAT_REVIEWED < EVENT_RECORDED < RAW_CAPTURED < MINED < INDEXED < FORMING < APPLIED < VERIFIED

Usage:
  taky_ledger.py check  [.taky/ledger.json]   -> score + violations, exit 1 if DONE is not allowed
  taky_ledger.py --stop-hook                  -> Stop hook mode (reads hook JSON on stdin)
"""
import json
import os
import sys

LADDER = ["CHAT_REVIEWED", "EVENT_RECORDED", "RAW_CAPTURED", "MINED", "INDEXED", "FORMING", "APPLIED", "VERIFIED"]
KINDS = ("observation", "inference", "unknown")
WEIGHT = {"must": 3, "should": 2, "could": 1}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check(ledger):
    items = ledger.get("items", [])
    violations, total, got, open_must = [], 0, 0.0, []
    for it in items:
        iid = it.get("id", "?")
        state, kind = it.get("state"), it.get("kind")
        ev = [e for e in it.get("evidence", []) if e.get("ref")]
        if state not in LADDER:
            violations.append(f"{iid}: 알 수 없는 상태 {state!r}")
            continue
        if kind not in KINDS:
            violations.append(f"{iid}: kind는 observation/inference/unknown 중 하나여야 함")
        rank = LADDER.index(state)
        if rank >= LADDER.index("APPLIED") and not ev:
            violations.append(f"{iid}: {state}인데 증거가 없음 (RULE: 증거 없이 PASS 주장 금지)")
        if state == "VERIFIED" and kind != "observation":
            violations.append(f"{iid}: VERIFIED는 관측(observation)만 가능. {kind}는 검증 완료가 아님")
        if state == "VERIFIED" and not any(e.get("type") in ("command", "readback", "screenshot", "test") for e in ev):
            violations.append(f"{iid}: VERIFIED 증거가 실행/재조회 영수증이 아님 (문서·주장만 있음)")
        if kind == "unknown" and not it.get("limits"):
            violations.append(f"{iid}: unknown에는 무엇이 왜 모르는지(limits)가 필요")
        w = WEIGHT.get(it.get("priority", "should"), 2)
        total += w
        got += w * (1.0 if state == "VERIFIED" else 0.5 if state == "APPLIED" else 0.0)
        if it.get("priority") == "must" and state != "VERIFIED":
            open_must.append(f"{iid} ({state})")
    score = round(100 * got / total) if total else 0
    applied_only = [i.get("id") for i in items if i.get("state") == "APPLIED"]
    return {"score": score, "violations": violations, "open_must": open_must,
            "code_done_not_value": applied_only,
            "done_allowed": not violations and not open_must}


def report(res):
    print(f"VALUE 점수 {res['score']}/100 (must 3 · should 2 · could 1, APPLIED는 절반)")
    for v in res["violations"]:
        print("  위반:", v)
    if res["open_must"]:
        print("  열린 must:", ", ".join(res["open_must"]))
    if res["code_done_not_value"]:
        print("  CODE DONE != VALUE DELIVERED:", ", ".join(res["code_done_not_value"]))
    print("DONE 허용" if res["done_allowed"] else "DONE 불가: 위 항목이 남아 있음")


def stop_hook():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    if event.get("stop_hook_active"):
        return 0  # already blocked once this turn; never loop
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    path = os.path.join(root, ".taky", "ledger.json")
    if not os.path.exists(path):
        return 0
    try:
        res = check(load(path))
    except Exception as e:
        print(json.dumps({"decision": "block", "reason": f"TAKY DONE GATE: ledger.json을 읽을 수 없음 ({e})"}))
        return 0
    if res["violations"]:
        reason = "TAKY DONE GATE: 원장에 증거 없는 완료 주장이 있다. 고치거나 상태를 낮춘 뒤 보고할 것.\n" + \
                 "\n".join("- " + v for v in res["violations"][:8])
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


def main():
    if "--stop-hook" in sys.argv:
        return stop_hook()
    path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(".taky", "ledger.json")
    res = check(load(path))
    report(res)
    return 0 if res["done_allowed"] else 1


if __name__ == "__main__":
    sys.exit(main())
