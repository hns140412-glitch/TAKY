// Regression: transfer freshness is not provider freshness; missing windows stay visible.
// Added: control-center tab (PC load, works) and hidden ChatGPT web / Antigravity cards.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, 'TAKY_USAGE_MOBILE_VIEW.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, 'embedded viewer script');
class Element {
  constructor(tag) { this.tag=tag; this.className=''; this.textContent=''; this.style={}; this.children=[]; this.attrs={}; this.hidden=false; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children=[...nodes]; }
  setAttribute(k,v) { this.attrs[k]=v; }
}
const text = n => n.textContent + n.children.map(text).join(' ');
const nodes={status:new Element('div'),list:new Element('main'),control:new Element('main'),
  tabUsage:new Element('button'),tabControl:new Element('button')};
let intervals=0, requests=0;
const api = { withSuccessHandler(fn) { this.success=fn; return this; },
  withFailureHandler(fn) { this.failure=fn;return this; }, loadUsage() {requests++} };
const ctx = { document: {getElementById: id => nodes[id],createElement: tag => new Element(tag)},
  google:{script:{run:api}},setInterval:()=>{intervals++}, console };
vm.runInNewContext(script, ctx);
assert.equal(requests,1,'one request on app open');
assert.equal(intervals,0,'no background interval polling');
const claude = {name:'Claude Code',observedAt:'2026-10-19T11:30:00+09:00',
  fresh:false,fiveHour:{usedPercent:null},week:{usedPercent:49,resetAt:'2026-10-21T12:00:00+09:00'}};
ctx.render({ok:true,source:'LIVE_PC',synchronized:true,data:{exportedAt:'2026-10-19T22:07:00+09:00',providers:[claude]}});
assert.match(nodes.status.textContent,/PC 직접 응답/);
assert.match(nodes.status.textContent,/사용량 자체 지연\/미확인: Claude Code/);
const lines=nodes.list.children[0].children.filter(c=>c.className==='line');
assert.equal(lines.length,2,'five-hour and weekly usage always shown');
assert.equal(lines[0].children[1].textContent,'미확인');
assert.equal(lines[1].children[1].textContent,'49.0%');
ctx.render({ok:true,synchronized:false,data:{exportedAt:'2026-10-19T22:07:00+09:00',providers:[{...claude,fresh:true}]}});
assert.match(nodes.status.textContent,/PC 연결 불가/);
assert.match(nodes.status.textContent,/자료 갱신 지연/);
ctx.render({ok:false});
assert.match(nodes.status.textContent,/실패/);

// Hidden providers: no card, and they never make the status "stale".
ctx.render({ok:true,source:'LIVE_PC',synchronized:true,data:{exportedAt:'2026-10-19T22:07:00+09:00',providers:[
  {...claude,fresh:true},{name:'ChatGPT 웹/앱',fresh:false},{name:'Antigravity',fresh:false}]}});
assert.equal(nodes.list.children.length,1,'ChatGPT web and Antigravity hidden');
assert.match(nodes.status.textContent,/최근 사용량 관측/);

// Control tab without data from an old sync: explicit message, not empty.
ctx.show('control');
assert.equal(nodes.list.hidden,true); assert.equal(nodes.control.hidden,false);
assert.match(nodes.status.textContent,/관제판 자료 없음/);
assert.match(text(nodes.control),/아직 포함되지 않았어요/);

// Control tab with PC load and works.
const cc={schema:'YKH_CONTROL_MOBILE_V1',observedAt:'2026-11-06T08:41:24+00:00',state:'OK',
  counts:{VERIFYING:6,WAITING_USER:2,FAILED:0,total:16},
  attention:[{workId:'AGP-20261105-0007',kind:'DECISION',projectId:'PILOT',title:'훅 검증'}],
  works:[{workId:'AGP-1',title:'REV 정합',priority:'P0',state:'BLOCKED',next:'원천 확보'}],
  pcs:[{id:'YKH-RENDER',label:'렌더 PC',state:'OK',cpuPct:96,cpuMax1h:97,memPct:28.8,memAvailGb:22.7,memTotalGb:31.9,
        gpu:[{name:'RTX 2080 Ti',utilPct:0,memUsedGb:0.5,memTotalGb:11}],measuredAt:'2026-11-06T08:41:24+00:00',alertCount:1},
       {id:'YKH-SangMinYang',label:'로컬 PC',state:'LOST',cpuPct:null,memPct:null,gpu:[]}]};
ctx.render({ok:true,source:'CACHED_DRIVE',synchronized:true,data:{exportedAt:'2026-11-06T17:41:00+09:00',providers:[],controlCenter:cc}});
const all=text(nodes.control);
assert.match(nodes.status.textContent,/관제판 정상 수집/);
assert.match(all,/렌더 PC · 정상/); assert.match(all,/96\.0%/); assert.match(all,/1시간 최고 97\.0%/);
assert.match(all,/여유 22\.7GB/); assert.match(all,/RTX 2080 Ti/); assert.match(all,/경보 1건/);
assert.match(all,/로컬 PC · 수신 끊김/); assert.match(all,/미확인/);
assert.match(all,/검증 중 6/); assert.doesNotMatch(all,/실패 0/);
assert.match(all,/확인 필요 1건/); assert.match(all,/\[P0\] REV 정합/); assert.match(all,/막힘/);
const hot=nodes.control.children[0].children.find(c=>c.className==='track').children[0];
assert.equal(hot.className,'fill crit','CPU over 95% is red');
ctx.show('usage');
assert.equal(nodes.tabUsage.attrs['aria-selected'],'true');
console.log('TAKY_USAGE_MOBILE_VIEW_REGRESSION_PASS stale, missing, transfer-delay, failure, hidden, control-tab');
