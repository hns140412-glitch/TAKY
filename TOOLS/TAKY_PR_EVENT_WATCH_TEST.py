#!/usr/bin/env python3
"""Self-contained tests for TAKY_PR_EVENT_WATCH.py (mocked gh; temp dirs; no network)."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "TAKY_PR_EVENT_WATCH.py"
spec = importlib.util.spec_from_file_location("taky_pr_event_watch", SRC)
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)  # import must succeed on Windows (no fcntl etc.)

REPO, PR, WID = "o/r", 7, "TAKY-001"
A, B = "a" * 40, "b" * 40


def view(head=A, state="OPEN", draft=False, mergeable="MERGEABLE", ms="CLEAN", review="", number=PR):
    return json.dumps({
        "number": number, "url": "https://github.com/%s/pull/%d" % (REPO, number), "headRefOid": head,
        "state": state, "isDraft": draft, "mergeable": mergeable, "mergeStateStatus": ms,
        "reviewDecision": review})


def checks(*pairs):
    return json.dumps([{"name": n, "bucket": b, "state": b.upper()} for n, b in pairs])


class FakeGh:
    """Replaces subprocess.run. views: consumed in order; checks: single response."""

    def __init__(self, views, check_rc=0, check_out="[]"):
        self.views = list(views)
        self.check_rc, self.check_out = check_rc, check_out
        self.calls = []

    def __call__(self, argv, **kw):
        self.calls.append((list(argv), kw))
        assert kw.get("shell") is not True
        if argv[2] == "view":
            out = self.views.pop(0) if len(self.views) > 1 else self.views[0]
            return subprocess.CompletedProcess(argv, 0, out, "")
        assert argv[2] == "checks", argv
        return subprocess.CompletedProcess(argv, self.check_rc, self.check_out, "")


def run(state, fake, work_id=WID):
    real = watch.subprocess.run
    watch.subprocess.run = fake
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = watch.main(["--repo", REPO, "--pr", str(PR), "--work-id", work_id, "--state-file", state])
    finally:
        watch.subprocess.run = real
    return rc, json.loads(buf.getvalue())


def kinds(res):
    return [e["event"] for e in res["events"]]


def fake_ok(v=None, rc=0, out="[]"):
    v = v or view()
    return FakeGh([v, v], rc, out)


def main():
    src = SRC.read_text(encoding="utf-8")
    assert "fcntl" not in src and "shell=True" not in src and "sleep(" not in src
    assert watch.WORK_ID_RE.match("SKL-001") and not watch.WORK_ID_RE.match("bad")

    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "sub", "pr7.json")

        # 1. first run: pre-existing failure is actionable; exit 1 from gh checks is data
        fails = checks(("build", "fail"), ("lint", "pass"))
        g = fake_ok(rc=1, out=fails)
        rc, r = run(st, g)
        assert rc == 0 and r["status"] == "OK" and r["ci"] == "FAIL", r
        assert kinds(r) == ["ci_failure"] and r["events"][0]["new_failing_checks"] == ["build"], r
        assert os.path.exists(st) and not any(f.endswith(".tmp") for f in os.listdir(os.path.dirname(st)))
        # read-only: only gh pr view / gh pr checks, never shell
        for argv, kw in g.calls:
            assert argv[:2] == ["gh", "pr"] and argv[2] in ("view", "checks") and not kw.get("shell")

        # 2. unchanged -> no event, checkpoint bytes untouched
        before = Path(st).read_bytes()
        rc, r = run(st, fake_ok(rc=1, out=fails))
        assert rc == 0 and r["events"] == [] and Path(st).read_bytes() == before, r

        # 3. failed -> green: recovery + merge-ready-for-human-review (no merge performed)
        rc, r = run(st, fake_ok(out=checks(("build", "pass"), ("lint", "pass"))))
        assert kinds(r) == ["ci_recovered", "merge_ready_for_human_review"], r
        assert r["forbidden_actions"] == ["push", "merge", "deploy", "github_mutation"]
        rc, r = run(st, fake_ok(out=checks(("build", "pass"), ("lint", "pass"))))
        assert r["events"] == []

        # 4. new failure on a new head after green is a new event
        v2 = view(head=B)
        rc, r = run(st, FakeGh([v2, v2], 1, checks(("build", "fail"))))
        assert kinds(r) == ["ci_failure"], r

        # 5. stale head: head changes between the reads -> UNKNOWN, checkpoint intact
        before = Path(st).read_bytes()
        rc, r = run(st, FakeGh([view(head=B), view(head=A)], 0, checks(("build", "pass"))))
        assert rc == 3 and r["status"] == "UNKNOWN" and r["reason"] == "stale_head_during_read" and r["events"] == []
        assert Path(st).read_bytes() == before

    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")

        # 6. wrong identity (PR number / repo mismatch) -> UNKNOWN, no checkpoint
        rc, r = run(st, fake_ok(view(number=99)))
        assert rc == 3 and r["reason"] == "identity_mismatch" and not os.path.exists(st)

        # 7. malformed gh JSON (view and checks) and unreachable gh -> UNKNOWN
        rc, r = run(st, fake_ok("not json"))
        assert rc == 3 and r["reason"] == "gh_json_malformed" and not os.path.exists(st)
        rc, r = run(st, fake_ok(rc=0, out="{oops"))
        assert rc == 3 and r["reason"] == "gh_json_malformed" and not os.path.exists(st)
        rc, r = run(st, fake_ok(rc=4, out="[]"))
        assert rc == 3 and r["reason"] == "gh_exit_4"
        rc, r = run(st, fake_ok(out=json.dumps([{"name": "x", "bucket": "weird"}])))
        assert rc == 3 and r["reason"] == "checks_entry_invalid"

        def boom(argv, **kw):
            raise FileNotFoundError("gh")
        rc, r = run(st, boom)
        assert rc == 3 and r["reason"] == "gh_unavailable" and not os.path.exists(st)

        # 8. exit 8 (pending) with valid JSON is data: PENDING, no event, no green
        rc, r = run(st, fake_ok(rc=8, out=checks(("build", "pending"), ("lint", "pass"))))
        assert rc == 0 and r["ci"] == "PENDING" and r["events"] == [], r

    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")

        # 9. no checks is never PASS and never merge-ready; no-checks text output -> UNKNOWN
        rc, r = run(st, fake_ok(out="[]"))
        assert rc == 0 and r["ci"] == "NO_CHECKS" and r["events"] == [], r
        rc, r = run(st, FakeGh([view(), view()], 1, "no checks reported on the 'x' branch"))
        assert rc == 3 and r["reason"] == "gh_json_malformed"

        # 10. conflict / review / draft flags
        rc, r = run(st, fake_ok(view(mergeable="CONFLICTING", ms="DIRTY", review="CHANGES_REQUESTED"),
                                out=checks(("build", "pass"))))
        assert kinds(r) == ["review_needed", "conflict"], r
        # draft never review_needed / merge_ready
        st2 = os.path.join(d, "draft.json")
        rc, r = run(st2, fake_ok(view(draft=True, review="REVIEW_REQUIRED"), out=checks(("b", "pass"))))
        assert r["events"] == [], r

        # 11. merged / closed terminal events once
        rc, r = run(st, fake_ok(view(state="MERGED"), out=checks(("build", "pass"))))
        assert kinds(r) == ["merged"], r
        rc, r = run(st, fake_ok(view(state="MERGED"), out=checks(("build", "pass"))))
        assert r["events"] == []

    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")

        # 12. state write failure: fail closed, no events, no leftover temp, no checkpoint
        real_replace = watch.os.replace

        def bad_replace(a, b):
            raise OSError("disk full")
        watch.os.replace = bad_replace
        try:
            rc, r = run(st, fake_ok(rc=1, out=checks(("build", "fail"))))
        finally:
            watch.os.replace = real_replace
        assert rc == 3 and r["reason"] == "state_write_failed" and r["events"] == []
        assert not os.path.exists(st) and not any(f.endswith(".tmp") for f in os.listdir(d))

        # 13. corrupt checkpoint -> UNKNOWN, file preserved (not overwritten)
        Path(st).write_text("{garbage", encoding="utf-8")
        rc, r = run(st, fake_ok(out=checks(("build", "pass"))))
        assert rc == 3 and r["reason"] == "checkpoint_corrupt" and Path(st).read_text(encoding="utf-8") == "{garbage"
        os.remove(st)

        # 14. checkpoint bound to identity: other work-id cannot reuse it
        rc, r = run(st, fake_ok(out=checks(("build", "pass"))))
        assert rc == 0
        before = Path(st).read_bytes()
        rc, r = run(st, fake_ok(out=checks(("build", "pass"))), work_id="OTHER-002")
        assert rc == 3 and r["reason"] == "checkpoint_identity_mismatch" and Path(st).read_bytes() == before

        # 15. OS lock refuses concurrent admission, even when lock path is old.
        with watch._Lock(st):
            os.utime(st + ".lock", (1, 1))
            rc, r = run(st, fake_ok(out=checks(("build", "pass"))))
            assert rc == 3 and r["reason"] == "state_locked", r
        # A persistent sidecar remains, but its kernel lock is released.
        rc, r = run(st, fake_ok(out=checks(("build", "pass"))))
        assert rc == 0 and os.path.exists(st + ".lock"), r

    # 16. argument validation (bad work id, non-positive PR, bad repo)
    for bad in (["--repo", REPO, "--pr", "0", "--work-id", WID, "--state-file", "x"],
                ["--repo", REPO, "--pr", "1", "--work-id", "bad", "--state-file", "x"],
                ["--repo", "nope", "--pr", "1", "--work-id", WID, "--state-file", "x"],
                ["--repo", REPO, "--pr", "1", "--work-id", WID]):
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                watch.main(bad)
            except SystemExit as exc:
                assert exc.code == 2
            else:
                raise AssertionError("expected usage failure: %r" % bad)

    # 17. gh allow-list refuses anything but pr view / pr checks
    try:
        watch._run_gh(["pr", "merge", "1"])
    except watch.Unknown as exc:
        assert exc.reason == "gh_subcommand_not_allowed"
    else:
        raise AssertionError("mutating gh subcommand must be refused")

    resume_tests()
    _independent_review_regressions()
    print("TAKY_PR_EVENT_WATCH_TEST: PASS")


def row(**over):
    r = {"id": WID, "status": "READY", "approval_required": False, "dependencies": [],
         "github_pr": {"repo": REPO, "pr": PR}}
    r.update(over)
    return r


def run_resume(state, fake, board, engine, work_id=WID):
    saved = (watch.subprocess.run, watch._registered_gate, watch._engine_dispatch)
    watch.subprocess.run = fake
    watch._registered_gate = lambda w, r, p: watch._gate_row(board, w, r, p)
    watch._engine_dispatch = engine
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = watch.main(["--repo", REPO, "--pr", str(PR), "--work-id", work_id,
                             "--state-file", state, "--resume-registered-local"])
    finally:
        watch.subprocess.run, watch._registered_gate, watch._engine_dispatch = saved
    return rc, json.loads(buf.getvalue())


def valid_result(item_status="LOCAL_DIAGNOSIS_EVIDENCED_NOT_DONE", item_work_id=WID, receipt=True, **over):
    ref = None
    if receipt:
        name = "taky-goal-queue-%s.json" % os.urandom(16).hex()
        ref = ".local/" + name
        # Persist the exact existing queue summary, not a presence-only dummy file.
    res = {"schema": "TAKY_GOAL_QUEUE_OBSERVATION_V2", "queue_id": "prwatch-test",
           "status": "REGISTERED_LOCAL_TASKS_OBSERVED", "items_total": 1, "items_executed": 1,
           "items_deferred": 0, "deferred_work_ids": [],
           "items": [{"work_id": item_work_id, "status": item_status, "attempted": True}],
           "goals_verified_done": 0, "model_calls": 0, "authority_updated": False}
    if ref:
        res["local_queue_receipt"] = ref
    res.update(over)
    if ref:
        (watch.ROOT_DIR / ref).write_text(json.dumps(
            {k: v for k, v in res.items() if k != "local_queue_receipt"}), encoding="utf-8")
    return res


class Engine:
    def __init__(self, result=None, exc=None):
        self.calls, self.result, self.exc = [], result, exc

    def __call__(self, work_id, deps, key):
        self.calls.append((work_id, deps, key))
        if self.exc:
            raise self.exc
        return self.result if self.result is not None else valid_result()


def resume_tests():
    real_root = watch.ROOT_DIR
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, ".local"))
        watch.ROOT_DIR = Path(root).resolve()
        try:
            _resume_tests()
            _hardening_tests()
            _integrated_registered_queue_test()
        finally:
            watch.ROOT_DIR = real_root


def _integrated_registered_queue_test():
    """Real watcher -> existing queue -> real receipt; mocked *local worker* only."""
    from unittest.mock import patch
    repo_root = HERE.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    import TAKY_ORCHESTRATION_ADVANCE as advance
    from ENFORCEMENT.taky_registered_goal_queue import execute_registered_queue

    root = watch.ROOT_DIR
    (root / "TOOLS").mkdir(exist_ok=True)
    proof_dir = root / "evidence"
    proof_dir.mkdir(exist_ok=True)
    board_file = root / "canonical-board.json"
    board_file.write_text(json.dumps({"tasks": [row()]}), encoding="utf-8")
    state = str(root / "integrated-state.json")
    called = []

    def real_queue_local_worker(work_id, _board, evidence, **_kwargs):
        assert work_id == WID and evidence.resolve() == proof_dir.resolve()
        _kwargs["on_worker_claimed"](work_id)
        called.append(work_id)
        proof = proof_dir / "synthetic-local-proof.json"
        proof.write_text(json.dumps({"schema": "TAKY_LOCAL_WORK_SLICE_V1",
                                    "task_id": WID, "portfolio_done": False}), encoding="utf-8")
        return {"task_id": WID, "no_model_calls": True, "evidence": str(proof)}

    def admissible(_board, _root):
        return {"considered": [{"task_id": WID, "route": "READY_FOR_LOCAL_EXECUTION"}]}

    saved_gh = watch.subprocess.run
    gh = fake_ok(rc=1, out=checks(("build", "fail")))
    try:
        with patch.object(advance, "DEFAULT_BOARD", board_file), \
             patch.object(advance, "EVIDENCE", proof_dir), \
             patch.object(advance, "choose", admissible), \
             patch.object(advance, "run_checks", real_queue_local_worker), \
             patch.dict(advance.LOCAL_EXECUTORS, {WID: "SYNTHETIC_READONLY"}):
            watch.subprocess.run = gh
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = watch.main(["--repo", REPO, "--pr", str(PR),
                                   "--work-id", WID, "--state-file", state,
                                   "--resume-registered-local"])
            result = json.loads(output.getvalue())
            assert code == 0 and kinds(result) == ["ci_failure"], result
            accepted = result["registered_dispatch"]
            assert accepted["status"] == "DISPATCHED_OBSERVATION_NOT_DONE", accepted
            assert called == [WID] and accepted["engine_result"]["items_executed"] == 1, (called, accepted)
            ref = accepted["engine_result"]["local_queue_receipt"]
            receipt = json.loads((root / ref).read_text(encoding="utf-8"))
            assert receipt["items"][0]["work_id"] == WID
            assert "pending" not in json.loads(Path(state).read_text(encoding="utf-8"))
            # Existing persisted checkpoint prevents a second worker launch.
            gh2 = fake_ok(rc=1, out=checks(("build", "fail")))
            watch.subprocess.run = gh2
            repeat_output = io.StringIO()
            with contextlib.redirect_stdout(repeat_output):
                code = watch.main(["--repo", REPO, "--pr", str(PR),
                                   "--work-id", WID, "--state-file", state,
                                   "--resume-registered-local"])
            repeated = json.loads(repeat_output.getvalue())
            assert code == 0 and repeated["registered_dispatch"]["status"] == "NONE_PENDING"
            assert called == [WID] and repeated["events"] == []
            assert all(argv[2] in ("view", "checks") for argv, _kw in gh.calls + gh2.calls)
    finally:
        watch.subprocess.run = saved_gh


def _hardening_tests():
    fail = checks(("build", "fail"))
    board = {"tasks": [row()]}
    # BUG1: default (flag off) run with a changed snapshot must keep pending, never dispatch
    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, Engine(exc=RuntimeError("boom")))
        before = json.loads(Path(st).read_text(encoding="utf-8"))["pending"]
        assert len(before) == 1
        def no_engine(*a):
            raise AssertionError("default run must not dispatch")
        saved = watch._engine_dispatch
        watch._engine_dispatch = no_engine
        try:
            rc, r = run(st, fake_ok(rc=0, out=checks(("build", "pass"))))  # snapshot changed
            assert rc == 0 and "registered_dispatch" not in r, r
            cp = json.loads(Path(st).read_text(encoding="utf-8"))
            assert cp["pending"] == before and cp["ci"] == "PASS", cp
            rc, r = run(st, fake_ok(rc=1, out=checks(("other", "fail"))))  # changed again
            assert json.loads(Path(st).read_text(encoding="utf-8"))["pending"] == before
        finally:
            watch._engine_dispatch = saved
    # Old-head failures cannot dispatch under a newer PR head; only current events may.
    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "old-head.json")
        first = run_resume(st, fake_ok(rc=1, out=fail), board, Engine(exc=RuntimeError("failed")))
        assert first[1]["registered_dispatch"]["status"] == "DISPATCH_ERROR"
        old_key = json.loads(Path(st).read_text(encoding="utf-8"))["pending"][0]["key"]
        v2 = view(head=B)
        current_engine = Engine()
        rc, r = run_resume(st, FakeGh([v2, v2], 1, fail), board, current_engine)
        assert rc == 0 and len(current_engine.calls) == 1
        assert current_engine.calls[0][2] == watch._event_key(r["snapshot_hash"], "ci_failure")
        assert current_engine.calls[0][2] != old_key
        pending = json.loads(Path(st).read_text(encoding="utf-8"))["pending"]
        assert len(pending) == 1 and pending[0]["key"] == old_key
        held_engine = Engine()
        rc, r = run_resume(st, FakeGh([v2, v2], 1, fail), board, held_engine)
        assert r["registered_dispatch"]["status"] == "STALE_PENDING_HOLD" and not held_engine.calls
    # BUG2: only an exact valid ACK clears pending
    tampered_receipt = valid_result()
    (watch.ROOT_DIR / tampered_receipt["local_queue_receipt"]).write_text(
        '{"status":"REGISTERED_LOCAL_TASKS_OBSERVED"}', encoding="utf-8")
    bad_results = {
        "tampered_receipt_contents": tampered_receipt,
        "deferred": valid_result(status="REGISTERED_LOCAL_TASKS_PARTIALLY_DEFERRED", items_deferred=1,
                                 deferred_work_ids=[WID]),
        "items_deferred_only": valid_result(items_deferred=1),
        "missing_receipt": valid_result(receipt=False),
        "fake_receipt": valid_result(receipt=False, local_queue_receipt=".local/taky-goal-queue-" + "0" * 32 + ".json"),
        "wrong_work_id": valid_result(item_work_id="OTHER-002"),
        "bad_item_status": valid_result(item_status="EXISTING_CANONICAL_GATE_HOLD"),
        "wrong_schema": valid_result(schema="X"),
        "two_items": valid_result(items_total=2),
        "plain_dict": {"status": "LOCAL_DONE_OBS", "items_executed": 1},
    }
    for name, res in bad_results.items():
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "s.json")
            eng = Engine(result=res)
            rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng)
            assert r["registered_dispatch"]["status"] == "ENGINE_RESULT_NOT_ACKED", (name, r)
            assert len(eng.calls) == 1 and r["registered_dispatch"]["dispatch_calls"] == 1
            assert len(json.loads(Path(st).read_text(encoding="utf-8"))["pending"]) == 1, name
    # reused-evidence item status is also a valid ACK
    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")
        eng = Engine(result=valid_result(item_status="REUSED_CANONICAL_LOCAL_EVIDENCE"))
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng)
        assert r["registered_dispatch"]["status"] == "DISPATCHED_OBSERVATION_NOT_DONE"
        assert "pending" not in json.loads(Path(st).read_text(encoding="utf-8"))


def _resume_tests():
    fail = checks(("build", "fail"))
    board = {"tasks": [row(dependencies=["DEP-001"]), row(id="OTHER-002")]}
    # production: TAKY-001 has no github_pr binding -> real gate HOLDs (0 dispatch)
    ok, why = watch._registered_gate(WID, REPO, PR)
    assert not ok, (ok, why)

    # gate rejections: no/conflicting binding, approval, inactive, duplicate, bad shape
    for bad in (row(github_pr=None), row(github_pr={"repo": REPO, "pr": PR + 1}),
                row(github_pr={"repo": "x/y", "pr": PR}), row(github_pr={"repo": REPO, "pr": True}),
                row(github_pr={"repo": REPO, "pr": PR, "x": 1}), row(approval_required=True),
                row(approval_required=None), row(status="DONE"), row(status="VERIFIED")):
        with tempfile.TemporaryDirectory() as d:
            eng = Engine()
            rc, r = run_resume(os.path.join(d, "s.json"), fake_ok(rc=1, out=fail), {"tasks": [bad]}, eng)
            assert rc == 0 and kinds(r) == ["ci_failure"], r
            assert r["registered_dispatch"]["status"] == "HOLD" and not eng.calls, (bad, r)
    for tasks in ([], [row(), row()]):
        assert not watch._gate_row({"tasks": tasks}, WID, REPO, PR)[0]

    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")
        # actionable -> exactly one engine call with canonical deps; unchanged -> none
        eng = Engine()
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng)
        assert len(eng.calls) == 1 and eng.calls[0][:2] == (WID, ["DEP-001"]), eng.calls
        assert r["registered_dispatch"]["status"] == "DISPATCHED_OBSERVATION_NOT_DONE"
        assert "pending" not in json.loads(Path(st).read_text(encoding="utf-8"))
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng)
        assert len(eng.calls) == 1 and r["registered_dispatch"]["status"] == "NONE_PENDING", r

        # merge_ready_for_human_review only notifies: no dispatch, no merge call
        g = fake_ok(out=checks(("build", "pass")))
        rc, r = run_resume(st, g, board, eng)
        assert kinds(r) == ["ci_recovered", "merge_ready_for_human_review"], r
        assert len(eng.calls) == 2  # only the ci_recovered actionable event
        assert all(a[2] in ("view", "checks") for a, _ in g.calls)
        rc, r = run_resume(st, fake_ok(out=checks(("build", "pass"))), board, eng)
        assert len(eng.calls) == 2

    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")
        # engine failure after checkpoint: pending persisted, replayed next run, then cleared
        eng = Engine(exc=RuntimeError("boom"))
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng)
        assert r["registered_dispatch"]["status"] == "DISPATCH_ERROR"
        assert len(json.loads(Path(st).read_text(encoding="utf-8"))["pending"]) == 1
        eng2 = Engine()
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng2)
        assert r["events"] == [] and len(eng2.calls) == 1, r
        assert "pending" not in json.loads(Path(st).read_text(encoding="utf-8"))
        # engine pre-claim rejection keeps pending, no loss
        st3 = os.path.join(d, "s3.json")
        eng3 = Engine(result={"status": "QUEUE_V2_CANONICAL_BINDING_REJECTED", "items_executed": 0})
        rc, r = run_resume(st3, fake_ok(rc=1, out=fail), board, eng3)
        assert r["registered_dispatch"]["status"] == "ENGINE_REJECTED"
        assert len(json.loads(Path(st3).read_text(encoding="utf-8"))["pending"]) == 1
        # PR closed -> stale pending dropped without dispatch
        eng4 = Engine()
        rc, r = run_resume(st3, fake_ok(view(state="CLOSED"), out=fail), board, eng4)
        assert not eng4.calls and r["registered_dispatch"]["status"] == "DROPPED_PR_NOT_OPEN"

    with tempfile.TemporaryDirectory() as d:
        st = os.path.join(d, "s.json")
        # UNKNOWN (corrupt / tampered pending / overflow / identity): no dispatch
        eng = Engine()
        Path(st).write_text("{garbage", encoding="utf-8")
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng)
        assert rc == 3 and r["reason"] == "checkpoint_corrupt" and not eng.calls
        os.remove(st)
        run_resume(st, fake_ok(rc=1, out=fail), {"tasks": []}, eng)  # HOLD -> no pending written
        cp = json.loads(Path(st).read_text(encoding="utf-8"))
        cp["pending"] = [{"event": "conflict", "snapshot_hash": "0" * 64, "key": "deadbeefdeadbeef"}]
        Path(st).write_text(json.dumps(cp), encoding="utf-8")
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng)
        assert rc == 3 and r["reason"] == "checkpoint_pending_corrupt" and not eng.calls
        cp["pending"] = [{"event": "conflict", "snapshot_hash": "0" * 64,
                          "key": watch._event_key("0" * 64, "conflict")}] * 17
        Path(st).write_text(json.dumps(cp), encoding="utf-8")
        rc, r = run_resume(st, fake_ok(rc=1, out=fail), board, eng)
        assert rc == 3 and r["reason"] == "checkpoint_pending_corrupt" and not eng.calls

    # default CLI unchanged: no registered_dispatch key, engine never touched
    with tempfile.TemporaryDirectory() as d:
        def no_engine(*a):
            raise AssertionError("engine must not be called without the flag")
        saved = watch._engine_dispatch
        watch._engine_dispatch = no_engine
        try:
            rc, r = run(os.path.join(d, "s.json"), fake_ok(rc=1, out=fail))
        finally:
            watch._engine_dispatch = saved
        assert "registered_dispatch" not in r and kinds(r) == ["ci_failure"]
    # no unrelated work-id: engine call is always for the bound work-id
    assert watch._gate_row({"tasks": [row(id="OTHER-002")]}, WID, REPO, PR)[0] is False


def _independent_review_regressions():
    """Independent Codex review: malformed identity and TOCTOU must fail closed."""
    original = json.loads(view())
    cases = [
        ({k: v for k, v in original.items() if k != "reviewDecision"}, "view_fields_missing"),
        ({**original, "reviewDecision": None}, "view_fields_invalid"),
        ({**original, "url": "https://evil.example/o/r/pull/7"}, "identity_mismatch"),
        ({**original, "url": "https://github.com.evil.example/o/r/pull/7"}, "identity_mismatch"),
        ({**original, "url": "https://github.com/o/r/pull/7-other"}, "identity_mismatch"),
        ({**original, "url": "https://github.com/o/r/pull/7?from=evil"}, "identity_mismatch"),
        ({**original, "number": True}, "identity_mismatch"),
    ]
    for altered, reason in cases:
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "s.json")
            rc, result = run(st, fake_ok(json.dumps(altered), out=checks(("build", "pass"))))
            assert rc == 3 and result["reason"] == reason and not os.path.exists(st), (altered, result)

    changing = [
        (view(review="APPROVED"), view(review="CHANGES_REQUESTED")),
        (view(draft=False), view(draft=True)),
        (view(mergeable="MERGEABLE"), view(mergeable="CONFLICTING")),
        (view(ms="CLEAN"), view(ms="DIRTY")),
    ]
    for before, after in changing:
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "s.json")
            rc, result = run(st, FakeGh([before, after], 0, checks(("build", "pass"))))
            assert rc == 3 and result["reason"] == "pr_metadata_changed_during_read", result
            assert result["events"] == [] and not os.path.exists(st)


if __name__ == "__main__":
    main()
