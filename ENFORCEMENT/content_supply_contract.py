"""TAKY content supply contract P0. Deterministic gap classification; no I/O or authority promotion."""
REQUIRED = ("demand_id", "consumer", "requirements")
STAGES = ("DISCOVERY", "GATHERING", "MINING", "INDEXING", "FORMING", "PRODUCTION", "INTEGRATION", "VALIDATION", "FEEDBACK")
ROUTES = {
    "SOURCE_ABSENT": "DISCOVERY",
    "RAW_INCOMPLETE": "GATHERING",
    "EXTRACTION_FAILED": "MINING",
    "INDEX_MISSING": "INDEXING",
    "KNOWLEDGE_NOT_FORMED": "FORMING",
    "PRODUCT_MISSING": "PRODUCTION",
    "CONSUMER_NOT_BOUND": "INTEGRATION",
    "QUALITY_FAILED": "VALIDATION",
}
def audit(contract):
    if (not isinstance(contract, dict)
        or any(not isinstance(contract.get(x), str) or not contract[x].strip() for x in ('demand_id','consumer'))
        or 'requirements' not in contract):
        return {"status": "HOLD", "reason": "CONTRACT_INCOMPLETE", "coverage": None, "actions": []}
    items = contract["requirements"]
    if (not isinstance(items, list) or not items
        or any(not isinstance(x, dict) or not isinstance(x.get('id'), str)
               or not x['id'].strip() or (x.get('query') is not None and not isinstance(x['query'], str))
               for x in items)):
        return {"status": "HOLD", "reason": "REQUIREMENTS_INVALID", "coverage": None, "actions": []}
    identifiers = [str(x["id"]) for x in items]
    if len(set(identifiers)) != len(identifiers):
        return {"status": "HOLD", "reason": "DUPLICATE_REQUIREMENT", "coverage": None, "actions": []}
    actions = []
    declaration_count = 0
    for item in items:
        status = item.get("status")
        proof = item.get("consumer_evidence")
        if status == "CONSUMED_VERIFIED" and isinstance(proof, dict) and proof.get("artifact_ref") and proof.get("test_ref") and proof.get("revision"):
            declaration_count += 1
            continue
        cause = item.get("gap_cause")
        route = ROUTES.get(cause)
        if route is None:
            route = "VALIDATION" if status == "CONSUMED_VERIFIED" else "COVERAGE_DIAGNOSIS"
        actions.append({"requirement_id": item["id"], "cause": cause or "UNDIAGNOSED", "route": route,
                        "recovery_status": "NEEDS_EVIDENCE" if route == "VALIDATION" else "PENDING"})
    declared_coverage = declaration_count / len(items)
    return {"status": "CANDIDATE" if not actions else "HOLD", "coverage": None,
            "declared_coverage": declared_coverage, "verified": 0,
            "declared_verified": declaration_count, "required": len(items), "actions": actions,
            "release_approved": False, "evidence_scope": "DECLARATION_ONLY",
            "invariant": "SOURCE_COUNT_NEVER_IMPLIES_CONTENT_SUFFICIENCY"}
