#!/usr/bin/env python3
"""TAKY shared Index Retrieval Runtime V1.

Implements the non-authoritative SEARCH_PROJECTION defined by
DATA_INDEX_SCHEMA_CONTRACT_V1:
STRUCTURED_FILTER -> LEXICAL_RETRIEVAL -> SEMANTIC_RETRIEVAL ->
RANK_FUSION -> RELATION_EXPANSION -> DETAIL_FETCH.

This module never mutates RAW/INDEX/CURRENT and never decides learning policy.
"""
from __future__ import annotations
import math, re, unicodedata
from collections import defaultdict

EXACT_FIELDS={
    "source_id","canonical_title","content_hash","source_family","source_type",
    "authority_class","origin","current_relation","index_state","review_state"
}
RELATION_TYPES={
    "PART_OF","CONTAINS","FRAGMENT_OF","EXTRACTED_FROM","DERIVED_FROM",
    "VERSION_OF","SUPERSEDES","EXACT_DUPLICATE_OF","NEAR_DUPLICATE_OF",
    "SAME_FAMILY_AS","REFERENCES","RELATED_TO"
}

def _norm(value):
    text=unicodedata.normalize("NFKC",str(value or "")).lower()
    return " ".join(re.findall(r"[A-Za-z0-9가-힣]+",text))

def _tokens(value):
    return [x for x in _norm(value).split() if x]

def _row_id(row):
    return str(row.get("source_id") or row.get("identity",{}).get("source_id") or "")

def _get(row, key):
    if key in row: return row.get(key)
    for section in ("identity","classification","provenance","discovery","state"):
        block=row.get(section)
        if isinstance(block,dict) and key in block: return block.get(key)
    return None

def structured_filter(rows, filters=None):
    filters=filters or {}
    out=[]
    for row in rows:
        ok=True
        for key,wanted in filters.items():
            actual=_get(row,key)
            values=wanted if isinstance(wanted,(list,tuple,set)) else [wanted]
            if key in EXACT_FIELDS:
                if _norm(actual) not in {_norm(v) for v in values}: ok=False; break
            else:
                hay=set(_tokens(actual))
                if not any(set(_tokens(v)).issubset(hay) for v in values): ok=False; break
        if ok: out.append(row)
    return out

def lexical_retrieval(rows, query):
    q=set(_tokens(query))
    if not q: return []
    scored=[]
    for row in rows:
        fields=[
            _get(row,"canonical_title"), _get(row,"short_summary"),
            _get(row,"source_family"), _get(row,"source_type"),
            " ".join(map(str,_get(row,"controlled_terms") or [])) if isinstance(_get(row,"controlled_terms"),list) else _get(row,"controlled_terms"),
            " ".join(map(str,_get(row,"keywords") or [])) if isinstance(_get(row,"keywords"),list) else _get(row,"keywords"),
        ]
        toks=set()
        for f in fields: toks.update(_tokens(f))
        overlap=len(q & toks)
        if overlap:
            score=overlap/max(1,math.sqrt(len(q)*max(1,len(toks))))
            scored.append((_row_id(row),score,row))
    return sorted(scored,key=lambda x:(-x[1],x[0]))

def semantic_retrieval(rows, query, semantic_scores=None):
    """Provider-neutral semantic channel.

    V1 intentionally does not own embeddings. Callers may supply semantic_scores
    keyed by source_id from any derived semantic index. Without scores this
    channel contributes no ranking, preserving exact/lexical correctness.
    """
    semantic_scores=semantic_scores or {}
    scored=[]
    for row in rows:
        sid=_row_id(row)
        if sid in semantic_scores:
            try: score=float(semantic_scores[sid])
            except (TypeError,ValueError): continue
            if score>0: scored.append((sid,score,row))
    return sorted(scored,key=lambda x:(-x[1],x[0]))

def reciprocal_rank_fusion(channels, k=60):
    scores=defaultdict(float); rows={}
    for channel in channels:
        for rank,(sid,_score,row) in enumerate(channel,1):
            if not sid: continue
            scores[sid]+=1.0/(k+rank)
            rows[sid]=row
    return sorted(((sid,score,rows[sid]) for sid,score in scores.items()),key=lambda x:(-x[1],x[0]))

def expand_relations(ranked, relations, index_by_id, max_hops=1, allowed_types=None):
    allowed=set(allowed_types or RELATION_TYPES)
    seeds=[sid for sid,_,_ in ranked]
    seen=set(seeds); frontier=list(seeds); expanded=[]
    adjacency=defaultdict(list)
    for rel in relations or []:
        typ=str(rel.get("type") or "").upper()
        if typ not in allowed: continue
        a=str(rel.get("from") or rel.get("source_id") or "")
        b=str(rel.get("to") or rel.get("target_id") or "")
        if a and b:
            adjacency[a].append((b,typ)); adjacency[b].append((a,typ))
    for hop in range(1,max_hops+1):
        nxt=[]
        for sid in frontier:
            for other,typ in adjacency.get(sid,[]):
                if other in seen or other not in index_by_id: continue
                seen.add(other); nxt.append(other)
                expanded.append({"source_id":other,"via":sid,"relation_type":typ,"hop":hop,"row":index_by_id[other]})
        frontier=nxt
        if not frontier: break
    return expanded

def detail_fetch(source_ids, detail_rows):
    wanted=set(map(str,source_ids))
    return [d for d in (detail_rows or []) if str(d.get("source_id") or "") in wanted]

def retrieve(index_rows, query="", filters=None, semantic_scores=None, relations=None,
             detail_rows=None, top_k=10, relation_hops=1):
    candidates=structured_filter(index_rows or [],filters)
    lexical=lexical_retrieval(candidates,query)
    semantic=semantic_retrieval(candidates,query,semantic_scores)
    # Exact structured-only queries still return deterministic rows.
    if not query.strip():
        fused=[(_row_id(r),1.0,r) for r in sorted(candidates,key=lambda x:_row_id(x))]
    else:
        fused=reciprocal_rank_fusion([lexical,semantic])
    primary=fused[:max(0,int(top_k))]
    index_by_id={_row_id(r):r for r in index_rows or [] if _row_id(r)}
    expanded=expand_relations(primary,relations,index_by_id,max_hops=max(0,int(relation_hops)))
    result_ids=[sid for sid,_,_ in primary]+[x["source_id"] for x in expanded]
    details=detail_fetch(result_ids,detail_rows)
    return {
        "schema":"TAKY_INDEX_RETRIEVAL_RESULT_V1",
        "query":query,
        "filters":filters or {},
        "primary":[{"source_id":sid,"score":round(score,8),"row":row} for sid,score,row in primary],
        "expanded":[{k:v for k,v in x.items() if k!="row"}|{"row":x["row"]} for x in expanded],
        "details":details,
        "counts":{"candidate":len(candidates),"primary":len(primary),"expanded":len(expanded),"details":len(details)},
        "guards":{
            "search_projection_is_not_source_of_truth":True,
            "raw_unchanged":True,
            "index_unchanged":True,
            "current_unchanged":True,
            "domain_policy_not_decided":True,
            "semantic_scores_are_derived_only":True,
        },
    }
