#!/usr/bin/env python3
import importlib.util, json, subprocess, tempfile, unittest
from pathlib import Path

from grow_lineage_packet import validate_event
from reference_intake_executor import execute as execute_reference

ROOT=Path(__file__).resolve().parents[1]
ARCH_TOOL=ROOT/"TOOLS"/"ARCHIGROW_COMPETITION_LEARN.py"

def independent_owner(sid, proposal):
    return {"issuer":"INDEXING_OWNER","reviewed":True,"decision":"INDEXED",
            "source_id":sid,"source_ref":"INDEX:"+sid,"index_version":"TEST",
            "review_evidence_refs":["TEST_OWNER:"+sid]}

class GrowProducerLineageIntegrationTest(unittest.TestCase):
    def test_three_producers_emit_same_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)

            # Reference Intake -> LEARNING_GROW RAW/INDEX/LEARNING
            route={"pass":True,"route_type":"REFERENCE_INTAKE_REVIEW","domain":"learning","consumer":"LEARNING_ENGINE"}
            rr=execute_reference({
                "source_id":"SRC-GROW-1",
                "reference_intake_execution":{
                    "acquisition_state":"ACQUIRED_AND_PRESERVED",
                    "recorded_at":"2026-10-03T12:00:00+00:00",
                    "index_result":{"source_id":"SRC-GROW-1","source_ref":"INDEX:SRC-GROW-1","index_version":"TEST"}
                }
            },route,root,independent_index_owner_verifier=independent_owner)
            self.assertTrue(rr["pass"])
            ref_events=[json.loads(x) for x in (root/"LEARNING/evidence/grow-lineage.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([x["stage"] for x in ref_events],["RAW","INDEX","LEARNING"])

            # ArchiGrow -> ARCHI_GROW RAW/LEARNING
            spec=importlib.util.spec_from_file_location("archlearn_integration",ARCH_TOOL)
            mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            class A:
                ledger=str(root/"arch-evidence.jsonl")
                lineage_ledger=str(root/"arch-grow-lineage.jsonl")
                project_id="P1"; competition="C1"; agency="LH"; entry_id="E1"
                submission_stage="FINAL"; submission_revision="R1"; artifact_id="A1"
                artifact_type="DRAWING"; board_no="1"; page_no=None; drawing_name="section"
                mode="SECTION"; technique="clean_vector_section"; outcome="SUCCESS"; state="CASE"
                why="clear"; reviewer_signal="understood"; failure_mode=""
                artifact_ref=["artifact:A1"]; source_ref=["source:S1"]
            rec,_=mod.append_record(A())
            arch_events=[json.loads(x) for x in (root/"arch-grow-lineage.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([x["stage"] for x in arch_events],["RAW","LEARNING"])
            self.assertEqual(rec["grow_lineage_event_id"],arch_events[-1]["event_id"])

            # Learning Grow pure producer -> scoped durable entry includes OUTCOME/GROWTH packets.
            node=r"""
const Ledger=require(process.argv[1]);
const receipt={authority:'REAL_LEARNING_EVIDENCE_RECEIPT',receipt_id:'r1',evidence_digest_sha256:'d',
 raw_evidence_immutable:true,scope:{member_id:'MEMBER_PRIVATE',subject:'영어',concept_skill_target:'vocab'}};
const feedback={ok:true,learning_strategy_feedback:{authority:'LEARNING_OUTCOME_FEEDBACK_ONLY',
 verified_target:true,outcome:1,observation_only:false,suggested_adjustments:['PRESERVE_SUCCESSFUL_STRATEGY']},
 mining_strategy_feedback_candidate:null};
const r=Ledger.append(Ledger.emptyLedger(),{real_evidence_receipt:receipt,outcome_feedback:feedback,recorded_at:'2026-10-03T12:00:00.000Z'});
process.stdout.write(JSON.stringify(r.entry.grow_lineage_events));
"""
            p=subprocess.run(["node","-e",node,str(ROOT/"LEARNING/lifecycle/growth-strategy-ledger.js")],
                             text=True,capture_output=True,check=True)
            learning_events=json.loads(p.stdout)
            self.assertEqual([x["stage"] for x in learning_events],["OUTCOME","GROWTH"])
            self.assertTrue(all(x["grow_domain"]=="LEARNING_GROW" for x in learning_events))
            self.assertNotIn("MEMBER_PRIVATE",json.dumps([x.get("payload") for x in learning_events],ensure_ascii=False))

            all_events=ref_events+arch_events+learning_events
            self.assertTrue(all(not validate_event(x) for x in all_events))
            self.assertTrue(all(x["promotion_authorized"] is False for x in all_events))
            self.assertTrue(all(x["authority_transfer"] is False for x in all_events))

if __name__=="__main__":
    unittest.main()
