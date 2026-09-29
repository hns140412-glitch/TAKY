# TAKY DESIGN / UI ASSET SOURCE PROTOCOL

Status: USER-CONFIRMED GLOBAL RULE / 2026-09-29 / applicable to all TAKY-governed conversations and work surfaces.
Rule ID: `TKY-ASSET-001`
Classification: GLOBAL INVARIANT for asset provenance and delivery; project-specific design and Visual ID authority remain with their actual owner.
Semantic owner: this protocol. `TAKY-ASSETS` is the canonical binary source repository; app repos contain source pointers and verified build/staging copies only.
Related: `MASTER/MASTER_LOGIC.md`, `MASTER/UI_REFERENCE_PROTOCOL.md`, `MASTER/TRACEABILITY_PROTOCOL.md`, `MASTER/CONVERSATION_CONTINUITY_PROTOCOL.md`.

## 0. User decision — HARD LOCK
Whenever TAKY designs or implements **mockups, app UI, browser UI, PWA UI, shared illustrations, icons, badges, characters, animated/effect visuals or visual backgrounds**, storing every approved/reusable *original asset and its separately useful layers* in the central GitHub **`hns140412-glitch/TAKY-ASSETS`** asset folder/registry is the **default part of the task**, not a separately requested afterthought.

`IMAGE GENERATED != ASSET REGISTERED != UI IMPLEMENTED != BUILD VERIFIED != DEPLOYED`.

This obligation applies to new chat conversations, old chat continuations, implementation handoffs, ChatGPT, external executors and cross-app visual projects. Do not infer that it has mechanically entered the context of an already-open conversation unless that conversation loads the current owner or receives the new-chat directive.

## 1. Canonical ownership and storage
- Original asset binary, unflattened reusable layer, character Visual ID asset, image/animation master, asset metadata, usage rights and provenance are centrally stored and versioned in `TAKY-ASSETS`.
- Organize by stable project/family, surface/type, asset or Visual ID and approved revision. Record a source manifest: logical asset ID, canonical path, source revision/hash, dimensions and format, layer roles/dependencies, license/consent status when relevant, approved visual authority, current status, and consumer pointers.
- Do not make a temporary local download, AI generation attachment, Drive document, screenshot, GitHub Action artifact, or app runtime output a second canonical asset source. Those are evidence, intake or derived outputs until centrally registered and verified.
- App repositories (`Ready-Set`, `Hide-Seek`, `Snap-Pop`, others) SHOULD retain a compact pointer/manifest to exact central revision and use pinned, integrity-checked **derived deployment copies** in their own `assets/` output. These compiled copies are necessary for offline PWA / Netlify, but are not independent editable originals.
- Do not ship the entire central source repository or secrets/child original photo to a public PWA. Only release-required consented derivatives and applicable optimized variants are included. Shared original can have multiple authorized usage projections without duplicating ownership.

## 2. Design-to-UI execution sequence — HARD LOCK
`APPROVED MOCKUP / USER DIRECTION -> RECOVER ORIGINALS -> ASSET INVENTORY -> SOURCE/LAYER PREPARATION -> CENTRAL UPLOAD -> CHECKSUM / RIGHTS / VISUAL ID -> UI CODE BINDING -> RENDER + FUNCTION + RESPONSIVE COMPARISON -> REPORT`.

1. Before generation, inspect existing approved original/Visual ID and mark `PRESERVE / CHANGE_ALLOWED / NEW_REQUIRED`. A rejected sample or composite concept board must never silently become a production image source.
2. Create or edit only missing material while maintaining explicitly approved composition/painting style. For a layered UI, keep scenery, foreground, props/effects, logo/wood/parchment, profile child slot, selected crew, copy, facts/award values and interaction effects independently addressable where functionally applicable. A preview composite does not replace original layers.
3. Write binaries and metadata to categorized `TAKY-ASSETS` folder and verify **actual GitHub content exists**, file count, hash, dimensions, alpha/transparency where expected, approved Visual ID and source provenance. **Manifest-only commits do NOT pass asset completion.**
4. Bind UI components to exact asset ID/path/revision; preserve app-specific approved screen proportions, interactions and responsive/tablet rules. Render the real UI and compare with the approved design, not just HTML presence or synthetic fixture output. Only then claim the applicable completion level.
5. If any upload/credential/tool barrier remains, pursue another authorized route and explicitly report `ASSET_UPLOAD_OPEN`, with exact files, verified staging result and next viable step. Never report `UI_DONE`, `ASSET_REGISTERED` or `PWA_READY` because a ZIP or illustration was generated alone.
6. Do not require the user to be the routine debugger/uploader unless a genuine user credential/permission or local-system boundary cannot be crossed by available authorized tools. `USER != DEBUGGER`.

## 3. Scope, conflicts and exclusion boundaries
- This is an **asset management and design-to-code delivery standard**, not a universal demand that every text document or planning answer create visual files. It does not collapse document/A3 print output rules, browser business UI rules or mobile-app UI visual contracts into one layout rule.
- Existing approved visual sources and their Visual IDs are preserved; centralization does not authorize redrawing, forced migration, overwriting, flattening, re-licensing, public release or choosing new characters.
- Read-only/library/connected-app access limitations do not prove an original is absent. Record source pointers and recover it when possible.
- Explicit owner-approved exceptions (licensed resources that prohibit redistribution, private/child photo sources, temporary diagnostics, third-party-hosted assets) must be classified; store permission-safe derivatives or a metadata pointer only when appropriate. `CENTRAL DEFAULT != PUBLIC RAW UPLOAD`.
- No Netlify deployment, main merge of app runtime, public exposure, or asset promotion solely due to this governance decision. Honor project-specific gates and human approval.

## 4. Status reporting and handoff — HARD LOCK
Every material image/UI task reports these separately:
`DESIGN_REFERENCE_CONFIRMED | SOURCE_LAYER_READY | CENTRAL_ASSET_COMMITTED | ASSET_HASH_VERIFIED | RUNTIME_BOUND | UI_VISUAL_MATCH_VERIFIED | INTERACTION_VERIFIED | DEVICE_VERIFIED | RELEASED`.
Never convert a prior PASS in one dimension into another.

For new conversation/resume, read applicable TAKY current owner and this protocol if the task involves visual design, asset production or UI. The new-chat bootstrap reminder is:
> Latest TAKY standard: `TKY-ASSET-001`. Approved/reusable visual originals and individual layers go to GitHub `TAKY-ASSETS` first; app repos reference the exact source revision and hold only verified deployment copies. Original assets/Visual IDs are preserved. An image or ZIP alone is not UI implementation. Verify the actual binary upload, binding, real render and interactions. USER != DEBUGGER.

END
