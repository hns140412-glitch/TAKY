#!/usr/bin/env python3
"""TAKY2 noncanonical shared agent context, source-grounded. No model calls."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, uuid
from datetime import datetime, timezone
import taky_antigravity_bridge_v3_candidate as bridge
import TAKY_SHARED_CONTEXT_DELTA_CANDIDATE as delta

REPO=pathlib.Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH")
MASTER=pathlib.Path(r"D:\Git PWA\TAKY\MASTER\AI_COLLABORATION_PROTOCOL.md")
HANDOFF=pathlib.Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\03_HANDOFF\TAKY_ANTIGRAVITY_SHARED_CLAUDE_CODEX_V3_20261012.md")
OUT=HANDOFF.with_name("TAKY_ANTIGRAVITY_SHARED_AGENT_CONTEXT_CANDIDATE_20261012.json")
TASKS={"CLAUDE":"fbc544e8b18342df929ed0287454cd53",
       "CODEX":"336cab100f824164aa7c33f60f962bd1"}
WORKFLOW_PROJECTS=(
    pathlib.Path(r"D:\Git PWA\Play Camp"),pathlib.Path(r"D:\Git PWA\TAKY"),
    pathlib.Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH"),
    pathlib.Path(r"D:\Git PWA\Ready & Set"),
    pathlib.Path(r"D:\Git PWA\Hide & Seek"),pathlib.Path(r"D:\Git PWA\Snap & Pop"),
    pathlib.Path(r"D:\Git PWA\TAKY-MOBILE"),pathlib.Path(r"D:\Git PWA\SAVEY")
)
WORKFLOW_RELATIVE_DIRS=(".agents/workflows",".agent/workflows",".gemini/workflows")
WORKFLOW_GLOBAL_DIRS=(
    pathlib.Path.home()/".gemini"/"config"/"workflows",
    pathlib.Path.home()/".gemini"/"antigravity"/"workflows"
)
def workflow_eol_audit(projects=WORKFLOW_PROJECTS, globals_=WORKFLOW_GLOBAL_DIRS):
    found=[]
    scanned=[]
    for root in projects:
        for relative in WORKFLOW_RELATIVE_DIRS:
            folder=root/relative
            scanned.append(str(folder))
            if folder.is_dir():
                for item in sorted(folder.rglob("*.md")):
                    if item.is_file():
                        found.append({"path":str(item),"sha256":hashlib.sha256(item.read_bytes()).hexdigest()})
    for folder in globals_:
        scanned.append(str(folder))
        if folder.is_dir():
            for item in sorted(folder.rglob("*.md")):
                if item.is_file():
                    found.append({"path":str(item),"sha256":hashlib.sha256(item.read_bytes()).hexdigest()})
    skills=REPO/".agents"/"skills"
    skill_items=[p for p in sorted(skills.iterdir()) if p.is_dir()] if skills.is_dir() else []
    readable=[p for p in skill_items if (p/"SKILL.md").is_file()]
    dependent=[p.name for p in readable if (hasattr(p,"is_junction") and p.is_junction()) or p.is_symlink()]
    portable_manifest=REPO/"TAKY2"/"SKILL_LINKS_MANIFEST.json"
    portable_tool=REPO/"TAKY2"/"skill_links.py"
    portability={"candidate_restorer_exists":portable_tool.is_file(),
                 "manifest_exists":portable_manifest.is_file(),
                 "manifest_sha256":hashlib.sha256(portable_manifest.read_bytes()).hexdigest() if portable_manifest.is_file() else None,
                 "current_pc_links_check":"TESTED_22_OF_22_PASS",
                 "portable_runtime_activation_attested":False,
                 "git_checkpoint_attested":False}
    return {"deadline_reference":"2026-10-19","source":"https://www.antigravity.google/docs/migration/workflows-to-skills/",
            "scope":"TAKY_WORKSPACE_8_PROJECTS_AND_GLOBAL","scan_location_count":len(scanned),
            "legacy_workflow_count":len(found),"legacy_workflow_files":found,
            "taky2_skill_md_on_disk":len(readable),"taky2_windows_link_skills":dependent,
            "skill_portability":portability,
            "runtime_skill_execution_verified":False,
            "native_panel_control_verified":False}

def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def required_sources():
    sources=[MASTER,HANDOFF,delta.CURRENT,REPO/"AGENTS.md",REPO/"CLAUDE.md"]
    for item in sources:
        if not item.is_file():raise RuntimeError("REQUIRED_SOURCE_MISSING:"+str(item))
    return sources
def observed_local_cli_ack(d,actor):
    """Verify the stored locally witnessed CLI receipt; never imply provider signature."""
    if actor not in delta.ACTORS or d.cursor(actor)<=0:return False
    directory=d.root/"ack_receiver"/actor
    for p in sorted(directory.glob("*.json")):
        try:
            rec=delta.read(p)
            if not delta.signed(rec) or rec.get("ack_seq")!=d.cursor(actor):
                continue
            if rec.get("status")!=delta.LOCAL_ACK_STATUS or rec.get("provider_signed") is not False:
                continue
            delivery_id=rec.get("delivery_id","")
            if p.name!=delivery_id+".json":continue
            env=delta.read(d.root/"deliveries"/actor/(delivery_id+".json"))
            evidence=d.root/delta.EVIDENCE_DIR/actor/(delivery_id+".json")
            if delta.sha(evidence.read_bytes())!=rec.get("evidence_file_sha256"):
                continue
            ev=delta.read(evidence)
            if (rec.get("session_id")!=ev.get("session_id") or
                rec.get("evidence_receipt_sha256")!=ev.get("receipt_sha256") or
                rec.get("delivery_receipt_sha256")!=env.get("receipt_sha256") or
                rec.get("current_sha256")!=env.get("current",{}).get("sha256")):
                continue
            ack={"actor":actor,"delivery_id":delivery_id,
                 "current_sha256":rec["current_sha256"],"event_ids":rec["event_ids"],
                 "event_seq_end":rec["ack_seq"],"challenge":rec["challenge"]}
            if d.validate_ack(env,ack,proof=evidence) is None:
                return True
        except (OSError,KeyError,ValueError,TypeError):
            continue
    return False
def snapshot():
    required_sources()
    repo=bridge.snap(REPO)
    d=delta.Delta()
    events=d.events()
    if not events:raise RuntimeError("EMPTY_SIGNED_EVENT_LOG")
    consumers={}
    for actor,task_id in TASKS.items():
        reply=bridge.poll(task_id)
        if reply.get("status")!="PREPARED_NOT_EXECUTED" or reply.get("provider_invoked") is not False:
            raise RuntimeError("UNEXPECTED_EXECUTION_STATE:"+actor)
        binding=(reply.get("data") or {}).get("context_delivery_binding")
        if not binding or binding!=bridge.delivery_binding(actor,binding["delivery_id"]):
            raise RuntimeError("UNVERIFIED_SIGNED_DELIVERY:"+actor)
        skills=REPO/(".claude/skills" if actor=="CLAUDE" else ".agents/skills")
        count=sum(x.is_dir() and (x/"SKILL.md").is_file() for x in skills.iterdir())
        consumers[actor]={
            "task_id":task_id,"delivery_id":binding["delivery_id"],
            "event_ids":binding["event_ids"],"last_verified_read_seq":d.cursor(actor),
            "provider_delivered":False,"provider_ack":False,
            "local_subscription_cli_ack_observed":observed_local_cli_ack(d,actor),
            "skills_on_disk":count,
            "mcp_config":bridge.mcp_names(REPO,actor),
            "session_binding":"IDE_NATIVE_PANEL_UNVERIFIED"
        }
    return {
       "schema":"TAKY_AGENT_SHARED_CONTEXT_PROJECTION_CANDIDATE_V1",
       "generated_utc":datetime.now(timezone.utc).isoformat(),
       "authority":"DERIVED_NONCANONICAL_NOT_CURRENT",
       "user_outcome":"General Chat TAKY orchestration; Antigravity is IDE/platform, use Claude Code and Codex as subscription-authenticated executors with shared files, memory, skills/MCP/harness.",
       "rules":"Canonical MASTER AI collaboration protocol: ChatGPT orchestrator, Claude Code primary code executor when needed and subscription capacity allows, Codex independent reviewer or usage-justified fallback executor. Never let a skill override authority; respect cost and approval gates.",
       "source_master":{"path":str(MASTER),"sha256":sha(MASTER)},
       "source_handoff":{"path":str(HANDOFF),"sha256":sha(HANDOFF)},
       "source_derived_resume":{"path":str(delta.CURRENT),"sha256":sha(delta.CURRENT),
                                "canonical_owner":False,"canonical_sequence":"UNRESOLVED"},
       "repo":{"path":str(REPO),**repo},
       "signed_events":[{"seq":x["seq"],"event_id":x["event_id"],"text":x["value"]} for x in events],
       "workflow_eol_readiness":workflow_eol_audit(),
       "consumers":consumers,
       "verified_results":{
          "signed_chat_to_drive_to_pc_roundtrip":"PASS",
          "detached_claude_subscription_cli_single_turn":"PASS_NOT_NATIVE_PANEL",
          "codex_live_turn":("LOCAL_CLI_ACK_NOT_PROVIDER_SIGNED"
              if consumers["CODEX"]["local_subscription_cli_ack_observed"]
              else "HOLD_NO_VERIFIED_CODEX_RECEIPT"),
          "native_antigravity_panel_submit":"OPEN_NOT_SUPPORTED_ATTESTED",
          "remote_control_cli_capability":"SUPPORTED_HELP_READONLY_EXISTING_PANEL_NOT_CONNECTED",
          "cli_mcp_tool_listing":"PASS_BUT_IDE_RUNTIME_NOT_PROVED",
          "real_receiver_ack":("LOCAL_CLI_ACK_NOT_PROVIDER_SIGNED"
              if consumers["CLAUDE"]["local_subscription_cli_ack_observed"]
              else "OPEN_AND_FAIL_CLOSED"),
          "provider_signed_receiver_ack":"NOT_ATTESTED",
          "codex_receiver_route":"DIRECT_PYTHON_TAKY2_PREFLIGHT_EXECUTE_CODEX_VERIFY_ONLY_NO_POWERSHELL",
          "manual_powershell_review_preflight_guard":"BOUNDED_35S_LOCAL_TEST_PASS_NOT_CODEX_RECEIVER_PATH",
          "per_actor_local_cli_ack":{a:consumers[a]["local_subscription_cli_ack_observed"] for a in sorted(delta.ACTORS)}
       },
       "reading_instructions":"This is orientation evidence only. Read task-relevant registered authority and latest live repo state before acting. Only a verified, locally witnessed subscription CLI evidence record can advance a derived local cursor; this is NOT provider-signed proof or native Antigravity panel receipt. Prepared deliveries alone are not model ACK. No push/merge/deploy/paid API/reset.",
       "no_new_paid_api":True,
       "no_model_called_by_projection":True
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--check",action="store_true")
    args=p.parse_args()
    state=snapshot()
    if args.check:
        if not OUT.is_file():raise RuntimeError("PROJECTION_NOT_PRESENT")
        existing=json.loads(OUT.read_text(encoding="utf-8"))
        keys=("source_master","source_handoff","source_derived_resume")
        if any(existing[k]["sha256"]!=state[k]["sha256"] for k in keys):
            raise RuntimeError("SOURCE_HASH_DRIFT")
        if existing["repo"]!=state["repo"] or existing["consumers"]!=state["consumers"]:
            raise RuntimeError("REPO_OR_DELIVERY_DRIFT")
        if existing.get("workflow_eol_readiness")!=state["workflow_eol_readiness"]:
            raise RuntimeError("WORKFLOW_OR_SKILL_LAYOUT_DRIFT")
        print(json.dumps({"state":"SOURCE_BOUND_VIEW_VALID","cursor_claude":state["consumers"]["CLAUDE"]["last_verified_read_seq"],
           "cursor_codex":state["consumers"]["CODEX"]["last_verified_read_seq"]},ensure_ascii=False))
    else:
        data=json.dumps(state,ensure_ascii=False,indent=2).encode("utf-8")
        tmp=OUT.with_name(OUT.name+"."+uuid.uuid4().hex+".pending")
        with tmp.open("xb") as f:f.write(data)
        os.replace(tmp,OUT)
        if OUT.read_bytes()!=data:raise RuntimeError("PROJECTION_READBACK_FAILED")
        print(json.dumps({"state":"PROJECTION_WRITTEN_VERIFIED","path":str(OUT),
            "sha256":hashlib.sha256(data).hexdigest(),"size":len(data),
            "provider_ack":False},ensure_ascii=False))
if __name__=="__main__":main()
