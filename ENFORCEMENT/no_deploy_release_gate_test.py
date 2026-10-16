"""Read-only no-deploy contract regression. No cloud calls or live publication."""
import base64
import copy
import datetime as dt
import hashlib
import json
import unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import no_deploy_release_gate as gate
from asset_distribution_manifest_validator import validate as validate_v1

ROOT=Path(__file__).resolve().parents[1]
SHA=hashlib.sha256(b"original approved asset").hexdigest()

class NoDeployTests(unittest.TestCase):
    def setUp(self):
        self.private=Ed25519PrivateKey.generate()
        self.public=self.private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        self.keys={"test-public-key":self.public}
        self.doc={
            "schema":gate.SCHEMA,"package_id":"READY_HOME_V2","package_version":"1.0.1",
            "kind":"VISUAL_ASSET","generated_at":"2026-10-13T15:00:00+09:00",
            "effective_manifest_version":2,"source_authority":gate.SOURCE,
            "distribution_authority":gate.DISTRIBUTION,
            "consumer_apps":["READY_SET"],"runtime_contract_min":1,"runtime_contract_max":2,
            "required_slots":["READY_HOME_MASTER"],"assets":[{
                "slot_id":"READY_HOME_MASTER","asset_id":"READY_HOME_MASTER_APPROVED",
                "master_ref":"gdrive:hns:source-id","master_revision":"rev3:"+SHA,
                "source_sha256":SHA,"distribution_ref":"gdrive:siezeall:content-id",
                "distribution_sha256":SHA,"mime_type":"image/png","bytes":1024,
                "release_scope":"PUBLIC_RELEASE_SAFE","consumer_apps":["READY_SET"],
                "status":"APPROVED_FOR_DISTRIBUTION"}],
            "approval":{"state":"USER_APPROVED","evidence_ref":"approval:test-only"},
            "signature":None
        }
        now=dt.datetime.now(dt.timezone.utc).isoformat()
        self.secure_acl={"folder_id":gate.resolve("siezeall","03_UPDATES")["id"],
            "readback_at":now,"audit_receipt":"fixture-only",
            "ancestors":[
                {"folder_id":gate.resolve("siezeall","20_PLATFORM")["id"],
                 "permissions":[{"type":"user","role":"owner","emailAddress":"siezeall@gmail.com"}]},
                {"folder_id":gate.resolve("siezeall","TAKY")["id"],
                 "permissions":[{"type":"user","role":"owner","emailAddress":"siezeall@gmail.com"}]}
            ],
            "permissions":[{"type":"user","role":"owner","emailAddress":"siezeall@gmail.com"},
                           {"type":"anyone","role":"reader"}]}
        self.unsafe_acl=copy.deepcopy(self.secure_acl)
        self.unsafe_acl["permissions"][1]["role"]="writer"
    def sign(self,doc=None):
        d=doc or self.doc
        d["signature"]={"alg":"Ed25519","kid":"test-public-key",
            "value":base64.b64encode(self.private.sign(gate.canonical(d))).decode("ascii")}
        return d

    def errors(self,doc=None):
        return gate.inspect_manifest(doc or self.doc,public_keys=self.keys)

    def test_valid_v2_signature_and_schema(self):
        self.sign()
        self.assertEqual([],self.errors())
    def test_single_byte_change_breaks_signature(self):
        self.sign()
        self.doc["package_version"]="1.0.2"
        self.assertIn("PUBLISHER_SIGNATURE_UNTRUSTED",self.errors())
    def test_untrusted_key_rejected(self):
        self.sign()
        self.assertIn("PUBLISHER_SIGNATURE_UNTRUSTED",
                      gate.inspect_manifest(self.doc,public_keys={}))
    def test_wrong_source_delivery_hash(self):
        self.doc["assets"][0]["distribution_sha256"]="1"*64
        self.sign()
        self.assertIn("ASSET_0_SOURCE_DISTRIBUTION_HASH_MISMATCH",self.errors())
    def test_missing_slot(self):
        self.doc["required_slots"]=["MISSING_SLOT"]
        self.sign()
        self.assertIn("REQUIRED_SLOT_MISSING",self.errors())
    def test_dangerous_mime(self):
        self.doc["assets"][0]["mime_type"]="image/svg+xml"
        self.sign()
        self.assertIn("ASSET_0_MIME_UNSAFE",self.errors())
    def test_dangerous_delivery_ref(self):
        self.doc["assets"][0]["distribution_ref"]="javascript:alert(1)"
        self.sign()
        self.assertIn("ASSET_0_DISTRIBUTION_REF_UNSAFE",self.errors())
    def test_content_only_non_binary_pack(self):
        self.doc["kind"]="LEARNING_CONTENT"
        self.doc["assets"]=[]
        self.doc["required_slots"]=[]
        self.doc["content_entries"]=[{
           "entry_id":"VOCAB_001","source_sha256":SHA,"distribution_sha256":SHA,
           "source_ref":"gdrive:hns:id","distribution_ref":"gdrive:siezeall:id",
           "mime_type":"application/json","bytes":212,"release_scope":"PUBLIC_RELEASE_SAFE"}]
        self.sign()
        self.assertEqual([],self.errors())
    def test_current_unsafe_acl_blocks_even_valid_signed_manifest(self):
        self.sign()
        result=gate.preflight(self.doc,acl=self.unsafe_acl,public_keys=self.keys,
            runtime={"verified_loader":True,"remote_auth_api":True},
            publisher_evidence={"authorized":True})
        self.assertEqual("HOLD",result["status"])
        self.assertIn("PUBLIC_OR_DOMAIN_WRITER_BLOCKED",result["errors"])
        self.assertFalse(result["remote_written"])
    def test_unknown_parent_acl_blocks(self):
        self.sign()
        self.secure_acl.pop("ancestors")
        self.assertIn("ACL_PARENT_INHERITANCE_UNVERIFIED",
                      gate.preflight(self.doc,acl=self.secure_acl,public_keys=self.keys)["errors"])
    def test_runtime_unverified_blocks(self):
        self.sign()
        result=gate.preflight(self.doc,acl=self.secure_acl,public_keys=self.keys,
                              publisher_evidence={"authorized":True})
        self.assertEqual("HOLD",result["status"])
        self.assertIn("RUNTIME_LOADER_OR_API_UNVERIFIED",result["errors"])
    def test_only_local_preflight_with_all_test_evidence(self):
        self.sign()
        result=gate.preflight(self.doc,acl=self.secure_acl,public_keys=self.keys,
            runtime={"verified_loader":True,"remote_auth_api":True},
            publisher_evidence={"authorized":True})
        self.assertEqual("LOCAL_PREFLIGHT_READY_NOT_PUBLISHED",result["status"])
        self.assertEqual(gate.resolve("siezeall","03_UPDATES")["id"],result["route"]["folder_id"])
        self.assertFalse(result["github_push"])
        self.assertFalse(result["netlify_deploy"])
    def test_v1_existing_e2e_unchanged(self):
        p=ROOT/"CURRENT"/"ASSET_DISTRIBUTION_E2E_CURRENT_2026-10-07.json"
        d=json.loads(p.read_text(encoding="utf-8-sig"))
        self.assertEqual([],validate_v1(d))
        self.assertEqual("TAKY_ASSET_DISTRIBUTION_MANIFEST_V1",d["schema"])
    def test_wrong_folder_id_denied(self):
        self.sign()
        self.secure_acl["folder_id"]="wrong-folder"
        self.assertIn("ACL_EVIDENCE_MISSING_OR_WRONG_FOLDER",
                      gate.preflight(self.doc,acl=self.secure_acl,public_keys=self.keys)["errors"])
    def test_other_group_writer_denied(self):
        self.secure_acl["permissions"].append({"type":"group","role":"writer"})
        self.assertIn("UNAPPROVED_WRITER_BLOCKED",
                      gate.inspect_acl(self.secure_acl,gate.resolve("siezeall","03_UPDATES")["id"]))
    def test_older_acl_denied(self):
        self.secure_acl["readback_at"]="2026-01-01T01:00:00+00:00"
        self.assertIn("ACL_READBACK_STALE",
                      gate.inspect_acl(self.secure_acl,gate.resolve("siezeall","03_UPDATES")["id"]))
    def test_inherited_root_public_writer_blocks(self):
        self.sign()
        self.secure_acl["ancestors"][1]["permissions"].append({"type":"anyone","role":"writer"})
        res=gate.preflight(self.doc,acl=self.secure_acl,public_keys=self.keys,
            runtime={"verified_loader":True,"remote_auth_api":True},
            publisher_evidence={"authorized":True})
        self.assertEqual("HOLD",res["status"])
        self.assertIn("INHERITED_PUBLIC_ACCESS_BLOCKED",res["errors"])
    def test_ancestor_ids_must_match_existing_drive_map(self):
        self.secure_acl["ancestors"][1]["folder_id"]="forged-root"
        self.assertIn("ACL_PARENT_INHERITANCE_UNVERIFIED",
            gate.inspect_acl(self.secure_acl,gate.resolve("siezeall","03_UPDATES")["id"]))
    def test_private_pack_cannot_use_anyone_reader(self):
        self.doc["assets"][0]["release_scope"]="FAMILY_PRIVATE_AUTHENTICATED"
        self.sign()
        res=gate.preflight(self.doc,acl=self.secure_acl,public_keys=self.keys,
            runtime={"verified_loader":True,"remote_auth_api":True},
            publisher_evidence={"authorized":True})
        self.assertEqual("HOLD",res["status"])
        self.assertIn("PRIVATE_PACKAGE_PUBLIC_READ_BLOCKED",res["errors"])


if __name__=="__main__":
    unittest.main(verbosity=2)
