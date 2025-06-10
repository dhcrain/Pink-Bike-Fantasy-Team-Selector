import unittest
from merge_uci_results import fuzzy_match_name, normalize_name

class TestFuzzyMatchName(unittest.TestCase):
    def test_exact_match(self):
        candidates = [normalize_name(n) for n in ["Richie Rude", "Loic Bruni", "Amaury Pierron"]]
        self.assertEqual(fuzzy_match_name(normalize_name("Richie Rude"), candidates), normalize_name("Richie Rude"))

    def test_fuzzy_match(self):
        candidates = [normalize_name(n) for n in ["Richie Rude", "Loic Bruni", "Amaury Pierron"]]
        self.assertEqual(fuzzy_match_name(normalize_name("Richard Rude Jr"), candidates, threshold=0.6), normalize_name("Richie Rude"))

    def test_no_match(self):
        candidates = [normalize_name(n) for n in ["Loic Bruni", "Amaury Pierron"]]
        self.assertIsNone(fuzzy_match_name(normalize_name("Richie Rude"), candidates))

if __name__ == "__main__":
    unittest.main()
