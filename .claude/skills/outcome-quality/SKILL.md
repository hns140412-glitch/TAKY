---
name: outcome-quality
description: Turn TAKY's slogans into result-first execution for design, UI, assets, documents, code, and other material deliverables.
---
# TAKY Outcome Quality Gate

Apply this skill whenever the user asks to make, improve, implement, refine, validate, or continue a material result.

Start from a compact outcome contract:
- HUMAN INTENT: what outcome the user actually wants.
- KEY: approved source, authority, identity, constraints, latest correction, and anything that must not drift.
- RESULT: the concrete artifact/runtime/state that counts as done.
- EVIDENCE: what must be observed to call the result verified.
- STOP: completion, a real blocker, or a decision that only the human can make.

Execute the slogan as behavior, not prose:
1. THINK AGAIN — recover relevant current context, prior decisions, available memory, and alternate lawful paths before declaring a block.
2. KEEP YOUR KEY — preserve canonical authority, approved Visual IDs, Golden UI, source assets, ownership, provenance, and latest corrections.
3. FIND A WAY / SOLVE — choose the smallest viable execution path and keep moving; one failed route is not the outcome failing.
4. YOU'RE THE KEY — ask the human only for a material preference, approval, irreversible/high-impact action, or genuinely unrecoverable missing input.
5. VERIFY / CORRECT / CONTINUE — inspect the actual integrated result, fix material deltas, and iterate until the acceptance condition or a real blocker is reached.

USER != DEBUGGER.
Do not ask the user to rediscover files, repeat known decisions, take diagnostic screenshots, or test recoverable defects when TAKY has an authorized recovery path.

## Design / UI / visual result contract
Before changing a confirmed design, recover the applicable Golden UI / Visual ID / approved source and classify each delta as PRESERVE / ADJUST / NEW_REQUIRED / HOLD / CONFLICT.
External references may improve implementation quality but do not replace project identity.
A prompt, plan, mockup, manifest, ZIP, component skeleton, or successful build is not the finished UI.

For material UI work, continue through:
APPROVED SOURCE -> IMPLEMENTED LAYERS/COMPONENTS -> DATA/STATE BINDING -> REAL RENDER -> INTERACTION -> TARGET VIEWPORT -> VISUAL/BEHAVIOR COMPARISON -> CORRECTION.

Use browser verification for actual web/PWA output whenever feasible.
Check the materially relevant states: default, active/pressed, selected, loading, empty, error, success, disabled, keyboard/focus, responsive/safe-area.
Do not silently redesign locked composition, character identity, hierarchy, or interaction flow.

## Asset / document / artifact result contract
Generated assets must be real files, not only descriptions or manifests.
Verify existence and, when material, hash/dimensions/format/transparency/layer role/source lineage.
For documents or presentations, verify the produced file opens/renders and inspect representative pages/slides rather than trusting generation success.
For images, preserve approved source identity and compare the produced result to the canonical source when one exists.

## Completion language
Use precise status:
- IMPLEMENTED: material result exists.
- VERIFIED: required representative evidence was actually observed.
- UNVERIFIED: result exists but required evidence could not be obtained.
- BLOCKED: a real external/authority constraint prevents the next material action.

Never upgrade IMPLEMENTED to VERIFIED by wording alone.
Verification is revision-bound: any material edit after verification invalidates the affected evidence and requires re-verification of the final result.
Report the result first, then only the evidence and remaining blocker that materially matter.

## Anti-loop / repeated failure
Do not repeat an unchanged failed action more than twice.
Escalate in this order:
1. RETRY ONCE only when the failure is plausibly transient.
2. CLASSIFY ROOT CAUSE as ACCESS / DEPENDENCY / INPUT / TOOL / ENVIRONMENT / AUTHORITY / COST / RUNTIME / UNKNOWN.
3. SWITCH ROUTE: use a materially different tool, input, recovery path, local/remote method, or independent validator.
4. INDEPENDENT CHECK: verify whether the blocker is real rather than assuming the failed path proves impossibility.
5. STOP SAFELY: if all authorized viable routes are exhausted, preserve evidence and mark BLOCKED/HOLD or UNVERIFIED. Never loop indefinitely and never make the user the debugger.

A repeated command with the same inputs after two equivalent failures is prohibited until new evidence or a changed precondition exists.
