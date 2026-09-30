#!/usr/bin/env python3
"""Conservative candidate discovery for publisher HTML with DEXT5 inline uploads.

Some official publishers expose original source paths only inside inert page
initializer calls, not regular <a href>. This parser NEVER evaluates script,
fetches the URL, decides publisher authenticity, or promotes source evidence.
It turns exact caller-named targets into bounded candidates for the authorized
original-byte acquisition adapter and Index identity owner.
"""
from __future__ import annotations
import html
import re
from urllib.parse import urljoin,urlparse,unquote

RECORD=re.compile(
    r"DEXT5UPLOAD\.AddUploadedFile\(\s*'(?P<post>\d+)'\s*,\s*"
    r"'(?P<name>[^']+)'\s*,\s*'(?P<path>[^']+)'\s*,\s*"
    r"'(?P<size>\d+)'\s*,\s*'(?P<file>\d+)'",re.S
)
MAX_HTML_CHARS=2_000_000
MAX_SOURCE_BYTES=120_000_000


def discover_exact_inline_attachments(raw_html:str, publisher_page_url:str,
                                      exact_filenames:list[str], *, post_id:str)->dict:
    names=[str(x) for x in exact_filenames or [] if str(x)]
    names=list(dict.fromkeys(names))
    page=urlparse(str(publisher_page_url or ""))
    if (page.scheme!="https" or not page.hostname or not str(post_id).isdigit()
        or not isinstance(raw_html,str) or len(raw_html)>MAX_HTML_CHARS
        or len(names)>50):
        return {"state":"HOLD_INVALID_SOURCE_CONTEXT","candidates":[],
                "unresolved_names":names,"rejected":[]}
    records={}; rejected=[]
    for match in RECORD.finditer(raw_html):
        values={key:html.unescape(value) for key,value in match.groupdict().items()}
        name=values["name"]
        if name not in names or values["post"]!=str(post_id):
            continue
        relative=values["path"]
        parsed=urlparse(relative)
        decoded=unquote(relative)
        ext=".hwpx" if name.lower().endswith(".hwpx") else ".pdf" if name.lower().endswith(".pdf") else ""
        if (not ext or not relative.startswith("/upload/")
            or not relative.lower().endswith(ext)
            or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
            or "\\" in decoded or ".." in decoded or "//" in decoded):
            rejected.append({"original_filename":name,"reason":"UNSAFE_OR_MISMATCHED_PUBLISHER_PATH"})
            continue
        size=int(values["size"])
        if not 0<size<=MAX_SOURCE_BYTES:
            rejected.append({"original_filename":name,"reason":"PUBLISHER_SIZE_OUT_OF_BOUND"})
            continue
        absolute=urljoin(publisher_page_url,relative)
        if (urlparse(absolute).scheme!="https"
            or urlparse(absolute).hostname!=page.hostname):
            rejected.append({"original_filename":name,"reason":"CROSS_ORIGIN_SOURCE_REJECTED"})
            continue
        candidate={
            "original_filename":name,"source_url":absolute,
            "publisher_size_bytes":size,"publisher_file_id":values["file"],
            "publisher_post_id":values["post"],
            "publisher_page_url":publisher_page_url,
            "discovery_surface":"INLINE_DEXT5_UPLOAD_METADATA",
            "acquired_original_bytes":False,
            "independently_verified":False,
            "automatic_index_promotion":False,
        }
        previous=records.get(name)
        if previous is not None and (previous["source_url"]!=absolute
                                     or previous["publisher_size_bytes"]!=size):
            records.pop(name,None)
            rejected.append({"original_filename":name,"reason":"CONFLICTING_DUPLICATE_INLINE_ENTRY"})
        elif not any(x["original_filename"]==name and x["reason"]=="CONFLICTING_DUPLICATE_INLINE_ENTRY"
                     for x in rejected):
            records[name]=candidate
    return {
        "schema":"TAKY_INLINE_ATTACHMENT_CANDIDATES_V1",
        "state":"CANDIDATES_REQUIRE_ORIGINAL_FETCH" if records else "NO_EXACT_ATTACHMENT_CANDIDATE",
        "candidates":[records[name] for name in names if name in records],
        "unresolved_names":[name for name in names if name not in records],
        "rejected":rejected,
        "guards":{"no_script_execution":True,"no_network_calls":True,
                  "file_labels_not_acquired_bytes":True,
                  "same_publisher_origin_required":True,
                  "exact_target_name_required":True},
    }
