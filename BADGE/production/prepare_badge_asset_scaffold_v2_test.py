#!/usr/bin/env python3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from prepare_badge_asset_scaffold_v2 import ROOT,packet_map,make_manifest,make_depth_profile,write_scaffold
class ScaffoldTests(unittest.TestCase):
    def test_current_60_packets_available(self):
        self.assertEqual(60,len(packet_map()))
    def test_manifest_never_approves_runtime(self):
        p=next(iter(packet_map().values()));m=make_manifest(p)
        self.assertEqual("BADGE_DETAIL_VIEW_ONLY",m["detail_effect_scope"])
        self.assertEqual("NOT_APPROVED_PENDING_ADMISSION",m["approval_status"])
        self.assertFalse(m["runtime_binding"])
        self.assertIn("subject.png",m["required_files"])
    def test_depth_profile_is_earned_detail_only(self):
        p=next(iter(packet_map().values()));d=make_depth_profile(p)
        self.assertEqual([ "EARNED" ],d["enabled_ownership_states"])
        self.assertEqual("BADGE_DETAIL_VIEW_ONLY",d["surface"])
        self.assertEqual("STATIC_COMPOSITE",d["reduced_motion"])
        self.assertEqual(7,d["layers"]["subject"]["max_px"])
    def test_write_is_fail_closed_on_overwrite(self):
        p=next(iter(packet_map().values()))
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"BADGE/production").mkdir(parents=True)
            source=ROOT/"BADGE/production/badge-depth-profile-default-v1.json"
            (root/"BADGE/production/badge-depth-profile-default-v1.json").write_bytes(source.read_bytes())
            first=write_scaffold(p,root)
            self.assertEqual(2,len(first))
            with self.assertRaises(FileExistsError):write_scaffold(p,root)
if __name__=="__main__":unittest.main()
