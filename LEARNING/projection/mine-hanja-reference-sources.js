'use strict';
const fs=require('fs');
const path=require('path');

const ROOT='D:/Git PWA/TAKY/LEARNING/data';
const srcDir=path.join(ROOT,'sources');
const outDir=path.join(ROOT,'prelearned');

const surface=JSON.parse(fs.readFileSync(path.join(srcDir,'nikl-basic-vocab-surface-index-v1.json'),'utf8'));
const nikl=JSON.parse(fs.readFileSync(path.join(srcDir,'nikl-basic-vocab-40000-objects-v1.json'),'utf8'));
const official=JSON.parse(fs.readFileSync(path.join(ROOT,'official-term-candidates-56-v1.json'),'utf8'));
const objByKey=new Map(nikl.objects.map(x=>[x.lexeme_key_v1,x]));
const known=[...new Set([...Object.keys(surface.index||{}),...(official.terms||[]).map(x=>x.term)])]
  .filter(Boolean).sort((a,b)=>b.length-a.length||a.localeCompare(b,'ko'));

const CJK=/[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/;
const CJK_GLOBAL=/[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]/g;
const CJK_RUN=/[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF](?:\s*[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF])*/g;
const isCjk=c=>CJK.test(c);
const isHangul=c=>/[가-힣]/.test(c);
const clean=s=>String(s??'').replace(/\s+/g,' ').trim();
const normalizeText=s=>String(s).replace(/\\r\\n/g,'\n').replace(/\\n/g,'\n').replace(/\r\n/g,'\n').replace(/\r/g,'\n');
const normCjk=s=>[...String(s??'').normalize('NFKC')].filter(isCjk).join('');
const pureHanja=s=>normCjk(s);
const uniq=a=>[...new Set((a||[]).filter(Boolean))];

function termPrefix(s){
  const flat=s.replace(/^\s+/,'');
  for(const w of known)if(flat.startsWith(w))return w;
  const first=flat.split(/\s|\n/)[0]||'';
  return first.replace(/[^가-힣()·]/g,'');
}

function extractGlosses(phrase,readings){
  const tokens=clean(phrase).split(/\s+/).filter(Boolean);
  let pos=0; const out=[];
  for(const reading of readings){
    let hit=-1,attached=false,prefix='';
    for(let j=pos;j<tokens.length;j++)if(tokens[j]===reading){hit=j;break;}
    if(hit<0){
      for(let j=pos;j<tokens.length;j++){
        if(tokens[j].endsWith(reading)&&tokens[j].length>reading.length){
          hit=j;attached=true;prefix=tokens[j].slice(0,-reading.length);break;
        }
      }
    }
    if(hit<0)return null;
    const before=tokens.slice(pos,hit);
    let gloss=attached?prefix:(before.length?before[before.length-1]:'');
    gloss=clean(gloss).replace(/^[^가-힣]+|[^가-힣]+$/g,'');
    if(!gloss||gloss===reading)return null;
    out.push({reading,gloss});
    pos=hit+1;
  }
  return out;
}

function parseFile(file,sourceId,subjectHint){
  const raw=normalizeText(fs.readFileSync(file,'utf8'));
  const parts=raw.split(/-\s*(\d{1,3})\s*-/g);
  const entries=[],chars=[];
  for(let i=1;i<parts.length;i+=2){
    const no=Number(parts[i]),body=parts[i+1]||'';
    const firstPrompt=body.search(/|한자 뜻 그대로/);
    const head=(firstPrompt>=0?body.slice(0,firstPrompt):body.slice(0,350)).slice(0,350);
    const cjk=[...head].filter(isCjk);
    if(!cjk.length)continue;
    const firstCjk=head.search(CJK);
    const before=head.slice(0,firstCjk);
    const term=termPrefix(before);
    if(!term)continue;
    const syll=[...term].filter(isHangul);
    let hanja='';
    for(let j=firstCjk;j<head.length;j++){
      const ch=head[j];
      if(isCjk(ch))hanja+=ch;
      else if(hanja&&!/[\s()·]/.test(ch))break;
    }
    if(!hanja)continue;
    const hchars=[...normCjk(hanja)];
    const aligned=syll.length===hchars.length;
    let glosses=null;
    if(aligned){
      const phrase=clean(before.slice(before.indexOf(term)+term.length));
      glosses=extractGlosses(phrase,syll);
    }
    const entry={source_id:sourceId,entry_no:no,subject:subjectHint,term,hanja:normCjk(hanja),aligned,glosses:glosses||[],components:[]};
    if(glosses?.length===hchars.length){
      entry.components=hchars.map((ch,k)=>({text:ch,reading:glosses[k].reading,meaning:glosses[k].gloss}));
      hchars.forEach((ch,k)=>chars.push({
        char:ch,reading:glosses[k].reading,meaning:glosses[k].gloss,
        term,hanja:entry.hanja,source_id:sourceId,entry_no:no,subject:subjectHint
      }));
    }
    entries.push(entry);
  }
  return {entries,chars};
}

const SCIENCE_TERMS=[
'중력','질량','탄성력','마찰력','등속운동','자유낙하운동','정전기','전류','전압','저항',
'직렬연결','병렬연결','비열','파동','매질','파장','진폭','주기','진동수','원소',
'원자','분자','확산','압력','밀도','용해도','융해','응고','기화','액화',
'광합성','엽록체','공변세포','모세혈관','중추신경계','말초신경계','항상성','염색체','염색분체','염색사',
'생장','생식','감수분열','형질','반성유전','화성암','퇴적암','변성암','조암광물','수온약층',
'조석','조차','복사평형','단열팽창','기단','전선','행성','위성','성단','성운'
];

const MATH_TERMS=[
'소수','소인수분해','역수','대입','계수','동류항','등식','이항','해','원점',
'사분면','직교','평행','동위각','작도','합동','회전체','단면','변량','도수',
'유한소수','무한소수','순환소수','지수법칙','연립방정식','평행이동','x절편, y절편','평면도형','이등변삼각형','외접원, 내접원',
'외심','내심','이등분','무게중심','평행사변형','대변, 대각','대각선','피타고라스의 정리','경우의 수','확률',
'제곱근','근호','분모의 유리화','전개','인수','인수분해','중근','완전제곱식','포물선','대칭축',
'삼각비','원주각','대푯값','중앙값','최빈값','산포도','편차','분산','산점도','상관관계'
];

function exactLexemeHanja(term){
  const refs=surface.index?.[term]||[];
  const objects=refs.map(r=>objByKey.get(r.k)).filter(Boolean);
  const forms=uniq(objects.map(x=>pureHanja(x.original_form)).filter(Boolean));
  return forms.length===1?forms[0]:'';
}

function extractPromptField(body,startPattern,endPatterns){
  const start=body.search(startPattern);
  if(start<0)return '';
  const after=body.slice(start);
  const q=after.indexOf('?');
  const from=start+(q>=0?q+1:0);
  let end=body.length;
  for(const p of endPatterns){
    const tail=body.slice(from);
    const m=tail.search(p);
    if(m>=0)end=Math.min(end,from+m);
  }
  return clean(body.slice(from,end)
    .replace(/<과학>|<수학>/g,' ')
    .replace(//g,' ')
    .replace(/\s*-\s*\d+\s*-\s*$/,' '));
}

function pageBodies(section){
  const pages=new Map();
  const re=/-\s*(\d{1,2})\s*-/g;
  let cursor=0,m;
  while((m=re.exec(section))){
    const no=Number(m[1]);
    if(no>=1&&no<=60){
      pages.set(no,section.slice(cursor,m.index));
      cursor=re.lastIndex;
    }
  }
  return pages;
}

function findTermStart(body,term){
  const firstCjk=body.search(CJK);
  const before=firstCjk>=0?body.slice(0,firstCjk):body.slice(0,600);
  const variants=[
    term,
    term.replace(/x/g,'').replace(/y/g,''),
    term.replace(/,\s*/g,', '),
    term.split(',')[0].trim()
  ];
  let best=-1;
  for(const v of variants){
    if(!v)continue;
    const i=before.lastIndexOf(v);
    if(i>best)best=i;
  }
  return best;
}

function mapGlossesByRuns(body,term,hanja){
  const readings=[...term].filter(isHangul);
  const hchars=[...normCjk(hanja)];
  if(!readings.length||readings.length!==hchars.length)return {components:[],candidates:[]};
  const candidates=[];
  let expectedPos=0;
  for(const m of body.matchAll(CJK_RUN)){
    const run=[...normCjk(m[0])];
    if(!run.length)continue;
    let pos=-1;
    for(let p=expectedPos;p<=hchars.length-run.length;p++){
      if(hchars.slice(p,p+run.length).join('')===run.join('')){pos=p;break;}
    }
    if(pos<0)continue;
    const prefix=body.slice(Math.max(0,m.index-100),m.index);
    const glosses=extractGlosses(prefix,readings.slice(pos,pos+run.length));
    if(glosses?.length===run.length){
      run.forEach((ch,i)=>{
        let meaning=clean(glosses[i].gloss);
        if(meaning.startsWith(term)&&meaning.length>term.length)meaning=meaning.slice(term.length);
        candidates.push({index:pos+i,text:ch,reading:glosses[i].reading,meaning});
      });
      expectedPos=pos+run.length;
    }
  }
  const byIndex=new Map();
  for(const c of candidates)if(!byIndex.has(c.index))byIndex.set(c.index,c);
  const full=hchars.map((ch,i)=>byIndex.get(i)).filter(Boolean);
  return {
    components:full.length===hchars.length?full.map(({text,reading,meaning})=>({text,reading,meaning})):[],
    candidates:[...byIndex.values()].sort((a,b)=>a.index-b.index).map(({text,reading,meaning})=>({text,reading,meaning}))
  };
}

function parseSubjectSection(raw,{label,subject,terms,sourceId}){
  const marker='2015 개정 교육과정 중학교 ['+label+'] 교과서 속 단어 모음';
  const start=raw.indexOf(marker);
  if(start<0)throw new Error('SECTION_NOT_FOUND:'+label);
  const nextTitle=raw.indexOf('2015 개정 교육과정 중학교 [',start+marker.length);
  const section=raw.slice(start,nextTitle>=0?nextTitle:raw.length);
  const pages=pageBodies(section);
  const entries=[],chars=[];
  for(let no=1;no<=60;no++){
    const term=terms[no-1];
    const page=pages.get(no)||'';
    if(!page){entries.push({source_id:sourceId,entry_no:no,subject,term,state:'PAGE_MISSING',components:[]});continue;}
    const startAt=findTermStart(page,term);
    const body=startAt>=0?page.slice(startAt):page.slice(Math.max(0,page.search(CJK)-160));
    const lexemeHanja=exactLexemeHanja(term);
    const rawCjk=normCjk(body);
    const hangulLen=[...term].filter(isHangul).length;
    const sourceCandidate=rawCjk&&hangulLen>0?rawCjk.slice(0,hangulLen):'';
    const provisionalHanja=lexemeHanja||sourceCandidate;
    const gloss=mapGlossesByRuns(body,term,provisionalHanja);
    const hanja=lexemeHanja||(gloss.components.length===hangulLen?gloss.components.map(x=>x.text).join(''):'');
    let literal=extractPromptField(body,/한자 뜻 그대로\s*하면?\s*어떤 뜻일까\?/,
      [/우리\s+(?:과학|수학)\s*과목에서는\s*무슨 뜻일까\?/,/(?:과학|수학)\s*교과(?:서)?[\s\S]{0,100}?어떻게\s*사용될까\?/,/우리\s+생활\s*속에서/]);
    let subjectMeaning=extractPromptField(body,/우리\s+(?:과학|수학)\s*과목에서는\s*무슨 뜻일까\?/,
      [/(?:과학|수학)\s*교과(?:서)?[\s\S]{0,100}?어떻게\s*사용될까\?/,/우리\s+생활\s*속에서/,/<(?:과학|수학)>/]);
    let usage=extractPromptField(body,/(?:과학|수학)\s*교과(?:서)?[\s\S]{0,100}?어떻게\s*사용될까\?/,
      [/<(?:과학|수학)>/]);
    if(literal.length>220||/교과(?:서)?\s*속/.test(literal))literal='';
    if(subjectMeaning.length>320||/한자 뜻 그대로/.test(subjectMeaning))subjectMeaning='';
    if(usage.length>420)usage='';
    const entry={
      source_id:sourceId,entry_no:no,subject,term,state:'PARSED_REFERENCE',
      hanja,hanja_source:lexemeHanja?'NIKL_EXACT_SURFACE':'SOURCE_PAGE_CJK_CANDIDATE',
      aligned:gloss.components.length>0,
      glosses:gloss.components.map(x=>({reading:x.reading,gloss:x.meaning})),
      components:gloss.components,
      component_candidates:gloss.candidates,
      literal_meaning:literal,
      source_subject_meaning:subjectMeaning,
      source_usage_excerpt:usage,
      authority_class:'REFERENCE_SEMANTIC_MORPHOLOGY_ONLY_NOT_GRADE_AUTHORITY'
    };
    entries.push(entry);
    for(const c of gloss.components)chars.push({
      char:c.text,reading:c.reading,meaning:c.meaning,
      term,hanja,source_id:sourceId,entry_no:no,subject
    });
  }
  return {entries,chars};
}

function parseScienceMath(){
  const file=path.join(srcDir,'science-math-hanja-vocab.drive-extracted.txt');
  const raw=normalizeText(fs.readFileSync(file,'utf8'));
  const sci=parseSubjectSection(raw,{
    label:'과학',subject:'SCIENCE',terms:SCIENCE_TERMS,
    sourceId:'DAEGU_EDU_SCIENCE_HANJA_REFERENCE'
  });
  const math=parseSubjectSection(raw,{
    label:'수학',subject:'MATH',terms:MATH_TERMS,
    sourceId:'DAEGU_EDU_MATH_HANJA_REFERENCE'
  });
  return {entries:[...sci.entries,...math.entries],chars:[...sci.chars,...math.chars]};
}

const parsed=[
  parseFile(path.join(srcDir,'social-history-hanja-vocab.drive-extracted.txt'),'DAEGU_EDU_SOCIAL_HISTORY_HANJA_REFERENCE','SOCIAL_HISTORY'),
  parseFile(path.join(srcDir,'korean-hanja-vocab.drive-extracted.txt'),'DAEGU_EDU_KOREAN_HANJA_REFERENCE','KOREAN'),
  parseScienceMath()
];

const allEntries=parsed.flatMap(x=>x.entries);
const allChars=parsed.flatMap(x=>x.chars);
const byChar=new Map();
for(const row of allChars){
  const x=byChar.get(row.char)||{char:row.char,readings:[],meanings:[],evidence:[]};
  x.readings.push(row.reading);x.meanings.push(row.meaning);
  x.evidence.push({
    term:row.term,hanja:row.hanja,source_id:row.source_id,entry_no:row.entry_no,
    subject:row.subject,reading:row.reading,meaning:row.meaning
  });
  x.readings=uniq(x.readings);x.meanings=uniq(x.meanings);
  byChar.set(row.char,x);
}
const conflict=[...byChar.values()].filter(x=>x.meanings.length>1||x.readings.length>1);

const out={
  schema:'TAKY_HANJA_REFERENCE_MINING_V2',
  state:'REFERENCE_ENRICHMENT_NOT_CURRICULUM_AUTHORITY',
  generated_at:new Date().toISOString(),
  sources:[
    {source_id:'DAEGU_EDU_SOCIAL_HISTORY_HANJA_REFERENCE',file:'social-history-hanja-vocab.drive-extracted.txt',source_type:'education-office_reference',scope:'middle-school social/history'},
    {source_id:'DAEGU_EDU_KOREAN_HANJA_REFERENCE',file:'korean-hanja-vocab.drive-extracted.txt',source_type:'education-office_reference',scope:'middle-school Korean'},
    {source_id:'DAEGU_EDU_SCIENCE_HANJA_REFERENCE',file:'science-math-hanja-vocab.drive-extracted.txt',source_type:'education-office_reference',scope:'middle-school science'},
    {source_id:'DAEGU_EDU_MATH_HANJA_REFERENCE',file:'science-math-hanja-vocab.drive-extracted.txt',source_type:'education-office_reference',scope:'middle-school math'}
  ],
  counts:{
    entries:allEntries.length,
    parsed_reference_entries:allEntries.filter(x=>x.state==='PARSED_REFERENCE').length,
    aligned_entries:allEntries.filter(x=>x.components?.length).length,
    char_evidence:allChars.length,
    unique_chars:byChar.size,
    conflict_chars:conflict.length
  },
  entries:allEntries,
  chars:[...byChar.values()].sort((a,b)=>a.char.localeCompare(b.char)),
  conflicts:conflict
};

fs.writeFileSync(path.join(outDir,'hanja-reference-mining-v1.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify(out.counts,null,2));
console.log(JSON.stringify({
  science:out.entries.filter(x=>x.subject==='SCIENCE').slice(0,5),
  math:out.entries.filter(x=>x.subject==='MATH').slice(0,5),
  conflicts:conflict.slice(0,8)
},null,2));
