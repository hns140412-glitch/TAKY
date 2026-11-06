// Self-test: a good page must PASS, a bad page must FAIL for the right reasons,
// and DG-09 must mark a previous receipt STALE when the artifact changes.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { run } = require('../ui_design_gate.cjs');

(async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dg-selftest-'));
  const fx = path.join(__dirname, 'fixtures');
  fs.copyFileSync(path.join(fx, 'good.html'), path.join(tmp, 'good.html'));
  fs.copyFileSync(path.join(fx, 'bad.html'), path.join(tmp, 'bad.html'));
  const ready = "document.documentElement.dataset.ready==='1'";
  const goodSpec = path.join(tmp, 'good.json');
  fs.writeFileSync(goodSpec, JSON.stringify({
    name: 'good', artifacts: ['good.html'], ready, viewports: [320, 390],
    pages: [{ id: 'main', url: 'good.html', expectText: ['카드 하나'], forbidText: ['ERROR'] }],
    interactions: [{ name: 'switch', page: 'main', steps: [
      { click: '#tB' }, { expectVisible: '#pB' }, { expectHidden: '#pA' }, { expectAttr: { selector: '#tB', name: 'aria-selected', value: 'true' } }] }],
    baselines: [{ page: 'main', url: 'good.html', maxDiffRatio: 0.001 }]
  }));
  const g = await run(goodSpec, { out: path.join(tmp, 'out_good') });
  const gs = g.receipt.subreceipts;
  assert.equal(g.receipt.verdict, 'PASS', JSON.stringify(Object.fromEntries(Object.entries(gs).map(([k, v]) => [k, v.fails || v.result]))));
  assert.equal(gs.INTERACTION.result, 'PASS');
  assert.equal(gs.VISUAL_COMPARE.result, 'PASS');
  assert.equal(gs.DEVICE_OR_RUNTIME.result, 'OPEN');
  assert.equal(g.receipt.artifacts[0].sha256.length, 64);

  const badSpec = path.join(tmp, 'bad.json');
  fs.writeFileSync(badSpec, JSON.stringify({ name: 'bad', artifacts: ['bad.html'], ready, viewports: [320], pages: [{ id: 'main', url: 'bad.html', expectText: ['없는 문구'] }] }));
  const b = await run(badSpec, { out: path.join(tmp, 'out_bad') });
  const bs = b.receipt.subreceipts; const all = Object.values(bs).flatMap(s => s.fails || []).join('\n');
  assert.equal(b.receipt.verdict, 'FAIL');
  assert.equal(bs.TARGET_RENDER.result, 'FAIL');
  assert.match(all, /horizontal scroll/);
  assert.match(all, /missing text "없는 문구"/);
  assert.match(all, /target 18px < 24px/);
  assert.match(all, /contrast [0-9.]+ < 4\.5/);
  assert.match(all, /aria-selected without selectable role/);
  assert.match(all, /control without accessible name/);
  assert.match(all, /img without alt/);
  assert.match(all, /html lang missing/);
  assert.match(all, /focus not visible/);

  // DG-09: change the artifact -> previous receipt is STALE
  fs.appendFileSync(path.join(tmp, 'good.html'), '\n<!-- changed -->\n');
  const g2 = await run(goodSpec, { out: path.join(tmp, 'out_good2'), previous: g.file });
  assert.equal(g2.receipt.previous.previous_now, 'STALE');
  assert.equal(g2.receipt.previous.artifacts_changed.length, 1);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log('UI_DESIGN_GATE_SELFTEST_PASS good=PASS bad=FAIL(10 reasons) dg09=STALE');
})().catch(e => { console.error(e); process.exit(1); });
