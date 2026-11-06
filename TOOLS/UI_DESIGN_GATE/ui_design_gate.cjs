#!/usr/bin/env node
// TAKY UI DESIGN GATE runner — executable form of the UI parts of the TAKY DESIGN_GATE contract
// (DG-08 subreceipts, DG-09 hash invalidation, PS14 resize/reflow/text-spacing/target-size,
//  PS20 visual compare, PS23 receipt binding). Local only: no upload, no model call.
//
// usage: node ui_design_gate.cjs <spec.json> [--out DIR] [--previous receipt.json]
// exit:  0 = PASS (warnings allowed), 1 = FAIL, 2 = usage/harness error
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const VERSION = 'TAKY_UI_DESIGN_GATE_V1';

function loadPlaywright() {
  const tries = [process.env.PLAYWRIGHT_MODULE, 'playwright', 'playwright-core'];
  try {
    const g = require('node:child_process').execSync('npm root -g', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    tries.push(path.join(g, 'playwright'), path.join(g, '@playwright', 'mcp', 'node_modules', 'playwright'));
  } catch { /* npm missing is fine */ }
  for (const t of tries.filter(Boolean)) { try { return require(t); } catch { /* next */ } }
  throw new Error('PLAYWRIGHT_NOT_FOUND (set PLAYWRIGHT_MODULE)');
}

async function launch(chromium) {
  const errs = [];
  for (const opt of [{}, { channel: 'chrome' }, { channel: 'msedge' }, process.env.CHROME_PATH && { executablePath: process.env.CHROME_PATH }].filter(Boolean)) {
    try { return { browser: await chromium.launch(opt), engine: opt.channel || (opt.executablePath ? 'custom' : 'bundled') }; }
    catch (e) { errs.push(String(e.message).split('\n')[0]); }
  }
  throw new Error('BROWSER_LAUNCH_FAILED: ' + errs.join(' | '));
}

// Local static server (127.0.0.1 only). Serves text as UTF-8 like most real hosts
// (Apps Script, Netlify); file:// would fall back to a legacy encoding for pages without <meta charset>.
function serve(root) {
  const http = require('node:http');
  const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif', '.woff2': 'font/woff2' };
  const rootAbs = path.resolve(root);
  const srv = http.createServer((req, res) => {
    let rel; try { rel = decodeURIComponent(new URL(req.url, 'http://x').pathname); } catch { res.writeHead(400); return res.end(); }
    const f = path.resolve(rootAbs, '.' + rel);
    if (f !== rootAbs && !f.startsWith(rootAbs + path.sep)) { res.writeHead(403); return res.end(); }
    fs.readFile(f, (err, buf) => {
      if (err) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'content-type': types[path.extname(f).toLowerCase()] || 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(buf);
    });
  });
  return new Promise(ok => srv.listen(0, '127.0.0.1', () => ok({ srv, origin: `http://127.0.0.1:${srv.address().port}` })));
}

const sha256 = buf => crypto.createHash('sha256').update(buf).digest('hex');
const resolveFrom = (base, p) => (path.isAbsolute(p) ? p : path.resolve(base, p));
function withCacheBust(u, n) {
  const hashAt = u.indexOf('#');
  const head = hashAt < 0 ? u : u.slice(0, hashAt), hash = hashAt < 0 ? '' : u.slice(hashAt);
  return head + (head.includes('?') ? '&' : '?') + '__dg=' + n + hash;
}

// ---------- in-page probes (serialized into the browser) ----------
const PROBE = () => {
  const d = document.documentElement;
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const label = e => (e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (typeof e.className === 'string' && e.className ? '.' + e.className.trim().split(/\s+/).join('.') : '') + ' "' + (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 30) + '"');
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const lum = c => { const f = x => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const bgOf = e => { for (let n = e; n; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > 0.5) return c; } return { r: 255, g: 255, b: 255, a: 1 }; };
  const overflow = [...document.querySelectorAll('body *')].filter(e => vis(e) && e.getBoundingClientRect().right > d.clientWidth + 1 && getComputedStyle(e).position !== 'fixed').map(label);
  const targets = [...document.querySelectorAll('button,a[href],input:not([type=hidden]),select,textarea,[role=button],[role=tab],[role=link],[role=checkbox],[role=switch]')]
    .filter(vis).map(e => { const r = e.getBoundingClientRect(); return { el: label(e), w: Math.round(r.width), h: Math.round(r.height), inline: e.tagName === 'A' && getComputedStyle(e).display === 'inline' }; });
  const contrast = [];
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e) || ![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const s = getComputedStyle(e); const fg = parse(s.color); if (!fg) continue;
    const bg = bgOf(e); const a = fg.a; const mix = { r: fg.r * a + bg.r * (1 - a), g: fg.g * a + bg.g * (1 - a), b: fg.b * a + bg.b * (1 - a) };
    const L1 = lum(mix), L2 = lum(bg); const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const px = parseFloat(s.fontSize), bold = parseInt(s.fontWeight, 10) >= 700;
    const large = px >= 24 || (bold && px >= 18.66);
    contrast.push({ el: label(e), ratio: Math.round(ratio * 100) / 100, need: large ? 3 : 4.5 });
  }
  const SEL_ROLES = ['tab', 'option', 'row', 'gridcell', 'treeitem', 'columnheader', 'rowheader'];
  const aria = [];
  document.querySelectorAll('[aria-selected]').forEach(e => { if (!SEL_ROLES.includes(e.getAttribute('role'))) aria.push('aria-selected without selectable role: ' + label(e)); });
  document.querySelectorAll('[role=tab]').forEach(e => { if (!e.closest('[role=tablist]')) aria.push('role=tab outside tablist: ' + label(e)); });
  document.querySelectorAll('[aria-controls]').forEach(e => { e.getAttribute('aria-controls').split(/\s+/).forEach(id => { if (id && !document.getElementById(id)) aria.push('aria-controls target missing: ' + id); }); });
  document.querySelectorAll('button,[role=button],[role=tab],a[href]').forEach(e => { if (vis(e) && !(e.innerText || '').trim() && !e.getAttribute('aria-label') && !e.getAttribute('aria-labelledby') && !e.getAttribute('title')) aria.push('control without accessible name: ' + label(e)); });
  document.querySelectorAll('img').forEach(e => { if (!e.hasAttribute('alt')) aria.push('img without alt: ' + label(e)); });
  if (!document.documentElement.getAttribute('lang')) aria.push('html lang missing');
  return { hScroll: d.scrollWidth > d.clientWidth + 1, scrollWidth: d.scrollWidth, clientWidth: d.clientWidth, overflow: overflow.slice(0, 8), targets, contrast, aria, text: document.body.innerText };
};
const TEXT_SPACING_CSS = '*{line-height:1.5!important;letter-spacing:0.12em!important;word-spacing:0.16em!important}p,div,li{margin-bottom:2em!important}';

