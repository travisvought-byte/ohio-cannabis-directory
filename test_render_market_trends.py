"""Tests for sourced, state-first market trend rendering."""
import unittest
from render_market_trends import render_market_trends


class TrendTests(unittest.TestCase):
    def row(self, year, value, scope="medical"):
        return {"state": "PA", "metric": "operational_retail_locations", "scope": scope,
                "unit": "count", "period": "day", "period_start": f"{year}-03-01",
                "period_end": f"{year}-03-01", "value": value,
                "definition": "Operational locations", "source_ids": ["pa-source"]}

    def test_sourced_trend(self):
        html = render_market_trends([self.row(2024, 180), self.row(2026, 192)],
                                    {"PA": "Pennsylvania"}, lambda sid: f'<a href="#{sid}">source</a>')
        self.assertIn("2024-03-01", html)
        self.assertIn("2026-03-01", html)
        self.assertIn("192", html)
        self.assertIn('href="#pa-source"', html)

    def test_single_observation_does_not_imply_trend(self):
        html = render_market_trends([self.row(2026, 192)],
                                    {"PA": "Pennsylvania"}, lambda sid: sid)
        self.assertIn("More source-verified observations", html)

    def test_different_market_scopes_not_combined(self):
        html = render_market_trends([self.row(2024, 180), self.row(2026, 192, "adult_use")],
                                    {"PA": "Pennsylvania"}, lambda sid: sid)
        self.assertIn("More source-verified observations", html)


if __name__ == "__main__":
    unittest.main()
