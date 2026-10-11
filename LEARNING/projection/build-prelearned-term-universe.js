'use strict';

const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const PatternRouter=require('./mining-learning-pattern-router.js');

const ROOT=path.resolve(__dirname,'..','..');
const DATA=path.join(ROOT,'LEARNING/data');
const SOURCES=path.join(DATA,'sources');
const OUT=path.join(DATA,'prelearned');
fs.mkdirSync(OUT,{recursive:true});

const readJson=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const sha256=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const clean=v=>String(v??'').trim();
const uniq=a=>[...new Set(a.filter(Boolean))];
const isCjk=c=>/[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/.test(c);
const cjkChars=s=>[...clean(s)].filter(isCjk);

const officialPath=path.join(DATA,'official-term-candidates-56-v1.json');
const niklPath=path.join(SOURCES,'nikl-basic-vocab-40000-objects-v1.json');
const surfacePath=path.join(SOURCES,'nikl-basic-vocab-surface-index-v1.json');
const toolPath=path.join(SOURCES,'korean-tool-vocab-verified-token-2026-09-22.txt');
const ambiguityPath=path.join(SOURCES,'nikl-tool-vocab-ambiguity-v1.json');
const policyPath=path.join(SOURCES,'tool-language-lexeme-resolution-policy-v1.json');
const seedPath=path.join(DATA,'term-decoder-reference-catalog-v1.json');
const hanjaRefPath=path.join(OUT,'hanja-reference-mining-v1.json');
const registryPath=path.join(DATA,'official-snapshots','official-standard-registry-v0.3.0.json');
const unitPath=path.join(DATA,'official-snapshots','official-unit-map-v0.2.2.json');
const academicPath=path.join(ROOT,'LEARNING','projection','academic-vocab-1387-level-map-v1.json');

const official=readJson(officialPath);
const nikl=readJson(niklPath);
const surface=readJson(surfacePath);
const tool=readJson(toolPath);
const ambiguity=readJson(ambiguityPath);
const policy=readJson(policyPath);
const seed=readJson(seedPath);
const hanjaRef=fs.existsSync(hanjaRefPath)?readJson(hanjaRefPath):{chars:[]};
const registry=readJson(registryPath);
const unit=readJson(unitPath);
const academic=readJson(academicPath);

const objByKey=new Map(nikl.objects.map(x=>[x.lexeme_key_v1,x]));
const standardByCode=new Map(registry.RECORDS.map(x=>[x.code,x]));
const seedByTerm=new Map((seed.terms||[]).map(x=>[x.subject+'|'+x.term,x]));
const hanjaReferenceByTerm=new Map((hanjaRef.entries||[])
  .filter(x=>['SCIENCE','MATH'].includes(x.subject)&&x.state==='PARSED_REFERENCE')
  .map(x=>[x.subject+'|'+x.term,x]));

const SUBJECT_ID={국어:'KOREAN',사회:'SOCIAL',과학:'SCIENCE',수학:'MATH',영어:'ENGLISH'};
const GRADE_STAGE={5:'E5',6:'E6'};
const NIKL_GRADE_BAND={'1등급':'PRESCHOOL','2등급':'E1-2','3등급':'E3-4','4등급':'E5-6','5등급':'M1-3'};

const charInfo=new Map();
function addCharInfo(ch,meaning,reading,source){
  if(!ch||!isCjk(ch))return;
  const prev=charInfo.get(ch)||{char:ch,meanings:[],readings:[],sources:[]};
  if(clean(meaning))prev.meanings.push(clean(meaning));
  if(clean(reading))prev.readings.push(clean(reading));
  if(clean(source))prev.sources.push(clean(source));
  prev.meanings=uniq(prev.meanings);
  prev.readings=uniq(prev.readings);
  prev.sources=uniq(prev.sources);
  charInfo.set(ch,prev);
}
for(const t of seed.terms||[]){
  const comps=Array.isArray(t.components)?t.components:[];
  for(let i=0;i<comps.length;i++){
    const ch=clean(comps[i].text);
    if([...ch].length!==1)continue;
    let reading='';
    const h=cjkChars(t.hanja);
    if(h.length===clean(t.term).length && h[i]===ch)reading=[...clean(t.term)][i]||'';
    addCharInfo(ch,comps[i].meaning,reading,'TERM_DECODER_REFERENCE_SEED');
  }
}
for(const row of hanjaRef.chars||[]){
  if(!row?.char||!Array.isArray(row.meanings)||!Array.isArray(row.readings))continue;
  if(row.meanings.length!==1||row.readings.length!==1)continue;
  addCharInfo(row.char,row.meanings[0],row.readings[0],'EDUCATION_OFFICE_HANJA_REFERENCE');
}

const familyByChar=new Map();
for(const o of nikl.objects){
  const form=clean(o.original_form);
  if(!form)continue;
  for(const ch of uniq(cjkChars(form))){
    let arr=familyByChar.get(ch);
    if(!arr){arr=[];familyByChar.set(ch,arr);}
    if(arr.length<80)arr.push({word:o.word,form:o.original_form,grade:o.grade,meaning:o.meaning,key:o.lexeme_key_v1});
  }
}
for(const [ch,arr] of familyByChar){
  arr.sort((a,b)=>{
    const ga=Number(String(a.grade).match(/\d/)?.[0]||9), gb=Number(String(b.grade).match(/\d/)?.[0]||9);
    return ga-gb || a.word.length-b.word.length || a.word.localeCompare(b.word,'ko');
  });
  const seen=new Set();
  familyByChar.set(ch,arr.filter(x=>{if(seen.has(x.word))return false;seen.add(x.word);return true;}).slice(0,12));
}

function lexicalCandidates(term){
  const refs=surface.index?.[term]||[];
  return refs.map(r=>objByKey.get(r.k)).filter(Boolean);
}
function pureHanjaForm(form){
  const s=clean(form);
  if(!s)return '';
  const chars=[...s];
  const cjk=chars.filter(isCjk);
  if(!cjk.length)return '';
  return cjk.join('');
}
function gradeBand(grades){
  const gs=uniq((grades||[]).map(Number).filter(g=>g===5||g===6)).sort();
  if(gs.length===2)return '5-6';
  return gs.length?String(gs[0]):'';
}
function componentsFor(hanja,term,seedTerm,termReference=null){
  if(seedTerm?.components?.length)return {components:seedTerm.components,coverage:1,source:'REFERENCE_SEED'};
  const chars=cjkChars(hanja);
  const refChars=cjkChars(termReference?.hanja);
  if(chars.length&&termReference?.components?.length===chars.length&&refChars.join('')===chars.join('')){
    const components=termReference.components.map(x=>({
      text:clean(x.text),meaning:clean(x.meaning),reading:clean(x.reading)
    }));
    if(components.every(x=>x.text&&x.meaning))
      return {components,component_candidates:components,coverage:1,source:'EDUCATION_OFFICE_TERM_REFERENCE'};
  }
  if(!chars.length)return {components:[],coverage:0,source:'NONE'};
  const syll=[...clean(term)];
  const aligned=chars.length===syll.length;
  const comps=chars.map((ch,i)=>{
    const info=charInfo.get(ch);
    return {text:ch,meaning:info?.meanings?.[0]||'',reading:aligned?(syll[i]||''):(info?.readings?.[0]||'')};
  });
  const known=comps.filter(x=>x.meaning).length;
  return {components:known===chars.length?comps:[],component_candidates:comps,coverage:chars.length?known/chars.length:0,source:known===chars.length?'DERIVED_CHAR_GLOSS':'PARTIAL_CHAR_GLOSS'};
}
function familyGroups(hanja){
  return cjkChars(hanja).map(ch=>({
    anchor:ch,
    words:(familyByChar.get(ch)||[]).slice(0,6).map(x=>x.word)
  })).filter(x=>x.words.length);
}
function toolOverlap(term){
  const bands=[];
  for(const b of ['1_2','3_4','5_6']){
    const toks=tool.grade_bands?.[b]?.tokens||[];
    if(toks.includes(term))bands.push(b);
  }
  return bands;
}
function officialContext(row){
  const standards=(row.standards||[]).map(c=>standardByCode.get(c)).filter(Boolean);
  const summaries=uniq(standards.map(x=>clean(x.semantic_summary)));
  const keywords=uniq(standards.flatMap(x=>x.keywords||[]));
  return {summaries,keywords};
}
function lexicalState(cands,seedTerm){
  if(seedTerm?.hanja){
    const exact=cands.filter(x=>pureHanjaForm(x.original_form)===pureHanjaForm(seedTerm.hanja));
    if(exact.length===1)return {state:'RESOLVED_BY_REFERENCE_SEED',preferred:exact[0]};
  }
  if(cands.length===1)return {state:'UNIQUE_EXACT_SURFACE',preferred:cands[0]};
  if(cands.length>1)return {state:'AMBIGUOUS_CONTEXT_REQUIRED',preferred:null};
  return {state:'NO_NIKL_SURFACE_MATCH',preferred:null};
}

const officialTerms=[];
for(const row of official.terms||[]){
  const subject=SUBJECT_ID[row.subject];
  if(!subject || subject==='ENGLISH')continue;
  const stages=uniq((row.grades||[]).map(g=>GRADE_STAGE[g]).filter(Boolean));
  if(!stages.length)continue;
  const seedTerm=seedByTerm.get(subject+'|'+row.term)||null;
  const cands=lexicalCandidates(row.term);
  const lex=lexicalState(cands,seedTerm);
  const preferred=lex.preferred;
  const preferredHanja=pureHanjaForm(preferred?.original_form);
  const seedHanja=pureHanjaForm(seedTerm?.hanja);
  const rawTermReference=hanjaReferenceByTerm.get(subject+'|'+row.term)||null;
  const referenceHanja=pureHanjaForm(rawTermReference?.hanja);
  const referenceBound=!!(rawTermReference&&referenceHanja&&(
    (seedHanja&&referenceHanja===seedHanja)||
    (preferredHanja&&referenceHanja===preferredHanja)
  ));
  const termReference=referenceBound?rawTermReference:null;
  const hanja=seedHanja||preferredHanja;
  const comp=componentsFor(hanja,row.term,seedTerm,termReference);
  const ctx=officialContext(row);
  const conceptSummary=clean(seedTerm?.concept?.summary)||ctx.summaries[0]||'';
  const dictionaryMeaning=clean(seedTerm?.meaning)||clean(preferred?.meaning);
  const meaning=dictionaryMeaning||conceptSummary;
  const meaningSource=dictionaryMeaning?(seedTerm?.meaning?'REFERENCE_SEED':'NIKL_LEXEME'):(conceptSummary?'OFFICIAL_STANDARD_CONTEXT':'NONE');
  const decoderReady=!!meaning && comp.components?.length>0 && comp.coverage===1;
  const formReady=!!hanja;
  const termRecord={
    term_id:'official56:'+subject.toLowerCase()+':'+row.term,
    layer:'SUBJECT_TERMINOLOGY',
    subject,
    subject_ko:row.subject,
    term:row.term,
    school_stages:stages,
    grade_band:gradeBand(row.grades),
    grades:row.grades,
    semesters:row.semesters||[],
    standards:row.standards||[],
    units:row.units||[],
    domains:row.domains||[],
    source_refs:row.source_refs||[],
    grade_alignment:{
      state:'VERIFIED',
      authority_class:'OFFICIAL_STANDARD_KEYWORD_WITH_GRADE_UNIT_MAPPING',
      source_ref:uniq([...(row.source_refs||[]),...(row.standards||[]).map(x=>'STANDARD:'+x)]).join('|'),
      reviewed:true
    },
    lexical:{
      state:lex.state,
      candidate_count:cands.length,
      preferred_key:preferred?.lexeme_key_v1||null,
      candidates:cands.slice(0,8).map(x=>({
        key:x.lexeme_key_v1,grade:x.grade,pos:x.pos_source,origin_type:x.origin_type,
        original_form:x.original_form,meaning:x.meaning,field:x.field
      }))
    },
    meaning,
    meaning_source:meaningSource,
    hanja,
    components:comp.components||[],
    component_candidates:comp.component_candidates||comp.components||[],
    component_coverage:comp.coverage,
    morphology_source:comp.source,
    decoder_reference:termReference?{
      source_id:termReference.source_id,
      authority_class:termReference.authority_class,
      literal_meaning:clean(termReference.literal_meaning),
      source_subject_meaning:clean(termReference.source_subject_meaning),
      binding:'HANJA_MATCH_TO_TRUSTED_LEXICAL_OR_SEED'
    }:null,
    reference_candidate:rawTermReference?{
      source_id:rawTermReference.source_id,
      hanja:referenceHanja||null,
      binding_state:referenceBound?'BOUND':'HELD_CONTEXT_OR_LEXEME_MISMATCH'
    }:null,
    families:hanja?familyGroups(hanja):[],
    conceptLinks:uniq([...(row.domains||[]),...(row.units||[]),...ctx.keywords]).slice(0,16),
    concept:{
      summary:conceptSummary,
      clues:uniq(ctx.keywords).slice(0,12),
      relations:seedTerm?.concept?.relations||[],
      contrast:seedTerm?.concept?.contrast||[],
      hierarchy:uniq([row.subject,...(row.domains||[]),...(row.units||[]),row.term]).slice(0,10),
      compare:seedTerm?.concept?.compare||[]
    },
    example:clean(seedTerm?.example),
    tool_language_overlap:toolOverlap(row.term),
    readiness:{
      recommendation:true,
      lexical_resolution:lex.state,
      hanja_form:formReady,
      decoder_full:decoderReady,
      decoder_form_only:formReady&&!decoderReady
    }
  };
  termRecord.mining_learning_pattern=PatternRouter.derive(termRecord);
  officialTerms.push(termRecord);
}

const toolRecords=[];
for(const band of ['1_2','3_4','5_6']){
  const stages=band==='1_2'?['E1','E2']:band==='3_4'?['E3','E4']:['E5','E6'];
  const toks=tool.grade_bands?.[band]?.tokens||[];
  toks.forEach((token,index)=>{
    const cands=lexicalCandidates(token);
    const lex=lexicalState(cands,null);
    const preferred=lex.preferred;
    const hanja=pureHanjaForm(preferred?.original_form);
    const comp=componentsFor(hanja,token,null);
    toolRecords.push({
      token_id:'tool:'+band+':'+index+':'+token,
      layer:'LEARNING_TOOL_LANGUAGE',
      term:token,
      grade_band:band.replace('_','-'),
      school_stages:stages,
      source_occurrence_index:index,
      lexical:{
        state:lex.state,
        candidate_count:cands.length,
        preferred_key:preferred?.lexeme_key_v1||null,
        candidates:cands.slice(0,8).map(x=>({
          key:x.lexeme_key_v1,grade:x.grade,pos:x.pos_source,origin_type:x.origin_type,
          original_form:x.original_form,meaning:x.meaning,field:x.field
        }))
      },
      meaning:clean(preferred?.meaning),
      hanja,
      components:comp.components||[],
      component_candidates:comp.component_candidates||comp.components||[],
      component_coverage:comp.coverage,
      morphology_source:comp.source
    });
  });
}

const general56=nikl.objects.filter(x=>x.grade==='4등급').map(x=>({
  key:x.lexeme_key_v1,term:x.word,grade:x.grade,school_stages:['E5','E6'],
  pos:x.pos_source,origin_type:x.origin_type,original_form:x.original_form,
  meaning:x.meaning,field:x.field
}));

const manifest={
  schema:'TAKY_PRELEARNED_TERM_UNIVERSE_MANIFEST_V1',
  generated_at:new Date().toISOString(),
  policy:'PREBUILD_BEFORE_RUNTIME_SELECTION',
  counts:{
    official_subject_terms_56:officialTerms.length,
    official_by_subject:Object.fromEntries(['KOREAN','SOCIAL','SCIENCE','MATH'].map(s=>[s,officialTerms.filter(x=>x.subject===s).length])),
    official_decoder_full:officialTerms.filter(x=>x.readiness.decoder_full).length,
    official_hanja_form:officialTerms.filter(x=>x.readiness.hanja_form).length,
    official_reference_candidates:officialTerms.filter(x=>x.reference_candidate).length,
    official_reference_bound:officialTerms.filter(x=>x.decoder_reference).length,
    official_reference_held:officialTerms.filter(x=>x.reference_candidate&&!x.decoder_reference).length,
    official_unique_lexical:officialTerms.filter(x=>['UNIQUE_EXACT_SURFACE','RESOLVED_BY_REFERENCE_SEED'].includes(x.lexical.state)).length,
    official_ambiguous:officialTerms.filter(x=>x.lexical.state==='AMBIGUOUS_CONTEXT_REQUIRED').length,
    official_no_nikl_match:officialTerms.filter(x=>x.lexical.state==='NO_NIKL_SURFACE_MATCH').length,
    tool_language_total:toolRecords.length,
    tool_language_56:toolRecords.filter(x=>x.grade_band==='5-6').length,
    nikl_general_vocab_56:general56.length,
    nikl_total:nikl.objects.length,
    academic_vocab_entries:academic.entry_count||0,
    academic_vocab_families:academic.family_count||Object.keys(academic.levels||{}).length,
    academic_vocab_by_level:Object.fromEntries([1,2,3,4].map(level=>[String(level),Object.values(academic.levels||{}).filter(levels=>Array.isArray(levels)&&levels.includes(level)).length])),
    char_gloss_seed_count:charInfo.size
  },
  source_hashes:{
    official_terms:sha256(officialPath),
    nikl_objects:sha256(niklPath),
    nikl_surface:sha256(surfacePath),
    tool_vocab:sha256(toolPath),
    ambiguity:sha256(ambiguityPath),
    lexeme_policy:sha256(policyPath),
    reference_seed:sha256(seedPath),
    hanja_reference_mining:fs.existsSync(hanjaRefPath)?sha256(hanjaRefPath):null,
    science_math_hanja_reference:fs.existsSync(path.join(SOURCES,'science-math-hanja-vocab.drive-extracted.txt'))?sha256(path.join(SOURCES,'science-math-hanja-vocab.drive-extracted.txt')):null,
    official_registry:sha256(registryPath),
    official_unit_map:sha256(unitPath),
    academic_vocab_1387_map:sha256(academicPath)
  },
  source_authority:{
    subject_terms:'OFFICIAL_STANDARD_REGISTRY + OFFICIAL_GRADE_UNIT_MAPPING',
    general_vocab:'NIKL_BASIC_VOCAB_40000_OBJECTS_V1',
    tool_language:'KOREAN_TOOL_VOCAB_VERIFIED_TOKEN_V1',
    ambiguity_policy:policy.schema,
    thinking_tool_words_1387:'TAKY_ACADEMIC_VOCAB_1387_LEVEL_MAP_V1_ENGINE_READY'
  },
  coverage:{
    hanja_form_terms:officialTerms.filter(x=>x.readiness.hanja_form).length,
    decoder_full_terms:officialTerms.filter(x=>x.readiness.decoder_full).length,
    decoder_form_only_terms:officialTerms.filter(x=>x.readiness.hanja_form&&!x.readiness.decoder_full).length,
    lexical_ambiguous_terms:officialTerms.filter(x=>x.lexical.state==='AMBIGUOUS_CONTEXT_REQUIRED').length,
    lexical_no_nikl_match_terms:officialTerms.filter(x=>x.lexical.state==='NO_NIKL_SURFACE_MATCH').length
  },
  runtime_guards:[
    'RUNTIME_SELECTS_FROM_PREBUILT_PROJECTION_ONLY',
    'LEARNER_SCHOOL_STAGE_FILTER_REQUIRED',
    'UNVERIFIED_COMPONENT_GLOSS_DOES_NOT_ENABLE_FULL_DECOMPOSITION',
    'FORM_ONLY_HANJA_SUPPRESSES_COMPONENT_FAMILY_TRANSFER',
    'MIDDLE_SCHOOL_REFERENCE_NEVER_SETS_ELEMENTARY_GRADE_AUTHORITY',
    'TERM_REFERENCE_REQUIRES_HANJA_MATCH_TO_TRUSTED_LEXEME_OR_SEED',
    'AMBIGUOUS_SURFACE_LEXEME_REQUIRES_CONTEXTUAL_RESOLUTION'
  ],
  runtime_rule:'Runtime selects from prebuilt projections; runtime does not mine or invent curriculum terms.'
};

fs.writeFileSync(path.join(OUT,'subject-term-universe-56-v1.json'),JSON.stringify({schema:'TAKY_SUBJECT_TERM_UNIVERSE_56_V1',terms:officialTerms},null,2)+'\n');
fs.writeFileSync(path.join(OUT,'tool-language-universe-v1.json'),JSON.stringify({schema:'TAKY_TOOL_LANGUAGE_UNIVERSE_V1',records:toolRecords},null,2)+'\n');
fs.writeFileSync(path.join(OUT,'general-vocab-grade56-v1.json'),JSON.stringify({schema:'TAKY_GENERAL_VOCAB_GRADE56_V1',mapping:'NIKL_4등급 -> E5-E6 lexical baseline',records:general56},null,2)+'\n');
fs.writeFileSync(path.join(OUT,'hanja-char-gloss-seed-v1.json'),JSON.stringify({schema:'TAKY_HANJA_CHAR_GLOSS_SEED_V1',chars:[...charInfo.values()].sort((a,b)=>a.char.localeCompare(b.char))},null,2)+'\n');
fs.writeFileSync(path.join(OUT,'prelearned-term-universe-manifest-v1.json'),JSON.stringify(manifest,null,2)+'\n');

console.log(JSON.stringify(manifest,null,2));
