/*
 * TAKY FIRST JOURNEY CONTRACT V1
 * Canonical sequence derives from preserved 2026-09-25 12-scene onboarding board.
 * 2026-09-27 11-panel board combines/omits discrete discovery panels; neither
 * image is a license to invent new design, audio, assets or consent.
 * This state engine owns order ONLY. UI, account verification, persistence and
 * official companion relationship remain with their existing TAKY owners.
 * NEVER treat a stored flag or client-supplied role as authenticated authority.
 */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 root.TakyFirstJourneyContractV1=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const VERSION='2026.10.15-authority-restore-v1';
const STEPS=Object.freeze([
 'FAMILY_CONNECT','CREW_FIRST_MEET','CREW_SELECT','USER_VISUAL_ID',
 'PACK_BAG','DEPARTURE','ISLAND_FIRST_SIGHT','ISLAND_NAME',
 'BASECAMP_DISCOVERY','BASECAMP_NAME','BASECAMP_ARRIVAL','LEARNING_HOME'
]);
const CORE6=Object.freeze(['dubi','lori','ink','nova','take','zero']);
const EQUIPMENT=Object.freeze(['map','lantern','water','camera','hat','compass']);
const clean=x=>typeof x==='string'?x.trim():'';
function fail(reason){throw Object.assign(new Error('TAKY_JOURNEY_'+reason),{code:'TAKY_JOURNEY_'+reason});}
function validName(x){const a=clean(x);if(a.length<1||a.length>32||/[\u0000-\u001f<>]/u.test(a))fail('INVALID_NAME');return a;}
function distinct(ids){return Array.isArray(ids)&&ids.every(x=>typeof x==='string')&&new Set(ids).size===ids.length;}
function build({getVerifiedSession,crewRoster=CORE6,onTransition}={}){
 if(typeof getVerifiedSession!=='function')fail('SERVER_SESSION_PROVIDER_REQUIRED');
 if(!distinct(crewRoster)||crewRoster.length<6||!CORE6.every(id=>crewRoster.includes(id)))fail('INVALID_CREW_ROSTER');
 const available=new Set(crewRoster);
 let state={step:STEPS[0],stepIndex:0,verifiedFamilyId:null,verifiedMemberId:null,
   seenCrew:[],selectedCrew:[],introPreferredCrewId:null,userVisualIdState:'NOT_STARTED',
   packedItems:[],travelMode:null,islandName:null,basecampName:null,
   acceptedSceneEvents:[],complete:false};
 function publicSnapshot(){
   const s={...state,seenCrew:state.seenCrew.slice(),selectedCrew:state.selectedCrew.slice(),
     packedItems:state.packedItems.slice(),acceptedSceneEvents:state.acceptedSceneEvents.slice()};
   // No tokens, child photos, member names or raw session contents ever held here.
   return Object.freeze(s);
 }
 function requireStep(step){if(state.step!==step)fail('WRONG_STEP_'+state.step+'_EXPECTED_'+step);}
 async function session(){
   const info=await getVerifiedSession();
   const family=clean(info?.family_id),self=clean(info?.self_member_id);
   const authorized=Array.isArray(info?.authorized_member_ids)?info.authorized_member_ids.filter(Boolean):[];
   if(!family||!self||!distinct(authorized))fail('CENTRAL_FAMILY_SESSION_REQUIRED');
   const allowed=[...new Set([self,...authorized])];
   if(state.verifiedFamilyId&&state.verifiedFamilyId!==family)fail('FAMILY_CHANGED_REAUTH_REQUIRED');
   if(state.verifiedMemberId&&!allowed.includes(state.verifiedMemberId))fail('MEMBER_REVOKED');
   return {family,allowed,self};
 }
 function commit(next,record={}){
   const before=state.step,after=STEPS[next];
   if(!after||next!==state.stepIndex+1)fail('NON_SEQUENTIAL_TRANSITION');
   state={...state,...record,step:after,stepIndex:next,complete:next===11};
   if(typeof onTransition==='function')onTransition({from:before,to:after,version:VERSION});
   return publicSnapshot();
 }
 async function connectFamily(memberId){
   requireStep('FAMILY_CONNECT');
   const s=await session(),member=clean(memberId);
   if(!member||!s.allowed.includes(member))fail('MEMBER_NOT_AUTHORIZED');
   state={...state,verifiedFamilyId:s.family,verifiedMemberId:member};
   return commit(1);
 }
 async function seeFirstMeet(crewId){
   requireStep('CREW_FIRST_MEET');await session();
   if(!CORE6.includes(crewId))fail('CORE6_ONLY_IN_FIRST_MEET');
   if(!state.seenCrew.includes(crewId))state={...state,seenCrew:[...state.seenCrew,crewId]};
   return publicSnapshot();
 }
 async function finishFirstMeet(){
   requireStep('CREW_FIRST_MEET');await session();
   if(CORE6.some(id=>!state.seenCrew.includes(id)))fail('CORE6_INTRO_INCOMPLETE');
   return commit(2);
 }
 async function chooseCrew(ids,preferredId){
   requireStep('CREW_SELECT');await session();
   if(!distinct(ids)||ids.length<5||ids.length>6||!ids.every(id=>available.has(id)))fail('CREW_SELECTION_5_TO_6_REQUIRED');
   if(!ids.includes(preferredId))fail('PREFERRED_CREW_NOT_SELECTED');
   // Do not assign main_character_id, affinity or unlock state here.
   return commit(3,{selectedCrew:ids.slice(),introPreferredCrewId:preferredId});
 }
 async function userVisualId(choice){
   requireStep('USER_VISUAL_ID');await session();
   const status=choice?.state;
   if(!['DEFERRED_NO_COST','EXISTING_ID_VERIFIED','CREATED_AND_CONFIRMED'].includes(status))fail('VISUAL_ID_REVIEW_REQUIRED');
   if(status!=='DEFERRED_NO_COST'&&!clean(choice?.visualId))fail('VISUAL_ID_NOT_CONFIRMED');
   return commit(4,{userVisualIdState:status});
 }
 async function packBag(items){
   requireStep('PACK_BAG');await session();
   if(!distinct(items)||items.length===0||items.length>6||!items.every(x=>EQUIPMENT.includes(x)))fail('EQUIPMENT_NOT_SELECTED');
   return commit(5,{packedItems:items.slice()});
 }
 function sceneEvidence(kind,proof){
   // Only a UI event explicitly emitted by the rendered scene may be consumed.
   // Runtime trustworthiness still needs real browser integration + receipts.
   if(proof?.kind!==kind||!clean(proof?.sceneEventId)||clean(proof.sceneEventId).length>128)fail('SCENE_EVIDENCE_REQUIRED');
   if(state.acceptedSceneEvents.some(x=>x.id===proof.sceneEventId))fail('SCENE_EVENT_REPLAY');
   return [...state.acceptedSceneEvents,{kind,id:proof.sceneEventId}];
 }
 async function depart(route,proof){
   requireStep('DEPARTURE');await session();
   if(!['SAIL','FALL'].includes(route))fail('DEPARTURE_ROUTE_REQUIRED');
   return commit(6,{travelMode:route,acceptedSceneEvents:sceneEvidence('DEPARTURE_RENDERED',proof)});
 }
 async function discoverIsland(proof){
   requireStep('ISLAND_FIRST_SIGHT');await session();
   return commit(7,{acceptedSceneEvents:sceneEvidence('ISLAND_SIGHT_RENDERED',proof)});
 }
 async function nameIsland(name){
   requireStep('ISLAND_NAME');await session();
   return commit(8,{islandName:validName(name)});
 }
 async function discoverBasecamp(proof){
   requireStep('BASECAMP_DISCOVERY');await session();
   return commit(9,{acceptedSceneEvents:sceneEvidence('BASECAMP_DISCOVERED_RENDERED',proof)});
 }
 async function nameBasecamp(name){
   requireStep('BASECAMP_NAME');await session();
   return commit(10,{basecampName:validName(name)});
 }
 async function arriveBasecamp(proof){
   requireStep('BASECAMP_ARRIVAL');await session();
   return commit(11,{acceptedSceneEvents:sceneEvidence('BASECAMP_ARRIVED_RENDERED',proof)});
 }
 async function mayEnterHome(){
   await session();
   if(state.step!=='LEARNING_HOME'||!state.complete||!state.islandName||!state.basecampName)fail('JOURNEY_NOT_COMPLETE');
   return {ok:true,member_id:state.verifiedMemberId,family_id:state.verifiedFamilyId,
     home:'TAKY_INTEGRATED_LEARNING_HOME',firstJourneyComplete:true};
 }
 return Object.freeze({version:VERSION,STEPS,CORE6,EQUIPMENT,snapshot:publicSnapshot,
   connectFamily,seeFirstMeet,finishFirstMeet,chooseCrew,userVisualId,packBag,
   depart,discoverIsland,nameIsland,discoverBasecamp,nameBasecamp,arriveBasecamp,mayEnterHome});
}
return Object.freeze({VERSION,STEPS,CORE6,EQUIPMENT,build});
});
