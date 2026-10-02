# TAKY Badge Source Producer Gap Audit — 2026-10-02
Status: QA_EVIDENCE_ONLY_NOT_ACTIVE

## Current
- source producer QA PASS: 15/60
- remaining: 45/60
- active: 0/60
- deployment: HOLD

## Classification
### A. CURRENT_SIGNAL_INSUFFICIENT — 29
These badges cannot be safely produced from current runtime signals without relying on elapsed time, score, silence, attempt count, inferred attention, parent behavior, or other weak proxies.

Slots:
001 EARLY_START
002 ALARM_RESPONSE
003 MICRO_START
004 RESTART_AFTER_BREAK
005 PREPARATION_COMPLETE
013 SINGLE_TASK_FOCUS
014 FAST_COMPLETE_CHECKED
015 ACCURATE_COMPLETE
017 PERSIST_TO_COMPLETE
018 LONG_FOCUS
019 QUIET_IMMERSION
020 FLOW_CONTINUATION
022 FOCUS_RETURN
023 SELF_NOTICE_RETURN
031 PERSISTENT_BREAKTHROUGH
032 CONCEPT_UNDERSTOOD
033 REFLECT_BEFORE_ANSWER
038 DEEP_THINKING_PERSISTENCE
039 BLOCK_RESOLVED
040 STOP_AT_RIGHT_TIME
041 MEANINGFUL_OVERRUN
042 FLOW_IMMERSION
043 BREAK_RETURN
044 TIMER_RETURN
045 DISTRACTION_RESISTANCE
046 TASK_RESTART
049 MICRO_TASK_COMPLETE
054 IMPROVEMENT
057 START_DESPITE_CONDITION

Decision:
- keep SOURCE_PRODUCER_REQUIRED
- do not synthesize observations from weak proxies
- require stronger child-authored or feature-declared evidence before implementation

### B. EXPLICIT_UI_OR_SOURCE_EVENT_NEEDED — 13
The semantic can be made safe, but current UI/runtime does not expose the explicit child action needed to prove it.

006 TIME_CREATION
- need explicit child action selecting a real free schedule slot and starting the task from that selected slot

007 TIME_CREATION_EXTRA
- need explicit child action creating/selecting extra time outside the existing plan plus extra task execution

012 SELF_PLANNING_SEQUENCE
- need child-authored reorder/sequence action, not passive Planner order

016 CHUNKED_COMPLETE
- need explicit child-created or child-accepted chunk plan plus completion of those chunks

030 ROOT_CAUSE_FOUND
- need child-authored root-cause explanation/selection tied to a concrete error artifact

034 REREAD_CHECK
- need explicit reread/check action before corrected submission

035 CALCULATION_CHECK
- need explicit calculation-check action tied to before/after correction evidence

036 CORRECTION_COURAGE
- need explicit child correction action whose intent is independent of generic retry/correction badges

050 PRIORITIZE_HARD
- need child choice explicitly marking/selecting a harder task first from comparable available tasks

051 WARM_START
- need explicit child strategy choice to start with an easier task, then evidence of continuing the full plan

052 STRATEGY_SWITCH
- need explicit child-selected strategy change after a specific blocked attempt; AI suggestion alone is insufficient

053 SELF_EXPLANATION
- need child-authored explanation action tied to the learned concept/material; generic writing does not prove self-explanation

056 PLAN_ADAPTATION
- need unexpected-change provenance + child-authored replan + execution of revised plan

Decision:
- keep SOURCE_PRODUCER_REQUIRED
- add producer only when the app feature emits an exact declared event with evidence_ref

### C. EXISTING_ACTION_REVIEW_NEEDED — 3
These have superficially similar existing actions but are not safe to bind yet because of semantic overlap/collision risk.

008 EXTRA_TASK
- Snap bonus exercise already produces BDG-DRAFT-055 VOLUNTARY_EXTRA.
- Reusing the same bonus action would risk multi-award collision.
- Need a distinct source action meaning “after finishing planned work, child independently selects one additional task.”

009 BEFORE_PROMPT
- current app can observe task start but cannot prove no parent prompt occurred.
- Requires an authoritative prompt/request ledger or explicit parent-free initiation boundary.

010 RESPONSIVE_START
- “immediately after guidance” cannot be inferred from elapsed time.
- Requires a feature-declared response action whose semantics explicitly encode response to a named prompt, not timing threshold.

Decision:
- keep SOURCE_PRODUCER_REQUIRED
- do not bind to existing producer until collision/authority gap is resolved

## Global false-positive guard
Never use as sufficient evidence:
- elapsed or focus duration
- score/grade/mastery
- silence
- attempt count
- AI/model inference
- parent guess
- lack of recorded parent interaction
- generic completion
- generic task selection
- generic writing text

## Invariants
- 60 badge IDs/names/core descriptions/nature taxonomy/Visual IDs/Asset Slot IDs/SHA unchanged
- historical trigger prose remains descriptive, not executable
- source-only award boundary unchanged
- active remains 0/60
- no main merge
- no Netlify deployment
