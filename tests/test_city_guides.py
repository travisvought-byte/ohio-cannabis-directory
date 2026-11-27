"""The Denver, Chicago, New York City, Los Angeles, Detroit, Boston, Seattle, Phoenix, Miami, San Francisco, Portland, New Orleans
and Washington, DC visitor guides (city_guides.py): every point cites a listed primary source with a checked date, the FAQ data matches the questions shown,
yes/no answers are shown in words as well as symbols, no business or phone number is named, and each state page and the home page link
the guide (California's box links both Los Angeles and San Francisco). Miami and New Orleans, in medical-only states, say first that
Florida and Louisiana allow medical marijuana only, and their yes/no tables answer for a patient. Washington, DC says first that it
allows possession but sells only through its medical program. The visiting.html hub lists every guide, Las Vegas included, with
whether adults 21 and older can buy there in words and a symbol, and every guide, state box and the home page link it."""
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
STATE_PAGE = {'denver.html': 'colorado.html', 'chicago.html': 'illinois.html', 'new-york-city.html': 'new-york.html',
              'los-angeles.html': 'california.html', 'detroit.html': 'michigan.html', 'boston.html': 'massachusetts.html',
              'seattle.html': 'washington.html', 'phoenix.html': 'arizona.html', 'miami.html': 'florida.html',
              'san-francisco.html': 'california.html', 'portland.html': 'oregon.html', 'new-orleans.html': 'louisiana.html',
              'washington-dc.html': 'district-of-columbia.html'}
MEDICAL_ONLY = {'miami.html', 'new-orleans.html'}
STATUS = MEDICAL_ONLY | {'washington-dc.html'}  # guides that open with a status notice
CHECKED = '2026-11-27'


def build(name, origin=''):
    previous = build_national.ORIGIN
    build_national.ORIGIN = origin
    try:
        return city_guides.page(build_national, name, LANDING[name])
    finally:
        build_national.ORIGIN = previous


