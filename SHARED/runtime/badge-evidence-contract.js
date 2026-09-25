(function(root,factory){
  const api=factory(root);
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyBadgeEvidence=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(root){
  'use strict';
  if(typeof module==='object'&&module.exports){
    return require('./badge-explicit-evidence.js');
  }
  if(!root.TakyBadgeExplicitEvidence) throw new Error('TAKY_BADGE_EXPLICIT_EVIDENCE_CANONICAL_REQUIRED');
  return root.TakyBadgeExplicitEvidence;
});
