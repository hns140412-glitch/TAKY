'use strict';

const assert=require('node:assert/strict');
const fsp=require('node:fs').promises;
const os=require('node:os'),path=require('node:path');
const Endpoint=require('../LEARNING/transport/family-user-data-http-endpoint.js');
const Context=require('../LEARNING/transport/member-learning-context-store.js');
const UserData=require('../LEARNING/transport/family-user-data-store.js');
const {LocalJsonStrongStore}=require('../LEARNING/transport/local-json-strong-store.js');

const parent={
  authenticated:true,principal_id:'PARENT',identity_provider:'TEST',
  families:[{family_id:'F1',self_member_id:'PARENT',authorized_member_ids:['A','B']}]
};
const childA={
  authenticated:true,principal_id:'A',identity_provider:'TEST',
  families:[{family_id:'F1',self_member_id:'A',authorized_member_ids:['A']}]
};
const token='validated-bearer-token-001';
const headers={authorization:'Bearer '+token,'content-type':'application/json'};
const post=(record,expected_etag)=>({
  method:'POST',path:'/api/family/user-data',headers,
  body:JSON.stringify({record,...(expected_etag?{expected_etag}:{})})
});
const get=(q)=>({method:'GET',path:'/api/family/user-data',headers:{authorization:'Bearer '+token},query:q});
const assignment=(member,id,status,title)=>({
  family_id:'F1',member_id:member,record_type:'ASSIGNMENT',record_id:id,
  source_app:'family-main',status,recorded_at:'2026-10-07T13:00:00.000Z',
  due_at:'2026-10-09T09:00:00.000Z',
  payload:{title,subject:'English',task_id:'TASK-'+id,note:'parent-entered private note'}
});

(async()=>{
  const dir=await fsp.mkdtemp(path.join(os.tmpdir(),'taky-user-data-'));
  try{
    const store=await new LocalJsonStrongStore(dir).init();
    const parentEp=Endpoint.create({store,verifyBearerToken:async()=>parent});
    const childEp=Endpoint.create({store,verifyBearerToken:async()=>childA});

    let out=await parentEp.handle(post(assignment('A','HW-A1','DRAFT','Vocabulary 12')));
    assert.equal(out.status,200,out.body);
    let body=JSON.parse(out.body);
    assert.equal(body.storage_confirmed,true);
    assert.equal(body.learning_context_queued,false);
    assert.equal(body.backup_status,'PENDING_VERIFIED_ARCHIVE');
    const draftEtag=body.etag;

    out=await parentEp.handle(post(assignment('A','HW-A1','CONFIRMED','Vocabulary 12')));
    assert.equal(out.status,409,'update without etag must fail');

    out=await parentEp.handle(post(assignment('A','HW-A1','CONFIRMED','Vocabulary 12'),draftEtag));
    assert.equal(out.status,200,out.body);
    body=JSON.parse(out.body);
    assert.equal(body.learning_context_queued,true);
    const confirmedEtag=body.etag;

    out=await parentEp.handle(post(assignment('B','HW-B1','CONFIRMED','Science worksheet')));
    assert.equal(out.status,200,out.body);
    assert.equal(JSON.parse(out.body).learning_context_queued,true);

    out=await childEp.handle(get({family_id:'F1',member_id:'B',record_type:'ASSIGNMENT',record_id:'HW-B1'}));
    assert.equal(out.status,403,'child A must not read child B');

    out=await childEp.handle(get({family_id:'F1',member_id:'A',record_type:'ASSIGNMENT',record_id:'HW-A1'}));
    assert.equal(out.status,200,out.body);
    const readA=JSON.parse(out.body);
    assert.equal(readA.record.member_id,'A');
    assert.equal(readA.record.status,'CONFIRMED');
    assert.equal(readA.record.payload.note,'parent-entered private note');

    out=await parentEp.handle(post({...assignment('C','HW-C1','CONFIRMED','Denied'),member_id:'C'}));
    assert.equal(out.status,403,'unauthorized member write must fail');

    const ca=await Context.read(store,'F1','A');
    const cb=await Context.read(store,'F1','B');
    assert(ca?.data&&cb?.data);
    assert.deepEqual(Object.keys(ca.data.records),['HW-A1']);
    assert.deepEqual(Object.keys(cb.data.records),['HW-B1']);
    assert.equal(ca.data.member_id,'A');
    assert.equal(cb.data.member_id,'B');
    assert.equal(JSON.stringify(ca.data).includes('Science worksheet'),false);
    assert.equal(JSON.stringify(cb.data).includes('Vocabulary 12'),false);
    assert.equal(JSON.stringify(ca.data).includes('parent-entered private note'),false);

    const aKey=UserData.keyFor({family_id:'F1',member_id:'A'},'ASSIGNMENT','HW-A1');
    const bKey=UserData.keyFor({family_id:'F1',member_id:'B'},'ASSIGNMENT','HW-B1');
    assert.notEqual(aKey,bKey);
    assert(aKey.includes('/members/A/'));
    assert(bKey.includes('/members/B/'));

    out=await parentEp.handle(post({...assignment('A','HW-A1','COMPLETED','Vocabulary 12')},confirmedEtag));
    assert.equal(out.status,200,out.body);
    assert.equal(JSON.parse(out.body).learning_context_queued,true);
    const ca2=await Context.read(store,'F1','A');
    assert.equal(ca2.data.records['HW-A1'].status,'COMPLETED');

    console.log('FAMILY_USER_DATA_LEARNING_ENGINE_E2E_PASS');
    console.log(JSON.stringify({
      parent_assignment_write:true,
      per_member_durable_isolation:true,
      unauthorized_cross_member_denied:true,
      optimistic_concurrency:true,
      confirmed_assignment_learning_queue:true,
      private_payload_not_copied_to_context:true,
      backup_status:'PENDING_VERIFIED_ARCHIVE'
    }));
  }finally{await fsp.rm(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exit(1)});
