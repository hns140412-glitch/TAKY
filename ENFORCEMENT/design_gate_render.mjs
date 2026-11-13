#!/usr/bin/env node
// TAKY design-gate render probe (TKY-UIREF-001 §20: DGC-16, DGC-19, DGC-07 evidence).
// Opens a page in real Chromium at declared viewports, takes screenshots, and
// measures facts a reviewer cannot get from source text alone.
// Usage: node design_gate_render.mjs <url-or-file> <out-dir> [viewports-json]
// Prints one JSON object to stdout. Facts only; PASS/FAIL is decided by design_gate_harness.py.
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

// Resolve playwright from the project or from a global install (NODE_PATH / preinstalled).
const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch {
  ({ chromium } = await import("playwright"));
}

const [, , target, outDir, vpArg] = process.argv;
if (!target || !outDir) {
  console.error("usage: design_gate_render.mjs <url-or-file> <out-dir> [viewports-json]");
  process.exit(2);
}
const DEFAULT_VIEWPORTS = [
  { id: "mobile", width: 390, height: 844 },
  { id: "tablet", width: 820, height: 1180 },
  { id: "desktop", width: 1440, height: 900 },
];
const viewports = vpArg ? JSON.parse(vpArg) : DEFAULT_VIEWPORTS;
const url = /^https?:\/\//.test(target) ? target : pathToFileURL(resolve(target)).href;
mkdirSync(outDir, { recursive: true });
const sha = (buf) => createHash("sha256").update(buf).digest("hex");

