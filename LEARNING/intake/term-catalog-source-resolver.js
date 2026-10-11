'use strict';

const fs=require('node:fs');
const path=require('node:path');

const VERSION='TAKY_TERM_CATALOG_SOURCE_RESOLVER_V3';
const LEGACY_SCHEMA='TAKY_TERM_DECODER_ALIGNED_CATALOG_V1';
const PRELEARNED_SCHEMA='TAKY_SUBJECT_TERM_UNIVERSE_56_V1';
const ELEMENTARY_SCHEMA='TAKY_SUBJECT_TERM_UNIVERSE_ELEMENTARY_V1';
const clean=v=>String(v??'').trim();
const upper=v=>clean(v).toUpperCase();

function stageOf(profile={}){
  const stage=upper(profile.school_stage||profile.schoolStage);
  return /^(?:E[1-6]|M[1-3])$/.test(stage)?stage:'';
}

function termStages(term={}){
  if(Array.isArray(term.school_stages))return [...new Set(term.school_stages.map(upper).filter(Boolean))];
  const grades=Array.isArray(term.grades)?term.grades:[];
  return [...new Set(grades.map(Number).filter(g=>g>=1&&g<=9).map(g=>g<=6?'E'+g:'M'+(g-6)))];
}

function isPrelearned(data={}){
  return [PRELEARNED_SCHEMA,ELEMENTARY_SCHEMA].includes(data.schema);
}
function sourceMeta(data={},absolute='',allowProvisional=true){
  if(isPrelearned(data)){
    const elementary=data.schema===ELEMENTARY_SCHEMA;
    return {
      source_ref:clean(data.source_ref)||absolute,
      authority_class:clean(data.authority_class)||(elementary
        ?'OFFICIAL_ELEMENTARY_STANDARD_GRADE_BAND+NIKL_LEXICAL_ENRICHMENT'
        :'OFFICIAL_STANDARD_KEYWORD_WITH_GRADE_UNIT_MAPPING+NIKL_LEXICAL_ENRICHMENT'),
      allow_provisional:false,
      official_alignment_summary:{verified:Array.isArray(data.terms)?data.terms.length:0,provisional:0},
      official_source_provenance:{
        kind:elementary?'PRELEARNED_ELEMENTARY_TERM_UNIVERSE':'PRELEARNED_TERM_UNIVERSE',
        schema:data.schema,
        stages:Array.isArray(data.stages)?data.stages:null,
        source_provenance:data.source_provenance||null
      }
    };
  }
  return {
    source_ref:clean(data.source_ref)||absolute,
    authority_class:clean(data.authority_class),
    allow_provisional:allowProvisional===true,
    official_alignment_summary:data.official_alignment_summary||null,
    official_source_provenance:data.official_source_provenance||null
  };
}

function create({catalogPath,allowProvisional=true}={}){
  if(!catalogPath)throw new Error('TERM_CATALOG_PATH_REQUIRED');
  const absolute=path.resolve(String(catalogPath));
  let cached=null,cachedMtimeMs=-1;

  function load(){
    const stat=fs.statSync(absolute);
    if(cached&&stat.mtimeMs===cachedMtimeMs)return cached;
    const parsed=JSON.parse(fs.readFileSync(absolute,'utf8').replace(/^\uFEFF/,''));
    const validSchema=[LEGACY_SCHEMA,PRELEARNED_SCHEMA,ELEMENTARY_SCHEMA].includes(parsed?.schema);
    if(!validSchema||!Array.isArray(parsed.terms))throw new Error('TERM_CATALOG_INVALID');
    cached=parsed;
    cachedMtimeMs=stat.mtimeMs;
    return parsed;
  }

  return async function resolveCurriculumTerms({subject,learner_profile={}}={}){
    const wanted=upper(subject);
    if(!wanted)throw new Error('TERM_SUBJECT_REQUIRED');
    const data=load();
    const learnerStage=stageOf(learner_profile);
    let terms=data.terms.filter(x=>upper(x.subject)===wanted);
    if(learnerStage){
      terms=terms.filter(x=>{
        const stages=termStages(x);
        return !stages.length||stages.includes(learnerStage);
      });
    }
    const meta=sourceMeta(data,absolute,allowProvisional);
    return {
      resolver_version:VERSION,
      source_schema:data.schema,
      source_ref:meta.source_ref,
      authority_class:meta.authority_class,
      allow_provisional:meta.allow_provisional,
      official_alignment_summary:meta.official_alignment_summary,
      official_source_provenance:meta.official_source_provenance,
      learner_stage_filter:learnerStage||null,
      terms
    };
  };
}

module.exports=Object.freeze({
  VERSION,LEGACY_SCHEMA,PRELEARNED_SCHEMA,ELEMENTARY_SCHEMA,stageOf,termStages,create
});
