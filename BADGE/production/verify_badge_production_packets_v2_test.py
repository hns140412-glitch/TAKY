#!/usr/bin/env python3
import copy,unittest,json
from verify_badge_production_packets_v2 import ROOT,PACKETS,verify
class PacketV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=json.loads((ROOT/PACKETS).read_text(encoding="utf-8"))
    def test_current_packets(self):self.assertEqual([],verify(ROOT,self.base))
    def test_detail_depth_cannot_spread(self):
        d=copy.deepcopy(self.base);d["items"][0]["detail_effect_scope"]="ALL_SURFACES"
        self.assertTrue(any("PACKET_DEPTH_SCOPE" in x for x in verify(ROOT,d)))
    def test_packet_cannot_activate_runtime(self):
        d=copy.deepcopy(self.base);d["items"][0]["runtime_binding"]=True
        self.assertTrue(any("PACKET_FALSE_APPROVAL" in x for x in verify(ROOT,d)))
    def test_complete_layer_delivery(self):
        d=copy.deepcopy(self.base);d["items"][0]["asset_contract"].pop("subject")
        self.assertTrue(any("PACKET_DELIVERY_SET" in x for x in verify(ROOT,d)))
    def test_asset_directory_collision_fails(self):
        d=copy.deepcopy(self.base);d["items"][1]["asset_dir"]=d["items"][0]["asset_dir"]
        self.assertIn("PACKET_ASSET_DIR_COLLISION",verify(ROOT,d))
if __name__=="__main__":unittest.main()
