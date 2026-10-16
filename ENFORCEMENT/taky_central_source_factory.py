#!/usr/bin/env python3
"""TAKY Central Source Factory V1 — ONE durable queue/index, multiple evidence sources.

All project/Drive inputs converge into one SQLite registry and append-only events.
Physical RAW must be hashed. Drive metadata is a locator, not mined RAW.
FORMING and LEARNING are gated by verified, reviewed evidence and existing owners.
No cloud downloads, paid APIs, auto promotion, user data writes, push or deploy.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import sqlite3
import sys

ROOT=Path(r"D:\Git PWA")
VAULT=ROOT/"TAKY-SOURCE-VAULT"
WAREHOUSE=ROOT/"TAKY_AI_WORKBENCH"/"REFERENCE"
DB=WAREHOUSE/"99_CONTROL"/"SOURCE_UNIVERSE"/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3"
DRIVE=ROOT/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"CROSS_STORAGE_DRIVE_METADATA_DISCOVERY_20261013.json"
REFERENCE=ROOT/"TAKY_AI_WORKBENCH"/"00_CONTROL"/"TAKY_REFERENCE_UNIVERSE_INDEX.json"
ARCHIVE=WAREHOUSE
LEGACY_ARCHIVE=ROOT/"TAKY_ARCHI GROW"/"SOURCE_ARCHIVE"
ARCHIVE_RECEIPT=VAULT/"data"/"source_universe"/"WEB_SOURCE_ARCHIVE_REHOME_RECEIPT.json"
STAGES=("ACQUIRE","VERIFY","EXTRACT","ANALYZE","REVIEW","INDEX","FORMING","LEARNING","CONSUME")
IMAGE_SUFFIX={".png",".jpg",".jpeg",".webp",".gif",".svg",".bmp"}
TEXT_SUFFIX={".txt",".md",".csv",".tsv",".json",".jsonl",".html",".htm",".xml"}
PRIVATE_ROLE=("USER_DATA","RUNTIME","AUTH","TOKEN","PASSWORD","CREDENTIAL")
MAX_EXTRACT_BYTES=512_000

def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
def hashbytes(data):
    return hashlib.sha256(data).hexdigest()
def file_hash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(262144),b""):h.update(b)
    return h.hexdigest()
def compact(data):
    return json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def stable_id(prefix,value):
    return prefix+":"+hashbytes(value.encode("utf-8"))[:32]
def bounded(v,lim=500):
    return str(v or "")[:lim]
def domain_hint(name,context=""):
    s=(name+" "+context).casefold()
    # Untrusted heuristic for routing only. It is not an approved semantic claim.
    # "archive" contains the letters "archi" but is not an architecture term.
    architecture_words=("건축","cad","architecture","도면","오토캐드","심의","공모")
    architecture_prefix=re.search(r"(?<![a-z])archi(?:tect|grow|comp|cad|[\W_]|$)",s)
    if any(x in s for x in architecture_words) or architecture_prefix:
        return "ARCHITECTURE"
    if any(x in s for x in ("교육","영어","한자","한글","school","learning","vocab","학습","수학","과학","교과")):
        return "LEARNING"
    if any(x in s for x in ("audio","voice","음성","tts","wav","mp3")):
        return "VOICE_MEDIA"
    # Strong AI-operations context wins over generic 'design' (system design).
    if re.search(r"(?<![a-z])ai(?![a-z])",s) and any(
        x in s for x in ("continuity","agent","orchestration","llm","model routing","governance","a2a")
    ):
        return "AI_REFERENCE"
    if (any(x in s for x in ("design","badge","asset","visual","시안","에셋"))
        or re.search(r"(?<![a-z])ui(?![a-z])",s)):
        return "DESIGN_ASSET"
    if any(x in s for x in ("github","claude","codex","ai","mining","index","pipeline","mcp")):
        return "AI_REFERENCE"
    return "UNCLASSIFIED"
def kind_hint(name,mime=""):
    x=Path(name).suffix.casefold()
    if x in IMAGE_SUFFIX:return "IMAGE"
    if x in (".wav",".mp3",".m4a",".ogg"):return "AUDIO"
    if x in (".mp4",".mov",".avi",".mkv"):return "VIDEO"
    if x==".pdf" or mime=="application/pdf":return "PDF"
    if x in (".xls",".xlsx",".csv"):return "TABLE"
    if x in TEXT_SUFFIX:return "TEXT"
    if x in (".json",".jsonl"):return "STRUCTURED"
    if x in (".lsp",".py",".js",".ts",".ps1"):return "CODE"
    return "BINARY_OR_UNKNOWN"

def connect(path=DB):
    path.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(str(path),timeout=10)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=10000")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS source(
      id TEXT PRIMARY KEY, original_sha256 TEXT, status TEXT NOT NULL,
      domain_hint TEXT NOT NULL, media_kind TEXT NOT NULL,
      authoritative_review TEXT NOT NULL DEFAULT 'UNREVIEWED',
      created_at TEXT NOT NULL, changed_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS location(
      provider TEXT NOT NULL, account TEXT NOT NULL, locator TEXT NOT NULL,
      source_id TEXT NOT NULL REFERENCES source(id), name TEXT NOT NULL,
      source_role TEXT NOT NULL, trust TEXT NOT NULL,
      size_bytes INTEGER, modified TEXT, metadata_json TEXT NOT NULL,
      PRIMARY KEY(provider,account,locator));
    CREATE INDEX IF NOT EXISTS location_source ON location(source_id);
    CREATE TABLE IF NOT EXISTS stage(
      source_id TEXT NOT NULL REFERENCES source(id),
      stage TEXT NOT NULL, state TEXT NOT NULL, receipt_json TEXT NOT NULL,
      updated_at TEXT NOT NULL, PRIMARY KEY(source_id,stage));
    CREATE INDEX IF NOT EXISTS stage_pending ON stage(stage,state,updated_at);
    CREATE TABLE IF NOT EXISTS evidence(
      source_id TEXT PRIMARY KEY REFERENCES source(id), raw_sha256 TEXT NOT NULL,
      parse_state TEXT NOT NULL, summary TEXT, index_terms TEXT NOT NULL,
      modified_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS evidence_unit(
      source_id TEXT NOT NULL REFERENCES source(id),
      unit_id TEXT NOT NULL,
      raw_sha256 TEXT NOT NULL,
      line_start INTEGER NOT NULL,
      line_end INTEGER NOT NULL,
      content_sha256 TEXT NOT NULL,
      excerpt TEXT NOT NULL,
      review_state TEXT NOT NULL DEFAULT 'EXTRACTIVE_UNREVIEWED',
      PRIMARY KEY(source_id,unit_id),
      CHECK(line_start >= 1),
      CHECK(line_end >= line_start)
    );
    CREATE INDEX IF NOT EXISTS evidence_unit_source_anchor ON evidence_unit(source_id,line_start);
    CREATE TABLE IF NOT EXISTS event(
      event_id INTEGER PRIMARY KEY AUTOINCREMENT, happened_at TEXT NOT NULL,
      source_id TEXT, kind TEXT NOT NULL, detail_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS relation(
      source_id TEXT NOT NULL REFERENCES source(id), consumer TEXT NOT NULL,
      relation_type TEXT NOT NULL, PRIMARY KEY(source_id,consumer,relation_type));
    CREATE TABLE IF NOT EXISTS run(
      run_id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL,
      operation TEXT NOT NULL, result_json TEXT);
    """)
    return c
