"""Dispensary lists (data/medical-dispensaries.json) are regulator-sourced and rendered in full."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build_national  # noqa: E402

DATA = json.loads((ROOT / 'data/medical-dispensaries.json').read_text(encoding='utf-8'))
PERM = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))


class MedicalDispensaries(unittest.TestCase):
    def test_each_list_names_a_regulator_source_and_complete_rows(self):
        seen = set()
        for entry in DATA['states']:
            self.assertIn(entry['state'], PERM['jurisdictions'])
            self.assertNotIn(entry['state'], seen)
            seen.add(entry['state'])
            src = entry['source']
            self.assertEqual(src['kind'], 'regulator')
            self.assertTrue(src['url'].startswith('https://'))
            self.assertRegex(src['retrieved_on'], r'^\d{4}-\d{2}-\d{2}$')
            self.assertTrue(entry['locations'])
            for loc in entry['locations']:
                self.assertTrue(loc['name'].strip() and loc['address'].strip(), loc)
                self.assertFalse(set(loc) - {'name', 'licensee', 'address', 'phone', 'county', 'website', 'opened'}, loc)

    def test_state_pages_show_every_location(self):
        pages = build_national.pages()
        for entry in DATA['states']:
            page = pages[build_national.slug(PERM['jurisdictions'][entry['state']]) + '.html']
            self.assertEqual(page.count('<li><strong>'), len(entry['locations']))
            for loc in entry['locations']:
                self.assertIn(build_national.esc(loc['address']), page)
            self.assertIn(build_national.esc(entry['source']['url']), page)


if __name__ == '__main__':
    unittest.main()
