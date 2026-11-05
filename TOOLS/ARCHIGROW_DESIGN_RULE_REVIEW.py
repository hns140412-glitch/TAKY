#!/usr/bin/env python3
"""ArchiGrow: source-bound SVG + company-rule case review, optional bounded partition alternative.

This is a candidate stage. The SVG is the geometry authority for tagged 2D polygons;
the manual's actual bytes/locator are required before its transcribed rules can be used.
No statutory compliance, vehicle swept-path, structural, MEP or design-approval claim.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
_spec=importlib.util.spec_from_file_location("archigrow_layout_kpi",ROOT/"TOOLS"/"ARCHIGROW_LAYOUT_KPI.py")
K=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K)
VERSION="ARCHIGROW_DESIGN_RULE_REVIEW/2026-10-21.1"
KINDS={"MIN_ROOM_AREA","MIN_ROOM_RECT_WIDTH","MIN_CLEAR_HEIGHT","MAX_RAMP_GRADE"}
FLOAT=r"[-+]?(?:\d*\.?\d+)(?:[eE][-+]?\d+)?"

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def good_num(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def safe_path(base,ref):return (base/ref).resolve() if not Path(ref).is_absolute() else Path(ref).resolve()
def validate_source_file(ref, expected_sha, label):
    if not ref or not re.fullmatch("[0-9a-fA-F]{64}",str(expected_sha or "")):
        raise ValueError(label+"_REF_AND_SHA_REQUIRED")
    path=Path(ref)
    if not path.is_file():raise ValueError(label+"_FILE_MISSING")
    if digest(path).lower()!=expected_sha.lower():raise ValueError(label+"_SHA_MISMATCH")
    return path

def svg_polygons(path):
    tree=ET.parse(path)
    root=tree.getroot()
    shapes={}
    for element in root.iter():
        # An SVG transform would invalidate plain coordinate extraction.
        if "transform" in element.attrib:raise ValueError("SVG_TRANSFORM_NEEDS_NORMALIZATION")
        tag=element.tag.rsplit("}",1)[-1]
        if tag!="polygon":continue  # open SVG polylines are not closed room boundaries
        key=element.get("id")
        if not key:continue
        raw=element.get("points","")
        vals=re.findall(FLOAT,raw)
        if len(vals)<6 or len(vals)%2:raise ValueError("SVG_POLYGON_INVALID:"+key)
        pts=[[float(vals[i]),float(vals[i+1])] for i in range(0,len(vals),2)]
        if len(pts)>3 and pts[0]==pts[-1]:pts.pop()
        if not K.polygon_valid(pts):raise ValueError("SVG_POLYGON_INVALID:"+key)
        if key in shapes:raise ValueError("DUPLICATE_SVG_ELEMENT_ID:"+key)
        shapes[key]=pts
    return shapes,root.get("viewBox")

def resolve_entities(doc, svg):
    scale=doc.get("meters_per_svg_unit")
    if not good_num(scale) or scale<=0:raise ValueError("SVG_UNIT_SCALE_REQUIRED")
    entities={}
    for raw in doc.get("entities",[]):
        if not isinstance(raw,dict):raise ValueError("ENTITY_INVALID")
        key=raw.get("id"); svg_id=raw.get("svg_id")
        if not key or key in entities:raise ValueError("ENTITY_ID_MISSING_OR_DUPLICATE")
        if svg_id not in svg:raise ValueError("SEMANTIC_SVG_ELEMENT_MISSING:"+str(svg_id))
        if not raw.get("level"):raise ValueError("ENTITY_LEVEL_REQUIRED:"+key)
        if raw.get("kind") not in ("ROOM","DRIVE_ZONE","OBSTRUCTION","RAMP","FIXED_STRUCTURE","OTHER"):
            raise ValueError("ENTITY_KIND_UNSUPPORTED:"+str(raw.get("kind")))
        ent={**raw,"polygon":svg[svg_id]}
        entities[key]=ent
    if not entities:raise ValueError("NO_SEMANTIC_GEOMETRY")
    return entities,float(scale)

def select(rule,entities):
    return [e for e in entities.values() if e["kind"]==rule.get("target_kind") and
            (not rule.get("target_use") or e.get("use")==rule["target_use"]) and
            (not rule.get("target_id") or e["id"]==rule["target_id"])]

def check_rule(rule,entities,scale,completeness):
    typ=rule["type"];threshold=rule["threshold"]
    targets=select(rule,entities)
    if not targets:
        return {"status":"NEEDS_SOURCE","issue":"TARGET_NOT_IDENTIFIED","results":[]}
    observations=[]
    for obj in targets:
        record={"entity_id":obj["id"]}
        if typ=="MIN_ROOM_AREA":
            value=K.area(obj["polygon"])*scale*scale
            record.update(value=round(value,5),unit="m2")
            record["status"]="PASS" if value+1e-7>=threshold else "VIOLATION"
        elif typ=="MIN_ROOM_RECT_WIDTH":
            poly=obj["polygon"]
            xs={p[0] for p in poly};ys={p[1] for p in poly}
            if len(poly)!=4 or len(xs)!=2 or len(ys)!=2:
                record.update(status="NEEDS_SOURCE",issue="NONRECT_ROOM_WIDTH_UNVERIFIED")
            else:
                axis=rule.get("measure_axis")
                if axis not in ("x","y"):raise ValueError("RECT_WIDTH_MEASURE_AXIS_REQUIRED")
                coords=xs if axis=="x" else ys
                value=(max(coords)-min(coords))*scale
                record.update(value=round(value,5),unit="m")
                record["status"]="PASS" if value+1e-7>=threshold else "VIOLATION"
        elif typ=="MAX_RAMP_GRADE":
            rise=obj.get("rise_m");run=obj.get("run_m")
            if not good_num(rise) or not good_num(run) or run<=0 or obj.get("run_basis")!="HORIZONTAL":
                record.update(status="NEEDS_SOURCE",issue="RAMP_RISE_RUN_REQUIRED")
            else:
                value=100*abs(rise)/run
                record.update(value=round(value,5),unit="%")
                record["status"]="PASS" if value<=threshold+1e-7 else "VIOLATION"
        elif typ=="MIN_CLEAR_HEIGHT":
            floor=obj.get("finished_floor_z_m")
            if not good_num(floor):
                record.update(status="NEEDS_SOURCE",issue="DRIVE_FINISH_LEVEL_REQUIRED")
            else:
                obstacles=[x for x in entities.values() if x["kind"]=="OBSTRUCTION" and x["level"]==obj["level"] and
                           K.intersection_area(obj["polygon"],x["polygon"])*scale*scale>1e-8]
                if any(not good_num(x.get("underside_z_m")) for x in obstacles):
                    record.update(status="NEEDS_SOURCE",issue="OBSTRUCTION_UNDERSIDE_MISSING")
                else:
                    value=min((x["underside_z_m"]-floor for x in obstacles),default=None)
                    if value is not None:
                        record.update(value=round(value,5),unit="m",obstacle_ids=[x["id"] for x in obstacles])
                        record["status"]="PASS" if value+1e-7>=threshold else "VIOLATION"
                    else:
                        record.update(status="NEEDS_SOURCE",issue="NO_CEILING_OR_OBSTRUCTION_LEVEL")
                    # If obstacles are not completely surveyed, a measured PASS is only partial evidence.
                    if record["status"]=="PASS" and completeness.get("overhead_obstacles")!="VERIFIED_COMPLETE":
                        record.update(status="NEEDS_SOURCE",issue="OBSTACLE_COVERAGE_UNVERIFIED")
        observations.append(record)
    states={r["status"] for r in observations}
    return {"status":"VIOLATION" if "VIOLATION" in states else ("NEEDS_SOURCE" if "NEEDS_SOURCE" in states else "PASS"),
            "results":observations}

def validate_rules(rules):
    seen=set()
    for r in rules:
        if r.get("id") in seen or not r.get("id"):raise ValueError("RULE_ID_DUPLICATED_OR_MISSING")
        seen.add(r["id"])
        if r.get("type") not in KINDS:raise ValueError("RULE_TYPE_UNSUPPORTED:"+str(r.get("type")))
        if not good_num(r.get("threshold")) or r["threshold"]<=0:raise ValueError("RULE_THRESHOLD_INVALID")
        if not r.get("source_locator"):raise ValueError("RULE_SOURCE_LOCATOR_REQUIRED")
        if r["type"] in ("MIN_ROOM_AREA","MIN_ROOM_RECT_WIDTH") and r.get("target_kind")!="ROOM":
            raise ValueError("RULE_ROOM_TARGET_REQUIRED")
        if r["type"]=="MIN_CLEAR_HEIGHT" and r.get("target_kind")!="DRIVE_ZONE":raise ValueError("DRIVE_ZONE_TARGET_REQUIRED")
        if r["type"]=="MAX_RAMP_GRADE" and r.get("target_kind")!="RAMP":raise ValueError("RAMP_TARGET_REQUIRED")

def rect_bounds(poly):
    if len(poly)!=4:return None
    xs={p[0] for p in poly};ys={p[1] for p in poly}
    if len(xs)!=2 or len(ys)!=2:return None
    return min(xs),min(ys),max(xs),max(ys)

def generate_alternatives(source, entities, scale, rules, completeness):
    baseline={r["id"]:check_rule(r,entities,scale,completeness) for r in rules}
    old_violations=sum(r["status"]=="VIOLATION" for r in baseline.values())
    if not old_violations:return []
    options=[]
    for bound in source.get("movable_partitions",[]):
        a,b=entities.get(bound.get("room_a")),entities.get(bound.get("room_b"))
        axis=bound.get("axis")
        if not a or not b or a["kind"]!="ROOM" or b["kind"]!="ROOM" or a["level"]!=b["level"] or axis not in ("x","y"):
            continue
        if a.get("locked") or b.get("locked"):continue
        ar,br=rect_bounds(a["polygon"]),rect_bounds(b["polygon"])
        if ar is None or br is None:continue
        # For a vertical (x) partition, A must be on left and B on right with identical y extents.
        if axis=="x":
            if abs(ar[2]-br[0])>1e-8 or abs(ar[1]-br[1])>1e-8 or abs(ar[3]-br[3])>1e-8:continue
            edge=ar[2]
        else:
            if abs(ar[3]-br[1])>1e-8 or abs(ar[0]-br[0])>1e-8 or abs(ar[2]-br[2])>1e-8:continue
            edge=ar[3]
        max_shift=bound.get("max_shift_m",0)
        if not good_num(max_shift) or max_shift<=0:continue
        # A small bounded search; no ungrounded reprogramming of fixed walls/MEP.
        steps=int(min(20,max(1,math.floor(max_shift/0.05+1e-8))))
        for k in range(-steps,steps+1):
            if k==0:continue
            shift_m=k*0.05
            if abs(shift_m)>max_shift+1e-8:continue
            new_edge=edge+shift_m/scale
            cand=copy.deepcopy(entities)
            for name,obj,orig in ((a["id"],a,ar),(b["id"],b,br)):
                points=[]
                for x,y in obj["polygon"]:
                    if axis=="x":
                        target_x=orig[2] if name==a["id"] else orig[0]
                        points.append([new_edge if abs(x-target_x)<1e-8 else x,y])
                    else:
                        target_y=orig[3] if name==a["id"] else orig[1]
                        points.append([x,new_edge if abs(y-target_y)<1e-8 else y])
                cand[name]["polygon"]=points
            if not K.polygon_valid(cand[a["id"]]["polygon"]) or not K.polygon_valid(cand[b["id"]]["polygon"]):continue
            if abs(K.area(a["polygon"])+K.area(b["polygon"])-
                   K.area(cand[a["id"]]["polygon"])-K.area(cand[b["id"]]["polygon"]))>1e-5:continue
            # Candidate may not overlap other identified rooms or fixed structure; no exterior change.
            collision=False
            for name in (a["id"],b["id"]):
                for other in cand.values():
                    if other["id"] in (a["id"],b["id"]):continue
                    if other["level"]==cand[name]["level"] and other["kind"] in ("ROOM","FIXED_STRUCTURE") and K.intersection_area(
                            cand[name]["polygon"],other["polygon"])*scale*scale>1e-8:
                        collision=True
                        break
            if collision:continue
            checks={r["id"]:check_rule(r,cand,scale,completeness) for r in rules}
            worse=any(baseline[rid]["status"]!="VIOLATION" and rec["status"]=="VIOLATION" for rid,rec in checks.items())
            remaining=sum(rec["status"]=="VIOLATION" for rec in checks.values())
            if worse or remaining>=old_violations:continue
            options.append({"partition_id":bound.get("id"),"room_ids":[a["id"],b["id"]],
                            "shift_m":round(shift_m,3),"violations_before":old_violations,
                            "violations_after":remaining,"candidate_polygons":{name:cand[name]["polygon"] for name in (a["id"],b["id"])},
                            "candidate_rules":{rid:rec["status"] for rid,rec in checks.items()},
                            "status":"GEOMETRY_CANDIDATE_REVIEW_REQUIRED"})
    options.sort(key=lambda x:(x["violations_after"],abs(x["shift_m"]),x["partition_id"] or ""))
    return options[:3]

def write_overlay(path,alternatives,viewbox):
    # Candidate overlay: geometry-only, avoids changing original CAD/SVG geometry.
    selected=alternatives[0] if alternatives else None
    if not selected:return None
    shapes=[]
    for name,poly in selected["candidate_polygons"].items():
        pts=" ".join(f"{x:.4f},{y:.4f}" for x,y in poly)
        shapes.append(f'<polygon points="{pts}" fill="none" stroke="#e65d24" stroke-width="35" stroke-dasharray="120 60" data-source-room="{name}"/>')
    vb=f' viewBox="{viewbox}"' if viewbox else ""
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg"'+vb+'>'+''.join(shapes)+'</svg>',encoding="utf-8")
    return path

def write_review_surfaces(directory,project_id,entities,checks,alternatives,viewbox,scale):
    """Excel-readable inspection rows + self-contained, inert SVG comparison sheet."""
    import csv
    from html import escape as esc
    csv_path=directory/"design_review_table.csv"
    columns=["project_id","rule_id","type","source_locator","entity_id","status","observed","threshold","unit","issue"]
    with csv_path.open("w",encoding="utf-8-sig",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=columns);writer.writeheader()
        for check in checks:
            for item in check["results"] or [{"entity_id":"","status":check["status"],"issue":check.get("issue") or ""}]:
                writer.writerow({
                    "project_id":project_id,"rule_id":check["rule_id"],"type":check["type"],
                    "source_locator":check["source_locator"],"entity_id":item.get("entity_id",""),
                    "status":item.get("status"),"observed":item.get("value",""),
                    "threshold":check["threshold"],"unit":item.get("unit",""),
                    "issue":item.get("issue",check.get("issue") or "")})
    x=[p[0] for obj in entities.values() for p in obj["polygon"]]
    y=[p[1] for obj in entities.values() for p in obj["polygon"]]
    xmin,xmax,ymin,ymax=min(x),max(x),min(y),max(y)
    if viewbox:
        nums=[float(s) for s in viewbox.replace(","," ").split()]
        if len(nums)==4 and nums[2]>0 and nums[3]>0:
            xmin,ymin,wd,ht=nums;xmax,ymax=xmin+wd,ymin+ht
    padding=max(xmax-xmin,ymax-ymin)*.04
    box=f"{xmin-padding:.2f} {ymin-padding:.2f} {xmax-xmin+2*padding:.2f} {ymax-ymin+2*padding:.2f}"
    line=max(xmax-xmin,ymax-ymin)*.0022
    font=max(xmax-xmin,ymax-ymin)*.019
    rule_fail={item["entity_id"] for r in checks for item in r["results"] if item["status"]=="VIOLATION"}
    active=alternatives[0] if alternatives else None
    def vector(mode):
        out=[]
        for obj in entities.values():
            room_changed=bool(active and obj["id"] in active["candidate_polygons"])
            pts=active["candidate_polygons"][obj["id"]] if mode=="candidate" and room_changed else obj["polygon"]
            coord=" ".join(f"{xx:.4f},{yy:.4f}" for xx,yy in pts)
            is_bad=obj["id"] in rule_fail and not(mode=="candidate" and room_changed)
            is_obstacle=obj["kind"]=="OBSTRUCTION"
            tone=("#c9544d" if is_bad else "#147f91" if obj["kind"]=="ROOM" else "#8c7e68")
            fill="#eebfb4" if is_bad else "#c8e4e4" if obj["kind"]=="ROOM" else "#d3d5d7"
            if is_obstacle:fill="#e3bf7d"
            out.append(f'<polygon points="{coord}" stroke="{tone}" stroke-width="{line:.2f}" fill="{fill}" fill-opacity=".65"/>')
            centerx=sum(p[0] for p in pts)/len(pts)
            centery=sum(p[1] for p in pts)/len(pts)
            label=esc(str(obj.get("use") or obj["id"]))
            out.append(f'<text x="{centerx:.3f}" y="{centery:.3f}" font-size="{font:.2f}" text-anchor="middle" fill="#23333e" font-family="Arial">{label}</text>')
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" role="img" aria-label="{mode} geometry">'+"".join(out)+"</svg>"
    statuses={"PASS":"충족","VIOLATION":"기준 차이","NEEDS_SOURCE":"확인 필요"}
    cells=[]
    for rule in checks:
        values=", ".join(str(v["value"])+" "+v.get("unit","") for v in rule["results"] if "value" in v) or "도면 근거 부족"
        mark=statuses.get(rule["status"],rule["status"])
        cls=esc(rule["status"].lower())
        cells.append("<tr>"
                     f"<td>{esc(str(rule['rule_id']))}</td>"
                     f"<td>{esc(str(rule['type']))}</td>"
                     f"<td>{esc(str(rule['source_locator']))}</td>"
                     f"<td>{esc(values)}</td>"
                     f"<td>{esc(str(rule['threshold']))}</td>"
                     f'<td class="{cls}">{esc(mark)}</td></tr>')
    choice_text=(f"{esc(str(active['partition_id']))} · 경계 이동 {active['shift_m']:+.2f}m "
                 f"· 개선 전 문제 {active['violations_before']} → 변경 후 {active['violations_after']}건"
                 if active else "검증 가능한 변경안 없음 — 추가 도면 근거 또는 조정 가능한 설계 변수가 필요함")
    html=f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>ARCHI GROW · 설계 기준 검토</title>
    <style>
    :root{{--ink:#192f39;--muted:#5f7079;--line:#b6c9cf;--accent:#137c91;--bg:#f4f8f9}}
    *{{box-sizing:border-box}}body{{margin:0;background:var(--bg);font:14px/1.5 "Malgun Gothic",Arial,sans-serif;color:var(--ink)}}
    main{{max-width:1540px;margin:32px auto;background:white;padding:42px 48px;box-shadow:0 2px 30px #18374413}}
    .top{{display:flex;justify-content:space-between;gap:20px;align-items:end;border-bottom:3px solid var(--ink);padding-bottom:20px}}
    .eyebrow{{text-transform:uppercase;letter-spacing:.17em;font-size:11px;color:var(--accent);font-weight:800}}
    h1{{font-size:30px;margin:6px 0 5px;font-weight:800;letter-spacing:-.055em}}
    h2{{font-size:18px;margin:0 0 12px}}p{{margin:5px 0;color:var(--muted)}}
    .source{{font-size:11px;color:#617681;text-align:right}}
    .cols{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:28px}}
    .panel{{padding:12px 16px 20px;border:1px solid var(--line);min-width:0}}
    .panel-title{{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid var(--line);padding:5px 0 12px;margin-bottom:14px}}
    .panel svg{{display:block;width:100%;height:360px;max-height:40vw;background:#f9fcfc}}
    .alt{{margin:16px 0 22px;padding:16px 0;border-bottom:1px solid var(--line);font-weight:700;color:#235161}}
    table{{border-collapse:collapse;width:100%;font-size:12px}}
    td,th{{padding:10px 12px;text-align:left;border-bottom:1px solid #dfe8eb;vertical-align:top}}
    th{{color:#47616e;border-bottom:2px solid var(--ink);font-size:11px;background:#f4f8f9}}
    .violation{{color:#ad3831;font-weight:800}}.needs_source{{color:#9e7123;font-weight:800}}.pass{{color:#137d6a;font-weight:800}}
    footer{{border-top:1px solid var(--line);margin-top:28px;padding-top:15px;color:#6d7b80;font-size:11px}}
    @media(max-width:780px){{main{{margin:0;padding:20px}}.cols{{grid-template-columns:1fr}}.panel svg{{max-height:inherit}}.top{{display:block}}.source{{text-align:left}}}}
    @media print{{body{{background:#fff}}main{{box-shadow:none;margin:0;padding:8mm}}.panel svg{{height:245px}}}}
    </style></head><body><main>
    <header class="top"><div><div class="eyebrow">ARCHI GROW / DESIGN INTELLIGENCE</div>
    <h1>설계 기준 검토 · 개선 대안</h1><p>기존 SVG 도면과 원문 출처를 가진 설계기준에 따른 기계적 검토</p></div>
    <div class="source">PROJECT {esc(project_id)}<br>VECTOR SCALE {scale:g}m / SVG unit<br>NOT APPROVED · SYNTHETIC DEMO OR SOURCE REVIEW REQUIRED</div></header>
    <section class="cols"><div class="panel"><div class="panel-title"><b>01. 기존 계획</b><span>ORIGINAL / READ ONLY</span></div>{vector("original")}</div>
    <div class="panel"><div class="panel-title"><b>02. 개선 대안</b><span>GEOMETRY CANDIDATE</span></div>{vector("candidate")}</div></section>
    <div class="alt">{choice_text}</div><h2>03. 기준별 검토 결과</h2>
    <table><thead><tr><th>ID</th><th>기준 분류</th><th>원문 근거</th><th>산출값</th><th>기준값</th><th>판정</th></tr></thead>
    <tbody>{''.join(cells)}</tbody></table>
    <footer>원본 CAD/건설사 매뉴얼 및 인허가 법규에 대한 승인 판정이 아님. 가상 자료일 경우 실제 기준값으로 사용 금지.
    벽 이동안은 설비·구조·문·가구·인허가 영향 검토 이전의 계획 후보임.</footer></main></body></html>"""
    html_path=directory/"design_review_preview.html"
    html_path.write_text(html,encoding="utf-8")
    return [csv_path,html_path]

