# 2026-09-19 — Conversation Continuity / Context Economy Standard

Status: CANONICAL CHANGE RECORD

## Trigger
User requested a durable standard where the sum of conversations can be recovered through NotebookLM without omission or repeated questioning, while avoiding a heavyweight always-on full-history architecture.

## Decision
Adopt:
**TOTALITY STORED, CONTEXT SELECTIVE.**

The system preserves total material meaning in raw evidence + C2S/state/history/indexes, but loads only the minimum sufficient context for each action.

## New canonical behaviors
- L0 HOT current working set for ordinary continuation.
- L1 WARM canonical state/owner/open-delta recovery for new-chat resume.
- L2 targeted NotebookLM/index recovery only when L0/L1 is insufficient.
- L3 raw-source verification for exact/correction/canonical disputes.
- L4 full forensic/global reconstruction only for explicit full/global scope.
- ASK LAST: do not ask the user to repeat recoverable context.
- FULL SCAN LAST: do not reload all history for ordinary work.
- Conversation end performs incremental C2S/state persistence, not automatic NotebookLM/global rescan.
- NotebookLM is cold-memory/index assistance, not always-loaded memory.
- Maintain topic/project notebook partition plus lightweight global source/topic map.

## Enforcement
Added deterministic continuity-record validator and fixtures that reject:
- user re-asking while a recoverable path remains;
- L4 full scan without explicit authorization;
- NotebookLM use when L0/L1 was declared sufficient.

## Goal
High continuity / low context cost:
- no needless re-asking;
- no silent material loss;
- no full-history reload by default;
- new chats resume from canonical state and only escalate when necessary.

END
