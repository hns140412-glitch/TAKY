# TAKY ENFORCEMENT / REPLAY PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Role: Convert material TAKY prose rules into executable or auditable gates and prevent `RULE WRITTEN ≠ RULE ENFORCED` recurrence.
Normative taxonomy: `MASTER/FAILURE_TAXONOMY.md`.
Rule ownership registry: `MASTER/RULE_REGISTRY.json`.
Executable reference implementation: `ENFORCEMENT/taky_gate.py`.
Representative cases: `ENFORCEMENT/replay_cases.json` + `ENFORCEMENT/replay_cases_v2.json`.
Bundle closure validator: `ENFORCEMENT/handoff_bundle_validator.py`.

## 0. Core rule — HARD LOCK

`RULE WRITTEN ≠ RULE ENFORCED`.
`FIXTURE DESCRIBED ≠ FIXTURE REPLAYED`.
`CHECKSUM MATCH ≠ EXTERNAL SOURCE VERIFIED`.
`PACKAGE OPENS ≠ HANDOFF RECOVERABLE`.
`HUMAN APPROVAL REQUIRED ≠ HUMAN APPROVAL ASSUMED`.
`REFERENCE_ONLY ≠ EXECUTION AUTHORITY`.
`PRE-RESPONSE CHECKLIST ≠ DETERMINISTIC RUNTIME INTERCEPT`.

A material rule that is mechanically checkable or replayable SHALL have a concrete enforcement expression when technically feasible. Concrete enforcement may include deterministic assertions, schema/contract validation, replay fixtures, bundle/file closure checks, CI/release blocking, post-write readback, or explicit human approval records.

If no executable enforcement exists for a material mechanically-checkable rule, status is `ENFORCEMENT_MISSING`; prose existence alone SHALL NOT be described as recurrence-prevention PASS.

## 0.1 Universal-basis activation gate — HARD LOCK

For TAKY-controlled runtimes, material answers/actions across MASTER/OS/project/mobile-web/Work/Codex/tool surfaces SHALL enter the pre-execution path without requiring the user to restate "TAKY 기준".

When an execution record marks `material_taky_turn=true`, the deterministic gate requires:
- `pre_execution_gate_required=true`;
- non-empty applicable rule/context/history evidence;
- an operational `working_model` mapping applicable rules to execution;
- truthful claim ceiling for runtime enforcement.

For low-risk/non-material conversational turns, a full repository preflight need not be created, but the answer remains subject to active universal invariants and SHALL NOT knowingly contradict applicable canonical state.

`TAKY-GOVERNED MATERIAL TURN + NO PREFLIGHT = RULE_NOT_APPLIED`.
`NO TAKY PREFIX != NO TAKY GOVERNANCE`.

This repository gate can enforce only runtimes that actually invoke it. Hosted ChatGPT native auto-invocation remains UNVERIFIED unless directly evidenced.

## 1. Pre-response negative-existence gate — HARD LOCK

Before a material claim equivalent to “없다 / 말한 적 없다 / 규칙이 없다 / 자료가 없다 / 확인되지 않는다”, the execution record SHALL contain sufficient recovery evidence.

Minimum fields when applicable:
- `negative_existence_claim`;
- `recovery_paths_checked`;
- `material_alternate_path_available`;
- `source_found_after_claim`;
- `source_recoverable_by_taky`;
- `user_had_to_recover`.

Hard behavior:
- material alternate recovery path remains + only one/single-path miss ⇒ negative-existence claim blocked;
- source later found after premature absence claim ⇒ `FALSE_MISSING_DECLARATION`;
- user had to recover evidence TAKY could materially recover ⇒ `USER_FORCED_RECOVERY` + normally `USER_AS_QA`;
- genuinely inaccessible after applicable paths ⇒ `TRUE_UNAVAILABLE / UNVERIFIED_SOURCE_COVERAGE`, not “never existed”.

## 1.1 Recovery-exhaustion / no-user-as-QA gate — HARD LOCK

