#!/usr/bin/env python3
"""Learning -> execution binding: mined ArchiGrow lessons (2026-09-30) must be executable where the ledger says BOUND."""
import importlib.util, json, re, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"REFERENCE"/"ARCHIGROW_LEARNING_BINDING_LEDGER_2026-10-12.json"
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
Q=load(ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_QUALITY.py","quality")
BUILD=load(ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_BUILD.py","build")
RT=load(ROOT/"ENFORCEMENT"/"architecture_pipeline_runtime_test.py","runtime_fixtures")

class Ledger(unittest.TestCase):
    def test_bound_entries_reference_existing_files_and_rate_is_reported(self):
        led=json.loads(LEDGER.read_text(encoding="utf-8"))
        for b in led["bindings"]:
            self.assertIn(b["status"],led["status_vocabulary"],b["id"])
            if b["status"]=="BOUND":
                self.assertTrue(b.get("evidence"),b["id"])
                for ref in b["evidence"]:
                    path=ref.split("#")[0].split(" ")[0]
                    self.assertTrue((ROOT/path).exists(),(b["id"],path))
        counts={s:sum(1 for b in led["bindings"] if b["status"]==s) for s in led["status_vocabulary"]}
        self.assertGreater(counts["UNBOUND"]+counts["PARTIAL"],counts["BOUND"])  # honesty guard: no blanket "reflected" claim

class LearnedGates(unittest.TestCase):
    def test_print_legibility_gate_catches_5pt_text(self):
        css="html,body{{margin:0;font-size:9pt;}}.meta{{font-size:.65em}}".replace("{{","{").replace("}}","}")
        self.assertAlmostEqual(Q.html_min_font_pt(css),5.85,places=2)
        with tempfile.TemporaryDirectory() as td:
            Path(td,"report.html").write_text(css,encoding="utf-8")
            min_pt,floor=Q.legibility(td,"A3_REPORT",{"type_mm":{"meta":2.2,"body":2.7}})
            self.assertLess(min_pt,floor)
    def test_builder_css_respects_registry_floor(self):
        reg=json.loads((ROOT/"DOMAIN"/"ARCHITECTURE_COMPETITION_VISUAL_QUALITY_REGISTRY.json").read_text(encoding="utf-8"))
        for delivery in ("A1_BOARD","A3_REPORT","PDF_DRAWING_BOOK"):
            css=BUILD.css_for(delivery); floor=min(v*72/25.4 for v in reg[delivery]["type_mm"].values())
            html="<style>html,body{"+re.search(r"html,body\{([^}]*)\}",css).group(1)+"}"+css+"</style>"
            self.assertGreaterEqual(Q.html_min_font_pt(html)+0.05,floor,delivery)
    def test_release_status_never_approves_and_maps_learned_gates(self):
        with tempfile.TemporaryDirectory() as td:
            man,_=RT.project(td); s=RT.P.run(man)
            self.assertEqual(s["release_status"],"MECHANICAL_CLEAR__HUMAN_REVIEW_PENDING"); self.assertFalse(s["approval_inferred"])
            self.assertTrue(s["evidence_ladder"]["GEOMETRY_AGREES"]); self.assertFalse(s["evidence_ladder"]["HUMAN_REVIEW"])
        with tempfile.TemporaryDirectory() as td:
            man,_=RT.project(td,void=True); s=RT.P.run(man)
            self.assertEqual(s["release_status"],"DRAFT_WITH_ISSUES"); self.assertIn("CROSS_DOC_VALUE_MISMATCH",s["learned_gates_triggered"])
        with tempfile.TemporaryDirectory() as td:
            man,_=RT.project(td); RT.w(Path(td)/"trace.json",{**RT.PT.full(),"project_id":"OTHER"})
            self.assertIn("SITE_ID_CONFLICT",RT.P.run(man)["learned_gates_triggered"])

if __name__=="__main__": unittest.main()
