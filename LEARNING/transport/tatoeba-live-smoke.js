'use strict';

const assert=require('assert');
const Provider=require('./tatoeba-provider.js');
const Adapter=require('../adapters/tatoeba-provider-item.js');

(async()=>{
  const query='island';
  const search=await Provider.searchSentences({
    language:'eng',
    query,
    max_word_count:12,
    limit:10,
    require_owned:true,
    exclude_unapproved:true,
    exclude_license_problem:true
  });
  assert.equal(search.ok,true,'live search failed: '+JSON.stringify(search));
  assert.ok(search.candidates.length>0,'no live candidates');

  const first=search.candidates[0];
  assert.equal(Provider.validateCandidate(first).ok,true,'mapped candidate invalid');

  const item=await Provider.fetchSentenceById(first.sentence_id);
  assert.equal(item.ok,true,'live item fetch failed: '+JSON.stringify(item));
  assert.equal(item.candidate.sentence_id,first.sentence_id);
  assert.equal(item.candidate.text,first.text);
  assert.equal(item.candidate.language,'eng');
  assert.ok(['CC-BY-2.0-FR','CC0'].includes(item.candidate.license));
  assert.ok(item.candidate.license_provenance.endsWith('/v1/sentences/'+item.candidate.sentence_id));
  if(item.candidate.license==='CC-BY-2.0-FR')assert.ok(item.candidate.owner_or_author);

  const adapterResult=Adapter.normalizeProviderItem(item.candidate,{
    requested_language:'eng',
    target_learning_id:'live-smoke:island',
    target_form:'island',
    context_or_sense_ref:'UNVERIFIED_LIVE_SMOKE',
    context_verified:false,
    safety_age_fit_verified:false,
    requested_use:'REFERENCE_ONLY',
    retrieved_at:item.candidate.retrieved_at
  });
  assert.equal(adapterResult.state,'CONTEXT_HOLD','live item must not bypass context verification');
  assert.equal(item.candidate.index_owner_authority,false);
  assert.equal(item.candidate.child_facing_approved,false);
  assert.equal(item.candidate.normative_usage_authority,false);
  assert.equal(item.candidate.frequency_authority,false);
  assert.equal(item.candidate.mastery_authority,false);

  console.log(JSON.stringify({
    status:'TATOEBA_LIVE_PROVIDER_SMOKE_PASS',
    sentence_id:item.candidate.sentence_id,
    language:item.candidate.language,
    license:item.candidate.license,
    owner_present:!!item.candidate.owner_or_author,
    license_provenance:item.candidate.license_provenance,
    adapter_state:adapterResult.state,
    direct_child_approval:false,
    index_owner_authority:false
  }));
})().catch(error=>{console.error(error);process.exit(1);});
