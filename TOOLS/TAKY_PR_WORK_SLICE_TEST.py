#!/usr/bin/env python3
"""Self-contained tests for TAKY_PR_WORK_SLICE (temp fixtures only; no gh/model/network)."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import TAKY_PR_WORK_SLICE as W  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def wjson(path, data):
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class Env:
    def __init__(self, root):
        root = Path(root)
        self.src = [root / "TAKY_PR_EVENT_WATCH.py", root / "TAKY_PR_EVENT_WATCH_TEST.py"]
        self.src[0].write_text("# watch\n", encoding="utf-8")
        self.src[1].write_text("# test\n", encoding="utf-8")
        self.sources = tuple(str(p) for p in self.src)
        self.board = root / "TASK_REGISTER.json"
        self.receipt = root / "receipt.json"
        self.review = root / "review.json"
        self.write_all()

    def row(self, **over):
        row = {"id": "TAKY-001", "intake": {"project": "TAKY"}, "status": "IMPLEMENTING",
               "approval_required": False, "dependencies": [], "github_pr": None,
               "planned_source_bindings": [{"path": s, "sha256": sha(s)} for s in self.sources]}
        row.update(over)
        return row

    def write_all(self, row=None, receipt=None, review=None):
        wjson(self.board, {"tasks": [row or self.row(), {"id": "OTHER-1"}]})
        wjson(self.receipt, receipt or {
            "work_id": "TAKY-001",
            "current_verified_scope": {"source_sha256": {s: sha(s) for s in self.sources},
                                       "original_review_source_sha256": {s: sha(s) for s in self.sources}}})
        wjson(self.review, review or {
            "state": "COMPLETE_UNVERIFIED", "content_quality_verified": False,
            "content_qa_state": "CITATIONS_SCREENED_SEMANTIC_CONTENT_UNVERIFIED",
            "review_source_binding": {"source_manifest": [
                {"path": s, "sha256": sha(s),
                 "includedLines": 1, "totalLines": 1} for s in self.sources]}})

    def run(self):
        return {c["name"]: c for c in W.evaluate(
            str(self.board), str(self.receipt), str(self.review), self.sources)}


def reason(checks, name):
    return checks[name].get("reason")


def main():
    with tempfile.TemporaryDirectory() as tmp_raw:
        tmp = str(Path(tmp_raw).resolve())  # expand 8.3 short names so redirect check is not tripped
        e = Env(tmp)
        # Baseline: no github_pr binding -> HOLD PR_OWNER_BINDING_MISSING, integrity gates PASS.
        c = e.run()
        for name in ("canonical_task_row", "planned_source_pins_match_live",
                     "implementation_receipt_source_sha"):
            assert c[name]["status"] == "PASS", (name, c[name])
        assert c["canonical_task_row"]["board_source"] == "FIXTURE_INJECTED"
        # Self-consistent historical manifest is reference only, never an independent PASS.
        rv = c["signed_review_status_and_receipt_sha"]
        assert rv["status"] == "HOLD" and rv["reason"] == "HISTORICAL_REVIEW_NOT_INDEPENDENTLY_VERIFIED", rv
        assert "reference diagnostic only" in rv["detail"]
        assert c["github_pr_owner_binding"]["status"] == "HOLD"
        assert reason(c, "github_pr_owner_binding") == "PR_OWNER_BINDING_MISSING"
        assert "next_action" in c["github_pr_owner_binding"]

        # Valid binding -> PASS (presence only, no PR call).
        e.write_all(row=e.row(github_pr={"repo": "owner/name", "pr": 7}))
        assert e.run()["github_pr_owner_binding"]["status"] == "PASS"
        # Malformed bindings never PASS.
        for bad in ({"repo": "owner/name"}, {"repo": "owner/name", "pr": True},
                    {"repo": "bad repo", "pr": 1}, {"repo": "o/n", "pr": 1, "x": 1}, "o/n#1"):
            e.write_all(row=e.row(github_pr=bad))
            assert e.run()["github_pr_owner_binding"]["reason"] == "PR_OWNER_BINDING_INVALID", bad

        # Row gates fail closed and skip dependent checks.
        for over, why in (({"status": "VERIFIED"}, "WORK_NOT_ACTIVE"),
                          ({"approval_required": True}, "APPROVAL_REQUIRED_OR_UNKNOWN"),
                          ({"dependencies": ["X-1"]}, "DEPENDENCIES_NOT_EMPTY"),
                          ({"intake": {"project": "OTHER"}}, "PROJECT_MISMATCH")):
            e.write_all(row=e.row(**over))
            c = e.run()
            assert reason(c, "canonical_task_row") == why, (over, c["canonical_task_row"])
            assert c["planned_source_pins_match_live"]["status"] == "HOLD"
            assert c["github_pr_owner_binding"]["status"] == "HOLD"
        wjson(e.board, {"tasks": [e.row(), e.row()]})
        assert reason(e.run(), "canonical_task_row") == "WORK_ID_NOT_UNIQUE_IN_REGISTER"
        wjson(e.board, {"tasks": []})
        assert reason(e.run(), "canonical_task_row") == "WORK_ID_NOT_UNIQUE_IN_REGISTER"

        # Pin drift / malformed pins.
        e.write_all()
        pins = e.row()["planned_source_bindings"]
        bad_pin = [dict(pins[0], sha256="0" * 64), pins[1]]
        e.write_all(row=e.row(planned_source_bindings=bad_pin))
        c = e.run()["planned_source_pins_match_live"]
        assert c["status"] == "FAIL" and c["reason"] == "PLANNED_SOURCE_PIN_SHA_MISMATCH"
        e.write_all(row=e.row(planned_source_bindings=[dict(pins[0], extra=1), pins[1]]))
        assert e.run()["planned_source_pins_match_live"]["reason"] == "PLANNED_SOURCE_BINDING_KEYS"
        e.write_all(row=e.row(planned_source_bindings=[pins[0]]))
        assert e.run()["planned_source_pins_match_live"]["reason"] == "PLANNED_SOURCE_BINDINGS_INVALID"
        e.write_all(row=e.row(planned_source_bindings=[pins[0], dict(pins[0])]))
        assert e.run()["planned_source_pins_match_live"]["status"] == "HOLD"
        e.write_all(row=e.row(planned_source_bindings=[pins[0], dict(pins[1], path=str(Path(tmp) / "x.py"))]))
        assert e.run()["planned_source_pins_match_live"]["reason"] == "PLANNED_SOURCE_BINDING_PATHS_UNEXPECTED"

        # Receipt: wrong work id, missing mapping, sha drift.
        e.write_all(receipt={"work_id": "OTHER-1", "current_verified_scope": {"source_sha256": {}}})
        assert reason(e.run(), "implementation_receipt_source_sha") == "RECEIPT_WORK_ID_MISMATCH"
        e.write_all(receipt={"work_id": "TAKY-001"})
        assert reason(e.run(), "implementation_receipt_source_sha") == "RECEIPT_SOURCE_MAPPING_MISSING"
        e.write_all(receipt={"work_id": "TAKY-001", "current_verified_scope": {
            "source_sha256": {e.sources[0]: sha(e.sources[0])}}})
        assert reason(e.run(), "implementation_receipt_source_sha") == "RECEIPT_SOURCE_SHA_ABSENT"
        e.write_all(receipt={"work_id": "TAKY-001", "current_verified_scope": {
            "source_sha256": {e.sources[0]: sha(e.sources[0]), e.sources[1]: "1" * 64}}})
        c = e.run()["implementation_receipt_source_sha"]
        assert c["status"] == "FAIL" and c["reason"] == "RECEIPT_SOURCE_SHA_MISMATCH"

        # Review: state/flags/manifest/receipt sha.
        e.write_all()
        base = json.loads(e.review.read_text(encoding="utf-8"))
        for field, value, why in (
                ("state", "COMPLETE", "REVIEW_STATE_NOT_RECORDED_STATE"),
                ("content_quality_verified", True, "REVIEW_QUALITY_FLAG_UNEXPECTED"),
                ("content_qa_state", "VERIFIED", "REVIEW_QA_STATE_UNEXPECTED"),
                ("review_source_binding", {}, "REVIEW_SOURCE_MANIFEST_MISSING")):
            wjson(e.review, dict(base, **{field: value}))
            assert reason(e.run(), "signed_review_status_and_receipt_sha") == why, field
        wjson(e.review, dict(base, review_source_binding={"source_manifest": []}))
        assert reason(e.run(), "signed_review_status_and_receipt_sha") == "REVIEW_SOURCE_SET_MISMATCH"
        stale = {"source_manifest": [{"path": s, "sha256": "2" * 64
                                      if i == 0 else sha(s)}
                                     for i, s in enumerate(e.sources)]}
        wjson(e.review, dict(base, review_source_binding=stale))
        c = e.run()["signed_review_status_and_receipt_sha"]
        assert c["status"] == "FAIL" and c["reason"] == "HISTORICAL_REVIEW_SOURCE_SHA_MISMATCH"

        # Duplicate JSON keys and colliding normalized receipt paths are rejected.
        e.write_all()
        e.board.write_text('{"tasks": [], "tasks": []}', encoding="utf-8")
        assert reason(e.run(), "canonical_task_row") == "JSON_DUPLICATE_KEY"
        e.write_all()
        e.receipt.write_text('{"work_id": "TAKY-001", "work_id": "OTHER-1"}', encoding="utf-8")
        assert reason(e.run(), "implementation_receipt_source_sha") == "JSON_DUPLICATE_KEY"
        alias = e.sources[0].replace("TAKY_PR_EVENT_WATCH.py", "." + os.sep + "TAKY_PR_EVENT_WATCH.py")
        e.write_all(receipt={"work_id": "TAKY-001", "current_verified_scope": {"source_sha256": {
            e.sources[0]: sha(e.sources[0]), alias: "3" * 64, e.sources[1]: sha(e.sources[1])}}})
        assert reason(e.run(), "implementation_receipt_source_sha") == "RECEIPT_SOURCE_KEY_DUPLICATE"

        # Ancestor symlink/redirect is refused; relative paths are refused.
        e.write_all()
        real = Path(tmp) / "realdir"
        real.mkdir()
        (real / "f.json").write_text("{}", encoding="utf-8")
        link = Path(tmp) / "linkdir"
        try:
            os.symlink(real, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            print("symlink unavailable: ancestor-symlink case skipped")
        else:
            try:
                W._safe_file(str(link / "f.json"))
                raise AssertionError("ancestor symlink accepted")
            except W.Hold as h:
                assert h.reason == "PATH_REPARSE", h.reason
        assert W._safe_file(str(real / "f.json")).name == "f.json"
        try:
            W._safe_file("relative.json")
            raise AssertionError("relative path accepted")
        except W.Hold as h:
            assert h.reason == "PATH_NOT_ABSOLUTE"

        # Missing files and unreadable JSON never PASS.
        e.write_all()
        e.review.write_text("{not json", encoding="utf-8")
        assert e.run()["signed_review_status_and_receipt_sha"]["status"] == "HOLD"
        e.review.unlink()
        assert reason(e.run(), "signed_review_status_and_receipt_sha") == "FILE_MISSING"

        # Live source drift after pinning is caught.
        e.write_all()
        e.src[0].write_text("# changed\n", encoding="utf-8")
        assert e.run()["planned_source_pins_match_live"]["status"] == "FAIL"

        # Worker contract + isolation: list of dicts, constant paths absolute, no side effects.
        assert W.WORKERS == {"TAKY-001": W.pr_work_slice}
        for p in (*W.SOURCE_PATHS, W.RECEIPT_PATH, W.REVIEW_PATH):
            assert os.path.isabs(p)
        before = sorted(os.listdir(tmp))
        e.run()
        assert sorted(os.listdir(tmp)) == before
    print("TAKY_PR_WORK_SLICE_TEST: PASS")


if __name__ == "__main__":
    main()
