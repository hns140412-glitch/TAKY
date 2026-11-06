import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from TAKY2.enforcement import stable_hash
from TAKY_MODEL_REVIEW_PACKET import make_packet


class BoundedPacketTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        (self.repo / "TOOLS").mkdir()
        (self.repo / "ENFORCEMENT").mkdir()
        (self.repo / "TOOLS" / "first.ps1").write_bytes(b"alpha\nbeta\n")
        (self.repo / "ENFORCEMENT" / "second.py").write_bytes(b"def f():\n    return 42\n")

    def test_includes_explicit_files_with_lines_sha_and_binding(self):
        request = "Review TOOLS/first.ps1 and ENFORCEMENT/second.py"
        packet, sources = make_packet(self.repo, request)
        self.assertEqual(len(sources), 2)
        self.assertIn("0001| alpha", packet)
        self.assertIn("0002| beta", packet)
        self.assertIn("def f():", packet)
        self.assertEqual(sources[0]["sha256"], hashlib.sha256(b"alpha\nbeta\n").hexdigest())
        self.assertEqual(len(stable_hash(packet)), 20)
        self.assertNotIn(str(self.repo), packet)

    def test_repeated_names_do_not_duplicate_files(self):
        packet, sources = make_packet(self.repo, "TOOLS/first.ps1 TOOLS/first.ps1")
        self.assertEqual(len(sources), 1)

    def test_three_valid_sources_fit_in_packet_without_arbitrary_count_hold(self):
        (self.repo / "TOOLS" / "third.ps1").write_text("c")
        packet, sources = make_packet(self.repo, "TOOLS/first.ps1 ENFORCEMENT/second.py TOOLS/third.ps1")
        self.assertEqual(len(sources), 3)
        self.assertEqual(sources[2]["path"], "TOOLS/third.ps1")
        self.assertIn("SOURCE_FILE TOOLS/third.ps1", packet)

    def test_three_implementation_sources_when_complete_fit_in_packet(self):
        (self.repo / "TOOLS" / "third.ps1").write_text("new code\n")
        packet, sources = make_packet(self.repo, "Update TOOLS/first.ps1 ENFORCEMENT/second.py TOOLS/third.ps1", mode="implementation")
        self.assertEqual(len(sources), 3)
        self.assertIn("as many replacements as are genuinely necessary", packet)

    def test_real_node_test_and_module_files_are_bound(self):
        (self.repo / "ENFORCEMENT" / "decision.cjs").write_text("module.exports={safe:true};\\n", encoding="utf-8")
        (self.repo / "TOOLS" / "ui.mjs").write_text("export const ready=true;\\n", encoding="utf-8")
        packet, sources = make_packet(
            self.repo, "Review ENFORCEMENT/decision.cjs and TOOLS/ui.mjs")
        self.assertEqual([s["path"] for s in sources],
                         ["ENFORCEMENT/decision.cjs", "TOOLS/ui.mjs"])
        self.assertTrue(all(s["complete"] for s in sources))
        self.assertIn("module.exports", packet)
        self.assertIn("export const ready", packet)

    def test_missing_file_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "UNAVAILABLE"):
            make_packet(self.repo, "TOOLS/not-here.ps1")

    def test_oversize_content_fails_closed(self):
        (self.repo / "TOOLS" / "first.ps1").write_bytes(b"x" * 100001)
        with self.assertRaisesRegex(ValueError, "OVERSIZE"):
            make_packet(self.repo, "TOOLS/first.ps1")

    def test_prompt_only_packet_does_not_claim_file_review(self):
        packet, sources = make_packet(self.repo, "Summarize a review packet")
        self.assertEqual(sources, [])
        self.assertIn("Do not claim that unprovided files were inspected", packet)

    def test_taky2_real_kernel_review_paths_are_explicit(self):
        (self.repo / "TAKY2").mkdir()
        (self.repo / "TAKY2" / "orchestrator.py").write_text("def route():\n    return 'gate'\n")
        packet, sources = make_packet(self.repo, "Review TAKY2/orchestrator.py")
        self.assertEqual(len(sources), 1)
        self.assertIn("def route()", packet)

    def test_live_packet_includes_actual_pinned_operating_skill_bytes(self):
        from TAKY_MODEL_REVIEW_PACKET import _pinned_operating_skills, MAX_PACKET_CHARS
        packet, sources = make_packet(self.repo, "Review TOOLS/first.ps1 with evidence.")
        skills = _pinned_operating_skills()
        self.assertEqual([x[0] for x in skills], ["authority-check", "cross-model-review"])
        self.assertEqual(len(sources), 1)
        for skill_id, sha, original in skills:
            self.assertIn(f"PINNED_TAKY_SKILL {skill_id} sha256={sha}", packet)
            self.assertIn(original, packet)
        self.assertLess(packet.index("PINNED_TAKY_SKILL"), packet.index("TASK:"))
        self.assertIn("0001| alpha", packet)
        self.assertLess(len(packet), MAX_PACKET_CHARS)

    def test_actual_implementation_route_uses_outcome_skill_not_reviewer_skill(self):
        from TAKY_MODEL_REVIEW_PACKET import _pinned_operating_skills
        packet, files = make_packet(
            self.repo, "Implement ENFORCEMENT/second.py", mode="implementation")
        required = _pinned_operating_skills("implementation")
        self.assertEqual([s[0] for s in required], ["authority-check", "outcome-quality"])
        for name, digest, body in required:
            self.assertIn(f"PINNED_TAKY_SKILL {name} sha256={digest}", packet)
            self.assertIn(body, packet)
        self.assertNotIn("PINNED_TAKY_SKILL cross-model-review", packet)
        self.assertEqual(files[0]["includedLines"], files[0]["totalLines"])

    def test_implementation_without_named_source_holds(self):
        with self.assertRaisesRegex(ValueError, "IMPLEMENTATION_SOURCE_FILES_REQUIRED"):
            make_packet(self.repo, "Implement the workflow", mode="implementation")

    def test_ready_task_includes_pinned_learning_and_mobile_skills(self):
        root = self.repo / "Ready & Set"
        (root / "TOOLS").mkdir(parents=True)
        (root / "TOOLS" / "unit.py").write_text("value = 1\n", encoding="utf-8")
        packet, files = make_packet(root, "Implement TOOLS/unit.py", mode="implementation")
        self.assertIn("PINNED_TAKY_SKILL learning-grow", packet)
        self.assertIn("PINNED_TAKY_SKILL mobile-webapp-build", packet)
        self.assertIn("PINNED_TAKY_SKILL outcome-quality", packet)
        self.assertEqual(len(files), 1)

    def test_archigrow_named_work_in_taky_selects_archi_skill(self):
        root = self.repo / "TAKY"
        (root / "TOOLS").mkdir(parents=True)
        (root / "TOOLS" / "ARCHIGROW_TASK.py").write_text("value = 2\n", encoding="utf-8")
        packet, files = make_packet(root, "Review TOOLS/ARCHIGROW_TASK.py")
        self.assertIn("PINNED_TAKY_SKILL archi-grow", packet)
        self.assertIn("PINNED_TAKY_SKILL cross-model-review", packet)
        self.assertEqual(len(files), 1)

    def test_archigrow_project_repo_includes_archi_skill(self):
        root = self.repo / "TAKY_ARCHI GROW"
        (root / "TOOLS").mkdir(parents=True)
        (root / "TOOLS" / "unit.py").write_text("value = 3\n", encoding="utf-8")
        packet, sources = make_packet(root, "Review TOOLS/unit.py")
        self.assertIn("PINNED_TAKY_SKILL archi-grow", packet)
        self.assertEqual(len(sources), 1)

    def test_archigrow_prefix_collision_does_not_activate_domain(self):
        root = self.repo / "TAKY"
        (root / "TOOLS").mkdir(parents=True)
        (root / "TOOLS" / "ArchiGrowUnrelated.py").write_text("x=1\n", encoding="utf-8")
        packet, _ = make_packet(root, "Review TOOLS/ArchiGrowUnrelated.py")
        self.assertNotIn("PINNED_TAKY_SKILL archi-grow", packet)

    def test_dot_segments_cannot_route_into_unrelated_source(self):
        root = self.repo / "TAKY"
        (root / "TOOLS" / "archigrow").mkdir(parents=True)
        (root / "TOOLS" / "unrelated.py").write_text("x=2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SOURCE_FILE_DOT_SEGMENT_NOT_ALLOWED"):
            make_packet(root, "Review TOOLS/archigrow/../unrelated.py")

    def test_domain_and_learning_sources_activate_from_verified_paths(self):
        root = self.repo / "TAKY"
        (root / "DOMAIN").mkdir(parents=True)
        (root / "LEARNING").mkdir(parents=True)
        (root / "DOMAIN" / "ARCHIGROW_LOGIC.md").write_text("architecture", encoding="utf-8")
        (root / "LEARNING" / "logic.js").write_text("const a=1;", encoding="utf-8")
        architecture, sources = make_packet(root, "Review DOMAIN/ARCHIGROW_LOGIC.md")
        self.assertIn("PINNED_TAKY_SKILL archi-grow", architecture)
        self.assertEqual(sources[0]["path"], "DOMAIN/ARCHIGROW_LOGIC.md")
        learning, sources = make_packet(root, "Review LEARNING/logic.js")
        self.assertIn("PINNED_TAKY_SKILL learning-grow", learning)
        self.assertEqual(sources[0]["path"], "LEARNING/logic.js")

    def test_unrelated_review_does_not_load_domain_skill(self):
        packet, _ = make_packet(self.repo, "Review TOOLS/first.ps1")
        self.assertNotIn("PINNED_TAKY_SKILL archi-grow", packet)
        self.assertNotIn("PINNED_TAKY_SKILL learning-grow", packet)

    def test_implementation_source_within_total_budget_is_complete(self):
        source = self.repo / "ENFORCEMENT" / "second.py"
        source.write_text("value = 100\n" * 1600, encoding="utf-8")
        packet, files = make_packet(
            self.repo, "Edit ENFORCEMENT/second.py", mode="implementation")
        self.assertEqual(files[0]["includedLines"], 1600)
        self.assertEqual(files[0]["totalLines"], 1600)
        self.assertTrue(files[0]["complete"])
        self.assertIn("1600| value = 100", packet)
        self.assertLessEqual(len(packet), 41000)
        self.assertGreater(len(packet), 18000)
        self.assertIn("PINNED_TAKY_SKILL outcome-quality", packet)

    def test_actual_495_line_writing_source_no_longer_blocked(self):
        from TAKY_MODEL_REVIEW_PACKET import TAKY_ROOT, MAX_SOURCE_CHARS, MAX_PACKET_CHARS
        source = TAKY_ROOT / "TOOLS" / "TAKY_WRITING_FLOW.py"
        self.assertTrue(source.is_file())
        packet, files = make_packet(
            TAKY_ROOT, "Implement TOOLS/TAKY_WRITING_FLOW.py", mode="implementation")
        self.assertEqual(files[0]["includedLines"], files[0]["totalLines"])
        framed = "".join(f"{i:04d}| {line}\n"
                         for i, line in enumerate(source.read_text(encoding="utf-8-sig").splitlines(), 1))
        self.assertGreater(len(framed), MAX_SOURCE_CHARS)
        self.assertIn(framed, packet)
        self.assertLessEqual(len(packet), MAX_PACKET_CHARS)
        self.assertIn(f'included_lines={files[0]["totalLines"]}/{files[0]["totalLines"]}', packet)
        self.assertIn("PINNED_TAKY_SKILL authority-check", packet)
        self.assertIn("PINNED_TAKY_SKILL outcome-quality", packet)

    def test_oversized_implementation_source_holds_without_truncation(self):
        source = self.repo / "ENFORCEMENT" / "second.py"
        source.write_text("value = 100\n" * 3500, encoding="utf-8")
        packet, sources = make_packet(
            self.repo, "Review ENFORCEMENT/second.py", mode="review")
        self.assertLess(sources[0]["includedLines"], sources[0]["totalLines"])
        self.assertIn("SOURCE_FILE ENFORCEMENT/second.py", packet)
        with self.assertRaisesRegex(
                ValueError, "IMPLEMENTATION_COMPLETE_SOURCE_EXCEEDS_PACKET_BUDGET"):
            make_packet(self.repo, "Edit ENFORCEMENT/second.py", mode="implementation")

    def test_signed_skill_manifest_reconstructs_exact_stdin_markers(self):
        from TAKY_MODEL_REVIEW_PACKET import packet_skill_manifest
        packet, _ = make_packet(self.repo, "Review TOOLS/first.ps1")
        skills = packet_skill_manifest(packet)
        self.assertEqual([s["name"] for s in skills],
                         ["authority-check", "cross-model-review"])
        for item in skills:
            self.assertIn(
                f'PINNED_TAKY_SKILL {item["name"]} sha256={item["sha256"]}',
                packet)
        packet2, _ = make_packet(self.repo, "Edit TOOLS/first.ps1", mode="implementation")
        self.assertEqual([s["name"] for s in packet_skill_manifest(packet2)],
                         ["authority-check", "outcome-quality"])
        with self.assertRaisesRegex(ValueError, "PACKET_SKILL_MANIFEST_INVALID"):
            packet_skill_manifest("No signed skills")

    def test_unrecognized_mode_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_TASK_SKILL_MODE"):
            make_packet(self.repo, "Review TOOLS/first.ps1", mode="extra")

    def test_tampered_canonical_skill_fails_before_packet_creation(self):
        root = self.repo / "fake-taky"
        skills = root / ".claude" / "skills"
        manifest = root / "TAKY2_MANIFEST.json"
        pins = {}
        for skill in ("authority-check", "cross-model-review"):
            target = skills / skill / "SKILL.md"
            target.parent.mkdir(parents=True)
            body = ("approved " + skill).encode("utf-8")
            target.write_bytes(body)
            pins[skill] = hashlib.sha256(body).hexdigest()
        manifest.write_text(json.dumps({
            "schema": "TAKY2_SKILL_LINK_MANIFEST_V1",
            "source_repo": "TAKY", "skills": pins,
        }), encoding="utf-8")
        (skills / "authority-check" / "SKILL.md").write_text("TAMPERED", encoding="utf-8")
        with patch("TAKY_MODEL_REVIEW_PACKET.TAKY_ROOT", root), patch(
                "TAKY_MODEL_REVIEW_PACKET.SKILL_MANIFEST", manifest):
            with self.assertRaisesRegex(ValueError, "REQUIRED_SKILL_HASH_DRIFT"):
                make_packet(self.repo, "Review TOOLS/first.ps1")

    def test_packet_is_labelled_limited_not_independent(self):
        packet, sources = make_packet(self.repo, "Review TOOLS/first.ps1")
        self.assertIn("EVIDENCE_CLASS: LIMITED (NOT INDEPENDENT)", packet)
        self.assertIn("not an independent review of the original sources", packet)
        self.assertEqual(sources[0]["evidenceClass"], "LIMITED")
        self.assertTrue(sources[0]["complete"])
        self.assertIs(sources[0]["independentReview"], False)

    def test_no_sources_forbids_original_source_claim(self):
        packet, sources = make_packet(self.repo, "Is this plan sound?")
        self.assertEqual(sources, [])
        self.assertIn("NO_ORIGINAL_SOURCE_ATTACHED", packet)
        self.assertIn("do not claim original-source review", packet)
        self.assertNotIn("complete bounded snippets", packet)

    def test_truncated_excerpt_is_flagged_and_not_complete(self):
        (self.repo / "ENFORCEMENT" / "second.py").write_text("value = 100\n" * 2300, encoding="utf-8")
        packet, sources = make_packet(self.repo, "Review ENFORCEMENT/second.py")
        self.assertFalse(sources[0]["complete"])
        self.assertIs(sources[0]["independentReview"], False)
        self.assertIn("TRUNCATED_EXCERPTS: ENFORCEMENT/second.py", packet)
        self.assertNotIn("complete bounded snippets", packet)

    def test_long_prompt_fails_closed(self):
        with self.assertRaises(ValueError):
            make_packet(self.repo, "x" * 2501)


if __name__ == "__main__":
    unittest.main()
