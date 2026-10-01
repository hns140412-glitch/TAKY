# TAKY Learning Evidence I/O + Language Usage Kind — Closure Update 2026-10-02

Status: CLOSED / BRANCH VALIDATED / HUMAN APPROVAL GATE
Main merge: HOLD
CURRENT promotion: HOLD
Canonical promotion: HOLD
Deployment: HOLD

## 1. Closed learning loop

PLANNER ALLOCATION
-> READY EXECUTION
-> READY / HIDE / SNAP / IMAGINATION CLOUD RAW EVIDENCE
-> TAKY LEARNING ENGINE
-> REVIEW NEED / LEARNING INTENSITY / RECOMMENDED QUANTITY INTENT /
   QUESTION-HINT-GROWTH INTENT
-> READY PLANNER DATE + ACTUAL QUANTITY MATERIALIZATION
-> READY EXECUTION

Hard ownership:
- Ready = execution facts
- Hide = memory / retrieval evidence
- Snap = raw language / thinking production evidence
- Imagination Cloud = support observation only
- Learning Engine = interpretation / review need / intensity / recommended quantity / growth intent
- Planner = date / calendar placement / actual allocated quantity

## 2. Common evidence contract

Official:
- LEARNING/contracts/learning-evidence-io-contract.js
- LEARNING/contracts/learning-engine-output-contract.js
- LEARNING/adapters/canonical-evidence.js
- LEARNING/contracts/imagination-cloud-evidence-contract.js

Reference roles remain separate:
- CURRICULUM_ALIGNMENT
- LEXICAL_SEMANTICS
- LANGUAGE_USAGE
- PEDAGOGICAL_USAGE
- GENERAL_REFERENCE

## 3. LANGUAGE_USAGE evidence-kind split

Official:
- LEARNING/contracts/language-usage-evidence-kind-contract.js

Evidence kinds:
- EXAMPLE_SENTENCE
  - context example / phrase occurrence cross-check only
  - NOT collocation frequency / grammar authority / universal naturalness
- DEPENDENCY_PATTERN
  - grammar / dependency / collocation candidate support
  - NOT universal naturalness or grade authority
- CHILD_ADULT_SPOKEN_DEPENDENCY_PATTERN
  - spoken grammar / spoken chunk candidate support
  - NOT grade-5 prescription
- PEDAGOGICAL_USAGE
  - expression chunk / grammar pattern / question frame / production target
  - NOT corpus frequency authority

Index Owner must verify evidence kind.
App payload, filename or source title cannot self-assign it.

## 4. Learning Index consumption

Learning Index preserves:
- learning_evidence_role
- learning_evidence_kind

Growth policy consumes LANGUAGE_USAGE by capability.

Example:
Tatoeba EXAMPLE_SENTENCE may supply usage_example_sentences.
It cannot populate natural_collocations or grammar_patterns.

A Tatoeba-only index therefore does NOT close:
- dependency pattern gap
- collocation candidate gap
- corpus grammar-pattern gap
- frequency authority
- universal naturalness

## 5. Current usage source state

Precheck:
MIGRATION/INDEX_OWNER/ENGLISH_LANGUAGE_USAGE_PRECHECK_2026-10-02_V1.json

Ready for explicit human Index decision:
- ENGLISH_USAGE_TATOEBA_TEXT
- evidence kind = EXAMPLE_SENTENCE
- license = CC-BY-2.0-FR
- attribution required

Still HOLD:
- UD English EWT
  - DEPENDENCY_PATTERN
  - CC-BY-SA-4.0 compatibility review open
- UD English CHILDES
  - CHILD_ADULT_SPOKEN_DEPENDENCY_PATTERN
  - ShareAlike + age/context transfer review open

Approval packet:
HANDOFF/LANGUAGE_USAGE_PARTIAL_INDEX_APPROVAL_PACKET_2026-10-02_V1.json

Approval packet != approval.
No promotion executed.

## 6. Existing indexed reference state

V27:
- CURRICULUM_ALIGNMENT = 177 INDEXED
- LEXICAL_SEMANTICS = OEWN 2025 x1 INDEXED
- LANGUAGE_USAGE = 0 INDEXED

V27 remains:
- NOT CURRENT
- NOT CANONICAL
- no main merge
- no deployment

## 7. Final validation

Validated SHA:
6fa518c5d44aa940e9bbbd3f61b48d9a098485c4

- TAKY Mining Indexing Learning Integration
  run 36942812937 — SUCCESS
- TAKY Enforcement Replay
  run 36942812888 — SUCCESS

Specialist branches remain previously validated:
- Ready Integration / Runtime / Bridge: PASS
- Hide Bridge / Validate: PASS
- Snap Bridge / Validate: PASS

## 8. Candidate-only Hide enhancements

Still NOT CORE:
- per-word automatic memory-state routing
- adaptive past-word ratio
- delayed-recall automation

## 9. Next gate

Human approval is required before indexing Tatoeba as:
LANGUAGE_USAGE / EXAMPLE_SENTENCE only.

If approved:
Index Owner receipt
-> new index revision
-> Learning Index rebuild
-> verify example-sentence capability closes only
-> verify dependency/collocation gaps remain OPEN
-> stop again before CURRENT / CANONICAL / main / deployment.
