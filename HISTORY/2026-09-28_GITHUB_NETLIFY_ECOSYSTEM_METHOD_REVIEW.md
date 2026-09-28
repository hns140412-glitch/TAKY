# TAKY | GitHub + Netlify external ecosystem method review

Captured: 2026-09-28 (public source snapshot)  
Status: REFERENCE_ONLY / CANDIDATE_LOCALIZATION / NOT_IMPLEMENTATION_AUTHORIZATION  
Authority: This is source/evidence history, NOT another Master rule, Owner, platform guarantee, live monitor, adoption decision or deployment request.  
Scope: Central TAKY Mining -> Indexing -> Growth/Outcome method; project-specific app or paused-project implementation EXCLUDED. No personal, child, customer, confidential or connected account information was used in public research.

## 1. Selection rule: popularity is discovery, not evidence of fitness

GitHub does not expose a product-quality star rating equivalent to verified acceptance testing: stargazers signal community attention. A quality appraisal needs exact use-case, public issue reproduction, maintainer response/PR/regression, recency, official docs, license/usage restrictions, costs and a local baseline. A single thread/author report is evidence of a possible failure, not prevalence or a universal platform defect. A popular repo is not automatically suitable to install, run, or copy into TAKY.

Observed public repository pages, rounded star snapshot (values change; do not place in canonical policy or rank product quality):

| Repository | Approx stars | Selection purpose | Snapshot source |
|---|---:|---|---|
| n8n-io/n8n | 206.1k | workflow/agent resume and tool-call identity | https://github.com/n8n-io/n8n |
| langfuse/langfuse | 35.1k | trace vs experiment vs observed feedback | https://github.com/langfuse/langfuse |
| promptfoo/promptfoo | 25.5k | distinguish evaluator failure from criterion failure | https://github.com/promptfoo/promptfoo |
| argoproj/argo-cd | 24.3k | declared / rendered / live revision difference | https://github.com/argoproj/argo-cd |
| temporalio/temporal | 23.3k | retry, replay and idempotency | https://github.com/temporalio/temporal |
| renovatebot/renovate | 22.6k | discovery/priority vs actual schedule, hold and approval | https://github.com/renovatebot/renovate |
| open-telemetry/opentelemetry-collector | 7.6k | producer/collector/exporter observation and duplicated work | https://github.com/open-telemetry/opentelemetry-collector |
| netlify/cli | 1.9k | exact local/remote CLI deploy behavior and reproducible dependencies | https://github.com/netlify/cli |
| netlify/build | 259 | original build pipeline mechanics regardless of lower social popularity | https://github.com/netlify/build |

Do not convert stars, unresolved issue counts or comment count into a universal numeric TAKY trust or product score. Licenses must be checked per project before using any source code: n8n is presented as fair-code and Langfuse's MIT claim excludes its ee folders, for example.

## 2. Community discussions/Issues/PR evidence -> TAKY-localized insight

### A. An attractive automatic loop can silently lose its execution meaning
- n8n issue #38503, Sep 12: reporter describes canonical tool name being replaced by a node-derived display name during history reconstruction; subsequent model tool call can be silently omitted. Status shown open/needs feedback; source: https://github.com/n8n-io/n8n/issues/38503
- n8n issue #37779, Sep 3 + comments Sep 9/23: agent retry after maxIterations can resume without tool state and retry budget can reset; a commenter reported reproducing and a draft patch. Treat reported tests as author evidence, not independently tested here: https://github.com/n8n-io/n8n/issues/37779
- TAKY use: keep stable semantic IDs and trace/retry budget across handoff; invocation receipt, actual tool execution and post-write result are distinct. Prior HEAD/branch success does not prove latest live result. No n8n integration or new orchestration engine recommended.

### B. Evaluation error must remain distinct from actual quality failure
- Promptfoo #10481 (Aug 24): author distinguishes grader/provider/no-output failure from a valid failed factuality assertion; conflation can create false CI regression. Status open at inspection: https://github.com/promptfoo/promptfoo/issues/10481
- Langfuse #14797 (Jul 5, closed record): author reports score events receiving HTTP 201 without appearing in query/store. This is a case report for a specific self-hosted version, not a proven general/current defect: https://github.com/langfuse/langfuse/issues/14797
- Langfuse #15216 (Jul 20): author reports experiment UI rendering bad input/trace association despite API data being intact: https://github.com/langfuse/langfuse/issues/15216
- Langfuse 2026 roadmap discussion includes feedback on agents, eval experiments and qualitative comments, but roadmap intent != released capability: https://github.com/orgs/langfuse/discussions/11391
- TAKY use: preserve source/raw -> processed/indexed -> evaluator attempted/result/error -> owner-disposition -> user outcome as DIFFERENT evidence planes. HTTP accepted / CI green / dashboard shows success are not sufficient to assert persisted or correct result. Keep UNKNOWN/UNVERIFIED instead of fabricating a pass/fail. Reuse existing C2S, Indexing and Outcome owner; no duplicate telemetry product.

### C. Declared success must not override fresh authority
- Argo CD #28980 (Jul 30): reported real sync phase Succeeded despite a resource being skipped after dry-run detected change: https://github.com/argoproj/argo-cd/issues/28980
- Argo CD #29732 (Sep 15): issue listing describes rejected same-repo multi-source revision generation proceeding with a stale revision, a source-lineage case rather than a verified TAKY fault: https://github.com/argoproj/argo-cd/issues/29732
- Argo CD discussion #19666: users report sync-wave ordering discrepancies and discuss health checks/delays: https://github.com/argoproj/argo-cd/discussions/19666
- TAKY use: CURRENT + EXACT HEAD + authoritative original + post-write readback remain different checkpoints. Avoid blanket rechecking when no changed source; target checks to materially affected revision/Owner.