Before asking the user to search old chats, re-upload a file, prove a prior statement, collect a screenshot, or perform debugging/evidence recovery that TAKY can materially attempt itself, inventory distinct recovery families.

Minimum fields:
- `user_evidence_request`;
- `available_recovery_families`;
- `attempted_recovery_families`;
- `material_recovery_path_remaining`;
- `user_is_only_possible_source`;
- `recovery_log_present`.

Recovery families are distinct evidence surfaces, not repeated keyword variations in one surface. Examples: current conversation, conversation/library raw evidence, Context Ledger/Handoff, canonical/history, connected workspace/Drive/Notion, actual implementation/runtime.

Execution rule:
- if 3 or more materially available families exist, attempt at least 3 materially distinct families before asking the user;
- if fewer than 3 materially available families exist, attempt all materially available families;
- if a material recovery path still remains, user evidence/debug request is blocked;
- if the user is genuinely the only possible source holder, a bounded user request is allowed and SHALL state that boundary.

Violation ⇒ `RECOVERY_FAILED / USER_AS_QA` with reason `USER_QA_OFFLOADING_VIOLATION`.

## 2. Maximum/full handoff portability gate — HARD LOCK

When the user requests `최대한 / 모두 / 전체 / 원문 / 최대 / full / maximum` handoff/transfer and the recipient may lack repository access, the package SHALL be independently recoverable without silently relying on inaccessible repository pointers.

Required contract fields when applicable:
- `handoff_requested_maximum`;
- `recipient_repo_access`;
- `portable_source_snapshots` or `portable_diff_with_base`;
- `repo_pointers_only`;
- `source_manifest_present`;
- `evidence_authority_classified`;
- `resume_simulation_passed`;
- `bundle_closure_required`;
- `bundle_closure_passed`;
- `claims_complete`.

Hard behavior:
- no recipient repo access + only SHA/blob pointers ⇒ `HANDOFF_LOSS / FAIL`;
- no recipient repo access + neither full source snapshot nor reconstructable diff+complete base ⇒ `HANDOFF_LOSS / FAIL`;
- maximum/full requested + material accessible sources not inventoried/classified ⇒ NOT PASS;
- package checksum proves package/internal integrity only, not independent live repository verification.

Allowed freshness labels:
- `SNAPSHOT_VERIFIED`;
- `LIVE_HEAD_VERIFIED`;
- `LIVE_HEAD_UNVERIFIED`.

## 2.1 Bundle closure gate — HARD LOCK

For a claimed self-contained maximum/full handoff, `MANIFEST.json` SHALL be machine-verifiable. Every `required_for_resume` artifact must physically exist inside the bundle, match its declared SHA-256, carry an authority class and freshness class, and be resolvable from declared artifact IDs. Resume simulation must cover every materially required canonical owner.

The reference validator is:
`python ENFORCEMENT/handoff_bundle_validator.py <bundle-root>`.

`OFFLINE_RECONSTRUCTION_PASS ≠ LIVE_STATE_CURRENT`.
A bundle may prove declared-scope offline reconstruction while live external freshness remains `LIVE_HEAD_UNVERIFIED`.

Bundle closure failure is classified as `HANDOFF_LOSS` with reason `BUNDLE_CLOSURE_MISSING`; do not create a parallel semantic failure token solely for package structure.

## 3. Replay gate — HARD LOCK

A correction that claims recurrence prevention for an applicable fixture SHALL run a representative replay or equivalent deterministic check before recurrence-prevention PASS.

Required sequence:
`HISTORICAL FAILURE INPUT/STATE → CURRENT GATE → EXPECTED BLOCK/CLASSIFICATION → POST-FIX COMPLIANT INPUT/STATE → EXPECTED PASS → RECORDED LOG`.

A prose fixture without an executed replay is `REPLAY_NOT_PERFORMED`.

## 4. Rule-application gate — HARD LOCK

