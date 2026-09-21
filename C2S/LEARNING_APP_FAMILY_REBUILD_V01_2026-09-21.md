# LEARNING APP FAMILY REBUILD ARCHITECTURE — 2026-09-21

Status: REBUILD_V01_STARTED

## Goal
Replace monolithic application composition while preserving already-verified domain logic and contracts.

## Non-negotiable architecture
App Shell
→ Domain Modules
→ State/Store
→ Runtime Services
→ Integration Adapters
→ UI Views
→ Persistence

Shared Technical Capability may include only semantic-light mechanisms:
- event envelope
- release/PWA lifecycle
- storage adapter patterns
- runtime diagnostics
- contract validation
- test harness patterns

Never commonize through the shared layer:
- user/family/org identity authority
- role/permission authority
- Learning Engine domain authority
- Planner allocation authority
- Language Memory authority
- Snap authorship/expression semantics

## Rebuild policy
1. Existing active product branches are evidence sources, not edit targets.
2. Rebuild happens only on dedicated rebuild branches.
3. No broad rebase over newer product work.
4. Preserve verified domain engines where possible.
5. Rebuild app composition and ownership boundaries before adding features.
6. Every migrated capability needs runtime regression before old path removal.
7. Old monolith remains fallback until replacement path reaches parity.
8. No device/production/deploy claims from static or browser-only evidence.

## Product-specific strategy

### Ready & Set
Preserve:
- Learning Master rules/contracts
- Planner domain rules that are already validated
- session contract semantics
- Learning App Family integration contract

Rewrite / split:
- app.js composition
- Planner data/domain/UI separation
- session UI composition
- schedule/assignment/planner/session feature modules

Target modules:
- shell/
- schedule/
- assignment/
- learning/
- planner/
- session/
- integrations/
- persistence/
- views/

### Hide & Seek
Preserve:
- verified language evidence model
- Memory Ladder semantics
- language-domain learning basis
- resolved Ready learning-context boundary
- OCR adapter boundary

Rewrite / split:
- app.js monolith
- capture UI/state coupling
- retrieval flow orchestration
- memory mutation vs rendering
- records composition

Target modules:
- shell/
- capture/
- vocabulary/
- retrieval/
- memory/
- language/
- integrations/
- persistence/
- views/

### Snap & Pop
Preserve:
- semantic writing/authorship guard
- learning context consumer
- vocabulary ownership contract
- voice boundary
- badge/crew domain contracts
- shared release/PWA/event contracts

Rewrite / split:
- app.js monolith
- direct DOM event wiring
- exploration state + rendering coupling
- writing/session composition
- crew/badge/records/family composition

Target modules:
- shell/
- exploration/
- writing/
- crew/
- badge/
- records/
- family/
- integrations/
- persistence/
- views/

## Migration acceptance
A migrated feature counts toward product implementation only if:
- STRUCTURE = migrated into target ownership module
- FUNCTIONAL = behavior implemented
- JOURNEY = reachable through real app flow
- UI_UX = user-facing state is coherent
- RUNTIME = browser E2E PASS
- DEVICE = separately verified when actually run

CODED alone is never product implementation completion.

## Baseline user-facing implementation estimate before rebuild
- Ready & Set: ~48%
- Hide & Seek: ~45%
- Snap & Pop: ~40%
- Family overall: ~44–48%

These are practical-use estimates, not code-presence scores.

END


## Rebuild execution checkpoint

Dedicated rebuild branches:
- Ready: `taky/ready-rebuild-v01-2026-09-21`
- Hide: `taky/hide-rebuild-v01-2026-09-21`
- Snap: `taky/snap-rebuild-v01-2026-09-21`

Active product branches remain untouched.

### Foundation implemented in all three apps
- `src/core/state-store.js`
- `src/shell/app-shell.js`
- `src/integrations/contract-gate.js`
- executable rebuild validator
- rebuild-only GitHub Actions workflow

Foundation exact-commit CI:
- Ready `215b31837358fdfa7c89b435cb4512fda63f1e0d`: PASS
- Hide `88399e41c59929dfe226085298d0718cec852de3`: PASS
- Snap `50a6af1857a994bb156f24abd4c1df233c0ddbcc`: PASS

### First domain extraction
Ready:
- `src/planner/planner-domain.js`
- `src/planner/outcome-policy.js`
- state mapping / session ownership / carry policy extracted.

Hide:
- `src/vocabulary/word-domain.js`
- `src/retrieval/retrieval-flow.js`
- word normalization / NEW-REVIEW inference / retrieval base phase machine extracted.

Snap:
- `src/exploration/exploration-session.js`
- `src/exploration/exploration-flow.js`
- exploration session shape / writing recovery / 3-step transition extracted.

Parity validation:
- Ready first domain parity commit `92f395f9c0335fa3c693361dd09fb3cea8a620cb`: PASS.
- Hide first domain parity commit `c2b9a0bb3103e6e431b6d9b1f2095d9220363669`: PASS.
- Snap first domain parity commit `9ee807001ff3b262a2865bb9ca5ebfd87582cdd2`: PASS.

Second flow extraction latest commits:
- Ready `578681c57c5dd37722a2fcffc7e8862d6dbd253e`: CI queued at checkpoint.
- Hide `880cd6f98a60d35a13389501e4ac2f3c0e83ec9b`: CI queued at checkpoint.
- Snap `1332d958bdc4a8b2bec93900dbe2dbdb2a840ea2`: PASS.

## Reporting rule during rebuild

Two percentages must stay separate:

1. EXISTING_PRODUCT_USABLE_IMPLEMENTATION
   - Ready baseline ~48%
   - Hide baseline ~45%
   - Snap baseline ~40%
   - family ~44–48%

2. REBUILD_MIGRATION_COMPLETION
   - counts only capabilities actually migrated into the new architecture and parity/runtime verified.
   - foundation scaffolding alone does not count as user-facing completion.
   - existing product percentage does not increase merely because shadow modules were created.

Next:
- wire one bounded production path per app into the new modules;
- preserve old path as fallback until parity;
- then begin removing monolith responsibilities.
