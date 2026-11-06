"""Keep content routing free from the SHA suffix of preserved RAW filenames."""
import unittest
from taky_central_source_factory import domain_hint


class DomainHintTests(unittest.TestCase):
    def test_hash_suffix_does_not_masquerade_as_cad(self):
        self.assertNotEqual(
            domain_hint("DispatchSEO open source PR approval SEO workflow",
                        "README__1970bcadcc3a.md"), "ARCHITECTURE")

    def test_real_cad_remains_architecture(self):
        self.assertEqual(domain_hint("59 CAD unit plan", "floorplan.dwg"), "ARCHITECTURE")
        self.assertEqual(domain_hint("기준층 도면", "a.json"), "ARCHITECTURE")

    def test_unrelated_suffix_remains_unclassified(self):
        self.assertEqual(domain_hint("generic source", "readme__abcadef234.md"), "UNCLASSIFIED")


if __name__ == "__main__":
    unittest.main()
