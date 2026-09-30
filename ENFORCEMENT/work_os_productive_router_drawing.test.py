#!/usr/bin/env python3
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("router",HERE/"work_os_productive_router.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

r=m.route({"kind":"DRAWING_PRODUCTION","artifact_class":"FINAL","producer_type":"PYTHON_ONE_OFF","registered_engine":False,"engine_available":True,"bypass_used":True})
assert r["pass"] is False
assert "ENGINE_AVAILABLE_BYPASS_USED_GOVERNANCE_FAILURE" in r["detected"]

r=m.route({"kind":"DRAWING_PRODUCTION","artifact_class":"FINAL","producer_type":"DRAWING_ENGINE","registered_engine":True})
assert r["pass"] is True and r["route"]["destination"]=="AUTHORIZED_DRAWING_ENGINE"

r=m.route({"kind":"HANDOFF_MODE","mode":"RESUME","structural_failure_count":3})
assert r["pass"] is False and r["route"]["mode"]=="SURGERY"

r=m.route({"kind":"HANDOFF_MODE","mode":"RETROSPECTIVE","structural_failure_count":3})
assert r["pass"] is True
print("work_os_productive_router drawing surgery: PASS")
