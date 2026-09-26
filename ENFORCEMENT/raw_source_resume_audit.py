#!/usr/bin/env python3
"""Evidence-bound scope audit: raw files -> independent scope manifest -> inventory -> handoff.

The manifest is an explicit scope declaration, NOT proof that inaccessible chats/files
were recovered. Each included source must have a full-file SHA and each material item
an exact unique quote. Fail closed on drift, missing inventory/handoff items, fake
pointers and correction targets. Never infer that unlisted source items do not exist.
"""
import argparse
import hashlib
import json
from pathlib import Path
from source_inventory_omission_gate import check as reconcile

def sha(data):
    return hashlib.sha256(data).hexdigest()

def audit(root, manifest_path, inventory_path, handoff_path):
    errors=[]
    root=root.resolve()
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    inventory=json.loads(inventory_path.read_text(encoding="utf-8"))
    handoff=json.loads(handoff_path.read_text(encoding="utf-8"))
    files=manifest.get("raw_sources")
    items=manifest.get("material_items")
    if not manifest.get("scope_id") or not manifest.get("scope_boundary"):
        errors.append("scope_id/scope_boundary missing")
    if manifest.get("unavailable_sources"):
        errors.append("UNAVAILABLE_SOURCES: full recovered-scope PASS forbidden")
    if not isinstance(files,list) or not files:
        errors.append("raw_sources must be nonempty")
        files=[]
    if not isinstance(items,list) or not items:
        errors.append("material_items must be nonempty")
        items=[]
    raw={}
    for f in files:
        sid=f.get("source_id")
        rel=f.get("path")
        if not sid or not rel or sid in raw:
            errors.append(f"invalid/duplicate raw source: {sid}")
            continue
        path=(root/rel).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            errors.append(f"missing/escaping raw source: {sid}")
            continue
        data=path.read_bytes()
        if sha(data)!=f.get("sha256"):
            errors.append(f"RAW_SOURCE_DRIFT: {sid}")
        try:
            raw[sid]=data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-UTF8 raw source: {sid}")
    # Strict raw-line accounting: every nonblank line in every declared raw file
    # must be represented by a material quote or explicitly excluded with a reason.
    # This prevents a preparer from simply leaving an inconvenient source line
    # out of both the inventory and the handoff.
    exclusions=manifest.get("excluded_lines")
    if not isinstance(exclusions,list):
        errors.append("excluded_lines must be an explicit list (empty allowed)")
        exclusions=[]
    excluded={}
    for entry in exclusions:
        sid=entry.get("raw_source_id")
        line=entry.get("line")
        if not isinstance(line,int) or line<1 or not entry.get("reason"):
            errors.append(f"INVALID_EXCLUSION: {sid}:{line}")
        elif (sid,line) in excluded:
            errors.append(f"DUPLICATE_EXCLUSION: {sid}:{line}")
        else:
            excluded[(sid,line)]=entry
    seen=set()
    expected={}
    for item in items:
        key=item.get("source_id")
        if not key or key in seen:
            errors.append(f"invalid/duplicate material item: {key}")
            continue
        seen.add(key)
        sid=item.get("raw_source_id")
        quote=item.get("exact_quote")
        if not quote or not isinstance(quote,str):
            errors.append(f"QUOTE_MISSING: {key}")
            continue
        if sid not in raw or raw[sid].count(quote)!=1:
            errors.append(f"RAW_QUOTE_NOT_UNIQUE_OR_MISSING: {key}")
        if item.get("content_sha256")!=sha(quote.encode("utf-8")):
            errors.append(f"QUOTE_HASH_MISMATCH: {key}")
        if not item.get("classification"):
            errors.append(f"CLASSIFICATION_MISSING: {key}")
        if item.get("type")=="CORRECTION" and not item.get("correction_targets"):
            errors.append(f"CORRECTION_TARGET_MISSING: {key}")
        expected[key]=item
    covered=set()
    for key,item in expected.items():
        sid=item.get("raw_source_id")
        quote=item.get("exact_quote","")
        if sid in raw and quote and raw[sid].count(quote)==1:
            start=raw[sid].index(quote)
            end=start+len(quote)
            first=raw[sid][:start].count("\n")+1
            last=raw[sid][:end-1].count("\n")+1
            covered.update((sid,n) for n in range(first,last+1))
    for sid,content in raw.items():
        for line_no,line in enumerate(content.splitlines(),1):
            if not line.strip():
                continue
            key=(sid,line_no)
            if key not in covered and key not in excluded:
                errors.append(f"UNACCOUNTED_RAW_LINE: {sid}:{line_no}")
            if key in covered and key in excluded:
                errors.append(f"EXCLUDED_BUT_MATERIAL: {sid}:{line_no}")
    for sid,line in excluded:
        if sid not in raw or line>len(raw[sid].splitlines()) or not raw[sid].splitlines()[line-1].strip():
            errors.append(f"INVALID_EXCLUDED_LINE_REFERENCE: {sid}:{line}")
    for key,item in expected.items():
        for target in item.get("correction_targets",[]):
            if target not in expected:
                errors.append(f"CORRECTION_TARGET_UNRESOLVED: {key} -> {target}")
    inv={x.get("source_id"):x for x in inventory.get("source_items",[]) if isinstance(x,dict)}
    cov={x.get("source_id"):x for x in handoff.get("coverage_items",[]) if isinstance(x,dict)}
    for key,item in expected.items():
        if key not in inv:
            errors.append(f"RAW_MANIFEST_ITEM_OMITTED_FROM_INVENTORY: {key}")
            continue
        x=inv[key]
        if x.get("content_sha256")!=item.get("content_sha256") or x.get("classification")!=item.get("classification"):
            errors.append(f"RAW_INVENTORY_DRIFT: {key}")
        if x.get("source_pointer")!=f"raw:{item.get('raw_source_id')}#{key}":
            errors.append(f"RAW_POINTER_MISMATCH: {key}")
        if item.get("type")=="CORRECTION" and cov.get(key,{}).get("correction_linkage")!=item.get("correction_targets"):
            errors.append(f"CORRECTION_LINEAGE_DRIFT: {key}")
    for key in inv.keys()-expected.keys():
        errors.append(f"INVENTORY_ITEM_NOT_IN_RAW_MANIFEST: {key}")
    if inventory.get("raw_manifest_sha256")!=sha(manifest_path.read_bytes()):
        errors.append("raw_manifest_sha256 mismatch")
    errors.extend(reconcile(inventory_path,handoff_path))
    return errors

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source_root",type=Path)
    p.add_argument("raw_manifest",type=Path)
    p.add_argument("inventory",type=Path)
    p.add_argument("handoff_coverage",type=Path)
    a=p.parse_args()
    errors=audit(a.source_root,a.raw_manifest,a.inventory,a.handoff_coverage)
    print(json.dumps({"pass":not errors,"errors":errors,
        "claim_boundary":"DECLARED_RECOVERED_SCOPE_ONLY; unlisted/inaccessible history and hosted auto-invocation NOT proven"},ensure_ascii=False,indent=2))
    return int(bool(errors))
if __name__=="__main__":
    raise SystemExit(main())
