#!/usr/bin/env python3
import argparse,copy,json
from pathlib import Path
from build_badge_production_packets_v2 import ROOT,build

REQUIRED_FILES=["manifest.json","base.png","bg.png","subject.png","fx.png","composite.png",
                "preview-64.png","preview-120.png","preview-200.png","preview-320.png",
                "depth-profile.json","review.json"]

def packet_map(root=ROOT):
    return {x["badge_id"]:x for x in build(root)["items"]}

def make_manifest(packet):
    return {
      "schema":"TAKY_BADGE_INDIVIDUAL_MANIFEST_V2",
      "badge_id":packet["badge_id"],
      "visual_id":packet["visual_id"],
      "asset_dir":packet["asset_dir"],
      "production_classification":packet["production_classification"],
      "required_files":REQUIRED_FILES,
      "detail_effect_scope":"BADGE_DETAIL_VIEW_ONLY",
      "approval_status":"NOT_APPROVED_PENDING_ADMISSION",
      "runtime_binding":False
    }

def make_depth_profile(packet,root=ROOT):
    base=json.loads((Path(root)/"BADGE/production/badge-depth-profile-default-v1.json").read_text(encoding="utf-8"))
    out=copy.deepcopy(base)
    out["badge_id"]=packet["badge_id"]
    out["visual_id"]=packet["visual_id"]
    out["asset_dir"]=packet["asset_dir"]
    return out

def write_scaffold(packet,root=ROOT,force=False):
    directory=Path(root)/packet["asset_dir"]
    directory.mkdir(parents=True,exist_ok=True)
    outputs={
      directory/"manifest.json":make_manifest(packet),
      directory/"depth-profile.json":make_depth_profile(packet,root)
    }
    for path,data in outputs.items():
        if path.exists() and not force:
            raise FileExistsError("REFUSE_OVERWRITE_EXISTING_SCAFFOLD "+str(path))
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return [str(x.relative_to(root)) for x in outputs]

def main():
    p=argparse.ArgumentParser(description="Prepare metadata-only badge asset scaffold. Never generates art.")
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--badge-id")
    g.add_argument("--all",action="store_true")
    p.add_argument("--force",action="store_true")
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    packets=packet_map()
    selected=list(packets.values()) if a.all else [packets.get(a.badge_id)]
    if any(x is None for x in selected): raise SystemExit("UNKNOWN_BADGE_ID")
    if a.dry_run:
        print(json.dumps([{"manifest":make_manifest(x),"depth_profile":make_depth_profile(x)} for x in selected],ensure_ascii=False,indent=2))
        return
    written=[]
    for x in selected: written.extend(write_scaffold(x,force=a.force))
    print(json.dumps({"written":written},ensure_ascii=False))
if __name__=="__main__":main()
