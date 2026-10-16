'use strict';
/**
 * Independently pinned Ed25519 FORMING attestation verifier.
 *
 * The trusted host supplies the pin + public key OUTSIDE the review packet.
 * The author of an approval JSON cannot appoint their own trust root.
 * This adapter is compatible with forming-bound-approval.js, which separately
 * verifies evidence SHA, artifact revision and owner/consumer exact scope.
 *
 * This file never generates signing keys or writes operational files.
 */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const HEX=/^[a-f0-9]{64}$/;
const SIG=/^[A-Za-z0-9+/]{86}==$/;
const FIELDS=Object.freeze([
  'issuer','decision','artifact_id','artifact_revision','owner_namespace',
  'target_consumer','approved_by','approved_at','evidence_ref','evidence_sha256'
]);
const clean=v=>typeof v==='string'?v.trim():'';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const canonical=x=>Array.isArray(x)?'['+x.map(canonical).join(',')+']':
 x&&typeof x==='object'?'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}':JSON.stringify(x);
function message(receipt){
 if(!receipt||typeof receipt!=='object'||Array.isArray(receipt))throw Error('APPROVAL_NOT_OBJECT');
 const signed={};
 for(const field of FIELDS){
  const v=receipt[field];
  if(typeof v!=='string'||!v.trim()||v!==v.trim()||v.length>2048)
   throw Error('APPROVAL_SIGNED_FIELD_INVALID:'+field);
  signed[field]=v;
 }
 if(signed.issuer!=='FORMING_APPROVAL_AUTHORITY'||signed.decision!=='APPROVED')
   throw Error('NOT_APPROVED_FORMING_AUTHORITY');
 if(!HEX.test(signed.evidence_sha256))throw Error('APPROVAL_EVIDENCE_SHA_INVALID');
 return Buffer.from('TAKY:FORMING:INDEPENDENT_APPROVAL:ED25519:V1\n'+canonical(signed),'utf8');
}
function pinPublicKey(publicKeyPem,expectedSpkiSha256){
 if(typeof publicKeyPem!=='string'||publicKeyPem.length>12000
   ||typeof expectedSpkiSha256!=='string'||!HEX.test(expectedSpkiSha256))
   throw Error('INDEPENDENT_AUTHORITY_TRUST_PIN_REQUIRED');
 const key=crypto.createPublicKey(publicKeyPem);
 if(key.asymmetricKeyType!=='ed25519')throw Error('ONLY_ED25519_FORMING_AUTHORITY');
 const spki=key.export({type:'spki',format:'der'});
 if(hash(spki)!==expectedSpkiSha256)throw Error('AUTHORITY_PUBLIC_KEY_PIN_MISMATCH');
 return key;
}
function checkPinnedApproval(receipt,{publicKeyPem,expectedSpkiSha256}={}){
 let key;
 try{key=pinPublicKey(publicKeyPem,expectedSpkiSha256);}
 catch{return false;}
 if(!SIG.test(clean(receipt?.approval_signature_ed25519)))return false;
 let msg;
 try{msg=message(receipt);}catch{return false;}
 const sig=Buffer.from(receipt.approval_signature_ed25519,'base64');
 return sig.length===64&&crypto.verify(null,msg,key,sig);
}
/**
 * File-local trust configuration path must be set by the host, not provided
 * from the approval JSON or a browser query. The pinned fingerprint is
 * a separate trusted setting. Caller-side fixture injection is never accepted
 * in the installed production adapter.
 */
function fromTrustedHostSettings({publicKeyPath,expectedSpkiSha256}={}){
 if(!clean(publicKeyPath)||!HEX.test(clean(expectedSpkiSha256)))
   return {configured:false,reason:'INDEPENDENT_AUTHORITY_TRUST_NOT_CONFIGURED',
     independentAuthorityCheck:()=>false};
 let key;
 try{
  const f=path.resolve(publicKeyPath);
  if(!fs.statSync(f).isFile()||fs.lstatSync(f).isSymbolicLink())
   throw Error('UNSAFE_TRUST_KEY_FILE');
  key=pinPublicKey(fs.readFileSync(f,'utf8'),expectedSpkiSha256);
 }catch{
  return {configured:false,reason:'INDEPENDENT_AUTHORITY_TRUST_INVALID',
    independentAuthorityCheck:()=>false};
 }
 return {configured:true,reason:null,
  independentAuthorityCheck:({receipt})=>{
    try{
      const signedMessage=message(receipt);
      const sig=clean(receipt?.approval_signature_ed25519);
      if(!SIG.test(sig))return false;
      const bytes=Buffer.from(sig,'base64');
      return bytes.length===64&&crypto.verify(null,signedMessage,key,bytes);
    }catch{return false;}
  }};
}
module.exports=Object.freeze({FIELDS,message,pinPublicKey,checkPinnedApproval,fromTrustedHostSettings});
