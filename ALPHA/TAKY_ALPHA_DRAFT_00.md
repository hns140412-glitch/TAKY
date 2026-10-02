# TAKY ALPHA — NEW STRUCTURE DRAFT 00

Status: ALPHA / NEW WRITE / NOT YET CANONICAL  
Source boundary: Beta Frozen at `4af88d609d5b09fc673f342c77b7b6df33b9cf02`  
Rule: Alpha is rebuilt from the Frozen whitelist. It is not an append-only rewrite of Beta.

## 0. Purpose

TAKY Alpha keeps governance semantics durable while separating volatile operational state from semantic authority.

Core cycle remains:

`HUMAN INTENT → THINK AGAIN → KEEP YOUR KEY → FIND A WAY / SOLVE → YOU'RE THE KEY → VERIFY / CORRECT / CONTINUE`

Hard locks:
- USER != DEBUGGER
- HUMAN AUTHORITY != HUMAN OPERATIONAL BURDEN
- CURRENT != CANONICAL OWNER
- HANDOFF != AUTHORITY
- HISTORY != CURRENT
- CANDIDATE != MAIN CANONICAL
- RUNTIME/DEVICE/DEPLOY evidence are separate claim levels

## 1. Alpha authority model

Alpha uses four distinct classes only.

### A. OWNER
Durable semantic authority. One rule ID has one semantic owner.

Examples:
- TAKY governance
- Learning Engine semantics
- Exploration Crew semantics
- project product semantics

OWNER files must not carry mutable live PR/head/deploy state except immutable provenance references.

### B. CURRENT
Namespace-scoped operational state only.

Each namespace has exactly one logical CURRENT resolver target.
CURRENT may contain live heads, OPEN/HOLD, runtime evidence pointers, and next action.
CURRENT must declare freshness and verification timestamp.
A stale CURRENT is stale state, not stale semantics.

### C. EVIDENCE
Immutable or dated proof.

Includes:
- runtime/CI results
- audit packets
- historical checkpoints
- comparison reports
- recovery evidence

Evidence never becomes semantic authority by location or filename.

### D. HANDOFF
Recovery pointer only.

Handoff contains:
- namespace
- exact owner
- exact CURRENT
- first unresolved gate
- minimal evidence pointers

Handoff never restates broad mutable system truth.

## 2. Resolution order

`USER INTENT → TAKY ALPHA ROOT → RULE REGISTRY → SEMANTIC OWNER → NAMESPACE CURRENT → LIVE EVIDENCE VERIFY → ACTION`

For resume:

`STATE INDEX → NAMESPACE → OWNER → CURRENT → LIVE REVERIFY → FIRST OPEN GATE`

Do not select by:
- newest filename
- largest REV/V
- LATEST suffix
- handoff prose
- remembered status

## 3. State separation

Alpha removes duplicate mutable truth from durable owner documents.

Owner documents may say:
- what the state means
- who may mutate it
- which transitions are valid
- which evidence is required

Owner documents must not be the primary place for:
- current branch HEAD
- current PR head
- current CI run ID
- current deployment SHA
- current OPEN work count

Those belong in namespace CURRENT/EVIDENCE.

## 4. Namespace contract

Minimum namespaces at Alpha start:
- system
- learning_engine
- learning_data
- learning_family
- explorer_crew
- ready_set
- mobile_registry
- design_ui_assets

Each namespace record must define:
- semantic owner
- operational CURRENT
- evidence families
- mutation authority
- cross-namespace inputs/outputs
- OPEN/HOLD/UNVERIFIED
- live verification policy

## 5. Cross-layer ownership

TAKY governs flow; owners keep meaning.

Rules:
- shared technical capability may share mechanism, not domain authority
- Work and Learning identities/roles/permissions remain separately owned
- Learning Engine interprets evidence and pedagogical need; it does not own dated scheduling
- Planner allocates dates/capacity
- Ready executes assigned sessions
- specialist apps create domain evidence, not global authority
- platform adapters own mechanics only

## 6. Claim ladder

Alpha requires explicit claim level.

`WRITTEN → IMPLEMENTED → TESTED → RUNTIME_VERIFIED → INTEGRATED → DEVICE_VERIFIED → DEPLOYED → PRODUCTION_VERIFIED`

No upward inference.

Examples:
- CI PASS != production PASS
- merged != deployed
- deployed != device verified
- code exists != behavior verified
- CURRENT says CLOSED != evidence exists

## 7. Frozen Beta defects prevented by Alpha

Alpha explicitly prevents:
1. live PR/head state embedded across multiple durable documents;
2. dated CURRENT snapshots visually impersonating live truth;
3. Handoff status overriding repository reality;
4. semantic and operational status changing at different speeds inside one file;
5. historical LATEST documents re-entering authority resolution.

## 8. Alpha bootstrap gate

Alpha may become canonical only after:
1. rule-owner coverage check;
2. namespace CURRENT uniqueness check;
3. Beta whitelist traceability check;
4. no semantic loss against Frozen Beta KEEP set;
5. no stale state duplicated in OWNER files;
6. resume simulation from namespace CURRENT;
7. regression check on Work/Learning/Explorer/Ready ownership boundaries;
8. human approval for canonical promotion.

## 9. Initial Alpha status

- Beta Frozen: PASS
- Alpha structural draft: CREATED
- Alpha semantic migration: OPEN
- Alpha rule registry rebuild: OPEN
- Alpha namespace CURRENT rebuild: OPEN
- Alpha regression/self-validation: OPEN
- canonical promotion: HOLD
- Netlify/deployment: HOLD
