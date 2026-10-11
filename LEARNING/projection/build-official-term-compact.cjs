const fs=require('fs');
const p='D:/Git PWA/TAKY/LEARNING/data/official-term-candidates-56-v1.json';
const x=JSON.parse(fs.readFileSync(p,'utf8'));
const small=x.terms.map(t=>({s:t.subject,t:t.term,g:t.grades}));
const out='D:/Git PWA/TAKY/LEARNING/data/official-term-candidates-56-compact.json';
fs.writeFileSync(out,JSON.stringify(small));
console.log(JSON.stringify({count:small.length,bytes:fs.statSync(out).size}));
