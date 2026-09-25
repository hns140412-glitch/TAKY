#!/usr/bin/env python3
import unittest

from current_reconciler import reconcile


def candidate(
    file_id,
    *,
    schema="TAKY_DATA_UTILIZATION_INDEX_V18",
    semantic_role="UTILIZATION_CURRENT",
    assessed=573,
    review_required=93,
    through="CAP-104",
    continue_from="CAP-105",
    modified="2026-09-24T00:00:00Z",
):
    return {
        "file_id": file_id,
        "schema": schema,
        "semantic_role": semantic_role,
        "state_fingerprint": {
            "assessed_count": assessed,
            "review_required_count": review_required,
            "reviewed_through": through,
            "continue_from": continue_from,
        },
        "modified_time": modified,
    }


class CurrentReconcilerTest(unittest.TestCase):
    def test_v17_later_progress_wins(self):
        old = candidate(
            "A",
            schema="TAKY_DATA_UTILIZATION_INDEX_V17",
            assessed=556,
            review_required=110,
            through="CAP-096",
            continue_from="CAP-097",
        )
        new = candidate(
            "B",
            schema="TAKY_DATA_UTILIZATION_INDEX_V17",
            assessed=557,
            review_required=109,
            through="CAP-097",
            continue_from="CAP-098",
        )
        result = reconcile([old, new])
        self.assertEqual(result["status"], "SELECTED")
        self.assertEqual(result["selected"]["file_id"], "B")
        self.assertEqual(result["reason"], "STATE_PROGRESSION_DOMINANCE")

    def test_same_state_duplicates_collapse_deterministically(self):
        older = candidate("A", modified="2026-09-24T01:00:00Z")
        newer = candidate("B", modified="2026-09-24T02:00:00Z")
        result = reconcile([older, newer])
        self.assertEqual(result["selected"]["file_id"], "B")
        self.assertEqual(result["reason"], "DUPLICATE_COLLAPSE_METADATA_TIEBREAK")
        self.assertEqual([item["file_id"] for item in result["duplicates"]], ["A"])

    def test_explicit_pointer_wins_same_state_even_if_older_metadata(self):
        pointed = candidate("A", modified="2026-09-24T01:00:00Z")
        newer_metadata = candidate("B", modified="2026-09-24T02:00:00Z")
        result = reconcile([pointed, newer_metadata], explicit_current_pointer="A")
        self.assertEqual(result["selected"]["file_id"], "A")
        self.assertEqual(result["reason"], "EXPLICIT_VERIFIED_POINTER")

    def test_verified_progress_can_supersede_stale_pointer(self):
        stale = candidate(
            "A",
            assessed=556,
            review_required=110,
            through="CAP-096",
            continue_from="CAP-097",
        )
        progressed = candidate(
            "B",
            assessed=557,
            review_required=109,
            through="CAP-097",
            continue_from="CAP-098",
        )
        result = reconcile([stale, progressed], explicit_current_pointer="A")
        self.assertEqual(result["selected"]["file_id"], "B")
        self.assertEqual(result["reason"], "STATE_PROGRESSION_DOMINANCE")

    def test_semantic_identity_conflict_holds(self):
        utilization = candidate("A")
        other = candidate("B", semantic_role="OTHER_CURRENT")
        result = reconcile([utilization, other])
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"], "SEMANTIC_IDENTITY_CONFLICT")

    def test_missing_explicit_pointer_holds(self):
        result = reconcile([candidate("A")], explicit_current_pointer="MISSING")
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["reason"], "EXPLICIT_POINTER_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
