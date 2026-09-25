#!/usr/bin/env python3
import unittest
from pathlib import Path

import runtime_orchestrator as ro


class ContextFirewallTest(unittest.TestCase):
    def test_runtime_contains_firewall_guards(self):
        source = Path(ro.__file__).read_text(encoding="utf-8")
        self.assertIn("CONTEXT_FIREWALL_ISOLATION_REQUIRED", source)
        self.assertIn("CONTEXT_FIREWALL_ALLOWED_REFS_INVALID", source)
        self.assertIn("CONTEXT_FIREWALL_RETURN_CONTRACT_INVALID", source)
        self.assertIn("CONTEXT_FIREWALL_FORBIDDEN_BULK_CONTEXT", source)
        self.assertIn('"context_firewall": context_firewall_result', source)

    def test_forbidden_bulk_context_keys_are_explicit(self):
        source = Path(ro.__file__).read_text(encoding="utf-8")
        for key in [
            "full_conversation",
            "full_chat_history",
            "entire_history",
            "parent_runtime_state",
            "all_rules",
        ]:
            self.assertIn(key, source)


if __name__ == "__main__":
    unittest.main()
