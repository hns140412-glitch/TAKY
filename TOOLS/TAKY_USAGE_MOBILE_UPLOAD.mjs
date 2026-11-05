// TAKY mobile: update exactly one app-created Drive JSON file, using local clasp OAuth.
// Never log credentials; do not transmit unfiltered source data.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {Readable} from 'node:stream';
import {createRequire} from 'node:module';
const work=path.join(process.env.LOCALAPPDATA||path.join(os.homedir(),'AppData','Local'),'TAKY','USAGE_BOARD');
const stateFile=path.join(work,'mobile_cloud_state.json');
const input=process.argv[2];
const dry=process.argv.includes('--dry-run');
if(!input || !fs.existsSync(input))throw new Error('SANITIZED_SNAPSHOT_REQUIRED');
const content=fs.readFileSync(input,'utf8');
if(Buffer.byteLength(content)>100000)throw new Error('SNAPSHOT_TOO_LARGE');
const payload=JSON.parse(content);
if(payload.schema!=='TAKY_USAGE_MOBILE_PROJECTION_V1'||!Array.isArray(payload.providers))
  throw new Error('NOT_ALLOWLISTED_PROJECTION');
const current=fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile,'utf8')):{};
if(dry){
  process.stdout.write(JSON.stringify({status:'DRY_RUN',bytes:Buffer.byteLength(content),
    providers:payload.providers.length,existingCloudFile:!!current.driveFileId})+'\n');
  process.exit(0);
}
const claspDir=path.join(process.env.APPDATA,'npm','node_modules','@google','clasp');
const require=createRequire(path.join(claspDir,'package.json'));
const {google}=require('googleapis');
const authPath=path.join(os.homedir(),'.clasprc.json');
if(!fs.existsSync(authPath))throw new Error('GOOGLE_OAUTH_NOT_AUTHORIZED');
const stored=JSON.parse(fs.readFileSync(authPath,'utf8'));
const credentials=stored.tokens?.default || (stored.refresh_token?stored:null);
if(!credentials || !credentials.refresh_token)throw new Error('GOOGLE_OAUTH_NOT_AUTHORIZED');
const client=new google.auth.OAuth2(credentials.client_id,credentials.client_secret);
client.setCredentials(credentials);
const drive=google.drive({version:'v3',auth:client});
const media=()=>({mimeType:'application/json',body:Readable.from([content])});
let id=current.driveFileId;
if(id){
  await drive.files.update({fileId:id,media:media(),fields:'id',supportsAllDrives:true});
  process.stdout.write(JSON.stringify({status:'CLOUD_UPDATED',id,bytes:Buffer.byteLength(content)})+'\n');
}else{
  const result=await drive.files.create({requestBody:{name:'TAKY_USAGE_CURRENT.json',
    description:'TAKY AI usage: sanitized read-only mobile projection',mimeType:'application/json'},
    media:media(),fields:'id,name',supportsAllDrives:true});
  id=result.data.id;
  if(!id)throw new Error('CLOUD_CREATE_NO_FILE_ID');
  fs.mkdirSync(work,{recursive:true});
  const tmp=stateFile+'.tmp';
  fs.writeFileSync(tmp,JSON.stringify({driveFileId:id},null,2)+'\n',{encoding:'utf8',mode:0o600});
  fs.renameSync(tmp,stateFile);
  process.stdout.write(JSON.stringify({status:'CLOUD_CREATED',id,bytes:Buffer.byteLength(content)})+'\n');
}
