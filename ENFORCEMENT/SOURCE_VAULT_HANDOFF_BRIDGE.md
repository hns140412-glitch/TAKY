# SOURCE VAULT → TAKY central routing bridge (Draft)

This new-file-only bridge takes the existing local SOURCE VAULT reports/INCREMENTAL_QUEUE.json, MINING_INBOX_HANDOFF.json, and INCREMENTAL_SUMMARY.json and invokes TAKY's existing reference_intake_router.py for each still-pending Notion Page ID. It does not alter the current Windows installation or scheduler.

### Boundaries
- Fail closed for missing/mismatched handoff, duplicate IDs, count mismatches, or unexpected promotion/acknowledgment.
- Separate public URL candidates, URL conflicts, Notion child/container records, attachment-only records and unresolved locators.
- Remove tracking and ephemeral access tokens from output; preserve meaningful query selectors.
- Emit a local receipt with source input SHA-256 values. Snapshot folder name is a locator hint, not content verification.
- Do not re-query Notion, run the old full collector, mutate original files, acquire external pages, perform semantic Mining, write Indexing/CURRENT, or acknowledge pending work.
- The existing reference_acquisition_adapter.py remains the acquisition owner; the existing reference_intake_executor.py remains the receipt owner. Draft PR #167's independent Indexing owner-review requirement must not be bypassed. No canonical promotion.

### Validation
cd ENFORCEMENT && python -m unittest -v source_vault_handoff_bridge_test.py

A local 147-row rehearsal using the user-provided earlier queue and a matching synthetic handoff passed: 147 route decisions, 147 distinct source IDs, no input changes, no Mining/Indexing claim. This rehearsal uses an older pre-V2.2 queue snapshot; it does not prove current Windows runtime activation or latest URL fallback counts.

Only when separately authorized and provisioned, run read-only routing with:

python ENFORCEMENT/source_vault_handoff_bridge.py --reports "D:\Git PWA\TAKY-SOURCE-VAULT\reports"

Result is SOURCE_VAULT_ROUTER_RECEIPT.json, NOT a Mining completion receipt. No changes to 03:30 / 13:00 schedule, SOURCE VAULT root, Netlify or repository main.


### Deterministic local snapshot evidence stage
The companion source_vault_snapshot_evidence.py uses the *same validated handoff* and reads only the existing SOURCE VAULT data/notion_incremental/snapshots/<Page ID>/<fingerprint>/blocks.json under an explicitly supplied trusted vault root. It rejects claimed paths outside that root, invalid page/fingerprint locators, oversized/malformed snapshots, duplicate queue IDs and input changes. The output records actual raw-byte SHA-256 and block-ID-scoped text evidence, with attachment and child-page discovery gaps explicitly flagged. A directory fingerprint is merely an existing collector locator; the raw-byte hash proves only the bytes read.

Run (when authorized) from TAKY:
python ENFORCEMENT/source_vault_snapshot_evidence.py --vault-root "D:\Git PWA\TAKY-SOURCE-VAULT"

Result: reports/SOURCE_VAULT_SNAPSHOT_EVIDENCE.json. This is NOT a semantic Mining report, an acquired external URL page/attachment, an Indexing receipt, or an acknowledgment. It does not run on the user's PC merely because the GitHub Draft branch was updated. The evidence file contains extracted user content; keep it local and do not commit it into a public repository.

### Operational activation gate
The user-visible schedule is a separate local Windows task. This Draft does not modify that task, install the bridge, or configure a free local semantic runtime. A scheduled ChatGPT subscription is not a local autonomous model/API service. Before claiming end-to-end one-click Mining, require a verified local/authorized semantic analysis runtime, source-by-source analysis receipts, independent Indexing-owner verification, and unattended Windows run proof. Until then, preserve the pending queue.


### Bounded public URL acquisition (NEW, opt-in only)
ENFORCEMENT/source_vault_external_acquisition.py consumes the same validated queue/handoff/summary and calls the EXISTING reference_acquisition_adapter.acquire only for URL-property-derived PUBLIC_URL_CANDIDATE records, up to three network attempts per invocation. A bare body hyperlink, URL-property conflict, Notion container or signed Notion attachment is never automatically treated as the external original. Default is dry-run with no write or network. A specifically authorized local run may add immutable files under existing SOURCE VAULT/data/notion_incremental/acquired_external/ and append its local receipt under existing reports/SOURCE_VAULT_EXTERNAL_ACQUISITION.json. Repeated runs verify the prior raw bytes by SHA-256 before reusing; duplicate URLs share one capture with distinct per-page receipts. Access restrictions and unresolved sources remain review items. The original pending queue is not acknowledged or deleted. No software subscription or model API is implied.

Dry-run (no network): python ENFORCEMENT/source_vault_external_acquisition.py --vault-root "D:\Git PWA\TAKY-SOURCE-VAULT"
Explicit bounded run (not scheduled or installed by this Draft): python ENFORCEMENT/source_vault_external_acquisition.py --vault-root "D:\Git PWA\TAKY-SOURCE-VAULT" --execute-public --max-fetches 3