async function pixelDiff(page, a, b) {
  return page.evaluate(async ([A, B]) => {
    const img = src => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = 'data:image/png;base64,' + src; });
    const [x, y] = await Promise.all([img(A), img(B)]);
    const w = Math.max(x.width, y.width), h = Math.max(x.height, y.height);
    const draw = i => { const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.drawImage(i, 0, 0); return g.getImageData(0, 0, w, h).data; };
    const p = draw(x), q = draw(y); let diff = 0;
    for (let k = 0; k < p.length; k += 4) if (Math.abs(p[k] - q[k]) > 32 || Math.abs(p[k + 1] - q[k + 1]) > 32 || Math.abs(p[k + 2] - q[k + 2]) > 32) diff++;
    return { width: w, height: h, sizeChanged: x.width !== y.width || x.height !== y.height, diffRatio: diff / (w * h) };
  }, [a.toString('base64'), b.toString('base64')]);
}

function sub() { return { result: 'PASS', checks: 0, fails: [], warns: [], evidence: {} }; }
function fail(s, msg) { s.fails.push(msg); s.result = 'FAIL'; }
function warn(s, msg) { s.warns.push(msg); if (s.result === 'PASS') s.result = 'PASS_WITH_WARNINGS'; }

async function run(specPath, opts = {}) {
  const specRaw = fs.readFileSync(specPath);
  const spec = JSON.parse(specRaw.toString('utf8'));
  const base = path.dirname(path.resolve(specPath));
  const out = path.resolve(opts.out || path.join(base, 'dg_out', spec.name || 'gate'));
  const shots = path.join(out, 'shots');
  fs.mkdirSync(shots, { recursive: true });
  const T = Object.assign({ targetMin: 24, targetRecommended: 44, zoom: 2 }, spec.thresholds || {});
  const viewports = spec.viewports || [320, 390, 768];
  const shotViewports = new Set(spec.screenshotViewports || [viewports.includes(390) ? 390 : viewports[0]]);
  const artifacts = (spec.artifacts || []).map(p => { const f = resolveFrom(base, p); return { path: f, sha256: sha256(fs.readFileSync(f)) }; });
  const S = { HARNESS_HEALTH: sub(), TARGET_RENDER: sub(), INTERACTION: sub(), A11Y: sub(), VISUAL_COMPARE: sub(), PERFORMANCE_CONTEXT: sub() };
  // Relative page URLs are served over a local UTF-8 HTTP server rooted at spec.serveRoot (default: spec dir).
  const served = await serve(resolveFrom(base, spec.serveRoot || '.'));
  const serveRootAbs = resolveFrom(base, spec.serveRoot || '.');
  const toPageUrl = u => {
    if (/^(https?|file|data):/i.test(u)) return u;
    const cut = u.search(/[?#]/);
    const file = cut < 0 ? u : u.slice(0, cut), rest = cut < 0 ? '' : u.slice(cut);
    const rel = path.relative(serveRootAbs, resolveFrom(base, file));
    if (rel.startsWith('..')) throw new Error('PAGE_OUTSIDE_SERVE_ROOT: ' + u);
    return served.origin + '/' + rel.split(path.sep).map(encodeURIComponent).join('/') + rest;
  };
  const { chromium } = loadPlaywright();
  const { browser, engine } = await launch(chromium);
  const ctx = await browser.newContext({ deviceScaleFactor: 1, locale: spec.locale || 'ko-KR', timezoneId: spec.timezone || 'Asia/Seoul' });
  if (spec.inject) await ctx.addInitScript({ path: resolveFrom(base, spec.inject) });
  const page = await ctx.newPage();
  const consoleErrors = []; let requests = 0;
  page.on('pageerror', e => consoleErrors.push('pageerror: ' + e.message));
  // Failed loads are judged by URL (the console text has none); a missing favicon is not a page defect.
  page.on('console', m => { if (m.type() === 'error' && !/^Failed to load resource/.test(m.text())) consoleErrors.push(m.text()); });
  page.on('response', r => { if (r.status() >= 400 && !/\/favicon\.ico(\?|$)/.test(r.url())) consoleErrors.push(`HTTP ${r.status()} ${r.url().replace(/^https?:\/\/127\.0\.0\.1:\d+/, '')}`); });
  page.on('request', () => { requests++; });
  let n = 0;
  const open = async (url, w) => {
    await page.setViewportSize({ width: w, height: spec.viewportHeight || 800 });
    const t0 = Date.now();
    await page.goto(withCacheBust(toPageUrl(url), ++n), { waitUntil: 'load' });
    if (spec.ready) await page.waitForFunction(spec.ready, null, { timeout: spec.readyTimeoutMs || 8000 });
    return Date.now() - t0;
  };
  const shot = async name => { const f = path.join(shots, name.replace(/[^\w.-]+/g, '_') + '.png'); await page.screenshot({ path: f, fullPage: true }); return f; };
  const loadTimes = [];
  try {
    for (const pg of spec.pages) {
      for (const w of viewports) {
        const tag = `${pg.id}@${w}`;
        try { loadTimes.push(await open(pg.url, w)); S.HARNESS_HEALTH.checks++; }
        catch (e) { fail(S.HARNESS_HEALTH, `${tag}: not ready (${String(e.message).split('\n')[0]})`); continue; }
        const m = await page.evaluate(PROBE);
        S.TARGET_RENDER.checks++;
        if (m.hScroll) fail(S.TARGET_RENDER, `${tag}: horizontal scroll ${m.scrollWidth}>${m.clientWidth} ${m.overflow.slice(0, 2).join(', ')}`);
        for (const t of pg.expectText || []) if (!m.text.includes(t)) fail(S.TARGET_RENDER, `${tag}: missing text "${t}"`);
        for (const t of pg.forbidText || []) if (m.text.includes(t)) fail(S.TARGET_RENDER, `${tag}: forbidden text "${t}"`);
        S.A11Y.checks++;
        for (const t of m.targets) {
          if (t.inline) continue;
          const min = Math.min(t.w, t.h);
          if (min < T.targetMin) fail(S.A11Y, `${tag}: target ${min}px < ${T.targetMin}px ${t.el}`);
          else if (min < T.targetRecommended) warn(S.A11Y, `${tag}: target ${min}px < ${T.targetRecommended}px ${t.el}`);
        }
        for (const c of m.contrast) if (c.ratio < c.need) fail(S.A11Y, `${tag}: contrast ${c.ratio} < ${c.need} ${c.el}`);
        for (const a of m.aria) fail(S.A11Y, `${tag}: ${a}`);
        if (shotViewports.has(w)) S.TARGET_RENDER.evidence[tag] = await shot(tag);
      }
      // PS14: 200% zoom at the narrowest viewport, text spacing at the shot viewport
      const wz = Math.min(...viewports), ws = [...shotViewports][0];
      try {
        await open(pg.url, wz); await page.evaluate(z => { document.body.style.zoom = String(z); }, T.zoom);
        const z = await page.evaluate(PROBE);
        if (z.hScroll) fail(S.A11Y, `${pg.id}@${wz}: ${T.zoom * 100}% zoom horizontal scroll ${z.overflow.slice(0, 2).join(', ')}`);
        S.A11Y.evidence[`${pg.id}_zoom`] = await shot(`${pg.id}@${wz}_zoom${T.zoom * 100}`);
        await open(pg.url, ws); await page.addStyleTag({ content: TEXT_SPACING_CSS });
        const ts = await page.evaluate(PROBE);
        if (ts.hScroll) fail(S.A11Y, `${pg.id}@${ws}: text-spacing overflow ${ts.overflow.slice(0, 2).join(', ')}`);
        S.A11Y.checks += 2;
      } catch (e) { fail(S.HARNESS_HEALTH, `${pg.id}: zoom/text-spacing run failed (${String(e.message).split('\n')[0]})`); }
      // keyboard focus visibility on the first focusables
      try {
        await open(pg.url, ws);
        const seen = [];
        for (let k = 0; k < Math.min(spec.focusSteps || 6, 20); k++) {
          await page.keyboard.press('Tab');
          const f = await page.evaluate(() => { const e = document.activeElement; if (!e || e === document.body) return null; const s = getComputedStyle(e); return { el: e.tagName + (e.id ? '#' + e.id : '') + ' ' + (e.innerText || '').trim().slice(0, 20), visible: (s.outlineStyle !== 'none' && (s.outlineStyle === 'auto' || parseFloat(s.outlineWidth) > 0)) || s.boxShadow !== 'none' }; });
          if (f) seen.push(f);
        }
        S.A11Y.checks++;
        [...new Set(seen.filter(f => !f.visible).map(f => f.el))].forEach(el => fail(S.A11Y, `${pg.id}: focus not visible on ${el}`));
        S.A11Y.evidence[`${pg.id}_focusOrder`] = seen.map(f => f.el);
      } catch (e) { warn(S.A11Y, `${pg.id}: focus walk skipped (${String(e.message).split('\n')[0]})`); }
    }
    // INTERACTION
    for (const it of spec.interactions || []) {
      const pg = spec.pages.find(p => p.id === it.page);
      if (!pg) { fail(S.INTERACTION, `${it.name}: unknown page ${it.page}`); continue; }
      try {
        await open(pg.url, it.viewport || [...shotViewports][0]);
        for (const st of it.steps) {
          S.INTERACTION.checks++;
          if (st.click) await page.locator(st.click).first().click();
          else if (st.press) await page.keyboard.press(st.press);
          else if (st.focus) await page.locator(st.focus).first().focus();
          else if (st.expectVisible) { if (!await page.locator(st.expectVisible).first().isVisible()) fail(S.INTERACTION, `${it.name}: not visible ${st.expectVisible}`); }
          else if (st.expectHidden) { if (await page.locator(st.expectHidden).first().isVisible()) fail(S.INTERACTION, `${it.name}: still visible ${st.expectHidden}`); }
          else if (st.expectAttr) { const v = await page.locator(st.expectAttr.selector).first().getAttribute(st.expectAttr.name); if (v !== st.expectAttr.value) fail(S.INTERACTION, `${it.name}: ${st.expectAttr.selector}[${st.expectAttr.name}]=${v} != ${st.expectAttr.value}`); }
          else if (st.expectText) { const t = await page.evaluate(() => document.body.innerText); if (!t.includes(st.expectText)) fail(S.INTERACTION, `${it.name}: missing text "${st.expectText}"`); }
        }
        S.INTERACTION.evidence[it.name] = await shot('interaction_' + it.name);
      } catch (e) { fail(S.INTERACTION, `${it.name}: ${String(e.message).split('\n')[0]}`); }
    }
    if (!(spec.interactions || []).length) { S.INTERACTION.result = 'N/A'; }
    // PS20 VISUAL_COMPARE
    for (const v of spec.baselines || []) {
      const pg = spec.pages.find(p => p.id === v.page); const w = v.viewport || [...shotViewports][0];
      try {
        await open(v.url, w); const before = await page.screenshot({ fullPage: true }); fs.writeFileSync(path.join(shots, `baseline_${v.page}@${w}.png`), before);
        await open(pg.url, w); const after = await page.screenshot({ fullPage: true });
        const d = await pixelDiff(page, before, after); S.VISUAL_COMPARE.checks++;
        S.VISUAL_COMPARE.evidence[v.page] = Object.assign({ baseline_url: v.url, baseline_sha256: v.file ? sha256(fs.readFileSync(resolveFrom(base, v.file))) : null }, d);
        const max = v.maxDiffRatio ?? 0.01;
        if (d.diffRatio > max || d.sizeChanged) {
          if (v.expectedChange) warn(S.VISUAL_COMPARE, `${v.page}@${w}: diff ${(d.diffRatio * 100).toFixed(1)}% (expected change: ${v.expectedChange}) — needs owner acceptance`);
          else fail(S.VISUAL_COMPARE, `${v.page}@${w}: diff ${(d.diffRatio * 100).toFixed(1)}% > ${(max * 100).toFixed(1)}%`);
        }
      } catch (e) { fail(S.VISUAL_COMPARE, `${v.page}: ${String(e.message).split('\n')[0]}`); }
    }
    if (!(spec.baselines || []).length) { S.VISUAL_COMPARE.result = 'N/A'; }
  } finally { await browser.close(); served.srv.close(); }
  // HARNESS_HEALTH / PERFORMANCE_CONTEXT
  consoleErrors.forEach(e => fail(S.HARNESS_HEALTH, 'console: ' + e.slice(0, 160)));
  S.HARNESS_HEALTH.evidence = { engine, pagesOpened: n };
  S.PERFORMANCE_CONTEXT.checks = loadTimes.length;
  const maxLoad = Math.max(0, ...loadTimes);
  S.PERFORMANCE_CONTEXT.evidence = { maxLoadMs: maxLoad, requests, note: 'local harness timing, not field data' };
  if (maxLoad > (T.maxLoadMs || 5000)) warn(S.PERFORMANCE_CONTEXT, `slow load ${maxLoad}ms`);
  // DG-09 stale detection
  let previous = null;
  if (opts.previous && fs.existsSync(opts.previous)) {
    const p = JSON.parse(fs.readFileSync(opts.previous, 'utf8'));
    const now = Object.fromEntries(artifacts.map(a => [a.path, a.sha256]));
    const changed = (p.artifacts || []).filter(a => now[a.path] && now[a.path] !== a.sha256).map(a => a.path);
    previous = { receipt: opts.previous, spec_changed: p.spec_sha256 !== sha256(specRaw), artifacts_changed: changed, previous_now: changed.length || p.spec_sha256 !== sha256(specRaw) ? 'STALE' : 'STILL_BOUND' };
  }
  const results = Object.values(S).map(s => s.result);
  const verdict = results.includes('FAIL') ? 'FAIL' : results.includes('PASS_WITH_WARNINGS') ? 'PASS_WITH_WARNINGS' : 'PASS';
  const receipt = {
    receipt: VERSION, created_at: new Date().toISOString(), spec: path.resolve(specPath), spec_sha256: sha256(specRaw),
    artifacts, viewports, profile: 'UI_IMPLEMENTATION',
    gate_refs: ['DG-08', 'DG-09', 'PS14', 'PS20', 'PS23'],
    claim_ceiling: 'Browser harness on this PC. Not a real device; DEVICE_OR_RUNTIME stays OPEN until an owner/device check is recorded.',
    subreceipts: Object.assign({}, S, { FONT_PRINT_PDF: { result: 'N/A' }, DEVICE_OR_RUNTIME: { result: 'OPEN' } }),
    previous, verdict
  };
  for (const s of Object.values(receipt.subreceipts)) { if (s.fails) s.fails = s.fails.slice(0, 40); if (s.warns) s.warns = [...new Set(s.warns)].slice(0, 40); }
  const rf = path.join(out, 'DG_RECEIPT.json');
  fs.writeFileSync(rf, JSON.stringify(receipt, null, 2));
  return { receipt, file: rf };
}

if (require.main === module) {
  const a = process.argv.slice(2);
  const spec = a.find(x => !x.startsWith('--'));
  const val = k => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : undefined; };
  if (!spec) { console.error('usage: node ui_design_gate.cjs <spec.json> [--out DIR] [--previous receipt.json]'); process.exit(2); }
  run(spec, { out: val('--out'), previous: val('--previous') }).then(({ receipt, file }) => {
    for (const [k, s] of Object.entries(receipt.subreceipts)) {
      console.log(`${k.padEnd(20)} ${s.result}${s.fails && s.fails.length ? '  ' + s.fails.length + ' fail' : ''}${s.warns && s.warns.length ? '  ' + s.warns.length + ' warn' : ''}`);
      (s.fails || []).slice(0, 5).forEach(f => console.log('   x ' + f));
    }
    if (receipt.previous) console.log('previous receipt: ' + receipt.previous.previous_now);
    console.log(`VERDICT ${receipt.verdict}\nRECEIPT ${file}`);
    process.exit(receipt.verdict === 'FAIL' ? 1 : 0);
  }).catch(e => { console.error('HARNESS_ERROR ' + e.message); process.exit(2); });
}
module.exports = { run };