If an applicable rule was loaded/cited/known and the actual result violates it, classify `RULE_NOT_APPLIED` regardless of how accurately the rule was quoted.

`RULE CITED + RESULT VIOLATES RULE = FAIL`.

## 4.1 Delegated-continuation / premature-stop gate — HARD LOCK

When the user delegates continued execution with wording equivalent to `확인이 필요할 때까지 진행`, `계속 진행`, `멈추지 마`, `알아서 진행`, `ㄱ`, or another context-grounded continue instruction, TAKY SHALL continue through authorized executable next actions until a real blocker, required human-only decision, safety/permission boundary, or requested completion condition is reached.

Violation ⇒ `PREMATURE_STOP`.

## 4.2 Result-not-narration gate — HARD LOCK

When the user requests a concrete artifact/action/result and the system has authority/capability to produce it, explanation or intention text alone is not the requested result.

If a concrete authorized result was required and the response stopped at explanation/plan, classify at least `SUBSTITUTE_RESULT`; add `OUTPUT_FORM_MISMATCH` when the requested form was not supplied, and `PREMATURE_STOP` when delegated continuation was also active.

## 4.4 Pre-action rule-application gate — HARD LOCK

This is the generic control for the recurring failure pattern:

`RULE EXISTS → RULE LOADED → ACTION STILL VIOLATES RULE`.

Before any material action, the execution record SHALL bind applicable rules to the exact action and SHALL prove required preconditions before the action is allowed.

Minimum structured fields:
- `material_action_planned`;
- `action_id`;
- `action_rule_refs`;
- `action_rule_bindings[]` with `rule_ref / effect / implication`;
- `action_preconditions[]` with `id / required / satisfied`;
- `action_conflicts_with_rule`;
- when relevant, `lower_impact_compliant_path_available`, `higher_cost_side_effect_selected`, and explicit override approval.

Execution rule:
- a material action with no rule binding is blocked;
- a required precondition that is not satisfied blocks the action;
- an action that conflicts with an applicable rule is blocked;
- if a lower-impact compliant path exists, selecting a higher-cost side effect without explicit override is blocked.

Violation classification: `RULE_NOT_APPLIED`.
Repeated violation after the correction may additionally be `POST_CORRECTION_REOCCURRENCE`.

This gate is domain-independent. It applies to implementation, validation, external validation, deployment, C2S, reflection, handoff, repository writes, and other material actions.

Reference replay:
`python ENFORCEMENT/taky_gate.py --replay ENFORCEMENT/replay_cases_v5.json`.

## 4.4B Architecture profile auto-activation — HARD LOCK

A material architecture/shared-core/OS-boundary/ownership move SHALL NOT depend on the caller remembering to opt into the `ARCHITECTURE_CHANGE` profile.

When any execution record declares one of the following material intents:
- `architecture_change_planned=true`;
- `shared_core_change_planned=true`;
- `os_boundary_change_planned=true`;
- `cross_domain_architecture_change_planned=true`;
- `ownership_move_planned=true`;

the deterministic gate SHALL require:
- `engineering_execution_profile_required=true`;
- `engineering_profile=ARCHITECTURE_CHANGE`.

Omission or a different profile => `RULE_NOT_APPLIED`.

This closes the activation gap between "the rule exists" and "the architecture-specific rule was actually selected for the action."

`MATERIAL ARCHITECTURE INTENT != OPTIONAL ARCHITECTURE PROFILE`.

## 4.4A Architecture owner/sharing boundary gate — HARD LOCK

Semantic ownership is defined by `MASTER/ENGINEERING_EXECUTION_PROFILE_PROTOCOL.md` under the `ARCHITECTURE_CHANGE` profile. This section defines the deterministic execution expression.