Still OPEN: installing/authorizing a supported local execution route, Notion child and attachment binary acquisition via an authorized Notion API context, actual semantic Mining model/runtime and its held-out tests, independent Indexing owner receipt (PR #167), and unattended schedule proof. Do not claim end-to-end completion from unit CI, and do not copy private SOURCE VAULT data into GitHub.

### STORAGE / WORK OS HARD LOCK (2026-09-28)
### Confirmed storage ownership — DATA vs DEV SOURCE/APP ASSET
- DATA STORAGE = existing authorized Google Drive folder OR a local data folder already synchronized/backed up through Google Drive. This includes collected originals, reference/source records, captures, attachments, Mining/Indexing datasets, private manifests/receipts, operational state and generated working/result files. A local folder is considered durable only after its actual sync/persistence is verified; local path alone != cloud copy. Reuse the existing synchronized folder directly; do not create a second mirror, new root or recursive sync route.
- GITHUB = development SOURCE REPOSITORY and approved APP/PWA ASSETS: application/PWA code, required UI/illustration/audio assets with appropriate rights, tests, build/deployment/configuration devices, and central governance code/contracts. It is NOT the data store. Do not exclude legitimate app source/assets simply because they are named "source" or "asset"; distinguish dev code and reviewed app assets from acquired RAW/reference data by role and provenance.
- CONNECTION = refer to persistent data via existing file ID/source ID/authorized local path and retrieve only what is needed for the current operation. No GitHub RAW upload, no Work OS wholesale ingest and no duplicated Google Drive/PC copy unless separately justified. Private data IDs/locators and secrets remain in authorized data storage or protected configuration, not a public commit.

- SOURCE VAULT retains RAW snapshots, acquired external originals, and local acquisition/extraction receipts. Google Drive may hold intentionally synchronized source files or archives under separate access controls; it is not automatically populated by this Draft.
- GitHub is an implementation surface, NOT a source/data warehouse. Product repositories retain PWA/app source code, deliberately approved app assets, UI/build/test/deployment configurations and necessary implementation contracts. Central TAKY retains its governance code/contracts/tests. SOURCE VAULT source records, source refs tied to user material, inventory, Mining/Indexing data, reports and receipts remain in existing authorized local/Drive storage; they are NOT GitHub contents merely because they are small or metadata-only. Never commit the vault directory, SOURCE_ARCHIVE, captures_v04, blocks.json snapshots, attachments, acquired_external, full extracted text, signed source URLs, Notion tokens, or personal data. Approved runtime assets for the PWA are distinct from captured source/reference images: do not publish RAW images by relabeling them assets.
- Indexing owns stable IDs, relations, versions, references and retrieval metadata; a locator/hash alone does not mean original content is in the index. Source details are fetched on demand from authorized storage. Mining obtains/uses source evidence without bulk GitHub publication.
- Work OS is a downstream, task-scoped consumer and is currently HOLD. No bulk ingestion/replication of SOURCE VAULT or whole index into Work OS, no automatic Work OS synchronization, and no policy-authority transfer. Once explicitly activated, pass only necessary verified source_refs, minimal evidence excerpts, permitted result artifact links and bounded summaries.
- REFERENCE != CANONICAL; MINED != INDEXED; INDEXED != WORK_OS_STORED. Never auto-commit generated or private files to GitHub. This Draft introduces no GitHub upload, Git LFS integration, repository-backed RAW storage or Work OS write path.

- A PWA may contain its necessary built-in/approved assets and code. A private reference source is not a PWA asset until rights, purpose, minimality and approved asset binding are established; use pointers to authorized local/Drive locations for normal source consumption. Do not upload entire corpora, create a new source repository, or duplicate sources into Work OS. GitHub PR/Actions logs/artifacts also must not publish source content or private source manifests.


### Cross-repository PWA source/data Git boundary — integration candidate

- Central guard implementation: `ENFORCEMENT/github_storage_boundary.py` with synthetic regressions in `ENFORCEMENT/github_storage_boundary_test.py`. Reusable GitHub composite action: `.github/actions/git-data-boundary/action.yml`.
- Action reads `git ls-files --cached -z` **in the invoking repository** and returns only category counts. It does not read source bytes, list sensitive paths in logs, write files, upload data, or decide whether a visual asset is approved. If a guarded data path has already been committed, `.gitignore` by itself does not untrack it; the guard must fail until a separately reviewed remediation.
- Central CI self-invokes the reusable action and checks that an authorized app image path is not blanket-ignored. App integrations should use an immutable central action commit SHA only after this Draft is approved. Avoid changing existing app branches/Netlify build behavior merely to trial a governance rule; install an app-specific `.gitignore` + CI reference only through its own reviewed branch.
- Repo-tree read-only check at the 2026-09-28 audit examined TAKY, TAKY-WORK-OS, Ready-Set, Hide-Seek and Snap-Pop `main`, plus six selected active Ready/Hide/Snap PR heads. No explicit guarded RAW/source-data patterns were observed in those **Git-tracked trees**. This is not a scan of all branches, ignored PC files, existing Drive sync state, source rights, or in-use PWA asset approval.
- The path policy is intentionally based on RAW source/data identity, not filename extension. A legitimate PWA image/audio/JSON asset stays eligible for GitHub; private research capture/reference imagery and source inventories remain in Google Drive or its verified local synchronized data folder. App assets with `reference` in a name require actual provenance/use review, not automatic deletion.
- No app repositories, main branches, Netlify deployment or PC data were modified in this central Draft. The reusable action is only a candidate until the PR is reviewed.
