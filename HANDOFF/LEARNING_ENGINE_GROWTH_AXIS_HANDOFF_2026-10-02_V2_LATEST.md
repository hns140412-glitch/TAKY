# TAKY Learning Engine Growth Axis — HANDOFF V2 2026-10-02

Status: VALIDATED_CANDIDATE_CORE_DIRECTION_V2
Implementation authorization: BRANCH_ONLY
Main merge: HOLD
Deployment: HOLD

## 1. Core growth loop

Learning Engine is a growth engine, not only a correctness/review engine.

Growth dimensions:
- VOCABULARY
- GRAMMAR
- EXPRESSION
- THINKING
- ENGLISH_THINKING

Canonical loop:

SOURCE UNIVERSE
-> MINING ENGINE
-> MINING INDEX / INDEX OWNER
-> LEARNING INDEX
-> LEARNER EVIDENCE
-> LANGUAGE GROWTH PROFILE
-> GROWTH CONTROL
-> HIDE / SNAP EXECUTION
-> APPLIED CHALLENGE CONTEXT + RESULT
-> DIMENSION VERIFICATION WHEN AVAILABLE
-> GROWTH OUTCOME FEEDBACK CANDIDATE
-> RECENT + STABILITY WINDOW RE-DERIVATION
-> NEXT GROWTH CONTROL

## 2. Source-role authority

Language-growth reference evidence is role-separated.

- CURRICULUM_ALIGNMENT
  - official education/curriculum
  - grade / achievement-standard / exposure alignment

- LEXICAL_SEMANTICS
  - dictionary / lexical reference
  - easy-English meaning / lexical semantics

- LANGUAGE_USAGE
  - corpus / usage evidence
  - expression chunks / collocations / natural usage

- PEDAGOGICAL_USAGE
  - curated pedagogical evidence
  - scaffolds / English-thinking support

- GENERAL_REFERENCE
  - no automatic language-growth authority

Roles are derived from indexed provenance tags.
Filename/title inference is forbidden.
Ambiguous role provenance fails closed.

Hard locks:
CURRICULUM AUTHORITY != LEXICAL AUTHORITY
LEXICAL AUTHORITY != GRADE ALIGNMENT
USAGE EVIDENCE != CURRICULUM AUTHORITY

## 3. Role-specific Mining gaps

Learning Engine checks whether the required role is present, not whether any source exists.

Reference gaps:
- CURRICULUM_ALIGNMENT_REFERENCE_REQUIRED
- LEXICAL_SEMANTICS_REFERENCE_REQUIRED
- LANGUAGE_USAGE_REFERENCE_REQUIRED
- PEDAGOGICAL_LANGUAGE_SUPPORT_REFERENCE_REQUIRED

Route:

LEARNING GAP
-> LEARNING INDEX ROLE CHECK
-> MINING INDEX provenance-tag check
-> matching role exists: INDEX_REQUERY
-> matching role absent: MINING_REQUEST
-> acquisition
-> Index-owner review
-> provenance role retained in search projection
-> Learning Index rebuild
-> Learning Engine requery

Learner-performance gaps remain separate:
LEARNING ENGINE -> HIDE / SNAP specialist evidence acquisition

External Mining is forbidden for learner-performance gaps.

## 4. Growth-control vector

Learning Engine emits:
- evidence_confidence: LOW / MEDIUM / HIGH
- learning_intensity:
  - SUPPORT_BUILD
  - BUILD_CONNECT
  - STRETCH_TRANSFER
- expression_level:
  - L1_CHUNK_OR_PHRASE
  - L2_SIMPLE_SENTENCE
  - L3_EXPANDED_SENTENCE
  - L4_REASONED_RESPONSE
  - L5_TRANSFER_CREATION
- easy_english_level
- question_depth: 1..5
- hint_strength
- hint_fade
- target_dimensions
- challenge_direction

Age/grade changes language load, not cognitive ceiling.

## 5. Evidence quality and applied difficulty

Growth evidence distinguishes:
- observation vs verified evidence
- assisted vs unassisted
- transfer evidence
- cross-app convergence
- applied challenge context

Snap returns the conditions under which the result occurred:
- learning_intensity
- expression_level
- question_depth
- hint_strength
- hint_fade
- challenge_direction

This is SPECIALIST_EXECUTION_CONTEXT_ONLY.

Strong-scaffold success and minimal-cue success are not equivalent evidence.

## 6. Longitudinal anti-oscillation

Growth Profile V3 uses:

RECENT WINDOW
- drives immediate support
- default candidate limit 8 relevant signals

