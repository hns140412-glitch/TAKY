'use strict';
const s=require('../data/official-snapshots/standard-object-2022-elementary-v1.json');
const nikl=require('../data/sources/nikl-basic-vocab-40000-objects-v1.json');

const byWord=new Map();
for(const o of nikl.objects){
  if(!String(o.pos_source||'').includes('명사'))continue;
  const a=byWord.get(o.word)||[];
  a.push(o);byWord.set(o.word,a);
}
const particles=['으로부터','에게서','한테서','에서','에게','한테','까지','부터','처럼','보다','이나','나','라도','이라도','으로','로','와','과','하고','의','에','은','는','이','가','을','를','도','만','께'];
const stop=new Set(['내용','학생','자신','방법','경우','과정','활동','관심','태도','생각','느낌','이해','표현','활용','관계','상황','정도','대상','문제','결과','자료','정보','특성','경험','의미','필요','부분','종류','다양','기준','사람','서로','여러','사용','주변','관련','목적','중심','학습','교과','기능','지식','가치','우리','가지','생활','지금','대한','위해','통해','대해','각각','보고','인해','최근','직접','일상']);
function candidate(token){
  if(byWord.has(token))return token;
  for(const p of particles){
    if(token.endsWith(p)&&token.length-p.length>=2){
      const stem=token.slice(0,-p.length);
      if(byWord.has(stem))return stem;
    }
  }
  return null;
}
function extract(text){
  const out=new Map(),toks=String(text||'').match(/[가-힣]{2,}/g)||[];
  for(const tok of toks){
    const w=candidate(tok); if(!w)continue;
    const prev=out.get(w)||{word:w,hits:0,exact:0,objs:byWord.get(w)};
    prev.hits++;if(w===tok)prev.exact++;out.set(w,prev);
  }
  return [...out.values()];
}
const agg=new Map();
for(const row of s.objects){
  if(!['1_2','3_4'].includes(row.grade_band))continue;
  const key=row.grade_band+'|'+row.subject;if(!agg.has(key))agg.set(key,new Map());const m=agg.get(key);
  for(const x of extract(row.standard_text+' '+row.domain)){
    const r=m.get(x.word)||{word:x.word,count:0,exact:0,codes:new Set(),domains:new Set(),objects:x.objs};
    r.count++;r.exact+=x.exact;r.codes.add(row.standard_code);r.domains.add(row.domain);m.set(x.word,r);
  }
}
const subjectPresence=new Map();
for(const [k,m] of agg)for(const w of m.keys()){const set=subjectPresence.get(w)||new Set();set.add(k);subjectPresence.set(w,set)}
for(const [k,m] of agg){
 const [band,sub]=k.split('|');if(!['국어','수학','사회','과학','바른 생활','슬기로운 생활','즐거운 생활'].includes(sub))continue;
 const targetMax=band==='1_2'?2:3;
 const arr=[...m.values()].map(x=>{const grade=Math.min(...x.objects.map(o=>Number(String(o.grade).match(/\d/)?.[0]||9)));const specificity=subjectPresence.get(x.word)?.size||1;const score=x.count*5+x.exact*3+(x.word.length>=4?2:0)-(specificity>2?4:0)-(grade>targetMax?3:0)-(stop.has(x.word)?10:0);return {...x,grade,specificity,score,domains:[...x.domains],codes:[...x.codes]}}).filter(x=>x.score>=5&&!stop.has(x.word)).sort((a,b)=>b.score-a.score||b.word.length-a.word.length||a.word.localeCompare(b.word,'ko')).slice(0,80);
 console.log('\n### '+k+' count='+arr.length);console.log(arr.slice(0,50).map(x=>x.word+'('+x.score+',g'+x.grade+')').join(', '));
}
