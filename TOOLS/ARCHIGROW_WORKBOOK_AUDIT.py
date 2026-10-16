#!/usr/bin/env python3
"""ARCHIGROW read-only design-overview workbook audit (OOXML, no third-party dependency).

Binds mined lessons (Drive 10_DOMAINS/02_ARCHIGROW/02_RAW, 2026-09-30) to an executable check:
- AC-03 / P0-3: a summary PASS must not mask detail CHECK/UNKNOWN rows -> PASS_AND_OPEN_COEXIST flagged, release DRAFT_WITH_ISSUES
- GATE:NO_UNSUPPORTED_ZERO: IFERROR(...,0) and hard-coded constants in formulas are listed, never read as evidence
- AC-05: A3 page setup is metadata only (OUTPUT_PRINT_QA stays false)
- AC-04: FAR-like values are reported with sheet/cell/label, never reconciled or chosen
The workbook is never modified.
"""
import argparse,hashlib,json,re,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

TOOL_VERSION="ARCHIGROW_WORKBOOK_AUDIT/2026-10-12.1"
NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel":"http://schemas.openxmlformats.org/package/2006/relationships"}
OPEN_STATUS=re.compile(r"(?i)\bCHECK\b|확인\s*필요|보완\s*필요|중요\s*보완|미정|미확정|UNKNOWN|TBD|협의\s*(필요|중)|검토\s*필요|작성\s*중|확정\s*아님")
PASS_STATUS=re.compile(r"(?i)^\s*(PASS|OK|적합|충족)\s*$")
FAR=re.compile(r"용적률|FAR")

def col_row(ref):
    m=re.match(r"([A-Z]+)(\d+)",ref); return m.group(1),int(m.group(2))
def safe_xml(raw):
    """Untrusted workbook XML: refuse DTD/entity declarations (billion-laughs/XXE) instead of expanding them."""
    if b"<!DOCTYPE" in raw[:4096] or b"<!ENTITY" in raw: raise ValueError("XML_DTD_OR_ENTITY_REFUSED")
    return ET.fromstring(raw)
