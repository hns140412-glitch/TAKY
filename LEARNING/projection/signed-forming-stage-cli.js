'use strict';
/**
 * Explicitly approved FORMING -> local Learning stage.
 * No CURRENT / registry / app change. Trust root MUST come from separate
 * trusted host configuration, never from the source packet or approval JSON.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const Stage=require('./approved-learning-stage');
const Signed=require('../intake/independent-signed-forming-authority');
const EVIDENCE=path.resolve(__dirname,'..','..','..','TAKY_AI_WORKBENCH',
    '01_BACKLOG_AND_ADOPTION','80_EVIDENCE');
const inside=(base,file)=>path.resolve(file).startsWith(path.resolve(base)+path.sep);
const safeRead=(file,root,maxBytes=1_000_000)=>{
  if(!file||!root||!inside(root,file))throw Error('SOURCE_PACKET_OUTSIDE_REVIEW_ROOT');
  const stat=fs.lstatSync(file);
  if(!stat.isFile()||stat.isSymbolicLink()||stat.size>maxBytes)throw Error('SOURCE_PACKET_NOT_SAFE_FILE');
  if(!inside(fs.realpathSync(root),fs.realpathSync(file)))throw Error('SOURCE_PACKET_SYMLINK_ESCAPE');
  return JSON.parse(fs.readFileSync(file,'utf8'));
};
const validHash=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
function run({sourcePacketPath,approvalRecordPath,hostEnv=process.env}={}){
 const fields=[
   'TAKY_FORMING_TRUST_PUBLIC_KEY_FILE',
   'TAKY_FORMING_TRUST_PINNED_SPKI_SHA256',
   'TAKY_FORMING_APPROVAL_ROOT',
   'TAKY_FORMING_EVIDENCE_ROOT'
 ];
 if(fields.some(k=>typeof hostEnv[k]!=='string'||!hostEnv[k].trim())
    ||!validHash(hostEnv.TAKY_FORMING_TRUST_PINNED_SPKI_SHA256)){
   return {ok:false,status:'HOLD_INDEPENDENT_APPROVAL_TRUST_NOT_CONFIGURED',
      current_changed:false,learning_consumed:false,app_released:false};
 }
 const trust=Signed.fromTrustedHostSettings({
   publicKeyPath:hostEnv.TAKY_FORMING_TRUST_PUBLIC_KEY_FILE,
   expectedSpkiSha256:hostEnv.TAKY_FORMING_TRUST_PINNED_SPKI_SHA256
 });
 if(!trust.configured){
   return {ok:false,status:'HOLD_INVALID_INDEPENDENT_APPROVAL_TRUST',
       current_changed:false,learning_consumed:false,app_released:false};
 }
 if(!sourcePacketPath||!approvalRecordPath) {
   return {ok:false,status:'HOLD_SIGNED_FORMING_SOURCE_PACKET_OR_RECORD_REQUIRED',
       current_changed:false,learning_consumed:false,app_released:false};
 }
 const prepared=safeRead(sourcePacketPath,EVIDENCE);
 const formed=prepared?.formed;
 if(prepared?.ok!==true||prepared?.stage!=='FORMING_DRAFT'
   ||!formed?.artifact_id||!validHash(formed?.artifact_revision)){
   return {ok:false,status:'HOLD_VERIFIED_FORMING_DRAFT_REQUIRED',
       current_changed:false,learning_consumed:false,app_released:false};
 }
 const stageId='signed-forming-'+crypto.createHash('sha256')
  .update(formed.artifact_id+'|'+formed.artifact_revision).digest('hex').slice(0,26);
 const authorityOptions={
   authorityRoot:hostEnv.TAKY_FORMING_APPROVAL_ROOT,
   evidenceRoot:hostEnv.TAKY_FORMING_EVIDENCE_ROOT,
   independentAuthorityCheck:trust.independentAuthorityCheck
 };
 // Every invocation, including an idempotent replay, must revalidate the
 // independent signed approval and evidence against the current trust key.
 const independent=require('../intake/forming-authority-consumer')
   .consumeFromAuthority(prepared,approvalRecordPath,authorityOptions);
 if(!independent.ok)return {ok:false,
   status:'HOLD_INDEPENDENT_SIGNED_APPROVAL_REJECTED',
   issues:independent.issues||[],current_changed:false,
   learning_consumed:false,app_released:false};
 const folder=path.join(Stage.STAGING_ROOT,stageId);
 if(fs.existsSync(folder)){
   const read=Stage.loadStaged(stageId);
   if(read.manifest.artifact_revision!==formed.artifact_revision
      ||read.manifest.artifact_id!==formed.artifact_id
      ||read.manifest.publication_authority!==false
      ||read.manifest.operational!==false)
       throw Error('EXISTING_STAGE_NOT_SAME_SIGNED_SOURCE');
   return {ok:true,status:'VERIFIED_SIGNED_STAGE_REUSED_LOCAL_ONLY',
      stage_id:stageId,stage_path:folder,
      approved_source_ids:read.manifest.source_ids,
      new_stage_created:false,current_changed:false,
      learning_consumed:false,app_released:false};
 }
 const staged=Stage.stageApproved({
   prepared,approvalRecordPath,authorityOptions,stageId});
 if(!staged.ok)return {ok:false,status:'HOLD_INDEPENDENT_SIGNED_APPROVAL_REJECTED',
   issues:staged.issues||[],current_changed:false,
   learning_consumed:false,app_released:false};
 const checked=Stage.loadStaged(stageId);
 if(checked.manifest.artifact_revision!==formed.artifact_revision)
   throw Error('SIGNATURE_SCOPED_STAGE_READBACK_MISMATCH');
 return {ok:true,status:'VERIFIED_SIGNED_STAGE_WRITTEN_LOCAL_ONLY',
   stage_id:stageId,stage_path:staged.stage_path,
   approved_source_ids:checked.manifest.source_ids,
   new_stage_created:true,current_changed:false,
   learning_consumed:false,app_released:false};
}
if(require.main===module){
 const [sourcePacketPath,approvalRecordPath]=process.argv.slice(2);
 try{
  const result=run({sourcePacketPath,approvalRecordPath});
  process.stdout.write(JSON.stringify(result)+'\n');
  if(!result.ok)process.exitCode=2;
 }catch(e){
  process.stderr.write(JSON.stringify({ok:false,status:'HOLD_SIGNED_FORMING_STAGE_ERROR',
    reason:e.message,current_changed:false,learning_consumed:false,app_released:false})+'\n');
  process.exitCode=2;
 }
}
module.exports=Object.freeze({run,EVIDENCE});
