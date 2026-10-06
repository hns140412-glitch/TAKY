#!/usr/bin/env python3
"""Sentinel check that MASTER/MASTER_LOGIC.md §0.2 preserves the TAKY 2.0 systemwide basis.

Detects accidental meaning loss or drift (sixth gate, vendor-as-role, auto-promotion),
not exact-file immutability.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "MASTER" / "MASTER_LOGIC.md"

REQUIRED = (
    # identity + dual slogan + subordinate control plane
    "`Think Again, Keep Your Key.`",
    "`Think Again, You're The Key.`",
    "`USER = KEY OWNER / FINAL AUTHORITY`",
    "subordinate control/execution model under TAKY",
    # canonical authority boundary; candidates stay candidates
    "TAKY2/TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL_20261006.md",
    "remain CANDIDATE until a verified, USER-authorized promotion",
    "not by storage location or a `CANONICAL` header string",
    "`CANONICAL DESIGN != IMPLEMENTATION PASS`",
    # source-of-truth: GitHub canonical master; designated Drive surfaces are readback, conflicts block
    "GitHub TAKY = CANONICAL MASTER SOURCE.",
    "does not make arbitrary Drive files canonical",
    "record a `CONFLICT` and block material mutation",
    "an unverified readback blocks material mutation",
    # control roles without mandatory spawn; role/owner/tool separation
    "`NAVIGATOR`",
    "`GUARDIAN`",
    "`DRIVER + SAVEY_AI_ECONOMY`",
    "`SCOUT`",
    "SHALL NOT require spawning one agent or AI call per role",
    "`ROLE != AGENT`. `OWNER != ROUTER`. `TOOL != AUTHORITY`.",
    "vendor/model names SHALL NOT define role ontology",
    # exact five gates; necessity inside COST
    "The hard gates are exactly `KEY / CONTEXT / ROUTE / COST / DONE`.",
    "It SHALL NOT become a sixth hard gate.",
    # one shared Driver/COST economy policy; single evaluator stays implementation-OPEN, not claimed enforced
    "consume one shared economy policy (`SAVEY_AI_ECONOMY_POLICY`); two diverging economy policies are a defect.",
    "The single runtime evaluator remains implementation-OPEN (V2 §8); this rule SHALL NOT be reported as mechanically enforced until implemented and verified.",
    "runtime realization of this basis remains OPEN until code + evidence + regression close it (V2 §8).",
    "Conflict precedence (V2 §9)",
    # Driver economy (active V2 §4 order) with MASTER execution protection labeled as such, and acceptance-quality floor
    "Canonical policy order (V2 §4): `NECESSITY -> REUSE / CACHE -> LOCAL / DETERMINISTIC -> EXISTING SUBSCRIPTION / AUTH -> BATCH / CONTEXT REUSE -> LOWEST SUFFICIENT CAPABILITY -> PAID / EXTERNAL ROUTE`.",
    "MASTER execution protection (not V2 verbatim): the paid/external route is taken only if justified + authorized, and is followed by `EXECUTE -> VERIFY -> ACCOUNT FOR RESOURCE COST`.",
    "`CHEAPEST != CHEAPEST_SUFFICIENT`",
    "Cost saving SHALL NOT lower acceptance criteria, authority, safety or evidence quality.",
    "`SAVEY_AI_ECONOMY != SAVEY_FAMILY_FINANCE`",
    # Beta / Alpha / TAKY2
    "`BETA = EVIDENCE / DEFENSE / FROZEN REALITY`",
    "`ALPHA = SEMANTIC OWNER / WHOLE-SYSTEM OWNERSHIP MAP`",
    "`TAKY2 = COMPACT CROSS-CUTTING ENFORCEMENT KERNEL`",
    "owners retain their specialized meaning",
    # semantic owner first
    "SHALL NOT transfer semantic ownership",
    "`OWNER_GAP`, never a guess",
    # CURRENT / HISTORY / HANDOFF / CANONICAL + OPEN-only resume
    "`CURRENT` = live OPEN work only",
    "`HANDOFF` = recovery pointer, not authority",
    "Canonical wins and the conflict is recorded as a CURRENT CONFLICT item",
    "proceed OPEN-only",
    # technical delivery vs USER confirmation, without weakening approval
    "`RULE WRITTEN != RULE ENFORCED != FEATURE IMPLEMENTED != TECHNICALLY VERIFIED != USER INTENT VERIFIED != USER CONFIRMED`",
    "`TECHNICALLY_DELIVERED`",
    "`USER_CONFIRMED`",
    "any two-stage completion policy built on them remains CANDIDATE until promoted.",
    "does not weaken §6 approval levels",
    "does not change current DONE gate semantics",
    "`USER != DEBUGGER`",
    # generic no-auto-promotion principle
    "Discovery, mining, index and learning outputs are EVIDENCE/CANDIDATE.",
    "SHALL NOT be automatically promoted to Canonical, MASTER or a global rule.",
    "Domain-owned learning stays with its domain owner and SHALL NOT be globalized by recurrence",
)

# Pipeline-specific operational detail belongs to its domain owner, not to the MASTER basis.
PIPELINE_SPECIFIC = (r"HTTP\s*200", r"SHELL-ONLY", r"learning\s+queue")

FIVE_GATES = ("KEY", "CONTEXT", "ROUTE", "COST", "DONE")
VENDOR_NAMES = ("ChatGPT", "Codex", "Claude", "Gemini", "OpenAI", "Anthropic")
# Active Drive-restored V2 has sections 1-10 only; older local numbering (e.g. §0.1, §14, §19) is stale.
V2_SECTIONS = {str(n) for n in range(1, 11)}


def section_02(text):
    m = re.search(r"^## 0\.2 .*?(?=^## )", text, re.M | re.S)
    return m.group(0) if m else ""


def subsection(sec, sid):
    m = re.search(r"^### " + re.escape(sid) + r"\b.*?(?=^### |\Z)", sec, re.M | re.S)
    return m.group(0) if m else ""


def validate(text):
    fail = []
    sec = section_02(text)
    if not sec:
        return ["MISSING_SECTION:0.2"]
    for token in REQUIRED:
        if token not in text:
            fail.append("MISSING_BASIS_TOKEN:" + token)
    # Every KEY / CONTEXT / ... gate list must be exactly the five hard gates.
    for m in re.finditer(r"\bKEY\s*/\s*CONTEXT(?:\s*/\s*[A-Z_]+)+", text):
        gates = [g.strip() for g in m.group(0).split("/")]
        if gates != list(FIVE_GATES):
            fail.append("SIXTH_HARD_GATE" if len(gates) > 5 else "HARD_GATES_ALTERED")
    if re.search(r"\b[A-Z_]+\s*/\s*KEY\s*/\s*CONTEXT\b", text):
        fail.append("SIXTH_HARD_GATE")
    if re.search(r"(?i)necessity\s+(?:is|=)\s+(?:a\s+)?(?:sixth\s+)?hard\s+gate", sec):
        fail.append("NECESSITY_PROMOTED_TO_GATE")
    # Storage location or CURRENT must not become the canonical source.
    if re.search(r"(?im)^(?:-\s*)?(?:Google\s+)?Drive\b[^\n]*=\s*CANONICAL\s+MASTER\s+SOURCE", text):
        fail.append("DRIVE_DECLARED_CANONICAL_MASTER_SOURCE")
    if re.search(r"(?im)^(?:-\s*)?`?CURRENT`?\s*=\s*(?:CANONICAL|SEMANTIC AUTHORITY)", text):
        fail.append("CURRENT_DECLARED_CANONICAL")
    # Section ids (## and ###) must stay unique.
    ids = re.findall(r"^#{2,3}\s+([0-9]+(?:\.[0-9]+)?[A-Z]?)\b", text, re.M)
    for dup in sorted({x for x in ids if ids.count(x) > 1}):
        fail.append("DUPLICATE_SECTION_ID:" + dup)
    # `V2 §n` citations must use the active V2 numbering.
    for ref in re.findall(r"\bV2\s*§\s*([0-9]+(?:\.[0-9]+)?)", text):
        if ref not in V2_SECTIONS:
            fail.append("STALE_V2_SECTION_REF:§" + ref)
    # The MASTER-only execution tail must not be presented as part of the V2 §4 order.
    if re.search(r"V2 §4\)?:[^\n]*EXECUTE\s*->\s*VERIFY", sec):
        fail.append("MASTER_PROTECTION_PRESENTED_AS_V2")
    # Role ontology (§0.2B) must not be bound to vendor/model names; references outside it are not role ontology.
    roles = subsection(sec, "0.2B")
    if not roles:
        fail.append("MISSING_SECTION:0.2B")
    for name in VENDOR_NAMES:
        if re.search(r"\b" + name + r"\b", roles):
            fail.append("VENDOR_NAME_IN_ROLE_BASIS:" + name)
    # The shared economy evaluator is implementation-OPEN; it must not be claimed enforced/implemented.
    if re.search(r"(?i)\b(?:economy\s+policy|economy\s+evaluator|runtime\s+evaluator)\b[^.\n]*?\b(?:is|are)\s+(?:now\s+)?(?:mechanically\s+)?(?:enforced|implemented)\b", sec):
        fail.append("ECONOMY_POLICY_CLAIMED_ENFORCED")
    # A two-stage completion policy stays CANDIDATE and must not redefine DONE.
    if re.search(r"(?i)two-stage\s+completion\s+policy[^.\n]*?\b(?:is|=)\s+(?:now\s+)?(?:canonical|active|enforced|adopted|promoted)\b", sec):
        fail.append("TWO_STAGE_COMPLETION_PROMOTED")
    if re.search(r"(?i)\bDONE\b[^.\n]*?\b(?:requires|=|means)\s+`?USER_CONFIRMED", sec):
        fail.append("DONE_REDEFINED_AS_USER_CONFIRMED")
    # Generic no-auto-promotion: pipeline operational text must not be globalized into the basis.
    for pat in PIPELINE_SPECIFIC:
        if re.search(r"(?i)" + pat, sec):
            fail.append("PIPELINE_SPECIFIC_TEXT_IN_MASTER_BASIS:" + pat)
    if re.search(r"(?i)\b(?:discovery|mining|index|learning)\b[^.\n]*?\b(?:are|is|may be)\s+(?:automatically\s+)?(?:promoted|canonical)\b", sec):
        fail.append("AUTO_PROMOTION_ALLOWED")
    # Candidate must not be declared canonical by this section.
    if re.search(r"(?i)V3[^\n]*\b(?:is|=|promoted to)\s+canonical", sec):
        fail.append("CANDIDATE_PROMOTED_TO_CANONICAL")
    return fail


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_PATH
    fail = validate(path.read_text(encoding="utf-8"))
    if fail:
        print("FAIL: MASTER_LOGIC systemwide basis")
        for x in fail:
            print(x)
        return 1
    print("PASS: MASTER_LOGIC preserves TAKY identity, control plane, five gates, Driver economy, owner-first and state semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
