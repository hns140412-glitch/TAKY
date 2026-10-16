from pathlib import Path
import json
root=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH")
base=root/"01_BACKLOG_AND_ADOPTION"
for folder in ["00_INBOX","10_POST_CLEANUP","20_MCP","30_SKILLS","40_TOOLS","50_INTEGRATION","60_DECISIONS","70_EXECUTION_QUEUE","80_EVIDENCE","90_DONE"]:
 (base/folder).mkdir(parents=True,exist_ok=True)
items=[
 ("CLN-001","POST_CLEANUP","Inventory duplicate folders, retired paths, live Git worktrees and external references","P0",["filesystem-inventory","path-registry"],"AFTER_CLEANUP"),
 ("CLN-002","POST_CLEANUP","Verify canonical CURRENT, owner and archived revisions without duplicates","P0",["CLN-001"],"AFTER_CLEANUP"),
 ("MCP-001","MCP","Audit connected MCP inventory and effective permissions; avoid installing redundant tools","P1",["CLN-001"],"ASSESS"),
 ("MCP-002","MCP","Verify Remote Desktop Commander paths, shell reliability and CPU limits","P0",["CLN-001"],"ASSESS"),
 ("MCP-003","MCP","Check Drive and GitHub connector access vs local source authority; minimize remote calls","P1",["MCP-001"],"ASSESS"),
 ("SKL-001","SKILLS","Catalog Claude and Codex skills; trigger rules, compatibility and necessity gate","P1",["CLN-001"],"ASSESS"),
 ("SKL-002","SKILLS","Evaluate Agent Reach and Graft only after directory cleanup; record exact utility and adoption decision","P2",["CLN-001"],"AFTER_CLEANUP"),
 ("INT-001","INTEGRATION","Connect WORK_ID task manifests with shared GPT Claude Codex handoffs","P0",["CLN-002"],"IMPLEMENT"),
 ("INT-002","INTEGRATION","Bind UI gallery to real approval evidence, Visual ID and app screen state","P0",["CLN-002"],"IMPLEMENT"),
 ("INT-003","INTEGRATION","Bind script, pronunciation, voice samples, approvals and runtime audio events","P0",["CLN-002"],"IMPLEMENT"),
 ("GATE-001","INTEGRATION","Enforce no GitHub push, Netlify deploy or paid API without explicit approval","P0",["INT-001"],"IMPLEMENT"),
 ("OPS-001","TOOLS","After cleanup, audit observer and local collector stage coverage and rate/CPU limits","P0",["CLN-001"],"ASSESS")
]
path=base/"70_EXECUTION_QUEUE"/"TASK_REGISTER.json"
if not path.exists():
 data={"schema":"TAKY_WORKBENCH_BACKLOG_V1","authority":"TAKY/CURRENT","tasks":[{"id":i,"category":c,"title":t,"priority":pr,"dependencies":dep,"phase":phase,"status":"NOT_STARTED","owner":"UNASSIGNED","approval_required":False,"evidence":[],"decision":"UNDECIDED"} for i,c,t,pr,dep,phase in items],"states":["NOT_STARTED","DISCOVERY","EVALUATION","READY","IMPLEMENTING","VERIFIED","ADOPTED","REJECTED","BLOCKED"]}
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
readme=base/"README.md"
readme.write_text("""# TAKY WORKBENCH - Adoption & Backlog (top level)
This is the single entry for after-cleanup adoption of MCP, skills, tools and pending work.
- 00_INBOX: untriaged suggestions (not yet accepted)
- 10_POST_CLEANUP: cleanup closing conditions and baseline
- 20_MCP / 30_SKILLS / 40_TOOLS: suitability evaluations, not auto installation
- 50_INTEGRATION: integration plans
- 60_DECISIONS: ACCEPT / HOLD / REJECT decisions, with provenance
- 70_EXECUTION_QUEUE/TASK_REGISTER.json: authoritative work queue within this workspace
- 80_EVIDENCE: verification results
- 90_DONE: closed-task references

Hard gates: necessity before call; no paid API, plugin install, GitHub push or Netlify deploy without user authorization. No MCP or skill is considered installed merely by being listed. Dependencies must be verified. After folder cleanup, promote only evidenced items; do not blindly install all candidates.
""",encoding="utf-8")
print(json.dumps({"path":str(base),"tasks":len(json.loads(path.read_text(encoding="utf-8"))["tasks"]),"folders":10},ensure_ascii=False))
