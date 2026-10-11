# TAKY DESIGN / UI ASSET SOURCE PROTOCOL

Status: USER-CONFIRMED GLOBAL RULE / 2026-09-29 / applicable to all TAKY-governed conversations and work surfaces.
Rule ID: `TKY-ASSET-001`
Classification: GLOBAL INVARIANT for asset provenance and delivery; project-specific design and Visual ID authority remain with their actual owner.
Semantic owner: this protocol. Current binary storage/distribution authority is resolved by `OS/DRIVE_STORAGE_MAP.json`: HNS approved master -> SIEZEALL approved distribution -> device verified cache. Historical GitHub `TAKY-ASSETS` remains migration/catalog evidence and code/schema/manifest context, not current binary authority.
Related: `MASTER/MASTER_LOGIC.md`, `MASTER/UI_REFERENCE_PROTOCOL.md`, `MASTER/TRACEABILITY_PROTOCOL.md`, `MASTER/CONVERSATION_CONTINUITY_PROTOCOL.md`.

## 0. User decision — HARD LOCK
Whenever TAKY designs or implements **mockups, app UI, browser UI, PWA UI, shared illustrations, icons, badges, characters, animated/effect visuals or visual backgrounds**, registering every approved/reusable *original asset and its separately useful layers* in the current HNS approved asset master route is the **default part of the task**, not a separately requested afterthought. Current physical paths are resolved through `OS/DRIVE_STORAGE_MAP.json`; release-safe packages are distributed through SIEZEALL.

`IMAGE GENERATED != ASSET REGISTERED != UI IMPLEMENTED != BUILD VERIFIED != DEPLOYED`.

This obligation applies to new chat conversations, old chat continuations, implementation handoffs, ChatGPT, external executors and cross-app visual projects. Do not infer that it has mechanically entered the context of an already-open conversation unless that conversation loads the current owner or receives the new-chat directive.

## 1. Canonical ownership and storage
- Original asset binary, unflattened reusable layer, character Visual ID asset, image/animation master, asset metadata, usage rights and provenance are centrally stored and versioned in the HNS approved master route (`TAKY/20_PLATFORM/UI_SOURCE_AUTHORITY` for UI/source authority; other governed asset leaves keep stable IDs under the grouped layout).
- Organize by stable project/family, surface/type, asset or Visual ID and approved revision. Record a source manifest: logical asset ID, canonical path, source revision/hash, dimensions and format, layer roles/dependencies, license/consent status when relevant, approved visual authority, current status, and consumer pointers.
- Do not make a temporary local download, AI generation attachment, Drive document, screenshot, GitHub Action artifact, or app runtime output a second canonical asset source. Those are evidence, intake or derived outputs until centrally registered and verified.
- App repositories (`Ready-Set`, `Hide-Seek`, `Snap-Pop`, others) SHOULD retain code/schema/slot contracts and a compact pointer/manifest to the exact approved asset revision. Normal current delivery is HNS master -> SIEZEALL distribution package -> device verified cache; app-bundled binaries are limited to explicit factory/emergency fallback or code-coupled assets. A routine asset/data package refresh does not require a GitHub commit or Netlify redeploy unless code/schema/slot/rendering logic changes.
- Do not ship the entire central source repository or secrets/child original photo to a public PWA. Only release-required consented derivatives and applicable optimized variants are included. Shared original can have multiple authorized usage projections without duplicating ownership.

## 2. Design-to-UI execution sequence — HARD LOCK
`APPROVED MOCKUP / USER DIRECTION -> RECOVER ORIGINALS -> ASSET INVENTORY -> SOURCE/LAYER PREPARATION -> CENTRAL UPLOAD -> CHECKSUM / RIGHTS / VISUAL ID -> UI CODE BINDING -> RENDER + FUNCTION + RESPONSIVE COMPARISON -> REPORT`.

1. Before generation, inspect existing approved original/Visual ID and mark `PRESERVE / CHANGE_ALLOWED / NEW_REQUIRED`. A rejected sample or composite concept board must never silently become a production image source.
2. Create or edit only missing material while maintaining explicitly approved composition/painting style. For a layered UI, keep scenery, foreground, props/effects, logo/wood/parchment, profile child slot, selected crew, copy, facts/award values and interaction effects independently addressable where functionally applicable. A preview composite does not replace original layers.
3. Write binaries and metadata to the categorized HNS approved master route and verify the **actual master binary exists**, file count, hash, dimensions, alpha/transparency where expected, approved Visual ID and source provenance. Build the distribution manifest/hash gate before SIEZEALL publication. **Manifest-only registration does NOT pass asset completion.**
4. Bind UI components to exact asset ID/path/revision; preserve app-specific approved screen proportions, interactions and responsive/tablet rules. Render the real UI and compare with the approved design, not just HTML presence or synthetic fixture output. Only then claim the applicable completion level.
5. If any upload/credential/tool barrier remains, pursue another authorized route and explicitly report `ASSET_UPLOAD_OPEN`, with exact files, verified staging result and next viable step. Never report `UI_DONE`, `ASSET_REGISTERED` or `PWA_READY` because a ZIP or illustration was generated alone.
6. Do not require the user to be the routine debugger/uploader unless a genuine user credential/permission or local-system boundary cannot be crossed by available authorized tools. `USER != DEBUGGER`.

## 3. Asset-generation / runtime-behavior boundary — HARD LOCK

`ASSET GENERATION ENGINE != CHARACTER BEHAVIOR ENGINE`.

