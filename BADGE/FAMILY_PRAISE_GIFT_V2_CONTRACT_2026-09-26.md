# FAMILY PRAISE GIFT — FAMILY MEMBERSHIP / GIFT PERMISSION CORRECTION — 2026-09-26

## New direct user correction (overrides the Parent-only interpretation in PR #148)
**Family is not synonymous with Parent.** The family can include parents, grandparents, guardians, siblings and other relatives / family members. Relationship is profile information, not grant authority. A member may GIVE a praise badge or 1..5 gems per gift ONLY when a trusted family authority explicitly grants `FAMILY_PRAISE_GIFT`. Parent status alone is not a gift permission. Child/sibling status alone neither grants nor forbids it; permissions are family-policy decisions, never inferred from relationship. The recipient of this slice is still a verified Child within the same family; self-gifting and cross-family gifting are forbidden.

The prior explicit requirement that **Parent has no personal unearned/LOCKED Badge atlas** remains in force. A family gift-giver sees a gift-options surface, NOT their personal unearned badge collection. Child achievement collection remains child-scoped and distinct from a family praise gift inbox.

## Actual source reality
The current Ready main `netlify/functions/ready-family-auth-core.js` maps authenticated Identity accounts only to `PARENT` or `CHILD`; it does not yet expose validated grandparent/guardian/relative relationships or `FAMILY_PRAISE_GIFT` permission grants. A Node test that injects a trusted example session for a grandparent is NOT proof of live Ready Identity support. A real provider-verified family membership and an authoritative permission lookup must be integrated separately. Do not turn all existing `CHILD` accounts into authorized givers.

## V2 executable contracts
- `BADGE/family-praise-gift.js`: `TAKY_FAMILY_PRAISE_GIFT_V2`, family-member giver with verified server Identity session, authoritative live membership and an explicit action- and target-specific permission receipt. Request body cannot set family, giver, role, relation, permission or Award Ledger metadata. V2 requires `explicit_gift_action`; no legacy `explicit_parent_action` authority.
- `BADGE/family-praise-gift-journal.js`: `TAKY_FAMILY_PRAISE_GIFT_JOURNAL_V2`. Stores `giver_member_id`, receiver Child, family, kind, amount or separately approved family-praise badge ID, signed/idempotent history. File domain and HMAC domain are new V2 values, intentionally distinct from historical Parent-only V1 records. No silent V1 migration or data deletion.
- Legacy `parent-praise-gift.js` and `parent-praise-gift-journal.js` remain historical V1 compatibility assets, not the latest design authority for new family gifting. No production service is currently wired to either.
- Gift amount remains an integer **1 to 5 per gift**, not a daily, monthly or lifetime limit. The service and the journal each independently validate it.
- Successful Gift Journal append is **not** an immediate Gem Wallet balance credit and is NOT a child Achievement Award Ledger receipt, EXP, or graded learning evidence.
- Only `APPROVED_ACTIVE`, `FAMILY_PRAISE_BADGE`, `giftable=true` definitions are selectable; 60 historical working drafts remain inactive/unbound.

## Test and OPEN boundaries
V2 tests cover Parent, Grandparent, Guardian and an explicitly authorized Child sibling as example givers, plus a same-family relative without grant who is denied. Real relationship/permission verification must come from a trusted provider, not from any test object or browser form.
Also regress unauthenticated/fake session, missing origin, modified grant scope, self-gift, parent recipient, cross-family member, mixed gift fields, max-five gems, idempotency/restart, family-scoped signed journal and no automatic balance updates.

OPEN: actual Ready multi-relation family model and authenticated permission management; production service endpoint, durable multi-device storage, child Gem Wallet consumer, approved Family Praise Badge art/catalog and app UI. No deploy or historical badge activation.
