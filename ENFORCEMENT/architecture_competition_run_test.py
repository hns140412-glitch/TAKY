#!/usr/bin/env python3
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_RUN.py"
BRIEF=ROOT/"REFERENCE"/"ARCHIGROW_COMPETITION_BRIEF_SAMPLE.json"

def run(*args):
    return subprocess.run([sys.executable,str(RUN),*args,"--no-render"],capture_output=True,text=True,encoding="utf-8")

class CompetitionRun(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
        self.brief_delivery=json.loads(BRIEF.read_text(encoding="utf-8"))["delivery"]
    def tearDown(self): self.tmp.cleanup()
    def test_explicit_delivery_without_brief_is_honored(self):
        for delivery in ("A1_BOARD","PPT","PDF_DRAWING_BOOK"):
            p=run("--delivery",delivery,"--out-dir",str(self.d/delivery))
            self.assertEqual(p.returncode,0,p.stderr[-800:])
            s=json.loads((self.d/delivery/"run-summary.json").read_text(encoding="utf-8"))
            self.assertEqual((s["delivery"],s["rendered"],s["next_gate"]),(delivery,False,"RESOLVE_SOURCE_GAPS"))
    def test_brief_delivery_wins_when_not_requested(self):
        p=run("--brief-file",str(BRIEF),"--out-dir",str(self.d/"b"))
        self.assertEqual(p.returncode,0,p.stderr[-800:])
        self.assertEqual(json.loads((self.d/"b"/"run-summary.json").read_text(encoding="utf-8"))["delivery"],self.brief_delivery)
    def test_conflicting_explicit_delivery_fails_instead_of_substituting(self):
        other="PPT" if self.brief_delivery!="PPT" else "A1_BOARD"
        p=run("--brief-file",str(BRIEF),"--delivery",other,"--out-dir",str(self.d/"c"))
        self.assertNotEqual(p.returncode,0); self.assertIn("DELIVERY_CONFLICT",p.stderr)
        self.assertFalse((self.d/"c"/"run-summary.json").exists())

if __name__=="__main__": unittest.main()
