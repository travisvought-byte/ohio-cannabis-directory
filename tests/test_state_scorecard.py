"""Published coverage labels must match what the completion standard measures."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_state_scorecard  # noqa: E402


class StateScorecardTest(unittest.TestCase):
    def setUp(self):
        self.result, self.json_text, self.md_text = build_state_scorecard.build()

    def test_declared_labels_match_earned_levels(self):
        mismatches = [(code, p, v['declared'], v['level']) for code, st in self.result['states'].items()
                      for p, v in st['pathways'].items() if v['declared'] != v['level']]
        self.assertEqual(mismatches, [], 'Update the state pack coverage_status or the data; run python build_state_scorecard.py')

    def test_generated_scorecard_is_current(self):
        self.assertEqual((ROOT / 'data/state-scorecard.json').read_text(), self.json_text)
        self.assertEqual((ROOT / 'architecture/STATE_SCORECARD.md').read_text(), self.md_text)

    def test_every_published_state_is_measured(self):
        self.assertEqual(set(self.result['states']), {'OH', 'PA', 'NY'})
        for st in self.result['states'].values():
            self.assertEqual(set(st['pathways']), set(build_state_scorecard.PATHWAYS))


if __name__ == '__main__':
    unittest.main()
