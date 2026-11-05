#!/usr/bin/env python3
"""Private, bounded snapshot for TAKY Mobile admin server-only env.

Generated only from the already-derived Workbench projection. NO RAW chat text,
filesystem paths, source tokens, credentials, or write access to TAKY CURRENT.
This does not configure Netlify environment or deploy.
"""
import json
import re
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\00_CONTROL")
ROUTED_HISTORY=Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\04_HISTORY")
PREPARED_TASK_INBOX=Path(r"F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\01_INBOX\AI_TASKS")
TAKY_CODE_REPO=Path(r"D:\Git PWA\TAKY")
SRC=ROOT/"TAKY_CONVERSATION_PROGRESS_INDEX.json"
TOPIC=ROOT/"CONVERSATION_2026_10_ONWARD_TOPIC_INDEX.json"
KERNEL=Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH\TAKY2\state\runtime.json")
OUT=ROOT/"PRIVATE_ADMIN_EXPORT"/"TAKY_ADMIN_PROGRESS_ENV_PAYLOAD.json"
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_attested_kernel():
 # Existing TAKY2 HMAC + rollback-anchor verification; NEVER create/read out a key in reports.
 import sys
 orchard=str(KERNEL.parents[2])
 if orchard not in sys.path:sys.path.insert(0,orchard)
 from TAKY2.state_store import load_bundle, RUNTIME_KEY_PATH
 if not RUNTIME_KEY_PATH.is_file():raise ValueError("SIGNED_KERNEL_KEY_MISSING_HOLD")
 key=RUNTIME_KEY_PATH.read_bytes()
 if len(key)<32:raise ValueError("SIGNED_KERNEL_KEY_INVALID_HOLD")
 _,runtime,_=load_bundle(runtime_key=key)
 return runtime

def current_source_verified(data,project):
 # A matching SHA attests to the WORKBENCH project projection, never global CURRENT authority.
 if not re.fullmatch(r"[A-Za-z0-9_-]{2,60}",project or ""):return False
 file=ROOT.parent/"10_PROJECTS"/project/"PROJECT_CURRENT.json"
 if not file.is_file():return False
 known={str(e.get("path","")).replace("\\","/").lower():e.get("sha256","")
        for e in data.get("source_manifest",[]) if isinstance(e,dict)}
 return known.get(str(file).replace("\\","/").lower())==digest(file)
def clean(v,size=300):
 text=str(v or "")[:size]
 # Source-supplied task titles and alert notes may contain private local paths.
 # Do not expose even a partial path through the private admin data route.
 if re.search(r"(?i)(?:[A-Z]:[\\/]|\\\\[A-Za-z0-9_.-]+[\\/]|/home/|/Users/|Bearer\\s+|(?:api[_-]?key|secret|password)\\s*[:=])",text):
  return "PRIVATE_TEXT_REDACTED"
 return text
QA_SOURCE=TAKY_CODE_REPO/".local"/"family-qa"/"latest-quick.json"
def read_local_qa(path=QA_SOURCE):
 # Read exactly the existing local synthetic QA receipt, never real family data.
 # No test is triggered; an old receipt remains historical evidence only.
 if path.is_symlink() or not path.is_file() or path.stat().st_size>250000:
  return None
 try:
  raw=path.read_bytes()
  d=json.loads(raw.decode("utf-8"))
 except (OSError,UnicodeError,ValueError):return None
 if (not isinstance(d,dict) or d.get("contract")!="TAKY_FAMILY_PERIODIC_QA_V1"
     or d.get("mode") not in ("quick","deep")
     or d.get("productionVerified") is not False
     or not isinstance(d.get("statuses"),dict)
     or not isinstance(d.get("gaps"),list)):return None
 counts=d["statuses"]
 keys=("passed","failed","blocked","openGaps")
 if (any(type(counts.get(k)) is not int or not 0<=counts[k]<=10000 for k in keys)
     or len(d["gaps"])>100 or counts["openGaps"]!=len(d["gaps"])
     or not isinstance(d.get("results"),list) or
     len(d["results"])!=counts["passed"]+counts["failed"]+counts["blocked"]):
  return None
 observed={"PASS":0,"FAIL":0,"BLOCKED":0}
 for row in d["results"]:
  if not isinstance(row,dict):return None
  st=row.get("state")
  if st=="PASS":observed["PASS"]+=1
  elif st in ("BLOCKED","NOT_RUN"):observed["BLOCKED"]+=1
  else:observed["FAIL"]+=1
 if (observed["PASS"]!=counts["passed"] or
     observed["FAIL"]!=counts["failed"] or
     observed["BLOCKED"]!=counts["blocked"]):return None
 gaps=[]
 for x in d["gaps"]:
  if not isinstance(x,dict):continue
  ident=x.get("id"); priority=x.get("priority"); area=x.get("area")
  if (not isinstance(ident,str) or not re.fullmatch(r"[a-z0-9-]{3,95}",ident)
      or priority not in ("P0","P1","P2")
      or not isinstance(area,str) or not re.fullmatch(r"[A-Z0-9/-]{1,35}",area)):continue
  gaps.append({"id":ident,"priority":priority,"area":area})
 if len(gaps)!=len(d["gaps"]) or len({x["id"] for x in gaps})!=len(gaps):
  return None
 return {"source":"LOCAL_SYNTHETIC_QA_RECEIPT_NOT_PRODUCTION",
         "mode":d["mode"],"finishedAt":clean(d.get("finishedAt"),45),
         "sourceSha256":hashlib.sha256(raw).hexdigest(),
         "verdict":clean(d.get("verdict"),70),
         "passed":counts["passed"],
         "failed":counts["failed"],
         "blocked":counts["blocked"],
         "openGaps":counts["openGaps"],
         "openP0":sum(x["priority"]=="P0" for x in gaps),
         "gaps":gaps,"productionVerified":False,
         "independentUserOutcomeVerified":False}
