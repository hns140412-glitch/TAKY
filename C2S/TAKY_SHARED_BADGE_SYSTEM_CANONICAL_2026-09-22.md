# TAKY SHARED BADGE SYSTEM CANONICAL — 2026-09-22

Status: CANONICAL CANDIDATE / CROSS-APP RECONCILIATION
Scope: Ready & Set / Snap & Pop / Hide & Seek / future learning apps
Authority order: latest direct user correction → TAKY governance → this canonical → app masters → app runtime evidence.

## 1. Product role

Badge is a **shared process/experience collection axis** across the learning-app family.

It is not owned by one child app as a product economy.
Each app may produce badge-relevant experience evidence, but no app may silently convert local events into family-wide badge awards.

Badge records meaningful learning/process moments including:
- self-start;
- time creation;
- extra task;
- focus;
- return/recovery;
- appropriate help request;
- error discovery;
- retry;
- deep thinking;
- self-explanation;
- plan adaptation;
- special behavior;
- writing/exploration behavior;
- future source-validated families.

Badge is not:
- Character level;
- EXP;
- Snap gem/wish economy;
- affinity;
- world state;
- mastery;
- leaderboard;
- power;
- punishment/streak pressure.

## 2. Canonical pipeline

APP LOCAL ACTION
→ LOCAL OBSERVATION
→ EVIDENCE CONTRACT
→ TAKY_BADGE_EXPERIENCE_EVENT_V1
→ CANDIDATE MATCH/PROPOSAL
→ REVIEW
→ CANONICAL CATALOG ACTIVATION
→ BADGE INSTANCE / PROGRESS
→ PRESENTATION SURFACE

Hard rule:
OBSERVATION != BADGE AWARD.

Shared event envelope must not carry award/economy authority.

## 3. Ownership

### TAKY shared layer owns
- event-family vocabulary;
- shared event envelope;
- cross-app provenance;
- dedupe/idempotency rules;
- candidate-review-activation governance;
- canonical catalog status;
- cross-app progress semantics;
- migration policy;
- shared visual contract;
- collection IA contract.

### App local layer owns
- raw local action;
- local context;
- local evidence artifacts;
- local privacy/identity;
- app-specific producer adapters;
- child-facing contextual acknowledgement where allowed.

### Apps do not own
- family-wide award authority;
- shared catalog activation;
- cross-app identity/role/permission authority;
- conversion of badge into EXP/gem/affinity/power.

## 4. Identity boundary

Shared badge event remains semantic-light.

Do not put shared user/family/org identity into the technical envelope.
Identity binding happens in the authorized owning layer.

Current invariant:
identity_scope = APP_OWNED_NOT_SHARED
role_scope = APP_OWNED_NOT_SHARED
permission_scope = APP_OWNED_NOT_SHARED

## 5. Evidence classes

### A. DIRECT_ACTION evidence
May be strong enough when the child explicitly performs the action:
- explicit help request;
- explicit extra task selection;
- explicit retry;
- explicit reflection;
- explicit self-correction;
- explicit plan change;
- explicit special action.

### B. ARTIFACT_CHANGE evidence
Requires before/after or equivalent artifact provenance:
- error discovery;
- correction;
- revision;
- self-explanation;
- plan adaptation when inferred from changed plan.

### C. TEMPORAL/BEHAVIORAL evidence
Requires conservative treatment:
- focus;
- issue duration;
- return/recovery;
- time creation;
- self-start.

Elapsed time, retry count, idle time, silence, score or AI inference alone must never prove ability/trait.

### D. COMPOSITE evidence
Some badge candidates may require multiple weak signals plus one explicit action/artifact.
No composite rule is active until canonical review.

## 6. Candidate / activation rule

Historical badge names and trigger wording are recovery material, not automatic active rules.

New candidate:
- must have candidate_id;
- one or more event families;
- evidence event IDs;
- reason/provenance;
- REVIEW_REQUIRED;
- active=false;
- awardAuthorized=false.

