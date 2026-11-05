// Regression: transfer freshness is not provider freshness; missing windows stay visible.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, 'TAKY_USAGE_MOBILE_VIEW.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script, 'embedded viewer script');
class Element {
  constructor(tag) { this.tag=tag; this.className=''; this.textContent=''; this.style={}; this.children=[]; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children=[...nodes]; }
}
const nodes={status:new Element('div'),list:new Element('main')};
let intervals=0;
const api = { withSuccessHandler(fn) { this.success=fn; return this; },
  withFailureHandler(fn) { this.failure=fn;return this; }, loadUsage() {} };
const ctx = { document: {getElementById: id => nodes[id],createElement: tag => new Element(tag)},
  google:{script:{run:api}},setInterval:()=>{intervals++}, console };
vm.runInNewContext(script, ctx);
assert.equal(intervals,1,'auto refresh wired');
const claude = {name:'Claude Code',observedAt:'2026-10-19T11:30:00+09:00',
  fresh:false,fiveHour:{usedPercent:null},week:{usedPercent:49,resetAt:'2026-10-21T12:00:00+09:00'}};
ctx.render({ok:true,synchronized:true,data:{exportedAt:'2026-10-19T22:07:00+09:00',providers:[claude]}});
assert.match(nodes.status.textContent,/파일 전송 정상/);
assert.match(nodes.status.textContent,/실제 사용량 지연\/미확인: Claude Code/);
const lines=nodes.list.children[0].children.filter(c=>c.className==='line');
assert.equal(lines.length,2,'five-hour and weekly usage always shown');
assert.equal(lines[0].children[1].textContent,'미확인');
assert.equal(lines[1].children[1].textContent,'49.0%');
ctx.render({ok:true,synchronized:false,data:{exportedAt:'2026-10-19T22:07:00+09:00',providers:[{...claude,fresh:true}]}});
assert.match(nodes.status.textContent,/파일 전송 지연/);
assert.ok(!nodes.status.textContent.includes('최근 사용량 관측') || nodes.status.textContent.includes('파일 전송 지연'));
ctx.render({ok:false});
assert.match(nodes.status.textContent,/실패/);
console.log('TAKY_USAGE_MOBILE_VIEW_REGRESSION_PASS stale, missing, transfer-delay, failure');