#!/usr/bin/env python3
"""Read-only design-overview workbook audit (Excel side of route F) on a synthetic OOXML workbook."""
import importlib.util, json, tempfile, unittest, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
A=load(ROOT/"TOOLS"/"ARCHIGROW_WORKBOOK_AUDIT.py","audit")
P=load(ROOT/"TOOLS"/"ARCHIGROW_PIPELINE_RUN.py","pipeline")
M='xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'

def xlsx(path,rows,doctype=False,a3=True):
    shared=[]; cells=[]
    for ref,val,formula in rows:
        f=f"<f>{formula}</f>" if formula else ""
        if isinstance(val,str):
            shared.append(val); cells.append(f'<c r="{ref}" t="s">{f}<v>{len(shared)-1}</v></c>')
        else: cells.append(f'<c r="{ref}">{f}<v>{val}</v></c>')
    sheet=f'<worksheet {M}><sheetData><row r="1">{"".join(cells)}</row></sheetData>'+('<pageSetup paperSize="8" orientation="landscape"/>' if a3 else '')+'</worksheet>'
    sst=(('<!DOCTYPE x [<!ENTITY a "aaaa">]>') if doctype else '')+f'<sst {M}>'+"".join(f"<si><t>{s}</t></si>" for s in shared)+'</sst>'
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("xl/workbook.xml",f'<workbook {M}><sheets><sheet name="10_검산" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="x"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml",sheet); z.writestr("xl/sharedStrings.xml",sst)

class WorkbookAudit(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_open_status_zero_default_far_and_a3_metadata(self):
        p=self.d/"wb.xlsx"
        xlsx(p,[("A1","용적률",None),("B1",9.4998,None),("C1",5.9877,None),("D1","CHECK",None),("E1","PASS",None),("F1",0,"IFERROR(B1/0,0)"),("G1","중요 보완",None)])
        r=A.audit(p,"P1")
        kinds={i["issue"] for i in r["issues"]}
        self.assertEqual(kinds,{"OPEN_STATUS_ROWS","PASS_AND_OPEN_COEXIST","ZERO_OR_CONSTANT_DEFAULT_FORMULAS"})
        self.assertEqual(len(r["open_status_rows"]),2)
        self.assertEqual(r["far_values"][0]["values"][0]["value"],9.4998)
        self.assertEqual((r["page_setup"]["a3_sheets"],r["evidence_ladder"]["OUTPUT_PRINT_QA"]),(1,False))
        self.assertEqual(r["release_status"],"DRAFT_WITH_ISSUES")
    def test_clean_workbook_still_needs_verified_source(self):
        p=self.d/"wb.xlsx"; xlsx(p,[("A1","대지면적",None),("B1",1000,None)])
        self.assertEqual(A.audit(p,"P1")["release_status"],"DRAFT_WITH_ISSUES")
        self.assertEqual(A.audit(p,"P1","SOURCE_VERIFIED")["release_status"],"MECHANICAL_CLEAR__HUMAN_REVIEW_PENDING")
    def test_entity_declarations_refused(self):
        p=self.d/"bomb.xlsx"; xlsx(p,[("A1","x",None)],doctype=True)
        with self.assertRaisesRegex(ValueError,"XML_DTD_OR_ENTITY_REFUSED"): A.audit(p)
    def test_pipeline_workbook_stage_holds_and_never_approves(self):
        p=self.d/"wb.xlsx"; xlsx(p,[("A1","CHECK",None)])
        (self.d/"m.json").write_text(json.dumps({"schema":"ARCHIGROW_PIPELINE_MANIFEST_V1","project_id":"P1","inputs":{"workbook":{"xlsx":"wb.xlsx"}}}),encoding="utf-8")
        s=P.run(self.d/"m.json")
        self.assertEqual((s["stages"][0]["stage"],s["stages"][0]["status"],s["release_status"]),("WORKBOOK_AUDIT","HOLD","DRAFT_WITH_ISSUES"))

if __name__=="__main__": unittest.main()
