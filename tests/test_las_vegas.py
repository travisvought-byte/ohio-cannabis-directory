"""The Las Vegas visitor page (national/las-vegas.html): every point cites an official source with a checked date,
the FAQ data matches the questions shown, and the Nevada page, the home page and the MJBizCon card link to it."""
import json
import re
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_national  # noqa: E402
import las_vegas  # noqa: E402

DATA = json.loads((ROOT / 'data/las-vegas.json').read_text(encoding='utf-8'))
DIRECTORY = json.loads((ROOT / 'data/directory.json').read_text(encoding='utf-8'))
LANDING = build_national.load_landing()['national_pages'][las_vegas.NAME]


def build(origin='', today=None):
    previous = build_national.ORIGIN
    build_national.ORIGIN = origin
    try:
        return las_vegas.page(build_national, LANDING, DIRECTORY, today=today)
    finally:
        build_national.ORIGIN = previous


class LasVegasPage(unittest.TestCase):
    def test_every_point_cites_a_listed_primary_source_with_a_date(self):
        ids = {s['id'] for s in DATA['sources']}
        used = set()
        for s in DATA['sections']:
            self.assertTrue(s['points'], s['id'])
            for p in s['points'] + s.get('places', []):
                self.assertTrue(p['source_ids'], f'{s["id"]}: a point without a source')
                used.update(p['source_ids'])
        used.update(DATA['mix']['source_ids'])
        self.assertEqual(used - ids, set(), 'cited but not listed')
        self.assertEqual(ids - used, set(), 'listed but never cited')
        for src in DATA['sources']:
            self.assertTrue(src['url'].startswith('https://'), src['id'])
            self.assertEqual(src['kind'], 'primary', src['id'])
            self.assertLessEqual(date.fromisoformat(src['checked']), date.today(), src['id'])

    def test_sources_are_numbered_and_shown_with_their_checked_date(self):
        page = build()
        for n in set(re.findall(r'href="#lvsource-(\d+)"', page)):
            self.assertIn(f'id="lvsource-{n}"', page)
        for src in DATA['sources']:
            self.assertIn(build_national.esc(src['url']), page)
            self.assertIn('checked ' + build_national.long_date(src['checked']), page)

    def test_faq_data_matches_the_questions_on_the_page(self):
        page = build('https://the-reefer.com')
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1).replace('<\\/', '</'))
        faq = next(n for n in ld['@graph'] if n['@type'] == 'FAQPage')
        crumbs = next(n for n in ld['@graph'] if n['@type'] == 'BreadcrumbList')
        self.assertEqual([q['name'] for q in faq['mainEntity']], [s['question'] for s in DATA['sections']])
        for q, s in zip(faq['mainEntity'], DATA['sections']):
            self.assertIn(build_national.esc(s['question']), page)
            self.assertTrue(q['acceptedAnswer']['text'].startswith(s['short']))
            for p in s['points']:
                self.assertIn(p['text'], q['acceptedAnswer']['text'])
                self.assertIn(build_national.esc(p['text']), page)
        self.assertEqual([i['name'] for i in crumbs['itemListElement']], ['Home', 'Nevada', 'Visiting Las Vegas'])
        self.assertIn('<link rel="canonical" href="https://the-reefer.com/las-vegas.html">', page)

    def test_adults_notice_and_visit_counter(self):
        page = build()
        self.assertIn('For adults 21 and older', page)
        self.assertIn('assets/analytics.js', page)

    def test_mjbizcon_box_only_until_the_show_ends(self):
        event = next(e for e in DIRECTORY['events'] if e['id'] == build_national.MJBIZCON_EVENT_ID)
        end = date.fromisoformat(event['ends_on'])
        during = build(today=end)
        self.assertIn('id="mjbizcon-week"', during)
        self.assertIn('href="../pillage/contest.html"', during)
        self.assertNotIn('id="mjbizcon-week"', build(today=date.fromordinal(end.toordinal() + 1)))

    def test_linked_from_nevada_home_and_mjbizcon_card(self):
        pages = build_national.pages()
        self.assertIn(las_vegas.NAME, pages)
        self.assertIn(f'href="{las_vegas.NAME}"', pages['nevada.html'])
        self.assertIn(f'href="{las_vegas.NAME}"', pages['index.html'])
        event = next(e for e in DIRECTORY['events'] if e['id'] == build_national.MJBIZCON_EVENT_ID)
        card = build_national.mjbizcon_card(DIRECTORY, today=date.fromisoformat(event['starts_on']))
        self.assertIn(f'href="{las_vegas.NAME}"', card)

    def test_no_business_named_beyond_the_regulators_list(self):
        # Only the lounge point names businesses, and it cites the Cannabis Compliance Board's licensee list.
        for s in DATA['sections']:
            for p in s['points']:
                if 'DAZED!' in p['text'] or 'SOCIETY' in p['text']:
                    self.assertEqual(p['source_ids'], ['ccb-licensees'])
        self.assertNotRegex(build(), r'\(\d{3}\) ?\d{3}-\d{4}', 'no business phone numbers')


if __name__ == '__main__':
    unittest.main()
