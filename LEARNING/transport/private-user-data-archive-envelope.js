'use strict';

const crypto=require('node:crypto');
const VERSION='TAKY_PRIVATE_USER_DATA_ARCHIVE_ENVELOPE_V1';
const ID=/^[A-Za-z0-9._:-]{1,128}$/;
const SHA=/^[a-f0-9]{64}$/;
const clean=v=>String(v??'').trim();
const digest=v=>crypto.createHash('sha256').update(v).digest('hex');
const b64=b=>Buffer.from(b).toString('base64');
const from64=s=>Buffer.from(String(s),'base64');

function scopeDigest(familyId,memberId){
  if(!clean(familyId)||!clean(memberId))return null;
  return digest(Buffer.from('family='+clean(familyId)+'\nmember='+clean(memberId),'utf8'));
}
function seal({plaintext,encryption_key,key_id,archive_id,family_id,member_id}={}){
  const key=Buffer.isBuffer(encryption_key)?encryption_key:Buffer.from(encryption_key||[]);
  if(key.length!==32)return {ok:false,reason:'AES_256_KEY_REQUIRED'};
  if(!ID.test(clean(key_id))||!ID.test(clean(archive_id)))return {ok:false,reason:'ARCHIVE_KEY_IDENTITY_INVALID'};
  const scope=scopeDigest(family_id,member_id); if(!scope)return {ok:false,reason:'OPAQUE_SCOPE_REQUIRED'};
  const plain=Buffer.isBuffer(plaintext)?plaintext:Buffer.from(typeof plaintext==='string'?plaintext:JSON.stringify(plaintext??null),'utf8');
  if(!plain.length)return {ok:false,reason:'ARCHIVE_PLAINTEXT_REQUIRED'};
  const plainSha=digest(plain);
  const iv=crypto.randomBytes(12);
  const aad=Buffer.from([VERSION,archive_id,scope,plainSha].join('|'),'utf8');
  const cipher=crypto.createCipheriv('aes-256-gcm',key,iv);
  cipher.setAAD(aad);
  const ciphertext=Buffer.concat([cipher.update(plain),cipher.final()]);
  const tag=cipher.getAuthTag();
  const envelope={
    contract:VERSION,algorithm:'AES-256-GCM',key_id:key_id,archive_id,
    scope_sha256:scope,plaintext_sha256:plainSha,
    iv_base64:b64(iv),auth_tag_base64:b64(tag),ciphertext_base64:b64(ciphertext)
  };
  const serialized=Buffer.from(JSON.stringify(envelope),'utf8');
  return {ok:true,envelope,serialized,content_sha256:digest(serialized)};
}
function open({envelope,encryption_key}={}){
  const key=Buffer.isBuffer(encryption_key)?encryption_key:Buffer.from(encryption_key||[]);
  if(key.length!==32)return {ok:false,reason:'AES_256_KEY_REQUIRED'};
  if(!envelope||envelope.contract!==VERSION||envelope.algorithm!=='AES-256-GCM'||
     !ID.test(clean(envelope.key_id))||!ID.test(clean(envelope.archive_id))||
     !SHA.test(clean(envelope.scope_sha256))||!SHA.test(clean(envelope.plaintext_sha256)))
    return {ok:false,reason:'ARCHIVE_ENVELOPE_INVALID'};
  try{
    const aad=Buffer.from([VERSION,envelope.archive_id,envelope.scope_sha256,envelope.plaintext_sha256].join('|'),'utf8');
    const decipher=crypto.createDecipheriv('aes-256-gcm',key,from64(envelope.iv_base64));
    decipher.setAAD(aad);decipher.setAuthTag(from64(envelope.auth_tag_base64));
    const plaintext=Buffer.concat([decipher.update(from64(envelope.ciphertext_base64)),decipher.final()]);
    if(digest(plaintext)!==envelope.plaintext_sha256)return {ok:false,reason:'ARCHIVE_PLAINTEXT_HASH_MISMATCH'};
    return {ok:true,plaintext};
  }catch{return {ok:false,reason:'ARCHIVE_DECRYPT_OR_AUTH_FAILED'}}
}
module.exports=Object.freeze({VERSION,scopeDigest,seal,open});
