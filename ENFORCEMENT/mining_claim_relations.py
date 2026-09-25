#!/usr/bin/env python3
"""Claim relation evaluator for TAKY Mining Core.

Avoids treating every different wording as a conflict. Adapters may provide
explicit SUPPORTS/CONTRADICTS/QUALIFIES relations; conservative inference is
used only when structured polarity/subject/scope are available.
"""
from __future__ import annotations
import re

def norm(v):
    return " ".join(re.findall(r"[A-Za-z0-9_가-힣]+",str(v or "").lower()))

def claim_key(e):
    return (norm(e.get("subject")),norm(e.get("predicate")),norm(e.get("scope")))

def relation(a,b):
    explicit=str(a.get("relation_to",{}).get(str(b.get("evidence_id")),"")).upper()
    if explicit in {"SUPPORTS","CONTRADICTS","QUALIFIES"}: return explicit
    ka,kb=claim_key(a),claim_key(b)
    if not all(ka[:2]) or ka[:2]!=kb[:2]: return "UNRELATED"
    # Different explicit scopes are not automatically contradictory.
    if ka[2] and kb[2] and ka[2]!=kb[2]: return "QUALIFIES"
    pa=str(a.get("polarity","")).upper(); pb=str(b.get("polarity","")).upper()
    if pa and pb and pa!=pb and {pa,pb}<={"YES","NO","TRUE","FALSE","ALLOW","DENY"}: return "CONTRADICTS"
    va,vb=norm(a.get("value")),norm(b.get("value"))
    if va and vb and va==vb: return "SUPPORTS"
    return "UNRESOLVED"

def analyze(evidence):
    pairs=[]; conflict=False
    for i,a in enumerate(evidence):
        for b in evidence[i+1:]:
            r=relation(a,b); pairs.append({"a":a.get("evidence_id"),"b":b.get("evidence_id"),"relation":r})
            if r=="CONTRADICTS": conflict=True
    return {"conflict":conflict,"pairs":pairs,"unresolved_pairs":sum(1 for x in pairs if x["relation"]=="UNRESOLVED")}
