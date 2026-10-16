#!/usr/bin/env python3
"""TAKY shared-context delta candidate. NO MODEL CALLS / NO CANONICAL CURRENT.
Builds immutable source-grounded events + per-executor delivery envelopes.
A real receiver ACK cannot advance pointers without separately attested provider receipt.
"""
from __future__ import annotations
import argparse, hashlib, hmac, json, os, pathlib, sys
from contextlib import contextmanager
from datetime import datetime, timezone
import taky_antigravity_bridge_v3_candidate as bridge

COMMON=pathlib.Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON")
DEFAULT_ROOT=COMMON/"04_HISTORY"/"TAKY_CONTEXT_DELTA_CANDIDATE"
SOURCE_DIR=COMMON/"04_HISTORY"/"CLI_BRIDGE_RECEIPTS"
SOURCE_ID="4ba260fdf11342b0b8ece1529e054d3e"
CURRENT=COMMON/"02_CURRENT"/"TAKY_CONVERSATION_RESUME.json"
ACTORS={"CLAUDE","CODEX"}
CLI_ACTOR="CLAUDE"  # retained as the established Claude-only legacy route
EVIDENCE_DIR="receiver_evidence"
EVIDENCE_SCHEMA="TAKY_CLI_RECEIVER_EVIDENCE_V1"
LOCAL_ACK_STATUS="LOCAL_CLI_ACK_NOT_PROVIDER_SIGNED"
AUTH_METHODS={"claude.ai","oauth_token"}
# argv after the executable; fixed, never caller-supplied. Prompt goes through stdin.
CLI_ARGV_TAIL=["-p","--output-format","json","--max-turns","1","--tools","","--strict-mcp-config",
    "--settings","{}","--setting-sources","","--no-session-persistence","--permission-prompts","none"]
RESULT_KEYS={"actor","delivery_id","current_sha256","event_ids","event_seq_end","challenge","status"}
# One no-tool, read-only Codex subscription execution. Never use an API key fallback.
CODEX_CLI_ARGV_TAIL=["exec","--sandbox","read-only","--ephemeral",
    "--ignore-user-config","--strict-config","--json",
    "--skip-git-repo-check","-c",'model_reasoning_effort="low"',
    "-c",'web_search="disabled"',
    "--disable","shell_tool","--disable","unified_exec",
    "--disable","shell_snapshot","--disable","multi_agent",
    "--disable","apps","--disable","remote_plugin","-"]
CODEX_AUTH_METHOD="chatgpt"
def sha(v):return hashlib.sha256(v).hexdigest()
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def signed(obj):
    fields={k:v for k,v in obj.items() if k not in ("receipt_sha256","receipt_mac")}
    digest=sha(canon(fields))
    return hmac.compare_digest(str(obj.get("receipt_sha256","")),digest) and hmac.compare_digest(
        str(obj.get("receipt_mac","")),bridge.mac(digest))
def validate_cli_output(stdout,envelope,challenge):
    """Return (error,session_id,result_text). Only an exact, explicit ACK passes."""
    bad=lambda why:(why,None,None)
    if not isinstance(challenge,str) or len(challenge)<32 or any(c not in "0123456789abcdef" for c in challenge):
        return bad("CHALLENGE_INVALID")
    try:out=json.loads(stdout)
    except (TypeError,ValueError):return bad("CLI_OUTPUT_NOT_JSON")
    if (not isinstance(out,dict) or out.get("type")!="result" or out.get("subtype")!="success" or
        out.get("is_error") is not False):return bad("CLI_ENVELOPE_NOT_SUCCESS")
    session=out.get("session_id")
    if not isinstance(session,str) or not session.strip():return bad("CLI_SESSION_ID_MISSING")
    text=out.get("result")
    if not isinstance(text,str):return bad("CLI_RESULT_MISSING")
    try:res=json.loads(text)
    except ValueError:return bad("CLI_RESULT_NOT_JSON")
    if not isinstance(res,dict) or set(res)!=RESULT_KEYS:return bad("CLI_RESULT_SHAPE_INVALID")
    seq=res["event_seq_end"]
    if (res["status"]!="ACK" or res["actor"]!=envelope["actor"] or
        res["delivery_id"]!=envelope["delivery_id"] or
        res["current_sha256"]!=envelope["current"]["sha256"] or
        res["event_ids"]!=envelope["event_ids"] or isinstance(seq,bool) or
        seq!=envelope["event_seq_end"] or res["challenge"]!=challenge):
        return bad("CLI_RESULT_MISMATCH_OR_NOT_ACK")
    return None,session,text
