#!/usr/bin/env python3
"""Read-only MCP initialization + tools/list probe, no tool execution, no inference.
Only use locally governed exact packages. Timeout and terminate subprocess on all exits.
"""
import json, subprocess, sys, time, pathlib, hashlib
from datetime import datetime,timezone

BASE=pathlib.Path(r"D:\Git PWA\TAKY")
REPORT=pathlib.Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY\TAKY_MCP_PROTOCOL_PROBE_20261012.json")
PACKAGES={
  "playwright":"@playwright/mcp@0.0.83",
  "chrome-devtools":"chrome-devtools-mcp@1.10.1"
}
def rpc(method, request_id=None, params=None):
    o={"jsonrpc":"2.0","method":method}
    if request_id is not None:o["id"]=request_id
    if params is not None:o["params"]=params
    return json.dumps(o,ensure_ascii=False,separators=(",",":"))+"\n"
def probe(name,package):
    lines=[
      rpc("initialize",1,{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"TAKY_READONLY_DIAG","version":"1.0"}}),
      rpc("notifications/initialized"),
      rpc("tools/list",2,{})
    ]
    cmd=["cmd","/c","npx","-y",package]
    started=time.monotonic()
    p=None
    receipt={"name":name,"package":package,"state":"HOLD","tools_count":0,
             "read_only_probe":True,"tools_executed":0}
    try:
        p=subprocess.Popen(cmd,cwd=str(BASE),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        out,err=p.communicate("".join(lines).encode("utf-8"),timeout=24)
        responses=[]
        for line in out.decode("utf-8",errors="replace").splitlines():
            try:
                obj=json.loads(line)
                if isinstance(obj,dict):responses.append(obj)
            except (ValueError,TypeError):
                pass
        init=next((r for r in responses if r.get("id")==1 and "result" in r),None)
        tools=next((r for r in responses if r.get("id")==2 and "result" in r),None)
        receipt["protocol_version"]=((init or {}).get("result") or {}).get("protocolVersion")
        if init and tools:
            names=[t.get("name") for t in (tools.get("result") or {}).get("tools",[]) if isinstance(t,dict)]
            receipt.update(state="MCP_INITIALIZE_AND_TOOLS_LIST_PASS",
                           tools_count=len(names),sample_tool_names=names[:6])
        else:
            receipt["state"]="MCP_PROTOCOL_HANDSHAKE_HOLD"
            receipt["returned_ids"]=[r.get("id") for r in responses if r.get("id") is not None][:5]
        receipt["exit_code"]=p.returncode
        receipt["stderr_lines_count"]=len(err.decode("utf-8",errors="replace").splitlines())
    except subprocess.TimeoutExpired:
        receipt["state"]="MCP_PROBE_TIMEOUT_HOLD"
        if p:
            p.kill()
            try:p.communicate(timeout=3)
            except Exception:pass
    except Exception as e:
        receipt["state"]="MCP_PROBE_PROCESS_ERROR_HOLD"
        receipt["error_type"]=type(e).__name__
    finally:
        if p and p.poll() is None:
            p.kill()
            try:p.communicate(timeout=3)
            except Exception:pass
    receipt["duration_seconds"]=round(time.monotonic()-started,2)
    return receipt
data={"schema":"TAKY_MCP_PROTOCOL_INSPECTION_V1",
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "probes":[probe(k,v) for k,v in PACKAGES.items()],
      "no_model_calls":True,"no_mcp_tools_called":True,"no_live_browser_navigation":True,
      "authorization_not_granted_by_probe":True,"project_current_untouched":True}
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"results":data["probes"],"report_file":str(REPORT)},ensure_ascii=False))
sys.exit(0 if all(x["state"]=="MCP_INITIALIZE_AND_TOOLS_LIST_PASS" for x in data["probes"]) else 2)
