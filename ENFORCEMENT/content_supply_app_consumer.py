"""Play Camp TypeScript candidate-intake consumer, invoked locally with no network.

This module verifies that the actual application parser accepts the production
artifact. It does NOT register content or issue learner evidence.
"""
import json
import subprocess
from pathlib import Path

NODE_INTAKE = """import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const mod=await import(process.argv[1]);
const bytes=readFileSync(process.argv[2]);
const parsed=mod.parseSupplyCandidate(JSON.parse(bytes.toString('utf8')));
const intake=mod.inspectSupplyCandidate(JSON.parse(bytes.toString('utf8')));
if(!parsed||intake.status!=='CANDIDATE_NOT_AUTHORIZED'||
   intake.canRegisterActivity!==false||intake.canEmitLearningEvidence!==false){
  console.log(JSON.stringify({status:'INVALID'}));process.exit(3);
}
console.log(JSON.stringify({
  status:'APP_CANDIDATE_PARSED',
  artifact_sha256:createHash('sha256').update(bytes).digest('hex'),
  requirement_ids:parsed.units.map(x=>x.requirement_id),
  source_ids:parsed.units.map(x=>x.source_id),
  canRegisterActivity:false,canEmitLearningEvidence:false,
  consumer_adapter:'PLAY_CAMP_TS_SUPPLY_CANDIDATE_V1'
}));"""

def consume_playcamp_candidate(path, app_root):
    app = Path(app_root).resolve()
    adapter = app / "src" / "data" / "supplyCandidate.ts"
    target = Path(path).resolve()
    if not adapter.is_file() or not target.is_file():
        return {"status": "INPUT_UNAVAILABLE"}
    try:
        result = subprocess.run(
            ["node", "--input-type=module", "-e", NODE_INTAKE,
             adapter.as_uri(), str(target)],
            cwd=app, capture_output=True, text=True, encoding="utf-8",
            timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "APP_CONSUMER_UNAVAILABLE"}
    if result.returncode != 0:
        return {"status": "APP_CANDIDATE_REJECTED"}
    try:
        receipt = json.loads(result.stdout.strip())
    except (ValueError, TypeError):
        return {"status": "APP_RECEIPT_MALFORMED"}
    if receipt.get("status") != "APP_CANDIDATE_PARSED" or receipt.get("canRegisterActivity") is not False:
        return {"status": "APP_RECEIPT_INVALID"}
    return receipt
