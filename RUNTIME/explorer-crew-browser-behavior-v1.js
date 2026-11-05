(function(root,factory){
  const api=factory();
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  if(root) root.TakyExplorerCrewBehaviorRuntimeV1=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const ACTIONS=Object.freeze({
    IDLE:['BODY','FACE'],READ_BOOK:['BODY','FACE','HAND','PROP'],READ_MAP:['BODY','FACE','HAND','PROP'],
    WRITE_NOTE:['BODY','FACE','HAND','PROP'],USE_RADIO:['BODY','FACE','HAND','EQUIPMENT'],
    CHEER:['BODY','FACE','ARM'],THINK:['BODY','FACE'],POINT:['BODY','FACE','ARM','HAND'],
    CHECK_COMPASS:['BODY','FACE','HAND','EQUIPMENT'],ORGANIZE_BAG:['BODY','FACE','HAND','PROP'],
    USE_MAGNIFIER:['BODY','FACE','HAND','EQUIPMENT'],REST:['BODY','FACE']
  });
  const REL=new Set(['FIRST_ENCOUNTER','KNOWN','FAMILIAR','TRUSTED']);
  const DIALOGUE=new Set(['SILENT','SHORT','HINT','COACH','CELEBRATE']);
  function action(input={}){
    if(ACTIONS[input.requested_action])return input.requested_action;
    if(input.just_completed)return 'CHEER';
    if(input.needs_hint)return 'POINT';
    const mode=String(input.mode||'').toUpperCase();
    if(mode==='TRACE'||mode==='RECALL')return 'READ_BOOK';
    if(mode==='LINK'||mode==='CORE')return 'THINK';
    if(input.radio_input_active)return 'USE_RADIO';
    return 'IDLE';
  }
  function dialogue(input={},role='MAIN',relation='KNOWN'){
    if(role==='AMBIENT')return 'SILENT';
    const intervention=!!(
      input.needs_hint||input.just_completed||input.transition||input.reflection_due||
      input.user_requested||input.blocked_help||input.explicit_intervention
    );
    if((input.silence_by_default||input.child_working_well)&&!intervention)return 'SILENT';
    if(input.just_completed)return 'CELEBRATE';
    if(input.needs_hint)return relation==='TRUSTED'?'COACH':'HINT';
    if(DIALOGUE.has(input.requested_dialogue))return input.requested_dialogue;
    return 'SHORT';
  }
  function normalizeCharacter(c={},scene={}){
    const role=c.presence_role||'AMBIENT';
    const relation=REL.has(c.relationship_state)?c.relationship_state:'KNOWN';
    const resolvedAction=action({...scene,requested_action:c.action||scene.requested_action});
    const resolvedDialogue=dialogue({...scene,requested_dialogue:c.dialogue_level},role,relation);
    return Object.freeze({...c,presence_role:role,relationship_state:relation,action:resolvedAction,
      dialogue_level:resolvedDialogue,voice_allowed:resolvedDialogue!=='SILENT',
      required_roles:Object.freeze([...(ACTIONS[resolvedAction]||ACTIONS.IDLE)])});
  }
  function normalizePlan(plan={}){
    const chars=(Array.isArray(plan.characters)?plan.characters:[]).map(c=>normalizeCharacter(c,plan.behavior_state||{}));
    const maxSpeaking=Math.max(1,Math.min(Number(plan.max_speaking||1),2));
    let speakers=0;
    const normalized=chars.map(c=>{
      if(c.dialogue_level==='SILENT')return c;
      speakers++;
      return speakers<=maxSpeaking?c:Object.freeze({...c,dialogue_level:'SILENT'});
    });
    return Object.freeze({...plan,characters:Object.freeze(normalized),
      speaking_order:Object.freeze(normalized.filter(c=>c.dialogue_level!=='SILENT').map(c=>c.character_id)),
      visible_order:Object.freeze(normalized.map(c=>c.character_id)),
      generation_allowed:false,asset_selection_allowed:false});
  }
  return Object.freeze({version:'TAKY_EXPLORER_CREW_BROWSER_BEHAVIOR_V1',ACTIONS,action,dialogue,normalizeCharacter,normalizePlan});
});
