'use strict';

const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const PatternRouter=require('./mining-learning-pattern-router.js');

const ROOT=path.resolve(__dirname,'..');
const DATA=path.join(ROOT,'data');
const SOURCES=path.join(DATA,'sources');
const PRE=path.join(DATA,'prelearned');
const OUT=path.join(PRE,'subject-term-universe-elementary-v1.json');

const standardPath=path.join(DATA,'official-snapshots','standard-object-2022-elementary-v1.json');
const niklPath=path.join(SOURCES,'nikl-basic-vocab-40000-objects-v1.json');
const surfacePath=path.join(SOURCES,'nikl-basic-vocab-surface-index-v1.json');
const existing56Path=path.join(PRE,'subject-term-universe-56-v1.json');
const charGlossPath=path.join(PRE,'hanja-char-gloss-seed-v1.json');
const toolPath=path.join(SOURCES,'korean-tool-vocab-verified-token-2026-09-22.txt');
const academicPath=path.join(__dirname,'academic-vocab-1387-level-map-v1.json');

const readJson=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const sha256=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const clean=v=>String(v??'').trim();
const uniq=a=>[...new Set((a||[]).filter(Boolean))];
const cjkChars=s=>[...clean(s).normalize('NFKC')].filter(c=>/[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/.test(c));
const pureHanja=s=>cjkChars(s).join('');

const standard=readJson(standardPath);
const nikl=readJson(niklPath);
const surface=readJson(surfacePath);
const existing56=readJson(existing56Path);
const charGloss=readJson(charGlossPath);
const tool=readJson(toolPath);
const academic=readJson(academicPath);

const SUBJECT_ID=Object.freeze({
  '국어':'KOREAN','수학':'MATH','사회':'SOCIAL','과학':'SCIENCE','영어':'ENGLISH',
  '도덕':'MORAL','미술':'ART','음악':'MUSIC','체육':'PE','실과':'PRACTICAL',
  '바른 생활':'RIGHT_LIFE','슬기로운 생활':'WISE_LIFE','즐거운 생활':'JOYFUL_LIFE'
});
const BAND_STAGES=Object.freeze({
  '1_2':['E1','E2'],
  '3_4':['E3','E4'],
  '5_6':['E5','E6']
});
const BAND_MAX_NIKL=Object.freeze({'1_2':2,'3_4':3,'5_6':4});
const PARTICLES=[
  '으로부터','에게서','한테서','에서','에게','한테','까지','부터','처럼','보다','이나','라도','이라도',
  '으로','하고','로','와','과','의','에','은','는','이','가','을','를','도','만','께','나'
];
const STOP=new Set([
  '내용','학생','자신','방법','경우','과정','활동','관심','태도','생각','느낌','이해','표현','활용','관계',
  '상황','정도','대상','문제','결과','자료','정보','특성','경험','의미','필요','부분','종류','다양','기준',
  '사람','서로','여러','사용','주변','관련','목적','중심','학습','교과','기능','지식','가치','우리','가지',
  '생활','지금','대한','위해','통해','대해','각각','보고','인해','최근','직접','일상','누구','무엇','모두',
  '하나','여기','간의','수의','물의','각의','분과','그릴','살기','수로'
]);

const byWord=new Map();
for(const o of nikl.objects){
  const w=clean(o.word); if(!w)continue;
  const a=byWord.get(w)||[];a.push(o);byWord.set(w,a);
}
const nounByWord=new Map([...byWord].map(([w,arr])=>[w,arr.filter(o=>String(o.pos_source||'').includes('명사'))]).filter(([,arr])=>arr.length));
const objectByKey=new Map(nikl.objects.map(o=>[o.lexeme_key_v1,o]));
const charByGlyph=new Map((charGloss.chars||[]).map(x=>[x.char,x]));
const toolSet=new Set(Object.values(tool.grade_bands||{}).flatMap(x=>x.tokens||[]));
const academicSet=new Set(Object.keys(academic.levels||{}));

function candidateForToken(token){
  for(const p of PARTICLES){
    if(token.endsWith(p)&&token.length-p.length>=2){
      const stem=token.slice(0,-p.length);
      if(nounByWord.has(stem))return {word:stem,particle_stripped:true};
    }
  }
  if(nounByWord.has(token))return {word:token,particle_stripped:false};
  return null;
}
function termsFromText(text){
  const out=[];
  for(const tok of String(text||'').match(/[가-힣]{2,}/g)||[]){
    const c=candidateForToken(tok);
    if(c&&!STOP.has(c.word))out.push({...c,token:tok});
  }
  return out;
}
function niklGrade(arr=[]){
  const g=arr.map(o=>Number(String(o.grade||'').match(/\d/)?.[0]||9)).filter(Number.isFinite);
  return g.length?Math.min(...g):9;
}
function conciseMeaning(raw){
  const s=clean(raw).replace(/\s*\n\s*/g,' ');
  if(!s)return '';
  const first=s.split(/(?=「2」|\[2\]|\n)/)[0].replace(/^「1」/,'').replace(/^\[1\]/,'').trim();
  if(first.length<=220)return first;
  const sentence=first.slice(0,220).replace(/\s+\S*$/,'').trim();
  return sentence+(sentence.endsWith('.')?'':'…');
}
function lexical(word){
  const refs=surface.index?.[word]||[];
  const candidates=refs.map(r=>objectByKey.get(r.k)).filter(Boolean);
  if(candidates.length===1)return {state:'UNIQUE_EXACT_SURFACE',preferred:candidates[0],candidates};
  if(candidates.length>1)return {state:'AMBIGUOUS_CONTEXT_REQUIRED',preferred:null,candidates};
  const nouns=nounByWord.get(word)||[];
  if(nouns.length===1)return {state:'UNIQUE_NOUN_SURFACE',preferred:nouns[0],candidates:nouns};
  if(nouns.length>1)return {state:'AMBIGUOUS_CONTEXT_REQUIRED',preferred:null,candidates:nouns};
  return {state:'NO_NIKL_SURFACE_MATCH',preferred:null,candidates:[]};
}
function componentsFor(hanja,term){
  const chars=cjkChars(hanja),syll=[...clean(term)];
  if(!chars.length)return {components:[],coverage:0,source:'NONE'};
  const aligned=chars.length===syll.length;
  const comps=chars.map((ch,i)=>{
    const info=charByGlyph.get(ch);
    const meanings=uniq(info?.meanings||[]),readings=uniq(info?.readings||[]);
    return {
      text:ch,
      meaning:meanings.length===1?clean(meanings[0]):'',
      reading:aligned?(syll[i]||''):(readings.length===1?clean(readings[0]):'')
    };
  });
  const known=comps.filter(x=>x.meaning).length;
  return {
    components:known===chars.length?comps:[],
    component_candidates:comps,
    coverage:chars.length?known/chars.length:0,
    source:known===chars.length?'PRELEARNED_CHAR_GLOSS':'PARTIAL_CHAR_GLOSS'
  };
}
const familyByChar=new Map();
for(const o of nikl.objects){
  const form=pureHanja(o.original_form); if(!form)continue;
  for(const ch of uniq([...form])){
    const a=familyByChar.get(ch)||[];
    if(a.length<120)a.push({word:o.word,grade:o.grade,key:o.lexeme_key_v1});
    familyByChar.set(ch,a);
  }
}
function familiesFor(hanja){
  return cjkChars(hanja).map(ch=>{
    const seen=new Set();
    const words=(familyByChar.get(ch)||[])
      .sort((a,b)=>niklGrade([a])-niklGrade([b])||a.word.length-b.word.length)
      .filter(x=>!seen.has(x.word)&&seen.add(x.word))
      .slice(0,8).map(x=>x.word);
    return {anchor:ch,words};
  }).filter(x=>x.words.length);
}

const occurrence=new Map();
const bandSubjectMaps=new Map();
for(const row of standard.objects||[]){
  const subject=SUBJECT_ID[row.subject]; if(!subject)continue;
  const stages=BAND_STAGES[row.grade_band]; if(!stages)continue;
  const groupKey=row.grade_band+'|'+subject;
  if(!bandSubjectMaps.has(groupKey))bandSubjectMaps.set(groupKey,new Map());
  const map=bandSubjectMaps.get(groupKey);
  // Candidate terms must appear in the learner-facing achievement-standard text itself.
  // Domain labels remain concept metadata but do not get promoted merely because they name a curriculum domain.
  const tokens=termsFromText(row.standard_text);
  const uniqueWords=uniq(tokens.map(x=>x.word));
  for(const word of uniqueWords){
    const tokenInfo=tokens.filter(x=>x.word===word);
    const rec=map.get(word)||{
      word,band:row.grade_band,subject,subject_ko:row.subject,count:0,exact:0,particle_stripped:0,
      standard_codes:new Set(),source_refs:new Set(),domains:new Set(),standard_texts:[],co_terms:new Set()
    };
    rec.count++;
    rec.exact+=tokenInfo.filter(x=>x.word===x.token).length;
    rec.particle_stripped+=tokenInfo.filter(x=>x.particle_stripped).length;
    rec.standard_codes.add(row.standard_code);
    rec.source_refs.add(row.source_ref);
    rec.domains.add(row.domain);
    if(rec.standard_texts.length<8)rec.standard_texts.push(row.standard_text);
    map.set(word,rec);
    const global=occurrence.get(word)||new Set();global.add(groupKey);occurrence.set(word,global);
  }
  for(const word of uniqueWords){
    const rec=map.get(word);
    uniqueWords.filter(x=>x!==word).forEach(x=>rec.co_terms.add(x));
  }
}

function scoreRecord(rec){
  const objs=nounByWord.get(rec.word)||[];
  const grade=niklGrade(objs),target=BAND_MAX_NIKL[rec.band]||4;
  const cross=occurrence.get(rec.word)?.size||1;
  let score=rec.count*5+rec.exact*3+rec.particle_stripped*2;
  if(rec.word.length>=4)score+=2;
  if(toolSet.has(rec.word))score+=3;
  if(academicSet.has(rec.word))score+=3;
  if(grade<=target)score+=2; else score-=2;
  if(cross>=5)score-=6; else if(cross>=3)score-=3;
  return {score,grade,cross};
}
function confidence(rec,meta){
  if(rec.count>=2||rec.exact>=1||rec.domains.has(rec.word))return 'HIGH';
  if(meta.score>=7)return 'MEDIUM';
  return 'LOW';
}

const generated=[];
for(const [groupKey,map] of bandSubjectMaps){
  const [band,subject]=groupKey.split('|');
  const stages=BAND_STAGES[band];
  const rows=[...map.values()].map(rec=>({rec,...scoreRecord(rec)}))
    .filter(x=>x.score>=5)
    .sort((a,b)=>b.score-a.score||b.rec.count-a.rec.count||b.rec.word.length-a.rec.word.length||a.rec.word.localeCompare(b.rec.word,'ko'))
    .slice(0,120);
  for(const row of rows){
    const rec=row.rec,lex=lexical(rec.word),preferred=lex.preferred;
    const hanja=pureHanja(preferred?.original_form);
    const comp=componentsFor(hanja,rec.word);
    const meaning=preferred?conciseMeaning(preferred.meaning):'';
    const term={
      term_id:'official-elementary:'+band.toLowerCase()+':'+subject.toLowerCase()+':'+rec.word,
      layer:'SUBJECT_TERMINOLOGY',
      subject,subject_ko:rec.subject_ko,term:rec.word,
      school_stages:stages,
      grade_band:band.replace('_','-'),
      grades:stages.map(x=>Number(x.slice(1))),
      standards:[...rec.standard_codes],
      units:[...rec.domains],
      domains:[...rec.domains],
      source_refs:[...rec.source_refs],
      grade_alignment:{
        state:'VERIFIED',
        authority_class:'OFFICIAL_2022_ELEMENTARY_ACHIEVEMENT_STANDARD_GRADE_BAND',
        source_ref:[...rec.standard_codes].map(x=>'STANDARD:'+x).join('|'),
        reviewed:true
      },
      extraction:{
        method:'OFFICIAL_STANDARD_TEXT_NIKL_NOUN_MATCH',
        score:row.score,
        confidence:confidence(rec,row),
        standard_count:rec.count,
        exact_token_hits:rec.exact,
        particle_stripped_hits:rec.particle_stripped,
        cross_band_subject_presence:row.cross
      },
      lexical:{
        state:lex.state,
        candidate_count:lex.candidates.length,
        preferred_key:preferred?.lexeme_key_v1||null,
        candidates:lex.candidates.slice(0,8).map(x=>({
          key:x.lexeme_key_v1,grade:x.grade,pos:x.pos_source,origin_type:x.origin_type,
          original_form:x.original_form,meaning:conciseMeaning(x.meaning),field:x.field
        }))
      },
      meaning,
      meaning_source:meaning?'NIKL_UNIQUE_LEXEME':'OFFICIAL_CONTEXT_ONLY',
      hanja,
      components:comp.components,
      component_candidates:comp.component_candidates,
      component_coverage:comp.coverage,
      morphology_source:comp.source,
      families:hanja?familiesFor(hanja):[],
      conceptLinks:uniq([...rec.domains,...rec.co_terms]).slice(0,16),
      concept:{
        summary:rec.standard_texts[0]||'',
        clues:uniq([...rec.domains,...rec.co_terms]).slice(0,12),
        relations:[],
        contrast:[],
        hierarchy:uniq([rec.subject_ko,...rec.domains,rec.word]).slice(0,8),
        compare:[]
      },
      example:'',
      unit_context_source:'CURRICULUM_DOMAIN_NOT_TEXTBOOK_UNIT',
      readiness:{
        recommendation:true,
        lexical_resolution:lex.state,
        hanja_form:!!hanja,
        decoder_full:!!meaning&&comp.components.length>0&&comp.coverage===1,
        decoder_form_only:!!hanja&&!(!!meaning&&comp.components.length>0&&comp.coverage===1)
      }
    };
    term.mining_learning_pattern=PatternRouter.derive(term);
    generated.push(term);
  }
}

// Preserve the richer existing 5–6 core-subject universe as the primary representation.
// When the same subject+term exists there, its finer E5/E6 stage mapping wins over the coarser 5–6 band extraction.
const enrichedKeys=new Set((existing56.terms||[]).map(t=>t.subject+'|'+t.term));
const merged=new Map();
for(const t of generated){
  const key=t.subject+'|'+t.term;
  if(enrichedKeys.has(key))continue;
  if(!merged.has(key))merged.set(key,t);
  else{
    const prev=merged.get(key);
    prev.school_stages=uniq([...(prev.school_stages||[]),...(t.school_stages||[])]).sort();
    prev.grades=uniq([...(prev.grades||[]),...(t.grades||[])]).sort((a,b)=>a-b);
    prev.standards=uniq([...(prev.standards||[]),...(t.standards||[])]);
    prev.source_refs=uniq([...(prev.source_refs||[]),...(t.source_refs||[])]);
    prev.units=uniq([...(prev.units||[]),...(t.units||[])]);
    prev.domains=uniq([...(prev.domains||[]),...(t.domains||[])]);
  }
}
for(const t of existing56.terms||[]){
  const key=t.subject+'|'+t.term;
  merged.set(key,{...t,source_lineage:uniq([...(t.source_lineage||[]),'PRELEARNED_56_ENRICHED'])});
}
const terms=[...merged.values()].sort((a,b)=>
  (a.school_stages?.[0]||'').localeCompare(b.school_stages?.[0]||'')||
  String(a.subject).localeCompare(String(b.subject))||
  String(a.term).localeCompare(String(b.term),'ko')
);

const summary={};
for(const stage of ['E1','E2','E3','E4','E5','E6']){
  summary[stage]={};
  for(const subject of uniq(terms.filter(t=>t.school_stages?.includes(stage)).map(t=>t.subject)).sort()){
    summary[stage][subject]=terms.filter(t=>t.school_stages?.includes(stage)&&t.subject===subject).length;
  }
}
const output={
  schema:'TAKY_SUBJECT_TERM_UNIVERSE_ELEMENTARY_V1',
  generated_at:new Date().toISOString(),
  curriculum_version:'2022_REVISED_NATIONAL_CURRICULUM',
  authority_class:'OFFICIAL_ELEMENTARY_STANDARD_GRADE_BAND+NIKL_LEXICAL_ENRICHMENT',
  stages:['E1','E2','E3','E4','E5','E6'],
  stage_subject_counts:summary,
  counts:{
    terms:terms.length,
    generated_from_all_elementary_standards:generated.length,
    preserved_enriched_56:(existing56.terms||[]).length,
    decoder_full:terms.filter(t=>t.readiness?.decoder_full).length,
    hanja_form:terms.filter(t=>t.readiness?.hanja_form).length,
    lexical_ambiguous:terms.filter(t=>t.lexical?.state==='AMBIGUOUS_CONTEXT_REQUIRED').length,
    official_context_only:terms.filter(t=>!t.meaning).length
  },
  source_provenance:{
    standard_object:{schema:standard.schema,object_count:standard.objects.length,sha256:sha256(standardPath)},
    existing_enriched_56:{schema:existing56.schema,term_count:(existing56.terms||[]).length,sha256:sha256(existing56Path)},
    nikl:{schema:nikl.schema||'NIKL_BASIC_VOCAB_40000_OBJECTS_V1',object_count:nikl.objects.length,sha256:sha256(niklPath)}
  },
  guards:[
    'PROFILE_STAGE_FILTER_REQUIRED',
    'GRADE_BAND_COMES_FROM_OFFICIAL_STANDARD_OBJECT',
    'AMBIGUOUS_LEXEME_DOES_NOT_GET_INVENTED_MEANING_OR_HANJA',
    'CURRICULUM_DOMAIN_IS_NOT_CLAIMED_AS_PUBLISHER_UNIT',
    'LOWER_GRADE_PRESENTATION_ADAPTATION_DOES_NOT_CHANGE_GRADE_AUTHORITY'
  ],
  terms
};
fs.writeFileSync(OUT,JSON.stringify(output,null,2)+'\n','utf8');
console.log(JSON.stringify({out:OUT,counts:output.counts,stage_subject_counts:summary},null,2));
