#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = "node"
PYTHON = "python"


def run(cmd: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=cwd, text=True, encoding="utf-8", errors="strict",
        capture_output=True, check=True,
    )


def node_json(script: str, *args: str) -> dict:
    cp = run([NODE, "-e", script, *args])
    return json.loads(cp.stdout.strip().splitlines()[-1])


PACKET_ROWS = """[
  {member_id:'MEM-A',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:3,success_count:2,failure_count:1},
  {member_id:'MEM-B',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:2,success_count:1,failure_count:1},
  {member_id:'MEM-C',subject:'영어',concept_skill_target:'vocabulary',verified_outcome_count:3,success_count:2,failure_count:1}
]"""


class GrowReviewQueueE2ETest(unittest.TestCase):
    def test_learning_aggregate_to_review_report(self):
        with tempfile.TemporaryDirectory(prefix="taky-grow-review-e2e-") as td:
            store_root = str(Path(td) / "store")
            js = f"""
const {{LocalJsonStrongStore}}=require('./LEARNING/transport/local-json-strong-store.js');
const Adapter=require('./LEARNING/transport/durable-learning-system-growth-store-adapter.js');
const ReviewQueue=require('./LEARNING/transport/grow-review-queue-adapter.js');
(async()=>{{
  const store=await new LocalJsonStrongStore(process.argv[1]).init();
  const packet={{family_id:'FAMILY-E2E-PRIVATE',rows:{PACKET_ROWS}}};
  const first=await Adapter.appendAggregate(store,packet,{{min_members:3,min_verified_outcomes:6}});
  const second=await Adapter.appendAggregate(store,packet,{{min_members:3,min_verified_outcomes:6}});
  const family=await store.getWithMetadata(Adapter.stateKey(packet),{{type:'json',consistency:'strong'}});
  const queue=await store.getWithMetadata(ReviewQueue.KEY,{{type:'json',consistency:'strong'}});
  console.log(JSON.stringify({{
    first_ok:first.ok,
    first_idempotent:first.idempotent,
    second_ok:second.ok,
    second_idempotent:second.idempotent,
    family_state:family.data,
    queue_state:queue.data,
    queue_valid:ReviewQueue.selfValidate({{ok:true,state:queue.data}})
  }}));
}})().catch(e=>{{console.error(e);process.exit(1)}});
"""
            state = node_json(js, store_root)
            self.assertTrue(state["first_ok"])
            self.assertFalse(state["first_idempotent"])
            self.assertTrue(state["second_ok"])
            self.assertTrue(state["second_idempotent"])
            self.assertEqual(len(state["family_state"]["candidates"]), 1)
            self.assertEqual(len(state["queue_state"]["candidates"]), 1)
            self.assertTrue(state["queue_valid"]["ok"])

            serialized = json.dumps(state, ensure_ascii=False)
            for token in ("MEM-A", "MEM-B", "MEM-C", '"member_id"', '"member_ref"'):
                self.assertNotIn(token, serialized)

            report = Path(td) / "grow-review-gate-report.json"
            cp = run([
                PYTHON,
                str(ROOT / "TOOLS" / "GROW_REVIEW_RUN.py"),
                "--store-root",
                store_root,
                "--output",
                str(report),
            ])
            runner_summary = json.loads(cp.stdout.strip().splitlines()[-1])
            reviewed = json.loads(report.read_text(encoding="utf-8"))

            self.assertTrue(runner_summary["ok"])
            self.assertEqual(runner_summary["candidate_count"], 1)
            self.assertEqual(runner_summary["states"]["STRATEGY_EXPERIMENT_READY"], 1)
            self.assertFalse(runner_summary["promotion_authorized"])
            self.assertFalse(reviewed["promotion_authorized"])
            self.assertFalse(reviewed["queue_authoritative"])
            self.assertFalse(reviewed["writes_promotion_state"])
            self.assertEqual(reviewed["results"][0]["review_state"], "STRATEGY_EXPERIMENT_READY")
            self.assertFalse(reviewed["results"][0]["promotion_gate_invoked"])
            self.assertFalse(reviewed["results"][0]["promotion_authorized"])

            report_raw = report.read_text(encoding="utf-8")
            for token in ("MEM-A", "MEM-B", "MEM-C", '"member_id"', '"member_ref"'):
                self.assertNotIn(token, report_raw)

    def test_queue_failure_does_not_rollback_family_evidence(self):
        with tempfile.TemporaryDirectory(prefix="taky-grow-review-fail-") as td:
            store_root = str(Path(td) / "store")
            js = f"""
const {{LocalJsonStrongStore}}=require('./LEARNING/transport/local-json-strong-store.js');
const Adapter=require('./LEARNING/transport/durable-learning-system-growth-store-adapter.js');
const ReviewQueue=require('./LEARNING/transport/grow-review-queue-adapter.js');
class QueueFailStore {{
  constructor(inner){{this.inner=inner}}
  getWithMetadata(key,opts){{return this.inner.getWithMetadata(key,opts)}}
  setJSON(key,value,opts){{
    if(key===ReviewQueue.KEY){{
      const e=new Error('FORCED_QUEUE_WRITE_FAILURE');
      e.name='ForcedQueueWriteFailure';
      throw e;
    }}
    return this.inner.setJSON(key,value,opts);
  }}
}}
(async()=>{{
  const inner=await new LocalJsonStrongStore(process.argv[1]).init();
  const store=new QueueFailStore(inner);
  const packet={{family_id:'FAMILY-E2E-PRIVATE',rows:{PACKET_ROWS}}};
  const result=await Adapter.appendAggregate(store,packet,{{min_members:3,min_verified_outcomes:6}});
  const family=await inner.getWithMetadata(Adapter.stateKey(packet),{{type:'json',consistency:'strong'}});
  const queue=await inner.getWithMetadata(ReviewQueue.KEY,{{type:'json',consistency:'strong'}});
  console.log(JSON.stringify({{
    ok:result.ok,
    queue_attempted:result.review_queue?.attempted,
    queue_ok:result.review_queue?.ok,
    queue_non_blocking:result.review_queue?.non_blocking,
    family_candidate_count:family?.data?.candidates?.length||0,
    family_promotion_authorized:family?.data?.promotion_authorized,
    queue_exists:!!queue
  }}));
}})().catch(e=>{{console.error(e);process.exit(1)}});
"""
            state = node_json(js, store_root)
            self.assertTrue(state["ok"])
            self.assertTrue(state["queue_attempted"])
            self.assertFalse(state["queue_ok"])
            self.assertTrue(state["queue_non_blocking"])
            self.assertEqual(state["family_candidate_count"], 1)
            self.assertFalse(state["family_promotion_authorized"])
            self.assertFalse(state["queue_exists"])


if __name__ == "__main__":
    unittest.main()