Canonical visual creation, derivative production, checksum/versioning and registry promotion belong to the asset-production side. Runtime character state, relationship, dialogue intent, pose/expression/prop selection and animation cues belong to the behavior side. Runtime behavior SHALL reference approved registry assets and SHALL NOT silently invoke image generation to satisfy ordinary scene changes.

The detailed shared contract is `OS/CHARACTER_ASSET_BEHAVIOR_PIPELINE.md`.

## 4. Scope, conflicts and exclusion boundaries
- This is an **asset management and design-to-code delivery standard**, not a universal demand that every text document or planning answer create visual files. It does not collapse document/A3 print output rules, browser business UI rules or mobile-app UI visual contracts into one layout rule.
- Existing approved visual sources and their Visual IDs are preserved; centralization does not authorize redrawing, forced migration, overwriting, flattening, re-licensing, public release or choosing new characters.
- Read-only/library/connected-app access limitations do not prove an original is absent. Record source pointers and recover it when possible.
- Explicit owner-approved exceptions (licensed resources that prohibit redistribution, private/child photo sources, temporary diagnostics, third-party-hosted assets) must be classified; store permission-safe derivatives or a metadata pointer only when appropriate. `CENTRAL DEFAULT != PUBLIC RAW UPLOAD`.
- No Netlify deployment, main merge of app runtime, public exposure, or asset promotion solely due to this governance decision. Honor project-specific gates and human approval.

## 5. Status reporting and handoff — HARD LOCK
Every material image/UI task reports these separately:
`DESIGN_REFERENCE_CONFIRMED | SOURCE_LAYER_READY | CENTRAL_ASSET_COMMITTED | ASSET_HASH_VERIFIED | RUNTIME_BOUND | UI_VISUAL_MATCH_VERIFIED | INTERACTION_VERIFIED | DEVICE_VERIFIED | RELEASED`.
Never convert a prior PASS in one dimension into another.

For new conversation/resume, read applicable TAKY current owner and this protocol if the task involves visual design, asset production or UI. The new-chat bootstrap reminder is:
> Latest TAKY standard: `TKY-ASSET-001` + current Drive route. Approved/reusable visual originals and individual layers go to the HNS approved master first; release-safe packages go through SIEZEALL distribution after manifest/hash verification; app code references stable asset/slot contracts and verified runtime copies. Original assets/Visual IDs are preserved. An image or ZIP alone is not UI implementation. Verify the actual binary master, binding, real render and interactions. USER != DEBUGGER.

END

## 6. 2026-10-07 Cloud / Drive route delta — CURRENT OVERRIDE

This section is a **targeted storage/delivery override only**. It does not redefine the original asset-production, Visual ID, UI verification, privacy or behavior-engine rules above.

User decisions confirmed after the Google Cloud/OAuth account review:
- the active Google Cloud project / OAuth Client ID / Drive API ownership is on the **SIEZEALL** account;
- users do **not** use HNS as a file-drop surface;
- user/shared input goes through the SIEZEALL-facing Drive surface;
- the single user reference inbox is the **SIEZEALL** Drive folder `00_INBOX_USER` (Drive ID `1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB`); the former HNS-side F: local-path binding is superseded and must not be used as SIEZEALL sync authority;
- the local collector watches the SIEZEALL inbox only after an actual SIEZEALL local-sync path is bound; until then it must HOLD rather than scan HNS. It stops after Mining dispatch; Indexing/Learning/Canonical promotion stay downstream;
- HNS remains the internal/admin master route;
- SIEZEALL remains the approved distribution/user-sync route;
- GitHub/Netlify usage should stay minimal: code/schema/slot-contract changes may require commit/deploy, while data/asset package refresh alone should not;
- Netlify is not allowed to infer or decide asset identity/binding from deployed filenames. Asset binding is resolved before distribution through manifest + hash verification;
- approved asset delivery is `HNS approved master -> manifest/hash gate -> SIEZEALL distribution package -> device verified cache`.

Historical `TAKY-ASSETS` remains migration/catalog evidence until reconciled. Do not mass-delete, re-upload or restructure historical binaries merely because this storage route changed.

The current routing owners are:
- `OS/DRIVE_STORAGE_MAP.json`
- `CURRENT/DESIGN_UI_ASSET_SOURCE_DEFAULT_2026-09-29.json`


## 7. 2026-10-07 Physical Drive path lock

The current physical Drive presentation layout is owned by `OS/DRIVE_STORAGE_MAP.json`. Historical flat-path or GitHub-binary wording does not override these current physical routes.

Current HNS asset/source route:
- approved UI source authority: `TAKY/20_PLATFORM/UI_SOURCE_AUTHORITY`
- common/platform data: `TAKY/20_PLATFORM/03_COMMON`
- learning/app asset project surface: `TAKY/10_DOMAINS/01_LEARNING/05_ASSETS`

Current SIEZEALL distribution route:
- approved update/distribution package surface: `TAKY/20_PLATFORM/03_UPDATES`
- user-sync data surface: `TAKY/20_PLATFORM/04_USER_DATA`

The root presentation is locked to:
`00_CONTEXT / 10_DOMAINS / 20_PLATFORM / 90_MAINTENANCE`.

`00_CONTEXT` stays directly under the TAKY root. Existing semantic leaf folder IDs remain stable; path consumers must resolve the current path from `OS/DRIVE_STORAGE_MAP.json` rather than reconstructing an old flat path.

For storage authority only, earlier references in this protocol that describe GitHub `TAKY-ASSETS` as the current binary master are superseded by the 2026-10-07 Drive route override. The provenance, Visual ID, separation-of-layers, hash, verification and USER != DEBUGGER requirements remain active.