Before a material shared-core, OS split/merge, cross-domain common layer, ownership move, or common-capability extraction can pass the architecture execution gate, the engineering contract SHALL contain:
- non-empty `owner_map[]` with explicit `scope / owner`;
- non-empty `sharing_classification[]` using only `SHARED_TECHNICAL_PRIMITIVE / DOMAIN_OWNED_SEMANTIC / EXPLICIT_FEDERATION / NOT_SHARED`;
- `semantic_boundary_checked=true`;
- `authority_boundary_checked=true`;
- at least one usable `boundary_counterexamples[]` entry with `scenario / expected_boundary`;
- when a shared layer is proposed, `shared_layer_semantic_light=true`;
- no implicit cross-domain authority sharing;
- no semantic/authority sharing without explicit federation.

A shared authentication account, identifier, database, transport, event bus, storage engine or sync mechanism SHALL NOT by itself prove shared identity, role, permission, ownership, lifecycle or authority.

Violation:
- incomplete pre-structure boundary model ⇒ `RULE_NOT_APPLIED`;
- implicit cross-domain authority/semantic inheritance ⇒ `AUTHORITY_BOUNDARY_VIOLATION`.

This gate exists to prevent solution-first architecture where a plausible shared layer is proposed before ownership and non-shareable semantics are compiled.

Reference replay is included in `ENFORCEMENT/replay_engineering_profiles_v1.json`.

## 4.5 External-resource / hosting call budget gate — HARD LOCK

External hosting, deployment, production validation, paid API execution, quota-bearing preview creation, and repeated remote status polling are material side effects. They SHALL NOT be used as a substitute for lower-cost repository/branch/CI/runtime validation.

Default rule:
`LOCAL/BRANCH → CI/RUNTIME → ONE FROZEN CANDIDATE → EXTERNAL DEPLOY/VALIDATION`.

Required execution-record fields when applicable:
- `external_resource_action`;
- `external_resource_name`;
- `external_call_budget`;
- `external_call_count_for_same_goal`;
- `candidate_sha_frozen`;
- `same_external_call_repeated_without_new_evidence`;
- `deployment_attempted_before_candidate_frozen`;
- `lower_cost_local_validation_available`;
- `external_call_selected_before_local_closure`;
- for status polling: `external_status_poll`, `no_new_trigger_since_last_external_check`, `material_external_state_change_expected`.

Hard behavior:
- default budget for one deployment/preview goal is 1 external execution unless the governing workflow explicitly defines another budget;
- a second equivalent deploy/status call requires materially new evidence, a new trigger/state transition, or explicit override;
- if branch/CI/runtime validation can answer the question, repeated hosting calls are blocked;
- deployment before candidate SHA/build is frozen is blocked;
- polling an unchanged external state without a new trigger and without a material reason to expect change is blocked;
- a lower-impact compliant path SHALL be preferred over a quota/cost-bearing external side effect.

Violation ⇒ `RULE_NOT_APPLIED`; repeated violation after correction may additionally be `POST_CORRECTION_REOCCURRENCE`.

This rule applies even when the external tool is technically available and authorized. Tool availability does not imply that another call is justified.

`TOOL AVAILABLE != CALL JUSTIFIED`.
`STATUS CHECK != PROGRESS`.
`RETRY WITHOUT NEW EVIDENCE != VALIDATION`.
`HOSTING CALL != FREE SIDE EFFECT`.

Reference replay lives in `ENFORCEMENT/replay_cases_v5.json`.

## 4.3 Notion link-review execution gate — HARD LOCK

Semantic workflow ownership remains `OS/NOTION_OPS.md` (TKY-NOTION-001). This section only defines the auditable execution expression.

When an execution record sets `notion_link_review_required=true`, the deterministic gate SHALL verify at least:
- root/original source was attempted when applicable;
- material descendants were inventoried;
- material source-node discovered and dispositioned counts close;
- source graph is closed for the attempted/recovered scope;
- structured source-graph evidence is present in the governed runtime projection;
- analysis is complete;
- comparison is complete;
- complement/improvement is complete when material;
- the review record/evidence state was updated;
- database housekeeping was not substituted for the requested link/content review.
- a failed direct root fetch did not bypass an available governed recovered snapshot/body/Drive preservation path.
- Work launch readiness was based on a stable system-side inventory preflight (at least two reads), not on asking the user to run Work and report failures.
- high-link preserved records used for fallback have reachable archive contents, not merely a stored path string.

