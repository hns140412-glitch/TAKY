#!/usr/bin/env python3
"""Real headless Chrome/Playwright interaction QA for the ArchiGrow solar viewer (2 scenarios).

Manual execution only. Verifies rendering/interaction of the generated standalone viewers; does not assert
legal sunlight compliance, real-site data, or design approval.
  scenario 1: synthetic 3-date study  -> alt / date / time / grid / hover interactions change state + canvas
  scenario 2: unknown-height study    -> LIMITED banner, uncertain receivers, nominal withheld on hover
"""
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(case_dir, chrome):
    from playwright.sync_api import sync_playwright
    case_dir = Path(case_dir)
    out = case_dir / "browser_qa"
    out.mkdir(exist_ok=True)
    s1 = case_dir / "synthetic_run" / "stages" / "SOLAR_STUDY" / "solar_viewer.html"
    s2 = case_dir / "unknown_height_run" / "stages" / "SOLAR_STUDY" / "solar_viewer.html"
    checks, errors = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=str(chrome), args=["--disable-gpu"])
        try:
            page = browser.new_page(viewport={"width": 1500, "height": 900}, device_scale_factor=1)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            cv = page.locator("#cv")
            state = lambda: page.evaluate("window.__solar")

            def set_time(i):
                page.locator("#time").evaluate("(e,v)=>{e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}))}", i)
                page.wait_for_timeout(80)

            # ---- scenario 1
            assert s1.is_file(), "VIEWER_MISSING:" + str(s1)
            page.goto(s1.as_uri(), wait_until="load")
            page.wait_for_selector("#kpi tr")
            assert state()["status"] == "PASS"
            n = page.locator("#time").evaluate("e=>Number(e.max)")
            set_time(2)
            morning = state(); d_morning = sha(cv.screenshot())
            set_time(n - 3)
            evening = state(); d_evening = sha(cv.screenshot())
            assert morning["az"] < 180 < evening["az"], (morning, evening)
            assert d_morning != d_evening, "TIME_CHANGE_DID_NOT_CHANGE_CANVAS"
            page.screenshot(path=str(out / "s1_winter_evening_balanced.png"), full_page=True)
            set_time(2)
            kpi_a = page.locator("#kpi").inner_text()
            page.select_option("#alt", "SCULPTURAL")
            page.wait_for_timeout(80)
            kpi_b = page.locator("#kpi").inner_text(); d_alt = sha(cv.screenshot())
            assert state()["alt"] == "SCULPTURAL" and d_alt != d_morning, "ALT_CHANGE_DID_NOT_CHANGE_CANVAS"
            page.select_option("#alt", "BALANCED")
            page.select_option("#date", "2")  # summer solstice
            page.wait_for_timeout(100)
            summer = state(); d_summer = sha(cv.screenshot())
            page.select_option("#date", "0")
            page.wait_for_timeout(100)
            set_time(page.locator("#time").evaluate("e=>Math.round(Number(e.max)/2)"))
            winter_noon = state()
            page.select_option("#date", "2")
            set_time(page.locator("#time").evaluate("e=>Math.round(Number(e.max)/2)"))
            summer_noon = state()
            assert summer_noon["el"] > winter_noon["el"] + 25, (summer_noon, winter_noon)
            page.select_option("#date", "0")
            set_time(page.locator("#time").evaluate("e=>Math.round(Number(e.max)/2)"))
            page.select_option("#gridMode", "loss")
            page.wait_for_timeout(120)
            d_grid = sha(cv.screenshot())
            page.screenshot(path=str(out / "s1_loss_grid.png"), full_page=True)
            page.select_option("#gridMode", "off")
            page.wait_for_timeout(80)
            assert sha(cv.screenshot()) != d_grid, "GRID_TOGGLE_NO_EFFECT"
            box = cv.bounding_box()
            hit = False
            for dx in range(0, int(box["width"]), 24):
                for dy in range(int(box["height"] * 0.1), int(box["height"] * 0.9), 24):
                    page.mouse.move(box["x"] + dx, box["y"] + dy)
                    if "RCV-" in page.locator("#hover").inner_text():
                        hit = True
                        break
                if hit:
                    break
            assert hit, "HOVER_NEVER_REACHED_A_RECEIVER"
            before = state()["time"]
            page.locator("#play").click()
            page.wait_for_timeout(700)
            page.locator("#play").click()
            assert state()["time"] != before, "PLAY_DID_NOT_ADVANCE_TIME"
            checks.append({"scenario": "synthetic_three_dates", "html": str(s1), "html_sha256": sha(s1.read_bytes()),
                           "morning": morning, "evening": evening, "winter_noon": winter_noon, "summer_noon": summer_noon,
                           "kpi_table_identical_between_alts": kpi_a == kpi_b, "hover_info": page.locator("#hover").inner_text()[:160],
                           "canvas_digests": {"morning": d_morning, "evening": d_evening, "alt": d_alt, "summer": d_summer},
                           "actual_browser_interactions": True})
            # ---- scenario 2
            assert s2.is_file(), "VIEWER_MISSING:" + str(s2)
            page.goto(s2.as_uri(), wait_until="load")
            page.wait_for_selector("#kpi tr")
            banner = page.locator("#statusBanner").inner_text()
            assert state()["status"] == "LIMITED" and "제한" in banner, banner
            mid = page.locator("#time").evaluate("e=>Math.round(Number(e.max)/2)")
            set_time(mid)
            page.wait_for_timeout(150)
            page.screenshot(path=str(out / "s2_limited_unknown_height.png"), full_page=True)
            assert "구간" in page.locator("#top").inner_text() or "–" in page.locator("#top").inner_text(), "BOUNDS_NOT_SHOWN"
            uncertain = page.evaluate("""()=>{const d=document.querySelector('script').textContent;return d.includes('"unknown":true')}""")
            assert uncertain, "UNKNOWN_HEIGHT_OBSTACLE_NOT_MARKED"
            found = False
            box = cv.bounding_box()
            for dx in range(0, int(box["width"]), 14):
                for dy in range(int(box["height"] * 0.1), int(box["height"] * 0.9), 14):
                    page.mouse.move(box["x"] + dx, box["y"] + dy)
                    if "공칭값 보류" in page.locator("#hover").inner_text():
                        found = True
                        break
                if found:
                    break
            assert found, "NO_UNCERTAIN_RECEIVER_HOVER_WITH_WITHHELD_NOMINAL"
            checks.append({"scenario": "unknown_height_limited", "html": str(s2), "html_sha256": sha(s2.read_bytes()),
                           "banner": banner, "hover_info": page.locator("#hover").inner_text()[:200],
                           "actual_browser_interactions": True})
            assert not errors, errors
        finally:
            browser.close()
    receipt = {"schema": "ARCHIGROW_SOLAR_BROWSER_QA_V1", "executed_at": datetime.now(timezone.utc).isoformat(),
               "state": "BROWSER_RENDER_AND_INTERACTION_TESTED", "tests": checks, "js_errors": errors,
               "screenshot_dir": str(out), "legal_sunlight_verification": "NOT_EVALUATED",
               "real_site_data_verification": "NOT_EXECUTED_SYNTHETIC_FIXTURE", "user_design_approval": "NOT_OBTAINED"}
    (out / "solar_browser_qa_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-dir", required=True, type=Path)
    ap.add_argument("--chrome", default=r"C:\Program Files\Google\Chrome\Application\chrome.exe", type=Path)
    a = ap.parse_args()
    r = run(a.case_dir, a.chrome)
    print(json.dumps({"state": r["state"], "scenarios": [t["scenario"] for t in r["tests"]],
                      "receipt": str(a.case_dir / "browser_qa" / "solar_browser_qa_receipt.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
