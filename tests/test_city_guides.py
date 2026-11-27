"""The Denver, Chicago and New York City visitor guides (city_guides.py): every point cites a listed primary source
with a checked date, the FAQ data matches the questions shown, yes/no answers are shown in words as well as symbols,
no business or phone number is named, and each state page and the home page link the guide."""
import json
import re
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_national  # noqa: E402
import city_guides  # noqa: E402

LANDING = build_national.load_landing()['national_pages']
STATE_PAGE = {'denver.html': 'colorado.html', 'chicago.html': 'illinois.html', 'new-york-city.html': 'new-york.html'}
CHECKED = '2026-11-27'


def build(name, origin=''):
    previous = build_national.ORIGIN
    build_national.ORIGIN = origin
    try:
        return city_guides.page(build_national, name, LANDING[name])
    finally:
        build_national.ORIGIN = previous


class CityGuides(unittest.TestCase):
    def test_the_three_guides_are_registered(self):
        self.assertEqual(list(city_guides.GUIDES), ['denver.html', 'chicago.html', 'new-york-city.html'])
        for name in city_guides.GUIDES:
            self.assertIn(name, LANDING, f'{name}: no opening line in data/landing-pages.json')
            self.assertEqual(city_guides.load(name)['page']['state_page'], STATE_PAGE[name])

    def test_every_point_cites_a_listed_primary_source_checked_today(self):
        for name in city_guides.GUIDES:
            d = city_guides.load(name)
            ids = [s['id'] for s in d['sources']]
            self.assertEqual(len(ids), len(set(ids)), f'{name}: a source is listed twice')
            used = set()
            for s in d['sections']:
                self.assertTrue(s['points'], f'{name}: {s["id"]}')
                for p in s['points'] + s.get('places', []):
                    self.assertTrue(p['source_ids'], f'{name} {s["id"]}: a point without a source')
                    used.update(p['source_ids'])
            self.assertEqual(used - set(ids), set(), f'{name}: cited but not listed')
            self.assertEqual(set(ids) - used, set(), f'{name}: listed but never cited')
            for src in d['sources']:
                self.assertTrue(src['url'].startswith('https://'), src['id'])
                self.assertEqual(src['kind'], 'primary', src['id'])
                self.assertEqual(src['checked'], CHECKED, f'{name}: {src["id"]}')
                self.assertLessEqual(date.fromisoformat(src['checked']), date.today(), src['id'])
            # A blocked or partial retrieval is recorded as an attempt, never as a source.
            for a in d.get('attempts', []):
                self.assertNotIn(a['url'], {s['url'] for s in d['sources']}, f'{name}: {a["url"]}')

    def test_sources_are_numbered_and_shown_with_their_checked_date(self):
        for name in city_guides.GUIDES:
            d, page = city_guides.load(name), build(name)
            prefix = d['page']['prefix']
            for n in set(re.findall(rf'href="#{prefix}source-(\d+)"', page)):
                self.assertIn(f'id="{prefix}source-{n}"', page)
            for src in d['sources']:
                self.assertIn(build_national.esc(src['url']), page)
            self.assertEqual(page.count('checked November 27, 2026'), len(d['sources']), name)

    def test_faq_data_breadcrumbs_and_canonical(self):
        for name in city_guides.GUIDES:
            d, page = city_guides.load(name), build(name, 'https://the-reefer.com')
            ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1).replace('<\\/', '</'))
            faq = next(n for n in ld['@graph'] if n['@type'] == 'FAQPage')
            crumbs = next(n for n in ld['@graph'] if n['@type'] == 'BreadcrumbList')
            self.assertEqual([q['name'] for q in faq['mainEntity']], [s['question'] for s in d['sections']])
            for q, s in zip(faq['mainEntity'], d['sections']):
                self.assertIn(build_national.esc(s['question']), page)
                self.assertTrue(q['acceptedAnswer']['text'].startswith(s['short']))
                for p in s['points']:
                    self.assertIn(p['text'], q['acceptedAnswer']['text'])
                    self.assertIn(build_national.esc(p['text']), page)
            self.assertEqual([i['name'] for i in crumbs['itemListElement']], ['Home', d['page']['state_name'], d['page']['crumb']])
            self.assertIn(f'<link rel="canonical" href="https://the-reefer.com/{name}">', page)

    def test_accessible_structure(self):
        for name in city_guides.GUIDES:
            d, page = city_guides.load(name), build(name)
            self.assertEqual(page.count('<h1'), 1, name)
            self.assertIn('For adults 21 and older', page)
            self.assertIn('assets/analytics.js', page)
            for s in d['sections']:
                self.assertIn(f'<h2 id="{s["id"]}-h">', page)
            self.assertIn('<th scope="col">Place</th><th scope="col">Allowed?</th>', page)
            for s in d['sections']:
                for r in s.get('places', []):
                    self.assertIn(r['answer'], city_guides.MARK)
                    self.assertTrue(r['label'].strip(), f'{name}: a yes/no answer without words')
                    self.assertTrue(r['label'].startswith(('Yes', 'No', 'Only', 'In most')), f'{name}: {r["label"]}')
            # Every icon is decorative and sits next to text that says the same thing.
            self.assertNotRegex(page, r'<svg(?![^>]*aria-hidden="true")[^>]*viewBox="0 0 24 24"')
            for label in re.findall(r'<a href="[^"]+"[^>]*>([^<]*)</a>', page):
                self.assertNotIn(label.strip().lower(), {'here', 'click here', 'link', 'more'}, name)

    def test_no_business_phone_number_or_price(self):
        for name in city_guides.GUIDES:
            page = build(name)
            self.assertNotRegex(page, r'\(\d{3}\) ?\d{3}-\d{4}', f'{name}: a business phone number')
            text = json.dumps(city_guides.load(name)['sections'])
            self.assertNotRegex(text, r'\$\d+(?:\.\d\d)? (?:an?|per) (?:gram|eighth|ounce)', f'{name}: a price')

    def test_new_york_city_links_the_ocm_verification_page(self):
        page = build('new-york-city.html')
        self.assertIn('href="https://cannabis.ny.gov/dispensary-location-verification">Check a store on the state’s list of licensed dispensaries</a>', page)
        self.assertIn('only from a dispensary licensed by New York State’s Office of Cannabis Management', page)

    def test_linked_from_state_pages_and_home_after_las_vegas(self):
        pages = build_national.pages()
        home = pages['index.html']
        last = home.index('href="las-vegas.html">Visiting Las Vegas</a>')
        for name, state in STATE_PAGE.items():
            self.assertIn(name, pages)
            box = re.search(r'<aside class="cityguide".*?</aside>', pages[state], re.S)
            self.assertTrue(box, f'{state}: no visitor-guide box')
            self.assertIn(f'href="{name}"', box.group(0))
            at = home.index(f'href="{name}"')
            self.assertGreater(at, last, f'{name} should follow the links before it on the home page')
            last = at
        self.assertIn('href="las-vegas.html"', pages['nevada.html'])


if __name__ == '__main__':
    unittest.main()
