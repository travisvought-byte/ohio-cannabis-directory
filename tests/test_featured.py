import json
import unittest
from pathlib import Path

import build_national as bn

ROOT = Path(__file__).resolve().parent.parent


class FeaturedGroups(unittest.TestCase):
    def test_entries_are_complete_and_accepted(self):
        perm = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))
        featured = bn.load_featured(perm['jurisdictions'])
        for groups in featured.values():
            for g in groups:
                self.assertRegex(g['accepted_on'], r'^\d{4}-\d{2}-\d{2}$')

    def test_section_renders_links_and_donate_only_when_given(self):
        g = {'name': 'Group', 'kind': 'Advocacy group', 'text': 'Does things.', 'site': 'https://example.org/', 'links': []}
        html = bn.featured_section([g], 'Kentucky')
        self.assertIn('https://example.org/', html)
        self.assertNotIn('Donate', html)
        html = bn.featured_section([{**g, 'donate': 'https://example.org/give'}], 'Kentucky')
        self.assertIn('Donate to support their work', html)
        self.assertEqual(bn.featured_section([], 'Kentucky'), '')


if __name__ == '__main__':
    unittest.main()
