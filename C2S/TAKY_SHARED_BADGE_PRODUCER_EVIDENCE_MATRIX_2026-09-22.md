# TAKY SHARED BADGE PRODUCER / EVIDENCE MATRIX — 2026-09-22

Status: WORKING RECONCILIATION MATRIX
Companion: TAKY_SHARED_BADGE_SYSTEM_CANONICAL_2026-09-22.md

| Event family | Ready & Set | Snap & Pop | Hide & Seek | Minimum evidence | Weak proxy warning | Canonical status |
|---|---|---|---|---|---|---|
| SELF_START | PRIMARY | contextual | contextual | explicit start event + expected-window provenance | timestamp alone | RULE_REQUIRED |
| TIME_CREATION | PRIMARY | rare | rare | explicit plan/free-time delta + child action | elapsed time alone | RULE_REQUIRED |
| EXTRA_TASK | PRIMARY | supported | possible | explicit voluntary extra selection | completion count alone | STRONG_DIRECTION |
| FOCUS | PRIMARY | contextual | contextual | multi-signal + explicit/observable context | duration/idle alone | HOLD_FOR_RULE |
| RETURN_RECOVERY | PRIMARY | supported | PRIMARY | prior interruption state + explicit return/resume | reopen alone | RULE_REQUIRED |
| HELP_REQUEST | PRIMARY | PRIMARY | PRIMARY | explicit help action | hint shown automatically | STRONG |
| ERROR_DISCOVERY | possible | PRIMARY | possible | child-marked error + before/after artifact | model inference | STRONG |
| RETRY | supported | PRIMARY | PRIMARY | explicit retry after identifiable prior attempt | retry count alone | STRONG_DIRECTION |
| DEEP_THINKING | possible | PRIMARY | supported | explicit reflection artifact | long duration alone | STRONG |
| ISSUE_DURATION | Ready source candidate | contextual | contextual | not awardable by duration alone | duration alone | HOLD |
| SELF_EXPLANATION | supported | PRIMARY | PRIMARY | child-authored explanation artifact | answer correctness alone | STRONG_DIRECTION |
| PLAN_ADAPTATION | PRIMARY | contextual | contextual | explicit plan change or before/after plan artifact | schedule drift alone | RULE_REQUIRED |
| SPECIAL_BEHAVIOR | feature-specific | PRIMARY | feature-specific | feature-declared allowlisted action | generic novelty inference | STRONG |
| WRITING_EXPLORATION | possible | PRIMARY | N/A/contextual | child-authored completed expression event | text length alone | STRONG_DIRECTION |

## Producer contract

Each app producer must emit:
- local_event_id
- app_id
- event_family
- occurred_at
- provenance.source_event_id
- provenance.source_contract
- provenance.source_ref when available
- semantic-light payload

Each app producer must NOT emit:
- shared user/family/org identity
- badge award=true
- gem/EXP mutation authority
- mastery/ability/rank labels

## Consumer contract

Shared consumer must:
- dedupe on stable source event identity;
- preserve app provenance;
- reject unsupported families;
- keep candidate creation separate from award;
- keep catalog activation separate from observation;
- fail closed on malformed evidence;
- never convert missing data into a positive inference.

## App-specific gaps

### Ready & Set
Need:
- badge producer adapter;
- explicit event contracts for self-start/time-creation/return/plan-adaptation;
- mapping to Ready session/planner semantics without exporting private assignment content.

### Snap & Pop
Existing:
- observation runtime;
- explicit evidence runtime for ERROR_DISCOVERY / DEEP_THINKING / SPECIAL_BEHAVIOR;
- candidate runtime;
- catalog guard;
- shared envelope;
- visual compositor.

Need:
- remove any implication of family-wide ownership;
- complete cross-app consumer integration;
- canonical asset review.

### Hide & Seek
Need:
- replace legacy local achievement assumptions with shared producer adapter;
- map retry/recovery/help/self-explanation to evidence;
- preserve Hide learning semantics;
- do not import Snap gem/wish/blessing economy.

END