Missing Phase A source acquisition/closure ⇒ at least `OMISSION`.
Missing Phase B analysis/compare/improvement, or database-housekeeping-only substitution ⇒ at least `SUBSTITUTE_RESULT`.
If completion is claimed while either failure is present ⇒ `PREMATURE_PASS` through the existing completion gate.

Representative historical-failure and post-fix cases SHALL live in the replay fixtures.

`DATABASE CLEANUP ≠ NOTION LINK REVIEW`.
`NOTION SUMMARY ≠ SOURCE GRAPH CLOSURE`.
`SOURCE COLLECTION ≠ ANALYSIS / COMPARE / IMPROVE`.

Fresh-context recurrence validation for this command SHALL be system-side:
- zero prior conversation context;
- literal user input `노션검토`;
- no TAKY prefix required;
- expected route = Notion link-intelligence review of `📚 나의 링크`;
- Phase A + Phase B + review-record update required;
- structure-audit substitution rejected.

The user SHALL NOT be used as the default fresh-chat/Work tester when a repository replay can validate the contract. Hosted ChatGPT/Work automatic invocation remains a separate platform/runtime claim and SHALL stay `UNVERIFIED` unless directly evidenced by an available system-side runtime test.

`USER MANUAL SMOKE TEST ≠ REQUIRED REPOSITORY VALIDATION`.
`FRESH-CONTEXT REPLAY PASS ≠ HOSTED AUTO-INVOCATION VERIFIED`.

## 4.6 Engineering execution-profile gate — HARD LOCK

Semantic ownership remains `MASTER/ENGINEERING_EXECUTION_PROFILE_PROTOCOL.md` (TKY-ENGEXEC-001). This section defines only the auditable/mechanical expression.

When an execution record sets `engineering_execution_profile_required=true`, the record SHALL provide a known profile and a compact execution contract with:
- baseline evidence references;
- protected state;
- target delta;
- acceptance conditions;
- validation steps;
- regression scope;
- remaining unknowns;
- report mode.

Supported reusable profiles:
`REPAIR / ARCHITECTURE_CHANGE / DATABASE_MIGRATION / SECURITY_REVIEW / UI_IMPLEMENTATION`.

Selected profile-specific requirements SHALL be present and satisfied. The gate SHALL block at least:
- REPAIR that lacks failure evidence, a falsifiable root cause, minimum-sufficient delta, targeted retest or regression definition;
- repetition of the same failed repair approach under materially unchanged conditions without new evidence;
- ARCHITECTURE_CHANGE without current pattern/owner/interface impact inspection, or forced fragmentation without demonstrated benefit;
- DATABASE_MIGRATION without migration artifact, compatibility/access/referential/index-impact reasoning, migration test and rollback/forward-fix path;
- unjustified unconditional cascade deletion where lifecycle/history semantics were not checked;
- SECURITY_REVIEW driven by an arbitrary fixed finding count rather than evidence/applicable attack surface;
- SECURITY_REVIEW lacking attack-surface/control/finding/severity/regression evidence;
- UI_IMPLEMENTATION that treats an external design brand/style as project authority or fails to recover the applicable project reference/contract;
- concise user reporting that reduces internal validation or hides a material failed/unknown gate.

Violation uses the existing `RULE_NOT_APPLIED` / `STATE_CLAIM_MISMATCH` semantics rather than introducing a parallel failure taxonomy.

Reference replay:
`python ENFORCEMENT/taky_gate.py --replay ENFORCEMENT/replay_engineering_profiles_v1.json`.

`PROFILE SELECTED != PROFILE APPLIED`.
`SHORT REPORT != SHORT VALIDATION`.
`TEMPLATE BEST PRACTICE != PROJECT-SAFE EXECUTION`.

