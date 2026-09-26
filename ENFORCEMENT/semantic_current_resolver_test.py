#!/usr/bin/env python3
import copy
import json
import tempfile
import unittest
from pathlib import Path
from semantic_current_resolver import ROOT, CurrentResolutionError, resolve_owner, resolve_promoted_data

class SemanticCurrentResolverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=json.loads((ROOT/"MASTER/MASTER_FILE_REGISTRY.json").read_text(encoding="utf-8"))

    def test_real_master_and_family(self):
        for owner in ("TAKY_GRAND_MASTER","LEARNING_APP_FAMILY_MASTER","TAKY_CHANGE_HISTORY_POLICY"):
            self.assertEqual(resolve_owner(self.registry,owner)["semantic_owner"],owner)

    def test_real_promoted_data_pointer(self):
        x=resolve_promoted_data(self.registry)
        self.assertEqual(x["source_entries_total"],679)
        self.assertEqual(x["source_index_id"],"13tmAJVLn9jZRn8NUOfBtOhnEuCqCyS7ZY8iXLDKHtdc")
        self.assertEqual(x["utilization_index_id"],"1wjoNxZVhM7L_BL7VFtbAGuV-NwzrF4U3pK7y5vrRC3s")
        self.assertEqual(x["promotion_receipt_id"],"1OnnfRLofzOsQcr2snWAnzdU6ihRrYYG3eg_XFXNgg9w")

    def test_unknown_even_if_filename_looks_newer(self):
        for owner in ("LEARNING_APP_FAMILY_MASTER_REV_99","DATA_UTILIZATION_INDEX_V999",""):
            with self.assertRaisesRegex(CurrentResolutionError,"UNKNOWN_SEMANTIC_OWNER"):
                resolve_owner(self.registry,owner)

    def test_mismatched_alias_fails(self):
        r=copy.deepcopy(self.registry)
        r["logical_owner_aliases"]["LEARNING_APP_FAMILY_MASTER"]["path"]="MASTER/MASTER_LOGIC.md"
        with self.assertRaisesRegex(CurrentResolutionError,"OWNER_ALIAS_MISMATCH"):
            resolve_owner(r,"LEARNING_APP_FAMILY_MASTER")

    def test_duplicate_active_alias_fails(self):
        r=copy.deepcopy(self.registry)
        r["files"]["MASTER/MASTER_LOGIC.md"]["logical_id"]="LEARNING_APP_FAMILY_MASTER"
        with self.assertRaisesRegex(CurrentResolutionError,"AMBIGUOUS_ACTIVE_OWNER"):
            resolve_owner(r,"LEARNING_APP_FAMILY_MASTER")

    def test_legacy_cannot_become_current(self):
        r=copy.deepcopy(self.registry)
        r["logical_owner_aliases"]["LEARNING_APP_FAMILY_MASTER"]["path"]="MASTER/REMASTER_REV00_DRAFT.md"
        r["logical_owner_aliases"]["LEARNING_APP_FAMILY_MASTER"]["class"]="CANDIDATE"
        with self.assertRaisesRegex(CurrentResolutionError,"OWNER_NOT_ACTIVE"):
            resolve_owner(r,"LEARNING_APP_FAMILY_MASTER")

    def test_path_traversal_denied(self):
        r=copy.deepcopy(self.registry)
        r["logical_owner_aliases"]["TAKY_GRAND_MASTER"]["path"]="../outside"
        with self.assertRaisesRegex(CurrentResolutionError,"INVALID_OWNER_PATH"):
            resolve_owner(r,"TAKY_GRAND_MASTER")

    def test_promoted_pointer_does_not_select_newest_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"CURRENT/DATA").mkdir(parents=True)
            (root/"MASTER").mkdir()
            payload=json.loads((ROOT/"CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json").read_text(encoding="utf-8"))
            payload["authority_current"]["utilization_index"]["name"]="DATA_UTILIZATION_INDEX_V999.json"
            (root/"CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json").write_text(json.dumps(payload),encoding="utf-8")
            result=resolve_promoted_data(self.registry,root)
            self.assertEqual(result["utilization_index_id"],"1wjoNxZVhM7L_BL7VFtbAGuV-NwzrF4U3pK7y5vrRC3s")
            payload["authority_current"]["utilization_index"].pop("id")
            (root/"CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json").write_text(json.dumps(payload),encoding="utf-8")
            with self.assertRaisesRegex(CurrentResolutionError,"MISSING_OR_DUPLICATE_PROMOTION_ID"):
                resolve_promoted_data(self.registry,root)

if __name__=="__main__":
    unittest.main()
