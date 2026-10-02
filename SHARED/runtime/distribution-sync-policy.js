(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports) module.exports=api;
  else root.TakyDistributionSyncPolicy=Object.freeze(api);
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const LARGE_PACKAGE_BYTES=5*1024*1024;

  function normalizeType(v){
    const s=String(v||'').trim().toLowerCase();
    if(['wifi','ethernet','cellular','bluetooth','wimax','other','unknown','none'].includes(s)) return s;
    return '';
  }

  function inspectNetwork(input={}){
    const online=input.online!==false;
    if(!online) return {online:false,confirmed_wifi:false,kind:'OFFLINE'};
    const type=normalizeType(input.type);
    if(type==='wifi') return {online:true,confirmed_wifi:true,kind:'WIFI'};
    if(type) return {online:true,confirmed_wifi:false,kind:type.toUpperCase()};
    return {online:true,confirmed_wifi:false,kind:'ONLINE_TYPE_UNKNOWN'};
  }

  function decideDownload(input={}){
    const net=inspectNetwork(input.network||{});
    const bytes=Math.max(0,Number(input.bytes)||0);
    const automatic=input.automatic!==false;
    if(!net.online) return {allow:false,reason:'OFFLINE',network:net};
    if(input.save_data===true) return {allow:false,reason:'SAVE_DATA_ENABLED',network:net};
    if(!automatic) return {allow:true,reason:'USER_EXPLICIT',network:net};
    if(net.confirmed_wifi) return {allow:true,reason:'CONFIRMED_WIFI',network:net};
    if(bytes>=LARGE_PACKAGE_BYTES) return {allow:false,reason:'WAIT_FOR_CONFIRMED_WIFI',network:net};
    return {allow:false,reason:'AUTO_DOWNLOAD_REQUIRES_CONFIRMED_WIFI',network:net};
  }

  function publicStatus(decision){
    if(!decision||decision.allow===false){
      return Object.freeze({state:'WAITING',message:'업데이트 대기 중'});
    }
    return Object.freeze({state:'READY_TO_DOWNLOAD',message:'업데이트 준비됨'});
  }

  function buildRequest(input={}){
    const decision=decideDownload(input);
    return Object.freeze({
      contract:'TAKY_DISTRIBUTION_SYNC_POLICY_V1',
      provider_role:'SIEZEALL_APPROVED_DISTRIBUTION',
      ui_visibility:'APP_INTERNAL',
      expose_drive_structure:false,
      expose_provider_credentials:false,
      changed_packages_only:true,
      verify_sha256_before_activate:true,
      atomic_swap:true,
      keep_previous_known_good:true,
      decision,
      public_status:publicStatus(decision)
    });
  }

  return Object.freeze({
    version:'1.0.0',
    largePackageBytes:LARGE_PACKAGE_BYTES,
    inspectNetwork,
    decideDownload,
    publicStatus,
    buildRequest
  });
});