## 5. Human-approval gate — HARD LOCK

For promotions/actions whose governance requires human approval, the transition SHALL carry a recoverable approval record/token.

For lifecycle transitions into `MERGED` or `DEPLOYED`, approval evidence SHALL be bound to the exact transition context:
- task id;
- source state;
- requested destination state;
- concrete target reference (for example the reviewed commit/PR head or the deployment artifact/environment target);
- deterministic approval-context hash.

An approval for one target SHALL NOT be portable to a changed commit, changed merge target, changed deployment artifact, or different transition. A changed target requires fresh approval evidence.

Repository-side evidence such as `approver_ref` is a recoverable evidence reference unless the provider/runtime independently proves authenticated reviewer identity. TAKY SHALL NOT overclaim identity authentication from a string field alone.

If approval is required and not present, classify `HUMAN_APPROVAL_MISSING / FAIL`.
Malformed, stale, target-mismatched, transition-mismatched, or rejected approval evidence SHALL fail closed.
Names such as “Prime Agent”, “continual harness”, “lesson evolution”, “AI approval”, or “validated” SHALL NOT substitute for human approval.

## 5.1 Reference-only authority isolation gate — HARD LOCK

Notion pages, external AI proposals, web references, community templates, Handoffs, imported notes, and other non-canonical material SHALL enter as `REFERENCE_ONLY / CANDIDATE` unless an owning protocol explicitly gives them higher authority.

Promotion path:
`REFERENCE_ONLY → CANDIDATE → SOURCE_VALIDATED → LOCALIZED → IMPACT/REGRESSION_VALIDATED → HUMAN_APPROVED when required → CANONICAL_DELTA → CANONICAL_WRITE → POST_WRITE_VERIFY`.

A `REFERENCE_ONLY` input SHALL NOT directly control canonical execution logic. Promotion before required validation/localization/regression or approval ⇒ `AUTHORITY_BOUNDARY_VIOLATION`.

A textual `[STATUS: REFERENCE_ONLY / NON_EXECUTABLE]` header is useful evidence, but the header alone is not an enforcement mechanism. Structured authority metadata + validator enforcement is preferred.

## 6. State/history claim consistency gate — HARD LOCK

Narrative result/history wording SHALL NOT claim a higher state than the governing machine/state manifest supports.

If external validation remains `PENDING` or another material gate is not complete, wording may state completed local/canonical deltas but SHALL NOT present the entire validation program as unqualified complete.

Mismatch ⇒ `STATE_CLAIM_MISMATCH` and, when completion was claimed, `PREMATURE_PASS`.

## 7. Full-source/diff portability rule — HARD LOCK

For an offline/isolated review package that cites canonical files, use one of:
1. full canonical text snapshot; or
2. reconstructable diff plus its complete base snapshot/known base artifact.

Excerpt + blob/SHA alone is insufficient when the recipient lacks repository access and independent reconstruction is required. This rule applies to TAKY’s own validation packages as well as project handoffs.

## 8. Rule ownership / duplicate-definition gate

`MASTER/RULE_REGISTRY.json` is the machine-readable registry of normative owners. Rule semantics live in the declared owner. Other documents may reference or activate a rule but SHALL NOT establish a conflicting second owner.

Run:
`python ENFORCEMENT/rule_registry_lint.py`.

`VALIDATION_RULES.md` composes validation gates; it SHALL NOT silently become the semantic owner of taxonomy/recovery/intent/handoff rules already owned elsewhere.

## 9. Pre-response gate bridge

For TAKY-controlled runtimes/agents, the preferred enforcement chain is:

`USER REQUEST → EXECUTION CONTRACT/RECOVERY ACTION → PRE-RESPONSE RECORD → taky_gate.py → FAIL: corrective execution/block → PASS: user-visible response`.

This repository can define and test that bridge. A general ChatGPT conversation is not proven to invoke the validator automatically merely because the repository contains it.

