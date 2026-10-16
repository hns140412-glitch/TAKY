'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const projector=require('./build-mining-learning-pattern-registry');
const base=path.resolve(__dirname,'..','..');
const receipt=path.join(base,'CURRENT','DATA','LEARNING_REFERENCE_PATTERN_PROJECTION_CURRENT.json');
const refreshReceipt=path.join(base,'CURRENT','DATA','MINING_LEARNING_REFRESH_CURRENT.json');
const registry=path.join(base,'LEARNING','data','mining-learning-pattern-registry-v1.json');
const sourceLedger=path.join(base,'CURRENT','DATA','REFERENCE_INTAKE_DISPOSITION_LEDGER.json');
const files=[receipt,refreshReceipt,registry,sourceLedger];
const digest=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const baseline=files.map(p=>({path:p,hash:digest(p),mtime:fs.statSync(p).mtimeMs}));
function assertUnchanged(){
 for(const original of baseline) {
  assert.equal(digest(original.path),original.hash,'operating bytes altered: '+original.path);
  assert.equal(fs.statSync(original.path).mtimeMs,original.mtime,'operating mtime altered: '+original.path);
 }
}
// Verify public JS callers, forged candidate gate, and refresh CLI do not
// write to either operational output before authority attestation.
for(const options of [undefined,{}, {dry_run:false},{
 forming_gate:{ok:true,stage:'LEARNING_PATTERN_PROJECTION_CANDIDATE',
  write_performed:false,candidates:[{source_id:'REF-081',source_ref:'INDEX:REF-081'}]}
}]) {
 assert.throws(()=>projector.build(options),e=>
  e.code==='FORMING_APPROVAL_REQUIRED');
 assertUnchanged();
}
const preview=projector.build({dry_run:true});
assert.equal(preview.write_performed,false);
assert.equal(preview.receipt.summary.runtime_pattern_refs,2);
assertUnchanged();
const cli=spawnSync(process.execPath,
 [path.join(__dirname,'build-mining-learning-pattern-registry.js')],
 {cwd:base,encoding:'utf8',timeout:12000});
assert.equal(cli.status,2,'projector CLI must HOLD');
assert.match(cli.stderr,/FORMING_APPROVAL_REQUIRED_FOR_LEARNING_REGISTRY_WRITE/);
assertUnchanged();
const refresh=spawnSync(process.execPath,
 [path.join(__dirname,'refresh-mining-learning-projection.js')],
 {cwd:base,encoding:'utf8',timeout:20000});
assert.equal(refresh.status,2,'refresh must stop before any subsequent build steps');
assert.match(refresh.stderr,/"state": "HOLD"/);
assert.match(refresh.stderr,/"current_receipt_updated": false/);
assertUnchanged();
console.log('LEARNING_REGISTRY_PUBLICATION_GATE_PASS: missing/self-reported approval is HOLD; no registry, CURRENT, ledger or refresh receipt mutation');
