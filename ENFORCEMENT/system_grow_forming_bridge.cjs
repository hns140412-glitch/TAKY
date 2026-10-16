'use strict';
// Technical SYSTEM_GROW adapter; deliberately does not invoke education projection.
const fs=require('node:fs');
const crypto=require('node:crypto');
const Forming=require('../LEARNING/intake/forming-bridge');
const {consumeFromAuthority}=require('../LEARNING/intake/forming-authority-consumer');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function evaluate(binding, trustedPolicy=null){
  if(binding.owner!=='SYSTEM_GROW'||binding.consumer!=='TAKY_EXECUTION_EVIDENCE')
    throw Error('TECHNICAL_OWNER_SCOPE_REQUIRED');
  const formed=Forming.form({ok:true,version:'TAKY_INDEX_TO_LEARNING_EVIDENCE_HANDOFF_V1',
    candidates:[{source_id:binding.source_id,source_ref:'INDEX:'+binding.source_id,
      source_family:'USER_PROVIDED_TREND_REVIEW',source_type:'SINGLE_DOCUMENT',
      authority_class:'EVIDENCE_CANDIDATE',detail_anchor:binding.unit_id,
      index_version:'CENTRAL_DETAIL_V1',review_evidence_refs:binding.evidence_refs,
      provenance:[binding.raw_sha256,binding.anchor_sha256],relations:[binding]}]},
    {owner_namespace:binding.owner,forming_kind:'KNOWLEDGE_FORMING',
      target_consumer:binding.consumer,ruleset_revision:'SYSTEM_GROW_TECHNIQUE_FEEDBACK_V1'});
  if(!formed.ok)throw Error(formed.issues.join(','));
  const prepared={ok:true,stage:'FORMING_DRAFT',formed};
  // Pins are supplied by the trusted host, NEVER read from RAW, feedback, or draft.
  // No default pins, environment discovery, or source-controlled approval lookup.
  let gate={ok:false,stage:'AUTHORITY',issues:['INDEPENDENT_OWNER_APPROVAL_REQUIRED']};
  if(trustedPolicy){
    const p=trustedPolicy;
    gate=consumeFromAuthority(prepared,p.recordPath,{
      authorityRoot:p.authorityRoot,evidenceRoot:p.evidenceRoot,
      independentAuthorityCheck:({receipt})=>
        /^[a-f0-9]{64}$/.test(p.recordSha256||'') &&
        sha(fs.readFileSync(p.recordPath))===p.recordSha256 &&
        receipt.approved_by===p.approvedBy &&
        receipt.owner_namespace==='SYSTEM_GROW' &&
        receipt.target_consumer==='TAKY_EXECUTION_EVIDENCE'
    });
  }
  return {prepared,gate};
}
module.exports={evaluate};
if(require.main===module){
  const request=JSON.parse(fs.readFileSync(0,'utf8'));
  process.stdout.write(JSON.stringify(evaluate(request.binding,request.trustedPolicy)));
}
