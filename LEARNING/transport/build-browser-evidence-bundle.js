'use strict';
/** Deterministic dependency-free browser bundle of the five audited modules. */
const fs=require('node:fs');
const path=require('node:path');
const files=['scoped-evidence-outbox.js','indexeddb-evidence-outbox-store.js',
 'pwa-central-evidence-ack-client.js','pwa-scoped-evidence-pipeline.js',
 'specialist-observation-packet-mapper.js'];
const root=__dirname;
function build(){
 const modules=files.map(file=>{
  const code=fs.readFileSync(path.join(root,file),'utf8');
  if(/require\s*\(\s*['"]node:/.test(code))throw Error('BROWSER_NODE_BUILTIN_FORBIDDEN:'+file);
  return JSON.stringify('./'+file)+':function(module,exports,require){\n'+code+'\n}';
 }).join(',\n');
 return `(function(root){'use strict';\nconst modules={${modules}};const cache={};\nfunction require(id){if(!Object.hasOwn(modules,id))throw Error('UNDECLARED_BROWSER_MODULE:'+id);if(!cache[id]){const module={exports:{}};cache[id]=module;modules[id](module,module.exports,require)}return cache[id].exports}\nroot.TakyCentralEvidence=Object.freeze({pipeline:require('./pwa-scoped-evidence-pipeline.js'),mapper:require('./specialist-observation-packet-mapper.js')});\n})(globalThis);\n`;
}
if(require.main===module){
 const output=process.argv[2];
 if(!output)throw Error('EXPLICIT_OUTPUT_PATH_REQUIRED');
 fs.writeFileSync(output,build());
 console.log('BROWSER_EVIDENCE_BUNDLE_GENERATED');
}
module.exports={build};
