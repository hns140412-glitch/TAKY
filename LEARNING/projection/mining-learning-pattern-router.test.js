'use strict';
const assert=require('node:assert/strict');
const Router=require('./mining-learning-pattern-router.js');

const registry=Router.load();
assert.equal(registry.authority_class,'REFERENCE_PATTERN_ONLY_NOT_CURRICULUM_AUTHORITY');
assert.equal(registry.schema,'TAKY_LEARNING_REFERENCE_PATTERN_REGISTRY_V2');
assert.ok(registry.sources.some(x=>x.source_id==='REF-081'));
assert.ok(registry.sources.some(x=>x.source_id==='REF-085'));

const rich=Router.derive({
  term:'광합성',hanja:'光合成',meaning:'빛으로 양분을 만드는 과정',
  components:[{text:'光',meaning:'빛'}],
  families:[{anchor:'光',words:['광선']}],
  units:['생물의 구조와 에너지'],
  conceptLinks:['빛','식물','양분'],
  concept:{summary:'식물이 빛을 이용해 양분을 만든다',relations:['빛 → 양분'],compare:['호흡']}
});
assert.ok(rich.pattern_ids.includes('P_MORPHEME_FAMILY'));
assert.ok(rich.pattern_ids.includes('P_CONCEPT_RELATION'));
assert.ok(rich.pattern_ids.includes('P_COMPARE_CONTRAST'));
assert.ok(rich.pattern_ids.includes('P_CONTEXT_TRANSFER'));
assert.ok(rich.pattern_ids.includes('P_VISUAL_CONCEPT_CARD'));
assert.ok(rich.pattern_ids.includes('P_CONCEPT_GRAPH'));
assert.ok(rich.pattern_ids.includes('P_BLANK_RECALL'));
assert.deepEqual(rich.eligible_modes,['TRACE','LINK','CORE','RECALL']);
assert.ok(rich.source_refs.some(x=>x.includes('edu_navi')));
assert.ok(rich.source_refs.includes('INDEX:REF-085'));
assert.equal(rich.presentation.visual_concept_card,true);
assert.equal(rich.presentation.concept_graph,true);
assert.equal(rich.presentation.blank_recall,true);
assert.equal(rich.recovery.concept_gap,false);
assert.ok(rich.guards.includes('PATTERN_DOES_NOT_SET_GRADE'));

const conceptOnly=Router.derive({
  term:'저기압',meaning:'주변보다 기압이 낮은 곳',units:['날씨와 우리 생활'],
  conceptLinks:['기압','날씨'],concept:{summary:'저기압과 날씨의 관계'}
});
assert.equal(conceptOnly.eligible_modes.includes('TRACE'),false);
assert.equal(conceptOnly.eligible_modes.includes('LINK'),true);
assert.equal(conceptOnly.eligible_modes.includes('CORE'),true);
assert.equal(conceptOnly.eligible_modes.includes('RECALL'),true);

const recovery=Router.derive({term:'저기압',meaning:'주변보다 기압이 낮은 곳',units:['날씨와 우리 생활'],conceptLinks:['기압','날씨'],concept:{summary:'저기압과 날씨의 관계'}},{evidence_summary:{wrong:2}});
assert.ok(recovery.pattern_ids.includes('P_ERROR_TO_CONCEPT_GAP'));
assert.equal(recovery.recovery.route,'TARGETED_CONCEPT_REVIEW');
assert.ok(recovery.source_refs.includes('INDEX:REF-081'));
const singleMiss=Router.derive({term:'저기압',meaning:'주변보다 기압이 낮은 곳',units:['날씨와 우리 생활'],conceptLinks:['기압']},{evidence_summary:{wrong:1}});
assert.equal(singleMiss.pattern_ids.includes('P_ERROR_TO_CONCEPT_GAP'),false);

const literal=Router.derive({
  term:'퇴적암',hanja:'堆積巖',meaning:'퇴적물이 굳어 만들어진 암석',
  components:[{text:'堆',meaning:'쌓다'},{text:'積',meaning:'쌓다'},{text:'巖',meaning:'바위'}],
  decoder_reference:{source_id:'DAEGU',literal_meaning:'쌓여서 만들어진 바위'},
  units:['지층과 화석'],conceptLinks:['암석']
});
assert.ok(literal.pattern_ids.includes('P_LITERAL_TO_SUBJECT_MEANING'));

console.log('MINING_LEARNING_PATTERN_ROUTER_TEST: PASS');
