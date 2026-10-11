# TAKY Claude Setup — New Chat Start
Date: 2026-10-02
Status: SETUP_OPTIMIZED_PASS / NO_DEPLOY / NO_PAID_API_FALLBACK

## Fixed runtime
- Claude Code 2.1.287 native binary is primary.
- Claude auth: OAuth subscription path verified PASS.
- Default Claude Code builder: Sonnet 5.5.
- PowerShell profile removes ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY at startup.
- GitHub CLI authenticated and preferred over duplicate GitHub MCP.
- Notion MCP connected.
- Playwright MCP connected.
- Chrome DevTools MCP connected.
- Netlify MCP connected; production publish/deploy remains human-gated.
- Claude in Chrome is NOT required and is excluded from this setup.

## Account routing
- Claude subscription account: siezeall.
- Google Drive main account: hns.
- TAKY Drive folder is shared from siezeall to hns.
- Google Drive web connector uses hns. Claude Code uses browser MCP only when Drive access is needed.

## TAKY execution defaults
- USER != DEBUGGER.
- Claude operates as an open knowledge ecosystem under TAKY governance: NotebookLM, web, Drive, Notion, GitHub, MCP/connectors, trusted skills and independent models may enrich INDEX/LEARNING when materially useful.
- External findings are welcomed as EVIDENCE/REFERENCE and may challenge CURRENT, but only governed verification can promote or correct CURRENT. Do not reject useful knowledge merely because it comes from outside TAKY.
- NotebookLM is an INDEX/LEARNING augmentation engine for large-source synthesis, cross-document linking, contradiction discovery and source-grounded research; it is not a competing authority store.
- Figma free quota for the current month is exhausted: treat Figma as HOLD / non-default. UI work defaults to approved mockup/assets -> local code -> Playwright/Chrome DevTools runtime inspection -> visual compare/fix/regression. Re-enable Figma only when quota renews or explicit paid usage is approved.
- Architecture tasks inherit `CLAUDE.md` ArchiGrow reasoning contract + `DOMAIN/ARCHITECTURE_GROWTH_MAP.md`.
- ArchiGrow core: `Reality Locked / Possibility Open`; answer WHY THIS DESIGN with evidence; use `GOAL -> EVIDENCE -> OPTIONS -> COMPARE -> VERIFY -> SELECT/REFINE -> OUTCOME -> LEARN`; external architecture references remain REFERENCE_ONLY until governed validation.
- Subscription/OAuth/local-first; paid provider API requires explicit approval.
- acceptEdits default; safe read/test/build commands are pre-approved.
- push / merge / release / production deploy / destructive actions remain gated by TAKY hook.
- Use /clear between unrelated tasks; /compact only to continue a long task.
- Opus only for hard architecture/debugging/adversarial review where quota cost is justified.

## Verified
- CLAUDE_SETTINGS_JSON PASS
- TAKY_HOOK_COMPILE PASS
- NETLIFY_SKILL_HYGIENE PASS
- CLI_CLAUDE/CODEX/GEMINI/NETLIFY/GH PASS
- CODEX_CHATGPT_AUTH PASS
- CLAUDE_SUBSCRIPTION_AUTH PASS
- GLOBAL_GEMINI_API_KEY PASS (not set)
- TERMINAL_TAKY_ENTRY PASS
- MCP notion/playwright/chrome-devtools/netlify PASS

## Resume
Run TOOLS/TAKY_SETUP_CHECK.ps1 first. Continue only from actual FAIL/HOLD items; do not redo PASSED setup.
