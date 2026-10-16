"""Single review-reference intake into TAKY_AI_WORKBENCH/REFERENCE.

Use for user-provided file or URL when they ask '검토해'.
Files are physically deposited exactly once by SHA-256 and linked to central
catalog. URLs without captured bytes are locator-only and NOT 'RAW acquired'.
This is a callable local gateway; future ChatGPT requests must invoke it via
available tools (it is not a permanent chat event listener).
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,sqlite3,sys
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import taky_central_source_factory as factory
BASE=Path(r"D:\Git PWA")
REFERENCE=BASE/"TAKY_AI_WORKBENCH"/"REFERENCE"
DB=REFERENCE/"99_CONTROL"/"SOURCE_UNIVERSE"/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3"
RECEIPTS=REFERENCE/"99_CONTROL"/"INTAKE_RECEIPTS"
MAP={"LEARNING":"10_LEARNING","ARCHITECTURE":"20_ARCHITECTURE",
     "AI_REFERENCE":"30_AI_TECH","DESIGN_ASSET":"40_DESIGN_MEDIA",
     "VOICE_MEDIA":"40_DESIGN_MEDIA"}
MAX_FILE_BYTES=1_000_000_000
@contextmanager
def managed_db(path):
    connection=factory.connect(path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()
def domain_bucket(label,name):
    domain=factory.domain_hint(name,label)
    return MAP.get(domain,"80_UNCLASSIFIED"),domain
def sanitize(s):
    s=re.sub(r'[<>:"/\\|?*\x00-\x1f]+',"_",str(s)).strip(". ")
    return s[:110] or "unnamed"
def sha(p):
    return factory.file_hash(p)
def receipt_file(sid):
    RECEIPTS.mkdir(parents=True,exist_ok=True)
    return RECEIPTS/(hashlib.sha256(sid.encode("utf-8")).hexdigest()[:32]+".json")
def persist(record):
    r=receipt_file(record["source_id"])
    temp=r.with_suffix(".json.tmp")
    temp.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    os.replace(temp,r)
def from_file(path,title=None,consumer=None,origin=None,warehouse=REFERENCE,db=DB):
    source=Path(path).expanduser().resolve()
    if not source.is_file():raise ValueError("INPUT_FILE_MISSING")
    if source.is_symlink():raise ValueError("UNREVIEWED_FILE_SYMLINK")
    size=source.stat().st_size
    if not 0<size<=MAX_FILE_BYTES:raise ValueError("INPUT_FILE_ZERO_OR_EXCESSIVE_SIZE")
    original_hash=sha(source)
    label=title or source.name
    category,domain=domain_bucket(label,source.name)
    with managed_db(db) as c:
        old=c.execute("""SELECT l.locator FROM source s JOIN location l ON s.id=l.source_id
          WHERE s.original_sha256=? AND l.provider='LOCAL_FILE'
          ORDER BY l.locator""",(original_hash,)).fetchall()
        physical=None
        for x in old:
            path=Path(x["locator"])
            if path.is_file() and path.resolve().is_relative_to(warehouse.resolve()) and sha(path)==original_hash:
                physical=path
                break
        reused=physical is not None
        if not physical:
            name=original_hash[:16]+"__"+sanitize(source.name)
            physical=warehouse/category/"FILES"/name
            if physical.exists() and sha(physical)!=original_hash:
                raise ValueError("SAME_NAME_DIFFERENT_SOURCE_COLLISION")
            physical.parent.mkdir(parents=True,exist_ok=True)
            if not physical.exists():
                temp=physical.with_name(physical.name+".pending."+str(os.getpid()))
                try:
                    shutil.copyfile(source,temp)
                    if sha(temp)!=original_hash:raise RuntimeError("INTAKE_SHA_COPY_MISMATCH")
                    os.replace(temp,physical)
                finally:
                    temp.unlink(missing_ok=True)
        sid=factory.register(c,"LOCAL_FILE","TAKY_WORKBENCH_REFERENCE",
          str(physical),physical.name,"REFERENCE_PENDING_REVIEW",
          sha=original_hash,size=size,
          modified=str(physical.stat().st_mtime_ns),
          meta={"title":label,"source_filename":source.name,
            "original_upload_path":str(source),"source_url":origin,
            "verified_byte_hash":True,"category_heuristic":category,
            "approval":"NOT_GRANTED_BY_INTAKE"},domain=domain,consumer=consumer)
        factory.put_stage(c,sid,"ANALYZE","PENDING",{"origin":"USER_REVIEW_INTAKE"})
        factory.put_stage(c,sid,"REVIEW","WAITING_EVIDENCE_REVIEW",{"original_sha256":original_hash})
        factory.put_stage(c,sid,"FORMING","BLOCKED_PENDING_REVIEW",{})
        factory.put_stage(c,sid,"LEARNING","BLOCKED_FORMING",{})
        factory.put_stage(c,sid,"CONSUME","BLOCKED_UNAPPROVED",{})
        factory.event(c,sid,"REVIEW_ATTACHMENT_RECEIVED",
          {"source_kind":"FILE","title":label,"external_source":str(source),
           "canonical_ref":str(physical),"duplicate_physical_bytes_avoided":reused})
    record={"schema":"TAKY_REFERENCE_REVIEW_INTAKE_V1","kind":"FILE",
      "source_id":sid,"category":category,"provisional_domain":domain,
      "canonical_path":str(physical),"sha256":original_hash,"bytes":size,
      "title":label,"source_reference":str(source),"consumer":consumer,
      "new_physical_copy_created":not reused,
      "review_state":"WAITING_EVIDENCE_REVIEW","learning_state":"NOT_APPROVED"}
    if warehouse==REFERENCE and db==DB:persist(record)
    return record
def from_url(url,title=None,consumer=None,warehouse=REFERENCE,db=DB):
    parsed=urlsplit(url)
    if parsed.scheme.lower() not in ("https","http") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("INVALID_PUBLIC_REFERENCE_URL")
    if len(url)>4096:raise ValueError("URL_TOO_LONG")
    label=title or parsed.hostname+parsed.path.rsplit("/",1)[-1]
    category,domain=domain_bucket(label,parsed.hostname)
    with managed_db(db) as c:
        sid=factory.register(c,"WEB_URL","USER_REVIEW",url,label,
          "REFERENCE_URL_PENDING_CAPTURE",meta={
            "source_url":url,"reference_origin":"USER_MESSAGE",
            "category_heuristic":category,"snapshot_attached":False},domain=domain,
          consumer=consumer)
        factory.put_stage(c,sid,"EXTRACT","WAITING_RAW_BYTES",{})
        factory.put_stage(c,sid,"REVIEW","PENDING_FETCH_AND_VALIDATION",{})
        factory.put_stage(c,sid,"FORMING","BLOCKED_RAW_MISSING",{})
        factory.put_stage(c,sid,"LEARNING","BLOCKED_RAW_MISSING",{})
        factory.event(c,sid,"REVIEW_WEBSITE_RECEIVED",{"url":url,"title":label,
          "original_bytes_acquired":False})
    record={"schema":"TAKY_REFERENCE_REVIEW_INTAKE_V1","kind":"URL",
      "source_id":sid,"url":url,"title":label,"category":category,
      "provisional_domain":domain,"physical_snapshot_acquired":False,
      "capture_state":"PENDING_RAW_ACQUISITION","learning_state":"BLOCKED"}
    if warehouse==REFERENCE and db==DB:persist(record)
    return record
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file")
    group.add_argument("--url")
    parser.add_argument("--title")
    parser.add_argument("--consumer")
    parser.add_argument("--origin-url")
    args=parser.parse_args()
    if args.file:r=from_file(args.file,args.title,args.consumer,args.origin_url)
    else:r=from_url(args.url,args.title,args.consumer)
    print(json.dumps({k:v for k,v in r.items() if k not in ("source_reference",)},
      ensure_ascii=False,indent=2))
