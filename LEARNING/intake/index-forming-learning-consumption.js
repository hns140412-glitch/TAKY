'use strict';
const Index=require('./indexed-evidence-handoff');
const Forming=require('./forming-bridge');
function prepare(input, verifier, options){
 const indexed=Index.prepare(input,verifier);
 if(!indexed.ok)return {ok:false,stage:'INDEXING',issues:indexed.issues};
 const formed=Forming.form(indexed,options);
 if(!formed.ok)return {ok:false,stage:'FORMING',issues:formed.issues};
 return {ok:true,stage:'FORMING_DRAFT',indexed,formed,projection_eligible:false};
}
module.exports={prepare};
