'use strict';
const fs=require('node:fs');
const crypto=require('node:crypto');
const clean=x=>String(x??'').trim();
function verify(recordPath,artifactId,artifactRevision){
 if(!recordPath||!fs.existsSync(recordPath))return null;
 let r;try{r=JSON.parse(fs.readFileSync(recordPath,'utf8').replace(/^\uFEFF/,''));}catch(_){return null;}
 if(r?.issuer!=='FORMING_APPROVAL_AUTHORITY'||r?.decision!=='APPROVED'||r?.artifact_id!==artifactId||r?.artifact_revision!==artifactRevision)return null;
 if(!clean(r.evidence_ref)||!clean(r.owner_namespace)||!clean(r.target_consumer)||!clean(r.approved_by)||!clean(r.approved_at))return null;
 return {issuer:r.issuer,decision:r.decision,artifact_id:r.artifact_id,artifact_revision:r.artifact_revision,evidence_ref:r.evidence_ref,owner_namespace:r.owner_namespace,target_consumer:r.target_consumer,approved_by:r.approved_by,approved_at:r.approved_at};
}
module.exports=Object.freeze({verify});
