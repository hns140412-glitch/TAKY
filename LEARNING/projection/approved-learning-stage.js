'use strict';
/**
 * Local non-operational FORMING -> Learning stage. NO write to CURRENT, registry,
 * app source or service, even if a caller supplies a forged approval.
 * Authority proof is verified by existing independent FORMING owner first.
 */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {previewBoundApproved}=require('./forming-approved-input');
const REPO=path.resolve(__dirname,'..','..');
const STAGING_ROOT=path.resolve(REPO,'..','TAKY_AI_WORKBENCH',
  '01_BACKLOG_AND_ADOPTION','80_EVIDENCE','FORMING_LEARNING_STAGES');
const INPUTS={
 ledger:path.join(REPO,'CURRENT','DATA','REFERENCE_INTAKE_DISPOSITION_LEDGER.json'),
 rules:path.join(REPO,'LEARNING','data','learning-reference-pattern-projection-rules-v1.json'),
 template:path.join(REPO,'LEARNING','data','mining-learning-pattern-registry-template-v1.json'),
};
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const readDigest=p=>sha(fs.readFileSync(p));
const idValid=id=>typeof id==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_.-]{3,79}$/.test(id);
const sourceKeys=rows=>rows.map(x=>x.source_id+'|'+x.source_ref);
function assertBoundary(){
 const expected=path.resolve(REPO,'..','TAKY_AI_WORKBENCH','01_BACKLOG_AND_ADOPTION','80_EVIDENCE');
 const actual=path.dirname(STAGING_ROOT);
 if(actual!==expected)throw Error('EVIDENCE_BOUNDARY_INVALID');
 const root=fs.realpathSync(expected);
 if(!fs.statSync(root).isDirectory())throw Error('EVIDENCE_ROOT_NOT_DIRECTORY');
 const parentReal=fs.realpathSync(path.dirname(STAGING_ROOT));
 if(parentReal!==root)throw Error('STAGING_PARENT_SYMLINK_INVALID');
 return root;
}
function sourceDigests(){
 return Object.fromEntries(Object.entries(INPUTS).map(([name,file])=>[name,readDigest(file)]));
}
function requireSourceInputsUnchanged(digests){
 const fresh=sourceDigests();
 if(JSON.stringify(fresh)!==JSON.stringify(digests))throw Error('INPUT_AUTHORITY_CHANGED');
}
function stageApproved({prepared,approvalRecordPath,authorityOptions,stageId}={}){
 if(!idValid(stageId))throw Error('STAGE_ID_INVALID');
 assertBoundary();
 const baseline=sourceDigests();
 const verified=previewBoundApproved(prepared,approvalRecordPath,authorityOptions);
 if(!verified.ok)return {ok:false,stage:verified.stage,issues:verified.issues||[],
   write_performed:false,release_approved:false};
 // A proposed FORMING approval never confers software release authority.
 if(verified.authority!=='INDEPENDENT_AUTHORITY_CHECKED_LOCAL_PREVIEW_ONLY'
   ||verified.registry?.projection_scope?.operational!==false)
   throw Error('FORMING_PREVIEW_AUTHORITY_REQUIRED');
 const registry=verified.registry;
 const ids=[...new Set(verified.source_ids)];
 const keys=sourceKeys(registry.sources);
 if(!ids.length||ids.length!==registry.sources.length
   ||registry.sources.some(s=>s.projection_state!=='RUNTIME_PATTERN_CANDIDATE'
       ||!Array.isArray(s.patterns)||!s.patterns.length)
   ||keys.length!==new Set(keys).size
   ||ids.some(id=>!registry.sources.some(s=>s.source_id===id)))
   throw Error('SOURCE_LINEAGE_SCOPE_INVALID');
 requireSourceInputsUnchanged(baseline);
 const approvalRecord=fs.readFileSync(approvalRecordPath);
 const approvalSnapshot=JSON.parse(approvalRecord.toString('utf8'));
 const revision=prepared?.formed?.artifact_revision;
 const lineage=(prepared.formed.index_refs||[])
   .filter(x=>ids.includes(x.source_id))
   .map(x=>({
     source_id:x.source_id,source_ref:x.source_ref,
     detail_anchor:x.detail_anchor,
     authority_class:x.authority_class,
     index_version:x.index_version,
     review_evidence_refs:x.review_evidence_refs,
     relations_sha256:sha(Buffer.from(JSON.stringify(x.relations)))
   }));
 if(lineage.length!==ids.length||
   new Set(lineage.map(x=>x.source_id)).size!==ids.length)
   throw Error('FORMING_SEMANTIC_LINEAGE_INCOMPLETE');
 const rules=JSON.parse(fs.readFileSync(INPUTS.rules,'utf8'));
 if(!revision||prepared.formed.ruleset_revision!==rules.version)
   throw Error('FORMING_RULE_REVISION_INVALID');
 const bytes=Buffer.from(JSON.stringify(registry,null,2)+'\n');
 const manifest={
  schema:'TAKY_APPROVED_FORMING_LOCAL_STAGE_V1',
  state:'LOCAL_STAGE_ONLY_NOT_CURRENT_NOT_DEPLOYED',
  stage_id:stageId,
  artifact_id:verified.artifact_id,
  artifact_revision:revision,
  approval_record_sha256:sha(approvalRecord),
  approval_evidence_ref:verified.approval_evidence_ref,
  approval_evidence_sha256:approvalSnapshot.evidence_sha256,
  source_ids:ids,
  formed_source_lineage:lineage,
  source_ref_keys:keys,
  ruleset_revision:rules.version,
  input_sha256:baseline,
  registry_sha256:sha(bytes),
  registry_bytes:bytes.length,
  publication_authority:false,
  operational:false,
  application_consumption_verified:false,
  learner_feedback_persisted:false
 };
 if(!fs.existsSync(STAGING_ROOT))fs.mkdirSync(STAGING_ROOT,{recursive:true});
 if(fs.realpathSync(STAGING_ROOT)!==path.join(assertBoundary(),'FORMING_LEARNING_STAGES'))
   throw Error('STAGING_ROOT_SYMLINK_INVALID');
 const target=path.join(STAGING_ROOT,stageId);
 if(fs.existsSync(target))throw Error('STAGE_ALREADY_EXISTS');
 const tmp=fs.mkdtempSync(path.join(STAGING_ROOT,'.pending-'));
 let committed=false;
 try{
  fs.writeFileSync(path.join(tmp,'registry.json'),bytes,{flag:'wx'});
  fs.writeFileSync(path.join(tmp,'manifest.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
  requireSourceInputsUnchanged(baseline);
  if(fs.existsSync(target))throw Error('STAGE_ALREADY_EXISTS');
  fs.renameSync(tmp,target);
  committed=true;
 }finally{
  if(!committed)fs.rmSync(tmp,{recursive:true,force:true});
 }
 return {ok:true,stage:'FORMING_LEARNING_STAGED_LOCAL_ONLY',
   stage_id:stageId,stage_path:target,
   source_ids:ids,write_performed:true,operating_current_updated:false,
   operational:false,release_approved:false,learning_consumed:false};
}
function loadStaged(stageId){
 if(!idValid(stageId))throw Error('STAGE_ID_INVALID');
 assertBoundary();
 const root=path.join(STAGING_ROOT,stageId);
 if(!fs.existsSync(root)||fs.realpathSync(root)!==root)throw Error('STAGE_NOT_FOUND_OR_SYMLINK');
 const stat=fs.statSync(root);
 if(!stat.isDirectory())throw Error('STAGE_DIRECTORY_REQUIRED');
 const mb=fs.readFileSync(path.join(root,'manifest.json'));
 if(mb.length>200_000)throw Error('STAGE_MANIFEST_TOO_LARGE');
 const manifest=JSON.parse(mb.toString('utf8'));
 const rb=fs.readFileSync(path.join(root,'registry.json'));
 if(rb.length>2_000_000)throw Error('STAGED_REGISTRY_TOO_LARGE');
 if(manifest.schema!=='TAKY_APPROVED_FORMING_LOCAL_STAGE_V1'
   ||manifest.state!=='LOCAL_STAGE_ONLY_NOT_CURRENT_NOT_DEPLOYED'
   ||manifest.stage_id!==stageId
   ||manifest.operational!==false||manifest.publication_authority!==false
   ||!/^[a-f0-9]{64}$/.test(manifest.approval_record_sha256||'')
   ||!/^[a-f0-9]{64}$/.test(manifest.approval_evidence_sha256||'')
   ||manifest.registry_sha256!==sha(rb)||manifest.registry_bytes!==rb.length)
   throw Error('STAGED_PROVENANCE_MISMATCH');
 requireSourceInputsUnchanged(manifest.input_sha256);
 const registry=JSON.parse(rb.toString('utf8'));
 const scope=registry.projection_scope;
 if(scope?.mode!=='BOUND_FORMING_PREVIEW_ONLY'
   ||scope?.operational!==false
   ||scope.artifact_id!==manifest.artifact_id
   ||scope.artifact_revision!==manifest.artifact_revision
   ||JSON.stringify(scope.approved_source_ids)!==JSON.stringify(manifest.source_ids)
   ||JSON.stringify(sourceKeys(registry.sources||[]))!==JSON.stringify(manifest.source_ref_keys)
   ||!Array.isArray(manifest.formed_source_lineage)
   ||manifest.formed_source_lineage.length!==(registry.sources||[]).length
   ||manifest.formed_source_lineage.some((x,i)=>
      x.source_id!==registry.sources[i].source_id
      ||x.source_ref!==registry.sources[i].source_ref
      ||!x.detail_anchor||!x.authority_class
      ||!Array.isArray(x.review_evidence_refs)||!x.review_evidence_refs.length
      ||!/^[a-f0-9]{64}$/.test(x.relations_sha256||'')))
   throw Error('STAGED_SOURCE_BINDING_MISMATCH');
 return {ok:true,stage:'STAGED_LOCAL_PREVIEW_READBACK',
  registry,manifest,operational:false,learning_consumed:false};
}
module.exports=Object.freeze({STAGING_ROOT,stageApproved,loadStaged});
