'use strict';

const VERSION='TAKY_LANGUAGE_USAGE_EVIDENCE_KIND_V1';

const KINDS=Object.freeze({
  EXAMPLE_SENTENCE:{
    capabilities:['CONTEXT_EXAMPLE','PHRASE_OCCURRENCE_CROSS_CHECK'],
    forbids:['COLLOCATION_FREQUENCY','UNIVERSAL_NATURALNESS','GRAMMAR_PATTERN_AUTHORITY']
  },
  DEPENDENCY_PATTERN:{
    capabilities:['GRAMMAR_PATTERN','DEPENDENCY_RELATION','COLLOCATION_CANDIDATE'],
    forbids:['UNIVERSAL_NATURALNESS','GRADE_LEVEL_AUTHORITY']
  },
  CHILD_ADULT_SPOKEN_DEPENDENCY_PATTERN:{
    capabilities:['SPOKEN_GRAMMAR_PATTERN','SPOKEN_CHUNK_CANDIDATE','DEPENDENCY_RELATION'],
    forbids:['GRADE5_PRESCRIPTION','UNIVERSAL_NATURALNESS']
  },
  PEDAGOGICAL_USAGE:{
    capabilities:['EXPRESSION_CHUNK','GRAMMAR_PATTERN','QUESTION_FRAME','PRODUCTION_TARGET'],
    forbids:['CORPUS_FREQUENCY','UNIVERSAL_NATURALNESS']
  }
});

const clean=v=>String(v??'').trim().toUpperCase();

function normalize(kind){
  const k=clean(kind);
  return Object.prototype.hasOwnProperty.call(KINDS,k)?k:null;
}

function permits(kind,capability){
  const k=normalize(kind);
  if(!k)return false;
  return KINDS[k].capabilities.includes(clean(capability));
}

function validateEvidence(item={}){
  const issues=[];
  const kind=normalize(item.usage_evidence_kind||item.language_usage_evidence_kind);
  if(!kind)issues.push('USAGE_EVIDENCE_KIND_INVALID');
  if(item.learning_evidence_role&&item.learning_evidence_role!=='LANGUAGE_USAGE'&&kind!=='PEDAGOGICAL_USAGE')
    issues.push('USAGE_KIND_ROLE_MISMATCH');
  return {ok:issues.length===0,issues,kind};
}

module.exports=Object.freeze({VERSION,KINDS,normalize,permits,validateEvidence});