def validate_codex_cli_output(stdout,envelope,challenge):
    """Validate exact ACK from Codex JSONL, including thread/turn completion."""
    bad=lambda why:(why,None,None)
    if not isinstance(challenge,str) or len(challenge)<32 or any(c not in "0123456789abcdef" for c in challenge):
        return bad("CHALLENGE_INVALID")
    if not isinstance(stdout,str) or not stdout.strip():
        return bad("CODEX_OUTPUT_EMPTY")
    thread_ids=[]; replies=[]; turn_completed=0
    try:
        for line in stdout.splitlines():
            if not line.strip():continue
            event=json.loads(line)
            if not isinstance(event,dict):return bad("CODEX_JSONL_EVENT_INVALID")
            typ=event.get("type")
            if typ in ("error","turn.failed"):return bad("CODEX_TURN_FAILED")
            if typ=="thread.started":
                thread_ids.append(event.get("thread_id"))
            if typ=="turn.completed":
                turn_completed+=1
            if typ in ("item.started","item.updated","item.completed"):
                item=event.get("item") or {}
                if not isinstance(item,dict):return bad("CODEX_ITEM_INVALID")
                if item.get("type") in ("command_execution","mcp_tool_call","web_search","tool_call"):
                    return bad("CODEX_TOOL_ACTIVITY_FORBIDDEN")
                if typ=="item.completed" and item.get("type")=="agent_message":
                    replies.append(item.get("text"))
    except (ValueError,TypeError):
        return bad("CODEX_JSONL_NOT_JSON")
    if len(thread_ids)!=1 or not isinstance(thread_ids[0],str) or not thread_ids[0].strip():
        return bad("CODEX_SESSION_ID_MISSING")
    if turn_completed!=1 or len(replies)!=1 or not isinstance(replies[0],str):
        return bad("CODEX_REPLY_OR_TURN_INCOMPLETE")
    result_text=replies[0]
    try:res=json.loads(result_text)
    except ValueError:return bad("CODEX_RESULT_NOT_JSON")
    if not isinstance(res,dict) or set(res)!=RESULT_KEYS:
        return bad("CODEX_RESULT_SHAPE_INVALID")
    if (res["status"]!="ACK" or res["actor"]!=envelope["actor"] or
        res["delivery_id"]!=envelope["delivery_id"] or
        res["current_sha256"]!=envelope["current"]["sha256"] or
        res["event_ids"]!=envelope["event_ids"] or
        isinstance(res["event_seq_end"],bool) or
        res["event_seq_end"]!=envelope["event_seq_end"] or res["challenge"]!=challenge):
        return bad("CODEX_RESULT_MISMATCH_OR_NOT_ACK")
    return None,thread_ids[0],result_text
GOVERNED_CODEX_ROUTE=["TAKY_MODEL_REVIEW.ps1","CODEX_VERIFY_ONLY"]
GOVERNED_CODEX_PREFIX="[TAKY_DRY_RUN_PLAN] preflight completed"