def find_evidence_units(c, query, *, source_id=None, limit=25):
    """Bounded read-only search of exact hash/line-bound RAW units.

    Return source links and spans, never executable instructions or authority.
    """
    if not isinstance(query,str) or len(query.strip())<2 or len(query)>160:
        raise ValueError("DETAIL_QUERY_INVALID")
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=100:
        raise ValueError("DETAIL_LIMIT_INVALID")
    term=query.strip().casefold().replace("\\","\\\\").replace("%","\\%").replace("_","\\_")
    args=["%"+term+"%"]
    where="LOWER(u.excerpt) LIKE ? ESCAPE '\\'"
    if source_id is not None:
        if not isinstance(source_id,str) or len(source_id)>100:
            raise ValueError("DETAIL_SOURCE_ID_INVALID")
        where+=" AND u.source_id=?"
        args.append(source_id)
    args.append(limit)
    rows=c.execute(f"""SELECT u.source_id,u.unit_id,u.line_start,u.line_end,
       u.content_sha256,u.raw_sha256,u.excerpt,u.review_state,
       s.status,s.authoritative_review,l.locator AS raw_locator
       FROM evidence_unit u JOIN source s ON s.id=u.source_id
       JOIN location l ON l.source_id=u.source_id
            AND l.provider='LOCAL_FILE' AND l.account='TAKY_REVIEW_RAW'
       WHERE {where} ORDER BY u.source_id,u.line_start LIMIT ?""",args).fetchall()
    return [dict(r) for r in rows]

def read_verified_evidence_unit(c,source_id,unit_id, *, max_raw_bytes=8_000_000):
    """Resolve a hash-bound DETAIL anchor back to the exact source RAW.

    Reading original bytes is necessary: excerpts are only search hints.
    """
    if (not isinstance(source_id,str) or len(source_id)>100
        or not isinstance(unit_id,str) or len(unit_id)>100):
        raise ValueError("DETAIL_ID_INVALID")
    row=c.execute("""SELECT u.*,l.locator,s.authoritative_review
       FROM evidence_unit u JOIN source s ON s.id=u.source_id
       JOIN location l ON l.source_id=u.source_id
       WHERE u.source_id=? AND u.unit_id=? AND l.provider='LOCAL_FILE'
         AND l.account='TAKY_REVIEW_RAW'""",(source_id,unit_id)).fetchone()
    if row is None:return None
    locator=Path(row["locator"])
    if (not locator.is_file() or locator.stat().st_size>max_raw_bytes
        or file_hash(locator)!=row["raw_sha256"]):
        raise ValueError("DETAIL_SOURCE_RAW_HASH_MISMATCH")
    lines=locator.read_text(encoding="utf-8-sig").splitlines()
    start=row["line_start"];end=row["line_end"]
    if not 1<=start<=end<=len(lines):
        raise ValueError("DETAIL_SOURCE_ANCHOR_OUT_OF_RANGE")
    text="\n".join(lines[start-1:end]).strip()
    if hashbytes(text.encode("utf-8"))!=row["content_sha256"]:
        raise ValueError("DETAIL_SOURCE_UNIT_HASH_MISMATCH")
    return {
      "source_id":source_id,"unit_id":unit_id,
      "source_path":str(locator),"raw_sha256":row["raw_sha256"],
      "line_start":start,"line_end":end,
      "content_sha256":row["content_sha256"],
      "content":text,"review_state":row["review_state"],
      "source_authority":row["authoritative_review"],
      "forming_authorized":False,"learning_promoted":False
    }

def event(c,sid,kind,detail):
    c.execute("INSERT INTO event(happened_at,source_id,kind,detail_json) VALUES(?,?,?,?)",
      (utc(),sid,kind,compact(detail)))