def build(data,qa=None):
 if data.get("schema")!="TAKY_CONVERSATION_PROGRESS_PROJECTION_V1" or data.get("safe_to_publish_to_public_app") is not False:
  raise ValueError("INVALID_PRIVATE_PROGRESS_SOURCE")
 projects=[{"id":clean(p.get("project"),50),"registered":clean(p.get("registry_status"),40),
     "current":clean(p.get("current_status"),40),"signal":clean(p.get("progress_signal"),75),
     "localTrackedWipObserved":(p.get("local_activity") or {}).get("tracked_wip_observed") is True,
     "localTrackedChangedFiles":min(100000,int((p.get("local_activity") or {}).get("tracked_changed_files") or 0)),
     "workRegistrationGap":p.get("work_registration_gap") is True,
     "currentWorkId":clean((p.get("current_work_link") or {}).get("id"),90),
     "currentWorkRegistration":clean((p.get("current_work_link") or {}).get("registration"),45),
     "currentWorkVerified":False,
     "currentWorkPendingGates":min(100,int((p.get("current_work_link") or {}).get("pending_gate_count") or 0)),
     "currentWorkSourceVerified":current_source_verified(data,p.get("project")),
     "activityEvidence":"GIT_TRACKED_WIP_ONLY_NOT_TASK_OR_DONE_PROOF",
     "workCount":int(p.get("work_count") or 0),"historicalChats":len(p.get("historical_chats") or []),
     "relayCandidates":len(p.get("relay_events") or []),
     "latestCodeAt":clean((p.get("repo_evidence") or {}).get("head_date"),45),
     "currentProjectionShaMatched":current_source_verified(data,p.get("project"))}
     for p in data["projects"]]
 work=[]
 for x in data["work_items"]:
  receipts=x.get("receipts") or []
  if not isinstance(receipts,list):raise ValueError("INVALID_RECEIPT_COLLECTION")
  prepared_states=("PREPARED_NOT_EXECUTED","PREVIEW_ONLY_NOT_EXECUTED")
  claimed=sum(1 for r in receipts if isinstance(r,dict) and r.get("model_called") is True)
  prepared=sum(1 for r in receipts if isinstance(r,dict) and
       r.get("model_called") is not True and r.get("reported_status") in prepared_states)
  no_model=sum(1 for r in receipts if isinstance(r,dict) and
       r.get("model_called") is False and r.get("reported_status") not in prepared_states)
  work.append({"id":clean(x.get("work_id"),90),"project":clean(x.get("project"),50),
   "title":clean(x.get("title"),300),"status":clean(x.get("registry_status"),40),
   "executor":clean(x.get("executor"),60),"reviewer":clean(x.get("reviewer"),60),
   "receiptCount":int(x.get("receipt_count") or 0),"outputCount":len(x.get("output_refs") or []),
   "lastReceipt":clean(x.get("latest_receipt"),70),"verified":x.get("execution_verified") is True,
   "preparedCount":prepared,"noModelCount":no_model,"callClaimCount":claimed,
   "unclassifiedReceiptCount":max(0,len(receipts)-prepared-no_model-claimed),
   "chatLinked":x.get("chat_source_link") in ("PROVEN","VERIFIED"),
   "evidenceState":"DERIVED_RECORD_NOT_INDEPENDENT_EXECUTION_PROOF",
   "lastObserved":clean(x.get("last_observed"),45)})
 alerts=[{"kind":clean(x.get("type"),100),"project":clean(x.get("project"),50),
   "workId":clean(x.get("work_id"),90),"note":clean(x.get("reason"),200)} for x in data["alerts"]]
 c=data["counts"]
 return {"schema":"TAKY_MOBILE_ADMIN_PROGRESS_SNAPSHOT_V1",
  "generatedAt":datetime.now(timezone.utc).isoformat(),
  "counts":{"projects":len(projects),"work":len(work),"blocked":c.get("blocked",0),
     "review":c.get("review",0),"open":c.get("open",0),"verified":c.get("independently_verified_completion",0)},
  "coverage":{"historicalChats":25,"octoberNativeChats":data["source_scope"].get("oct_native_chat_count",0)},
  "projects":projects,"work":work,"alerts":alerts,
  "qa":qa if isinstance(qa,dict) else None}
