'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

(async()=>{
  const elements=new Map();
  const make=(id)=>({id,hidden:false,textContent:'',innerHTML:'',clientWidth:320,addEventListener(){},appendChild(){},setAttribute(){}});
  for(const id of ['takyAccountAuthHost','takyAccountAuthStatus','takyGoogleButton','takyFamilyChoices','takyAccountSignOut'])elements.set(id,make(id));
  const document={
    readyState:'complete',
    documentElement:{dataset:{}},
    getElementById:id=>elements.get(id)||null,
    querySelector:()=>null,
    createElement:tag=>make(tag),
    head:{appendChild(){}},
    body:{appendChild(){}}
  };
  let credentialCallback=null,rendered=false,boundFamily=null;
  const ctx={
    window:null,globalThis:null,document,location:{href:'https://ready.example.test/'},URL,console,setTimeout,clearTimeout,
    CustomEvent:function(type,opts){this.type=type;this.detail=opts?.detail},
    fetch:async(url,opts)=>{
      assert.equal(String(url),'https://central.example.test/api/family/session');
      assert.equal(opts.headers.authorization,'Bearer google-id-token-demo-0000001');
      return {ok:true,status:200,json:async()=>({ok:true,session:{principal_id:'google:sub1',identity_provider:'GOOGLE_OIDC_VERIFIED',families:[{family_id:'F1',self_member_id:'P1',authorized_member_ids:['P1','C1']}]}})};
    },
    TAKY_ACCOUNT_AUTH_CONFIG:{googleClientId:'1234567890-demo.apps.googleusercontent.com',apiBaseUrl:'https://central.example.test/'},
    TakyFamilyAuthRuntimeV1:{
      registerCentralBearerProvider({preferredFamilyId,getIdToken}){boundFamily=preferredFamilyId;this.getIdToken=getIdToken},
      async installFamilyRuntime(){assert.equal(await this.getIdToken(),'google-id-token-demo-0000001');return{state:'BOUND',family_id:boundFamily}}
    },
    google:{accounts:{id:{
      initialize(cfg){credentialCallback=cfg.callback},
      renderButton(){rendered=true;setTimeout(()=>credentialCallback({credential:'google-id-token-demo-0000001'}),0)},
      disableAutoSelect(){}
    }}},
    dispatchEvent(){}
  };
  ctx.window=ctx;ctx.globalThis=ctx;
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(__dirname+'/taky-google-account-auth-v1.js','utf8'),ctx,{filename:'taky-google-account-auth-v1.js'});
  await new Promise(r=>setTimeout(r,30));
  assert.equal(rendered,true);
  assert.equal(boundFamily,'F1');
  assert.equal(document.documentElement.dataset.takyAccountAuth,'AUTHENTICATED');
  assert.equal(ctx.TakyGoogleAccountAuthV1.status().authenticated,true);
  console.log('GOOGLE_ACCOUNT_AUTH_RUNTIME_PASS: account button credential -> verified family session -> TAKY family runtime bind; token remains memory-only');
})().catch(e=>{console.error(e);process.exit(1)});
