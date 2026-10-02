'use strict';
const assert=require('assert');
const Provider=require('./tatoeba-provider.js');

const searchUrl=Provider.buildSearchUrl({language:'eng',query:'island',max_word_count:8,limit:5});
const u=new URL(searchUrl);
assert.equal(u.origin,'https://api.tatoeba.org');
assert.equal(u.pathname,'/v1/sentences');
assert.equal(u.searchParams.get('lang'),'eng');
assert.equal(u.searchParams.get('q'),'island');
assert.equal(u.searchParams.get('is_unapproved'),'no');
assert.equal(u.searchParams.get('is_orphan'),'no');
assert.equal(u.searchParams.get('license'),'!PROBLEM');
assert.equal(u.searchParams.get('word_count'),'-8');
assert.equal(u.searchParams.get('showtrans'),'none');

assert.equal(Provider.mapLicense('CC BY 2.0 FR'),'CC-BY-2.0-FR');
assert.equal(Provider.mapLicense('CC0 1.0'),'CC0');
assert.equal(Provider.mapLicense('PROBLEM'),null);

const mapped=Provider.toProviderCandidate({
  id:1234,text:'The island is beautiful.',lang:'eng',license:'CC BY 2.0 FR',owner:'alice',is_unapproved:false
},'2026-10-02T01:00:00Z');
assert.equal(mapped.ok,true);
assert.equal(mapped.candidate.sentence_id,'1234');
assert.equal(mapped.candidate.license,'CC-BY-2.0-FR');
assert.equal(mapped.candidate.owner_or_author,'alice');
assert.equal(mapped.candidate.license_provenance,'https://api.tatoeba.org/v1/sentences/1234');
assert.equal(Provider.validateCandidate(mapped.candidate).ok,true);

assert.equal(Provider.toProviderCandidate({
  id:1234,text:'x',lang:'eng',license:'PROBLEM',owner:'alice'
}).state,'PROVENANCE_INCOMPLETE');
assert.equal(Provider.toProviderCandidate({
  id:1234,text:'x',lang:'eng',license:'CC BY 2.0 FR',owner:null
}).state,'PROVENANCE_INCOMPLETE');

const fakeFetch=async url=>({
  ok:true,status:200,
  json:async()=>url.includes('/v1/sentences/1234')
    ?{data:{id:1234,text:'The island is beautiful.',lang:'eng',license:'CC BY 2.0 FR',owner:'alice',is_unapproved:false}}
    :{data:[{id:1234,text:'The island is beautiful.',lang:'eng',license:'CC BY 2.0 FR',owner:'alice',is_unapproved:false}],paging:{}}
});

(async()=>{
  const searched=await Provider.searchSentences({language:'eng',query:'island'},{fetch_impl:fakeFetch});
  assert.equal(searched.ok,true);
  assert.equal(searched.candidates.length,1);
  const item=await Provider.fetchSentenceById('1234',{fetch_impl:fakeFetch});
  assert.equal(item.ok,true);
  assert.equal(item.candidate.license,'CC-BY-2.0-FR');
  console.log('TATOEBA_LIVE_PROVIDER_TRANSPORT_UNIT_TEST_PASS');
})().catch(error=>{console.error(error);process.exit(1);});
