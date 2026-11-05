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
    const data = JSON.parse(text);
    if (data.schema !== 'TAKY_USAGE_MOBILE_PROJECTION_V1' || !Array.isArray(data.providers))
      throw new Error('INVALID_PROJECTION_SCHEMA');
    const captured = Date.parse(data.exportedAt);
    const ageMs = Date.now() - captured;
    const freshSync = Number.isFinite(ageMs) && ageMs >= -120000 && ageMs < 12*60*1000;
    return {ok:true, data:data, synchronized:freshSync, ageMinutes:Math.round(ageMs/60000)};
  } catch(e) {
    return {ok:false, error:'SNAPSHOT_UNAVAILABLE'};
  }
}

