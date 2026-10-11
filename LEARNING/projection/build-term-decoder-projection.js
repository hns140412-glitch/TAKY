'use strict';

const fs=require('node:fs');
const path=require('node:path');
const Engine=require('../runtime/learning-engine-runtime.js');
const OfficialAligner=require('./official-term-grade-aligner.js');

const VERSION='TAKY_TERM_DECODER_PROJECTION_BUILDER_V2';
const hideRepo=path.resolve(process.env.HIDE_REPO||'D:\\Git PWA\\Hide & Seek');
const sourceRef='C2S/CHAT_REVIEW_TERM_DECODER_MINING_2026-10-07.json';
const referenceCatalogPath=path.resolve(process.env.TAKY_TERM_REFERENCE_CATALOG||path.join(__dirname,'..','data','term-decoder-reference-catalog-v1.json'));
const catalogPath=path.join(__dirname,'term-decoder-mined-catalog-v1.json');
const outDir=path.join(hideRepo,'data');
const packsPath=path.join(outDir,'learning-term-recommendation-packs-v1.json');
const registryPath=path.resolve(process.env.TAKY_OFFICIAL_REGISTRY||path.join(__dirname,'..','data','official-snapshots','official-standard-registry-v0.3.0.json'));
const unitMapPath=path.resolve(process.env.TAKY_OFFICIAL_UNIT_MAP||path.join(__dirname,'..','data','official-snapshots','official-unit-map-v0.2.2.json'));

function subjectPack(stage,subject,catalog){
  const out=Engine.deriveTermRecommendations({
    learner_profile:{schoolStage:stage},
    subject,
    curriculum_terms:catalog,
    term_evidence:[],
    consumer_app:'HIDE_SEEK',
    limit:36,
    allow_provisional:true
  });
  if(!out.ok)throw new Error('TERM_RECOMMENDATION_FAILED:'+stage+':'+subject+':'+out.reason);
  return {
    school_stage:stage,
    subject,
    recommendation_state:out.recommendation_state,
    cards:out.cards,
    recommendations:out.term_recommendations.map(x=>({
      term_id:x.term_id,term:x.term,priority:x.priority,score:x.score,reasons:x.reasons,
      grade_alignment_tier:x.grade_alignment_tier,source_ref:x.source_ref
    })),
    trace:out.trace
  };
}

const referenceCatalog=JSON.parse(fs.readFileSync(referenceCatalogPath,'utf8'));
if(referenceCatalog?.schema!=='TAKY_TERM_DECODER_REFERENCE_CATALOG_V1'||!Array.isArray(referenceCatalog.terms))throw new Error('TERM_REFERENCE_CATALOG_INVALID');
const provisionalCatalog=referenceCatalog.terms;
const officialSources=OfficialAligner.loadSources({registry_path:registryPath,unit_map_path:unitMapPath});
const alignment=OfficialAligner.alignCatalog(provisionalCatalog,officialSources);
const catalog=alignment.terms;
fs.writeFileSync(catalogPath,JSON.stringify({
  schema:'TAKY_TERM_DECODER_ALIGNED_CATALOG_V1',
  generated_at:new Date().toISOString(),
  builder_version:VERSION,
  authority_class:'MIXED_OFFICIAL_VERIFIED_AND_PROVISIONAL_REFERENCE',
  source_ref:sourceRef,
  reference_catalog_path:path.relative(path.resolve(__dirname,'..','..'),referenceCatalogPath).replace(/\\/g,'/'),
  official_source_provenance:officialSources.provenance,
  official_alignment_summary:{verified:alignment.aligned.length,provisional:alignment.unresolved.length},
  terms:catalog
},null,2)+'\n','utf8');

const subjects=['KOREAN','SOCIAL','SCIENCE','MATH'];
const stages=['E1','E2','E3','E4','E5','E6'];
const byStage={};
for(const stage of stages){
  byStage[stage]={};
  const all=[];
  for(const subject of subjects){
    const pack=subjectPack(stage,subject,catalog);
    byStage[stage][subject]=pack;
    all.push(...pack.cards);
  }
  byStage[stage].ALL={
    school_stage:stage,
    subject:'ALL',
    recommendation_state:all.length?'READY':'NO_ELIGIBLE_GRADE_TERMS',
    cards:all,
    recommendations:subjects.flatMap(s=>byStage[stage][s].recommendations)
  };
}
fs.writeFileSync(packsPath,JSON.stringify({
  schema:'TAKY_HIDE_TERM_RECOMMENDATION_PACKS_V1',
  projection_version:'2026-10-07.2',
  generated_at:new Date().toISOString(),
  generated_by:'TAKY_LEARNING_ENGINE_CORE',
  selector_version:require('../pedagogy/grade-aware-term-selector.js').VERSION,
  runtime_version:require('../runtime/term-recommendation-runtime.js').VERSION,
  source_ref:sourceRef,
  authority_class:'MIXED_OFFICIAL_VERIFIED_AND_PROVISIONAL_REFERENCE',
  official_source_provenance:officialSources.provenance,
  official_alignment_summary:{verified:alignment.aligned.length,provisional:alignment.unresolved.length},
  by_stage:byStage
},null,2)+'\n','utf8');

console.log(JSON.stringify({
  ok:true,builder:VERSION,reference_terms:provisionalCatalog.length,catalog_terms:catalog.length,
  official_verified:alignment.aligned.length,provisional:alignment.unresolved.length,
  official_verified_terms:alignment.aligned.map(x=>x.term),
  catalog_path:catalogPath,packs_path:packsPath,
  e5_science:byStage.E5.SCIENCE.cards.length,e6_science:byStage.E6.SCIENCE.cards.length,
  e5_all:byStage.E5.ALL.cards.length,
  e4_all:byStage.E4.ALL.cards.length
},null,2));
