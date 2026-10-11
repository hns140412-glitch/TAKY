'use strict';

const fs=require('node:fs');
const path=require('node:path');
const {spawnSync}=require('node:child_process');

const VERSION='TAKY_POST_MINING_LEARNING_REFRESH_V1';
const repoRoot=path.resolve(__dirname,'..','..');
const node=process.execPath;
const hideRepo=path.resolve(process.env.HIDE_REPO||'D:\\Git PWA\\Hide & Seek');
const receiptPath=path.join(repoRoot,'CURRENT','DATA','MINING_LEARNING_REFRESH_CURRENT.json');

function run(label,script,args=[],options={}){
  const started=Date.now();
  const result=spawnSync(node,[script,...args],{
    cwd:options.cwd||repoRoot,
    env:{...process.env,...(options.env||{})},
    encoding:'utf8',
    stdio:'pipe'
  });
  const out={
    label,
    script:path.relative(repoRoot,script).replace(/\\/g,'/'),
    exit_code:result.status,
    duration_ms:Date.now()-started,
    stdout:String(result.stdout||'').trim().slice(-12000),
    stderr:String(result.stderr||'').trim().slice(-12000)
  };
  if(result.status!==0){
    const err=new Error(label+'_FAILED');
    err.step=out;
    throw err;
  }
  return out;
}

function main(){
  const projectionDir=path.join(repoRoot,'LEARNING','projection');
  const verificationDir=path.join(repoRoot,'LEARNING','verification');
  const pedagogyDir=path.join(repoRoot,'LEARNING','pedagogy');
  const transportDir=path.join(repoRoot,'LEARNING','transport');
  const steps=[];

  steps.push(run('PROJECT_INDEXED_MINING_PATTERNS',path.join(projectionDir,'build-mining-learning-pattern-registry.js')));
  steps.push(run('MINE_REFERENCE_HANJA',path.join(projectionDir,'mine-hanja-reference-sources.js')));
  steps.push(run('BUILD_PRELEARNED_56',path.join(projectionDir,'build-prelearned-term-universe.js')));
  steps.push(run('BUILD_PRELEARNED_ELEMENTARY',path.join(projectionDir,'build-elementary-profile-term-universe.js')));

  let hideState='SKIPPED_HIDE_REPO_NOT_AVAILABLE';
  if(fs.existsSync(hideRepo)){
    steps.push(run(
      'BUILD_HIDE_PRELEARNED_PACKS',
      path.join(projectionDir,'build-hide-prelearned-term-packs.js'),
      [],
      {env:{HIDE_REPO:hideRepo}}
    ));
    hideState='BUILT';
  }

  const tests=[
    ['TEST_MINING_PATTERN_ROUTER',path.join(projectionDir,'mining-learning-pattern-router.test.js')],
    ['TEST_GRADE_AWARE_SELECTOR',path.join(pedagogyDir,'grade-aware-term-selector.test.js')],
    ['TEST_PRELEARNED_E2E',path.join(verificationDir,'prelearned-term-universe.e2e.test.js')],
    ['TEST_TERM_ENDPOINT',path.join(transportDir,'term-recommendation-http-endpoint.test.js')]
  ];
  if(fs.existsSync(hideRepo)){
    tests.push(
      ['TEST_HIDE_TERM_LOADER',path.join(hideRepo,'tools','test-learning-term-loader-v1.cjs')],
      ['TEST_HIDE_TERM_DECODER',path.join(hideRepo,'tools','test-term-decoder-v1.cjs')]
    );
  }
  for(const [label,script] of tests)steps.push(run(label,script,[],{cwd:path.dirname(script)}));

  const patternReceipt=JSON.parse(fs.readFileSync(
    path.join(repoRoot,'CURRENT','DATA','LEARNING_REFERENCE_PATTERN_PROJECTION_CURRENT.json'),'utf8'
  ).replace(/^\uFEFF/,''));
  const elementary=JSON.parse(fs.readFileSync(
    path.join(repoRoot,'LEARNING','data','prelearned','subject-term-universe-elementary-v1.json'),'utf8'
  ).replace(/^\uFEFF/,''));

  const receipt={
    schema:'TAKY_POST_MINING_LEARNING_REFRESH_RECEIPT_V1',
    generated_at:new Date().toISOString(),
    version:VERSION,
    policy:{
      collector_boundary:'COLLECTOR_ONLY_ACQUIRES_AND_HANDS_OFF; THIS_REFRESH_RUNS_AFTER_MINING_INDEXING',
      runtime_rule:'PRELEARNED_PROJECTION_FIRST; RUNTIME_SELECTS_ONLY',
      cost_mode:'LOCAL_FREE_ONLY',
      paid_api_calls:false,
      network_calls:false
    },
    pattern_projection:patternReceipt.summary,
    elementary_projection:{
      schema:elementary.schema,
      stages:elementary.stages,
      stage_subject_counts:elementary.stage_subject_counts,
      counts:elementary.counts
    },
    hide_projection:hideState,
    steps:steps.map(x=>({
      label:x.label,
      script:x.script,
      exit_code:x.exit_code,
      duration_ms:x.duration_ms
    })),
    state:'PASS'
  };
  fs.mkdirSync(path.dirname(receiptPath),{recursive:true});
  fs.writeFileSync(receiptPath,JSON.stringify(receipt,null,2)+'\n','utf8');
  console.log(JSON.stringify(receipt,null,2));
}

try{main()}
catch(err){
  const failure={
    schema:'TAKY_POST_MINING_LEARNING_REFRESH_RECEIPT_V1',
    generated_at:new Date().toISOString(),
    version:VERSION,
    state:'FAIL',
    failed_step:err.step||null,
    error:String(err&&err.stack||err)
  };
  fs.mkdirSync(path.dirname(receiptPath),{recursive:true});
  fs.writeFileSync(receiptPath,JSON.stringify(failure,null,2)+'\n','utf8');
  console.error(JSON.stringify(failure,null,2));
  process.exit(1);
}