def validate_codex_governed_output(stdout,envelope,challenge):
    """Read the existing TAKY2 governed review envelope, NOT a synthetic Codex session."""
    bad=lambda why:(why,None,None)
    if not isinstance(stdout,str):return bad("CODEX_GOVERNED_OUTPUT_NOT_TEXT")
    raw=stdout.replace("\r\n","\n").strip()
    prefix=GOVERNED_CODEX_PREFIX+"\n"
    if not raw.startswith(prefix):return bad("CODEX_GOVERNED_PREFLIGHT_NOT_ATTESTED")
    try:body=json.loads(raw[len(prefix):])
    except (TypeError,ValueError):return bad("CODEX_GOVERNED_ENVELOPE_NOT_JSON")
    if (not isinstance(body,dict) or body.get("allowed") is not True or
        body.get("state")!="EXECUTOR_RETURNED_UNVERIFIED" or
        "verification_state" in body):
        return bad("CODEX_GOVERNED_EXECUTION_NOT_ALLOWED")
    rid=body.get("receipt_id")
    if not isinstance(rid,str) or not rid.startswith("pf:external-review-"):
        return bad("CODEX_GOVERNED_RECEIPT_ID_INVALID")
    parts=rid.split(":")
    task_part=parts[1][len("external-review-"):] if len(parts)==3 else ""
    nonce=parts[2] if len(parts)==3 else ""
    if (len(parts)!=3 or len(task_part)!=32 or len(nonce)!=16 or
        any(ch not in "0123456789abcdef" for ch in task_part+nonce)):
        return bad("CODEX_GOVERNED_RECEIPT_ID_INVALID")
    result=body.get("result")
    if (not isinstance(result,dict) or type(result.get("returncode")) is not int
        or result["returncode"]!=0 or not isinstance(result.get("stdout"),str)):
        return bad("CODEX_GOVERNED_MODEL_NOT_SUCCESSFUL")
    response=result["stdout"].strip()
    try:obj=json.loads(response)
    except (TypeError,ValueError):return bad("CODEX_RECEIPT_RESPONSE_NOT_JSON")
    if not isinstance(obj,dict) or set(obj)!=RESULT_KEYS:
        return bad("CODEX_RECEIPT_RESPONSE_SHAPE_INVALID")
    if (obj["status"]!="ACK" or obj["actor"]!=envelope["actor"] or
        obj["delivery_id"]!=envelope["delivery_id"] or
        obj["current_sha256"]!=envelope["current"]["sha256"] or
        obj["event_ids"]!=envelope["event_ids"] or
        type(obj["event_seq_end"]) is not int or obj["event_seq_end"]!=envelope["event_seq_end"] or
        obj["challenge"]!=challenge):
        return bad("CODEX_GOVERNED_ACK_MISMATCH")
    return None,"TAKY2_RECEIPT:"+rid,response

def write_once(file,obj):
    bridge.write_new(file,obj)
def write_cursor(file,seq):
    temp=file.with_name(file.name+".new")
    if temp.exists():raise RuntimeError("UNRESOLVED_CURSOR_TEMP")
    pointer={"schema":"TAKY_CONTEXT_CURSOR_CANDIDATE_V1",
        "last_ack_seq":seq,"changed_utc":now(),"authority":"DERIVED_ONLY"}
    bridge.seal_receipt(pointer)
    bridge.write_new(temp,pointer)
    os.replace(temp,file)
@contextmanager
def lock(root):
    root.mkdir(parents=True,exist_ok=True)
    # Local process lock; cloud-side concurrency is not guaranteed.
    path=bridge.LOCAL_BRIDGE_DIR/"delta_candidate.lock"
    path.parent.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise RuntimeError("DELTA_WORKER_CONCURRENT_OR_STALE_LOCK")
    try:
        os.close(fd)
        yield
    finally:path.unlink(missing_ok=True)