`REPOSITORY ENFORCEMENT AVAILABLE ≠ LIVE RUNTIME AUTO-INVOCATION VERIFIED`.

## 10. CI / repository enforcement

The canonical repository SHOULD run deterministic replay, rule-registry lint, and syntax validation on relevant push/pull request changes. Bundle closure is run against actual generated handoff packages when such a package is produced; CI cannot validate a nonexistent runtime bundle.

CI success proves only the checks actually run. It does NOT prove live LLM behavior, external service state, deployment, or human-only judgment.

## 11. Enforcement evidence record

A recurrence-prevention claim SHALL identify canonical commit/ref tested, validator/fixture version, per-case result, remaining non-automatable boundary, and what the replay does/does not prove. Store completed canonical replay evidence under `HISTORY/`.

## 12. Fail-closed completion rule

If a material rule is designated executable but the enforcement mechanism was not run, failed to run, or lacks required evidence, TAKY SHALL NOT upgrade that rule to enforcement PASS.

Allowed wording includes:
- `RULE PRESENT / ENFORCEMENT NOT PERFORMED`;
- `DETERMINISTIC GATE PASS / LIVE RUNTIME UNVERIFIED`;
- `HUMAN APPROVAL PENDING`;
- `LIVE HEAD UNVERIFIED`.

Disallowed wording includes “재발 방지 완료” solely because prose was added, “최대 인수인계 완료” solely because ZIP/checksum exists, or “검증 완료” while governing state is still PENDING.


## 13. Conversation-to-System coverage gate — HARD LOCK

Conversation-derived canonical growth that claims coverage/compile completion SHALL satisfy TKY-C2S-001.

Machine-checkable baseline:
`python ENFORCEMENT/conversation_coverage_validator.py <coverage-ledger.json>`.

The validator checks, within the declared recovered scope:
- unique material atom IDs;
- required source pointer/content/type/disposition/destination;
- correction lineage via supersedes or affected targets;
- declared material/mapped counts;
- `UNMAPPED_MATERIAL = 0`;
- `SILENT_LOSS = 0`;
- `FALSE_CONVERGENCE = 0`;
- reverse-reconstruction booleans.

The validator does not prove semantic correctness of every atom, inaccessible source recovery, live LLM automatic invocation, or human approval. Those remain separately governed.

A prose statement such as "전체 반영" without a scoped coverage ledger/equivalent evidence SHALL NOT be treated as mechanically proven C2S coverage.

C2S coverage enforcement SHALL NOT require downstream execution-state evidence such as:
- implementation complete;
- CI pass;
- runtime/browser pass;
- deployment/production provenance;
- physical-device verification.

Those are separate claim domains. Their absence may keep downstream work OPEN, but SHALL NOT make a valid C2S coverage ledger fail.

Conversely, downstream verification success SHALL NOT substitute for missing C2S evidence. A deployed or device-verified implementation can still be C2S-incomplete if material atoms were omitted, falsely converged, or left unmapped.

`C2S COVERAGE PASS != IMPLEMENTATION PASS`.
`IMPLEMENTATION PASS != C2S COVERAGE PASS`.



## 14. C2S runtime composition bridge — HARD LOCK

For TAKY-controlled runtimes that perform conversation-derived governance/system writes, use:
`ENFORCEMENT/c2s_preflight_bridge.py`.

When the execution record sets `conversation_system_compile_required=true`, the bridge composes:
1. canonical preflight/evidence validation;
2. TKY deterministic execution gate;
3. TKY-C2S coverage validation.

Missing coverage record -> bridge FAIL.
Lossy/false-converged/unreconstructable coverage -> bridge FAIL.

Reference:
```bash
python ENFORCEMENT/c2s_preflight_bridge.py \
  --record ENFORCEMENT/fixtures/c2s_runtime_preflight_pass.json \
  --coverage-record ENFORCEMENT/fixtures/conversation_coverage_pass.json \
  --repo-root .
```

