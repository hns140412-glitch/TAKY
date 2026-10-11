#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

from ai_connection_trust_validator import validate

ROOT = Path(__file__).resolve().parents[1]


def load():
    manifest = json.loads((ROOT/"OS"/"AI_CONNECTION_TRUST_MANIFEST.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT/"OS"/"AI_CONNECTION_AUDIT.json").read_text(encoding="utf-8"))
    return manifest, audit


class AIConnectionTrustValidatorTest(unittest.TestCase):
    def test_current_manifest_passes(self):
        m, a = load()
        result = validate(m, a)
        self.assertTrue(result["pass"], result)

    def test_missing_connection_fails(self):
        m, a = load()
        m["connections"] = m["connections"][:-1]
        result = validate(m, a)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("TRUST_PROJECTION_MISSING_CONNECTION:") for x in result["detected"]))

    def test_token_passthrough_true_fails(self):
        m, a = load()
        m["connections"][0]["token_passthrough"] = True
        result = validate(m, a)
        self.assertIn("TOKEN_PASSTHROUGH_FORBIDDEN:playwright-mcp", result["detected"])

    def test_remote_unknown_identity_cannot_be_trusted_bounded(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "netlify-mcp")
        item["trust_state"] = "TRUSTED_BOUNDED"
        result = validate(m, a)
        self.assertIn("REMOTE_TRUST_OVERCLAIM:netlify-mcp", result["detected"])

    def test_sse_remote_unknown_identity_cannot_be_trusted_bounded(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "netlify-mcp")
        item["transport"] = "sse"
        item["trust_state"] = "TRUSTED_BOUNDED"
        # Keep audit aligned on transport so this assertion proves remote overclaim,
        # not merely inventory drift.
        next(x for x in a["connections"] if x["id"] == "netlify-mcp")["transport"] = "sse"
        result = validate(m, a)
        self.assertIn("REMOTE_TRUST_OVERCLAIM:netlify-mcp", result["detected"])

    def test_metered_requires_explicit_approval(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "scenario-mcp")
        item["approval_class"] = "APPROVAL_NOT_REQUIRED"
        result = validate(m, a)
        self.assertIn("METERED_COST_APPROVAL_MISSING:scenario-mcp", result["detected"])
        self.assertIn("TRUST_PROJECTION_APPROVAL_DOWNGRADE:scenario-mcp", result["detected"])

    def test_inventory_semantic_downgrade_fails(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "scenario-mcp")
        item["cost_class"] = "COST_INCLUDED_OR_LOCAL"
        item["action_scope"] = "READ"
        item["approval_class"] = "APPROVAL_NOT_REQUIRED"
        result = validate(m, a)
        self.assertIn(
            "TRUST_PROJECTION_SEMANTIC_DRIFT:scenario-mcp:cost_class",
            result["detected"],
        )
        self.assertIn(
            "TRUST_PROJECTION_SEMANTIC_DRIFT:scenario-mcp:action_scope",
            result["detected"],
        )
        self.assertIn("TRUST_PROJECTION_APPROVAL_DOWNGRADE:scenario-mcp", result["detected"])

    def test_pinned_remote_without_version_or_credentials_still_cannot_be_trusted(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "netlify-mcp")
        item["version_verification_state"] = "PINNED_CONFIG"
        item["auth_method"] = "oauth"
        item["trust_state"] = "TRUSTED_BOUNDED"
        result = validate(m, a)
        self.assertIn("REMOTE_TRUST_OVERCLAIM:netlify-mcp", result["detected"])

    def test_literal_unknown_auth_cannot_be_trusted(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "netlify-mcp")
        source = next(x for x in a["connections"] if x["id"] == "netlify-mcp")
        item["version"] = "1.0.0"
        item["version_verification_state"] = "PINNED_CONFIG"
        item["auth_method"] = "UNKNOWN"
        item["credential_binding"] = "HOST_MANAGED"
        item["token_passthrough"] = False
        item["source_trust"] = "SOURCE_AUTHENTICATED_EXTERNAL"
        item["trust_state"] = "TRUSTED_BOUNDED"
        source["version"] = "1.0.0"
        source["auth_method"] = "UNKNOWN"
        source["source_trust"] = "SOURCE_AUTHENTICATED_EXTERNAL"
        result = validate(m, a)
        self.assertIn("REMOTE_TRUST_OVERCLAIM:netlify-mcp", result["detected"])

    def test_literal_unknown_source_trust_cannot_be_trusted(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "netlify-mcp")
        source = next(x for x in a["connections"] if x["id"] == "netlify-mcp")
        item["version"] = "1.0.0"
        item["version_verification_state"] = "PINNED_CONFIG"
        item["auth_method"] = "oauth"
        item["credential_binding"] = "HOST_MANAGED"
        item["token_passthrough"] = False
        item["source_trust"] = "UNKNOWN"
        item["trust_state"] = "TRUSTED_BOUNDED"
        source["version"] = "1.0.0"
        source["auth_method"] = "oauth"
        source["source_trust"] = "UNKNOWN"
        result = validate(m, a)
        self.assertIn("REMOTE_TRUST_OVERCLAIM:netlify-mcp", result["detected"])

    def test_approval_class_must_cover_cost_and_write_semantics(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "scenario-mcp")
        item["approval_class"] = "HIGH_IMPACT_REQUIRES_EXPLICIT_APPROVAL"
        result = validate(m, a)
        self.assertIn("METERED_COST_APPROVAL_MISSING:scenario-mcp", result["detected"])
        self.assertIn("TRUST_PROJECTION_APPROVAL_DOWNGRADE:scenario-mcp", result["detected"])

    def test_fabricated_approval_class_is_rejected(self):
        m, a = load()
        item = next(x for x in m["connections"] if x["server_id"] == "scenario-mcp")
        item["approval_class"] = "NOT_REQUIRES_EXPLICIT_APPROVAL"
        result = validate(m, a)
        self.assertIn("APPROVAL_CLASS_INVALID:scenario-mcp", result["detected"])


if __name__ == "__main__":
    unittest.main()
