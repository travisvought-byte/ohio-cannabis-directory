"""The seed page's summary text must follow the data, not fixed counts."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_seeds  # noqa: E402


def record(name, area='Ohio', role='Breeder', **extra):
    base = {'name': name, 'area': area, 'role': role, 'types': ['Regular'], 'url': 'https://example.org/',
            'note': 'Test record.', 'shipping': 'Confirm directly.', 'sources': ['https://example.org/'],
            'phone': '', 'email': '', 'reviewed': '2026-11-05'}
    base.update(extra)
    return base


class SeedGeneratorTest(unittest.TestCase):
    def build(self, rows):
        original_loader, original_out = build_seeds.load_seed_records, build_seeds.OUT
        with tempfile.TemporaryDirectory() as tmp:
            build_seeds.load_seed_records = lambda: rows
            build_seeds.OUT = Path(tmp) / 'seeds.html'
            try:
                build_seeds.main()
                return build_seeds.OUT.read_text(encoding='utf-8')
            finally:
                build_seeds.load_seed_records, build_seeds.OUT = original_loader, original_out

    def test_counts_and_pickup_follow_data(self):
        page = self.build([
            record('Breeder A'),
            record('Shop B', role='Grow supplies / retailer lead'),
            record('Shop C', role='Grow supplies / retailer lead', pickup_verified=True),
            record('Bank D', area='National', role='Seed bank'),
        ])
        self.assertIn('2 seed providers and two Ohio grow-supply / retailer leads.', page)
        self.assertIn("Seed pickup has been confirmed on the seller's own page for: Shop C.", page)
        self.assertNotIn('not confirmed for any listed Ohio seller', page)
        self.assertNotIn('<option>Michigan</option>', page)

    def test_no_pickup_keeps_caution(self):
        page = self.build([record('Breeder A'), record('Shop B', role='Grow supplies / retailer lead')])
        self.assertIn('1 seed providers and one Ohio grow-supply / retailer lead.', page)
        self.assertIn('Current Ohio seed pickup is not confirmed for any listed Ohio seller.', page)

    def test_uncontrolled_area_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.build([record('Breeder A', area='Lebanon, OH')])


if __name__ == '__main__':
    unittest.main()