def put_stage(c,sid,stage,state,details=None):
    old=c.execute("SELECT state,receipt_json FROM stage WHERE source_id=? AND stage=?",
      (sid,stage)).fetchone()
    payload=compact(details or {})
    if old and old["state"]==state and old["receipt_json"]==payload:return False
    c.execute("""INSERT INTO stage VALUES(?,?,?,?,?)
      ON CONFLICT(source_id,stage) DO UPDATE SET state=excluded.state,
      receipt_json=excluded.receipt_json, updated_at=excluded.updated_at""",
      (sid,stage,state,payload,utc()))
    event(c,sid,"STAGE_CHANGE",{"stage":stage,"state":state,"details":details or {}})
    return True

def register(c,provider,account,locator,name,role,sha=None,size=None,modified=None,meta=None,domain=None,consumer=None):
    if not all([provider,account,locator,name]):raise ValueError("SOURCE_LOCATOR_REQUIRED")
    if sha and not re.fullmatch("[0-9a-fA-F]{64}",sha):raise ValueError("INVALID_RAW_SHA256")
    sha=sha.lower() if sha else None
    existing_unchanged=c.execute("""SELECT source_id,size_bytes,modified FROM location
      WHERE provider=? AND account=? AND locator=?""",(provider,account,locator)).fetchone()
    if sha:
        sid="raw:"+sha
    elif existing_unchanged and existing_unchanged["size_bytes"]==size and existing_unchanged["modified"]==modified:
        sid=existing_unchanged["source_id"]  # Preserve identity across physical rehome.
    else:
        sid=stable_id("location",provider+"\0"+account+"\0"+locator+"\0"+str(modified or "")+"\0"+str(size or ""))
    excluded=role.startswith("EXCLUDED") or any(x in role.upper() for x in PRIVATE_ROLE)
    old=c.execute("SELECT id,original_sha256,status FROM source WHERE id=?",(sid,)).fetchone()
    status="EXCLUDED_OPERATIONAL" if excluded else ("RAW_VERIFIED" if sha else "RAW_NOT_VERIFIED")
    if not old:
        c.execute("INSERT INTO source VALUES(?,?,?,?,?,?,?,?)",
          (sid,sha,status,domain or domain_hint(name,role),kind_hint(name, (meta or {}).get("mime_type","")),
           "UNREVIEWED",utc(),utc()))
        event(c,sid,"SOURCE_REGISTERED",{"provider":provider,"account":account,"role":role,"quality":status})
    elif (old["status"]!=status and status=="RAW_VERIFIED"
          and old["status"]!="INDEXED_CANDIDATE"):
        # Same content SHA can be rediscovered at multiple paths. Re-registration
        # is an idempotent location update, not a reason to demote an indexed
        # candidate back to RAW_VERIFIED.
        c.execute("UPDATE source SET status=?,original_sha256=?,changed_at=? WHERE id=?",
          (status,sha,utc(),sid))
    existing_loc=c.execute("SELECT source_id FROM location WHERE provider=? AND account=? AND locator=?",
     (provider,account,locator)).fetchone()
    if existing_loc and existing_loc["source_id"]!=sid:
        # Source byte revision changes create a new SHA source; the old event
        # remains immutable and former location linkage is superseded.
        event(c,existing_loc["source_id"],"LOCATION_SUPERSEDED",{"new_source":sid,"locator":locator})
        c.execute("DELETE FROM location WHERE provider=? AND account=? AND locator=?",
          (provider,account,locator))
        if c.execute("SELECT COUNT(*) FROM location WHERE source_id=?",(existing_loc["source_id"],)).fetchone()[0]==0:
            c.execute("UPDATE source SET status='SUPERSEDED' WHERE id=?",(existing_loc["source_id"],))
            event(c,existing_loc["source_id"],"SOURCE_NO_LONGER_CURRENT",{})
    c.execute("""INSERT INTO location VALUES(?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(provider,account,locator) DO UPDATE SET
      source_id=excluded.source_id,name=excluded.name,source_role=excluded.source_role,
      trust=excluded.trust,size_bytes=excluded.size_bytes,modified=excluded.modified,
      metadata_json=excluded.metadata_json""",
      (provider,account,locator,sid,name,role,"RAW_HASH_VERIFIED" if sha else "METADATA_ONLY",
       size,modified,compact(meta or {})))
    if consumer:
        c.execute("INSERT OR IGNORE INTO relation VALUES(?,?,?)",(sid,consumer,"REFERENCE_CONSUMER"))
    put_stage(c,sid,"ACQUIRE","DONE" if sha else ("EXCLUDED" if excluded else "LOCATOR_ONLY"),
      {"role":role,"bytes_available":bool(sha)})
    put_stage(c,sid,"VERIFY","DONE" if sha else ("EXCLUDED" if excluded else "WAITING_RAW_BYTES"),
      {"sha256":sha} if sha else {"reason":"RAW_NOT_ACQUIRED"})
    if sha:
        existing_extract=c.execute(
            "SELECT state FROM stage WHERE source_id=? AND stage='EXTRACT'",
            (sid,)).fetchone()
        # A re-seen SHA must never reset DONE/OCR/SPECIALIST/reviewed work.
        # Only genuinely new or unresolved-byte records enter the pending queue.
        if existing_extract is None or existing_extract["state"] in (
            "WAITING_RAW_BYTES","HOLD_EMPTY_OR_MISSING_RAW"):
            put_stage(c,sid,"EXTRACT","PENDING",{"hash_bound":sha})
    elif not excluded:
        put_stage(c,sid,"EXTRACT","WAITING_RAW_BYTES",{})
    return sid

