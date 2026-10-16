"""Build an immutable, non-authoritative review queue from Central SHA-bound DETAIL.

This is a preparation step between technical INDEX and owner-controlled FORMING.
It cannot mark REVIEW done or create FORMING, LEARNING, CURRENT, or approvals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from collections import Counter
from pathlib import Path

import central_pdf_page_batch as pdf
import central_html_capture_triage as html_capture
import taky_central_source_factory as factory

EVIDENCE = Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\80_EVIDENCE")
QUEUE_SCHEMA = "TAKY_CENTRAL_FORMING_REVIEW_QUEUE_V1"
INDEX_STATES = ("TECHNICAL_INDEX_READY", "TECHNICAL_PDF_INDEX_READY", "TECHNICAL_HTML_INDEX_READY")
ROUTING = {
    "ARCHITECTURE": "ARCHI_GROW_OWNER_REVIEW",
    "LEARNING": "LEARNING_DOMAIN_OWNER_REVIEW",
    "AI_REFERENCE": "SYSTEM_GROW_TECHNICAL_OWNER_REVIEW",
    "DESIGN_ASSET": "DESIGN_ASSET_OWNER_REVIEW",
    "VOICE_MEDIA": "MEDIA_OWNER_REVIEW",
    "UNCLASSIFIED": "OWNER_ROUTING_REQUIRED",
}


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj):
    return hashlib.sha256(compact(obj).encode("utf-8")).hexdigest()


def indexed_source_rows(c):
    rows = c.execute("""SELECT s.id AS source_id,s.original_sha256,s.domain_hint,
          s.media_kind,s.status,s.authoritative_review,st.state AS index_state
          FROM source s JOIN stage st ON st.source_id=s.id
          WHERE st.stage='INDEX'
            AND st.state IN ('TECHNICAL_INDEX_READY','TECHNICAL_PDF_INDEX_READY','TECHNICAL_HTML_INDEX_READY')
          ORDER BY s.id""").fetchall()
    return [dict(x) for x in rows]


def _semantic_signal(text):
    """Rank substantive paragraphs above badges, markup and link directories."""
    lines=text.splitlines()
    useful=[]
    for raw in lines:
        line=raw.strip()
        if (not line or line.startswith(("<","![","|","[![","```"))):
            continue
        if line.startswith(("## ","# ","---","- [")):
            continue
        plain=re.sub(r"\[[^]]+\]\([^)]+\)", "", line)
        plain=re.sub(r"https?://\S+|[*_`#]", "", plain).strip()
        if len(plain)>=32:
            useful.append(plain)
    prose=" ".join(useful)
    words=len(prose.split())
    heading=next((line.strip().lower() for line in lines if line.strip().startswith("#")), "")
    directory_penalty=700 if any(word in heading for word in ("documentation","community","star history","license")) else 0
    return min(len(prose),1000)+min(words,80)*2+len(useful)*25-directory_penalty


def _line_anchor(c, sid):
    # The first two units of a README are often only HTML, badges and links.
    # Bound cost, verify RAW hashes via the existing factory, prefer meaningful
    # paragraphs, then return selected anchors in original document order.
    rows=c.execute("""SELECT unit_id FROM evidence_unit
          WHERE source_id=? AND review_state='EXTRACTIVE_UNREVIEWED'
          ORDER BY line_start LIMIT 12""",(sid,)).fetchall()
    if not rows:return None
    verified=[]
    for row in rows:
        item=factory.read_verified_evidence_unit(c,sid,row["unit_id"])
        if (item is None or item["source_authority"]!="UNREVIEWED"
            or item["review_state"]!="EXTRACTIVE_UNREVIEWED"):
            raise ValueError("REVIEW_QUEUE_TEXT_RAW_NOT_VERIFIED")
        verified.append(item)
    ranked=sorted(verified,key=lambda item:(
        -_semantic_signal(item["content"]),item["line_start"]))
    selected=sorted(ranked[:min(4,len(ranked))],key=lambda item:item["line_start"])
    return [{
       "kind":"TEXT_LINE","ref":item["unit_id"],
       "line_start":item["line_start"],"line_end":item["line_end"],
       "content_sha256":item["content_sha256"],"raw_sha256":item["raw_sha256"],
       "excerpt":item["content"][:460],"review_state":item["review_state"]
    } for item in selected]


def _pdf_anchor(c, sid):
    # Page 1-2 may be a cover and a table of contents. Prefer grounded content
    # within a bounded, already indexed sample; no new PDF rendering or OCR.
    rows=c.execute("""SELECT page_number FROM pdf_page_evidence
           WHERE source_id=? AND review_state='EXTRACTIVE_UNREVIEWED'
           ORDER BY page_number LIMIT 8""",(sid,)).fetchall()
    if not rows:return None
    verified=[]
    for row in rows:
        page=pdf.read_verified_page(c,sid,row["page_number"])
        if page is None or page["review_state"]!="EXTRACTIVE_UNREVIEWED":
            raise ValueError("REVIEW_QUEUE_PDF_RAW_NOT_VERIFIED")
        verified.append(page)
    selected=sorted(sorted(verified,key=lambda a:(
        -_semantic_signal(a["text"]),a["page_number"]))[:min(4,len(verified))],
        key=lambda a:a["page_number"])
    return [{
       "kind":"PDF_PAGE","ref":str(a["page_number"]),
       "page_number":a["page_number"],
       "content_sha256":a["text_sha256"],"raw_sha256":a["raw_sha256"],
       "excerpt":a["text"][:460],"review_state":a["review_state"]
    } for a in selected]


def _html_anchor(c, sid):
    # Bounded semantic selection avoids passing only a header/nav block to
    # FORMING while still reading exclusively verified indexed HTML chunks.
    rows=c.execute("""SELECT chunk_no FROM html_text_evidence
        WHERE source_id=? AND review_state='EXTRACTIVE_UNREVIEWED'
        ORDER BY chunk_no LIMIT 8""",(sid,)).fetchall()
    if not rows:return None
    verified=[]
    for row in rows:
        a=html_capture.read_verified(c,sid,row["chunk_no"])
        if a is None or a["review_state"]!="EXTRACTIVE_UNREVIEWED":
            raise ValueError("REVIEW_QUEUE_HTML_RAW_NOT_VERIFIED")
        verified.append(a)
    selected=sorted(sorted(verified,key=lambda a:(
        -_semantic_signal(a["text"]),a["chunk_no"]))[:min(4,len(verified))],
        key=lambda a:a["chunk_no"])
    return [{
       "kind":"HTML_SEGMENT","ref":str(a["chunk_no"]),
       "chunk_no":a["chunk_no"],"content_sha256":a["content_sha256"],
       "raw_sha256":a["raw_sha256"],"excerpt":a["text"][:460],
       "review_state":a["review_state"]
    } for a in selected]


def _hold_reason(c, row):
    sid=row["source_id"]
    loc=c.execute("""SELECT l.name,l.size_bytes,l.source_role
        FROM location l WHERE l.source_id=? AND l.provider='LOCAL_FILE'
        ORDER BY l.account,l.locator LIMIT 1""",(sid,)).fetchone()
    name=(loc["name"] or "").lower() if loc else ""
    role=loc["source_role"] if loc else ""
    if loc and loc["size_bytes"]==0:
        return "EMPTY_RAW_NO_EXTRACTABLE_BYTES"
    if row["media_kind"]=="IMAGE":
        return "VISUAL_SOURCE_REQUIRES_SPECIALIST_GROUNDING"
    if name in ("run-summary.json","quality-report.json"):
        return "RUNTIME_METADATA_NOT_SEMANTIC_SOURCE"
    if role=="REFERENCE_DERIVED_EXAMPLE" or "sample" in name:
        return "DERIVED_SAMPLE_NOT_PRIMARY_SOURCE"
    if name.startswith("readme") or name.endswith("_archive.md"):
        return "ARCHIVE_ADMINISTRATIVE_REFERENCE"
    return "MISSING_EXTRACTIVE_DETAIL_REQUIRES_REVALIDATION"


ARTICLE_CITATION = re.compile(r"제\s*\d{1,4}\s*조(?:의\s*\d{1,3})?")
EFFECTIVE_DATE_CITATION = re.compile(
    r"(?:시행|개정)\s*[\\[(: ]*\s*\d{4}\s*[.\-/]\s*\d{1,2}\s*[.\-/]\s*\d{1,2}"
)


def _lexical_architecture_markers(anchors):
    """Only cite verbatim tokens; do not interpret law or applicability."""
    found=[]
    for anchor in anchors:
        for pattern,kind in ((ARTICLE_CITATION,"ARTICLE_TOKEN"),
                             (EFFECTIVE_DATE_CITATION,"DATE_TOKEN")):
            for match in pattern.finditer(anchor["excerpt"]):
                found.append({
                    "kind":kind,"text_as_printed":match.group(0),
                    "anchor_kind":anchor["kind"],"anchor_ref":anchor["ref"],
                    "text_offset_in_excerpt":match.start(),
                    "content_sha256":anchor["content_sha256"],
                    "evidence_state":"LEXICAL_UNREVIEWED",
                    "legal_effectiveness_verified":False})
                if len(found)>=12:
                    return found
    return found


def _domain_hint_conflict(hint, anchors):
    """Conservative lexical mismatch flag; never supplies a new domain owner.

    Suspends a suspect route when an architecture-hinted source is explicitly
    an elementary learning-video catalogue and no architectural subject term
    occurs in any SHA-verified excerpt. It does not reclassify RAW or INDEX.
    """
    if hint!="ARCHITECTURE":return None
    body=" ".join(a.get("excerpt","") for a in anchors).lower()
    education=("수학" in body and
               ("유튜브" in body or "youtube" in body) and
               ("초등" in body or "교육 콘텐츠" in body))
    architecture=any(term in body for term in (
        "건축", "소방", "도시계획", "정비사업", "교통영향", "피난",
        "건축심의", "설계도면", "building code", "architecture review"))
    if not education or architecture:return None
    matched=[a for a in anchors if "수학" in a.get("excerpt","")]
    return {"reason":"DOMAIN_HINT_CONTENT_CONFLICT_REVIEW_REQUIRED",
            "source_index_domain_hint":hint,
            "conflicting_excerpt_anchor_refs":[a["ref"] for a in matched],
            "inferred_domain_approved":False,
            "owner_route_assignment_allowed":False}


def build_queue(c,source_ids=None):
    sources=indexed_source_rows(c)
    if source_ids:
        allowed=set(source_ids)
        if len(allowed)>64 or len(allowed)!=len(source_ids) or any(not re.fullmatch(r"raw:[0-9a-f]{64}",x) for x in allowed):
            raise ValueError("FORMING_SCOPE_SOURCE_IDS_INVALID")
        sources=[row for row in sources if row["source_id"] in allowed]
        if len(sources)!=len(allowed):
            raise ValueError("FORMING_SCOPE_SOURCE_NOT_INDEXED")
    packets=[]
    holds=[]
    for row in sources:
        sid=row["source_id"]
        if (not row["original_sha256"] or sid!="raw:"+row["original_sha256"]
            or row["authoritative_review"]!="UNREVIEWED"):
            holds.append({"source_id":sid,"reason":"UNVERIFIED_OR_AUTHORITY_CHANGED"})
            continue
        # INDEX stage alone is insufficient. Verify full RAW and selected excerpt.
        if row["index_state"]=="TECHNICAL_PDF_INDEX_READY":
            anchors=_pdf_anchor(c,sid)
        elif row["index_state"]=="TECHNICAL_HTML_INDEX_READY":
            anchors=_html_anchor(c,sid)
        else:
            anchors=_line_anchor(c,sid)
        if not anchors:
            holds.append({"source_id":sid,"reason":_hold_reason(c,row),
                          "media_kind":row["media_kind"]})
            continue
        if any(a["raw_sha256"]!=row["original_sha256"] for a in anchors):
            raise ValueError("INDEX_SOURCE_RAW_MISMATCH")
        hint=row["domain_hint"] or "UNCLASSIFIED"
        route_conflict=_domain_hint_conflict(hint,anchors)
        packet={
          "source_id":sid,
          "raw_sha256":row["original_sha256"],
          "technical_index_state":row["index_state"],
          "media_kind":row["media_kind"],
          "domain_hint":hint,
          "owner_review_route_hint":(
              "OWNER_ROUTING_REQUIRED" if route_conflict else
              ROUTING.get(hint,"OWNER_ROUTING_REQUIRED")),
          **({"domain_hint_conflict":route_conflict} if route_conflict else {}),
          "route_is_authority":False,
          "assigned_owner_namespace":None,
          "reviewed_claims":[],
          "verified_extracts":anchors,
          "evidence_validation":"RAW_AND_ANCHOR_HASH_VERIFIED",
          "review_status":"OWNER_SEMANTIC_REVIEW_REQUIRED",
          "forming_status":"HOLD_PENDING_INDEPENDENT_OWNER_REVIEW",
          "consumer_contract_status":"BLOCKED_UNAPPROVED",
          "known_gaps":["NO_INDEPENDENT_SEMANTIC_REVIEW",
                       "NO_APPROVED_OWNER_RECORD",
                       "NO_CONSUMER_CONTRACT"],
        }
        if route_conflict:
            packet["known_gaps"].append("INDEX_DOMAIN_HINT_CONTENT_CONFLICT_OWNER_RECHECK")
        if hint=="ARCHITECTURE":
            packet["known_gaps"].extend(
                ["LEGAL_EFFECTIVE_DATE_NOT_VERIFIED","PROJECT_APPLICABILITY_NOT_VERIFIED"])
            packet["verbatim_legal_reference_markers"]=_lexical_architecture_markers(anchors)
        packet["packet_revision"]=digest(packet)
        packets.append(packet)
    result={
      "schema":QUEUE_SCHEMA,
      "status":"OWNER_REVIEW_INPUTS_PREPARED_NO_APPROVAL",
      "authority":"NON_AUTHORITATIVE_DERIVED_QUEUE",
      "canonical_source_db_read_only":True,
      "source_count":len(sources),
      "review_packet_count":len(packets),
      "missing_extract_hold_count":len(holds),
      "hold_reason_counts":dict(Counter(h["reason"] for h in holds)),
      "domain_counts":dict(Counter(p["domain_hint"] for p in packets)),
      "verbatim_legal_reference_marker_count":sum(
          len(p.get("verbatim_legal_reference_markers",[])) for p in packets),
      "review_packets":packets,"holds":holds,
      "forming_approved":False,"learning_consumed":False,
      "source_and_current_changed":False,
      "no_paid_api":True,
    }
    if source_ids:
        result["scoped_source_ids"]=sorted(set(source_ids))
    result["manifest_sha256"]=digest({k:v for k,v in result.items()
                                    if k!="manifest_sha256"})
    return result


def verify_queue(c, result):
    if result.get("schema")!=QUEUE_SCHEMA:
        raise ValueError("FORMING_QUEUE_SCHEMA_INVALID")
    own=dict(result)
    fingerprint=own.pop("manifest_sha256",None)
    if fingerprint!=digest(own):
        raise ValueError("FORMING_QUEUE_MANIFEST_TAMPERED")
    if (result.get("forming_approved") is not False
        or result.get("authority")!="NON_AUTHORITATIVE_DERIVED_QUEUE"):
        raise ValueError("FORMING_QUEUE_AUTHORITY_INVALID")
    rebuilt=build_queue(c,result.get("scoped_source_ids") or None)
    if rebuilt["manifest_sha256"]!=result["manifest_sha256"]:
        raise ValueError("FORMING_QUEUE_SOURCE_OR_INDEX_REVISION_CHANGED")
    return {"status":"FORMING_QUEUE_VERIFIED_NO_APPROVAL",
            "review_packets":result["review_packet_count"],
            "missing_extract_holds":result["missing_extract_hold_count"],
            "manifest_sha256":fingerprint}


def write_immutable(result, directory=EVIDENCE):
    root=Path(directory)
    root.mkdir(parents=True,exist_ok=True)
    dest=root/("TAKY_FORMING_REVIEW_QUEUE_"+result["manifest_sha256"][:20]+".json")
    body=json.dumps(result,ensure_ascii=False,indent=2)
    if dest.exists():
        existing=json.loads(dest.read_text(encoding="utf-8"))
        if existing!=result:
            raise ValueError("FORMING_QUEUE_IMMUTABLE_REVISION_CONFLICT")
        return dest,False
    try:
        with dest.open("x",encoding="utf-8") as out:
            out.write(body)
    except FileExistsError:
        existing=json.loads(dest.read_text(encoding="utf-8"))
        if existing!=result:
            raise ValueError("FORMING_QUEUE_IMMUTABLE_REVISION_CONFLICT")
        return dest,False
    return dest,True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--export",action="store_true")
    parser.add_argument("--source-id",action="append",dest="source_ids",default=[])
    parser.add_argument("--verify-file",type=Path)
    parser.add_argument("--check-forming-contract",action="store_true")
    args=parser.parse_args()
    if args.verify_file is not None and args.check_forming_contract:
        parser.error("VERIFY_FILE_AND_FORMING_GATE_MUTUALLY_EXCLUSIVE")
    with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=12) as db:
        db.row_factory=sqlite3.Row
        if args.verify_file is not None:
            item=json.loads(args.verify_file.read_text(encoding="utf-8"))
            output=verify_queue(db,item)
        else:
            item=build_queue(db,args.source_ids)
            output={"status":item["status"],
              "review_packets":item["review_packet_count"],
              "missing_extract_holds":item["missing_extract_hold_count"],
              "hold_reasons":item["hold_reason_counts"],
              "domain_counts":item["domain_counts"],
              "legal_reference_marker_count":item["verbatim_legal_reference_marker_count"],
              "manifest_sha256":item["manifest_sha256"],
              "operational_db_read_only":True}
            if args.export or args.check_forming_contract:
                dest,created=write_immutable(item)
                output["saved_path"]=str(dest)
                output["new_immutable_receipt"]=created
            if args.check_forming_contract:
                # Read-only Python SHA validation -> existing Node owner/FORMING gates.
                runner=Path(__file__).with_name("central_forming_owner_gate.cjs")
                checked=subprocess.run(
                    ["node",str(runner),str(dest)],
                    capture_output=True,text=True,encoding="utf-8",
                    timeout=120,check=False)
                if checked.returncode:
                    raise ValueError("FORMING_GATE_FAILED:"+checked.stderr[-400:])
                gate=json.loads(checked.stdout)
                if (gate["source_queue_sha256"]!=item["manifest_sha256"]
                    or gate["index_owner_review_required_count"]!=item["review_packet_count"]
                    or gate["reviewed_owner_draft_count"]!=0
                    or gate["semantic_approvals"]!=0
                    or gate["knowledge_promotions"]!=0):
                    raise ValueError("FORMING_GATE_UNAUTHORIZED_OR_INCOMPLETE")
                output["forming_owner_gate"]={
                    "status":gate["status"],
                    "index_owner_review_required_count":gate["index_owner_review_required_count"],
                    "drafts_generated":gate["reviewed_owner_draft_count"],
                    "independent_approvals":gate["semantic_approvals"],
                    "knowledge_promotions":gate["knowledge_promotions"]}
    print(json.dumps(output,ensure_ascii=True))


if __name__=="__main__":
    main()
