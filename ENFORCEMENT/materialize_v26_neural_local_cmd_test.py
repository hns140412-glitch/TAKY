#!/usr/bin/env python3
from pathlib import Path

def test_windows_wrapper_has_separate_commands():
    text=Path(__file__).with_name("materialize_v26_neural_local.cmd").read_text(encoding="utf-8")
    assert "\\npython" not in text
    lines=[x.strip() for x in text.splitlines()]
    materialize=[x for x in lines if "materialize_v26_neural_local_v2.py" in x]
    regression=[x for x in lines if "v26_neural_retrieval_regression.py" in x]
    assert len(materialize)==1
    assert len(regression)==1
    assert materialize[0] != regression[0]

if __name__=="__main__":
    test_windows_wrapper_has_separate_commands()
    print("V26_WINDOWS_WRAPPER_REGRESSION_SUCCESS")