def ingest_drive(c,doc):
    if doc.get("schema")!="TAKY_CROSS_STORAGE_DRIVE_DISCOVERY_V1":
        raise ValueError("DRIVE_DISCOVERY_SCHEMA_INVALID")
    seen=0;excluded=0;folders=0
    for scope in doc.get("folders",[]):
        account=scope.get("account")
        role=scope.get("role","UNREVIEWED")
        group=scope.get("group","UNKNOWN")
        for it in scope.get("files",[]):
            fileid=it.get("file_id")
            name=it.get("name")
            if not fileid or not name:continue
            if it.get("kind")=="folder":
                folders+=1
                # a folder is a traversal frontier, never a byte-acquired file.
                continue
            excluded_role=(role in ("MIXED_EXCLUDE_RUNTIME","ASSET_AUTHORITY_NOT_REFERENCE",
                "INDEX_NOT_RAW","PROJECT_DATA_NOT_REFERENCE") or
               (account=="SIEZEALL" and role not in ("REFERENCE_SHARE",)) )
            source_role="EXCLUDED_OPERATIONAL" if excluded_role else role
            register(c,"GOOGLE_DRIVE",account,fileid,name,source_role,
              size=int(it["size_bytes"]) if str(it.get("size_bytes","")).isdigit() else None,
              modified=it.get("modified"),meta={"mime_type":it.get("mime_type"),"folder_id":scope.get("id"),
                 "discovery_group":group,"source_file_id":fileid},
              consumer=None)
            seen+=1;excluded+=int(excluded_role)
    event(c,None,"DRIVE_DISCOVERY_IMPORTED",{"registered":seen,"excluded":excluded,"folders_skipped":folders})
    return {"file_locations":seen,"excluded_operational":excluded,"folders_traversal_frontier":folders}

def ingest_references(c,doc):
    if doc.get("schema")!="TAKY_GLOBAL_REFERENCE_UNIVERSE_INDEX_V1":
        raise ValueError("REFERENCE_UNIVERSE_SCHEMA_INVALID")
    touched=0;unique=set()
    for x in doc.get("items",[]):
        fp=Path(x["physical_path"] if "physical_path" in x else x["canonical_path"])
        root=Path(doc["single_physical_root"]).resolve()
        if not fp.resolve().is_relative_to(root):raise ValueError("REFERENCE_OUTSIDE_ROOT")
        if not fp.is_file() or file_hash(fp)!=x["sha256"]:
            raise ValueError("REFERENCE_HASH_MISMATCH:"+x["relative_path"])
        sid=register(c,"LOCAL_FILE","TAKY_SOURCE_VAULT",str(fp),fp.name,
          "REFERENCE_"+x.get("role","CANDIDATE"),sha=x["sha256"],size=fp.stat().st_size,
          modified=str(fp.stat().st_mtime_ns),meta={"relative_path":x["relative_path"],
          "approved":False,"verified_input_index":True},
          consumer="TAKY_ARCHI GROW")
        touched+=1;unique.add(sid)
    event(c,None,"VERIFIED_LOCAL_REFERENCE_IMPORTED",{"file_paths":touched,"unique_hashes":len(unique)})
    return {"file_paths":touched,"unique_sources":len(unique)}

def discover_archive(c,path,limit=15000,allowed_root=ROOT):
    path=Path(path).resolve()
    if not path.is_dir():return {"state":"NOT_PRESENT","files":0}
    if not path.is_relative_to(Path(allowed_root).resolve()):
        raise ValueError("ARCHIVE_ROOT_OUTSIDE_WORKSPACE")
    seen=0
    for base,dirs,files in os.walk(path):
        dirs[:]=[d for d in dirs if d not in ("node_modules",".git","__pycache__",
          "00_INBOX","99_CONTROL","90_DERIVED","WEB_SOURCE_ARCHIVE",
          "ARCHCOMP_OUTPUT_BUILD_TEST","CLAUDE_SKILLS")
          and not (Path(base)/d).is_junction()]
        # Only physical domain-classified capture files, not compatibility
        # junctions or mutable pipeline state.
        if Path(base)==WAREHOUSE:
            dirs[:]=[d for d in dirs if d in
              ("10_LEARNING","20_ARCHITECTURE","30_AI_TECH",
               "40_DESIGN_MEDIA","50_GENERAL","80_UNCLASSIFIED")]
        for name in files:
            fp=Path(base)/name
            if fp.is_symlink():continue
            try:stat=fp.stat()
            except OSError:continue
            prior=c.execute("""SELECT l.size_bytes,l.modified,s.status FROM location l
              JOIN source s ON s.id=l.source_id
              WHERE l.provider='LOCAL_FILE' AND l.account='TAKY_SOURCE_ARCHIVE'
              AND l.locator=?""",(str(fp),)).fetchone()
            if prior and prior["size_bytes"]==stat.st_size and prior["modified"]==str(stat.st_mtime_ns):
                seen+=1
                if seen>=limit:
                    return {"state":"INCOMPLETE_LIMIT_REACHED","files":seen}
                continue
            register(c,"LOCAL_FILE","TAKY_SOURCE_ARCHIVE",str(fp),name,
              "WEB_SOURCE_ARCHIVE_UNVERIFIED",size=stat.st_size,
              modified=str(stat.st_mtime_ns),meta={
                "relative_path":fp.relative_to(path).as_posix(),"raw_sha256_verified":False},
              consumer="TAKY_ARCHI GROW")
            seen+=1
            if seen>=limit:
                event(c,None,"ARCHIVE_DISCOVERY_LIMIT",{"limit":limit,"path":str(path)})
                return {"state":"INCOMPLETE_LIMIT_REACHED","files":seen}
    event(c,None,"ARCHIVE_DISCOVERY_IMPORTED",{"files":seen,"path":str(path)})
    return {"state":"LOCAL_METADATA_REGISTERED_RAW_PENDING","files":seen}

