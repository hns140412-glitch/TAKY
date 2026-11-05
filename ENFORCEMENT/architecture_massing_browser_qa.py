#!/usr/bin/env python3
"""Real Chrome/Playwright interaction checks for the ArchiGrow local massing viewer.

Manual execution only; does not assert original-video visual parity, legal
feasibility, deploy readiness, or signoff.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def run(folder, chrome):
    from playwright.sync_api import sync_playwright
    folder=Path(folder)
    out=folder/"browser_qa"
    out.mkdir(exist_ok=True)
    case_files=[
      ("reel",folder/"run"/"stages"/"MASSING"/"massing_viewer.html",6486,18),
      ("irregular",folder/"irregular_run"/"stages"/"MASSING"/"massing_viewer.html",2000,8),
    ]
    checks=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=str(chrome),args=["--disable-gpu"])
        try:
            page=browser.new_page(viewport={"width":1440,"height":900},device_scale_factor=1)
            errors=[]
            page.on("pageerror",lambda exc: errors.append(str(exc)))
            for case,html,target,floors in case_files:
                if not html.is_file():
                    raise RuntimeError("VIEWER_MISSING:"+str(html))
                page.goto(html.as_uri(),wait_until="load")
                page.wait_for_selector("#metrics .metric")
                page.wait_for_timeout(150)
                title=page.locator("#strategyName").inner_text()
                metrics=page.locator("#metrics").inner_text()
                if "BALANCED" not in title or str(floors)+" FLOOR" not in title:
                    raise AssertionError("DEFAULT_STRATEGY_OR_FLOOR_COUNT_BAD:"+title)
                expected=f"{target:,}"
                if expected not in metrics:
                    raise AssertionError("TARGET_GFA_NOT_DISPLAYED:"+metrics)
                view=page.locator("#model")
                initial=sha(view.screenshot())
                shot=out/(case+"_balanced.png")
                page.screenshot(path=str(shot),full_page=True)
                page.locator("#strategy").select_option("1")
                page.wait_for_timeout(120)
                sculpt_title=page.locator("#strategyName").inner_text()
                sculpt=sha(view.screenshot())
                if "SCULPTURAL" not in sculpt_title or sculpt==initial:
                    raise AssertionError("STRATEGY_CHANGED_BUT_CANVAS_UNCHANGED")
                page.screenshot(path=str(out/(case+"_sculptural.png")),full_page=True)
                shorter=max(1,floors//2)
                page.locator("#levels").evaluate(
                    "(el,count)=>{el.value=String(count);el.dispatchEvent(new Event('input',{bubbles:true}))}",
                    shorter)
                page.wait_for_timeout(120)
                short_title=page.locator("#strategyName").inner_text()
                short_metrics=page.locator("#metrics").inner_text()
                if f"{shorter} FLOOR" not in short_title or expected in short_metrics:
                    raise AssertionError("FLOOR_RANGE_DID_NOT_RECOMPUTE:"+short_title)
                after_range=sha(view.screenshot())
                if after_range==sculpt:
                    raise AssertionError("FLOOR_RANGE_CANVAS_UNCHANGED")
                page.locator("#angle").evaluate(
                    "(el)=>{el.value='85';el.dispatchEvent(new Event('input',{bubbles:true}))}"
                )
                rotated=sha(view.screenshot())
                if rotated==after_range:
                    raise AssertionError("ROTATION_DID_NOT_CHANGE_CANVAS")
                page.screenshot(path=str(out/(case+"_short_rotated.png")),full_page=True)
                checks.append({
                    "case":case,"html":str(html),"html_sha256":sha(html.read_bytes()),
                    "default_strategy":title,"default_metrics":metrics,
                    "changed_strategy":sculpt_title,"reduced_floors":short_title,
                    "reduced_metrics":short_metrics,
                    "canvas_digests":{"balanced":initial,"sculptural":sculpt,
                                     "shorter":after_range,"rotated":rotated},
                    "actual_browser_interactions":True,
                    "original_reference_visual_parity":"NOT_VERIFIED",
                    "legal_feasibility":"NOT_VERIFIED"
                })
            if errors:
                raise AssertionError("BROWSER_JAVASCRIPT_ERRORS:"+str(errors))
        finally:
            browser.close()
    receipt={
        "schema":"ARCHIGROW_MASSING_BROWSER_QA_V1",
        "executed_at":datetime.now(timezone.utc).isoformat(),
        "state":"BROWSER_RENDER_AND_INTERACTION_TESTED",
        "tests":checks,
        "js_errors":[],
        "screenshot_dir":str(out),
        "original_reel_visual_parity":"NOT_VERIFIED",
        "real_cadastral_and_regulatory_verification":"NOT_EXECUTED",
        "user_design_approval":"NOT_OBTAINED"
    }
    (out/"browser_qa_receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--case-dir",required=True,type=Path)
    ap.add_argument("--chrome",default=r"C:\Program Files\Google\Chrome\Application\chrome.exe",type=Path)
    args=ap.parse_args()
    r=run(args.case_dir,args.chrome)
    print(json.dumps({"state":r["state"],"tests":[x["case"] for x in r["tests"]],
                      "receipt":str(args.case_dir/"browser_qa"/"browser_qa_receipt.json")},
                     ensure_ascii=False))
if __name__=="__main__":
    main()
