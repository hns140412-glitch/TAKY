'use strict';
// Copywriting QA only. Not a child collection renderer or award/approval action.
const styles=new Set(['SITUATIONAL_TWIST','TALKING_OBJECT','PUN_WORDPLAY',
 'SELF_AWARE','CONTRAST','QUIET_PRIDE','MYSTERY_REVEAL','CALLBACK','WARM_CALLBACK']);
const clean=v=>typeof v==='string'?v.trim():'';
function validateNamingPack(pack,story){
 const issues=[],seenTitles=new Set;
 if(pack?.status!=='WOW_INSPIRED_ORIGINAL_KOREAN_COPY_PROPOSALS_NOT_ACTIVE')
   issues.push('COPY_MUST_REMAIN_PROPOSAL');
 if(pack?.preservation?.auto_award!==false||
    pack?.preservation?.canonical_names_unchanged!==true||
    pack?.preservation?.unapproved_art_remains_unbound!==true||
    pack?.preservation?.criteria_unchanged!==true)
   issues.push('CANONICAL_AND_AWARD_BOUNDARY_REQUIRED');
 const groups=[
  ['preset_copy','presets','source_draft_id','stable_name',60],
  ['discovery_copy','history_discovery_templates','template_id','suggested_title',20]
 ];
 for(const [copyKey,storyKey,idKey,nameKey,count] of groups){
  const c=pack?.[copyKey],original=story?.[storyKey];
  if(!Array.isArray(c)||c.length!==count||!Array.isArray(original)||original.length!==count){
   issues.push('COUNT_INVALID:'+copyKey);continue;
  }
  c.forEach((x,i)=>{
   if(x?.[idKey]!==original[i]?.[idKey]||
      x?.canonical_title!==original[i]?.[nameKey])
      issues.push('SOURCE_ID_OR_CANONICAL_TITLE_CHANGED:'+copyKey+':'+i);
   const label=clean(x?.display_title_proposal);
   if(!label||label.length>32||seenTitles.has(label))
     issues.push('DUPLICATE_OR_INVALID_TITLE:'+copyKey+':'+i);
   seenTitles.add(label);
   if(!clean(x?.unlock_toast_proposal)||x.unlock_toast_proposal.length>70||
      !clean(x?.flavor_text_proposal)||x.flavor_text_proposal.length>110||
      !styles.has(x?.wordplay_device))
     issues.push('COPY_MISSING_OR_TOO_LONG:'+copyKey+':'+i);
   if(x?.display_status!=='COPY_PROPOSAL_NOT_RUNTIME_APPROVED'||
      x?.unlock_condition!=='ONLY_AFTER_VERIFIED_AWARD_AND_APPROVED_ASSET'||
      x?.changes_criteria!==false||x?.changes_ownership!==false||x?.changes_rank!==false)
     issues.push('COPY_RUNTIME_OR_AWARD_AUTHORITY_LEAK:'+copyKey+':'+i);
  });
 }
 return {ok:issues.length===0,issues,preset:pack?.preset_copy?.length||0,history:pack?.discovery_copy?.length||0};
}
module.exports=Object.freeze({validateNamingPack});
