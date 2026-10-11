---
name: intent-router
description: Convert the user's natural-language request into a compact TAKY task contract and load only the minimum relevant skill/context.
---
Normalize the request into:
GOAL / TARGET / LOCKED / FORBIDDEN / ACCEPTANCE / VERIFY.
Do not paraphrase away concrete names, paths, IDs, approved visual references, or user corrections.
Remove repetition, filler, duplicated commands, and already-global TAKY rules.
Select at most the smallest relevant skill set; do not preload unrelated skills.
Default route:
- authority conflict/resume -> authority-check or taky-resume
- when a registered GROW domain is clear, route the domain owner first; mining/index-learning is a subordinate capability, not a competing owner
- mining/indexing/learning without a clearer domain owner -> mining-index-learning
- UI/design/asset/document/result-quality work -> outcome-quality + the smallest domain skill; add browser-verify for material web/PWA render evidence
- new/unlocked frontend visual direction -> outcome-quality + frontend-design only when its material design benefit justifies the extra model context; project authority still wins
- approved/locked UI implementation -> outcome-quality + mobile-webapp-build + browser-verify; do not let frontend-design reinterpret the locked composition/identity
- runtime integration -> runtime-e2e
- architecture office / architecture growth -> archi-grow (`ARCHI_GROW`)
- learning outcome / review policy / Learning Engine growth -> learning-grow (`LEARNING_GROW`); add mining-index-learning only when acquisition/index work is actually needed
- cost/model choice -> savey-ai-economy
- independent review -> cross-model-review only after a material delta or failure
Always preserve USER != DEBUGGER and fail-closed boundaries.
