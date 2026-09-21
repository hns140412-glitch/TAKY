#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"MASTER"/"SHARED_TECHNICAL_CAPABILITY_REGISTRY.json"
data=json.loads(REG.read_text(encoding="utf-8"))
fail=[]

caps=data.get("capabilities") or []
ids=[x.get("capability_id") for x in caps if isinstance(x,dict)]
if len(ids)!=len(set(ids)):
    fail.append("DUPLICATE_CAPABILITY_ID")

by_id={x.get("capability_id"):x for x in caps if isinstance(x,dict)}
for cid in ("CAP-RELEASE-COMPAT-001","CAP-PWA-UPDATE-001","CAP-EVENT-ENVELOPE-001","CAP-LOCAL-QUEUE-001","CAP-OCR-INGEST-001","CAP-HTTP-ADAPTER-001"):
    c=by_id.get(cid)
    if not c:
        fail.append("MISSING_CAPABILITY:"+cid)
        continue
    if c.get("state")!="REFERENCE_IMPLEMENTED":
        fail.append("REFERENCE_IMPLEMENTATION_STATE_MISSING:"+cid)
    impl=c.get("implementation")
    if not impl or not (ROOT/impl).is_file():
        fail.append("IMPLEMENTATION_MISSING:"+cid)

release=by_id.get("CAP-RELEASE-COMPAT-001") or {}
fields=((release.get("mechanism_contract") or {}).get("required_fields") or [])
for f in ("app_id","app_version","runtime_version","data_schema_version","contract_version","release_id"):
    if f not in fields:
        fail.append("RELEASE_FIELD_MISSING:"+f)

event_cap=by_id.get("CAP-EVENT-ENVELOPE-001") or {}
event_contract=event_cap.get("mechanism_contract") or {}
if "event_id is immutable event identity" not in (event_contract.get("identity_rule") or ""):
    fail.append("EVENT_IDENTITY_RULE_MISSING")
for x in ("family or organization ownership","role/permission/authority"):
    if x not in (event_cap.get("semantic_exclusions") or []):
        fail.append("EVENT_SEMANTIC_EXCLUSION_MISSING:"+x)

queue=by_id.get("CAP-LOCAL-QUEUE-001") or {}
queue_contract=queue.get("mechanism_contract") or {}
if "DEAD_LETTER" not in (queue_contract.get("states") or []):
    fail.append("LOCAL_QUEUE_DEAD_LETTER_MISSING")
if "bounded by max_attempts" not in (queue_contract.get("retry_rule") or ""):
    fail.append("LOCAL_QUEUE_BOUNDED_RETRY_RULE_MISSING")
for x in ("conflict resolution authority","family or organization identity","roles/permissions"):
    if x not in (queue.get("semantic_exclusions") or []):
        fail.append("LOCAL_QUEUE_SEMANTIC_EXCLUSION_MISSING:"+x)

pwa=by_id.get("CAP-PWA-UPDATE-001") or {}
rule=((pwa.get("mechanism_contract") or {}).get("required_transition_rule") or "")
if "safe_point=true" not in rule:
    fail.append("PWA_SAFE_POINT_RULE_MISSING")

ocr=by_id.get("CAP-OCR-INGEST-001") or {}
if ocr.get("state")!="REFERENCE_IMPLEMENTED":
    fail.append("OCR_INGEST_REFERENCE_IMPLEMENTATION_MISSING")
for x in ("assignment FACT confirmation","vocabulary pairing semantics","parent/child review authority","roles/permissions"):
    if x not in (ocr.get("semantic_exclusions") or []):
        fail.append("OCR_SEMANTIC_EXCLUSION_MISSING:"+x)

http=by_id.get("CAP-HTTP-ADAPTER-001") or {}
if http.get("state")!="REFERENCE_IMPLEMENTED":
    fail.append("HTTP_ADAPTER_REFERENCE_IMPLEMENTATION_MISSING")
for x in ("API credential ownership","authentication identity","roles/permissions","cross-domain authority"):
    if x not in (http.get("semantic_exclusions") or []):
        fail.append("HTTP_SEMANTIC_EXCLUSION_MISSING:"+x)

auth=by_id.get("CAP-AUTH-TRANSPORT-001") or {}
if auth.get("state")!="HOLD_BEFORE_EXTRACTION":
    fail.append("AUTH_TRANSPORT_NOT_HELD")
for x in ("organization identity","family/child identity","roles/permissions","cross-domain authority"):
    if x not in (auth.get("semantic_exclusions") or []):
        fail.append("AUTH_SEMANTIC_EXCLUSION_MISSING:"+x)

if fail:
    print("FAIL: shared technical capability registry")
    for x in fail: print(x)
    raise SystemExit(1)

node=subprocess.run(
    ["node",str(ROOT/"SHARED"/"runtime"/"shared-runtime-foundation.test.js")],
    cwd=ROOT,capture_output=True,text=True,check=False
)
if node.returncode:
    print(node.stdout,end="")
    print(node.stderr,end="",file=sys.stderr)
    raise SystemExit(node.returncode)
print(node.stdout.strip())
print("PASS: shared technical capability registry and reference implementations")
