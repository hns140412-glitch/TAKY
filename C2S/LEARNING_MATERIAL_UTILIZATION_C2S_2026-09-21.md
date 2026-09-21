# LEARNING MATERIAL UTILIZATION C2S — 2026-09-21

Status: C2S_COMPILE_CLOSED__REFLECTION_OPEN
Scope: Learning Engine + Learning App Family utilization of user-supplied learning-reference materials
Authority: TKY-C2S-001 + current Learning App Family integration contract

## 0. Purpose

This compile is NOT a book/content copy exercise.
It converts the attached materials into reusable learning-design atoms and routes each atom to the correct owner without transferring domain authority.

Hard boundary:
- External/social/book materials = REFERENCE_ONLY / EVIDENCE_ASSIST.
- Patterns may be adopted only as abstract learning mechanisms.
- Do not copy proprietary page layouts, text, examples, or book sequencing verbatim.
- Source material does not override TAKY / Learning Engine / app canonical ownership.

## 1. Recovered evidence scope

Current attachment set:
- IMG_8285.jpeg
- IMG_8286.jpeg
- IMG_8287.jpeg
- IMG_8288.jpeg
- IMG_8289.jpeg
- IMG_8290.jpeg
- IMG_8291.jpeg
- IMG_8292.jpeg
- IMG_8293.jpeg
- IMG_8294.jpeg

Observed source themes in this set:
1. elementary diary-writing workbook / observation diary
2. realistic elementary speaking/social-situation practice
3. staged writing progression from everyday writing to explanatory/argumentative forms
4. idiom / proverb / four-character idiom practice
5. Hanja learning support
6. travel/contextual reading material
7. multi-stage writing table-of-contents / progression cues

Also considered as same-conversation evidence already supplied by the user:
- diary scaffolding references: scene-first recall, sensory prompting, emotion expression, oral-before-writing
- math-literacy references: read the question, identify what is being asked, avoid calculation-first behavior

The stable binary pointers for those earlier image sets were not re-materialized in this compile, so they are preserved as same-conversation evidence, not as independently file-verified sources.

## 2. Existing owner locks preserved

From the current Learning App Family contract:
- Ready & Set = session/task routing / Planner / Learning Unit context owner.
- Ready Learning Engine = homework interpretation, Learning Unit, Hanja level/grade resolution.
- Hide & Seek = Language Memory & Meaning specialist.
- Snap & Pop = thought / expression / writing / speaking specialist.
- Specialist apps do not take Ready session authority.
- Hide does not independently infer Hanja grade.
- Cross-app context remains advisory learning metadata, not authority transfer.

Therefore:
- writing/diary/speaking patterns route primarily to Snap.
- vocabulary/idiom/Hanja meaning-memory patterns route primarily to Hide.
- subject interpretation / level / sequencing / assignment-to-learning-unit routing stays in Ready Learning Engine.
- scheduling and execution timing stay in Ready Planner.

## 3. Utilization map

| Material pattern | Abstracted learning mechanism | Primary owner | Secondary consumer | Utilization |
|---|---|---|---|---|
| Diary observation / one memorable scene | SCENE_FIRST_RECALL | Snap | Learning Engine | ADOPT_CANDIDATE |
| Sensory questions: what seen/heard/said/felt | SENSORY_RECALL_LADDER | Snap | Hide | ADOPT_CANDIDATE |
| Speak before writing | ORAL_BEFORE_WRITING | Snap | Ready | ADOPT_CANDIDATE |
| 1 sentence → 3 sentences → short text | GRADUAL_EXPRESSION_EXPANSION | Snap | Learning Engine | ADOPT_CANDIDATE |
| Emotion vocabulary / alternative expressions | EXPRESSION_VARIATION | Hide | Snap | ADOPT_CANDIDATE |
| Realistic child social situations | SITUATION_TO_LANGUAGE | Snap | Hide | ADOPT_CANDIDATE |
| Idiom/proverb/four-character idiom | MEANING_CONTEXT_REUSE | Hide | Snap | ADOPT_CANDIDATE |
| Hanja form/meaning/example | FORM_MEANING_USAGE_CHAIN | Hide | Ready Learning Engine | ADOPT_CANDIDATE |
| Hanja level/grade | RESOLVED_LEVEL_CONTEXT | Ready Learning Engine | Hide | PRESERVE_OWNER_LOCK |
| Writing progression across genres | WRITING_SCAFFOLD_GRAPH | Snap | Ready Learning Engine | ADOPT_CANDIDATE |
| Math question-first behavior | QUESTION_BEFORE_CALCULATION | Ready Learning Engine | specialist UIs | ADOPT_CANDIDATE |
| "What is this asking?" self-explanation | PROBLEM_RESTATE | Ready Learning Engine | Snap expression surface | ADOPT_CANDIDATE |
| Travel/context materials | CONTEXTUAL_LANGUAGE_SCENARIO | Learning Engine | Hide/Snap | HOLD_LOW_PRIORITY |

