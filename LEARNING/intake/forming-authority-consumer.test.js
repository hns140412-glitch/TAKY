'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {consumeFromAuthority}=require('./forming-authority-consumer');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'forming-authority-e2e-'));
try{
 const approvals=path.join(root,'approvals'),evidence=path.join(root,'evidence');fs.mkdirSync(approvals);fs.mkdirSync(evidence);
 const raw=Buffer.from('fixture evidence');fs.writeFileSync(path.join(evidence,'proof.txt'),raw);
 const {form}=require('./forming-bridge');
 const formed=form({ok:true,version:'TAKY_INDEX_TO_LEARNING_EVIDENCE_HANDOFF_V1',candidates:[{
   source_id:'S',source_ref:'INDEX:S',source_family:'REFERENCE',source_type:'DOCUMENT',
   authority_class:'REFERENCE_ONLY',detail_anchor:'RAW:line:1',relations:[],
   index_version:'INDEX_V1',review_evidence_refs:['OWNER:TEST'],provenance:['RAW:S']
 }]},{owner_namespace:'LEARNING_OS',forming_kind:'CONTENT_FORMING',
    target_consumer:'HIDE_SEEK',ruleset_revision:'R1'});
 const prep={ok:true,stage:'FORMING_DRAFT',formed};
 const receipt={issuer:'FORMING_APPROVAL_AUTHORITY',decision:'APPROVED',
   artifact_id:formed.artifact_id,artifact_revision:formed.artifact_revision,
   owner_namespace:'LEARNING_OS',target_consumer:'HIDE_SEEK',
   approved_by:'FIXTURE_ONLY',approved_at:'2026-10-12',
   evidence_ref:'proof.txt',evidence_sha256:crypto.createHash('sha256').update(raw).digest('hex')};
 const file=path.join(approvals,'forming.json');fs.writeFileSync(file,JSON.stringify(receipt));
 const opts={authorityRoot:approvals,evidenceRoot:evidence,independentAuthorityCheck:()=>true};
 assert.equal(consumeFromAuthority(prep,file,opts).ok,true);
 const tampered=structuredClone(prep);
 tampered.formed.index_refs[0].relations.push({type:'INJECTED',target:'FORGED',anchor:'RAW:line:1'});
 assert.equal(consumeFromAuthority(tampered,file,opts).ok,false);
 const injected=structuredClone(prep);
 injected.formed.index_refs.push({...injected.formed.index_refs[0],source_id:'INJECTED'});
 assert.equal(consumeFromAuthority(injected,file,opts).ok,false);
 assert.equal(consumeFromAuthority(prep,file,{...opts,independentAuthorityCheck:null}).ok,false);
 assert.equal(consumeFromAuthority(prep,file,{...opts,independentAuthorityCheck:()=>false}).ok,false);
 assert.equal(consumeFromAuthority(prep,file,{...opts,authorityRoot:evidence}).ok,false);
 fs.writeFileSync(file,JSON.stringify({...receipt,target_consumer:'READY_SET'}));
 assert.equal(consumeFromAuthority(prep,file,opts).ok,false);
 const unrelated=path.resolve('D:/Git PWA/TAKY/CURRENT/TAKY/TAKY_GROW_HUMAN_PROMOTION_APPROVAL_2026-10-04_R2.json');
 assert.equal(consumeFromAuthority(prep,unrelated,opts).ok,false);
 console.log('FORMING_AUTHORITY_CONSUMER E2E: 6/6 PASS (positive fixture only; unrelated actual approval rejected)');
}finally{fs.rmSync(root,{recursive:true,force:true});}
