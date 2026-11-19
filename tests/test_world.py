"""The world section shows every reviewed answer with its source and date, and adds no claim of its own."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build_national  # noqa: E402
import build_world  # noqa: E402

WORLD = json.loads((ROOT / 'data/world-permissions.json').read_text(encoding='utf-8'))
PERM = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))
PAGES = build_national.pages()
SOURCE_IDS = {s['id'] for s in WORLD['sources']}


class WorldTest(unittest.TestCase):
    def test_every_cited_source_exists_and_has_a_date(self):
        used = set()
        for c in WORLD['countries'].values():
            for a in c['answers'].values():
                used |= set(a['source_ids'])
                self.assertTrue(a['source_ids'] and a['reviewed_on'] and a['citation'])
                self.assertIn(a['status'], WORLD['statuses'])
        for p in WORLD['canada_provinces']:
            used |= set(p['age_source_ids']) | set(p['home_grow_source_ids'])
            self.assertEqual(bool(p['age']), bool(p['age_source_ids']), p['name'])
            self.assertEqual(bool(p['home_grow']), bool(p['home_grow_source_ids']), p['name'])
        for w in WORLD['travel_warnings']:
            used |= set(w['source_ids'])
            self.assertTrue(w['source_ids'], w['place'])
        used |= set(WORLD['texas_concentrates']['source_ids'])
        self.assertLessEqual(used, SOURCE_IDS)
        self.assertEqual(used, SOURCE_IDS, 'every listed source is cited somewhere')
        for s in WORLD['sources']:
            self.assertIn(s['kind'], build_national.KIND_LABEL)
            self.assertTrue(s['url'].startswith('https://'))
            self.assertTrue(s['retrieved_on'])

    def test_every_answer_is_on_its_country_page(self):
        for c in WORLD['countries'].values():
            text = PAGES[c['page']]
            for a in c['answers'].values():
                self.assertIn(build_national.esc(a['short']), text)
                self.assertIn(build_national.esc(a['detail']), text)
            self.assertIn(f'href="{c["page"]}"', PAGES['world.html'])

    def test_travel_warnings_list_each_country_and_every_state_without_adult_use(self):
        text = PAGES['travel-warnings.html']
        for w in WORLD['travel_warnings']:
            self.assertIn(build_national.esc(w['place']), text)
        no_adult = {a['state'] for a in PERM['answers'] if a['question'] == 'adult-use' and a['status'] in ('not-permitted', 'medical-only')}
        for code in no_adult:
            self.assertIn(f'href="{build_national.slug(PERM["jurisdictions"][code])}.html"', text)
        self.assertEqual(len(re.findall(r'<li><span class="state">', text)), len(no_adult))

    def test_world_is_in_the_menu_of_every_page(self):
        for name, text in PAGES.items():
            self.assertIn('href="world.html"', text, name)


if __name__ == '__main__':
    unittest.main()
