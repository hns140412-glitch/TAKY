"""Explicit one-shot TAKY read-only source review Workbench refresh.

CURRENT and Central DB untouched. Fresh source/index revision yields a new
immutable review queue, full RAW-verified anchors, and offline review UI.
No scheduled watcher, paid model, automatic owner credentials, or approvals.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import central_forming_review_queue as queue
import central_full_anchor_review as full
import central_local_review_console as console
import taky_central_source_factory as factory
import taky_gate

def ui_design_gate_hold(ui_path, evidence_root):
    """Project-reference-first gate for unapproved internal browser review UI."""
    contract={
        "baseline_evidence_refs":[str(ui_path),"MASTER/UI_REFERENCE_PROTOCOL.md",
                                  "MASTER/ENGINEERING_EXECUTION_PROFILE_PROTOCOL.md"],
        "protected_state":["External reference is not a project approved Golden",
                           "Review input UI does not grant semantic approval"],
        "target_delta":"Check against project-approved UI mockup before promotion",
        "acceptance_conditions":["approved mockup bound to design_contract_ref",
                                 "viewport matching and accessible interaction evidence"],
        "validation_steps":["Compare real browser render to approved reference"],
        "regression_scope":["browser search, notes and source anchor binding"],
        "remaining_unknowns":["No approved visual/mockup for this particular browser console was found"],
        "report_mode":"SEPARATE_UI_GATE",
        "project_reference_checked":False,
        "responsive_states_defined":False,
        "accessibility_check_defined":False,
        "design_contract_ref":"",
    }
    failures=taky_gate.validate_record({
        "engineering_execution_profile_required":True,
        "engineering_profile":"UI_IMPLEMENTATION",
        "engineering_contract":contract,
        "claims_complete":False,
    })
    if "RULE_NOT_APPLIED" not in failures:
        raise ValueError("MISSING_DESIGN_CONTRACT_WAS_NOT_REJECTED_BY_EXISTING_GATE")
    html_sha256=hashlib.sha256(Path(ui_path).read_bytes()).hexdigest()
    evidence={
        "schema":"TAKY_UI_DESIGN_GATE_SCREEN_AUDIT_V1",
        "surface":"TAKY_OFFLINE_SOURCE_REVIEW_CONSOLE",
        "ui_html":str(ui_path),"ui_html_sha256":html_sha256,
        "status":"HOLD_APPROVED_VISUAL_AND_DESIGN_CONTRACT_MISSING",
        "design_contract_ref":None,"approved_mockup_ref":None,
        "approved_mockup_sha256":None,"comparison_receipt":None,
        "responsive_verified":False,"accessibility_verified":False,
        "interaction_verification_separate":True,
        "taky_gate_findings":failures,
        "claim_ui_done":False,"design_promotion_allowed":False,
        "local_preview_allowed":True,"independent_approval":False,
    }
    path=Path(evidence_root)/("TAKY_UI_DESIGN_GATE_HOLD_"+html_sha256[:20]+".json")
    body=json.dumps(evidence,ensure_ascii=False,indent=2)+"\n"
    if path.exists():
        if path.read_text(encoding="utf-8")!=body:
            raise ValueError("DESIGN_GATE_RECEIPT_IMMUTABILITY_CONFLICT")
    else:
        with path.open("x",encoding="utf-8") as f:f.write(body)
    return path



def run(*, emit=True, evidence=queue.EVIDENCE, source_ids=None, candidates_json=None,
        design_candidate_css=None):
    with sqlite3.connect(factory.DB.as_uri()+"?mode=ro",uri=True,timeout=10) as db:
        db.row_factory=sqlite3.Row
        original=queue.build_queue(db,source_ids)
        expanded=full.project(db,original)
        notes=json.loads(Path(candidates_json).read_text(encoding="utf-8")) if candidates_json else None
        stylesheet=None
        if design_candidate_css is not None:
            allowed=(Path(__file__).resolve().parents[2]/
                "TAKY_AI_WORKBENCH"/"20_DESIGN_STUDIO"/"UI-UX").resolve()
            candidate=Path(design_candidate_css).resolve(strict=True)
            if (candidate.parent!=allowed or
                candidate.name!="TAKY_SOURCE_REVIEW_PC_DESIGN_CANDIDATE_V1.css"
                or candidate.is_symlink()):
                raise ValueError("UNAUTHORIZED_DESIGN_CANDIDATE_SOURCE")
            stylesheet=candidate.read_text(encoding="utf-8")
        html=console.render(expanded,db,application_candidates=notes,
                            candidate_stylesheet=stylesheet)
    if (expanded["review_ready_sources"]+len(expanded["existing_holds"])
        !=original["source_count"] or expanded["independent_owner_reviewed_count"]!=0
        or expanded["forming_approved"] or expanded["learning_consumed"]):
        raise ValueError("WORKBENCH_AUTHORITY_OR_COVERAGE_INVALID")
    root=Path(evidence)
    q_path,q_created=queue.write_immutable(original,root)
    all_path,all_created=full.save_immutable(expanded,root)
    ui_path=root/console.ui_name(expanded["manifest_sha256"],html)
    if ui_path.exists():
        if ui_path.read_text(encoding="utf-8")!=html:
            raise ValueError("LOCAL_UI_IMMUTABLE_REVISION_CONFLICT")
        ui_created=False
    else:
        with ui_path.open("x",encoding="utf-8") as output:
            output.write(html)
        ui_created=True
    gate_receipt=ui_design_gate_hold(ui_path,root)
    result={"status":"FUNCTIONAL_PREVIEW_DESIGN_GATE_HOLD",
        "indexed_sources":original["source_count"],
        "review_ready_sources":expanded["review_ready_sources"],
        "specialist_or_metadata_holds":len(expanded["existing_holds"]),
        "all_verified_anchors":expanded["verified_anchor_count"],
        "lexical_reference_mentions":expanded["verbatim_reference_mentions"],
        "duplicate_anchor_hash_occurrences":expanded["duplicate_anchor_hash_occurrences"],
        "queue_file":str(q_path),"full_anchor_file":str(all_path),
        "local_review_console":str(ui_path),
        "design_gate_receipt":str(gate_receipt),
        "design_gate_status":"HOLD_APPROVED_VISUAL_AND_DESIGN_CONTRACT_MISSING",
        "ui_visual_match_verified":False,
        "ui_design_approved":False,
        "local_preview_only":True,
        "design_candidate_applied_to_preview":design_candidate_css is not None,
        "new_files":sum([q_created,all_created,ui_created]),
        "independent_approvals":0,"forming_promotions":0,"learning_executed":False,
        "operational_db_readonly":True,"CURRENT_modified":False,
        "paid_api_calls":0,"scheduled_jobs_created":0}
    if emit:
        print(json.dumps(result,ensure_ascii=False))
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--refresh-once",action="store_true",required=True)
    parser.add_argument("--source-id",action="append",dest="source_ids",default=[])
    parser.add_argument("--candidates-json",type=Path)
    parser.add_argument("--design-candidate-css",type=Path)
    args=parser.parse_args()
    run(source_ids=args.source_ids or None,candidates_json=args.candidates_json,
        design_candidate_css=args.design_candidate_css)


if __name__=="__main__":
    main()
