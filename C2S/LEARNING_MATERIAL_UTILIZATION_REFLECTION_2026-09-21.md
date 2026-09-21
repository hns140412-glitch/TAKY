# LEARNING MATERIAL UTILIZATION — REFLECTION MAPPING — 2026-09-21

Status: REFLECTION_CLOSED__DOWNSTREAM_IMPLEMENTATION_OPEN
Authority: TKY-C2S-001 + Learning App Family ownership locks
Scope: Reflection only. No Ready / Hide / Snap product code changed.

## 1. Live rebuild baselines refreshed

- Ready & Set: `taky/ready-rebuild-v01-2026-09-21` @ `da42d5121087b58201e85b5135d9b0c0765625f2`
- Hide & Seek: `taky/hide-rebuild-v01-2026-09-21` @ `880cd6f98a60d35a13389501e4ac2f3c0e83ec9b`
- Snap & Pop: `taky/snap-rebuild-v01-2026-09-21` @ `1332d958bdc4a8b2bec93900dbe2dbdb2a840ea2`

Product rebuild branches were read only. This reflection does not override their own rebuild sequencing or runtime gates.

## 2. Ownership locks preserved

- Ready & Set = session / task routing / Planner.
- Ready Learning Engine = assignment interpretation / Learning Unit / level and Hanja grade interpretation / scaffold routing.
- Hide & Seek = Language Memory & Meaning.
- Snap & Pop = thought / expression / writing / speaking.
- Reference materials remain REFERENCE_ONLY / EVIDENCE_ASSIST.
- No source page, wording, exercise sequence or proprietary layout is adopted verbatim.

## 3. Reflection matrix

| Atom | Primary owner | Reflection classification | Live evidence / interpretation | Implementation GAP |
|---|---|---|---|---|
| SCENE_FIRST_RECALL | Snap | PARTIAL_IMPLEMENTATION | Snap writing flow already asks for one first idea/scene and has scene/description prompts, but it is not an explicit memorable-scene recall mode with a stable contract. | GAP-LMU-001 |
| SENSORY_RECALL_LADDER | Snap (+ Hide secondary) | PARTIAL_IMPLEMENTATION | Snap has sensory feature detection and prompts for sight/sound/smell/touch plus emotion lenses. It is not yet an ordered recall ladder linking visible detail → sound/spoken words → body/emotion → expression, and no Hide memory linkage is explicit. | GAP-LMU-002 |
| ORAL_BEFORE_WRITING | Snap | PARTIAL_IMPLEMENTATION | Snap has generic STT/TTS voice capability, but the writing runtime does not currently make learner speech/transcript a first-class pre-writing step. | GAP-LMU-003 |
| GRADUAL_EXPRESSION_EXPANSION | Snap (+ Learning Engine difficulty routing) | PARTIAL_IMPLEMENTATION | Snap has 3-step writing progression, one-next-move prompting and sentence-count-aware expansion, but not the full phrase → sentence → 3 sentences → paragraph → structured-text progression nor Learning Engine-routed difficulty. | GAP-LMU-004 |
| EXPRESSION_VARIATION | Hide (+ Snap consumer) | PARTIAL_IMPLEMENTATION | Hide already owns semantic/context memory axes and Snap can consume vocabulary material without ownership transfer. A Hide-owned context-bound alternative-expression mechanism is not explicit. | GAP-LMU-005 |
| SITUATION_TO_LANGUAGE | Snap (+ Hide secondary) | NOT_IMPLEMENTED | Current Snap writing prompts are generic expression lenses, not a reusable realistic-child-situation → learner-first response → optional model/scaffold mechanism. | GAP-LMU-006 |
| MEANING_CONTEXT_REUSE | Hide (+ Snap consumer) | PARTIAL_IMPLEMENTATION | Hide already models MEANING/CONTEXT/RECALL and response loops, but idiom/proverb/four-character-idiom meaning → situation → example → learner reuse is not encoded as a complete reusable chain. | GAP-LMU-007 |
| FORM_MEANING_USAGE_CHAIN | Hide (Ready resolves level) | PARTIAL_IMPLEMENTATION | Hide Hanja model already contains RADICAL/COMPONENT/SOUND/MEANING/COMPOUND_CONTEXT and form-sound-meaning-recall loops. Ready-supplied Hanja level fields are preserved. Familiar-usage + retrieval-cue chain is not yet explicit end-to-end. | GAP-LMU-008 |
| WRITING_SCAFFOLD_GRAPH | Snap (+ Learning Engine secondary) | PARTIAL_IMPLEMENTATION / P2_HOLD_FOR_FULL_GENRE | Snap already has reusable lenses/nodes (idea, emotion, description, viewpoint, final) and cross-lens suggestions. Full genre graph with reusable reason/example/comparison/order/conclusion nodes and Learning Engine scaffold routing is not complete. | GAP-LMU-009 |
| QUESTION_BEFORE_CALCULATION | Ready Learning Engine | NOT_IMPLEMENTED | Ready Learning Master has math concept/application/error-correction sequencing, but no enforced question-target comprehension gate before calculation. | GAP-LMU-010 |
| PROBLEM_RESTATE | Ready Learning Engine (+ Snap expression support) | NOT_IMPLEMENTED | No explicit learner restatement of “what the problem asks” was found in current Ready Learning Master/rebuild runtime. | GAP-LMU-011 |
| PRESERVE_CHILD_VOICE | Learning App Family | PARTIAL_IMPLEMENTATION | Snap has a strong authorship guard: forbids final-draft/rewrite/suggested-sentence output and enforces one next move. The corresponding Learning Engine prompting policy is not yet explicit, so family-wide closure is incomplete. | GAP-LMU-012 |

