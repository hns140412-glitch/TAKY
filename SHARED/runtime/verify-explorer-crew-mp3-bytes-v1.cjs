'use strict';
/* MP3 container/frame preflight. Checks that the uploaded bytes are MPEG Layer III
   and not a WAV/HTML/error page renamed .mp3. Auditory QA remains separate. */
const BITRATE_V1_L3=[0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0];
const BITRATE_V2_L3=[0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0];
function scan(buffer,{minDuration=0.35}={}){
 if(!Buffer.isBuffer(buffer)||buffer.length<1200)return {valid:false,reason:'MP3_BYTES_TOO_SHORT'};
 let pos=0,tagged=false;
 if(buffer.subarray(0,3).toString('ascii')==='ID3'){
  if(buffer.length<10)return {valid:false,reason:'INVALID_ID3_HEADER'};
  const parts=[buffer[6],buffer[7],buffer[8],buffer[9]];
  if(parts.some(x=>x&0x80))return {valid:false,reason:'INVALID_ID3_SYNCSAFE_SIZE'};
  const tagSize=(parts[0]<<21)|(parts[1]<<14)|(parts[2]<<7)|parts[3];
  pos=10+tagSize+((buffer[5]&0x10)?10:0);
  if(pos>buffer.length-100)return {valid:false,reason:'MP3_ID3_TAG_ONLY'};
  tagged=true;
 }
 const dataStart=pos;
 let first=null,frames=0,samples=0,samplesPerFrame=null,highest=null,lastError=null;
 while(pos+4<=buffer.length){
  const a=buffer[pos],b=buffer[pos+1],c=buffer[pos+2],d=buffer[pos+3];
  if(a!==0xff||(b&0xe0)!==0xe0){lastError='MPEG_FRAME_SYNC_MISSING';break}
  const ver=(b>>3)&3,layer=(b>>1)&3,rateIdx=(c>>4)&15,sampleIdx=(c>>2)&3;
  if(ver===1||layer!==1||rateIdx===0||rateIdx===15||sampleIdx===3){lastError='UNSUPPORTED_MPEG_LAYER_OR_HEADER';break}
  const mpeg1=ver===3,bs=(mpeg1?BITRATE_V1_L3:BITRATE_V2_L3)[rateIdx];
  const rates=[44100,48000,32000];
  const sr=Math.round(rates[sampleIdx]/(ver===3?1:ver===2?2:4));
  const padding=(c>>1)&1;
  const frameSize=Math.floor((mpeg1?144:72)*bs*1000/sr)+padding;
  const spf=mpeg1?1152:576;
  if(!bs||frameSize<24||pos+frameSize>buffer.length){lastError='INVALID_OR_TRUNCATED_MPEG_FRAME';break}
  if(!first)first={sample_rate:sr,channels:((d>>6)&3)===3?1:2,mpeg_version:ver===3?'MPEG1':ver===2?'MPEG2':'MPEG2.5'};
  if(sr!==first.sample_rate){lastError='INCONSISTENT_SAMPLE_RATE';break}
  frames++;samples+=spf;pos+=frameSize;highest=pos;
 }
 const trailing=buffer.subarray(pos);
 const validTrailing=(trailing.length===0 || (trailing.length===128&&trailing.subarray(0,3).toString('ascii')==='TAG'));
 const duration=first?samples/first.sample_rate:0;
 const valid=frames>=3&&duration>=minDuration&&validTrailing;
 return {valid,reason:valid?'MP3_FRAMES_VERIFIED':lastError||(!validTrailing?'UNEXPECTED_TRAILING_BYTES': 'INSUFFICIENT_MP3_DURATION'),
  tagged,frame_count:frames,duration_seconds:Math.round(duration*1000)/1000,
  audio_bytes:highest===null?0:highest-dataStart,...first};
}
module.exports=Object.freeze({scan});
