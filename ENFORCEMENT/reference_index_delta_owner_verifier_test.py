from __future__ import annotations
import hashlib,json,tempfile
from pathlib import Path
from reference_index_delta_owner_verifier import verify_delta,owner_binding

def wr(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def item(sid,url):
    return {
      "source_id":sid,"title":"x","url":url,"source_family":"F","source_type":"T","authority_level":"REFERENCE_ONLY",
      "source_review_state":"PENDING","current_relation":"REFERENCE_ONLY","version_relation":"NEW_SOURCE_OR_REFERENCE",
      "source_ref":"INDEX:"+sid,"source_actor":"actor","source_actor_class":"CLASS",
      "source_author_identity_state":"VERIFIED","source_direction":"DIR","source_direction_signals":["A"],
      "applicability_scope":["S"],"authority_ceiling":"REFERENCE_ONLY"
    }

def build(tmp,duplicate=False,tamper=False):
    root=tmp/"TAKY";vault=tmp/"TAKY-SOURCE-VAULT"
    parent=root/"C2S/NOTION_REFERENCE_INDEX_DELTA_V33_2026-10-05.json"
    wr(parent,{"schema":"PARENT","items":[item("REF-001","https://old.example")]})
    mining=vault/"reports/x.json";wr(mining,{"ok":True})
    delta=root/"C2S/NOTION_REFERENCE_INDEX_DELTA_V34_2026-10-08.json"
    wr(delta,{"parent":parent.name,"parent_sha256":sha(parent),"input_mining_receipt":"TAKY-SOURCE-VAULT/reports/x.json",
              "input_mining_sha256":("0"*64 if tamper else sha(mining)),
              "items":[item("REF-002","https://old.example" if duplicate else "https://new.example")]})
    return root,delta

def test_unique_passes_and_binds():
    with tempfile.TemporaryDirectory() as td:
        root,delta=build(Path(td))
        r=verify_delta(root,delta)
        assert r["decision"]=="INDEXED"
        b=owner_binding(r,"REF-002",{"source_ref":"INDEX:REF-002","index_version":"V34-NOTION-DELTA"})
        assert b and b["issuer"]=="INDEXING_OWNER"

def test_exact_url_duplicate_holds():
    with tempfile.TemporaryDirectory() as td:
        root,delta=build(Path(td),duplicate=True)
        r=verify_delta(root,delta)
        assert r["decision"]=="HOLD"
        assert "EXACT_PRIMARY_URL_ALREADY_INDEXED" in r["items"][0]["errors"]

def test_mining_hash_tamper_holds():
    with tempfile.TemporaryDirectory() as td:
        root,delta=build(Path(td),tamper=True)
        r=verify_delta(root,delta)
        assert r["decision"]=="HOLD"
        assert "MINING_SHA256_MISMATCH" in r["errors"]