def _verified_routed_receipt_id(work, kernel):
 """Bind only the existing registered output, never task-name or fuzzy similarity."""
 work_id=work.get("work_id")
 task=work.get("task_id")
 if (not isinstance(task,str) or not re.fullmatch(r"[0-9a-f]{32}",task)
     or work_id!="TAKY-CHAT-"+task):return None
 expected=ROUTED_HISTORY/("TAKY_ROUTED_"+task+".json")
 references=work.get("output_refs")
 if not isinstance(references,list):return None
 # The WORKBENCH source index is a bounded reference, not authority over paths.
 refs=[r for r in references if isinstance(r,dict)
       and r.get("path")==str(expected) and r.get("exists") is True]
 if len(refs)!=1 or not expected.is_file() or expected.is_symlink():return None
 size=expected.stat().st_size
 if size<=0 or size>180000 or refs[0].get("size")!=size:return None
 try:
  routed=json.loads(expected.read_text(encoding="utf-8-sig"))
 except (OSError,UnicodeError,ValueError):return None
 if not isinstance(routed,dict) or routed.get("task_id")!=task:return None
 if "work_id" in routed and routed.get("work_id")!=work_id:return None
 if routed.get("executor")!=work.get("executor"):return None
 signed=routed.get("taky2_signed_receipt_id")
 if not isinstance(signed,str) or not re.fullmatch(
     r"pf:external-review-"+task+r":[a-f0-9]{16}",signed):return None
 if routed.get("taky2_receipt_id") not in (None,signed):return None
 if routed.get("signed_readback_state") not in (
     "CLI_RETURNED_UNVERIFIED","OUTCOME_UNKNOWN","EXECUTOR_RETURNED_UNVERIFIED"):
  return None
 receipt=kernel["preflight_receipts"].get(signed)
 if not isinstance(receipt,dict) or receipt.get("task_id")!="external-review-"+task:return None
 expected_action="verify:codex-packet" if work.get("executor")=="Codex" else "review:external-model"
 if receipt.get("action_id")!=expected_action:return None
 if not isinstance(kernel["execution_calls"].get(signed),dict):return None
 return signed


def _unbound_execution_class(work):
 """Classify only evidence recorded in the registered WORKBENCH projection.
 Do not infer that an absent signed receipt proves no external model was called.
 """
 if not isinstance(work,dict):return "WORK_ID_NOT_IN_SOURCE_PROJECTION"
 receipts=work.get("receipts")
 outputs=work.get("output_refs")
 if not isinstance(receipts,list) or not isinstance(outputs,list):
  return "SOURCE_RECEIPT_COLLECTION_UNTRUSTED"
 statuses=[r.get("reported_status") for r in receipts if isinstance(r,dict)]
 if ("FAILED" in statuses or "OUTCOME_UNKNOWN" in statuses or
     work.get("registry_status")=="BLOCKED" and outputs):
  return "FAILURE_RECORDED_BUT_SIGNED_EXECUTION_LINK_MISSING"
 if not outputs and statuses and all(s in
     ("PREPARED_NOT_EXECUTED","PREVIEW_ONLY_NOT_EXECUTED") for s in statuses):
  return "PREPARATION_PREVIEW_ONLY_OBSERVED"
 return "NO_SIGNED_EXECUTION_LINK_RECONCILE_SOURCE"

