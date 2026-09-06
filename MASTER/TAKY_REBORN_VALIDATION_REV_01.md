# TAKY REBORN REV_01 — VALIDATION & REGRESSION RECORD

Status: REVIEWED CANDIDATE / NOT CANONICAL / NOT RELEASED
Target: `MASTER/TAKY_REBORN_REV_01.md`

## 1. Review scope
Compared:
- current `MASTER/MASTER_LOGIC.md` REV_00;
- `MASTER/TAKY_REBORN_CANDIDATE.md`;
- Notion-derived knowledge patterns on selective retrieval, token/context cost, externalized memory and graph-first narrowing;
- contemporary agent architecture patterns from OpenAI Agents SDK, Microsoft Agent Framework, Anthropic context engineering;
- current GitHub/community failure reports around routing, context compaction, infinite loops, stale memory and over-engineered repository context;
- 2026 research on repository-level context files.

## 2. Main findings
### A. REBORN candidate was directionally correct
Preserve:
- smallest-sufficient-system principle;
- progressive context;
- conditional heavy modules;
- Notion as knowledge supply rather than authority;
- short default runtime;
- multi-agent only when justified.

### B. Candidate removed too much protection from the always-on layer
Recovered into REV_01 as invariants:
- authority hierarchy;
- evidence-bounded claim rule;
- lifecycle distinctions;
- approval separation;
- no-silent-loss rule;
- loop/termination/budget guardrails;
- proportional trace;
- compaction/freshness/conflict handling.

### C. REV_00 was too expensive as a universal runtime
Moved from mandatory/default to conditional modules:
- full source recovery;
- decision-coverage matrices;
- reverse trace;
- deep analysis;
- broad research;
- handoff;
- cross-validation;
- regression and impact checks outside affected scope.

## 3. External evidence synthesis
### OpenAI Agents SDK
Useful principles:
- few primitives rather than a giant abstraction surface;
- handoffs/agents-as-tools are optional composition mechanisms;
- guardrails, sessions, HITL and tracing are separable capabilities;
- handoff context can require filtering/ownership rules;
- long-running execution benefits from durable state and resumption.

TAKY implication:
keep orchestration primitives small; separate ownership, context and approval; trace material execution.

### Microsoft Agent Framework
Useful principles:
- sequential, concurrent, handoff, group-chat and manager patterns are distinct tools;
- each extra orchestration pattern adds complexity;
- simplest pattern that satisfies requirements is preferred;
- workflows mix deterministic executors with agents;
- HITL/checkpoint/state/observability are separate production capabilities.

TAKY implication:
do not equate orchestration with multi-agent; prefer deterministic workflow where possible.

### Anthropic context engineering
Useful principles:
- context is finite attention budget;
- optimize for the smallest high-signal context;
- overly detailed brittle system prompts create maintenance problems;
- context must be curated dynamically rather than accumulated blindly.

TAKY implication:
CORE must remain minimal; detailed requirements should live at the narrowest applicable layer and be retrieved selectively.

### Research on AGENTS.md / repository context
Findings are mixed but converge on one guardrail:
- some studies report lower runtime/token use with repository instructions;
- other controlled evaluation reports lower task success and >20% inference-cost increase from unnecessary context;
- minimal, relevant instructions are safer than broad always-on requirements.

TAKY implication:
do not assume more permanent context improves correctness; measure and minimize.

### GitHub/community failure signals
Recurring operational failure modes:
- stale memory and state drift;
- context compaction losing instructions;
- repeated tool/delegation loops;
- wrong LLM-driven handoff/routing where deterministic routing could suffice;
- missing audit trail and checkpointing;
- multi-agent coordination overhead exceeding benefit.

TAKY implication:
add termination/budget guardrails, deterministic routing preference, context-preservation rules and recoverable state.

## 4. Error correction performed
Detected candidate gaps and corrections:
1. **Authority regression risk** → restored explicit hierarchy and canonical boundary.
2. **Validation weakening risk** → restored evidence-bounded claim ladder in compact form.
3. **Lifecycle ambiguity** → restored DRAFT/CANDIDATE/VALIDATED/APPROVED/COMMITTED/RELEASED/SUPERSEDED.
4. **Automation safety gap** → restored scoped approval/authority principle.
5. **Long-running loop risk** → added termination, retry, delegation and cost limits.
6. **Compaction/memory drift risk** → added no-silent-loss, freshness and conflict rules.
7. **Multi-agent overuse risk** → defined concrete admissible benefits and deterministic-first routing.
8. **Trace bloat risk** → changed exhaustive trace to proportional material trace.
9. **Research bloat risk** → external research remains trigger-based.
10. **Notion authority confusion** → retained digest/knowledge role while denying automatic canonical promotion.

## 5. Self-validation
### Structural check
PASS:
- CORE separated from modules/project/knowledge/history;
- default runtime is short;
- optional modules have identifiable triggers;
- authority/evidence/approval remain explicit;
- no requirement silently converts Notion/memory/chat into canonical truth.

### Contradiction check
PASS WITH CONDITION:
- “smallest sufficient context” and “no silent loss” can conflict if applied mechanically.
- REV_01 resolves this by escalating when preservation cannot be proved and marking continuity UNVERIFIED.

### Over-bloat check
PASS WITH CONDITION:
- REV_01 is materially shorter than REV_00 in mandatory runtime semantics, but still contains explanatory sections.
- future canonicalization should consider splitting normative CORE from explanatory/reference material so only CORE is always loaded.

## 6. Regression validation against REV_00
### Preserved
PASS:
- canonical authority;
- hierarchy;
- deterministic-before-AI principle;
- uncertainty states;
- human approval distinction;
- lifecycle state separation;
- evidence-bound validation claims;
- protected-decision preservation;
- composition/integration validation availability;
- recovery/deep-analysis/reverse-trace capability;
- HOLD/CONFLICT/UNKNOWN preservation semantics.

### Intentionally changed
EXPECTED CHANGE:
- handoff no longer mandatory;
- deep analysis no longer universal;
- cross-validation no longer universal;
- full conversation/source recovery no longer universal;
- regression/impact checks are affected-scope dependent;
- exhaustive decision-coverage matrix becomes a triggered audit module;
- trace depth is proportional rather than maximal.

### Potential regression still requiring future test
UNVERIFIED:
- real token/context reduction in actual ChatGPT/Codex use;
- task-success impact across representative TAKY projects;
- whether short CORE plus retrieved modules outperform current REV_00 for complex architecture/document/design tasks;
- effectiveness of routing/termination rules in implemented runtime because REV_01 is currently governance text, not an execution engine.

## 7. Validation result
`PASS_WITH_CONDITIONS`

Reason:
REV_01 improves the candidate by restoring safety/authority invariants while retaining selective context and conditional capability design. No canonical or release promotion is justified yet because runtime effectiveness and representative-project regression have not been empirically tested.

## 8. Required gate before canonical promotion
Before replacing `MASTER/MASTER_LOGIC.md`:
1. run representative scenario tests across low-risk, complex-project, coding, research and external-action cases;
2. compare context/rule load and task quality against REV_00;
3. verify escalation modules activate when required and stay inactive otherwise;
4. verify compaction/handoff does not lose protected decisions;
5. verify deterministic routing/loop limits on at least one agentic workflow;
6. review final diff with human approval;
7. only then promote/commit canonical replacement and update changelog/release state.