def read_workbook(path):
    z=zipfile.ZipFile(path)
    shared=[]
    if "xl/sharedStrings.xml" in z.namelist():
        for si in safe_xml(z.read("xl/sharedStrings.xml")).findall("m:si",NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
    wb=safe_xml(z.read("xl/workbook.xml"))
    rels={r.get("Id"):r.get("Target") for r in safe_xml(z.read("xl/_rels/workbook.xml.rels")).findall("rel:Relationship",NS)}
    names={d.get("name"):(d.text or "") for d in wb.iter(f"{{{NS['m']}}}definedName")}
    sheets=[]
    for i,s in enumerate(wb.find("m:sheets",NS).findall("m:sheet",NS)):
        target=rels[s.get(f"{{{NS['r']}}}id")].lstrip("/")
        xml=safe_xml(z.read(target if target.startswith("xl/") else "xl/"+target))
        cells={}
        for c in xml.iter(f"{{{NS['m']}}}c"):
            f=c.find("m:f",NS); v=c.find("m:v",NS); t=c.get("t")
            isv=c.find("m:is",NS)
            val=v.text if v is not None else ("".join(x.text or "" for x in isv.iter(f"{{{NS['m']}}}t")) if isv is not None else None)
            if t=="s" and val is not None: val=shared[int(val)]
            cells[c.get("r")]={"value":val,"formula":(f.text if f is not None else None),"type":t}
        ps=xml.find("m:pageSetup",NS); fit=xml.find("m:sheetPr/m:pageSetUpPr",NS)
        sheets.append({"name":s.get("name"),"index":i,"cells":cells,
                       "page":{"paperSize":ps.get("paperSize") if ps is not None else None,"orientation":ps.get("orientation") if ps is not None else None,
                               "fitToHeight":ps.get("fitToHeight") if ps is not None else None,"fitToPage":fit is not None and fit.get("fitToPage")=="1",
                               "print_area":any(k=="_xlnm.Print_Area" and v.startswith(("'"+s.get("name")+"'",s.get("name")+"!")) for k,v in names.items())}})
    return sheets
def row_label(cells,ref):
    col,row=col_row(ref)
    texts=[(c,x["value"]) for c,x in cells.items() if col_row(c)[1]==row and x["value"] and not re.fullmatch(r"[-\d.eE+]+",str(x["value"])) and not OPEN_STATUS.search(str(x["value"]))]
    texts.sort(key=lambda t:(len(col_row(t[0])[0]),col_row(t[0])[0]))
    return " / ".join(str(v)[:40] for _,v in texts[:3])

def audit(path,project_id="",source_role="PROVISIONAL_DERIVED"):
    path=Path(path); sheets=read_workbook(path)
    open_rows=[];pass_cells=[];defaults=[];far=[];pages=[];errors=[]
    for s in sheets:
        c=s["cells"]; spass=[];sopen=[]
        for ref,x in c.items():
            v=str(x["value"] or ""); f=x["formula"] or ""
            if x["type"]=="e" or v in ("#DIV/0!","#REF!","#VALUE!","#N/A","#NAME?","#NUM!","#NULL!"):
                errors.append({"sheet":s["name"],"cell":ref,"error":v,"formula":("="+f[:80]) if f else None,"row":row_label(c,ref)})
            if OPEN_STATUS.search(v): sopen.append({"sheet":s["name"],"cell":ref,"status":v[:60],"row":row_label(c,ref)})
            elif PASS_STATUS.match(v): spass.append({"sheet":s["name"],"cell":ref,"row":row_label(c,ref)})
            if f and (re.search(r"IFERROR\([^)]*,\s*0\s*\)",f,re.I) or re.fullmatch(r"\s*-?[\d.]+\s*",f)):
                defaults.append({"sheet":s["name"],"cell":ref,"formula":"="+f[:80],"cached":x["value"],"row":row_label(c,ref)})
            if FAR.search(v) and len(v)<40:
                col,row=col_row(ref)
                nums=[(r2,y["value"]) for r2,y in c.items() if col_row(r2)[1]==row and r2!=ref and y["value"] is not None and re.fullmatch(r"-?[\d.]+(E-?\d+)?",str(y["value"]))]
                if nums: far.append({"sheet":s["name"],"label_cell":ref,"label":v,"values":[{"cell":r2,"value":float(n)} for r2,n in sorted(nums,key=lambda t:(len(col_row(t[0])[0]),col_row(t[0])[0]))[:6]]})
        open_rows+=sopen; pass_cells+=spass
        pages.append({"sheet":s["name"],**s["page"],"a3":s["page"]["paperSize"]=="8"})
    # Same sheet holding PASS and open rows needs review (a summary PASS may hide detail CHECK); not proof of masking.
    coexist=sorted({p["sheet"] for p in pass_cells}&{o["sheet"] for o in open_rows})
    issues=[{"issue":"OPEN_STATUS_ROWS","count":len(open_rows)}] if open_rows else []
    if coexist: issues.append({"issue":"PASS_AND_OPEN_COEXIST","sheets":coexist})
    if defaults: issues.append({"issue":"ZERO_OR_CONSTANT_DEFAULT_FORMULAS","count":len(defaults)})
    if errors: issues.append({"issue":"FORMULA_ERROR_CELLS","count":len(errors)})
    a3=sum(p["a3"] for p in pages)
    return {"schema":"ARCHIGROW_WORKBOOK_AUDIT_V1","tool":TOOL_VERSION,"project_id":project_id or None,"source":str(path),"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_role":source_role,"sheet_count":len(sheets),"sheets":[s["name"] for s in sheets],
            "open_status_rows":open_rows,"pass_cells":pass_cells,"zero_or_constant_defaults":defaults,"formula_errors":errors,"far_values":far,
            "page_setup":{"a3_sheets":a3,"of":len(pages),"detail":pages},"issues":issues,
            "evidence_ladder":{"RAW_CALC_MATCH":None,"SOURCE_VERIFIED":source_role in ("SOURCE_VERIFIED","USER_CONFIRMED_LATEST"),"OUTPUT_PRINT_QA":False,"HUMAN_REVIEW":False},
            "release_status":"DRAFT_WITH_ISSUES" if issues or source_role not in ("SOURCE_VERIFIED","USER_CONFIRMED_LATEST") else "MECHANICAL_CLEAR__HUMAN_REVIEW_PENDING",
            "rule":"Read-only audit. Cached values are reported, not recalculated; FAR values are listed with location, never reconciled or chosen; A3 pageSetup is metadata, not print QA."}
def main():
    p=argparse.ArgumentParser(); p.add_argument("xlsx"); p.add_argument("--project-id",default=""); p.add_argument("--source-role",default="PROVISIONAL_DERIVED"); p.add_argument("--output")
    a=p.parse_args(); r=audit(a.xlsx,a.project_id,a.source_role); text=json.dumps(r,ensure_ascii=False,indent=2)
    if a.output: Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(text,encoding="utf-8")
    print(json.dumps({k:r[k] for k in ("sheet_count","issues","release_status")},ensure_ascii=False,indent=2))
    return 0 if r["release_status"]!="DRAFT_WITH_ISSUES" else 2
if __name__=="__main__": raise SystemExit(main())