def promote_local_hash(c,sid,locator,original_sha):
    # Merge metadata-only location into content source, retaining lineage.
    old=c.execute("SELECT * FROM location WHERE provider='LOCAL_FILE' AND locator=?",(locator,)).fetchone()
    if not old or old["source_id"]!=sid:return None
    new=register(c,"LOCAL_FILE",old["account"],locator,old["name"],old["source_role"],
       sha=original_sha,size=old["size_bytes"],modified=old["modified"],
       meta=json.loads(old["metadata_json"]),consumer="TAKY_ARCHI GROW")
    if sid!=new:
        old_count=c.execute("SELECT COUNT(*) AS n FROM location WHERE source_id=?",(sid,)).fetchone()["n"]
        if not old_count:
            event(c,sid,"SOURCE_HASH_RESOLVED",{"new_source":new})
    return new

def run_bounded(c,max_items=30,max_hash_bytes=20_000_000):
    if max_items<1 or max_items>1000 or max_hash_bytes<0 or max_hash_bytes>1_000_000_000:
        raise ValueError("RUN_BUDGET_INVALID")
    # Deterministic limited batches. Unverified local paths only; remote needs a
    # trusted downloader that attests bytes and origin identity.
    rows=c.execute("""SELECT l.*,s.id,s.status FROM location l
      JOIN source s ON s.id=l.source_id
      WHERE l.provider='LOCAL_FILE' AND s.original_sha256 IS NULL
      AND s.status!='EXCLUDED_OPERATIONAL'
      ORDER BY l.size_bytes ASC,l.locator LIMIT ?""",(max_items,)).fetchall()
    hashed=0;spent=0;changed=0;read_error=0
    for row in rows:
        size=row["size_bytes"] or 0
        if size<=0:
            put_stage(c,row["id"],"VERIFY","HOLD_EMPTY_OR_MISSING_RAW",{"reason":"ZERO_LENGTH_RAW"})
            c.execute("UPDATE source SET status='EMPTY_SOURCE_INCOMPLETE' WHERE id=?",(row["id"],))
            continue
        if size>max_hash_bytes-spent:continue
        path=Path(row["locator"])
        if not path.is_file():read_error+=1;continue
        try:
            before=path.stat()
            digest=file_hash(path)
            after=path.stat()
            if before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns:
                read_error+=1;continue
        except OSError:
            read_error+=1;continue
        spent+=after.st_size
        changed+=int(promote_local_hash(c,row["id"],row["locator"],digest) is not None)
        hashed+=1
    # Extract and classify only verified local source bytes. No inference from
    # pathnames can become approval or learning evidence.
    candidates=c.execute("""SELECT s.id,s.original_sha256,l.locator,l.name,l.source_role
      FROM source s JOIN location l ON s.id=l.source_id
      JOIN stage st ON st.source_id=s.id AND st.stage='EXTRACT'
      WHERE st.state='PENDING' AND l.provider='LOCAL_FILE' AND s.original_sha256 IS NOT NULL
      GROUP BY s.id ORDER BY l.size_bytes ASC LIMIT ?""",(max_items,)).fetchall()
    indexed=0;await_review=0
    for rec in candidates:
        fp=Path(rec["locator"])
        if not fp.is_file():continue
        try:
            if file_hash(fp)!=rec["original_sha256"]:
                put_stage(c,rec["id"],"VERIFY","SOURCE_CHANGED_REVERIFY_REQUIRED",{})
                continue
            size=fp.stat().st_size
            if size<=0:
                put_stage(c,rec["id"],"EXTRACT","HOLD_EMPTY_OR_MISSING_RAW",{})
                put_stage(c,rec["id"],"REVIEW","HOLD_EMPTY_OR_MISSING_RAW",{})
                c.execute("UPDATE source SET status='EMPTY_SOURCE_INCOMPLETE' WHERE id=?",(rec["id"],))
                continue
            suffix=fp.suffix.casefold()
            text=""
            if suffix in TEXT_SUFFIX and size<=MAX_EXTRACT_BYTES:
                text=fp.read_text(encoding="utf-8-sig",errors="replace")
            state="TEXT_CANDIDATE_EXTRACTED" if text else "BINARY_REQUIRES_SPECIALIST_EXTRACTION"
            hint=domain_hint(fp.name,rec["source_role"])
            words=re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}",text[:24000])
            freq=Counter(word.casefold() for word in words)
            keywords=[a for a,_ in freq.most_common(24)]
            summary=(" ".join(text.strip().split())[:400] if text else None)
            c.execute("""INSERT INTO evidence VALUES(?,?,?,?,?,?)
               ON CONFLICT(source_id) DO UPDATE SET raw_sha256=excluded.raw_sha256,
               parse_state=excluded.parse_state,summary=excluded.summary,
               index_terms=excluded.index_terms,modified_at=excluded.modified_at""",
               (rec["id"],rec["original_sha256"],state,summary,compact(keywords),utc()))
            put_stage(c,rec["id"],"EXTRACT","DONE" if text else "SPECIALIST_REQUIRED",
              {"extract_status":state,"size":size})
            put_stage(c,rec["id"],"ANALYZE","DRAFT_ONLY",
              {"method":"LOCAL_HEURISTIC","not_semantic_approved":True,"terms":keywords[:12]})
            put_stage(c,rec["id"],"REVIEW","WAITING_HUMAN_OR_AUTHORIZED_REVIEW",
              {"raw_sha256":rec["original_sha256"]})
            put_stage(c,rec["id"],"INDEX","TECHNICAL_INDEX_READY",
              {"domain_hint":hint,"content_verified":True,"deep_semantic_index":False})
            put_stage(c,rec["id"],"FORMING","BLOCKED_REVIEW_NOT_APPROVED",{})
            put_stage(c,rec["id"],"LEARNING","BLOCKED_FORMING_NOT_APPROVED",{})
            put_stage(c,rec["id"],"CONSUME","BLOCKED_NO_APPROVED_CONTRACT",{})
            c.execute("UPDATE source SET status='INDEXED_CANDIDATE',changed_at=? WHERE id=?",(utc(),rec["id"]))
            indexed+=1;await_review+=1
        except (OSError, UnicodeError):
            read_error+=1
    event(c,None,"BOUNDED_FACTORY_RUN",{"hashes_computed":hashed,
      "hash_bytes":spent,"indexed_candidates":indexed,"read_errors":read_error,
      "model_calls":0,"paid_api_calls":0})
    return {"local_hashes_computed":hashed,"local_hashed_bytes":spent,
        "technical_index_candidates":indexed,"review_queue_additions":await_review,
        "read_errors":read_error,"forming_auto_approved":0,"learning_auto_executed":0}

