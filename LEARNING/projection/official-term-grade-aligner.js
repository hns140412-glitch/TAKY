'use strict';

const fs=require('node:fs');
const crypto=require('node:crypto');

const VERSION='TAKY_OFFICIAL_TERM_GRADE_ALIGNER_V1';
const SUBJECT_KO=Object.freeze({
  KOREAN:'국어',SOCIAL:'사회',SCIENCE:'과학',MATH:'수학',ENGLISH:'영어'
});
const clean=v=>String(v??'').trim();
const uniq=a=>[...new Set(a.filter(Boolean))];

function sha256(file){
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}
function loadSources({registry_path,unit_map_path}={}){
  if(!registry_path||!unit_map_path)throw new Error('OFFICIAL_SOURCE_PATHS_REQUIRED');
  delete require.cache[require.resolve(registry_path)];
  delete require.cache[require.resolve(unit_map_path)];
  const registry=require(registry_path);
  const unit=require(unit_map_path);
  if(registry?.version!=='0.3.0'||registry?.RECORDS?.length!==177)
    throw new Error('OFFICIAL_STANDARD_REGISTRY_VERSION_OR_COUNT_MISMATCH');
  if(unit?.version!=='0.2.2'||unit?.RECORDS?.length!==196)
    throw new Error('OFFICIAL_UNIT_MAP_VERSION_OR_COUNT_MISMATCH');
  return {
    registry,unit,
    provenance:{
      registry:{version:registry.version,snapshot_sha256:sha256(registry_path),source_file_sha256:clean(registry.source_file_sha256)||null,records:registry.RECORDS.length},
      unit_map:{version:unit.version,snapshot_sha256:sha256(unit_map_path),source_file_sha256:clean(unit.source_file_sha256)||null,records:unit.RECORDS.length},
      curriculum_notice:registry.DATASET?.subject_curriculum_notice||null,
      framework_notice:registry.DATASET?.current_framework_notice||null,
      unit_source_id:unit.DATASET?.source_id||null,
      unit_source_url:unit.DATASET?.source_url||null
    }
  };
}
function exactTermSignal(term,row){
  const t=clean(term);
  if(!t)return false;
  return Array.isArray(row?.keywords)&&row.keywords.some(k=>clean(k)===t);
}
function alignTerm(term={},sources={}){
  const registry=sources.registry,unit=sources.unit;
  if(!registry||!unit)throw new Error('OFFICIAL_SOURCES_REQUIRED');
  const word=clean(term.term);
  const subjectId=clean(term.subject).toUpperCase();
  const subjectKo=SUBJECT_KO[subjectId]||clean(term.subject_ko);
  if(!word||!subjectKo)return {state:'UNALIGNED',reason:'TERM_AND_SUBJECT_REQUIRED'};

  const standardHits=registry.RECORDS.filter(row=>
    row.subject===subjectKo && exactTermSignal(word,row)
  );
  const directUnitHits=unit.GROUPS.filter(group=>
    group.subject===subjectKo && clean(group.unit_title).includes(word)
  );
  const codeSet=new Set(standardHits.map(x=>x.code));
  const mappedRows=unit.RECORDS.filter(row=>
    row.subject===subjectKo && codeSet.has(row.standard_code)
  );
  const allUnitRows=[...mappedRows,...directUnitHits.flatMap(group=>
    group.codes.map(standard_code=>({
      standard_code,subject:group.subject,grade:group.grade,semester:group.semester,
      unit_no:group.unit_no,unit_title:group.unit_title,source_page:group.source_page,
      direct_unit_title_match:true
    }))
  )];
  const uniqueUnitRows=[];
  const seen=new Set();
  for(const row of allUnitRows){
    const key=[row.standard_code,row.grade,row.semester,row.unit_title].join('|');
    if(seen.has(key))continue;seen.add(key);uniqueUnitRows.push(row);
  }
  const grades=uniq(uniqueUnitRows.map(x=>Number(x.grade)).filter(x=>x===5||x===6)).sort();
  const stages=grades.map(g=>'E'+g);
  const evidence=[];
  for(const row of standardHits)evidence.push({
    kind:'OFFICIAL_STANDARD_EXACT_KEYWORD',
    standard_code:row.code,subject:row.subject,domain:row.domain,
    matched_term:word,source_id:row.source
  });
  for(const row of uniqueUnitRows)evidence.push({
    kind:row.direct_unit_title_match?'OFFICIAL_UNIT_TITLE_EXACT_TERM':'OFFICIAL_STANDARD_TO_UNIT_MAP',
    standard_code:row.standard_code,grade:row.grade,semester:row.semester,
    unit_title:row.unit_title,source_page:row.source_page,source_id:unit.DATASET?.source_id||null
  });

  if(!evidence.length||!stages.length){
    return {
      state:'UNALIGNED',
      reason:evidence.length?'EXACT_GRADE_MAPPING_NOT_AVAILABLE':'NO_EXACT_OFFICIAL_TERM_SIGNAL',
      term:word,subject:subjectId,evidence
    };
  }
  const refs=uniq([
    ...standardHits.map(x=>'OFFICIAL_STANDARD:'+x.code+':'+x.source),
    ...uniqueUnitRows.map(x=>'OFFICIAL_UNIT:'+x.grade+'-'+x.semester+':'+x.unit_title+':'+(unit.DATASET?.source_id||'UNIT_MAP'))
  ]);
  return {
    state:'VERIFIED',
    authority_class:'OFFICIAL_CURRICULUM_AND_UNIT_MAPPING_EVIDENCE',
    term:word,subject:subjectId,
    school_stages:stages,
    grade_min:grades[0],
    grade_max:grades[grades.length-1],
    source_ref:refs.join('|'),
    evidence
  };
}
function alignCatalog(terms=[],sources={}){
  const aligned=[],unresolved=[];
  for(const raw of terms){
    const hit=alignTerm(raw,sources);
    const next={...raw};
    if(hit.state==='VERIFIED'){
      next.school_stages=hit.school_stages;
      next.grade_min=hit.grade_min;
      next.grade_max=hit.grade_max;
      next.grade_alignment={
        state:'VERIFIED',
        authority_class:hit.authority_class,
        source_ref:hit.source_ref,
        reviewed:true
      };
      next.official_alignment=hit;
      aligned.push(next);
    }else{
      next.official_alignment=hit;
      unresolved.push(next);
    }
  }
  return {aligned,unresolved,terms:[...aligned,...unresolved]};
}
module.exports=Object.freeze({VERSION,SUBJECT_KO,loadSources,alignTerm,alignCatalog});