class Delta:
    def __init__(self,root=DEFAULT_ROOT,current=CURRENT,src=SOURCE_DIR):
        self.root=pathlib.Path(root);self.current=pathlib.Path(current)
        self.src=pathlib.Path(src)
    def eventfiles(self):return sorted((self.root/"events").glob("*.json"))
    def events(self):
        items=[read(f) for f in self.eventfiles()]
        if [x["seq"] for x in items]!=list(range(1,len(items)+1)):
            raise RuntimeError("NONMONOTONIC_EVENT_SERIES")
        for item in items:
            if not signed(item):raise RuntimeError("EVENT_SIGNATURE_INVALID")
        return items
    def source(self):
        att=self.src/(SOURCE_ID+".attestation.json")
        original=self.src/(SOURCE_ID+".json")
        a=read(att);raw=original.read_bytes()
        if not signed(a) or a["source_receipt_sha256"]!=sha(raw):
            raise RuntimeError("SOURCE_ATTESTATION_NOT_VERIFIED")
        if a.get("status")!="E2E_RESPONSE_AND_REQUEST_BOUND_PASS":
            raise RuntimeError("SOURCE_STATUS_INVALID")
        return a,sha(att.read_bytes())
    def seed(self):
        with lock(self.root):
            a,proof_sha=self.source()
            eventid=sha(canon({"source_file_sha256":proof_sha,"source_task_id":SOURCE_ID,"event_type":"VERIFIED_EXECUTION"}))[:24]
            existing=self.events()
            if any(e["event_id"]==eventid for e in existing):
                return {"status":"ALREADY_PRESENT","event_id":eventid,"event_count":len(existing)}
            seq=len(existing)+1
            e={"schema":"TAKY_CONTEXT_DELTA_EVENT_V1","seq":seq,"event_id":eventid,
               "event_type":"VERIFIED_EXECUTION","source_task_id":SOURCE_ID,
               "source_receipt_attestation_sha256":proof_sha,
               "value":"Claude detached CLI roundtrip verified; native Antigravity panel NOT bound.",
               "authority":"NONCANONICAL_EVIDENCE_ONLY","generated_utc":now()}
            bridge.seal_receipt(e)
            write_once(self.root/"events"/(f"{seq:06d}.json"),e)
            return {"status":"APPENDED","event_id":eventid,"event_count":seq}
    def cursor(self,actor):
        if actor not in ACTORS:raise ValueError("UNKNOWN_ACTOR")
        p=self.root/"cursors"/(actor+".json")
        if not p.is_file():return 0
        obj=read(p)
        if not signed(obj) or obj.get("schema")!="TAKY_CONTEXT_CURSOR_CANDIDATE_V1":
            raise RuntimeError("CURSOR_SIGNATURE_INVALID")
        seq=obj.get("last_ack_seq")
        if not isinstance(seq,int) or isinstance(seq,bool) or seq<0 or seq>len(self.events()):
            raise RuntimeError("CURSOR_SEQUENCE_INVALID")
        return seq
    def current_digest(self):
        raw=self.current.read_bytes()
        obj=json.loads(raw)
        if obj.get("authority_status")!="DERIVED_NON_AUTHORITY":
            raise RuntimeError("CURRENT_SOURCE_AUTHORITY_UNEXPECTED")
        return {"path":str(self.current),"sha256":sha(raw),"status":"DERIVED_NON_AUTHORITY",
                "canonical_sequence":"UNRESOLVED"}
    def delivery(self,actor):
        with lock(self.root):
            if actor not in ACTORS:raise ValueError("UNKNOWN_ACTOR")
            all_events=self.events();seq=self.cursor(actor);unread=[e for e in all_events if e["seq"]>seq]
            current=self.current_digest()
            if not unread:
                return {"status":"NO_UNREAD_EVENTS","actor":actor,"last_ack_seq":seq,
                        "canonical_current":"UNRESOLVED"}
            ids=[e["event_id"] for e in unread]
            claim=sha(canon([actor,seq,current["sha256"],ids]))[:24]
            file=self.root/"deliveries"/actor/(claim+".json")
            if file.exists():
                obj=read(file)
                if not signed(obj):raise RuntimeError("DELIVERY_SIGNATURE_INVALID")
                return {"status":"ALREADY_PREPARED","actor":actor,"file":str(file),
                        "delivery_id":claim,"unread_count":len(ids)}
            high=unread[-1]["seq"]
            envelope={"schema":"TAKY_CONTEXT_DELIVERY_V1","delivery_id":claim,"actor":actor,
                "source_authority":"NONCANONICAL_DERIVED_SNAPSHOT","current":current,
                "last_acked_seq":seq,"event_seq_end":high,"event_ids":ids,
                "events":[{"seq":x["seq"],"event_id":x["event_id"],"value":x["value"],
                           "source_task_id":x["source_task_id"],
                           "source_receipt_attestation_sha256":x["source_receipt_attestation_sha256"]}
                          for x in unread],
                "created_utc":now(),"required_ack":"MATCH_SHA_SEQUENCE_AND_EVENT_IDS_PLUS_PROVIDER_PROOF",
                "delivery_state":"PENDING_RECEIVER_ACK","provider_invoked":False}
            bridge.seal_receipt(envelope)
            write_once(file,envelope)
            return {"status":"PREPARED_NOT_DELIVERED_TO_PROVIDER","actor":actor,"file":str(file),
                    "delivery_id":claim,"unread_count":len(ids),"last_ack_seq":seq,
                    "event_seq_end":high,"source_current_sha256":current["sha256"]}
    def _ack_failure(self,envelope,ack,proof,simulation):
        if not signed(envelope):return "DELIVERY_SIGNATURE_INVALID",None
        if (ack.get("delivery_id")!=envelope["delivery_id"] or
            ack.get("actor")!=envelope["actor"] or
            ack.get("current_sha256")!=envelope["current"]["sha256"] or
            ack.get("event_ids")!=envelope["event_ids"] or
            ack.get("event_seq_end")!=envelope["event_seq_end"]):
            return "ACK_CONTEXT_OR_EVENTS_MISMATCH",None
        if simulation:return None,None
        # A caller-supplied boolean/object is NOT proof: only a path to a signed local CLI
        # evidence record under the trusted evidence directory is examined.
        return self._check_proof(envelope,ack,proof)
    def validate_ack(self,envelope,ack,proof=None,simulation=False):
        return self._ack_failure(envelope,ack,proof,simulation)[0]
    def _check_proof(self,envelope,ack,proof):
        if not isinstance(proof,(str,os.PathLike)):return "RECEIVER_PROVIDER_PROOF_UNVERIFIED",None
        actor=envelope["actor"]
        if actor not in ACTORS:return "ACTOR_UNSUPPORTED_NO_WORKING_INVOCATION_PATH",None
        did=envelope["delivery_id"]
        try:
            path=pathlib.Path(proof)
            if path.is_symlink():return "PROOF_PATH_UNTRUSTED",None
            resolved=path.resolve(strict=True)
            base=(self.root/EVIDENCE_DIR/actor).resolve()
            if resolved.parent!=base or resolved.name!=did+".json" or not resolved.is_file():
                return "PROOF_PATH_UNTRUSTED",None
            raw=resolved.read_bytes();ev=json.loads(raw.decode("utf-8-sig"))
        except (OSError,ValueError):return "PROOF_UNREADABLE",None
        if not isinstance(ev,dict) or not signed(ev) or ev.get("schema")!=EVIDENCE_SCHEMA:
            return "EVIDENCE_SIGNATURE_INVALID",None
        bound=(ev.get("actor")==envelope["actor"] and ev.get("delivery_id")==did and
            ev.get("delivery_receipt_sha256")==envelope["receipt_sha256"] and
            ev.get("current_sha256")==envelope["current"]["sha256"] and
            ev.get("event_ids")==envelope["event_ids"] and
            ev.get("event_seq_end")==envelope["event_seq_end"] and
            ack.get("challenge")==ev.get("challenge"))
        if not bound:return "EVIDENCE_BINDING_MISMATCH",None
        stdout=ev.get("stdout_raw")
        expected_argv=CLI_ARGV_TAIL if actor=="CLAUDE" else GOVERNED_CODEX_ROUTE
        if (not isinstance(stdout,str) or ev.get("stdout_sha256")!=sha(stdout.encode("utf-8")) or
            ev.get("provider_signed") is not False or ev.get("returncode")!=0 or
            ev.get("argv_tail")!=expected_argv or ev.get("status")!=LOCAL_ACK_STATUS):
            return "EVIDENCE_OUTPUT_BINDING_INVALID",None
        auth=ev.get("auth")
        if not isinstance(auth,dict) or auth.get("api_keys_present") is not False:
            return "EVIDENCE_AUTH_INVALID",None
        if actor=="CLAUDE":
            if (auth.get("auth_method") not in AUTH_METHODS or
                auth.get("api_provider")!="firstParty" or auth.get("logged_in") is not True):
                return "EVIDENCE_AUTH_INVALID",None
            failure,session,result=validate_cli_output(stdout,envelope,ev.get("challenge"))
        else:
            if (auth.get("auth_method")!=CODEX_AUTH_METHOD or
                auth.get("api_provider")!="openai" or auth.get("logged_in") is not True):
                return "EVIDENCE_AUTH_INVALID",None
            failure,session,result=validate_codex_governed_output(stdout,envelope,ev.get("challenge"))
            rid=session.split("TAKY2_RECEIPT:",1)[-1] if session else ""
            if (not failure and (ev.get("governed_receipt_id")!=rid or
                    ev.get("execution_route")!="TAKY2_CODEX_VERIFY_ONLY" or
                    ev.get("native_panel_bound") is not False)):
                return "CODEX_GOVERNED_RECEIPT_BINDING_INVALID",None
        if failure:return failure,None
        if ev.get("session_id")!=session or ev.get("result_raw")!=result:
            return "EVIDENCE_OUTPUT_BINDING_INVALID",None
        return None,{"evidence":ev,"file_sha256":sha(raw)}
    def receive_proof(self,actor,ack,proof,max_age=900):
        """Commit an actor cursor only from locally witnessed, signed CLI evidence."""
        if actor not in ACTORS:raise ValueError("UNKNOWN_ACTOR")
        did=str(ack.get("delivery_id",""))
        if len(did)!=24 or any(c not in "0123456789abcdef" for c in did):
            return {"status":"HOLD","error":"DELIVERY_ID_INVALID"}
        with lock(self.root):
            p=self.root/"deliveries"/actor/(did+".json")
            if not p.is_file():return {"status":"HOLD","error":"DELIVERY_NOT_FOUND"}
            e=read(p)
            failure,bundle=self._ack_failure(e,ack,proof,False)
            if failure:return {"status":"HOLD","error":failure}
            ev=bundle["evidence"]
            try:
                age=(datetime.now(timezone.utc)-datetime.fromisoformat(ev["finished_utc"])).total_seconds()
                live=self.current_digest()["sha256"]
            except (KeyError,ValueError,OSError,RuntimeError):
                return {"status":"HOLD","error":"EVIDENCE_TIME_OR_CURRENT_UNVERIFIABLE"}
            if age<0 or age>max_age:return {"status":"HOLD","error":"EVIDENCE_STALE"}
            if live!=e["current"]["sha256"]:return {"status":"HOLD","error":"STALE_CURRENT"}
            if self.cursor(actor)!=e["last_acked_seq"]:
                return {"status":"HOLD","error":"POINTER_ALREADY_ADVANCED"}
            ackfile=self.root/"ack_receiver"/actor/(did+".json")
            if ackfile.exists():
                rec=read(ackfile)  # crash-resume only when the record is the same evidence
                if not signed(rec) or rec.get("evidence_file_sha256")!=bundle["file_sha256"]:
                    return {"status":"HOLD","error":"REPLAY_OR_ACK_RECORD_CONFLICT"}
            else:
                rec={"schema":"TAKY_CONTEXT_RECEIVER_ACK_CANDIDATE_V1","actor":actor,
                    "delivery_id":did,"delivery_receipt_sha256":e["receipt_sha256"],
                    "current_sha256":live,"event_ids":e["event_ids"],"ack_seq":e["event_seq_end"],
                    "challenge":ev["challenge"],"session_id":ev["session_id"],
                    "evidence_file_sha256":bundle["file_sha256"],
                    "evidence_receipt_sha256":ev["receipt_sha256"],
                    "status":LOCAL_ACK_STATUS,"provider_signed":False,"native_panel_bound":False,
                    "trust_boundary":"LOCAL_HOST_HMAC_ONLY_HOLDER_OF_HOST_KEY_CAN_FORGE",
                    "authority":"NONCANONICAL_EVIDENCE_ONLY","timestamp":now()}
                bridge.seal_receipt(rec)
                write_once(ackfile,rec)  # ack record is durable BEFORE the cursor moves
            write_cursor(self.root/"cursors"/(actor+".json"),e["event_seq_end"])
            return {"status":LOCAL_ACK_STATUS,"provider_signed":False,"ack_seq":e["event_seq_end"]}
    def simulation_ack(self,actor,ack):
        """Only for tests using a temporary workspace; NEVER advances live pointers."""
        if self.root.resolve()==DEFAULT_ROOT.resolve():
            return {"status":"HOLD_REAL_PROVIDER_ACK_REQUIRED"}
        with lock(self.root):
            p=self.root/"deliveries"/actor/(ack["delivery_id"]+".json")
            e=read(p)
            failure=self.validate_ack(e,ack,simulation=True)
            if failure:return {"status":"HOLD","error":failure}
            if self.cursor(actor)!=e["last_acked_seq"]:
                return {"status":"HOLD","error":"POINTER_ALREADY_ADVANCED"}
            write_cursor(self.root/"cursors"/(actor+".json"),e["event_seq_end"])
            result={"schema":"TAKY_CONTEXT_ACK_EVENT_CANDIDATE_V1",
                    "actor":actor,"delivery_id":e["delivery_id"],
                    "event_ids":e["event_ids"],"ack_seq":e["event_seq_end"],
                    "simulation":True,"authority":"TEST_ONLY","timestamp":now()}
            bridge.seal_receipt(result)
            write_once(self.root/"ack_simulated"/actor/(e["delivery_id"]+".json"),result)
            return {"status":"SIMULATED_ACK_PASS_NOT_REAL_DELIVERY","ack_seq":e["event_seq_end"]}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["seed","prepare","status"])
    ap.add_argument("--actor",choices=sorted(ACTORS),default="CLAUDE")
    args=ap.parse_args()
    d=Delta()
    if args.mode=="seed":ret=d.seed()
    elif args.mode=="prepare":ret=d.delivery(args.actor)
    else:ret={"schema":"TAKY_CONTEXT_DELTA_CANDIDATE_V1","events":len(d.events()),
              "pointers":{a:d.cursor(a) for a in sorted(ACTORS)},
              "source_current":d.current_digest(),
              "real_receiver_ack_attested":False,"provider_invocations_enabled":False}
    print(json.dumps(ret,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