Activation requires:
- canonical name approved;
- evidence rule approved;
- dedupe/repeat rule approved;
- progression rule approved;
- display wording approved;
- regression check against score/power/economy coupling.

## 7. Existing ~60 historical catalog

Direction confirmed:
- launch-scale approximately 60;
- expandable from observed child activity.

Current status:
- historical names/triggers = WORKING DRAFT;
- no bulk auto-activation;
- names may be retained, merged, split, renamed or retired after evidence review;
- original source wording/provenance must be preserved.

## 8. Progression visual contract

Recovered visual direction is preserved:

- circular badge;
- hand-drawn/pastel illustration;
- center visually stronger, outer edge softer/faded;
- child Profile Character is protagonist;
- stable child identity;
- theme changes expression, not identity;
- Green → Blue → Red → Gold → Platinum;
- 1–5 gem-star growth marks on upper semicircle.

Composition:
COMMON_BADGE_ART
+ CHILD_IDENTITY_LAYER
+ THEME_EXPRESSION_LAYER
+ BADGE_GROWTH_LAYER

Theme expression is cosmetic only.

## 9. Currency visual separation

Badge growth gem-stars are NOT Snap Wish Gems.

Mandatory design distinction:
- different asset family;
- different silhouette and/or framing;
- different motion;
- different naming;
- no spend affordance on badge growth marks.

Shared canonical name:
BADGE_GROWTH_MARK

Snap currency:
SNAP_WISH_GEM

## 10. App producer roles

### Ready & Set — primary candidate families
SELF_START
TIME_CREATION
EXTRA_TASK
FOCUS
RETURN_RECOVERY
HELP_REQUEST
PLAN_ADAPTATION
TASK_EXECUTION-derived future family only if approved.

### Snap & Pop — primary candidate families
HELP_REQUEST
ERROR_DISCOVERY
RETRY
DEEP_THINKING
SELF_EXPLANATION
SPECIAL_BEHAVIOR
WRITING_EXPLORATION
EXTRA_TASK
RETURN_RECOVERY where explicit.

### Hide & Seek — primary candidate families
RETURN_RECOVERY
RETRY
HELP_REQUEST
ERROR_DISCOVERY where child-evidenced
SELF_EXPLANATION
DEEP_THINKING / inference-reflection only when explicit
SPECIAL_BEHAVIOR if feature-declared.

No app family list is exclusive; producers require evidence contracts.

## 11. Display surfaces

Shared badge system does not imply one giant dashboard.

Allowed surfaces:
- contextual earned/progress acknowledgement;
- profile/character collection;
- dedicated badge collection;
- growth surface preview;
- record/history linkage.

Open:
- canonical primary collection destination;
- intro/profile ownership;
- badge-title relationship.

Until resolved:
- app-specific preview may exist;
- no app may present itself as sole owner of the entire family badge collection.

## 12. Anti-pressure rules

Forbidden:
- streak loss;
- badge removal due to absence;
- shame copy;
- comparative leaderboard;
- rarity/gacha framing;
- ability ranking;
- EXP/gem conversion;
- hidden pressure to farm badges.

Badge should feel like a record of lived learning moments, not a performance score.

## 13. Current known gaps

1. Ready shared producer adapter — OPEN.
2. Hide shared producer adapter — OPEN.
3. Cross-app aggregator/consumer — OPEN.
4. Canonical dedupe/repeat rules — OPEN.
5. Active catalog membership — OPEN.
6. Old observation migration — OPEN.
7. Final collection IA — OPEN.
8. Badge-title relationship — OPEN.
9. Canonical reviewed art asset set — OPEN.
10. Physical-device visual verification — NOT_RUN.

## 14. Regression locks

- Snap's local badge runtime is evidence/reference, not family-wide ownership.
- Hide legacy badge/reward assets are not automatically canonical.
- Ready historical badge motifs are lineage evidence, not automatic current UI.
- no active rule may infer child ability from weak proxies.
- no UI may imply all 60 drafts are currently earnable.

END
