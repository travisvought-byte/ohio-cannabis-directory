"""Advertising on the-reefer.com (owner's direction, November 19, 2026): sponsored spots are labeled, sit apart from the
listings and the law answers, never appear when data/national-sponsors.json is empty, and leave the no-paid-placement
rules in force. The privacy page says plainly what the site counts and keeps, and every page links to it."""
import json
import re
import sys
import tempfile
import unittest
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_national  # noqa: E402

TODAY = date.today()
DAY = timedelta(days=1)
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
# Containers a sponsored spot must never sit inside: the at-a-glance answers, answer and directory cards, the tile map,
# the dispensary and state lists, the medical card guides and the family of sites.
FORBIDDEN_CLASSES = {'glance', 'card', 'usmap', 'grid', 'rows', 'medcard', 'guides', 'family', 'needs', 'next', 'mapbox'}
FORBIDDEN_IDS = {'law', 'map', 'compare', 'disp-list', 'glance', 'dispensaries', 'medical-card'}


class SlotFinder(HTMLParser):
    """Records each sponsored spot with the classes and ids of every element around it."""

    def __init__(self):
        super().__init__()
        self.stack, self.slots = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        node = (tag, set((attrs.get('class') or '').split()), attrs.get('id'))
        if tag == 'aside' and 'ad-slot' in node[1]:
            self.slots.append({'attrs': attrs, 'ancestors': list(self.stack)})
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def slots_in(text):
    finder = SlotFinder()
    finder.feed(text)
    return finder.slots


def build_with(sponsors):
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'sponsors.json'
        path.write_text(json.dumps({'sponsors': sponsors}), encoding='utf-8')
        with mock.patch.object(build_national, 'SPONSORS_FILE', path):
            return build_national.pages()


FIXTURE = [
    {'id': 'ended', 'slot': 'home', 'sponsor': 'Old Sponsor', 'text': 'Ran last month.', 'url': 'https://old.example/',
     'start': (TODAY - 40 * DAY).isoformat(), 'end': (TODAY - DAY).isoformat()},
    {'id': 'later', 'slot': 'home', 'sponsor': 'Later Sponsor', 'text': 'Starts next month.', 'url': 'https://later.example/',
     'start': (TODAY + 30 * DAY).isoformat()},
    {'id': 'home-now', 'slot': 'home', 'sponsor': 'Example Testing Lab', 'text': 'Licensed testing for growers and processors.',
     'url': 'https://lab.example/', 'start': (TODAY - DAY).isoformat(), 'end': (TODAY + 30 * DAY).isoformat()},
    {'id': 'home-second', 'slot': 'home', 'sponsor': 'Second Sponsor', 'text': 'Never shown while another home spot runs.',
     'url': 'https://second.example/'},
    {'id': 'ohio', 'slot': 'state', 'sponsor': 'Example Ohio Clinic & Co', 'text': 'Medical card visits in Ohio.',
     'url': 'https://clinic.example/ohio', 'states': ['OH']},
]


class SponsoredSpotsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.empty = build_with([])
        cls.filled = build_with(FIXTURE)

    def test_empty_file_puts_nothing_on_any_page(self):
        for name, text in self.empty.items():
            self.assertNotIn('ad-slot', re.sub(r'<style>.*?</style>', '', text, flags=re.S), name)
            self.assertNotIn('>Sponsored</p>', text, name)
            self.assertNotIn('rel="sponsored', text, name)

    def test_committed_pages_follow_the_committed_file(self):
        committed = json.loads((ROOT / 'data/national-sponsors.json').read_text(encoding='utf-8'))
        self.assertIsInstance(committed['sponsors'], list)
        build_national.load_sponsors(build_national.load()[0]['jurisdictions'])  # the committed file passes the checks

    def test_one_labeled_spot_on_the_home_page(self):
        home = self.filled['index.html']
        slots = slots_in(home)
        self.assertEqual(len(slots), 1, 'at most one spot on the home page')
        self.assertEqual(slots[0]['attrs']['data-sponsor'], 'home-now', 'the first entry running today; ended and future spots are left out')
        self.assertEqual(slots[0]['attrs']['aria-label'], 'Sponsored')
        self.assertIn('<aside class="ad-slot" aria-label="Sponsored"', home)
        self.assertIn('<p class="ad-label">Sponsored</p>', home)
        self.assertIn('href="https://lab.example/" target="_blank" rel="sponsored noopener"', home)
        for absent in ('Old Sponsor', 'Later Sponsor', 'Second Sponsor', 'Example Ohio Clinic'):
            self.assertNotIn(absent, home)
        # After the map and the comparisons, before the family of sites.
        spot = home.index('<aside class="ad-slot"')
        self.assertGreater(spot, home.index('<section class="block" id="compare"'))
        self.assertGreater(spot, home.index('</section>', home.index('<section class="block" id="compare"')))
        self.assertLess(spot, home.index('<section class="block" id="family"'))
        self.assertIn('data-end="', home, 'a spot with an end date carries it, so the visitor’s date can hide it')
        self.assertIn(build_national.SPONSOR_SCRIPT, home)

    def test_state_spot_only_on_its_states_and_outside_the_answers(self):
        ohio = self.filled['ohio.html']
        slots = slots_in(ohio)
        self.assertEqual(len(slots), 1)
        self.assertIn('Example Ohio Clinic &amp; Co', ohio)
        self.assertIn('rel="sponsored noopener"', ohio)
        spot = ohio.index('<aside class="ad-slot"')
        self.assertGreater(spot, ohio.rindex('data-question="'), 'after every law answer')
        self.assertGreater(spot, ohio.rindex('data-pathway="'), 'after every directory card')
        self.assertGreater(spot, ohio.index('id="glance"'))
        self.assertNotIn(build_national.SPONSOR_SCRIPT, ohio, 'no end date, no script')
        for name in ('florida.html', 'pennsylvania.html', 'district-of-columbia.html'):
            self.assertEqual(slots_in(self.filled[name]), [], name)

    def test_spots_never_sit_inside_listings_answers_or_the_map(self):
        everywhere = [{'id': 'all', 'slot': 'state', 'sponsor': 'Everywhere', 'text': 'Every state page.', 'url': 'https://all.example/'},
                      {'id': 'home', 'slot': 'home', 'sponsor': 'Home', 'text': 'Home page.', 'url': 'https://home.example/'}]
        pages = build_with(everywhere)
        states = {build_national.slug(n) + '.html' for n in build_national.load()[0]['jurisdictions'].values()}
        for name, text in pages.items():
            slots = slots_in(text)
            if name in states or name == 'index.html':
                self.assertEqual(len(slots), 1, name)
            else:
                self.assertEqual(slots, [], f'{name} carries no sponsored spot')
            for slot in slots:
                for tag, classes, ident in slot['ancestors']:
                    self.assertFalse(classes & FORBIDDEN_CLASSES, f'{name}: spot inside .{sorted(classes & FORBIDDEN_CLASSES)}')
                    self.assertNotIn(ident, FORBIDDEN_IDS, f'{name}: spot inside #{ident}')
                    self.assertNotIn(tag, ('article', 'li', 'ul', 'ol', 'section', 'header', 'footer'), f'{name}: spot inside <{tag}>')

    def test_bad_entries_stop_the_build(self):
        codes = build_national.load()[0]['jurisdictions']
        good = {'id': 'x', 'slot': 'state', 'sponsor': 'X', 'text': 'Text.', 'url': 'https://x.example/'}
        bad = [
            {**good, 'url': 'http://x.example/'},
            {**good, 'url': 'javascript:alert(1)'},
            {**good, 'slot': 'law'},
            {**good, 'text': 'x' * 201},
            {**good, 'image': 'https://x.example/ad.png', 'image_alt': 'Ad'},
            {**good, 'image': 'assets/sponsors/missing.png', 'image_alt': 'Ad'},
            {**good, 'image_alt': 'No image'},
            {**good, 'states': ['ZZ']},
            {**good, 'states': []},
            {**good, 'slot': 'home', 'states': ['OH']},
            {**good, 'start': '2026-12-31', 'end': '2026-12-01'},
            {**good, 'end': 'next week'},
            {**good, 'rank': 1},
            {k: v for k, v in good.items() if k != 'sponsor'},
        ]
        for entry in bad:
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'sponsors.json'
                path.write_text(json.dumps({'sponsors': [entry]}), encoding='utf-8')
                with self.assertRaises(SystemExit, msg=entry):
                    build_national.load_sponsors(codes, path)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'sponsors.json'
            path.write_text(json.dumps({'sponsors': [good, good]}), encoding='utf-8')
            with self.assertRaises(SystemExit):
                build_national.load_sponsors(codes, path)