def report(c):
    stats={r["status"]:r["n"] for r in c.execute(
        "SELECT status,COUNT(*) AS n FROM source GROUP BY status")}
    source_count=c.execute("SELECT COUNT(*) FROM source").fetchone()[0]
    loc_count=c.execute("SELECT COUNT(*) FROM location").fetchone()[0]
    roles={r["source_role"]:r["n"] for r in c.execute(
        "SELECT source_role,COUNT(*) AS n FROM location GROUP BY source_role")}
    pending={r["stage"]+":"+r["state"]:r["n"] for r in c.execute(
        "SELECT stage,state,COUNT(*) AS n FROM stage GROUP BY stage,state")}
    by_origin={r["provider"]:r["n"] for r in c.execute(
        "SELECT provider,COUNT(*) AS n FROM location GROUP BY provider")}
    return {"schema":"TAKY_CENTRAL_SOURCE_FACTORY_STATUS_V1",
      "single_state_db":str(DB),"source_records":source_count,"source_locations":loc_count,
      "origin_locations":by_origin,"source_statuses":stats,"source_roles":roles,
      "stage_states":pending,"authority":"TAKY_CONTROL_PLANE_ONLY",
      "stages":["ACQUIRE","VERIFY","EXTRACT","ANALYZE","REVIEW","INDEX","FORMING","LEARNING","CONSUME"],
      "local_model_or_paid_api_calls":0,"hosted_runtime_wired":False,
      "not_ready_claims":["DRIVE_RAW_NOT_DOWNLOADED","FORMING_NOT_AUTO_APPROVED",
      "LEARNING_ENGINE_NOT_AUTO_CONSUMING","FULL_RECURSIVE_DRIVE_INVENTORY_NOT_COMPLETE"]}

def rehome_local_source_archive():
    """Same-volume physical move, no copy, preserving the old consumer path."""
    import subprocess
    target=ARCHIVE
    old=LEGACY_ARCHIVE
    if ARCHIVE_RECEIPT.is_file():
        receipt=json.loads(ARCHIVE_RECEIPT.read_text(encoding="utf-8-sig"))
        if (receipt.get("status")=="REHOMED" and target.is_dir() and old.is_dir()
           and os.path.samefile(old,target)):
            return {"status":"ALREADY_CENTRALIZED","file_count":receipt.get("file_count")}
    if target.exists() or not old.is_dir():
        raise RuntimeError("SOURCE_ARCHIVE_PATH_CONFLICT_OR_ABSENT")
    if old.is_symlink() or bool(os.stat(old,follow_symlinks=False).st_file_attributes & 0x400):
        raise RuntimeError("SOURCE_ARCHIVE_ALREADY_REPARSE_POINT")
    tracked=subprocess.run(["git","-C",str(ROOT/"TAKY_ARCHI GROW"),
      "ls-files","--","SOURCE_ARCHIVE"],capture_output=True,
      text=True,encoding="utf-8",timeout=20,check=True)
    if tracked.stdout.strip():
        raise RuntimeError("GIT_TRACKED_ARCHIVE_REHOME_FORBIDDEN")
    file_info=[]
    for base,folders,files in os.walk(old):
        for name in files:
            p=Path(base)/name
            if p.is_symlink() or bool(p.stat(follow_symlinks=False).st_file_attributes & 0x400):
                raise RuntimeError("REPARSE_FILE_IN_SOURCE_ARCHIVE")
            st=p.stat()
            file_info.append((p.relative_to(old).as_posix(),st.st_size))
    count=len(file_info)
    size=sum(x[1] for x in file_info)
    if count!=9094 or size!=2339941687:
        raise RuntimeError("ARCHIVE_INVENTORY_CHANGED_REQUIRE_REAUDIT:%s:%s"%(count,size))
    # A SHA sample checks pre/post references without reading all 2.34GB.
    file_info.sort()
    indices=sorted(set([0,count-1]+[int((count-1)*i/15) for i in range(16)]))
    sample={name:file_hash(old/name) for n in indices for name in [file_info[n][0]]}
    target.parent.mkdir(parents=True,exist_ok=True)
    if old.drive.casefold()!=target.drive.casefold():
        raise RuntimeError("CROSS_VOLUME_MOVE_WOULD_COPY")
    os.rename(old,target)
    try:
        cmd=subprocess.run(["cmd.exe","/c","mklink","/J",str(old),str(target)],
          capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=25)
        if cmd.returncode or not old.is_dir() or not os.path.samefile(old,target):
            raise RuntimeError("COMPAT_JUNCTION_CREATION_FAILED")
        for rel,hashval in sample.items():
            if file_hash(target/rel)!=hashval or file_hash(old/rel)!=hashval:
                raise RuntimeError("ARCHIVE_SAMPLE_HASH_DIFFERENCE:"+rel)
        after_count=0
        after_size=0
        for base,dirs,files in os.walk(target):
            for name in files:
                stat=(Path(base)/name).stat()
                after_count+=1;after_size+=stat.st_size
        if after_count!=count or after_size!=size:
            raise RuntimeError("ARCHIVE_POST_MOVE_INVENTORY_DRIFT")
        receipt={"status":"REHOMED",
          "canonical":str(target),"former_location":str(old),
          "file_count":count,"total_bytes":size,"pre_post_sample_sha256":sample,
          "validation":"ATOMIC_SAME_DISK_RENAME_FULL_COUNT_AND_SIZE_PLUS_18_SHA_SAMPLES",
          "full_2gb_sha256_scan":False,"duplicate_physical_copy_created":False,
          "drive_modified":False,"git_push":False}
        tmp=ARCHIVE_RECEIPT.with_suffix(".json.pending")
        tmp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        os.replace(tmp,ARCHIVE_RECEIPT)
        return {"status":"CENTRALIZED","file_count":count,"bytes":size,
          "sha_samples":len(sample),"canonical":str(target),
          "legacy_path_resolves":True}
    except BaseException:
        # On failure, do not leave a second physical copy.
        if target.exists() and not old.exists():
            os.rename(target,old)
        raise

