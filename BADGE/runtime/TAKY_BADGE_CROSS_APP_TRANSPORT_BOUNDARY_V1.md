# TAKY Badge Cross-App Observation Transport Boundary V1
Date: 2026-10-02
Status: CONTRACT_ONLY_NOT_ACTIVE

## Decision
Badge source producers remain owned by Ready-Set, Hide-Seek, and Snap-Pop.
TAKY-MOBILE is NOT assigned as the badge runtime owner because its current role is command/handoff/canonical orchestration MVP, not badge event ingestion.

## Allowed input
Only a normalized TAKY_BADGE_SOURCE_OBSERVATION_V1 object may cross from an app producer into a future central badge transport.

Required fields:
- contract_version
- event_id
- app_id
- event_family
- behavior_code
- occurred_at
- source_contract_id
- evidence_ref
- explicit_child_action=true
- disposition=OBSERVATION_ONLY
- badge_award_authorized=false
- economy_mutation_authorized=false
- catalog_activation_allowed=false

## Transport responsibilities
A future central transport MAY:
1. validate exact schema and allowed app ID;
2. reject missing/unknown source contract IDs;
3. dedupe by app_id + event_id;
4. preserve source observation immutably;
5. attach transport receipt metadata;
6. pass only validated observations to the central matcher.

A future central transport MUST NOT:
- invent or enrich behavior semantics;
- infer child intent;
- convert legacy recordBadgeEvent payloads;
- activate badges;
- award economy/rewards;
- rewrite source evidence;
- use elapsed time, score, silence, attempt count, AI inference, or parent guess as substitute evidence.

## Matcher handoff
The matcher input must preserve the exact tuple:
- appId
- eventFamily
- behaviorCode
- sourceContractId
- explicit_child_action=true

The transport is not allowed to loosen, normalize-away, or alias any tuple field.

## Dedupe
Primary dedupe key:
app_id + event_id

If an identical key arrives again:
- return the original receipt;
- do not create a second matcher input;
- do not create a second award candidate.

If the same event_id arrives with conflicting app_id or payload:
- FAIL CLOSED;
- preserve conflict evidence;
- do not forward to matcher.

## Runtime ownership
Current state:
- Ready-Set producer runtime: EXISTS
- Hide-Seek producer runtime: EXISTS
- Snap-Pop producer runtime: EXISTS
- Central badge transport runtime: NOT IMPLEMENTED
- Central immutable observation ledger: NOT IMPLEMENTED
- Central matcher runtime: CONTRACT EXISTS, cross-app runtime transport not yet proven
- Badge activation/economy authority: NOT GRANTED

## Implementation gate
Before transport runtime can be marked PASS:
1. explicit repository/runtime owner must be selected;
2. immutable observation storage contract must be defined;
3. exact-schema validator implemented;
4. dedupe/conflict tests implemented;
5. one observation from each producing app proven E2E into matcher input;
6. no badge activation/economy mutation during transport QA;
7. human approval still required separately for active=true.

## Invariants
- source producer QA remains 15/60 until new producer tests pass;
- active remains 0/60;
- deployment remains HOLD;
- this contract does not authorize TAKY-MOBILE or any other repo as runtime owner.
