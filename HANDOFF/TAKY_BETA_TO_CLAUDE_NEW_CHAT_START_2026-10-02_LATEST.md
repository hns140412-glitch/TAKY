# TAKY Beta → Claude Handoff / New Chat Start

Status: **BETA FROZEN / ALPHA NOT STARTED**  
Canonical repository: `hns140412-glitch/TAKY`  
Frozen Beta main SHA: `64ba56274d2f12f6745db4fa77eac792f4c41ab4`  
Date: 2026-10-02

## 0. What you are taking over

You are not continuing an existing Alpha.

You are receiving a **validated and adversarially hardened Frozen Beta** as the sole starting boundary for a new TAKY Alpha.

The user’s intended sequence is:

`BETA FIX → BETA FULL REVIEW → ADVERSARIAL DECISION-PATH ATTACK → DEFENSIVE HARDENING → REVALIDATE → BETA FROZEN → HANDOFF → ALPHA`

The Beta part is now complete at the frozen SHA above.

Do **not** reinterpret earlier work as permission to skip this boundary.

## 1. Highest operating doctrine

TAKY = TASK + KEY.

Dual slogan:
- **Think Again, Keep Your Key.**
- **Think Again, You’re The Key.**

Global execution cycle:

`HUMAN INTENT → THINK AGAIN → KEEP YOUR KEY → FIND A WAY / SOLVE → YOU’RE THE KEY → VERIFY / CORRECT / CONTINUE`

Hard invariants:
- `USER != DEBUGGER`
- `HUMAN AUTHORITY != HUMAN OPERATIONAL BURDEN`
- do not repeat a failed path under the same conditions;
- classify failure cause and switch to another lawful/authorized route when available;
- preserve meaning, ownership, provenance and latest user correction while changing methods.

## 2. Frozen Beta identity

Use exactly:

`64ba56274d2f12f6745db4fa77eac792f4c41ab4`

as the Beta source boundary.

The hardening was merged by PR #209.

Main post-merge verification at this SHA:
- TAKY Enforcement Replay: PASS
- integration-regression: PASS
- engineering-profile: PASS
- test: PASS

Do not silently advance the Beta boundary because a later file or branch exists.

## 3. What was attacked in Beta

The review intentionally attacked **decision pathways**, not only final states.

### A. Resume authority divergence

Risk:
- most governance paths used CURRENT-first resume;
- the Handoff protocol still contained wording that could be read as Handoff-first.

Defense:
- default resume is explicitly:
  `STATE → APPLICABLE OWNER → VERIFIED CURRENT → OPEN/NEXT → LIVE REVERIFY`
- Handoff is conditional recovery evidence only;
- Handoff Section 6 is scoped below the default CURRENT-first route;
- CI now checks resume-authority consistency.

### B. Approval bypass

Risk:
- lifecycle callers could pass:
  - `merge_approval_required=false`
  - `production_approval_required=false`

Defense:
- MERGED and DEPLOYED are now always human-approved transitions;
- per-call flags cannot weaken this hard boundary;
- bypass attempts fail closed;
- regression tests cover this.

### C. Premature canonical promotion

Risk:
- exact-target approval binding existed, but a system could still ask for approval at the wrong lifecycle moment;
- this allowed a technically valid approval to authorize a premature Alpha/main promotion.

Defense:
canonical promotion cannot even enter the HUMAN_APPROVAL stage unless all of the following are present:
- source boundary;
- decision lineage;
- exact promotion target;
- explicit prerequisite list;
- every prerequisite = PASS;
- every prerequisite has evidence.

The approval context hash includes promotion context.

### D. Rule Registry drift

Risk:
- `MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md` declared `TKY-CHECKPOINT-001`;
- Beta `RULE_REGISTRY.json` did not contain it;
- previous lint could remain green.

Defense:
- the existing rule ID was restored;
- no new Rule ID was invented;
- ACTIVE_OWNER-declared Rule IDs are now cross-checked against the machine registry;
- intentional `LEGACY_OPTIONAL` ownership remains permitted only when explicitly non-default.

### E. Snapshot freshness false confidence

Risk:
- structural validation of a dated CURRENT snapshot could be mistaken for live-current verification.

Defense:
- CURRENT remains a semantic resume pointer;
- dated snapshot ≠ live head;
- live-current claims require requery;
- resolver claim ceiling remains below live/deployment proof;
- CI checks this boundary.

### F. Hosted runtime enforcement gap

This remains intentionally **UNVERIFIED / CONTAINED**, not “fixed”.

Repository enforcement does not prove that hosted ChatGPT, Claude, or direct connector actions are automatically intercepted.

Therefore:
- never claim hosted automatic interception without evidence;
- do not assume repository validators ran merely because the rule exists;
- canonical promotion remains explicit human-approved;
- exact-target/context approval binding remains mandatory;
- Netlify/deployment remain HOLD unless separately authorized.

## 4. Canonical architecture rules to preserve into Alpha

Keep these semantics unless a deliberate Alpha decision explicitly supersedes them:

- `CURRENT != CANONICAL_OWNER`
- `HANDOFF != SOURCE OF TRUTH`
- `HANDOFF = RECOVERY EVIDENCE`
- `HISTORY = IMMUTABLE EVIDENCE, NOT DEFAULT RESUME SURFACE`
- one semantic owner per rule/meaning;
- logical CURRENT is namespace-scoped, not one giant global state;
- `REGISTRY_SNAPSHOT != LIVE_CURRENT_STATE`
- `CANDIDATE != MAIN_CANONICAL`
- `CANONICAL_SEMANTICS_CLOSED != RUNTIME_IMPLEMENTATION_CLOSED`
- validation evidence must not advance product/runtime state beyond what was actually proven;
- Learning Engine decides learning need/intensity; dated scheduling remains Planner/project-owned;
- merge and deployment are separate authorization gates.

