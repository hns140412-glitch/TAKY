/*
 * TAKY central-family-first journey browser adapter. DO NOT load in a child app
 * as a replacement sign-in flow: only an already verified TAKY_FAMILY_RUNTIME
 * may bind it. This module does not render screens or self-authorize a family.
 */
(function(root){
'use strict';
if(root.TakyFirstJourneyFamilyAdapterV1)return;
let engine=null,sessionKey='';
function authRuntime(){
 const rt=root.TAKY_FAMILY_RUNTIME;
 if(root.document?.documentElement?.dataset?.takyCentralAuth!=='BOUND'
   ||!rt||typeof rt.currentSession!=='function')throw Error('TAKY_JOURNEY_CENTRAL_AUTH_NOT_BOUND');
 return rt;
}
function clear(){engine=null;sessionKey='';}
async function connectVerifiedMember(memberId){
 const runtime=authRuntime();
 const current=await runtime.currentSession();
 const family=String(current?.family_id||'').trim();
 const member=String(memberId||'').trim();
 if(!family||!member)throw Error('TAKY_JOURNEY_MEMBER_SELECTION_REQUIRED');
 // Every transition re-checks central session via the bound provider.
 clear();
 const contract=root.TakyFirstJourneyContractV1;
 if(!contract?.build)throw Error('TAKY_JOURNEY_CONTRACT_MISSING');
 const candidate=contract.build({getVerifiedSession:()=>authRuntime().currentSession()});
 await candidate.connectFamily(member);
 engine=candidate;sessionKey=family+'|'+member;
 return state();
}
function state(){
 if(!engine)return Object.freeze({status:'NOT_BOUND',step:'FAMILY_CONNECT',homeAccess:false});
 try{authRuntime()}catch{clear();return Object.freeze({status:'AUTH_LOST',step:'FAMILY_CONNECT',homeAccess:false});}
 const x=engine.snapshot();
 return Object.freeze({status:'BOUND',step:x.step,stepIndex:x.stepIndex,complete:x.complete,
   member_id:x.verifiedMemberId,family_id:x.verifiedFamilyId,homeAccess:x.complete});
}
async function transition(method,...args){
 if(!engine)throw Error('TAKY_JOURNEY_NOT_BOUND');
 authRuntime();
 const names=['seeFirstMeet','finishFirstMeet','chooseCrew','userVisualId','packBag',
   'depart','discoverIsland','nameIsland','discoverBasecamp','nameBasecamp','arriveBasecamp'];
 if(!names.includes(method))throw Error('TAKY_JOURNEY_METHOD_NOT_ALLOWED');
 return engine[method](...args);
}
async function homeDecision(){
 if(!engine)throw Error('TAKY_JOURNEY_NOT_BOUND');
 authRuntime();
 return engine.mayEnterHome();
}
root.TakyFirstJourneyFamilyAdapterV1=Object.freeze({
 version:'2026.10.15-central-family-binding-v1',
 connectVerifiedMember,transition,homeDecision,state,clear
});
})(typeof globalThis!=='undefined'?globalThis:this);
