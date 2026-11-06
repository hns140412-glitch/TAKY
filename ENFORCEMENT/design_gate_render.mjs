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
    const png = await page.screenshot({ fullPage: true });
    const file = resolve(outDir, `${vp.id}.png`);
    writeFileSync(file, png);
    result.viewports.push({ ...vp, screenshot: file, screenshot_sha256: sha(png), ...facts });
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
