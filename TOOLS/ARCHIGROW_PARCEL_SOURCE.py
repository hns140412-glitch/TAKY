#!/usr/bin/env python3
"""ArchiGrow parcel evidence adapter, reusing the established massing pipeline.

SOURCE: VWorld cadastral polygon by exact 19-digit PNU, official EUM HTML area.
No fake parcel, automatic geocoder guess, unverified FAR source, or secret logging.
EUM HTML is official web-view evidence, not a legally issued document.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

VERSION="ARCHIGROW_PARCEL_SOURCE/2026-10-18.1"
VWORLD="https://api.vworld.kr/req/data"
EUM="https://www.eum.go.kr/web/ar/lu/luLandDet.jsp"
PNU_RE=re.compile(r"^[0-9]{19}$")

class SiteHold(Exception):
    def __init__(self,code,detail=""):
        super().__init__(code)
        self.code=code
        self.detail=str(detail)[:250]

def digest(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()

def bounded_fetch(url,max_bytes=3_000_000):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; ArchiGrowEvidence/1.0)","Accept":"text/html,application/json"})
    with urllib.request.urlopen(req,timeout=17) as r:
        declared=int(r.headers.get("Content-Length") or 0)
        if declared>max_bytes: raise SiteHold("UPSTREAM_RESPONSE_TOO_LARGE")
        raw=r.read(max_bytes+1)
        if len(raw)>max_bytes: raise SiteHold("UPSTREAM_RESPONSE_TOO_LARGE")
        return raw,r.headers.get("Content-Type",""),r.status

class EumFields(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active=None;self.parts=[];self.fields={}
        self.collect_th=False;self.th_parts=[];self.next_site_td=False
    def handle_starttag(self,tag,attrs):
        if tag=="th":
            self.collect_th=True;self.th_parts=[]
        if tag=="td":
            ident=dict(attrs).get("id")
            if ident=="present_area":
                self.active="present_area";self.parts=[]
            elif self.next_site_td:
                self.active="site_address";self.parts=[];self.next_site_td=False
    def handle_data(self,data):
        if self.collect_th:self.th_parts.append(data)
        if self.active:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=="th" and self.collect_th:
            self.next_site_td="소재지" in "".join(self.th_parts)
            self.collect_th=False;self.th_parts=[]
        if tag=="td" and self.active:
            value=" ".join("".join(self.parts).split())
            if value and (not self.fields.get(self.active)):
                self.fields[self.active]=value
            self.active=None;self.parts=[]

def parse_eum(html_bytes,pnu):
    text=html_bytes.decode("euc-kr",errors="replace")
    if pnu not in text:
        raise SiteHold("EUM_PNU_NOT_PRESENT_IN_RESPONSE")
    parsed=EumFields();parsed.feed(text)
    fields=parsed.fields
    raw=fields.get("present_area","")
    addr=fields.get("site_address","")
    if not addr:
        raise SiteHold("EUM_VISIBLE_SITE_ADDRESS_MISSING")
    match=re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)",raw)
    if not match:
        raise SiteHold("EUM_AREA_NOT_PRESENT","No numeric area in official detail page")
    area=float(match.group(1).replace(",",""))
    if not math.isfinite(area) or area<=0:
        raise SiteHold("EUM_AREA_INVALID")
    return {"pnu":pnu,"area_m2":area,"address":addr,
            "view_url":EUM+"?isNoScr=script&mode=search&pnu="+pnu+"&s_type=1&selGbn=umd",
            "evidence_sha256":digest(html_bytes),
            "source":"EUM_OFFICIAL_WEB_VIEW",
            "observed_at":now(),
            "document_status":"ONLINE_VIEW_NOT_LEGAL_CERTIFICATE",
            "parcel_identity_status":"VISIBLE_ADDRESS_REQUIRES_CADASTRAL_CROSS_CHECK"}

def preserve_raw(raw,raw_dir,pnu,kind,ext):
    """Immutable SHA-keyed original response; no credentials or request URLs stored."""
    root=Path(raw_dir);root.mkdir(parents=True,exist_ok=True)
    name=pnu+"_"+kind+"_"+digest(raw)+"."+ext
    path=root/name
    if not path.exists():
        path.write_bytes(raw)
    elif digest(path.read_bytes())!=digest(raw):
        raise SiteHold("RAW_HASH_COLLISION_OR_CHANGED_CONTENT")
    return str(path)

def fetch_eum(pnu,fetch=bounded_fetch,raw_dir=None):
    url=EUM+"?isNoScr=script&mode=search&pnu="+pnu+"&s_type=1&selGbn=umd"
    raw,media,status=fetch(url)
    if status!=200:raise SiteHold("EUM_HTTP_STATUS:"+str(status))
    raw_path=preserve_raw(raw,raw_dir,pnu,"EUM","html") if raw_dir else None
    record=parse_eum(raw,pnu)
    if raw_path:record["raw_ref"]=raw_path
    return record

def parse_vworld(data,pnu,crs="EPSG:5186"):
    # VWorld GetFeature responds with GeoJSON nested in response.result.featureCollection.
    if data.get("response",{}).get("status")=="ERROR" or data.get("response",{}).get("error"):
        raise SiteHold("VWORLD_PROVIDER_ERROR")
    collection=(data.get("response",{}).get("result",{}) or {}).get("featureCollection") or {}
    features=collection.get("features") if isinstance(collection,dict) else None
    if not isinstance(features,list):
        # Also accept GeoJSON feature collections supplied as direct test fixtures.
        features=data.get("features") if data.get("type")=="FeatureCollection" else None
    if not isinstance(features,list):raise SiteHold("VWORLD_FEATURE_COLLECTION_NOT_FOUND")
    matches=[f for f in features if str((f.get("properties") or {}).get("pnu",""))==pnu]
    if len(matches)!=1:raise SiteHold("VWORLD_PNU_MATCH_NOT_EXACTLY_ONE",str(len(matches)))
    geometry=matches[0].get("geometry") or {}
    typ=geometry.get("type")
    coords=geometry.get("coordinates")
    if typ=="Polygon":
        rings=coords
    elif typ=="MultiPolygon" and isinstance(coords,list) and len(coords)==1:
        rings=coords[0]
    else:
        raise SiteHold("MULTIPART_OR_INVALID_PARCEL_REQUIRES_GEOMETRY_REVIEW")
    if not isinstance(rings,list) or len(rings)!=1:
        raise SiteHold("CADASTRAL_HOLES_REQUIRE_MULTIRING_ENGINE")
    ring=rings[0]
    if not isinstance(ring,list) or len(ring)<4:
        raise SiteHold("CADASTRAL_BOUNDARY_INVALID")
    if ring[0]==ring[-1]:
        ring=ring[:-1]
    if not all(isinstance(p,list) and len(p)>=2 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in p[:2]) for p in ring):
        raise SiteHold("CADASTRAL_COORDINATES_INVALID")
    if crs not in ("EPSG:5186","EPSG:5179"):
        raise SiteHold("CADASTRAL_PROJECTED_CRS_UNSUPPORTED")
    x0,y0=ring[0][:2]
    if abs(x0)<1000 or abs(y0)<1000:
        raise SiteHold("CADASTRAL_CRS_METADATA_SUSPECT")
    local=[[round(float(p[0])-x0,7),round(float(p[1])-y0,7)] for p in ring]
    try:
        from shapely.geometry import Polygon
        g=Polygon(local)
    except ImportError as exc:
        raise SiteHold("FREE_SHAPELY_DEPENDENCY_REQUIRED") from exc
    if not g.is_valid or g.area<=0:
        raise SiteHold("CADASTRAL_POLYGON_INVALID")
    return {"pnu":pnu,"polygon_local_m":local,"polygon_area_m2":g.area,
            "projected_crs":crs,"projected_origin_m":[x0,y0],
            "source":"VWORLD_LP_PA_CBND_BUBUN",
            "feature_properties":{k:v for k,v in (matches[0].get("properties") or {}).items() if k in {"pnu","jibun","addr"}}}

def fetch_vworld(pnu,key,domain="",fetch=bounded_fetch,raw_dir=None):
    if not key:raise SiteHold("VWORLD_FREE_API_KEY_NOT_CONFIGURED")
    args={"service":"data","request":"GetFeature","data":"LP_PA_CBND_BUBUN",
          "key":key,"attrFilter":"pnu:=:"+pnu,"format":"json","crs":"EPSG:5186"}
    if domain:args["domain"]=domain
    # URL contains a credential: never return/print this URL, including exceptions.
    url=VWORLD+"?"+urllib.parse.urlencode(args)
    try:raw,media,status=fetch(url)
    except Exception as exc:raise SiteHold("VWORLD_NETWORK_ERROR",type(exc).__name__) from None
    if status!=200:raise SiteHold("VWORLD_HTTP_ERROR",str(status))
    raw_path=preserve_raw(raw,raw_dir,pnu,"VWORLD","json") if raw_dir else None
    try:data=json.loads(raw.decode("utf-8-sig"))
    except Exception:raise SiteHold("VWORLD_JSON_INVALID") from None
    out=parse_vworld(data,pnu)
    out["evidence_sha256"]=digest(raw)
    out["observed_at"]=now()
    if raw_path:out["raw_ref"]=raw_path
    return out

def parse_vworld_address(data,address):
    """Resolve *parcel-address* to a 19-digit PNU; no building/road centroid guessing."""
    resp=data.get("response") or {}
    if resp.get("status")!="OK" or resp.get("error"):
        raise SiteHold("VWORLD_ADDRESS_NOT_RESOLVED")
    refined=resp.get("refined") or {}
    structure=refined.get("structure") or {}
    pnu=str(structure.get("level4LC") or "")
    refined_text=str(refined.get("text") or "")
    if not PNU_RE.fullmatch(pnu):
        raise SiteHold("VWORLD_PARCEL_ADDRESS_PNU_NOT_FOUND")
    if not refined_text:
        raise SiteHold("VWORLD_PARCEL_ADDRESS_NOT_REFINED")
    return {"pnu":pnu,"input_address":address,"refined_address":refined_text,
            "method":"VWORLD_PARCEL_GETCOORD_REFINED_PNU",
            "identity_status":"UNVERIFIED_UNTIL_EUM_AND_CADASTRAL_MATCH"}


def fetch_vworld_address(address,key,domain="",fetch=bounded_fetch,raw_dir=None):
    if not key:raise SiteHold("VWORLD_FREE_API_KEY_NOT_CONFIGURED")
    address=str(address or "").strip()
    if not address or len(address)>200:raise SiteHold("PARCEL_ADDRESS_REQUIRED")
    args={"service":"address","request":"getCoord","type":"PARCEL",
          "refine":"true","simple":"false","format":"json",
          "address":address,"key":key}
    if domain:args["domain"]=domain
    url="https://api.vworld.kr/req/address?"+urllib.parse.urlencode(args)
    try:raw,media,status=fetch(url)
    except Exception as exc:raise SiteHold("VWORLD_ADDRESS_NETWORK_ERROR",type(exc).__name__) from None
    if status!=200:raise SiteHold("VWORLD_ADDRESS_HTTP_ERROR",str(status))
    try:data=json.loads(raw.decode("utf-8-sig"))
    except Exception:raise SiteHold("VWORLD_ADDRESS_JSON_INVALID") from None
    result=parse_vworld_address(data,address)
    if raw_dir:result["raw_ref"]=preserve_raw(raw,raw_dir,result["pnu"],"VWORLD_ADDRESS","json")
    result["evidence_sha256"]=digest(raw)
    return result


def _normalize_address(value):
    """Conservative parcel identity check; uncertain matches always HOLD."""
    v="".join(str(value or "").split())
    for a,b in (("서울특별시","서울"),("서울시","서울"),
                ("경기도","경기"),("인천광역시","인천"),("부산광역시","부산")):
        v=v.replace(a,b)
    return v.replace("번지","").replace("번","")


def _eum_cadastral_address_match(eum,parcel):
    official=_normalize_address(eum.get("address"))
    cadastral=_normalize_address((parcel.get("feature_properties") or {}).get("addr"))
    return bool(official and cadastral and official==cadastral)


def build(source,*,eum_fetch=fetch_eum,vworld_fetch=fetch_vworld,
          address_fetch=fetch_vworld_address):
    if source.get("schema")!="ARCHIGROW_SITE_SOURCE_INPUT_V1":
        raise SiteHold("SCHEMA_UNSUPPORTED")
    project_id=str(source.get("project_id") or "").strip()
    if not project_id:raise SiteHold("PROJECT_ID_REQUIRED")
    pnu=str(source.get("pnu") or "").strip()
    address=str(source.get("parcel_address") or "").strip()
    key=os.environ.get("VWORLD_KEY") or os.environ.get("VWORLD_API_KEY") or ""
    resolved=None
    if not pnu and address:
        if not key:raise SiteHold("VWORLD_FREE_API_KEY_NOT_CONFIGURED")
        resolved=address_fetch(address,key,os.environ.get("VWORLD_DOMAIN",""))
        pnu=resolved["pnu"]
    if not PNU_RE.fullmatch(pnu):raise SiteHold("PNU_19_DIGITS_REQUIRED")
    # The source identity is the 19-digit PNU. Never infer it from a road centroid.
    # EUM precedes polygon comparison so the HTML evidence survives missing credentials.
    eum=eum_fetch(pnu)
    if resolved and _normalize_address(resolved["refined_address"])!=_normalize_address(eum["address"]):
        return {"status":"HOLD","failure_class":"VWORLD_GEOCODE_EUM_ADDRESS_MISMATCH",
                "project_id":project_id,"pnu":pnu,"address_resolution":resolved,"eum":eum}
    if not key:
        return {"status":"HOLD","failure_class":"VWORLD_FREE_API_KEY_NOT_CONFIGURED",
                "project_id":project_id,"pnu":pnu,"eum":eum,
                "address_resolution":resolved,
                "area_identity_status":"UNVERIFIED_NO_CADASTRAL_CROSS_CHECK",
                "next_route":"CONFIGURE_EXISTING_VWORLD_KEY_IN_LOCAL_SECRET_ENV"}
    parcel=vworld_fetch(pnu,key,os.environ.get("VWORLD_DOMAIN",""))
    if not _eum_cadastral_address_match(eum,parcel):
        return {"status":"HOLD","failure_class":"EUM_VISIBLE_ADDRESS_CADASTRAL_MISMATCH",
                "project_id":project_id,"pnu":pnu,"eum":eum,"parcel":parcel,
                "area_identity_status":"UNVERIFIED_ADDRESS_MISMATCH"}
    eum["parcel_identity_status"]="VISIBLE_ADDRESS_MATCHES_PNU_BOUND_CADASTRAL"
    delta=parcel["polygon_area_m2"]-eum["area_m2"]
    limit=max(1.0,eum["area_m2"]*0.005)
    comparison={"eum_area_m2":eum["area_m2"],
                "cadastral_polygon_area_m2":parcel["polygon_area_m2"],
                "delta_m2":delta,"tolerance_m2":limit,
                "result":"MATCH_WITHIN_SCREENING_TOLERANCE" if abs(delta)<=limit else "HOLD_AREA_MISMATCH"}
    result={"status":"PASS" if abs(delta)<=limit else "HOLD",
            "failure_class":None if abs(delta)<=limit else "OFFICIAL_AREA_VS_GEOMETRY_MISMATCH",
            "project_id":project_id,"pnu":pnu,"eum":eum,"parcel":parcel,
            "address_resolution":resolved,"comparison":comparison}
    if result["status"]!="PASS":return result
    c=source.get("constraints") or {}
    # No guessed FAR/BCR/zoning. Area from EUM is used explicitly and separately.
    if any(k not in c for k in ("max_coverage_pct","max_far_pct","target_far_counted_area_m2","floor_count","floor_to_floor_m","demo_clearance_m")):
        result.update(status="HOLD",failure_class="DESIGN_PARAMETERS_MISSING")
        return result
    result["massing_input"]={
        "schema":"ARCHIGROW_MASSING_INPUT_V1","project_id":project_id,
        "source_role":"PUBLIC_PARCEL_EUM_AREA_WITH_UNVERIFIED_DESIGN_CONSTRAINTS",
        "rule_source_status":"UNVERIFIED_DEMO","coordinate_units":"m",
        "site_polygon":parcel["polygon_local_m"],
        "site_area_basis":{"area_m2":eum["area_m2"],"pnu":pnu,
                           "source":"LAND_USE_EUM","evidence_sha256":eum["evidence_sha256"],
                           "observed_at":eum["observed_at"]},
        "coordinate_frame":{"projected_crs":parcel["projected_crs"],
                            "projected_origin_m":parcel["projected_origin_m"]},
        "constraints":c,"strategies":source.get("strategies",["BALANCED","SCULPTURAL"]),
        "footprint_mode":"SITE_OFFSET",
    }
    return result

def run(source_path,outdir):
    inp=json.loads(Path(source_path).read_text(encoding="utf-8"))
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    raw_dir=outdir/"RAW"
    try:
        r=build(inp,
                eum_fetch=lambda p:fetch_eum(p,raw_dir=raw_dir),
                vworld_fetch=lambda p,k,d:fetch_vworld(p,k,d,raw_dir=raw_dir),
                address_fetch=lambda a,k,d:fetch_vworld_address(a,k,d,raw_dir=raw_dir))
    except SiteHold as ex:
        r={"status":"HOLD","failure_class":ex.code,"detail":ex.detail,
           "project_id":inp.get("project_id"),"pnu":inp.get("pnu")}
    r["raw_refs"]=sorted(str(p) for p in raw_dir.glob("*") if p.is_file()) if raw_dir.exists() else []
    (outdir/"site_source_receipt.json").write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    if r.get("status")=="PASS":
        (outdir/"massing_site_input.json").write_text(json.dumps(r["massing_input"],ensure_ascii=False,indent=2),encoding="utf-8")
    return r

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input");ap.add_argument("--out-dir",required=True)
    a=ap.parse_args();r=run(a.input,a.out_dir)
    print(json.dumps({"status":r["status"],"pnu":r.get("pnu"),"failure_class":r.get("failure_class"),
                      "eum_area_m2":(r.get("eum") or {}).get("area_m2"),
                      "comparison":r.get("comparison"),"output_dir":a.out_dir},
                     ensure_ascii=False))
    return 0 if r["status"]=="PASS" else 2
if __name__=="__main__":
    raise SystemExit(main())
