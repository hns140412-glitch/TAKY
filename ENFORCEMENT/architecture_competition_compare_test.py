#!/usr/bin/env python3
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_COMPARE.py"
spec=importlib.util.spec_from_file_location("cmp",TOOL)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def main():
    ledger=Path(tempfile.gettempdir())/"archcomp-compare-test.jsonl"
    rows=[
        {"agency":"LH","competition":"SAME-PROJECT","entry_id":"E1","artifact_id":"B1-P1","board_no":"1","representation_mode":"PLAN","technique":"clean_vector_plan","drawing_name":"1층 평면도","outcome":"SUCCESS"},
        {"agency":"LH","competition":"SAME-PROJECT","entry_id":"E1","artifact_id":"B1-S1","board_no":"1","representation_mode":"SECTION","technique":"rendered_section","drawing_name":"주요 단면도","outcome":"SUCCESS"},
        {"agency":"LH","competition":"SAME-PROJECT","entry_id":"E2","artifact_id":"B1-P2","board_no":"1","representation_mode":"PLAN","technique":"rendered_plan","drawing_name":"1층 평면도","outcome":"PARTIAL"},
        {"agency":"LH","competition":"SAME-PROJECT","entry_id":"E2","artifact_id":"B2-S2","board_no":"2","representation_mode":"SECTION","technique":"sectional_perspective","drawing_name":"주요 단면도","outcome":"SUCCESS"}
    ]
    ledger.write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in rows)+"\n",encoding="utf-8")
    result=mod.compare(mod.load_rows(ledger),"LH","SAME-PROJECT")
    assert result["entry_count"]==2
    assert result["entries"]["E1"]["artifact_count"]==2
    assert result["entries"]["E2"]["board_count"]==2
    diff_modes={d["mode"] for d in result["within_competition_differences"]}
    assert "PLAN" in diff_modes and "SECTION" in diff_modes
    print("PASS: same-competition multi-entry representation comparison")

if __name__=="__main__":
    raise SystemExit(main())
