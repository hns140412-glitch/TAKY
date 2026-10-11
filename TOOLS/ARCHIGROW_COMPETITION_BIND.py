#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

ALIASES={
 "CONTEXT":["context","site","masterplan","배치","대지","맥락","현황"],
 "CONCEPT":["concept","parti","mass","massing","개념","매스"],
 "PROGRAM":["program","zoning","zone","프로그램","조닝"],
 "CIRCULATION":["circulation","access","flow","동선","진입","접근"],
 "PLAN":["plan","floor","평면","평면도"],
 "SECTION":["section","단면","단면도"],
 "ELEVATION":["elevation","facade","입면","입면도"],
 "AXONOMETRIC":["axon","axo","iso","exploded","액소","아이소","분해"],
 "PERFORMANCE":["performance","sun","daylight","wind","energy","environment","채광","일사","바람","에너지","환경"],
 "EXPERIENCE":["experience","render","perspective","view","interior","exterior","투시","투시도","렌더","내부","외부"],
 "TECHNICAL":["technical","structure","parking","area","egress","detail","구조","주차","면적","피난","상세"]
}
EXTS={".svg",".png",".jpg",".jpeg",".webp",".pdf",".dxf",".dwg",".pptx",".emf"}

def norm(s):
    return re.sub(r"[^0-9a-z가-힣]+"," ",str(s).lower())

def score(mode,path,order):
    text=norm(path.stem)
    value=0
    hits=[]
    for alias in ALIASES.get(mode,[]):
        if norm(alias).strip() in text:
            value+=5
            hits.append(alias)
    if re.search(rf"(^|\s)0*{int(order)}($|\s)",text):
        value+=2
        hits.append(f"order:{order}")
    if path.suffix.lower() in {".svg",".emf",".dxf",".dwg"}:
        value+=1
        hits.append("vector")
    return value,hits

def build(package,source_dir):
    files=[p for p in Path(source_dir).rglob("*") if p.is_file() and p.suffix.lower() in EXTS]
    bindings={}
    suggestions={}
    for item in package.get("items",[]):
        key=f"{item.get('mode')}:{item.get('order')}"
        ranked=[]
        for p in files:
            s,h=score(item.get("mode",""),p,item.get("order",0))
            if s>0:
                ranked.append((s,str(p.resolve()),h))
        ranked.sort(key=lambda x:(-x[0],x[1].lower()))
        top=ranked[:5]
        auto=None
        confidence="NONE"
        if top:
            if top[0][0]>=5 and (len(top)==1 or top[0][0]>=top[1][0]+2):
                auto=top[0][1]
                confidence="HIGH"
            elif top[0][0]>=5:
                confidence="AMBIGUOUS"
            else:
                confidence="LOW"
        if auto:
            bindings[key]={"path":auto,"source_role":item.get("source_required"),"confidence":confidence}
        suggestions[key]={
            "mode":item.get("mode"),
            "source_required":item.get("source_required"),
            "confidence":confidence,
            "auto_bound":bool(auto),
            "candidates":[{"score":s,"path":p,"hits":h} for s,p,h in top]
        }
    return {"bindings":bindings,"suggestions":suggestions,"rule":"Only unique high-confidence matches auto-bind. Ambiguous candidates require evidence/user/project resolution; never guess."}

def main():
    p=argparse.ArgumentParser(description="Suggest/bind architecture competition source artifacts from a source directory.")
    p.add_argument("--package",required=True)
    p.add_argument("--source-dir",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    package=json.loads(Path(args.package).read_text(encoding="utf-8"))
    result=build(package,args.source_dir)
    out=Path(args.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ok":True,"bindings":len(result["bindings"]),"items":len(result["suggestions"]),"output":str(out)},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
