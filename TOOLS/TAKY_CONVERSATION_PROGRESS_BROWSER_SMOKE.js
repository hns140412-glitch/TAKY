"use strict";
/* Interactive offline DOM smoke: tabs, search, status, project selection. */
const fs=require("fs"),vm=require("vm"),assert=require("assert");
const path="D:\\Git PWA\\TAKY_AI_WORKBENCH\\00_CONTROL\\TAKY_CONVERSATION_PROGRESS_BOARD.html";
const source=fs.readFileSync(path,"utf8");
const dataMatch=source.match(/<script id="source-data" type="application\/json">([\s\S]*?)<\/script>/);
const scriptMatch=source.match(/<script>([\s\S]*?)<\/script><\/body>/);
assert(dataMatch&&scriptMatch,"HTML_DOCUMENT_HAS_EXPECTED_SCRIPTS");
const payload=JSON.parse(dataMatch[1]);
new vm.Script(scriptMatch[1],{filename:"TAKY_PROGRESS_VIEWER_BROWSER_JS"});
class Elem {
 constructor(tag="",id=""){this.tagName=tag;this.id=id;this.children=[];this.attributes={};this.dataset={};this.hidden=false;this.value="";this.className="";this.onclick=null;this.textContent="";}
 append(x){this.children.push(x)}
 replaceChildren(){this.children=[]}
 setAttribute(k,v){this.attributes[k]=v}
 addEventListener(ev,fn){this["on"+ev]=fn}
}
const ids={};
for(const id of ["source-data","metrics","projects","work","alerts","source","search","status","reset","count"])ids[id]=new Elem("div",id);
ids["source-data"].textContent=dataMatch[1];
const tabs=["projects","work","alerts","source"].map(key=>{const e=new Elem("button");e.dataset.tab=key;return e});
const document={
 getElementById(id){assert(ids[id],"MISSING_ELEMENT:"+id);return ids[id]},
 createElement(tag){return new Elem(tag)},
 createTextNode(value){return {textContent:String(value)}},
 querySelectorAll(sel){assert.strictEqual(sel,"[data-tab]");return tabs}
};
vm.runInNewContext(scriptMatch[1],{document,console,JSON},{timeout:1000});
function walk(e,matcher){let out=[];if(matcher(e))out.push(e);for(const c of e.children||[]){if(c instanceof Elem)out.push(...walk(c,matcher))}return out}
function cards(id){return walk(ids[id],e=>e.tagName==="article"&&e.className.includes("card"))}
assert.strictEqual(cards("projects").length,payload.counts.projects,"PROJECT_CARDS");
assert.strictEqual(ids["metrics"].children.length,8);
tabs[1].onclick();
assert.strictEqual(cards("work").length,
 payload.counts.registered_ai_work+(payload.counts.projects_with_explicit_current_unregistered_work||0),
 "REGISTERED_PLUS_EXPLICIT_UNREGISTERED_WORK_CANDIDATES");
ids["status"].value="REVIEW";ids["status"].onchange();
assert.strictEqual(cards("work").length,payload.counts.review,"REVIEW_FILTER");
ids["status"].value="BLOCKED";ids["status"].onchange();
assert.strictEqual(cards("work").length,payload.counts.blocked,"BLOCKED_FILTER");
ids["status"].value="";ids["status"].onchange();
ids["search"].value="not-a-real-project";ids["search"].oninput();
assert.strictEqual(cards("work").length,0,"SEARCH_FILTER");
ids["reset"].onclick();
assert.strictEqual(cards("work").length,
 payload.counts.registered_ai_work+(payload.counts.projects_with_explicit_current_unregistered_work||0),
 "RESET_FILTER");
tabs[0].onclick();
const projects=cards("projects");
assert.strictEqual(projects.length,9);
const taky=projects.find(x=>walk(x,e=>e.tagName==="h3").some(h=>h.children.some(t=>t.textContent==="TAKY")));
assert(taky,"TAKY_PROJECT_CARD");
const choose=walk(taky,x=>x.tagName==="button"&&x.className==="choose")[0];
assert(choose&&typeof choose.onclick==="function");
choose.onclick();
assert.strictEqual(cards("work").length,7,"PROJECT_DETAIL_FILTER");
tabs[0].onclick();
const archi=cards("projects").find(x=>walk(x,e=>e.tagName==="h3").some(h=>
 h.children.some(t=>t.textContent==="TAKY_ARCHI-GROW")));
assert(archi,"ARCHI_PROJECT_CARD");
walk(archi,x=>x.tagName==="button"&&x.className==="choose")[0].onclick();
const archiCards=cards("work");
assert.strictEqual(archiCards.length,1,"ARCHI_CURRENT_EXACT_WORK_CANDIDATE");
assert(walk(archiCards[0],e=>e.tagName==="p").some(e=>
 e.children.some(t=>t.textContent==="MCP-REA-20261016")),
 "SOURCE_CURRENT_ID_IS_VISIBLE_WITHOUT_ASSIGNMENT");
tabs[2].onclick();
assert.strictEqual(cards("alerts").length,payload.counts.status_review_alerts,"ALERT_VIEW");
tabs[3].onclick();
assert(walk(ids["source"],x=>x.className==="panel").length>=1,"SOURCE_SCOPE_VIEW");
console.log(JSON.stringify({test:"INTERACTIVE_OFFLINE_DOM_SMOKE",projects:9,work:7,review:payload.counts.review,blocked:payload.counts.blocked,alerts:payload.counts.status_review_alerts,result:"PASS"}));
