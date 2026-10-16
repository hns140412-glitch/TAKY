from pathlib import Path
import json,datetime
root=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH")
projects={"TAKY":"TAKY","TAKY-ASSETS":"TAKY-ASSETS","TAKY-MOBILE":"TAKY-MOBILE","TAKY_ARCHI-GROW":"TAKY_ARCHI GROW","READY-SET":"Ready & Set","HIDE-SEEK":"Hide & Seek","PLAY-CAMP":"Play Camp","SNAP-POP":"Snap & Pop","SAVEY":"SAVEY"}
folders=["00_CONTROL","20_DESIGN_STUDIO","30_AUDIO_STUDIO","40_AI_COLLAB","50_INTEGRATION_TEST","60_APPROVAL_GATE","70_RELEASE_CANDIDATES","90_ARCHIVE"]
for f in folders: (root/f).mkdir(parents=True,exist_ok=True)
for f in ["UI-UX","CHARACTER","BACKGROUND","BADGE","DESIGN-SYSTEM","RESPONSIVE"]: (root/"20_DESIGN_STUDIO"/f).mkdir(exist_ok=True)
for f in ["SCRIPT","VOICE-CASTING","TTS-MOCKUP","RECORDING","EDITING","QA","BINDING"]: (root/"30_AUDIO_STUDIO"/f).mkdir(exist_ok=True)
for f in ["GPT","CLAUDE","CODEX","SHARED-RESULTS"]: (root/"40_AI_COLLAB"/f).mkdir(exist_ok=True)
for name,src in projects.items(): (root/"10_PROJECTS"/name).mkdir(parents=True,exist_ok=True)
control=root/"00_CONTROL"
def put(name,obj):
 p=control/name
 if not p.exists():p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
put("PROJECT_REGISTRY.json",{"schema":"TAKY_WORKBENCH_PROJECT_REGISTRY_V1","projects":{k:{"workbench_path":f"10_PROJECTS/{k}","source_repo":f"D:/Git PWA/{v}","source_role":"REFERENCE_NOT_COPY","status":"IDLE"} for k,v in projects.items()}})
put("PATH_REGISTRY.json",{"authority":"D:/Git PWA/TAKY/CURRENT","asset_authority":"D:/Git PWA/TAKY-ASSETS","raw_authority":"D:/Git PWA/TAKY-SOURCE-VAULT","workbench":str(root).replace(chr(92),"/"),"remote_push":"USER_APPROVAL_REQUIRED","deploy":"USER_APPROVAL_REQUIRED"})
put("AI_WORK_ASSIGNMENTS.json",{"schema":"TAKY_AI_WORK_ASSIGNMENTS_V1","tasks":[],"required_fields":["work_id","project","owner","reviewer","authority_ref","input_refs","output_refs","status","evidence_refs"],"statuses":["OPEN","IN_PROGRESS","REVIEW","USER_APPROVAL_REQUIRED","APPROVED","PROMOTION_READY","PROMOTED","BLOCKED"]})
put("DESIGN_PRODUCTION_REGISTRY.json",{"schema":"TAKY_DESIGN_PRODUCTION_V1","records":[],"required_fields":["work_id","project","screen_id","ui_state","visual_id","baseline_ref","design_ref","asset_bindings","review_evidence","approval_state","consumer_repo"],"approval_default":"CANDIDATE"})
put("AUDIO_PRODUCTION_REGISTRY.json",{"schema":"TAKY_AUDIO_PRODUCTION_V1","records":[],"required_fields":["work_id","project","script_id","event_id","speaker_id","language","script_hash","phonetic_review","tts_mock_ref","interaction_qa","approved_recording_ref","runtime_binding","approval_state"],"approval_default":"CANDIDATE"})
policy="""# TAKY AI WORKBENCH - CONTROL POLICY
- All AIs use WORK_ID and one PROJECT_CURRENT reference per project; shared outputs are registered, not duplicated.
- WORKBENCH is a staging workspace. Approved design/audio source ownership is transferred into TAKY-ASSETS only after approval and consumer verification.
- UI production: baseline -> screen/state contract -> candidate -> compare -> explicit approval -> source transfer -> consumer binding -> regression.
- Audio production: event coverage -> script -> pronunciation -> mock TTS -> interaction QA -> recording approval -> source transfer -> replacement binding -> regression.
- GPT orchestrates, Claude executes/designs, Codex performs independent checks when needed; roles do not grant authority to approve.
- Each work item uses one staging folder; rejected candidates retain a trace, not promoted assets.
- Migration is move/rebind/verify, NOT clone-and-declare-a-second-source.
- GitHub push, remote repo rename, paid API, Netlify deploy are BLOCKED unless user explicitly approves.
- RULE WRITTEN is not RULE ENFORCED: these registries are scaffolds, no automated enforcement claimed.
"""
q=control/"TAKY_WORKBENCH_POLICY.md"
if not q.exists():q.write_text(policy,encoding="utf-8")
for name in projects:
 f=root/"10_PROJECTS"/name/"PROJECT_CURRENT.json"
 if not f.exists():f.write_text(json.dumps({"project":name,"current_work_id":None,"status":"IDLE","approval":"NONE","source_refs":[],"output_refs":[],"pending_gates":[]},indent=2)+"\n",encoding="utf-8")
print(json.dumps({"created":str(root),"projects":len(projects),"registries":len(list(control.glob("*.json"))),"source_directories_untouched":True},ensure_ascii=False))