## 4. Core reusable atoms

### LRN-UTIL-001 — Scene-first recall
Type: STRATEGY
Summary: When recalling a day/event, ask for one memorable scene before requesting a full chronology.
Why: reduces blank-page load and produces concrete retrieval cues.
Owner: Snap & Pop
Destination: writing/speaking scaffold runtime
Utilization state: PLANNED

### LRN-UTIL-002 — Sensory recall ladder
Type: STRATEGY
Summary: Retrieve memory through visible detail, sound, spoken words, body/emotion, then convert to language.
Owner: Snap & Pop
Secondary: Hide for expression-memory linkage
Utilization state: PLANNED

### LRN-UTIL-003 — Oral-before-writing
Type: STRATEGY
Summary: Let the child first say the remembered idea in their own words, then preserve that expression when converting to writing.
Constraint: parent/AI should not overwrite child authorship with polished adult prose.
Owner: Snap & Pop
Utilization state: PLANNED

### LRN-UTIL-004 — Progressive output expansion
Type: STRATEGY
Summary: Start with one short sentence and expand only after successful expression: phrase → sentence → 3 sentences → short paragraph → structured text.
Owner: Snap & Pop
Secondary: Learning Engine for difficulty routing
Utilization state: PLANNED

### LRN-UTIL-005 — Expression variation
Type: REQUIREMENT
Summary: Repetitive words such as "재미있었다" should trigger optional alternative-expression suggestions tied to the actual scene/emotion, not generic synonym dumping.
Owner: Hide & Seek
Consumer: Snap & Pop
Utilization state: PLANNED

### LRN-UTIL-006 — Situation-to-language
Type: STRATEGY
Summary: Teach speaking/writing through realistic child situations and let the learner produce a response before showing a model.
Owner: Snap & Pop
Secondary: Hide for phrase/meaning memory
Utilization state: PLANNED

### LRN-UTIL-007 — Meaning-context-reuse
Type: STRATEGY
Summary: Idioms/proverbs/four-character idioms should be learned as meaning → situation → example → learner reuse, not definition-only memorization.
Owner: Hide & Seek
Consumer: Snap & Pop
Utilization state: PLANNED

### LRN-UTIL-008 — Hanja form-meaning-usage chain
Type: STRATEGY
Summary: Hanja memory should link character form / core meaning / familiar compound or context / retrieval cue.
Owner: Hide & Seek
Constraint: level/grade is supplied by Ready Learning Engine; Hide does not infer it.
Utilization state: PLANNED

### LRN-UTIL-009 — Writing scaffold graph
Type: STRATEGY
Summary: Writing genres should share reusable scaffold nodes (recall, order, reason, example, comparison, conclusion) rather than separate hard-coded templates per worksheet.
Owner: Snap & Pop
Secondary: Ready Learning Engine
Utilization state: PLANNED

### LRN-UTIL-010 — Question before calculation
Type: STRATEGY
Summary: In math, require comprehension of the full question and what is being asked before computation begins.
Owner: Ready Learning Engine
Utilization state: PLANNED

