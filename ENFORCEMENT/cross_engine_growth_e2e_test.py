#!/usr/bin/env python3
import json, os, subprocess, tempfile, unittest
from pathlib import Path

from reference_intake_executor import execute as execute_reference
from learning_evidence_gap_broker import route_gap

REPO_ROOT=Path(__file__).resolve().parents[1]
NODE_RUNTIME=REPO_ROOT/"LEARNING/runtime/learning-engine-runtime.js"

def node_call(mode,payload):
    script=r"""
const fs=require('fs');
const Runtime=require(process.argv[1]);
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const out=process.argv[2]==='outcome' ? Runtime.applyOutcome(input) : Runtime.derive(input);
process.stdout.write(JSON.stringify(out));
"""
    p=subprocess.run(["node","-e",script,str(NODE_RUNTIME),mode],input=json.dumps(payload,ensure_ascii=False),text=True,capture_output=True,check=True)
    return json.loads(p.stdout)

def write_index(path,rows):
    path.write_text(json.dumps({"sources":rows},ensure_ascii=False),encoding="utf-8")

ROUTE={"pass":True,"route_type":"REFERENCE_INTAKE_REVIEW","domain":"learning","consumer":"LEARNING_ENGINE"}

class CrossEngineE2E(unittest.TestCase):
    def test_source_to_learning_to_gap_to_mining_to_requery_to_outcome(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            index=root/"index.json"

            # 1) Existing official source: Mining acquisition result -> durable Index candidate.
            first=execute_reference({
                "source_id":"SRC-OFFICIAL-1",
                "source_url":"https://example.test/official",
                "reference_intake_execution":{
                    "acquisition_state":"ACQUIRED_AND_PRESERVED",
                    "recorded_at":"2026-09-25T15:00:00+00:00",
                    "index_result":{"verified":True,"source_id":"SRC-OFFICIAL-1","index_version":"V26+E2E","source_ref":"INDEX:SRC-OFFICIAL-1"}
                }
            },ROUTE,root)
            self.assertTrue(first["pass"])
            self.assertEqual([x["state"] for x in first["emitted"]],["REGISTERED","INDEXED","EVIDENCE_CANDIDATE"])
            self.assertFalse(first["canonical_promotion"])

            rows=[{
                "source_id":"SRC-OFFICIAL-1","title":"영어 VOCABULARY 교육과정",
                "source_family":"OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS","source_type":"OFFICIAL_CURRICULUM",
                "authority_level":"OFFICIAL","keywords":["영어","VOCABULARY","교육과정"]
            }]
            write_index(index,rows)

            learner_evidence=[{
                "event_id":"learner-1","observed_at":"2026-09-25T15:01:00.000Z",
                "member_id":"A","subject":"영어","concept_skill_target":"VOCABULARY",
                "evidence_type":"MEMORY_RETRIEVAL_EVIDENCE","source_app":"hide-seek",
                "instrument_version":"hide-v1","assisted":False,"verified_outcome":1,
                "verification":{"authority":"LEARNING_VERIFICATION_RECEIPT","receipt_id":"vr-learner-1"}
            }]

            # 2) Index metadata reaches Learning, policy is enforced, sourceRef survives.
            forward=node_call("derive",{
                "scope":{"member_id":"A","subject":"영어","concept_skill_target":"VOCABULARY"},
                "evidence":learner_evidence,
                "indexed_evidence_handoff":{
                    "query_context":{"function_id":"LE-F01","consumer_app":"READY_SET","requested_behavior":"STANDARD_ALIGNMENT"},
                    "candidates":[{
                        "source_id":"SRC-OFFICIAL-1","source_ref":"INDEX:SRC-OFFICIAL-1",
                        "source_family":"OFFICIAL_STANDARDS_ACHIEVEMENT_LEVELS","source_type":"OFFICIAL_CURRICULUM",
                        "authority_class":"OFFICIAL","provenance":["OFFICIAL_STANDARD_REF"],
                        "detail_anchor":"DETAIL:SRC-OFFICIAL-1#standard"
                    }]
                }
            })
            self.assertTrue(forward["ok"])
            self.assertIn("INDEX:SRC-OFFICIAL-1",forward["trace"]["source_refs"])
            self.assertEqual(forward["evidence_policy"]["results"][0]["decision"],"ALLOW")
            # Sparse learner performance evidence must route to specialist, never web Mining.
            self.assertEqual(forward["evidence_gap"]["resolution_path"],"SPECIALIST_EVIDENCE_ACQUISITION")
            learner_gap_route=route_gap(forward["evidence_gap"],index_path=index)
            self.assertEqual(learner_gap_route["decision"],"SPECIALIST_EVIDENCE_REQUEST")
            self.assertIsNone(learner_gap_route["mining_request"])

            # 3) Learning needs a different external reference family not present in Index.
            missing_reference=node_call("derive",{
                "scope":{"member_id":"A","subject":"영어","concept_skill_target":"VOCABULARY"},
                "evidence":learner_evidence,
                "reference_evidence_requirement":{
                    "function_id":"LE-F06","consumer_app":"SNAP_POP","requested_behavior":"WRITING_PROCESS_SCAFFOLD",
                    "priority":"MEDIUM","acceptable_source_families":["STRUCTURED_WRITING_CORPUS"],
                    "acceptable_authority_classes":["OFFICIAL"],"required_provenance":["WRITING_CORPUS_SOURCE_REF"],
                    "query_terms":["영어","writing","rubric","process"]
                }
            })
            self.assertTrue(missing_reference["ok"])
            gap=missing_reference["evidence_gap"]
            self.assertEqual(gap["gap_type"],"REFERENCE_EVIDENCE_REQUIRED")
            reverse=route_gap(gap,index_path=index,min_results=1)
            self.assertEqual(reverse["decision"],"MINING_REQUEST")
            self.assertTrue(reverse["mining_request"]["index_check"]["performed"])
            self.assertEqual(reverse["mining_request"]["index_check"]["eligible_result_count"],0)

            # 4) Mining acquisition result returns; source is preserved and indexed, never auto-promoted.
            second=execute_reference({
                "source_id":"SRC-WRITING-1",
                "source_url":"https://example.test/writing",
                "reference_intake_execution":{
                    "acquisition_state":"ACQUIRED_AND_PRESERVED",
                    "recorded_at":"2026-09-25T15:02:00+00:00",
                    "index_result":{"verified":True,"source_id":"SRC-WRITING-1","index_version":"V26+E2E2","source_ref":"INDEX:SRC-WRITING-1"}
                }
            },ROUTE,root)
            self.assertTrue(second["pass"]); self.assertFalse(second["canonical_promotion"])
            rows.append({
                "source_id":"SRC-WRITING-1","title":"영어 writing rubric process",
                "source_family":"STRUCTURED_WRITING_CORPUS","source_type":"OFFICIAL_WRITING_REFERENCE",
                "authority_level":"OFFICIAL","keywords":["영어","writing","rubric","process"]
            })
            write_index(index,rows)
            reverse2=route_gap(gap,index_path=index,min_results=1)
            self.assertEqual(reverse2["decision"],"INDEX_REQUERY")
            self.assertTrue(reverse2["index_sufficient"])

            # 5) Requery binds new source to Learning and CONDITIONAL policy now passes.
            requery=node_call("derive",{
                "scope":{"member_id":"A","subject":"영어","concept_skill_target":"VOCABULARY"},
                "evidence":learner_evidence,
                "indexed_evidence_handoff":{
                    "query_context":{"function_id":"LE-F06","consumer_app":"SNAP_POP","requested_behavior":"WRITING_PROCESS_SCAFFOLD"},
                    "candidates":[{
                        "source_id":"SRC-WRITING-1","source_ref":"INDEX:SRC-WRITING-1",
                        "source_family":"STRUCTURED_WRITING_CORPUS","source_type":"OFFICIAL_WRITING_REFERENCE",
                        "authority_class":"OFFICIAL","provenance":["WRITING_CORPUS_SOURCE_REF"],
                        "detail_anchor":"DETAIL:SRC-WRITING-1#rubric"
                    }]
                }
            })
            self.assertTrue(requery["ok"])
            self.assertEqual(requery["evidence_policy"]["results"][0]["decision"],"ALLOW_CONDITIONAL")
            self.assertIn("INDEX:SRC-WRITING-1",requery["trace"]["source_refs"])

            # 6) Verified outcome feeds Learning strategy, but cannot auto-promote Mining or Index policy.
            outcome=node_call("outcome",{
                "runtime_result":missing_reference,
                "outcome":{
                    "verified_outcome":0,
                    "verification":{"authority":"LEARNING_VERIFICATION_RECEIPT","receipt_id":"vr-outcome-e2e"},
                    "assistance":"ASSISTED","assisted":True,"attempt_count":2,
                    "source_app":"snap-pop","learning_target_id":"writing:1"
                },
                "index_gap_route":reverse
            })
            self.assertTrue(outcome["ok"])
            candidate=outcome["outcome_feedback"]["mining_strategy_feedback_candidate"]
            self.assertIsNotNone(candidate)
            self.assertFalse(candidate["promotion_authorized"])
            self.assertFalse(candidate["acquisition_strategy_change_authorized"])
            self.assertFalse(candidate["canonical_classification_change_authorized"])

            # 7) Ledger is append-only and both sources remain preserved.
            ledger=json.loads((root/"CURRENT/DATA/REFERENCE_INTAKE_DISPOSITION_LEDGER.json").read_text(encoding="utf-8"))
            self.assertTrue(ledger["append_only"])
            source_keys={x["source_key"] for x in ledger["entries"]}
            self.assertEqual(source_keys,{"SRC-OFFICIAL-1","SRC-WRITING-1"})
            self.assertNotIn("PROMOTED",[x["state"] for x in ledger["entries"]])

if __name__=="__main__": unittest.main()