class AdvertisingWordingTest(unittest.TestCase):
    PAGES = build_national.pages()

    def test_no_page_promises_no_ads_or_no_sponsors(self):
        # Law answers may say a gift must be made "without advertising"; that is the law, not a promise about this site.
        promise = re.compile(r'\bno (ads|advertising|advertisements|adverts|sponsors|sponsorships?|sponsored)\b'
                             r'|\b(free of|without) (ads|advertisements|adverts|sponsors)\b|\bad-free\b'
                             r'|\bnever (sell|sells|carry|carries|run|runs|show|shows|accept|accepts) (ads|advertising|sponsors)\b', re.I)
        for name, text in self.PAGES.items():
            words = re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', text, flags=re.S))
            self.assertIsNone(promise.search(words), f'{name}: {promise.search(words)}')

    def test_no_paid_placement_rules_still_stand(self):
        self.assertIn('No paid placement, paid ranking or paid verification.', self.PAGES['about.html'])
        self.assertIn('No paid placement, paid ranking or paid verification. Listing is free and cannot be bought.', self.PAGES['partners.html'])
        self.assertIn('No paid placement or ranking.', self.PAGES['index.html'])
        rule = 'Sponsored spots are labeled “Sponsored”, sit apart from listings and answers, and never change what’s listed, how it ranks, or what a state page says.'
        for name in ('about.html', 'partners.html'):
            self.assertIn(rule, self.PAGES[name], name)

    def test_partners_page_explains_sponsoring_without_prices(self):
        partners = self.PAGES['partners.html']
        start = partners.index('<h2 id="sponsor">Sponsor or advertise</h2>')
        section = partners[start:partners.index('<h2 id="link">', start)]
        for words in ('Who can sponsor', 'labeled “Sponsored”', 'licensed where they operate', 'No health or medical claims',
                      'under 21', 'reviewed by a person', 'mailto:' + build_national.EMAIL):
            self.assertIn(words, section)
        self.assertIsNone(re.search(r'\$\s?\d|\bper (month|year|week)\b|\bprice', section, re.I), 'no prices on the page')


class PrivacyPageTest(unittest.TestCase):
    PAGES = build_national.pages()

    def test_privacy_page_says_what_is_counted_and_kept(self):
        text = self.PAGES['privacy.html']
        for words in ('Last updated November 21, 2026.', 'GoatCounter', 'sets no cookies', 'stores no personal information',
                      'your browser and screen size', 'approximate country', 'It does not store the IP address',
                      'GitHub Pages', build_national.PRIVACY_STATEMENT, 'server logs, including IP addresses, for security',
                      'not sent to this site', 'do not use cookies or your browser’s storage',
                      'labeled “Sponsored”', 'does not share visitor information with sponsors',
                      'adults 21 and older', 'not directed to children', 'We do not sell personal information',
                      'mailto:' + build_national.EMAIL,
                      # the store maps (November 21, 2026): where the street pictures come from and what the "near me" button does
                      '<h2 id="map">Maps</h2>', 'tile.openstreetmap.org', 'OpenStreetMap sees your IP address',
                      'Your location is never stored or sent to this site'):
            self.assertIn(words, text)

    def test_the_counter_is_still_goatcounter(self):
        script = (ROOT / 'assets/analytics.js').read_text(encoding='utf-8')
        self.assertIn('gc.zgo.at/count.js', script)
        self.assertNotIn('document.cookie', script)

    def test_national_pages_keep_no_storage(self):
        for name, text in self.PAGES.items():
            for api in ('localStorage', 'sessionStorage', 'document.cookie', 'indexedDB'):
                self.assertNotIn(api, text, f'{name} uses {api}; update privacy.html first')

    def test_every_page_links_to_privacy_in_its_footer(self):
        for name, text in self.PAGES.items():
            footer = text[text.index('<footer class="site">'):]
            self.assertIn('<a href="privacy.html">Privacy</a>', footer, name)


if __name__ == '__main__':
    unittest.main()
