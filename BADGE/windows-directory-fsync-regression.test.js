'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {createLedger}=require('./badge-award-ledger-store.js');
const {createFamilyGiftJournal}=require('./family-praise-gift-journal.js');
const {createParentGiftJournal}=require('./parent-praise-gift-journal.js');

const originalFsync=fs.fsyncSync;
const platformDescriptor=Object.getOwnPropertyDescriptor(process,'platform');
const family_id='FAMILY_A', child_id='CHILD_A';
const signingKey=crypto.randomBytes(32);
const now=()=> '2026-10-03T12:00:00.000Z';

function roots(){
  return [
    fs.mkdtempSync(path.join(os.tmpdir(),'taky-ledger-fsync-')),
    fs.mkdtempSync(path.join(os.tmpdir(),'taky-family-fsync-')),
    fs.mkdtempSync(path.join(os.tmpdir(),'taky-parent-fsync-'))
  ];
}
function makeWriters([ledgerDir,familyDir,parentDir]){
  const ledger=createLedger({directory:ledgerDir,family_id,signingKey,now,
    verifyDecision:x=>({ok:true,receipt:x}),isBadgeActive:()=>true});
  const family=createFamilyGiftJournal({directory:familyDir,family_id,signingKey,now});
  const parent=createParentGiftJournal({directory:parentDir,family_id,signingKey,now});
  return {
    ledger:()=>ledger.appendApprovedDecision({family_id,child_id,badge_id:'BADGE_A',
      decision_id:'DECISION_A',decision_ref:'REF_A',decision_status:'APPROVED',
      award_kind:'INITIAL_AWARD',approved_at:'2026-10-03T11:00:00Z'}),
    family:()=>family.appendGiftRecord({contract:'TAKY_FAMILY_PRAISE_GIFT_V2',
      source:'FAMILY_PRAISE',family_id,giver_member_id:'PARENT_A',
      receiver_child_id:child_id,idempotency_key:'family-key-001',message:'',
      kind:'GEM_GIFT',gem_count:1}),
    parent:()=>parent.appendGiftRecord({contract:'TAKY_PARENT_PRAISE_GIFT_V1',
      source:'PARENT_PRAISE',family_id,giver_parent_id:'PARENT_A',
      receiver_child_id:child_id,idempotency_key:'parent-key-001',message:'',
      kind:'GEM_GIFT',gem_count:1})
  };
}
function withWin32FsyncFault(kind,fn){
  Object.defineProperty(process,'platform',{value:'win32',configurable:true});
  fs.fsyncSync=fd=>{
    const isDirectory=fs.fstatSync(fd).isDirectory();
    if((kind==='directory'&&isDirectory)||(kind==='file'&&!isDirectory)){
      const error=new Error('simulated fsync EPERM'); error.code='EPERM'; throw error;
    }
    return originalFsync(fd);
  };
  try{return fn()}finally{
    fs.fsyncSync=originalFsync;
    Object.defineProperty(process,'platform',platformDescriptor);
  }
}
for(const mode of ['directory','file']){
  const dirs=roots();
  try{
    const writers=makeWriters(dirs);
    for(const [name,write] of Object.entries(writers)){
      const result=withWin32FsyncFault(mode,write);
      if(mode==='directory')assert.equal(result.ok,true,name+' should tolerate Windows directory EPERM');
      else assert.equal(result.ok,false,name+' must reject regular-file EPERM');
    }
  }finally{for(const dir of dirs)fs.rmSync(dir,{recursive:true,force:true})}
}
console.log('WINDOWS_DIRECTORY_FSYNC_REGRESSION_PASS');