// Runs inside the page. Keep it dependency-free.
function probe() {
  const els = [...document.querySelectorAll("body *")].filter((e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
  });
  const textEls = els.filter((e) => [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
  const colors = new Set();
  let minFont = Infinity;
  let gradientText = 0, maskImage = 0, allCapsLabels = 0;
  for (const e of els) {
    const cs = getComputedStyle(e);
    if (cs.webkitBackgroundClip === "text" || cs.backgroundClip === "text") gradientText++;
    if ((cs.maskImage && cs.maskImage !== "none") || (cs.webkitMaskImage && cs.webkitMaskImage !== "none")) maskImage++;
  }
  for (const e of textEls) {
    const cs = getComputedStyle(e);
    colors.add(cs.color);
    if (cs.backgroundColor && cs.backgroundColor !== "rgba(0, 0, 0, 0)") colors.add(cs.backgroundColor);
    const fs = parseFloat(cs.fontSize);
    if (fs < minFont) minFont = fs;
    const t = e.textContent.trim();
    if (cs.textTransform === "uppercase" && t.length < 40 && fs <= 14) allCapsLabels++;
  }
  const doc = document.documentElement;
  const interactive = [...document.querySelectorAll("a,button,input,select,textarea,[role=button]")]
    .map((e) => e.getBoundingClientRect())
    .filter((r) => r.width > 0 && r.height > 0);
  const smallTargets = interactive.filter((r) => r.width < 24 || r.height < 24).length;
  const declaredFamilies = new Set();
  for (const e of textEls) declaredFamilies.add(getComputedStyle(e).fontFamily.split(",")[0].replace(/["']/g, "").trim());
  return {
    horizontal_overflow_px: Math.max(0, doc.scrollWidth - doc.clientWidth),
    min_font_px: minFont === Infinity ? null : minFont,
    text_colors: [...colors],
    gradient_text_count: gradientText,
    mask_image_count: maskImage,
    allcaps_label_count: allCapsLabels,
    interactive_count: interactive.length,
    small_target_count: smallTargets,
    primary_font_families: [...declaredFamilies],
  };
}


// First-viewport facts (DGC-27) and PREMIUM restraint facts (SAVEY PG01-PG12, ported 2026-11-12).
// Runs inside the page at scroll position 0.
function probeFirstViewport() {
  const vh = window.innerHeight;
  const vis = [...document.querySelectorAll("body *")].filter((e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && r.top < vh && r.bottom > 0 && cs.visibility !== "hidden" && cs.display !== "none";
  });
  const cs = (e) => getComputedStyle(e);
  const text = vis.filter((e) => [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
  const sat = (c) => {
    const m = (c || "").match(/[\d.]+/g); if (!m) return false;
    let [r, g, b, a = 1] = m.map(Number); if (a < 0.3) return false;
    r /= 255; g /= 255; b /= 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn, l = (mx + mn) / 2;
    const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    return s >= 0.3 && l >= 0.12 && l <= 0.93;
  };
  const weights = text.map((e) => +cs(e).fontWeight);
  const blurOver = (sh) => (sh.match(/(-?[\d.]+)px\s+(-?[\d.]+)px\s+([\d.]+)px/g) || []).some((m) => parseFloat(m.split("px")[2]) > 16);
  return {
    filled_cta_count: vis.filter((e) => e.matches("button,a,[role=button]") && sat(cs(e).backgroundColor)).length,
    interactive_count: vis.filter((e) => e.matches("button,a,[role=button],input,select,textarea")).length,
    typeface_count: new Set(text.map((e) => cs(e).fontFamily.split(",")[0].replace(/["']/g, "").trim())).size,
    font_size_count: new Set(text.map((e) => Math.round(parseFloat(cs(e).fontSize)))).size,
    heavy_weight_pct: Math.round(100 * weights.filter((w) => w >= 800).length / Math.max(1, weights.length)),
    light_weight_count: weights.filter((w) => w < 400).length,
    text_shadow_count: text.filter((e) => cs(e).textShadow !== "none").length,
    big_shadow_count: vis.filter((e) => cs(e).boxShadow !== "none" && blurOver(cs(e).boxShadow)).length,
    radius_count: new Set(vis.map((e) => cs(e).borderTopLeftRadius).filter((r) => r !== "0px" && !r.includes("%") && parseFloat(r) < 400)).size,
    gradient_count: vis.filter((e) => cs(e).backgroundImage.includes("gradient")).length,
    chars: text.reduce((n, e) => n + [...e.childNodes].filter((x) => x.nodeType === 3).map((x) => x.textContent.trim()).join("").length, 0),
  };
}

// DGC-28: at the end of the scroll, nothing readable may sit under a fixed/sticky element.
function probeFixedOverlap() {
  const all = [...document.querySelectorAll("body *")];
  const isPinned = (e) => { const p = getComputedStyle(e).position; return p === "fixed" || p === "sticky"; };
  const pinned = all.filter((e) => isPinned(e)).map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter(({ r }) => r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < window.innerHeight);
  const inside = (e) => { for (let a = e; a && a !== document.body; a = a.parentElement) if (isPinned(a)) return true; return false; };
  const hits = [];
  for (const e of all) {
    if ([...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()) && !inside(e)) {
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0 || r.bottom <= 0 || r.top >= window.innerHeight) continue;
      for (const { e: p, r: q } of pinned) {
        const ox = Math.min(r.right, q.right) - Math.max(r.left, q.left);
        const oy = Math.min(r.bottom, q.bottom) - Math.max(r.top, q.top);
        if (ox > 4 && oy > 4) { hits.push(`${e.tagName.toLowerCase()}:"${e.textContent.trim().slice(0, 24)}" under ${p.tagName.toLowerCase()}${p.className ? "." + String(p.className).split(" ")[0] : ""}`); break; }
      }
    }
  }
  return hits.slice(0, 10);
}

// DGC-25 / DGC-26 / same-shape card row (§20.1g). Config comes from the DESIGN.md dashboard block via DGATE_DASHBOARD.
const DASH = (() => { try { return JSON.parse(process.env.DGATE_DASHBOARD || "{}") || {}; } catch { return {}; } })();
function probeDashboard(dash) {
  const vh = window.innerHeight;
  const shown = (e) => { const r = e.getBoundingClientRect(), c = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && r.top < vh && r.bottom > 0 && c.visibility !== "hidden" && c.display !== "none"; };
  const ownText = (e) => [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join("").trim();
  const out = { same_shape_rows: [], decision_metric: null, status_check: null };
  const applies = !dash.applies_when || !!document.querySelector(dash.applies_when);
  // Same-shape card row: >=4 visible siblings of equal size, each a rounded "card" (border, shadow or own background).
  const isCard = (e) => { const c = getComputedStyle(e);
    return parseFloat(c.borderTopLeftRadius) >= 8 && (parseFloat(c.borderTopWidth) > 0 || c.boxShadow !== "none" ||
      !/rgba\(0, 0, 0, 0\)|transparent/.test(c.backgroundColor)); };
  for (const p of document.querySelectorAll("body *")) {
    const kids = [...p.children].filter(shown);
    if (kids.length < 4) continue;
    const rs = kids.map((k) => k.getBoundingClientRect());
    const sameRow = rs.every((r) => Math.abs(r.top - rs[0].top) <= 2);
    const sameSize = rs.every((r) => Math.abs(r.width - rs[0].width) <= 2 && Math.abs(r.height - rs[0].height) <= 2);
    if (sameRow && sameSize && kids.every(isCard))
      out.same_shape_rows.push(`${kids.length}x ${kids[0].tagName.toLowerCase()}${kids[0].className ? "." + String(kids[0].className).split(" ")[0] : ""} ${Math.round(rs[0].width)}x${Math.round(rs[0].height)}`);
  }
  out.same_shape_rows = out.same_shape_rows.slice(0, 5);
  const pick = (spec) => { if (!spec) return null; const [sel, attr] = String(spec).split("@");
    const e = document.querySelector(sel); if (!e) return { missing: sel };
    const raw = attr === "style" ? e.getAttribute("style") || "" : attr ? e.getAttribute(attr) || "" : e.textContent || "";
    const m = raw.replace(/,/g, "").match(/-?\d+(\.\d+)?/); return { raw: raw.trim().slice(0, 80), num: m ? Number(m[0]) : null, el: e }; };
  if (applies && dash.decision_metric_selector) {
    const m = pick(dash.decision_metric_selector);
    if (m && m.el) {
      const px = (e) => parseFloat(getComputedStyle(e).fontSize);
      const nums = [...document.querySelectorAll("body *")].filter((e) => shown(e) && /\d/.test(ownText(e)));
      const top = nums.reduce((a, e) => (px(e) > (a ? px(a) : 0) ? e : a), null);
      const metricPx = Math.max(px(m.el), ...[...m.el.querySelectorAll("*")].map(px));
      out.decision_metric = { metric_px: metricPx, max_number_px: top ? px(top) : 0, max_number_text: top ? ownText(top).slice(0, 30) : "" };
    } else out.decision_metric = m;
  }
  const sc = dash.status_check;
  if (applies && sc && sc.status) {
    const st = pick(sc.status), burn = pick(sc.burn_pct), el = pick(sc.elapsed_pct);
    out.status_check = { status: st && st.raw, burn_pct: burn && burn.num, elapsed_pct: el && el.num,
      missing: [st, burn, el].filter((x) => x && x.missing).map((x) => x.missing) };
  }
  return out;
}

const result = { schema: "TAKY_DESIGN_GATE_RENDER_V1", target: url, viewports: [], harness: { ok: true } };
let browser;
try {
  browser = await chromium.launch();
  for (const vp of viewports) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    await page.goto(url, { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    const facts = await page.evaluate(probe);
    // Which declared families actually rendered (DGC-19: loaded font == spec font).
    // document.fonts.check() reports unknown fonts as available in Chromium, so compare
    // rendered text width against generic fallbacks instead.
    facts.font_check = await page.evaluate((fams) => {
      const c = document.createElement("canvas").getContext("2d");
      const sample = "mmmmmmmmmmlliWW 가나다라마바 0123456789";
      const w = (font) => { c.font = font; return c.measureText(sample).width; };
      return Object.fromEntries(fams.map((f) => [f,
        ["monospace", "serif", "sans-serif"].some((g) => w(`40px "${f}", ${g}`) !== w(`40px ${g}`))]));
    }, facts.primary_font_families);
    facts.loaded_font_faces = await page.evaluate(() =>
      [...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family.replace(/["']/g, "")));
    facts.first_viewport = await page.evaluate(probeFirstViewport);
    facts.dashboard_probe = await page.evaluate(probeDashboard, DASH);
    const first = await page.screenshot({ fullPage: false });
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await page.waitForTimeout(150);
    facts.fixed_overlap_at_end = await page.evaluate(probeFixedOverlap);
    await page.evaluate(() => window.scrollTo(0, 0));
    const png = await page.screenshot({ fullPage: true });
    const safeId = String(vp.id).replace(/[^A-Za-z0-9._-]/g, "_").replace(/^\.+/, "_");
    const file = resolve(outDir, `${safeId}.png`);
    writeFileSync(file, png);
    const firstFile = resolve(outDir, `${safeId}.first.png`);
    writeFileSync(firstFile, first);
    result.viewports.push({ ...vp, screenshot: file, screenshot_sha256: sha(png),
      first_viewport_screenshot: firstFile, first_viewport_sha256: sha(first), ...facts });
    await page.close();
  }
  // Print/PDF output (DGC-19: export targets are rendered, not assumed).
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "networkidle" });
  const pdf = await page.pdf({ printBackground: true, preferCSSPageSize: true });
  const pdfFile = resolve(outDir, "print.pdf");
  writeFileSync(pdfFile, pdf);
  result.print = { pdf: pdfFile, pdf_sha256: sha(pdf), bytes: pdf.length };
  if (!/^https?:/.test(target)) result.artifact_sha256 = sha(readFileSync(resolve(target)));
} catch (err) {
  // Harness failure is HOLD, not a product FAIL (prior review C-05/C-08).
  result.harness = { ok: false, error: String(err && err.message || err) };
} finally {
  if (browser) await browser.close();
}
process.stdout.write(JSON.stringify(result));
