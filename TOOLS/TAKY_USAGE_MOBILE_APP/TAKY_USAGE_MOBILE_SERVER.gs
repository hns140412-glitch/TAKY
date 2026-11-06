// TAKY usage mobile viewer. Deploy only to "Only myself", executing as owner.
// The setup script binds one app-owned sanitized Drive file ID before publishing.
const TAKY_MOBILE_CLOUD_FILE_ID = '1nfyzMSmTqZiTUe5rneaBUDcFqlmhUkw9';
function doGet() {
  return HtmlService.createHtmlOutputFromFile('TAKY_USAGE_MOBILE_VIEW')
    .setTitle('TAKY AI 사용량')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}
function loadUsage() {
  const id = TAKY_MOBILE_CLOUD_FILE_ID;
  if (!id) return {ok:false, error:'DRIVE_FILE_NOT_CONFIGURED'};
  try {
    const text = DriveApp.getFileById(id).getBlob().getDataAsString('UTF-8');
    if (text.length > 100000) throw new Error('SNAPSHOT_TOO_LARGE');
    const cached = JSON.parse(text);
    if (cached.schema !== 'TAKY_USAGE_MOBILE_PROJECTION_V1' || !Array.isArray(cached.providers))
      throw new Error('INVALID_PROJECTION_SCHEMA');
    const bridge = cached.bridge;
    delete cached.bridge; // Never disclose private access key to browser.
    let data = cached;
    let source = 'CACHED_DRIVE';
    let pcReachable = false;
    let liveRefresh = false;
    if (bridge && /^https:\/\/[a-z0-9-]+\.trycloudflare\.com$/.test(bridge.baseUrl) &&
        /^[a-f0-9]{64}$/.test(bridge.accessKey)) {
      try {
        const r = UrlFetchApp.fetch(bridge.baseUrl+'/api/usage/mobile', {
          method:'get', muteHttpExceptions:true, followRedirects:false,
          headers:{'X-TAKY-Usage-Key':bridge.accessKey}
        });
        if (r.getResponseCode() === 200) {
          const reply = JSON.parse(r.getContentText('UTF-8'));
          if (reply.ok && reply.data && reply.data.schema === 'TAKY_USAGE_MOBILE_PROJECTION_V1' &&
              Array.isArray(reply.data.providers)) {
            data = reply.data;
            delete data.bridge;
            pcReachable = true;
            liveRefresh = reply.refreshed === true;
            source = 'LIVE_PC';
          }
        }
      } catch(e) { /* Offline PC: return clearly labeled cached snapshot. */ }
    }
    const captured = Date.parse(data.exportedAt);
    const ageMs = Date.now() - captured;
    const freshSync = Number.isFinite(ageMs) && ageMs >= -120000 && ageMs < 12*60*1000;
    return {ok:true, data, synchronized:freshSync, ageMinutes:Math.round(ageMs/60000),
            source, pcReachable, liveRefresh};
  } catch(e) {
    return {ok:false, error:'SNAPSHOT_UNAVAILABLE'};
  }
}

