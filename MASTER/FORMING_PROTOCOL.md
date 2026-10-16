# TAKY FORMING — Shared Transformation Protocol
Status: ADOPTED BY USER / MASTER REFERENCE PENDING POST-WRITE VERIFICATION
Rule: TKY-FORMING-001
Scope: GLOBAL SHARED PROCESS CONTRACT; domain semantics stay domain/project-owned.

## Canonical route
MINING -> INDEXING -> FORMING -> {LEARNING PROJECTION | APPLICATION CONSUMPTION | BOTH} -> EXECUTION -> FEEDBACK.
LEARNING is conditional; FEEDBACK re-enters the smallest affected stage. This does not replace the canonical runtime approval cycle.

## Processing kinds
1. KNOWLEDGE_FORMING: grounded concepts, relations, constraints and evidence-linked candidate rules; no authority to approve legal or domain rules.
2. CONTENT_FORMING: explanations, examples, exercises, visual specifications and structured learning content; source facts must be distinguished from generated explanations.
3. APPLICATION_FORMING: schemas, deterministic computations, consumption contracts and task structures; does not transfer application ownership.
These are operations, not new repositories or authorities.

## Required input
source_refs, index_refs, owner_namespace, forming_kind, target_consumer, authority_scope, input_revision, ruleset_revision. Missing/partial sources -> INCOMPLETE, not success or SOURCE_ABSENT.

## Required output
artifact_id, owner_namespace, forming_kind, artifact_revision, source_refs, index_refs, ruleset_revision, input_fingerprint, output_fingerprint, consumer_contract, validation_status, approval_status, provenance_trace, known_gaps, generated_at.

## Governance and storage
Preserve RAW / INDEX / DETAIL / CURRENT role separation. Derived immutable revisions live in the existing DETAIL/HISTORY owner mechanisms. Only approved logical versions are exposed as namespace CURRENT. Do not overwrite RAW or earlier revisions. Input+rules+owner fingerprints drive idempotency; do not merge distinct authority or tenant scopes.
DRAFT -> VERIFIED -> APPROVED -> CONSUMABLE; HOLD/CONFLICT/REJECTED/SUPERSEDED are explicit. VERIFIED != APPROVED != IMPLEMENTED.
FORMING != LEARNING ENGINE. Learning projection and adaptive/scheduling decisions remain with their established owners. Prefer deterministic transformations; external model/API calls require applicable necessity/cost/authority gates.

## Gates
AUTHORITY (owner/provenance); GROUNDING (source and index linkage); STRUCTURE (schema/revision); SEMANTICS (facts vs examples/generated claims); CONSUMPTION (actual parse/contract); REGRESSION (protected-state and replay); FEEDBACK (cause-linked limited re-entry).
All material failures remain OPEN/INCOMPLETE/CONFLICT and must not be reported PASS.

## Acceptance
T01 provenance; T02 missing source; T03 deterministic replay; T04 revision regeneration; T05 legal authority boundary; T06 consumer contract; T07 RAW/INDEX immutability; T08 learning engine separation; T09 tenant separation; T10 feedback routing; T11 terminal END integrity; T12 archived history preservation.
This standard does not assert acceptance tests have passed without executable evidence.

END
