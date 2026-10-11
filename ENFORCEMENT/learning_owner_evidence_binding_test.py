import hashlib
from pathlib import Path

ROOT=Path(r"D:\Git PWA")
TAKY=ROOT/"TAKY"
READY=ROOT/"Ready & Set"
HIDE=ROOT/"Hide & Seek"
SNAP=ROOT/"Snap & Pop"

def text(p):
    return p.read_text(encoding="utf-8-sig")

shared=(TAKY/"SHARED/runtime/taky-learning-evidence-client-v1.js").read_bytes()
shared_sha=hashlib.sha256(shared).hexdigest()

for repo in (READY,HIDE,SNAP):
    p=repo/"taky-learning-evidence-client-v1.js"
    assert p.exists(), f"missing client in {repo.name}"
    assert hashlib.sha256(p.read_bytes()).hexdigest()==shared_sha, f"client drift in {repo.name}"

ready_index=text(READY/"index.html")
hide_index=text(HIDE/"index.html")
snap_index=text(SNAP/"index.html")
assert "taky-learning-evidence-client-v1.js" in ready_index
assert "taky-learning-evidence-client-v1.js" in hide_index
assert "hide-learning-evidence-source-v1.js" in hide_index
assert hide_index.index("hide-learning-evidence-source-v1.js") < hide_index.index("taky-learning-evidence-client-v1.js")
assert "taky-learning-evidence-client-v1.js" in snap_index

assert "taky-learning-evidence-client-v1.js" in text(READY/"sw.js")
assert "taky-learning-evidence-client-v1.js" in text(HIDE/"sw.js")
assert "hide-learning-evidence-source-v1.js" in text(HIDE/"sw.js")
assert "taky-learning-evidence-client-v1.js" in text(SNAP/"sw.js")

ready_runtime=text(READY/"ready-runtime-v07.js")
for needle in [
    "function learningScope()",
    "url.searchParams.set('subject',scope.subject)",
    "url.searchParams.set('concept_skill_target',scope.concept_skill_target)",
    "url.searchParams.set('learning_target_id',scope.learning_target_id)",
    "window.dispatchEvent(new CustomEvent('taky-learning-event',{detail:event}))"
]:
    assert needle in ready_runtime, f"Ready binding missing: {needle}"

hide_source=text(HIDE/"hide-learning-evidence-source-v1.js")
for needle in [
    "RETRIEVAL_ATTEMPT_RESULT",
    "verification_observation",
    "response_value"
]:
    assert needle in hide_source, f"Hide raw evidence missing: {needle}"
for forbidden in ["verified_outcome","LEARNING_VERIFICATION_RECEIPT","promotion_authorized"]:
    assert forbidden not in hide_source, f"Hide source leaks authority: {forbidden}"

snap_bridge=text(SNAP/"snap-bridge.js")
assert "snap_pop_shared_outbox_v1" in snap_bridge
assert "TASK_COMPLETED" in snap_bridge or "TASK_PARTIAL" in snap_bridge

client=text(TAKY/"SHARED/runtime/taky-learning-evidence-client-v1.js")
for forbidden in [
    "'verified_outcome'","'verification_input'","'verification_receipt'",
    "'verification_candidate'","'promotion_authorized'","'authority_transfer'"
]:
    assert forbidden in client, f"proof scrub list missing {forbidden}"
for required in [
    "MEMBER_SCOPE_REQUIRED","SUBJECT_SCOPE_REQUIRED","CONCEPT_SKILL_SCOPE_REQUIRED",
    "/api/learning/evidence","OBSERVATION_INGEST_RECEIPT","REAL_EVIDENCE_RECEIPT"
]:
    assert required in client, f"client invariant missing {required}"

print("LEARNING_OWNER_EVIDENCE_BINDING_STATIC_PASS")
print("CLIENT_SHA256="+shared_sha)