def web_capture_verified_excerpt(folder,revision,max_chars=560):
    """Bounded extractive preview from the actual SHA-attested captured bytes."""
    method=revision.get("review_extract_method")
    if method not in ("ORIGINAL_RENDERED_TEXT","ORIGINAL_NOTION_BLOCKS"):
        return None
    source=folder/("source.txt" if method=="ORIGINAL_RENDERED_TEXT"
                   else "notion/blocks.json")
    if not source.is_file() or not 0<source.stat().st_size<=MAX_EXTRACT_BYTES:
        return None
    digest=revision.get("review_evidence_sha256")
    if not digest or file_hash(source)!=digest:
        raise ValueError("WEB_CAPTURE_ORIGINAL_EXCERPT_SHA256_MISMATCH")
    if method=="ORIGINAL_RENDERED_TEXT":
        body=source.read_text(encoding="utf-8-sig",errors="replace")
    else:
        blocks=json.loads(source.read_text(encoding="utf-8-sig"))
        if not isinstance(blocks,list):raise ValueError("NOTION_CAPTURE_BLOCK_FORMAT_DRIFT")
        body="\n".join(
          y.get("plain_text","")
          for x in blocks for y in x.get(x.get("type",""),{}).get("rich_text",[])
          if isinstance(y,dict))
    return " ".join(body.split())[:max_chars] or None

def lookup_web_capture_sources(keyword,limit=20):
    """One logical result per user-reviewed reference source, not per crawl.

    Reads the existing WORKBENCH index. Never promotes RAW, CURRENT, FORMING,
    or LEARNING, and never opens websites or duplicates file bytes.
    """
    if not isinstance(keyword,str) or not keyword.strip() or len(keyword)>120:
        raise ValueError("WEB_CAPTURE_SEARCH_INVALID")
    if not isinstance(limit,int) or not 1<=limit<=100:
        raise ValueError("WEB_CAPTURE_LIMIT_INVALID")
    manifest=WAREHOUSE/"99_CONTROL"/"WEB_CAPTURE_CLASSIFICATION_CURRENT.json"
    if not manifest.is_file():return []
    data=json.loads(manifest.read_text(encoding="utf-8-sig"))
    proof=data.get("logical_group_proof",{})
    if (not data.get("source_groups")
        or len(data["source_groups"])!=proof.get("source_group_count")
        or len(data.get("records",[]))!=data.get("total_capture_dirs")):
        raise ValueError("WEB_CAPTURE_INDEX_NOT_CURRENT")
    needle=keyword.strip().casefold()
    matches=[]
    for src in data["source_groups"]:
        title=str(src.get("notion_title") or "")
        url=str(src.get("normalized_url") or "")
        if needle not in (title+" "+url+" "+src["source_key"]).casefold():
            continue
        preferred=src["preferred_review_snapshot"]
        folder=Path(preferred)
        if not (folder.is_dir() and folder.resolve().is_relative_to(WAREHOUSE.resolve())):
            raise ValueError("WEB_CAPTURE_SOURCE_PATH_UNRESOLVED")
        revision=next((x for x in src["revisions"] if x["snapshot_dir"]==preferred),None)
        if revision is None:raise ValueError("WEB_CAPTURE_PREFERRED_REVISION_NOT_FOUND")
        matches.append({
            "source_id":src["source_key"],"title":title,"source_url":url,
            "category_candidate":src["classification_candidate"],
            "capture_revisions":src["revision_count"],
            "preferred_review_snapshot":preferred,
            "preferred_extract_method":revision.get("review_extract_method","UNINSPECTED"),
            "preferred_extract_chars":revision.get("review_extract_chars",0),
            "original_extract_excerpt":web_capture_verified_excerpt(folder,revision),
            "original_evidence_sha256":revision.get("review_evidence_sha256"),
            "latest_snapshot":src["latest_snapshot"],
            "source_authority":"INDEX_ONLY_NOT_CURRENT_OR_CONTENT_APPROVED",
            "forming_learning_applied":False
        })
    return sorted(matches,key=lambda x:(x["title"].casefold(),x["source_id"]))[:limit]