def _native_work_topic_counts(topic):
 """Only a preserved native-export index with explicit work-id matches qualifies.
 These are index-level source observations, not full-account coverage.
 """
 if (topic.get("source_coverage")!="ONLY_AUTHENTICATED_NATIVE_EXPORT_FILES_IN_LOCAL_INBOX"
     or not topic.get("chats")):
  return {}
 manifest=topic.get("original_export_sources")
 if not isinstance(manifest,list) or not any(isinstance(x,dict) and
     x.get("state")=="SOURCE_PARSED" for x in manifest):
  return {}
 # The derived topic, native chat, and the actual indexed message must agree.
 # A free-floating topic label or forged work link does not establish provenance.
 chat_index={c.get("chat_id"):c for c in topic["chats"]
             if isinstance(c,dict) and isinstance(c.get("chat_id"),str)}
 message_pairs=set()
 for chat_id,chat in chat_index.items():
  for event in chat.get("links") or []:
   if not isinstance(event,dict):continue
   if not isinstance(event.get("topic_ids"),list) or not isinstance(event.get("work_ids"),list):continue
   for topic_id in event["topic_ids"]:
    for work_id in event["work_ids"]:
     if isinstance(topic_id,str) and isinstance(work_id,str):
      message_pairs.add((chat_id,topic_id,work_id))
 counts={}
 for t in topic["topics"]:
  if not isinstance(t,dict):continue
  topic_id=t.get("topic_id")
  topic_chats=t.get("chat_ids")
  topic_work_ids=t.get("work_ids")
  if not isinstance(topic_id,str) or not isinstance(topic_chats,list) or not isinstance(topic_work_ids,list):
   continue
  for link in t.get("ai_work_links") or []:
   if not isinstance(link,dict):continue
   work_id=link.get("work_id")
   if (link.get("binding")!="EXPLICIT_ID_MATCH" or not isinstance(work_id,str)
       or work_id not in topic_work_ids):continue
   if any(chat_id in chat_index and topic_id in (chat_index[chat_id].get("topic_ids") or [])
          and (chat_id,topic_id,work_id) in message_pairs for chat_id in topic_chats):
    counts[work_id]=counts.get(work_id,0)+1
 return counts

def _prepared_source_pin_state(work):
 """Read-only reconciliation of the EXISTING prepared task and its pinned code.
 Does not authorize execution, reprepare tasks, or inspect unlisted paths.
 """
 if not isinstance(work,dict):return "NOT_CHECKED"
 task_id=work.get("task_id")
 if not isinstance(task_id,str) or not re.fullmatch(r"[a-f0-9]{32}",task_id):
  return "NOT_CHECKED"
 task_path=PREPARED_TASK_INBOX/(task_id+".json")
 refs=work.get("input_refs")
 if not isinstance(refs,list) or not any(
     isinstance(r,dict) and r.get("path")==str(task_path) and r.get("exists") is True
     for r in refs):
  return "PREPARED_TASK_NOT_IN_REGISTERED_INPUTS"
 if not task_path.is_file() or task_path.is_symlink() or task_path.stat().st_size>100000:
  return "PREPARED_TASK_UNAVAILABLE_HOLD"
 try:
  task=json.loads(task_path.read_text(encoding="utf-8-sig"))
 except (OSError,ValueError,UnicodeError):
  return "PREPARED_TASK_UNREADABLE_HOLD"
 if (not isinstance(task,dict) or task.get("id")!=task_id
     or task.get("mode")!="BOUNDED_EDIT_PROPOSAL"):
  return "NOT_IMPLEMENTATION_PREPARATION"
 if str(task.get("repo","")).replace("\\","/").casefold()!=str(TAKY_CODE_REPO).replace("\\","/").casefold():
  return "OTHER_REPO_NOT_SCANNED"
 pins=task.get("allowed_files")
 if not isinstance(pins,list) or not pins or len(pins)>10:
  return "SOURCE_PIN_SCOPE_INVALID"
 source_drift=False
 for entry in pins:
  if not isinstance(entry,dict):return "SOURCE_PIN_SCOPE_INVALID"
  relative=entry.get("path")
  sha=entry.get("sha256")
  if (not isinstance(relative,str) or not re.fullmatch(r"[A-Za-z0-9_./-]{4,180}",relative)
      or ".." in relative.split("/") or not isinstance(sha,str)
      or not re.fullmatch(r"[a-f0-9]{64}",sha)):
   return "SOURCE_PIN_SCOPE_INVALID"
  path=(TAKY_CODE_REPO/relative).resolve(strict=False)
  try:path.relative_to(TAKY_CODE_REPO.resolve(strict=True))
  except (ValueError,OSError):return "SOURCE_PIN_SCOPE_INVALID"
  if not path.is_file() or path.is_symlink() or path.stat().st_size>100000:
   return "SOURCE_PIN_UNAVAILABLE_HOLD"
  if digest(path)!=sha:source_drift=True
 try:
  head=subprocess.run(["git","-C",str(TAKY_CODE_REPO),"rev-parse","HEAD"],
       capture_output=True,text=True,encoding="utf-8",timeout=6,
       creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),check=False)
 except (OSError,subprocess.TimeoutExpired):
  return "GIT_HEAD_NOT_CHECKED"
 if head.returncode!=0:return "GIT_HEAD_NOT_CHECKED"
 head_drift=head.stdout.strip()!=task.get("head")
 if source_drift and head_drift:return "PREPARED_SOURCE_AND_HEAD_DRIFT_HOLD"
 if source_drift:return "PREPARED_SOURCE_SHA_DRIFT_HOLD"
 if head_drift:return "PREPARED_HEAD_DRIFT_HOLD"
 return "SOURCE_PIN_MATCH_NOT_EXECUTION_AUTHORIZATION"