### D. Prioritization, throttling, and approval are independent controls
- Renovate discussion #42888 (Jul 2026, answered): prPriority orders processing; it does not prevent PR creation if rate-limit capacity exists; schedule/approval/disable control actual hold: https://github.com/renovatebot/renovate/discussions/42888
- Renovate discussion #45360 (Aug 2026): author describes batch PRs touching a common lock file and conflict after merging a subset; a community scenario, not reason to automatically merge more: https://github.com/renovatebot/renovate/discussions/45360
- Temporal issue #8901 / maintainer comment Jan 9: replay/retry makes activity idempotency necessary because network/worker failures can cause repetition independently of workflow retry: https://github.com/temporalio/temporal/issues/8901
- TAKY use: distinguish source importance, review urgency, actual execution permission, quota and owner HOLD. Do not auto-promote OPEN or queue simply because priority is high; avoid duplicate side effects during retries.

## 3. Netlify: official documents plus actual community limitations

The account's own pricing and permissions were NOT queried; all below refers to documented credit-based plans, NOT a statement of this user's actual tariff or remaining balance.

Official:
- Pricing Free 300 credits / month; credit-based successful production deploy is 15 credits; preview/branch deploy **deploy meter** 0 credits, while compute, bandwidth, web requests and inference can still consume metered resources. Credits and plan may differ on legacy account. https://www.netlify.com/pricing/ and https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/how-credits-work/
- Netlify default ignores unchanged base-directory builds; a custom `[build] ignore` command uses 0 to skip and 1 to build. IMPORTANT: build hooks bypass custom ignore (official explicit exception): https://docs.netlify.com/build/configure-builds/ignore-builds/
- Netlify CLI uses draft deploy by default and `--prod` for live; retries can target BRANCH HEAD rather than prior exact SHA, so name and verify the desired source before publication: https://github.com/netlify/cli/blob/main/docs/commands/deploy.md and https://www.netlify.com/knowledge-base/how-to-deploy-a-site-to-netlify/
- Notifications distinguish deploy started/succeeded/failed/locked/unlocked: https://docs.netlify.com/deploy/deploy-notifications/
- Old failed/cancelled deploy logs/assets may be automatically cleaned after 30 days (90 paid); retain only minimum essential source/receipt externally where authorized: https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/

Community counterevidence (user-specific account reports, do NOT generalize to all accounts or assert unresolved for this user):
- July 2026 forum report: preview succeeded while production was blocked despite apparently available credits; author later reported support/engineering resolved their case: https://answers.netlify.com/t/production-deploys-blocked-by-stale-credit-usage-exceeded-flag-despite-330-credits-available/164819
- Sep 9 and Sep 25 forum reports describe displayed Free credits but production still blocked; root cause/account applicability not independently verified: https://answers.netlify.com/t/free-plan-production-deploys-blocked-with-74-4-300-credits-remaining-stale-credit-flag/168967 and https://answers.netlify.com/t/my-netlify-free-plan-resetting-to-300-300-credits-while-my-team-and-projects-remain-incorrectly-paused-due-to-the-previous-billing-cycle-s-credit-limit-flag/171129
- Netlify CLI #7933 reporter claims `--no-build` still bundled Edge Functions on an observed version, so flag name alone is not enough for platform-effect claims: https://github.com/netlify/cli/issues/7933
- TAKY use: release readiness (source/CI) != platform deploy attempt != platform accepted != live URL/build hash/readback != app behavior; balance display != deployment permission; billing/plan and source SHA need independent exact live checks when an authorized release actually occurs. No speculative workaround, paid top-up, build-hook test, live deploy or rollback was performed here.

## 4. Local disposition without duplicating masters

- **ADJUST IN EXISTING OWNER:** The existing Outcome protocol may clarify event-triggered vs scheduled observation, targeted recheck, productive next action and stop; compare with central Draft PR #168 and the overlapping Growth 9A note in Draft PR #166 before any promotion. Keep human approval at existing actual authority boundaries; no universal extra gate.
- **PRESERVE IN EXISTING MASTER:** stable source/role/current references; source recovery, raw/index/detail/current roles; before/change/after/outcome evidence and valid UNKNOWN state.
- **REFERENCE ONLY:** issue-specific tool identity loss, evaluator-vs-assertion distinctions, sync status/drift, dependency scheduling and provider/deploy traceability. Promote only after matching an actual TAKY defect or outcome improvement evidence.
- **NETLIFY PLATFORM METHOD:** Read-only pricing/usage/source/deploy status inspection can inform a separately authorized deployment workflow. Default skip unnecessary production deployments and preserve exact asset/commit receipts. Do not infer this account's quota from public docs; no Netlify tool action is needed in this source-method review.
- **HOLD:** new always-on watcher/orchestrator, extra installed SaaS, paid LLM evaluator, user/client/child data sent to trials, auto PR merges, production deployments or changing unrelated project code. The explicit paused project remains untouched and is not a case in this research.

## 5. Source trust and review exit

Official platform doc determines claimed supported behavior; exact implementation/version and regression determine observed operation; maintainer reply/closed issue adds context but not independent full validation; comment/creator reel is a discovery witness, not runtime proof. Record the exact source, as-of date, adverse reports and any unresolved counterexample. One actionable central methodological improvement is sufficient for a source to be useful even when its star count is small.

This research document can support future central PR review; it neither changes the canonical main nor claims app-runtime, Netlify-account or end-user outcome verification.
