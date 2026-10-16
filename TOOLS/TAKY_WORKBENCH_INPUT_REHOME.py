"""Rehome pipeline DATA reference/input collections into WORKBENCH/REFERENCE.

Keep live runtime state (pipeline_bridge/site_watch/source_acquisition) in
SOURCE-VAULT. Preserve all legacy data paths as directory junctions.
Same-D volume rename, SHA samples, full file-count/size; fail on active writes.
"""
import argparse,json,os,subprocess,hashlib,time
from pathlib import Path
R=Path(r"D:\Git PWA")
OLD=R/"TAKY-SOURCE-VAULT"/"data"
WB=R/"TAKY_AI_WORKBENCH"/"REFERENCE"
EVIDENCE=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"REFERENCE_INPUTS_PHYSICAL_REHOME_20261013.json"
MAP={
 "direction_intake":"00_INBOX/DIRECTION_INTAKE",
 "external_raw":"00_INBOX/EXTERNAL_RAW",
 "mining_discovery_intake_inputs":"00_INBOX/DISCOVERY_INTAKE",
 "mining_manual_intake_inputs":"00_INBOX/MANUAL_INTAKE",
 "notion_incremental":"00_INBOX/NOTION_INCREMENTAL",
 "play_camp_gap_inputs":"10_LEARNING/PLAY_CAMP_INPUTS",
 "reference_inbox":"00_INBOX/REFERENCE_INBOX",
 "reference_intake":"00_INBOX/REFERENCE_INTAKE",
 "remote_drive_inbox":"00_INBOX/DRIVE_INBOX",
 "visual_evidence":"40_DESIGN_MEDIA/VISUAL_EVIDENCE",
}
PRESERVE={"pipeline_bridge","site_watch","source_acquisition"}
def overview(root):
    total=0;n=0;newest=0;choices=[]
    for base,dirs,files in os.walk(root):
        dirs[:]=[d for d in dirs if not (Path(base)/d).is_junction()]
        for f in files:
            path=Path(base)/f
            if path.is_symlink() or path.is_junction():
                raise RuntimeError("NESTED_SYMLINK_UNREVIEWED:"+str(path))
            info=path.stat()
            n+=1;total+=info.st_size;newest=max(newest,info.st_mtime)
            if info.st_size<=4_000_000:
                choices.append((info.st_size,path.relative_to(root).as_posix()))
    choices.sort()
    # Detect tampering for selected small files; large files verified via
    # atomic same-volume rename plus complete count/size and mtime evidence.
    picks=[rel for _,rel in choices[:2]]
    picks+=[rel for _,rel in choices[-2:]]
    return {"files":n,"bytes":total,"newest_epoch":newest,
     "sample_sha256":{rel:hashlib.sha256((root/rel).read_bytes()).hexdigest()
      for rel in sorted(set(picks))}}
def compare(source,proof):
    if not source.is_dir():return False
    now=overview(source)
    if now["files"]!=proof["files"] or now["bytes"]!=proof["bytes"]:return False
    return all(hashlib.sha256((source/rel).read_bytes()).hexdigest()==h
      for rel,h in proof["sample_sha256"].items())
def move_one(name,apply):
    source=OLD/name;dest=WB/MAP[name]
    if dest.is_dir():
        if not source.is_dir() or not source.is_junction() or not os.path.samefile(source,dest):
            raise RuntimeError("INPUT_ALREADY_MOVED_BUT_ALIAS_MISMATCH:"+name)
        inventory=overview(dest)
        return {"name":name,"state":"ALREADY_MOVED","files":inventory["files"],"bytes":inventory["bytes"]}
    if not source.is_dir() or source.is_junction() or dest.exists():
        raise RuntimeError("UNEXPECTED_INPUT_SOURCE_OR_DEST:"+name)
    proof=overview(source)
    if time.time()-proof["newest_epoch"]<600:
        return {"name":name,"state":"HOLD_RECENT_ACTIVE_WRITE","files":proof["files"]}
    if not apply:
        return {"name":name,"state":"READY","files":proof["files"],
         "mib":round(proof["bytes"]/1048576,2)}
    dest.parent.mkdir(parents=True,exist_ok=True)
    os.rename(source,dest)
    try:
        linked=subprocess.run(["cmd.exe","/c","mklink","/J",str(source),str(dest)],
          capture_output=True,text=True,errors="replace",timeout=15)
        if linked.returncode or not source.is_junction() or not os.path.samefile(source,dest):
            raise RuntimeError("INPUT_COMPAT_JUNCTION_FAILED:"+name)
        if not compare(dest,proof):
            raise RuntimeError("INPUT_AFTER_MOVE_HASH_OR_COUNT_DRIFT:"+name)
    except:
        if source.is_junction():os.rmdir(source)
        if not source.exists():os.rename(dest,source)
        raise
    return {"name":name,"state":"PHYSICAL_REHOMED_WITH_ALIAS",
     "canonical":str(dest),"legacy_alias":str(source),**proof}
def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit",action="store_true")
    group.add_argument("--apply",action="store_true")
    a=p.parse_args()
    results=[]
    for name in MAP:
        try:
            result=move_one(name,a.apply)
        except PermissionError:
            result={"name":name,"state":"HOLD_WINDOWS_DIRECTORY_BUSY"}
        results.append(result)
        if a.apply:print("INPUT",name,result["state"],flush=True)
    if a.apply:
        EVIDENCE.parent.mkdir(parents=True,exist_ok=True)
        out={"schema":"TAKY_WORKBENCH_REFERENCE_INPUT_REHOME_V1",
          "results":results,"preserved_live_pipeline_folders":sorted(PRESERVE),
          "source_vault_intake_data_bytes_referenced_not_copied":True,
          "git_or_drive_modified":False}
        temp=EVIDENCE.with_suffix(".json.pending")
        temp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        os.replace(temp,EVIDENCE)
    return {"status":"APPLIED" if a.apply else "AUDIT","summary":
       {st:sum(x["state"]==st for x in results)
         for st in {x["state"] for x in results}},
       "groups":len(results),
       "files_now_in_workbench":sum(x.get("files",0)
         for x in results if x["state"] in ("PHYSICAL_REHOMED_WITH_ALIAS","ALREADY_MOVED")),
       "held_for_busy_handle":[x["name"] for x in results if x["state"].startswith("HOLD")]}
if __name__=="__main__":
 print(json.dumps(main(),ensure_ascii=False))
