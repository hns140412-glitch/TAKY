const fs=require('fs'),cp=require('child_process');
const prompt=fs.readFileSync('C:/Users/YKH_1507-03/AppData/Roaming/TAKY/claude-visible-prompt.txt','utf8');
const args=['--print','--model','claude-sonnet-5-5','--add-dir','D:/Git PWA/TAKY-SOURCE-VAULT',prompt];
const r=cp.spawnSync('C:/Users/YKH_1507-03/.local/bin/claude.exe',args,{cwd:'D:/Git PWA/TAKY',encoding:'utf8',stdio:['ignore','pipe','pipe'],maxBuffer:32*1024*1024});
if(r.stdout)process.stdout.write(r.stdout);
if(r.stderr)process.stderr.write(r.stderr);
process.exit(Number.isInteger(r.status)?r.status:1);