def review(plan_path,manual_path,out_dir):
    plan_path=Path(plan_path).resolve();manual_path=Path(manual_path).resolve();out_dir=Path(out_dir).resolve()
    plan=load(plan_path);manual=load(manual_path)
    if plan.get("schema")!="ARCHIGROW_SEMANTIC_SVG_PLAN_V1":raise ValueError("PLAN_SCHEMA_UNSUPPORTED")
    if manual.get("schema")!="ARCHIGROW_MANUAL_RULEPACK_V1":raise ValueError("MANUAL_SCHEMA_UNSUPPORTED")
    if not plan.get("project_id"):raise ValueError("PROJECT_ID_REQUIRED")
    source=manual.get("manual_source") or {}
    manual_file=validate_source_file(safe_path(manual_path.parent,source.get("path","")),source.get("sha256"),"MANUAL")
    svg_ref=plan.get("source_svg") or {}
    svg_file=validate_source_file(safe_path(plan_path.parent,svg_ref.get("path","")),svg_ref.get("sha256"),"SVG")
    rules=manual.get("rules")
    if not isinstance(rules,list) or not rules:raise ValueError("RULES_REQUIRED")
    validate_rules(rules)
    polys,viewbox=svg_polygons(svg_file)
    entities,scale=resolve_entities(plan,polys)
    completeness=plan.get("completeness") or {}
    outputs=[]
    for r in rules:
        result=check_rule(r,entities,scale,completeness)
        outputs.append({"rule_id":r["id"],"type":r["type"],"source_locator":r["source_locator"],
                        "threshold":r["threshold"],"status":result["status"],"results":result["results"],
                        "issue":result.get("issue")})
    alt=generate_alternatives(plan,entities,scale,rules,completeness)
    summary={s:sum(o["status"]==s for o in outputs) for s in ("PASS","VIOLATION","NEEDS_SOURCE")}
    status="REVIEW_REQUIRED" if summary["VIOLATION"] else ("HOLD_SOURCE" if summary["NEEDS_SOURCE"] else "CANDIDATE_CHECK_CLEAR")
    receipt={"schema":"ARCHIGROW_DESIGN_CASE_REVIEW_RESULT_V1","tool":VERSION,"project_id":plan["project_id"],
             "source_manually_transcribed_rules":True,
             "manual":{"path":str(manual_file),"sha256":digest(manual_file),"company":manual.get("company"),"revision":source.get("revision")},
             "source_svg":{"path":str(svg_file),"sha256":digest(svg_file)},
             "rulepack_sha256":digest(manual_path),"plan_sha256":digest(plan_path),
             "summary":summary,"status":status,"checks":outputs,
             "alternatives":alt,"drawing_revision":plan.get("drawing_revision"),
             "authority":"DESIGN_CANDIDATE_ONLY","statutory_compliance":"NOT_VERIFIED",
             "next_route":"PROJECT_SPECIFIC_DESIGN_REVIEW_AND_3D_CROSSCHECK",
             "limits":["Only simple, explicitly mapped SVG polygons accepted; paths/transforms require a different geometry adapter",
                       "Manual rules are transcribed, not automatically proven by a passed arithmetic check",
                       "Overhead obstruction coverage and vehicle swept paths require independent source/3D checks",
                       "Candidate wall movement is not an approved or constructible CAD revision"]}
    out_dir.mkdir(parents=True,exist_ok=True)
    output=out_dir/"design_case_review.json"
    if output in (plan_path,manual_path,svg_file,manual_file):raise ValueError("OUTPUT_OVERWRITES_SOURCE")
    output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
    overlay=write_overlay(out_dir/"alternative_overlay.svg",alt,viewbox)
    visual_outputs=write_review_surfaces(out_dir,plan["project_id"],entities,outputs,alt,viewbox,scale)
    stage={"schema":"ARCHIGROW_STAGE_RECEIPT_V1","stage_id":"DESIGN_RULE_REVIEW",
           "inputs":[{"ref":str(p),"sha256":digest(p)} for p in (plan_path,manual_path,svg_file,manual_file)],
           "outputs":[{"ref":str(p),"sha256":digest(p)} for p in ([output,overlay] if overlay else [output])+visual_outputs],
           "status":"HOLD" if summary["NEEDS_SOURCE"] or summary["VIOLATION"] else "PASS",
           "claim_level":"CANDIDATE_GEOMETRY_ONLY","approval":"NOT_GRANTED"}
    (out_dir/"stage_receipt.json").write_text(json.dumps(stage,ensure_ascii=False,indent=2),encoding="utf-8")
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("plan_json");p.add_argument("manual_rulepack_json");p.add_argument("out_dir")
    a=p.parse_args()
    result=review(a.plan_json,a.manual_rulepack_json,a.out_dir)
    print(json.dumps({"status":result["status"],"summary":result["summary"],"alternatives":len(result["alternatives"])},ensure_ascii=False))
    return 0

if __name__=="__main__":raise SystemExit(main())
