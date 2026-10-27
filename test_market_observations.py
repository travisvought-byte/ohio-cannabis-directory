"""Tests for comparable, sourced state market observations."""
import copy
import json
import unittest
from pathlib import Path

from market_observations import validate_market, comparable

ROOT = Path(__file__).resolve().parent


class MarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/state-comparison.json").read_text(encoding="utf-8"))

    def sample(self):
        return {"state": "OH", "metric": "licensed_retailers", "unit": "count",
                "scope": "adult_use", "period": "month", "period_start": "2026-09-01",
                "period_end": "2026-09-30", "value": 100,
                "source_ids": ["oh-dcc-by-the-numbers"],
                "definition": "Example test fixture only, not a reported market statistic."}

    def test_empty_is_valid_missing_data(self):
        self.assertEqual(validate_market(self.data, []), 0)

    def test_valid_observation(self):
        self.assertEqual(validate_market(self.data, [self.sample()]), 1)

    def test_rejects_missing_source(self):
        row = self.sample()
        row["source_ids"] = []
        with self.assertRaises(AssertionError):
            validate_market(self.data, [row])

    def test_rejects_mismatched_unit(self):
        row = self.sample()
        row["unit"] = "USD"
        with self.assertRaises(AssertionError):
            validate_market(self.data, [row])

    def test_rejects_duplicates(self):
        row = self.sample()
        with self.assertRaises(AssertionError):
            validate_market(self.data, [row, copy.deepcopy(row)])

    def test_does_not_mix_periods_or_scopes(self):
        a = self.sample()
        b = dict(a, state="MI", scope="medical")
        c = dict(a, state="OR", period_start="2026-08-01", period_end="2026-08-31")
        result = comparable([a, b, c], "licensed_retailers", "adult_use", "2026-09-01", "2026-09-30")
        self.assertEqual(result, {"OH": 100})


if __name__ == "__main__":
    unittest.main()
