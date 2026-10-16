#!/usr/bin/env python3
"""Read-only metadata inventory for existing Antigravity Claude/Codex sessions.
Never collect user/assistant messages, auth material, tool inputs, or transcript body.
"""
from __future__ import annotations
import hashlib,json,pathlib
from datetime import datetime,timezone
ROOT=pathlib.Path.home()
CODEX=ROOT/".codex"/"sessions"
CLAUDE=ROOT/".claude"/"projects"/"D--Git-PWA-TAKY-2-0-ORCH"
OUT=pathlib.Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY\TAKY_ANTIGRAVITY_SESSION_METADATA_20261012.json")
def short_hash(x):return hashlib.sha256(str(x).encode()).hexdigest()[:12]
def rows(folder,provider,max_files=10):
  if not folder.is_dir():return []
  files=sorted(folder.rglob("*.jsonl") if provider=="CODEX" else folder.glob("*.jsonl"),key=lambda x:x.stat().st_mtime,reverse=True)[:max_files]
  result=[]
  for p in files:
    meta={"provider":provider,"basename":p.stem,"size_bytes":p.stat().st_size,
          "last_write_utc":datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),
          "content_exported":False,"session_id":"UNVERIFIED","source":"UNKNOWN","repo_match":"UNKNOWN"}
    try:
      with p.open("r",encoding="utf-8-sig",errors="replace") as f:
        for line in f:
          if len(line)>800000:continue
          d=json.loads(line)
          if provider=="CODEX" and d.get("type")=="session_meta":
            payload=d.get("payload") or {}
            meta["session_id"]=str(payload.get("id") or "UNKNOWN")
            meta["source"]=str(payload.get("source") or "UNKNOWN")[:64]
            cwd=str(payload.get("cwd") or "")
            meta["repo_match"]="TAKY2" if "TAKY-2.0-ORCH" in cwd.upper() else "TAKY" if "GIT PWA\\TAKY" in cwd.upper() else "OTHER_OR_UNKNOWN"
            meta["metadata_digest"]=short_hash([meta["session_id"],meta["source"],meta["repo_match"]])
            break
          if provider=="CLAUDE":
            # Claude filename is an opaque session ID. No content readback.
            meta["session_id"]=p.stem
            meta["repo_match"]="TAKY2_PROJECT_DIRECTORY"
            meta["source"]="CLAUDE_JSONL_METADATA_ONLY"
            break
    except (OSError,ValueError,TypeError):meta["source"]="PARSE_HOLD"
    result.append(meta)
  return result
d={"schema":"TAKY_EXISTING_IDE_SESSION_METADATA_CANDIDATE_V1",
   "generated_at":datetime.now(timezone.utc).isoformat(),
   "claude":rows(CLAUDE,"CLAUDE"),"codex":rows(CODEX,"CODEX"),
   "native_panel_binding":"UNVERIFIED","app_server_shared_writer":"NOT_CONNECTED",
   "no_model_invocation":True,"no_transcripts_exported":True,"authority":"METADATA_ONLY_NONCANONICAL"}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"claude_session_count":len(d["claude"]),"codex_session_count":len(d["codex"]),
  "codex_source_counts":{v:sum(x["source"]==v for x in d["codex"]) for v in sorted({x["source"] for x in d["codex"]})},
  "codex_taky2_sessions":sum(x["repo_match"]=="TAKY2" for x in d["codex"]),
  "latest_claude_metadata":d["claude"][0] if d["claude"] else None,
  "native_panel_binding":d["native_panel_binding"],"report_file":str(OUT)},ensure_ascii=False))
