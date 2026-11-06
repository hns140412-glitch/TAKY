"""Isolated test of TAKY outcome hook purpose anchor / rework gate (temp state dir, no global state touched)."""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path
HOOK = r"D:\Git PWA\TAKY\.claude\hooks\taky_outcome_hook.py"
tmp = Path(tempfile.mkdtemp(prefix="taky_purpose_"))
env = dict(os.environ, TAKY_OUTCOME_STATE_DIR=str(tmp / "state"), TAKY_FAILURE_LEDGER=str(tmp / "ledger.jsonl"), PYTHONIOENCODING="utf-8")
def run(ev):
    ev = dict(ev, session_id="t1", cwd="x")
    p = subprocess.run([sys.executable, "-B", HOOK], input=json.dumps(ev, ensure_ascii=False).encode("utf-8"), capture_output=True, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace").strip(), p.stderr.decode("utf-8", "replace").strip()
out = tmp / "out.xlsx"; old = tmp / "source.xlsx"; old.write_text("x"); os.utime(old, (time.time() - 3600,) * 2)
res = {}
rc, o, e = run({"hook_event_name": "UserPromptSubmit", "prompt": "<wake><message>미아동 888세대 계획안 정합 확인해서 보고서 만들어</message></wake>"})
ctx = json.loads(o)["hookSpecificOutput"]["additionalContext"]
res["anchor_emitted"] = "Purpose Anchor" in ctx and "미아동 888세대" in ctx and o.count("\n") == 0
res["stdout_ascii_safe"] = o.isascii()  # Windows cp949 must not garble Korean context
stops = []
for i in range(1, 4):
    if i > 1:
        run({"hook_event_name": "UserPromptSubmit", "prompt": "엑셀 양식 다시 고쳐줘"})
    out.write_text(str(i))
    run({"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": f'python build.py "{old}" "{out}"'}, "tool_response": {"stdout": "saved"}})
    rc, o, e = run({"hook_event_name": "Stop"})
    stops.append("Purpose Gate" in o)
    if "Purpose Gate" in o:
        res["stop_reason_korean_ok"] = "다시 만들었다" in json.loads(o)["reason"] and o.isascii()
res["no_block_turn1_2"] = stops[:2] == [False, False]
res["block_turn3"] = stops[2]
rc, o, e = run({"hook_event_name": "Stop"})
res["no_repeat_block"] = "Purpose Gate" not in o
st = json.loads(next((tmp / "state").glob("*.json")).read_text(encoding="utf-8"))
res["old_source_not_counted"] = "source.xlsx" not in st["rework"]
res["purpose_kept"] = st["purpose"].startswith("미아동 888세대")
run({"hook_event_name": "UserPromptSubmit", "prompt": "목적: AGW-0001 팀 업무 접수 연결"})
st = json.loads(next((tmp / "state").glob("*.json")).read_text(encoding="utf-8"))
res["purpose_override"] = st["purpose"] == "AGW-0001 팀 업무 접수 연결"
rc, o, e = run({"hook_event_name": "UserPromptSubmit", "prompt": '<wake reason="mention"><message trigger="true">ㄱ</message><system-note>If one quick read gets you the answer, just answer.</system-note></wake>'})
st = json.loads(next((tmp / "state").glob("*.json")).read_text(encoding="utf-8"))
res["short_prompt_keeps_purpose"] = st["purpose"] == "AGW-0001 팀 업무 접수 연결"
for k, v in res.items(): print(("PASS " if v else "FAIL ") + k)
print("ALL PASS" if all(res.values()) else "SOME FAIL")