## 4. Duplicate / ownership-error review

- TRUE_DUPLICATE atoms: 0.
- OWNERSHIP_ERROR atoms: 0.
- Some atoms overlap existing capabilities, but overlap is treated as PARTIAL_IMPLEMENTATION, not duplication.
- Hide does not gain Hanja level/grade authority.
- Snap does not gain language-mastery ownership.
- Ready does not gain language-memory or child-authorship ownership.

## 5. Gap consolidation

Raw atom-level implementation gaps: 12.

To avoid overbuilding, these should be implemented as 7 consolidated capability gaps:

1. GAP-CAP-01 — Snap Recall Entry
   - covers SCENE_FIRST_RECALL + SENSORY_RECALL_LADDER.
2. GAP-CAP-02 — Snap Oral-to-Writing Bridge
   - covers ORAL_BEFORE_WRITING.
3. GAP-CAP-03 — Progressive Expression Scaffold
   - covers GRADUAL_EXPRESSION_EXPANSION + WRITING_SCAFFOLD_GRAPH.
4. GAP-CAP-04 — Hide Contextual Reuse Layer
   - covers EXPRESSION_VARIATION + MEANING_CONTEXT_REUSE.
5. GAP-CAP-05 — Hide Hanja Memory Chain Completion
   - covers FORM_MEANING_USAGE_CHAIN while consuming Ready-resolved level.
6. GAP-CAP-06 — Ready Question-Comprehension Gate
   - covers QUESTION_BEFORE_CALCULATION + PROBLEM_RESTATE.
7. GAP-CAP-07 — Family Child-Voice Policy Completion
   - preserve current Snap guard and add Learning Engine prompt-policy parity.

SITUATION_TO_LANGUAGE remains a separate Snap capability inside GAP-CAP-03 implementation planning, but can be scheduled after the current rebuild runtime is stable.

## 6. Priority

P0 after rebuild runtime stabilization:
- GAP-CAP-06 Ready Question-Comprehension Gate.
- GAP-CAP-07 Family Child-Voice Policy Completion.
- GAP-CAP-01 Snap Recall Entry.
- GAP-CAP-02 Snap Oral-to-Writing Bridge.

P1:
- GAP-CAP-04 Hide Contextual Reuse Layer.
- GAP-CAP-05 Hide Hanja Memory Chain Completion.
- Progressive expression core portion of GAP-CAP-03.

P2 / HOLD until core runtime stabilization:
- Full multi-genre WRITING_SCAFFOLD_GRAPH.
- Broad realistic-situation library for SITUATION_TO_LANGUAGE.

## 7. Utilization assessment

Atom reflection coverage: 12 / 12 = 100%.

Current practical utilization by atom state:
- Fully implemented at family-atom level: 0 / 12.
- Partially implemented: 9 / 12.
- Not implemented: 3 / 12.
- Duplicate: 0.
- Ownership error: 0.

This does NOT mean the learning system is 75% complete. Partial implementation ranges from thin capability overlap to strong near-complete mechanisms.

Weighted current learning-material utilization estimate:
- approximately 46% at mechanism level.
- approximately 34% at end-to-end learner-flow level.

Reason:
- Snap already has substantial authorship, sensory and progressive-writing machinery.
- Hide already has meaningful semantic/Hanja structure.
- Ready already has Learning Master subject profiles.
- But the material-derived mechanisms are not yet consistently routed through the rebuilt end-to-end Learning Engine → specialist flow.

## 8. Closure

material atoms = 12
reflected atoms = 12
UNMAPPED_MATERIAL = 0
SILENT_LOSS = 0
FALSE_CONVERGENCE = 0
C2S_COMPILE_CLOSED = true
REFLECTION_COMPLETE = true
DOWNSTREAM_IMPLEMENTATION_COMPLETE = false

No Ready / Hide / Snap product code was modified in this reflection pass.