def lookup_hns_video_raw_status(keyword,limit=20):
    """Expose the existing 626-capture unresolved videos without hiding 404s.

    Provider availability is the recorded Oct 16 verification, not a live
    request; a 404 is never silently interpreted as deleted source material.
    """
    manifest=WAREHOUSE/"99_CONTROL"/"HNS_CAPTURE_626_SCOPE_COVERAGE_20261014.json"
    if not manifest.is_file():return []
    x=json.loads(manifest.read_text(encoding="utf-8-sig"))
    proof=x.get("live_reconciliation_20261016",{})
    details=x.get("remaining_details",[])
    if (len(details)!=22 or proof.get("hns_present_ids")!=6
        or proof.get("hns_404_ids")!=16 or proof.get("other_account_404_crosschecked")!=16):
        raise ValueError("VIDEO_SOURCE_AVAILABILITY_NOT_ATTESTED")
    query=keyword.strip().casefold()
    matches=[]
    for row in details:
        title=row.get("title","")
        id=row.get("id","")
        if query not in (title+" "+id).casefold():continue
        verified=bool(row.get("live_20261016_raw_provenance"))
        variant=row.get("chatgpt_library_variant")
        if variant and verified:raise ValueError("LIBRARY_VARIANT_INVALID_SOURCE_SCOPE")
        if variant and (variant.get("original_drive_hash_attested") is not False
              or variant.get("container_sha256_verified") is not True
              or len(variant.get("content_sha256",""))!=64):
            raise ValueError("CHATGPT_LIBRARY_VARIANT_PROVENANCE_DRIFT")
        matches.append({
            "source_id":id,"title":title,"mime_type":row.get("mime"),
            "provider_availability":row["live_20261016_status"],
            "prior_raw_sha256_attested":verified,
            "source_state":"RAW_VERIFIED_IN_EARLIER_CENTRAL_DB" if verified
                           else "RAW_UNRESOLVED_FILE_ID_404_BOTH_LINKED_ACCOUNTS",
            "provider_check_date":"2026-10-16",
            "chatgpt_library_review_copy":{
               "library_file_id":variant["file_id"],
               "copy_sha256":variant["content_sha256"],
               "copy_bytes":variant["size_bytes"],
               "codec":variant["codec_verified"],
               "original_equivalence":"NOT_ESTABLISHED",
               "windows_workbench_binary_ingested":False
            } if variant else None,
            "cannot_infer_deletion_from_404":True,
            "forming_learning_applied":False})
    return matches[:limit]

def cli():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,default=DB)
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("init")
    g=sub.add_parser("ingest-drive");g.add_argument("--file",type=Path,default=DRIVE)
    g=sub.add_parser("ingest-reference");g.add_argument("--file",type=Path,default=REFERENCE)
    g=sub.add_parser("discover-archive");g.add_argument("--path",type=Path,default=ARCHIVE);g.add_argument("--limit",type=int,default=12000)
    g=sub.add_parser("run");g.add_argument("--items",type=int,default=40);g.add_argument("--max-bytes",type=int,default=20_000_000)
    sub.add_parser("report")
    sub.add_parser("rehome-source-archive")
    g=sub.add_parser("lookup");g.add_argument("keyword");g.add_argument("--limit",type=int,default=20)
    g=sub.add_parser("search-evidence");g.add_argument("keyword");g.add_argument("--limit",type=int,default=20)
    a=p.parse_args()
    with connect(a.db) as c:
        if a.cmd=="init":data={"status":"INITIALIZED","single_db":str(a.db)}
        elif a.cmd=="ingest-drive":data=ingest_drive(c,json.loads(a.file.read_text(encoding="utf-8-sig")))
        elif a.cmd=="ingest-reference":data=ingest_references(c,json.loads(a.file.read_text(encoding="utf-8-sig")))
        elif a.cmd=="discover-archive":data=discover_archive(c,a.path,a.limit)
        elif a.cmd=="run":data=run_bounded(c,a.items,a.max_bytes)
        elif a.cmd=="report":data=report(c)
        elif a.cmd=="rehome-source-archive":data=rehome_local_source_archive()
        elif a.cmd=="lookup":
            rows=c.execute("""SELECT s.id,s.status,s.domain_hint,l.name,l.account,l.provider,
              l.locator FROM source s JOIN location l ON l.source_id=s.id
              WHERE l.name LIKE ? ORDER BY s.status,l.name LIMIT ?""",
              ("%"+a.keyword.replace("%","\\%")+"%",min(max(a.limit,1),100))).fetchall()
            data={"matches":[dict(x) for x in rows],
                  "web_capture_sources":lookup_web_capture_sources(a.keyword,min(max(a.limit,1),100)),
                  "hns_video_originals":lookup_hns_video_raw_status(a.keyword,min(max(a.limit,1),100)),
                  "web_capture_identity":"ONE_NOTION_PAGE_ID_PER_LOGICAL_SOURCE_ACROSS_REVISIONS",
                  "web_capture_approval":"INDEX_ONLY_NOT_CURRENT_OR_FORMING_APPROVED"}
        elif a.cmd=="search-evidence":
            term=a.keyword.strip().casefold()
            if not term or len(term)>120:raise ValueError("EVIDENCE_QUERY_INVALID")
            term=term.replace("~","~~").replace("%","~%").replace("_","~_")
            rows=c.execute("""SELECT e.source_id,e.parse_state,e.summary,
                 s.authoritative_review,
                 (SELECT l.name FROM location l WHERE l.source_id=e.source_id
                  AND l.provider='GOOGLE_DRIVE' AND l.account='HNS' LIMIT 1) AS title
              FROM evidence e JOIN source s ON s.id=e.source_id
              WHERE LOWER(e.index_terms) LIKE ? ESCAPE '~'
              ORDER BY CASE e.parse_state
                  WHEN 'VISUAL_CONTENT_EXTRACTED_UNREVIEWED' THEN 0 ELSE 1 END,
                  e.source_id LIMIT ?""",
              ("%"+term+"%",min(max(a.limit,1),100))).fetchall()
            data={"query":a.keyword,"matches":[dict(x) for x in rows],
                  "authority":"DERIVED_EVIDENCE_NOT_CURRENT_OR_APPROVED",
                  "forming_learning_applied":False}
        else:raise ValueError("UNKNOWN_FACTORY_ACTION")
        if a.cmd not in ("report","lookup","search-evidence"):
            runid=c.execute("INSERT INTO run(started_at,operation,result_json) VALUES(?,?,?)",
                (utc(),a.cmd,compact(data))).lastrowid
            data["run_id"]=runid
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=="__main__":
    cli()