class CityGuides(unittest.TestCase):
    def test_the_thirteen_guides_are_registered(self):
        self.assertEqual(list(city_guides.GUIDES), ['denver.html', 'chicago.html', 'new-york-city.html',
                                                    'los-angeles.html', 'detroit.html', 'boston.html',
                                                    'seattle.html', 'phoenix.html', 'miami.html',
                                                    'san-francisco.html', 'portland.html', 'new-orleans.html',
                                                    'washington-dc.html'])
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
            if d['page'].get('status'):
                self.assertTrue(d['page']['status']['source_ids'], f'{name}: a status notice without a source')
                used.update(d['page']['status']['source_ids'])
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
            header = build_national.esc(d['page'].get('places_header', 'Allowed?'))
            self.assertIn(f'<th scope="col">Place</th><th scope="col">{header}</th>', page)
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

    def test_miami_says_first_that_florida_is_medical_only(self):
        d, page = city_guides.load('miami.html'), build('miami.html')
        status = page.index('<section class="lv-status" aria-labelledby="miastatus-h"><h2 id="miastatus-h">')
        self.assertLess(page.index('For adults 21 and older'), status)
        self.assertLess(status, page.index('<ul class="lv-glance"'))
        self.assertIn('Florida allows medical marijuana only</h2>', page)
        self.assertIn('Visitors can’t buy marijuana in Florida.', page)
        self.assertIn('doesn’t accept medical marijuana cards from other states', page)
        self.assertIn('.lv-status{', page)
        buy = next(s for s in d['sections'] if s['id'] == 'buy')
        self.assertTrue(buy['short'].startswith('No. Florida has no adult-use sales.'))
        self.assertIn('a visitor without a Florida medical card can’t buy marijuana anywhere in the state', buy['short'])
        # The yes/no table answers for a registered patient, and says so in its caption and column header.
        self.assertIn('<caption>Where can a registered Florida patient use medical marijuana?</caption>', page)
        self.assertIn('<th scope="col">Allowed for a registered patient?</th>', page)
        self.assertNotIn('<caption>Can you use cannabis here?</caption>', page)
        self.assertNotIn('"yes"', json.dumps([r['answer'] for s in d['sections'] for r in s.get('places', [])]))
        for section in ('medical', 'possession', 'hemp'):
            self.assertIn(f'<h2 id="{section}-h">', page)
        self.assertIn('href="https://knowthefactsmmj.com/mmtc/">See the licensed treatment centers on the Office of Medical Marijuana Use’s list</a>', page)

    def test_new_orleans_says_first_that_louisiana_is_medical_only(self):
        d, page = city_guides.load('new-orleans.html'), build('new-orleans.html')
        status = page.index('<section class="lv-status" aria-labelledby="nolastatus-h"><h2 id="nolastatus-h">')
        self.assertLess(page.index('For adults 21 and older'), status)
        self.assertLess(status, page.index('<ul class="lv-glance"'))
        self.assertIn('Louisiana allows medical marijuana only</h2>', page)
        self.assertIn('Louisiana has no adult-use marijuana sales.', page)
        buy = next(s for s in d['sections'] if s['id'] == 'buy')
        self.assertTrue(buy['short'].startswith('Only as a medical marijuana patient. Louisiana has no adult-use sales.'))
        # What Louisiana law says about visitors: only a visiting qualifying patient with another state's card can buy (R.S. 40:1046.1).
        medical = next(s for s in d['sections'] if s['id'] == 'medical')
        self.assertEqual({sid for p in medical['points'] for sid in p['source_ids']}, {'la-1046-1', 'la-966'})
        self.assertIn('<caption>Where can a medical marijuana patient buy, take or use it?</caption>', page)
        self.assertIn('<th scope="col">Allowed for a patient?</th>', page)
        self.assertNotIn('<caption>Can you use cannabis here?</caption>', page)
        for section in ('medical', 'possession', 'hemp'):
            self.assertIn(f'<h2 id="{section}-h">', page)
        self.assertIn('href="https://ldh.la.gov/page/medical-marijuana">See the permitted retailers on the Louisiana Department of Health’s list</a>', page)
        # The Department of Health's list carries retailers' phone numbers; none is copied.
        self.assertNotRegex(page, r'\d{3}-\d{3}-\d{4}')

    def test_other_guides_keep_the_plain_table_and_no_status_notice(self):
        for name in city_guides.GUIDES:
            if name in STATUS:
                continue
            page, p = build(name), city_guides.load(name)['page']
            for key in ('status', 'places_caption', 'places_header'):
                self.assertNotIn(key, p, name)
            self.assertNotIn('lv-status', page, name)
            self.assertIn('<caption>Can you use cannabis here?</caption>', page, name)
            self.assertIn('<th scope="col">Place</th><th scope="col">Allowed?</th>', page, name)

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
        # California has two guides, both linked from its one visitor-guide box, Los Angeles first.
        box = re.search(r'<aside class="cityguide".*?</aside>', pages['california.html'], re.S).group(0)
        self.assertLess(box.index('href="los-angeles.html"'), box.index('href="san-francisco.html"'))
        self.assertIn('aria-label="Visitor guides: Los Angeles, San Francisco"', box)
        self.assertEqual(pages['california.html'].count('<aside class="cityguide"'), 1)

    def test_washington_dc_says_first_that_sales_are_medical_only(self):
        d, page = city_guides.load('washington-dc.html'), build('washington-dc.html')
        status = page.index('<section class="lv-status" aria-labelledby="dcstatus-h"><h2 id="dcstatus-h">')
        self.assertLess(page.index('For adults 21 and older'), status)
        self.assertLess(status, page.index('<ul class="lv-glance"'))
        self.assertIn('DC allows possession, but sells cannabis only through its medical program</h2>', page)
        buy = next(s for s in d['sections'] if s['id'] == 'buy')
        self.assertTrue(buy['short'].startswith('Only through DC’s medical cannabis program.'))
        # Initiative 71's limits come from the D.C. Code itself; federal land from the Attorney General, MPD and the Park Service.
        possession = next(s for s in d['sections'] if s['id'] == 'possession')
        self.assertIn('dc-904', possession['points'][0]['source_ids'])
        self.assertIn('2 ounces or less', possession['points'][0]['text'])
        federal = next(s for s in d['sections'] if s['id'] == 'federal-land')
        self.assertEqual({sid for p in federal['points'] for sid in p['source_ids']}, {'oag-mj', 'mpd-mj', 'nps-mj', 'nama-comp'})
        # The table answers for any adult 21 or older, so it keeps the plain caption.
        self.assertIn('<caption>Can you use cannabis here?</caption>', page)
        self.assertNotIn('places_caption', d['page'])
        self.assertIn('href="https://abca.dc.gov/service/find-medical-cannabis-retailer">See the licensed retailers on ABCA’s map</a>', page)
        self.assertIn('href="https://abca.dc.gov/page/patients-non-dc-residents">Check whether ABCA recognizes your state’s card</a>', page)
        # No fee or price from ABCA's pages is copied.
        self.assertNotRegex(json.dumps(d['sections'], ensure_ascii=False), r'\$\d')

    def test_visitor_guides_hub(self):
        pages = build_national.pages()
        self.assertIn(city_guides.HUB, pages)
        hub = pages[city_guides.HUB]
        rows = city_guides.hub_rows()
        # Every guide, Las Vegas included, once, A to Z within its group.
        self.assertEqual(sorted(r['page'] for r in rows), sorted(['las-vegas.html'] + list(city_guides.GUIDES)))
        adult = [r for r in rows if r['mark'] == 'yes']
        medical = [r for r in rows if r['mark'] != 'yes']
        self.assertEqual([r['city'] for r in adult], sorted(r['city'] for r in adult))
        self.assertEqual({r['page'] for r in medical}, {'miami.html', 'new-orleans.html', 'washington-dc.html'})
        self.assertLess(hub.index('id="adult-use"'), hub.index('id="medical-only"'))
        for r in rows:
            self.assertEqual(hub.count(f'<th scope="row"><a href="{r["page"]}">'), 1, r['page'])
            # The answer in words, from the guide's own "buy" answer, as well as a symbol.
            self.assertTrue(r['words'].startswith(('Yes', 'No', 'Only')), r['page'])
            self.assertIn(build_national.esc(r['words']), hub)
        self.assertIn('<th scope="col">Can adults 21 and older buy there?</th>', hub)
        self.assertEqual(hub.count('<h1'), 1)
        self.assertIn('For adults 21 and older', hub)
        self.assertIn('assets/analytics.js', hub)
        self.assertNotIn('FAQPage', hub)
        self.assertNotRegex(hub, r'<svg(?![^>]*aria-hidden="true")[^>]*viewBox="0 0 24 24"')
        self.assertIn('checked November 27, 2026', hub)
        page = build_national.ORIGIN
        try:
            build_national.ORIGIN = 'https://the-reefer.com'
            built = city_guides.hub(build_national, LANDING[city_guides.HUB])
        finally:
            build_national.ORIGIN = page
        self.assertIn('<link rel="canonical" href="https://the-reefer.com/visiting.html">', built)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', built, re.S).group(1).replace('<\\/', '</'))
        crumbs = next(n for n in ld['@graph'] if n['@type'] == 'BreadcrumbList')
        self.assertEqual([i['name'] for i in crumbs['itemListElement']], ['Home', 'Visitor guides'])
        # Linked from the home page next to the city links, from every guide and from every state's visitor-guide box.
        home = pages['index.html']
        self.assertLess(home.index(f'href="{city_guides.HUB}"'), home.index('href="las-vegas.html">Visiting Las Vegas</a>'))
        for name in ['las-vegas.html'] + list(city_guides.GUIDES):
            self.assertIn(f'<strong>More city guides:</strong> <a href="{city_guides.HUB}">', pages[name], name)
        for state in set(STATE_PAGE.values()) | {'nevada.html'}:
            box = re.search(r'<aside class="cityguide".*?</aside>', pages[state], re.S).group(0)
            self.assertIn(f'href="{city_guides.HUB}"', box, state)


if __name__ == '__main__':
    unittest.main()