This is repository-controlled enforcement. Hosted native automatic interception remains separately unverified.


## 15. NotebookLM source-security / authority gate — HARD LOCK

NotebookLM recovery sources may be machine-checked with:
`python ENFORCEMENT/notebooklm_source_validator.py <source-registry.json>`.

The gate blocks at least:
- NotebookLM-eligible sources that were not content-checked;
- sources marked eligible without `SAFE_FOR_NOTEBOOKLM`;
- sources containing session/auth material from direct NotebookLM ingestion;
- NotebookLM output promoted above `REFERENCE_ONLY / EVIDENCE_ASSIST`;
- HANDOFF / DERIVED_ANALYSIS mislabeled as direct original source.

Representative actual pilot registry:
`HISTORY/2026-09-19_NOTEBOOKLM_PILOT01_SOURCE_REGISTRY.json`.

This gate validates declared metadata consistency. It does not prove semantic completeness of the underlying file, inaccessible-history recovery or consumer NotebookLM UI execution.


## 16. Saved-share transcript sanitization gate — HARD LOCK

Saved ChatGPT share-page HTML SHALL NOT be passed directly to NotebookLM when session/bootstrap/auth material is present.

Repository reference path:
```bash
python ENFORCEMENT/chatgpt_share_transcript_sanitizer.py ENFORCEMENT/fixtures/chatgpt_share_fixture.html -o /tmp/share.md
python ENFORCEMENT/chatgpt_share_transcript_validator.py /tmp/share.md
diff -u ENFORCEMENT/fixtures/chatgpt_share_expected.md /tmp/share.md
```

Expected-failure safety case:
```bash
python ENFORCEMENT/chatgpt_share_transcript_validator.py ENFORCEMENT/fixtures/chatgpt_share_unsafe.md
```
MUST fail.

The sanitizer/validator proves transcript extraction and declared security-pattern exclusion for the processed file. It does not prove semantic completeness outside that saved page's `linear_conversation`.

## 17. Production artifact / user-exposure authority gate — HARD LOCK

For any domain that produces a PREVIEW / FINAL / USER_FACING artifact, the authorized production path SHALL be explicit and mechanically checkable.

Core route:
TASK → AUTHORIZED ROUTER → AUTHORIZED ENGINE/EXECUTOR → PRE-USER VALIDATION → USER EXPOSURE GATE → OUTPUT.

ENGINE AVAILABLE + BYPASS USED = GOVERNANCE FAILURE.
NO PASS → NO SHOW.

Required structured fields when applicable:
- production_artifact_planned;
- artifact_class;
- authorized_production_route_required;
- authorized_production_route_used;
- one_off_implementation_used;
- forbidden_production_operation_used;
- pre_user_validation_required;
- pre_user_validation_passed;
- user_exposure_requested.

Rules:
- one-off/local workaround implementations may be used as EXPERIMENT/DIAGNOSTIC but SHALL NOT directly create PREVIEW/FINAL/USER_FACING output when an authorized engine/executor exists;
- a production result that used an explicitly forbidden production operation fails authority admission;
- user exposure before applicable pre-user validation passes is blocked;
- asking the user to discover defects that were mechanically detectable before exposure is USER_AS_QA, not HUMAN APPROVAL.

Reference-effect work additionally requires:
- reference_effect_required=true;
- reference_compile_trace_complete=true;
- reference_output_effect_validated=true.

Reference presence/citation alone does not prove utilization.

For source freshness/equivalence decisions:
DATE != CONTENT CHANGE.
Timestamp-only inference without content-equivalence evidence cannot establish content delta/staleness.

For handoff-driven continuation, material workflows SHOULD declare RESUME / RETROSPECTIVE / SURGERY.
SURGERY may supersede/deprecate a known-bad prior structure; Handoff does not force preservation of a flawed architecture.

Deterministic expression lives in ENFORCEMENT/taky_gate.py.
Representative replay: ENFORCEMENT/replay_cases_v6.json.

END
