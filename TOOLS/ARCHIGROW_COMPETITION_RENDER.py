#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

EXPECTED_PT = {
    "A1_BOARD": (594 * 72 / 25.4, 841 * 72 / 25.4),
    "A3_REPORT": (297 * 72 / 25.4, 420 * 72 / 25.4),
    "PDF_DRAWING_BOOK": (297 * 72 / 25.4, 420 * 72 / 25.4),
    "PPT": (960.0, 540.0)
}

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def find_browser():
    candidates=[
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in candidates:
        if p.exists():
            return p
    for name in ("chrome","msedge"):
        found=shutil.which(name)
        if found:
            return Path(found)
    return None

def pdf_probe(path):
    b=Path(path).read_bytes()
    boxes=re.findall(rb"/MediaBox\s*\[([^\]]+)\]",b)
    parsed=[]
    for box in boxes:
        try:
            nums=[float(x) for x in box.decode("ascii","ignore").split()]
            if len(nums)>=4:
                parsed.append((nums[2]-nums[0],nums[3]-nums[1]))
        except Exception:
            pass
    page_count=len(re.findall(rb"/Type\s*/Page\b",b))
    first=parsed[0] if parsed else None
    return {"page_count":page_count,"first_media_box_pt":first,"media_boxes_pt":parsed[:20]}

def size_match(actual,expected,tol=4.0):
    if not actual or not expected:
        return False
    return abs(actual[0]-expected[0])<=tol and abs(actual[1]-expected[1])<=tol

def render_html(build_dir,delivery):
    names={"A1_BOARD":"board.html","A3_REPORT":"report.html","PDF_DRAWING_BOOK":"drawing-book.html"}
    html_path=build_dir/names[delivery]
    if not html_path.exists():
        raise RuntimeError(f"HTML_NOT_FOUND:{html_path}")
    browser=find_browser()
    if not browser:
        raise RuntimeError("HEADLESS_BROWSER_NOT_FOUND")
    pdf_path=html_path.with_suffix(".pdf")
    profile=Path(tempfile.mkdtemp(prefix="taky-archcomp-chrome-"))
    try:
        cmd=[
            str(browser),"--headless=new","--disable-gpu","--no-sandbox",
            f"--user-data-dir={profile}",f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri()
        ]
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        if proc.returncode!=0 or not pdf_path.exists():
            raise RuntimeError("HTML_PDF_RENDER_FAILED:"+((proc.stderr or proc.stdout)[-1000:]))
    finally:
        shutil.rmtree(profile,ignore_errors=True)
    return pdf_path
def render_ppt(build_dir):
    build_ps=build_dir/"BUILD_PPTX.ps1"
    if not build_ps.exists():
        raise RuntimeError("BUILD_PPTX_SCRIPT_NOT_FOUND")
    proc=subprocess.run(
        ["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",str(build_ps)],
        capture_output=True,text=True,timeout=180
    )
    pptx=build_dir/"competition-report.pptx"
    if proc.returncode!=0 or not pptx.exists():
        raise RuntimeError("PPTX_BUILD_FAILED:"+((proc.stderr or proc.stdout)[-1000:]))

    pdf=build_dir/"competition-report.pdf"
    fd,ps_name=tempfile.mkstemp(prefix="taky-ppt-render-",suffix=".ps1")
    os.close(fd)
    ps=Path(ps_name)
    script=f"""$ErrorActionPreference='Stop'
$ppt=New-Object -ComObject PowerPoint.Application
$pres=$ppt.Presentations.Open('{str(pptx).replace("'","''")}',$true,$false,$false)
$slides=$pres.Slides.Count
$pres.SaveAs('{str(pdf).replace("'","''")}',32)
$pres.Close()
$ppt.Quit()
Write-Output ('SLIDES='+$slides)
"""
    try:
        ps.write_text(script,encoding="utf-8-sig")
        proc2=subprocess.run(
            ["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",str(ps)],
            capture_output=True,text=True,timeout=180
        )
        if proc2.returncode!=0 or not pdf.exists():
            raise RuntimeError("PPT_PDF_RENDER_FAILED:"+((proc2.stderr or proc2.stdout)[-1000:]))
    finally:
        ps.unlink(missing_ok=True)
    return pptx,pdf

def expected_page_count(manifest):
    delivery=manifest.get("delivery")
    count=len(manifest.get("items") or [])
    if delivery=="A1_BOARD":
        return 1
    if delivery=="A3_REPORT":
        return count
    if delivery=="PDF_DRAWING_BOOK":
        return count+1
    if delivery=="PPT":
        return count
    return None

def update_validation(build_dir,evidence):
    p=build_dir/"validation.json"
    data=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    data["render_evidence"]=evidence
    gaps=data.get("source_gaps",[])
    data["verified"]=False
    data["status"]="RENDERED_SOURCE_GAPS" if gaps else "RENDERED_UNREVIEWED"
    data["rule"]="Rendered/size-checked does not equal final VERIFIED; visual/source cross-check is still required."
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
    p=argparse.ArgumentParser(description="Render and mechanically validate architecture competition result-specific outputs.")
    p.add_argument("--build-dir",required=True)
    args=p.parse_args()
    build_dir=Path(args.build_dir).resolve()
    manifest=json.loads((build_dir/"build-manifest.json").read_text(encoding="utf-8"))
    delivery=manifest["delivery"]

    evidence={"delivery":delivery,"outputs":[]}
    if delivery=="PPT":
        pptx,pdf=render_ppt(build_dir)
        evidence["outputs"].append({"path":str(pptx),"bytes":pptx.stat().st_size,"sha256":sha256(pptx),"kind":"PPTX"})
    else:
        pdf=render_html(build_dir,delivery)

    probe=pdf_probe(pdf)
    expected=EXPECTED_PT.get(delivery)
    expected_pages=expected_page_count(manifest)
    matches=size_match(probe.get("first_media_box_pt"),expected)
    page_count_match=(expected_pages is None or probe["page_count"]==expected_pages)
    evidence["outputs"].append({
        "path":str(pdf),"bytes":pdf.stat().st_size,"sha256":sha256(pdf),"kind":"PDF",
        "page_count":probe["page_count"],
        "expected_page_count":expected_pages,
        "page_count_match":page_count_match,
        "first_media_box_pt":probe["first_media_box_pt"],
        "expected_media_box_pt":expected,
        "physical_size_match":matches
    })
    evidence["mechanical_render_pass"]=bool(pdf.exists() and pdf.stat().st_size>1000 and matches and page_count_match)
    update_validation(build_dir,evidence)
    print(json.dumps(evidence,ensure_ascii=False,indent=2))
    return 0 if evidence["mechanical_render_pass"] else 2

if __name__=="__main__":
    raise SystemExit(main())
