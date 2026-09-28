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
