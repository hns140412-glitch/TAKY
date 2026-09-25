# MINING ENGINE OPERATIONS CAMPAIGN 01 — 2026-09-25

## MODE
OPERATIONS / REAL OUTCOME LEARNING

V2 remains CLOSED.
This campaign does not reopen V2 and does not imply V3.

## PURPOSE
Collect bounded real-use evidence to determine whether Mining Engine V2:
- finds the right sources,
- researches to the right depth,
- stops at the right time,
- synthesizes evidence correctly,
- produces useful alternatives,
- improves from repeated outcomes without cross-family leakage.

## CAMPAIGN BOUNDS
Target real runs: 12
Minimum distinct task families: 4
Minimum runs per family for any strategy-promotion review: 3
Minimum successful outcome quality for candidate success: 0.75
Minimum average quality for strategy review eligibility: 0.82

## REQUIRED EVIDENCE PER RUN
Each real run should record:
- run_id
- timestamp
- task_family
- human_goal
- selected depth
- frontier size
- providers attempted
- provider failures / fallbacks
- evidence accepted / rejected
- unresolved conflicts
- stop reason
- synthesis readiness
- outcome quality
- user correction rate when available
- strategy observation or failure observation
- checkpoint resume_key

## SUCCESS SIGNALS
- correct source family selected
- evidence trace preserved
- no unnecessary repeated search
- critical gaps resolved before stop
- synthesis does not collapse conflicts
- user correction is low
- repeated strategy success remains within same task family

## FAILURE SIGNALS
- wrong source/provider route
- shallow stop with critical gap
- over-deep research without material gain
- duplicate source mistaken for corroboration
- cross-family strategy leakage
- unresolved conflict collapsed
- poor synthesis despite strong evidence
- repeated user correction on same pattern

## V3 OPEN TRIGGER
V3 may be proposed only if one or more of the following are observed with concrete run evidence:
1. repeated failure pattern across >= 2 real runs,
2. missing capability blocks a user outcome,
3. current routing consistently over/under-researches,
4. provider architecture cannot recover from a recurring live failure,
5. synthesis/growth logic repeatedly misclassifies real outcomes.

A one-off inconvenience does not open V3.

## CURRENT PROGRESS
real_runs_recorded: 0 / 12
distinct_task_families: 0 / 4
strategy_review_eligible: 0
v3_triggered: false
