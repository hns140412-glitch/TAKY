(function(root,factory){
  const api=factory();
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  if(root) root.TakyExplorerCrewRelationRuntimeV1=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const TYPES=new Set(['FIRST_MEETING','SHARED_EPISODE','EXPLORATION_COMPLETE','HELP_ACCEPTED','COACHING_SHARED']);
  const STATES=new Set(['NOT_MET','KNOWN','FAMILIAR','TRUSTED']);
  function clean(events=[]){
    const seen=new Set(),out=[];
    for(const e of events){
      if(!e||e.verified!==true||!TYPES.has(e.type)||!e.event_id||!e.evidence_ref||seen.has(e.event_id))continue;
      seen.add(e.event_id);out.push(e);
    }
    return out;
  }
  function validatePolicy(p){
    return !!p&&Number.isInteger(p.familiar_min_verified_episodes)&&p.familiar_min_verified_episodes>=1&&
      Number.isInteger(p.trusted_min_verified_episodes)&&p.trusted_min_verified_episodes>p.familiar_min_verified_episodes;
  }
  function evaluate({character_id,committed_state='NOT_MET',events=[],policy}={}){
    if(!validatePolicy(policy))return {ok:false,reason:'RELATION_POLICY_REQUIRED'};
    if(!STATES.has(committed_state))return {ok:false,reason:'COMMITTED_STATE_INVALID'};
    const rows=clean(events),met=rows.some(x=>x.type==='FIRST_MEETING'),episodes=rows.filter(x=>x.type!=='FIRST_MEETING');
    let candidate='NOT_MET';
    if(met){
      if(episodes.length>=policy.trusted_min_verified_episodes)candidate='TRUSTED';
      else if(episodes.length>=policy.familiar_min_verified_episodes)candidate='FAMILIAR';
      else candidate='KNOWN';
    }
    return Object.freeze({ok:true,character_id,committed_state,candidate_state:candidate,verified_first_meeting:met,
      verified_episode_count:episodes.length,verified_event_ids:Object.freeze(rows.map(x=>x.event_id)),
      promotion_required:candidate!==committed_state,promotion_auto_commit:false,owner_commit_required:true,
      reward_delta:0,power_delta:0,ability_delta:0});
  }
  function projectStore(store,characterId,policy){
    const events=(store?.episodes||[]).filter(x=>x.character_id===characterId);
    const committed=store?.committed_relationships?.[characterId]?.state||'NOT_MET';
    return evaluate({character_id:characterId,committed_state:committed,events,policy});
  }
  return Object.freeze({version:'TAKY_EXPLORER_CREW_BROWSER_RELATION_V1',clean,evaluate,projectStore,automaticCommit:false});
});