STABILITY WINDOW
- guards promotion/demotion
- default candidate limit 24 relevant signals

Stability states:
- STRETCH_STABLE
- PROMOTION_CANDIDATE_NOT_STABLE
- TEMPORARY_SUPPORT_WITHOUT_LONG_TERM_DEMOTION
- SUPPORT_NEED_STABLE
- RECENT_EVIDENCE_INSUFFICIENT
- HOLD_OR_DEVELOP

Recent weakness may increase help without erasing stable growth.
Recent strength alone cannot trigger TRANSFER_PUSH until stable evidence supports it.

## 7. Dimension-level growth rubric

Snap production completion alone remains UNKNOWN quality.

Permitted HUMAN_GROWTH_RUBRIC can verify dimensions separately:
- VOCABULARY
- GRAMMAR
- EXPRESSION
- THINKING
- ENGLISH_THINKING

Dimension outcome:
- SUCCESS
- PARTIAL
- FAIL

Global receipt outcome remains null.
Dimension rubric cannot become global correctness/mastery.
Reviewed UNKNOWN placeholders are replaced only for matching dimensions.

## 8. App ownership

Hide & Seek:
- memory/retrieval evidence producer
- TRACE/LINK may emit objective vocabulary observations
- CORE spelling success != general vocabulary growth
- no long-term growth authority

Snap & Pop:
- re-resolves authenticated central growth decision
- executes expression/thinking prompts
- preserves child authorship
- returns applied challenge context and production evidence
- no completion->mastery promotion

Ready & Set:
- assignment decomposition
- execution-load metadata
- local-first operational fallback
- NOT learner-state authority
- NOT growth-control authority
- local memory review = LOCAL_FALLBACK_ONLY
- central TAKY Learning Engine takes precedence

Planner:
- sole dated allocation owner

## 9. Outcome feedback

Single result may create only an adjustment candidate:
- OBSERVE_MORE
- HOLD_LEVEL
- FADE_HINT_ONE_STEP_CANDIDATE
- HOLD_LEVEL_ADJUST_HINT_CANDIDATE
- INCREASE_SUPPORT_CANDIDATE
- KEEP_SUPPORT_AND_RECHECK
- PRESERVE_OR_STRETCH_CANDIDATE

Single result cannot directly mutate learner state or authorize control change.

## 10. Memory routing proposal remains separate

Still CANDIDATE / NOT CORE AUTHORITY:
- per-word automatic memory-state branching
- adaptive past-word proportion
- delayed-recall automation

Do not promote these merely because candidate code/tests exist.

## 11. Validated branches

TAKY:
- taky/learning-mining-runtime-integration-2026-10-01

Hide:
- taky/hide-memory-routing-learning-engine-2026-10-02

Snap:
- taky/snap-growth-engine-handoff-2026-10-02

Ready:
- taky/ready-growth-authority-cleanup-2026-10-02

## 12. Validation evidence

Latest TAKY code validation before documentation-only reconciliation:
- TAKY Mining Indexing Learning Integration: run 36896749821 — SUCCESS
- TAKY Enforcement Replay: run 36896749838 — SUCCESS
- includes Full Mining Indexing Learning growth E2E — SUCCESS

Ready authority cleanup:
- Ready Integration CI run 36894437163 — SUCCESS
- Hide Memory Review Roundtrip run 36894436925 — SUCCESS

Hide growth evidence:
- Learning Runtime Bridge Validation run 36890466371 — SUCCESS
- Validate Hide & Seek run 36890466576 — SUCCESS

Snap growth control / rubric path:
- Learning Runtime Bridge Validation run 36894758970 — SUCCESS
- Validate Snap & Pop run 36894758879 — SUCCESS

## 13. Current OPEN — keep separate from completed work

1. Hierarchical growth scope
   - current primary state remains member x subject x concept_skill_target
   - item/lexical evidence exists but item -> skill -> subject roll-up policy needs explicit contract
   - must avoid one word or one production overgeneralizing to subject-wide ability

2. Automated production assessment
   - current trustworthy dimension promotion path is human growth rubric
   - any AI/automatic grammar/expression/thinking verifier requires a separate calibrated verifier policy and provenance
   - no silent auto-grading

3. Real source acquisition mapping
   - source roles are now defined and Mining gaps are wired
   - production provider/source registry for curriculum/dictionary/corpus/pedagogy should be verified separately

4. Promotion/current authority
   - branch validation does not equal main/CURRENT promotion
   - merge/deployment remains HOLD

No Netlify deployment, main merge or CURRENT promotion is authorized by this handoff.
