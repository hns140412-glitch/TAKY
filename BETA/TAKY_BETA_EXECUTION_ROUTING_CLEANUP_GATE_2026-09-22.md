# TAKY BETA EXECUTION ROUTING & CLEANUP GATE — 2026-09-22

Status: BETA CANDIDATE / PRE-EXECUTION GATE
Purpose: Freeze cleanup and execution-routing criteria before assigning Codex, Work, or another execution surface.

## 1. Core rule

Do not choose Codex or Work first.

Required order:
1. define the exact architecture/rewrite target;
2. classify what is CURRENT / LEGACY / HISTORY / BROKEN / UNKNOWN;
3. define cleanup and preservation rules;
4. estimate execution size and usage cost;
5. select the smallest sufficient executor;
6. execute only after the contract is implementation-ready.

`EXECUTOR CHOICE FOLLOWS SCOPE DEFINITION.`
`USAGE OPTIMIZATION != SCOPE SHRINKAGE.`

## 2. Cleanup target classes

### REMOVE FROM ACTIVE SURFACE
- stale headers presented as current;
- wrong revision/header combinations;
- broken local references;
- superseded owner pointers;
- stale boot pointers;
- duplicated active authority;
- dated runtime snapshots presented as current;
- obsolete terminology presented as active;
- dead validator assumptions;
- runtime paths that no longer resolve.

### PRESERVE AS HISTORY / LINEAGE
- old decisions still needed to understand why the system changed;
- superseded terms with migration significance;
- prior owner/location evidence;
- failure cases and regression witnesses;
- old runtime snapshots useful for comparison;
- decisions later corrected by user input.

### HOLD / REVIEW
- material meaning whose new owner/destination is unresolved;
- content that appears duplicated but may encode a distinct exception;
- legacy references still required for compatibility;
- stale-looking runtime behavior whose actual consumer impact is unknown.

## 3. Header and identity normalization gate

For every active document:
- filename identity must match active header identity OR declare explicit lineage alias;
- status must distinguish CURRENT / CANDIDATE / LEGACY / HISTORY;
- canonical path must resolve;
- current owner must resolve;
- revision labels must not imply authority they do not have;
- legacy aliases must not appear as current owner names.

## 4. Runtime-error reduction gate

Before implementation realignment:
- resolve broken paths;
- remove stale boot references;
- make owner pointers machine-resolvable;
- separate current state from historical snapshots;
- align runtime/orchestrator/validator path assumptions;
- minimize duplicated configuration;
- reduce one-failure-causes-global-skip workflow chains;
- isolate affected-domain checks;
- record failure fingerprints to block repeated identical failed routes;
- avoid deployment-dependent verification unless specifically required.

## 5. Usage review before executor selection

Estimate:
- repositories/files touched;
- likely code/document delta size;
- context volume;
- expected tool calls;
- test loops;
- browser/runtime loops;
- cross-repository dependency;
- expected retries;
- rollback complexity.

Classify:
- LOW
- MEDIUM
- HIGH
- VERY_HIGH

## 6. Executor routing

### Ordinary Chat / connectors
Use for:
- architecture analysis;
- source recovery;
- inventory;
- comparison;
- C2S mapping;
- precise small canonical/support edits;
- GitHub inspection and bounded metadata fixes.

### Codex
Use when:
- actual software/runtime implementation is required;
- codebase changes are bounded;
- acceptance criteria are already frozen;
- file/module scope is sufficiently known;
- focused tests can establish correctness.

Do not send Codex to rediscover architecture that TAKY can settle first.

### Work
Use when:
- multi-source/browser/file workflow is materially required;
- execution needs persistent multi-step browser/computer interaction;
- the task cannot be completed efficiently with connectors/ordinary Chat.

Do not use Work as a default orchestrator for repository work.

## 7. Contract readiness before dispatch

No Codex/Work dispatch until the task contract states:
- target outcome;
- active owner;
- exact scope;
- files/modules or bounded discovery surface;
- protected intent;
- C2S lossless constraints;
- forbidden changes;
- acceptance criteria;
- focused test requirements;
- regression boundary;
- stop condition;
- evidence to return.

## 8. Pre-device target

Execution may proceed through:
- BETA_REWRITTEN
- IMPLEMENTATION_REALIGNED
- CI_VERIFIED
- RUNTIME_VERIFIED
- INTEGRATION/BROWSER_VERIFIED
- PRE_DEVICE_CANDIDATE

Stop before:
- physical-device verification;
- production release unless separately approved;
- unnecessary Netlify invocation.

## 9. Success criteria

- active surfaces contain no known stale identity/header/pointer defects;
- current and historical state are separated;
- runtime references resolve;
- validator/runtime contracts agree;
- no known repeated identical blocked-path loop remains;
- usage routing is proportional;
- C2S reverse trace remains intact after cleanup;
- no protected intent is removed to make the system appear cleaner.