def attach_evidence(snapshot,source,topic,kernel,*,topic_digest="",kernel_digest="",kernel_modified="",kernel_integrity="NOT_ATTESTED_TEST_SOURCE"):
 """Read-only exact-key join; status strings and returned calls are not DONE."""
 if topic.get("schema")!="TAKY_CONVERSATION_2026_10_ONWARD_SOURCE_LIMITED_V1":
  raise ValueError("INVALID_TOPIC_SOURCE")
 if not isinstance(topic.get("chats"),list) or not isinstance(topic.get("topics"),list):
  raise ValueError("INVALID_TOPIC_COLLECTION")
 for key in ("preflight_receipts","execution_calls","done_gate_receipts"):
  if not isinstance(kernel.get(key),dict):raise ValueError("INVALID_KERNEL_COLLECTION:"+key)
 preflight=kernel["preflight_receipts"]
 calls=kernel["execution_calls"]
 valid_receipts={rid:r for rid,r in preflight.items() if isinstance(rid,str) and isinstance(r,dict)}
 registry={w.get("work_id"):w for w in source["work_items"]
           if isinstance(w.get("work_id"),str) and isinstance(w.get("task_id"),str)
           and w["work_id"]=="TAKY-CHAT-"+w["task_id"]}
 matched=0
 signed_matched=0
 native_work_topics=_native_work_topic_counts(topic)
 for item in snapshot["work"]:
  work=registry.get(item["id"])
  task=work.get("task_id") if work else None
  direct=[rid for rid,r in valid_receipts.items() if task and r.get("task_id")==task]
  routed=_verified_routed_receipt_id(work,kernel) if work else None
  bound=list(dict.fromkeys(direct+([routed] if routed else [])))
  if routed:signed_matched+=1
  item["nativeTopicMatches"]=native_work_topics.get(item["id"],0)
  item["chatLinked"]=item["nativeTopicMatches"]>0
  item["executionGap"]=(
       "SIGNED_EXECUTION_LINK_OBSERVED" if bound else _unbound_execution_class(work))
  item["preparedSourceState"]=_prepared_source_pin_state(work)
  # The registered WORK_ID and its suffix/task_id must BOTH match exactly.
  item["kernelExact"]={
   "relation":"EXACT_REGISTERED_TASK_ID" if bound else "NO_EXACT_TASK_ID_MATCH",
   "proof":"REGISTERED_ROUTED_SIGNED_RECEIPT" if routed else ("DIRECT_TASK_ID_ONLY" if direct else "NO_VERIFIED_BINDING"),
   "preflightCount":len(bound),
   "invokedCount":sum(1 for rid in bound if isinstance(calls.get(rid),dict)
                    and isinstance(calls[rid].get("actual_calls"),int)
                    and calls[rid]["actual_calls"]>0),
   "unknownCount":sum(1 for rid in bound if isinstance(calls.get(rid),dict)
                    and calls[rid].get("status")=="OUTCOME_UNKNOWN"),
   "routeRecoveryCount":sum(1 for rid in bound if
                    isinstance(valid_receipts[rid].get("correction_provenance"),dict)
                    and valid_receipts[rid]["correction_provenance"].get("state")
                    =="TRUSTED_LOCAL_ROUTE_RECOVERY"),
  }
  if bound:matched+=1
 observed=kernel.get("runtime_version")
 counts={
  "runtimeVersion":observed if isinstance(observed,int) and observed>=0 else None,
  "preflightReceipts":len(preflight),"executionCallReceipts":len(calls),
  "actualInvocationReceipts":sum(1 for c in calls.values() if isinstance(c,dict)
                             and isinstance(c.get("actual_calls"),int) and c["actual_calls"]>0),
  "returnedReceipts":sum(1 for c in calls.values() if isinstance(c,dict) and c.get("status")=="RETURNED"),
  "outcomeUnknownReceipts":sum(1 for c in calls.values() if isinstance(c,dict)
                               and c.get("status")=="OUTCOME_UNKNOWN"),
  "failedReceipts":sum(1 for c in calls.values() if isinstance(c,dict) and c.get("status")=="FAILED"),
  "registeredRouteRecoveries":sum(1 for r in valid_receipts.values() if
                  isinstance(r.get("correction_provenance"),dict) and
                  r["correction_provenance"].get("state")=="TRUSTED_LOCAL_ROUTE_RECOVERY"),
  "doneGateRecords":len(kernel["done_gate_receipts"]),"exactWorkLinks":matched,"signedWorkLinks":signed_matched
 }
 snapshot["kernel"]={
  "source":"TAKY2_RUNTIME_READ_ONLY_NON_CANONICAL",
  "integrity":kernel_integrity,
  "observedFileModifiedAt":clean(kernel_modified,45),
  "sourceSha256":clean(kernel_digest,64),
  **counts
 }
 snapshot["lineage"]={
  "topicSource":"ONLY_NATIVE_EXPORTS_VERIFIED_FOR_INDEX",
  "nativeChatCount":len(topic["chats"]),
  "topicCount":len(topic["topics"]),
  "topicSourceSha256":clean(topic_digest,64),
  "projectCurrentProjectionHashMatches":sum(1 for x in snapshot["projects"]
                                             if x["currentProjectionShaMatched"]),
  "projectCount":len(snapshot["projects"]),
  "exactWorkKernelLinks":matched,"signedWorkKernelLinks":signed_matched,
  "workItemsWithNativeTopicReference":sum(1 for w in snapshot["work"] if w["chatLinked"]),
  "sourceFilesParsed":sum(1 for m in topic.get("original_export_sources",[]) if isinstance(m,dict) and m.get("state")=="SOURCE_PARSED"),
  "authority":"DERIVED_VIEW_ONLY_NOT_GLOBAL_CURRENT",
 }
 return snapshot

