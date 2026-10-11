#!/usr/bin/env python3
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"CURRENT"/"TAKY"/"TAKY_GROW_CURRENT_INDEX_2026-10-04_R2.json"
REGISTRY=ROOT/"DOMAIN"/"GROW_DOMAIN_REGISTRY.json"

def index_revision(path:Path):
    m=re.fullmatch(r"TAKY_GROW_CURRENT_INDEX_(\d{4}-\d{2}-\d{2})(?:_R(\d+))?\.json",path.name)
    if not m:
        return ("0000-00-00",-1)
    return (m.group(1),int(m.group(2) or 1))

class GrowCurrentIndexTest(unittest.TestCase):
    def setUp(self):
        self.d=json.loads(INDEX.read_text(encoding="utf-8"))

    def test_no_active_open(self):
        self.assertEqual(self.d["active_open"],[])

    def test_authority_targets_exist(self):
        for rel in self.d["current_by_scope"].values():
            self.assertTrue((ROOT/rel).exists(),rel)

    def test_superseded_surfaces_exist_and_cover_stale_open_keys(self):
        superseded=set(self.d["superseded_open_surfaces"])
        current_paths=set(self.d["current_by_scope"].values())
        current_domain_open=set(self.d.get("current_domain_open_surfaces",[]))
        for surface in current_domain_open:
            rel,key=surface.split("#",1)
            self.assertIn(rel,current_paths,f"domain OPEN surface is not current: {surface}")
            data=json.loads((ROOT/rel).read_text(encoding="utf-8"))
            self.assertIn(key,data,f"domain OPEN key missing: {surface}")
        for surface in superseded:
            rel,key=surface.split("#",1)
            p=ROOT/rel
            self.assertTrue(p.exists(),surface)
            data=json.loads(p.read_text(encoding="utf-8"))
            self.assertIn(key,data,surface)
            status_key=f"{key}_status"
            self.assertIn(status_key,data,f"missing superseded marker: {surface}")
            self.assertIn("TAKY_GROW_CURRENT_INDEX_2026-10-04_R2.json",str(data[status_key]))
        for p in (ROOT/"CURRENT"/"TAKY").glob("TAKY_GROW*.json"):
            data=json.loads(p.read_text(encoding="utf-8"))
            rel=p.relative_to(ROOT).as_posix()
            for key in ("open","next","next_gate","remaining"):
                if key not in data:
                    continue
                surface=f"{rel}#{key}"
                if rel in current_paths and key=="next":
                    continue
                if surface in current_domain_open:
                    continue
                self.assertIn(surface,superseded,f"unsuperseded stale surface: {surface}")

    def test_prior_index_and_current_best_are_explicitly_superseded(self):
        prior_index=ROOT/"CURRENT"/"TAKY"/"TAKY_GROW_CURRENT_INDEX_2026-10-04.json"
        prior_best=ROOT/"CURRENT"/"TAKY"/"TAKY_GROW_CURRENT_BEST_LOCALIZED_FAILURE_BOUNDED_RECOVERY_2026-10-04.json"
        i=json.loads(prior_index.read_text(encoding="utf-8"))
        b=json.loads(prior_best.read_text(encoding="utf-8"))
        self.assertEqual(i["status"],"SUPERSEDED")
        self.assertEqual(i["superseded_by"],INDEX.relative_to(ROOT).as_posix())
        self.assertEqual(b["status"],"SUPERSEDED_CURRENT_BEST")
        self.assertEqual(
            b["superseded_by"],
            self.d["current_by_scope"]["current_best_strategy"]
        )

    def test_handoff_pointer_exists_and_prior_handoff_is_superseded(self):
        handoff=ROOT/self.d["handoff"]
        self.assertTrue(handoff.exists())
        prior=ROOT/"HANDOFF"/"TAKY_GROW_NEW_CHAT_START_2026-10-03_LATEST.md"
        text=prior.read_text(encoding="utf-8")
        self.assertIn("SUPERSEDED",text.splitlines()[0])
        self.assertIn("TAKY_GROW_NEW_CHAT_START_2026-10-04_LATEST.md",text)

    def test_current_best_cross_reference(self):
        best_path=ROOT/self.d["current_by_scope"]["current_best_strategy"]
        best=json.loads(best_path.read_text(encoding="utf-8"))
        self.assertEqual(best["status"],"CURRENT_BEST")
        self.assertEqual(best["strategy_id"],self.d["current_best_strategy"])
        self.assertEqual(self.d["current_best_state"],self.d["current_by_scope"]["current_best_strategy"])

    def test_registry_points_to_latest_current_index_revision(self):
        registry=json.loads(REGISTRY.read_text(encoding="utf-8"))
        pointer=registry["shared_core"]["current_index"]
        self.assertEqual(pointer,INDEX.relative_to(ROOT).as_posix())
        indexes=list((ROOT/"CURRENT"/"TAKY").glob("TAKY_GROW_CURRENT_INDEX_*.json"))
        latest=max(indexes,key=index_revision)
        self.assertEqual((ROOT/pointer).resolve(),latest.resolve())

if __name__=="__main__":
    unittest.main()