### LRN-UTIL-011 — Problem restatement
Type: STRATEGY
Summary: Learner attempts to restate "what this problem is asking" in their own words; fluency is not required, semantic attempt is.
Owner: Ready Learning Engine
Consumer: Snap expression tools where verbalization support is useful
Utilization state: PLANNED

### LRN-UTIL-012 — Preserve child voice
Type: CONSTRAINT
Summary: AI/parent support may scaffold recall and structure, but should not silently replace the child's wording with adult-level polished output.
Owner: Learning App Family
Destinations: Snap authorship guard + Learning Engine prompting policy
Utilization state: PRESERVE / EXPAND

## 5. App-level utilization design

### Ready & Set / Learning Engine
Use the materials to improve:
- assignment interpretation
- level/difficulty routing
- scaffold selection
- subject-independent metacognition
- "question before action" policies
- handoff context to specialists

Do NOT:
- own vocabulary memory
- write the child's answer
- duplicate Snap/Hide specialist UIs

### Hide & Seek
Use the materials to improve:
- expression vocabulary memory
- idiom/proverb/Hanja meaning networks
- meaning → context → retrieval → reuse
- cumulative Language Memory
- Memory Ladder prompts

Do NOT:
- own diary/writing workflow
- infer Hanja grade/level
- own Ready homework/task scheduling

### Snap & Pop
Use the materials to improve:
- scene-first recall
- oral-before-writing
- sensory cueing
- sentence expansion
- writing scaffold graph
- realistic speaking situations
- child-authorship preservation

Do NOT:
- claim language mastery state owned by Hide
- infer assignment authority owned by Ready

## 6. Reuse-priority classification

P0 — high-value common learning mechanism
- SCENE_FIRST_RECALL
- ORAL_BEFORE_WRITING
- QUESTION_BEFORE_CALCULATION
- PROBLEM_RESTATE
- PRESERVE_CHILD_VOICE

P1 — high-value specialist mechanism
- SENSORY_RECALL_LADDER
- GRADUAL_EXPRESSION_EXPANSION
- EXPRESSION_VARIATION
- MEANING_CONTEXT_REUSE
- FORM_MEANING_USAGE_CHAIN
- SITUATION_TO_LANGUAGE

P2 — later enrichment
- WRITING_SCAFFOLD_GRAPH full genre coverage
- CONTEXTUAL_LANGUAGE_SCENARIO / travel material

## 7. Non-adoption / caution

Do not adopt as-is:
- proprietary worksheet page structure
- book-specific sequence or exact exercise wording
- commercial book claims as objective learning evidence
- social-media recommendation ranking as canonical authority
- adult-generated "ideal answer" that suppresses learner voice
- one-size-fits-all fixed prompts that make the app feel like a worksheet clone

## 8. Downstream reflection routes

Reflection is intentionally separate from this C2S compile.

Required downstream reflection:
1. Learning Engine: register shared scaffold-selection concepts, question-first comprehension and resolved-level ownership.
2. Snap: map writing/speaking atoms into rebuild architecture after current structural runtime stabilization.
3. Hide: map language-memory atoms into rebuild architecture without taking writing or Hanja-level authority.
4. Ready: expose only resolved learning context needed by specialist scaffold selection.
5. Cross-app: add regression checks that learning context does not transfer authority.

## 9. Closure

Recovered-scope material atoms: 12
Mapped material atoms: 12
UNMAPPED_MATERIAL = 0
SILENT_LOSS = 0
FALSE_CONVERGENCE = 0

Open limitations:
- source efficacy claims were not independently validated;
- current 10 files are visual reference evidence, not full book contents;
- earlier same-conversation image sets were semantically recovered but not rematerialized as stable binary pointers in this compile.

C2S_COMPILE_CLOSED = true
REFLECTION_COMPLETE = false
DOWNSTREAM_IMPLEMENTATION_COMPLETE = false