def main():
 source=json.loads(SRC.read_text(encoding="utf-8-sig"))
 topic=json.loads(TOPIC.read_text(encoding="utf-8-sig"))
 prior_kernel_sha=digest(KERNEL)
 kernel=read_attested_kernel()
 if digest(KERNEL)!=prior_kernel_sha:raise ValueError("RUNTIME_CHANGED_DURING_ATTESTATION_HOLD")
 data=attach_evidence(build(source,qa=read_local_qa()),source,topic,kernel,
      topic_digest=digest(TOPIC),kernel_digest=prior_kernel_sha,
      kernel_modified=datetime.fromtimestamp(KERNEL.stat().st_mtime,timezone.utc).isoformat(),
      kernel_integrity="HMAC_AND_ROLLBACK_ANCHOR_VERIFIED")
 raw=json.dumps(data,ensure_ascii=False,separators=(",",":"))+"\n"
 if len(raw)>180000:raise ValueError("SNAPSHOT_TOO_LARGE")
 OUT.parent.mkdir(exist_ok=True)
 # Never write the private snapshot into the TAKY Mobile publish='.' tree.
 if "TAKY-MOBILE" in str(OUT):raise ValueError("PUBLIC_PATH_FORBIDDEN")
 OUT.write_text(raw,encoding="utf-8")
 if OUT.read_text(encoding="utf-8")!=raw:raise RuntimeError("READBACK_FAILED")
 print(json.dumps({"path":str(OUT),"projects":len(data["projects"]),"work":len(data["work"]),
   "alerts":len(data["alerts"]),"bytes":len(raw.encode("utf-8")),
   "deployed":False,"admin_environment_modified":False},ensure_ascii=False))
if __name__=="__main__":main()
