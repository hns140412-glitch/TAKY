"""Local MCP executable check without starting providers or reading credentials."""
from pathlib import Path
import json,os,shutil,tomllib
ROOT=Path("D:/Git PWA");WB=ROOT/"TAKY_AI_WORKBENCH"
OUT=WB/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"TAKY_MCP_EXECUTABLE_PREFLIGHT_20261013.json"
def effective(cmd):
 if not isinstance(cmd,str) or not cmd.strip():return None
 item=Path(os.path.expandvars(cmd.strip()))
 if item.is_file():return str(item)
 return shutil.which(cmd.strip())
def main():
 home=Path.home()
 sources={
  "codex":(home/".codex"/"config.toml","mcp_servers"),
  "claude_desktop":(Path(os.environ["APPDATA"])/"Claude"/"claude_desktop_config.json","mcpServers"),
 }
 rows=[];missing=[]
 for name,(f,key) in sources.items():
  if not f.is_file():
   missing.append("CONFIG_NOT_PRESENT:"+name)
   continue
  data=tomllib.loads(f.read_text(encoding="utf-8-sig")) if f.suffix==".toml" else json.loads(f.read_text(encoding="utf-8-sig"))
  for server,entry in data.get(key,{}).items():
   if "url" in entry and "command" not in entry:
    rows.append({"client":name,"server":server,"type":"REMOTE_ENDPOINT","probe":"NOT_CALLED"})
    continue
   program=entry.get("command")
   resolved=effective(program)
   record={"client":name,"server":server,
           "program_name":Path(program).name if isinstance(program,str) else None,
           "present":bool(resolved),"not_executed":True}
   if not resolved:missing.append(name+":"+server)
   rows.append(record)
 result={"schema":"TAKY_MCP_EXECUTABLE_PREFLIGHT_V1",
         "launchers":rows,"missing":missing,
         "state":"REFERENCES_PRESENT" if not missing else "MISSING_LAUNCHER",
         "live_protocol_handshake_verified":False,
         "credentials_read":False,"external_call":False}
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"state":result["state"],"launchers":rows,
   "runtime_handshake":"NOT_PERFORMED","evidence":str(OUT)},ensure_ascii=False))
 raise SystemExit(0 if not missing else 2)
if __name__=="__main__":main()