## 5. Data/state model to inherit

Retain the 4-role architecture:

- RAW
- INDEX
- DETAIL
- CURRENT

Additional rules:
- OWNER is a semantic relationship, not a duplicate storage bucket;
- HISTORY is minimal immutable revision/evidence;
- CURRENT is a small logical resume surface;
- deep history should remain deep, execution surface light:
  **DEEP MEMORY — LIGHT EXECUTION**.

## 6. Default resume contract

Always resolve:

`STATE → SEMANTIC OWNER → VERIFIED CURRENT → OPEN/NEXT → LIVE EVIDENCE REVERIFY → CONTINUE`

Do not choose authority by:
- newest filename;
- largest REV/V;
- LATEST suffix alone;
- Handoff prose;
- remembered chat state;
- timestamp alone.

Use Handoff/history only when CURRENT is insufficient, ownership changed, portability is needed, or conflict reconstruction is required.

## 7. Important Beta evidence

Read these first:

1. `BETA_REVIEW/BETA_FROZEN_MANIFEST_20261002.json`
2. `BETA_REVIEW/BETA_ADVERSARIAL_AUDIT_20261002.json`
3. `BETA_REVIEW/BETA_DECISION_DEFENSE_MATRIX_20261002.json`
4. `MASTER/MASTER_FILE_REGISTRY.json`
5. `MASTER/RULE_REGISTRY.json`
6. `STATE.md`
7. `TAKY.md`
8. `MASTER/MASTER_LOGIC.md`
9. `MASTER/ENFORCEMENT_PROTOCOL.md`
10. `MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md`
11. `MASTER/CONVERSATION_CONTINUITY_PROTOCOL.md`
12. `MASTER/HANDOFF_PROTOCOL.md`

## 8. Earlier Alpha warning

PR #208 and the earlier `ALPHA/**` bootstrap are **historical / non-authoritative**.

They were created before the user clarified that Beta must first be fully fixed, reviewed, adversarially challenged, hardened and frozen.

The system was restored to Beta, then hardened through PR #209.

Therefore:
- do not resume PR #208;
- do not treat its ALPHA files as canonical input;
- do not cherry-pick them blindly;
- you may inspect them only as historical candidate material;
- any reuse requires a fresh comparison against Frozen Beta and an explicit Alpha design decision.

## 9. Alpha start rule for Claude

Create Alpha **from Frozen Beta SHA `64ba56274d2f12f6745db4fa77eac792f4c41ab4`**.

Do not mutate Frozen Beta in place.

Recommended first sequence:

1. load the Frozen Beta manifest and core governance owners;
2. reconstruct the exact protected invariants;
3. build an Alpha change thesis: what Alpha changes and why;
4. explicitly list KEEP / IMPROVE / REMOVE / REPLACE / OPEN;
5. attack the proposed Alpha decision pathways before implementation;
6. design defense controls before promotion;
7. create Alpha on a separate branch/namespace;
8. validate Alpha independently;
9. only request human canonical-promotion approval after all stated prerequisites PASS with evidence.

## 10. Alpha promotion prerequisite template

A canonical Alpha promotion request must include:
- exact Beta source boundary;
- exact Alpha target/head;
- decision lineage;
- full audit status;
- adversarial validation status;
- defense-hardening status;
- regression status;
- unresolved/contained risks;
- deployment status;
- explicit statement of what changes authority if approved.

No prerequisite may be silently omitted.

## 11. Non-goals / HOLD

Do not, merely because Alpha work starts:
- deploy;
- call Netlify;
- alter production;
- promote project feature branches;
- reopen CLOSED feature work without contradictory evidence;
- treat UI/Badge/Explorer feature work as part of TAKY Alpha governance unless explicitly brought into scope.

Current:
- Netlify = HOLD
- Deployment = HOLD

## 12. User working rules

- Prefer cost-free/local/repository paths.
- Do not use a paid API or usage-priced external route without prior cost disclosure and user approval.
- Do not make the user debug system-side problems.
- Do not repeat identical failures.
- Keep responses concise unless detailed evidence is specifically needed.
- Preserve originals; never silently replace approved/canonical evidence.
- When blocked, classify why and pursue another authorized route.

## 13. Handoff acceptance test

Before saying “Alpha ready to start”, confirm:

- Frozen Beta SHA matches exactly;
- Beta Frozen manifest is loaded;
- PR #208 is treated as historical only;
- CURRENT-first resume semantics are preserved;
- approval bypass protection is preserved;
- promotion prerequisite gate is preserved;
- Rule Registry consistency protection is preserved;
- snapshot/live claim boundary is preserved;
- hosted automatic interception is NOT claimed;
- deployment remains HOLD.

If any item is uncertain, mark it UNKNOWN/OPEN instead of inferring PASS.

## 14. First Claude command

Use this as the next-chat instruction:

> 최신 TAKY Frozen Beta `64ba56274d2f12f6745db4fa77eac792f4c41ab4`를 기준으로 Alpha 신규 설계를 시작해. 먼저 `BETA_REVIEW/BETA_FROZEN_MANIFEST_20261002.json`과 이 Handoff를 읽고, Beta의 보호 규칙·공격검수 결과·방어 게이트를 그대로 상속해. PR #208의 기존 Alpha는 historical candidate로만 취급하고 자동 재사용하지 마. Alpha는 별도 branch/namespace에서 신규 작성하고, KEEP/IMPROVE/REMOVE/REPLACE/OPEN 결정표를 먼저 만든 뒤 결정경로 공격검증과 방어설계를 거쳐 구현해. main 승격·배포·Netlify는 별도 사용자 승인 전 HOLD.

END
