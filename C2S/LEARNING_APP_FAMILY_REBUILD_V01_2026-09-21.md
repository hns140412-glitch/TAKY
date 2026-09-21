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
