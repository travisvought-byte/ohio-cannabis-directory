"""Regression tests for the state-first comparison projection."""
import copy
import json
import unittest
from pathlib import Path

from state_profiles import profiles, render_coverage


DATA = Path(__file__).resolve().parent / "data" / "state-comparison.json"


class StateProfilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_all_states_have_profiles(self):
        self.assertEqual(set(profiles(self.data)), set(self.data["states"]))

    def test_entries_are_projected_without_pairwise_data(self):
        output = profiles(self.data)
        for topic in self.data["topics"]:
            for entry in topic["entries"]:
                self.assertEqual(output[entry["state"]]["topics"][topic["id"]]["summary"], entry["summary"])
                self.assertEqual(output[entry["state"]]["topics"][topic["id"]]["source_ids"], entry["source_ids"])

    def test_duplicate_state_topic_rejected(self):
        data = copy.deepcopy(self.data)
        data["topics"][0]["entries"].append(copy.deepcopy(data["topics"][0]["entries"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate state/topic"):
            profiles(data)

    def test_unknown_state_rejected(self):
        data = copy.deepcopy(self.data)
        data["topics"][0]["entries"][0]["state"] = "XX"
        with self.assertRaisesRegex(ValueError, "Unknown state"):
            profiles(data)

    def test_coverage_is_derived(self):
        output = render_coverage(self.data)
        self.assertIn('role="progressbar"', output)
        self.assertIn('aria-valuemax="', output)
        self.assertIn("Coverage is not a policy score", output)


if __name__ == "__main__":
    unittest.main()
