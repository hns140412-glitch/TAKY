'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {scan}=require('./verify-explorer-crew-mp3-bytes-v1.cjs');
function synthFrame(){
 const rate=128000,sr=44100,length=Math.floor(144*rate/sr);
 const buffer=Buffer.alloc(length,0x42);
 buffer[0]=0xff;buffer[1]=0xfb;buffer[2]=0x90;buffer[3]=0x64;
 return buffer;
}
test('valid contiguous Layer III frame layout passes structural preflight',()=>{
 const bytes=Buffer.concat(Array.from({length:20},synthFrame));
 const r=scan(bytes);assert.equal(r.valid,true);assert.equal(r.sample_rate,44100);
 assert.equal(r.frame_count,20);assert.ok(r.duration_seconds>0.5);
});
test('ID3 header+valid frames accepted',()=>{
 const tag=Buffer.from([0x49,0x44,0x33,0x04,0,0,0,0,0,0]);
 assert.equal(scan(Buffer.concat([tag,...Array.from({length:20},synthFrame)])).valid,true);
});
test('reject WAV renamed mp3, fake HTTP document and corrupt frames',()=>{
 const wav=Buffer.alloc(12000);wav.write('RIFF',0);wav.write('WAVE',8);
 assert.equal(scan(wav).valid,false);
 const html=Buffer.from('<html>Quota exceeded</html>'.repeat(1000));
 assert.equal(scan(html).valid,false);
 const mp3=Buffer.concat(Array.from({length:20},synthFrame));mp3.fill(0,10*synthFrame().length,10*synthFrame().length+8);
 assert.equal(scan(mp3).valid,false);
});
test('reject ID3-only, impossible tag length and tiny file',()=>{
 const tag=Buffer.from([0x49,0x44,0x33,4,0,0,0,0,0x7f,0x7f]);
 assert.equal(scan(tag).valid,false);
 assert.equal(scan(Buffer.alloc(12)).valid,false);
});
