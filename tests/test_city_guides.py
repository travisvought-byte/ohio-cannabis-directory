"""The Denver, Chicago, New York City, Los Angeles, Detroit, Boston, Seattle, Phoenix, Miami, San Francisco, Portland, New Orleans
and Washington, DC visitor guides (city_guides.py): every point cites a listed primary source with a checked date, the FAQ data matches the questions shown,
yes/no answers are shown in words as well as symbols, no business or phone number is named, and each state page and the home page link
the guide (California's box links both Los Angeles and San Francisco). Miami and New Orleans, in medical-only states, say first that
Florida and Louisiana allow medical marijuana only, and their yes/no tables answer for a patient. Washington, DC says first that it
allows possession but sells only through its medical program. The visiting.html hub lists every guide, Las Vegas included, with
whether adults 21 and older can buy there in words and a symbol, and every guide, state box and the home page link it.
Columbus, Cleveland, Cincinnati, Dayton, Toledo and Akron are home-market guides: Ohio's box links all six, each links this
site's own Ohio dispensary finder filtered to a city and county that exist in the location data, Ohio's 2026 law (S.B. 56) is
cited from the Revised Code and the Legislative Service Commission, and Cincinnati says plainly that CVG is in Kentucky, under
Kentucky law. Toledo says Michigan weed is contraband in Ohio, Dayton cites the Air Force museum's own pages for Wright-Patterson
and Akron cites the National Park Service for Cuyahoga Valley; none states an airport rule its airport's own site didn't give."""
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
              'washington-dc.html': 'district-of-columbia.html', 'columbus.html': 'ohio.html', 'cleveland.html': 'ohio.html',
              'cincinnati.html': 'ohio.html', 'dayton.html': 'ohio.html', 'toledo.html': 'ohio.html', 'akron.html': 'ohio.html'}
OHIO = ['columbus.html', 'cleveland.html', 'cincinnati.html', 'dayton.html', 'toledo.html', 'akron.html']
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
    def test_the_nineteen_guides_are_registered(self):
        self.assertEqual(list(city_guides.GUIDES), ['denver.html', 'chicago.html', 'new-york-city.html',
                                                    'los-angeles.html', 'detroit.html', 'boston.html',
                                                    'seattle.html', 'phoenix.html', 'miami.html',
                                                    'san-francisco.html', 'portland.html', 'new-orleans.html',
                                                    'washington-dc.html', 'columbus.html', 'cleveland.html',
                                                    'cincinnati.html', 'dayton.html', 'toledo.html', 'akron.html'])
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

    def test_ohio_guides_link_the_directorys_own_listings(self):
        locations = json.loads((ROOT / 'data/public-locations.json').read_text(encoding='utf-8'))['locations']
        cities = {l['city'] for l in locations if l['state'] == 'OH'}
        counties = {l['county'] for l in locations if l['state'] == 'OH' and l.get('county')}
        script = (ROOT / 'locations.html').read_text(encoding='utf-8')
        for key in ('state', 'city', 'county'):  # the finder reads these filters from the address
            self.assertIn(f"params.get('{key}')" if key == 'state' else "for(const key of ['city','county'])", script)
        pages = build_national.pages()
        box = re.search(r'<aside class="cityguide".*?</aside>', pages['ohio.html'], re.S).group(0)
        self.assertIn('aria-label="Visitor guides: Columbus, Cleveland, Cincinnati, Dayton, Toledo, Akron"', box)
        self.assertEqual(pages['ohio.html'].count('<aside class="cityguide"'), 1)
        home = pages['index.html']
        for name in OHIO:
            d, page = city_guides.load(name), build(name)
            city = d['page']['crumb'].removeprefix('Visiting ')
            self.assertIn(f'href="{name}"', box)
            self.assertIn(f'href="{name}">Visiting {city}</a>', home)
            self.assertEqual(d['page']['state'], 'OH')
            links = [a['href'] for a in d['page']['listings']['links']]
            links += [p['link']['href'] for s in d['sections'] for p in s['points'] if p.get('link', {}).get('href', '').startswith('https://ohioweed.org/')]
            self.assertTrue(links)
            for href in links:
                # Only the finder's own filters, with values the location data actually has.
                self.assertTrue(href.startswith('https://ohioweed.org/locations.html?state=OH&'), href)
                query = dict(part.split('=') for part in href.split('?', 1)[1].split('&'))
                self.assertLessEqual(set(query), {'state', 'city', 'county'}, href)
                if 'city' in query:
                    self.assertIn(query['city'], cities, href)
                if 'county' in query:
                    self.assertIn(query['county'], counties, href)
            self.assertIn(f'?state=OH&amp;city={city}"', page)
            # The box comes after the tiles and before the questions, with a heading of its own.
            self.assertLess(page.index('<ul class="lv-glance"'), page.index('<aside class="lv-show"'))
            self.assertLess(page.index('<aside class="lv-show"'), page.index('<nav class="onpage"'))
            self.assertIn(f'<h2 id="{d["page"]["prefix"]}listings-h">', page)
            # Suburbs named in the text are cities the location data lists in that county.
            county = next(dict(part.split('=') for part in h.split('?', 1)[1].split('&'))['county'] for h in links if 'county=' in h)
            in_county = {l['city'] for l in locations if l['state'] == 'OH' and l.get('county') == county}
            text = d['page']['listings']['text']
            suburbs = text.split('to include ', 1)[1].rstrip('.') if 'to include ' in text else ''  # Lucas County lists Toledo alone
            self.assertEqual(bool(suburbs), in_county != {city}, name)
            for suburb in re.split(r', | and ', suburbs) if suburbs else []:
                self.assertIn(suburb, in_county, f'{name}: {suburb}')
            # Ohio's 2026 law, from the Revised Code and the Legislative Service Commission; no fee or price.
            ids = {s['id'] for s in d['sources']}
            self.assertLessEqual({'orc-3796-221', 'orc-3796-20', 'orc-3796-04', 'orc-3796-06', 'orc-3796-062', 'lsc-sb56', 'ga-sb56', 'tsa-mmj'}, ids)
            buy = next(s for s in d['sections'] if s['id'] == 'buy')
            self.assertTrue(buy['short'].startswith('Yes, if you are 21 or older'))
            limits = next(s for s in d['sections'] if s['id'] == 'limits')
            self.assertIn('2.5 ounces of plant material', limits['points'][0]['text'])
            self.assertIn('15 grams of extract', limits['points'][0]['text'])
            changes = next(s for s in d['sections'] if s['id'] == 'changes')
            self.assertIn('March 20, 2026', changes['short'])
            self.assertNotRegex(json.dumps(d['sections'], ensure_ascii=False), r'\$\d')
            self.assertNotIn('<caption>Where can', page)  # the plain table: Ohio sells to any adult 21 or older
            self.assertIn('No business is named on this page', page)

    def test_cincinnati_says_cvg_is_in_kentucky(self):
        d, page = city_guides.load('cincinnati.html'), build('cincinnati.html')
        ky = next(s for s in d['sections'] if s['id'] == 'kentucky')
        self.assertTrue(ky['short'].startswith('No. The Cincinnati/Northern Kentucky International Airport (CVG) is in Hebron, Kentucky'))
        self.assertEqual({sid for p in ky['points'] for sid in p['source_ids']}, {'cvg-dir', 'krs-218a-1422', 'ky-omc'})
        self.assertIn('href="#kentucky"', page)
        self.assertIn('CVG is in Kentucky', page)
        self.assertIn('href="kentucky.html"', page)
        flying = next(s for s in d['sections'] if s['id'] == 'flying')
        self.assertIn('krs-218a-1422', flying['points'][0]['source_ids'])
        # The other Ohio guides state no airport rule of their own: none was found on the airports' sites.
        for name in ('columbus.html', 'cleveland.html', 'dayton.html', 'toledo.html', 'akron.html'):
            flying = next(s for s in city_guides.load(name)['sections'] if s['id'] == 'flying')
            self.assertEqual({sid for p in flying['points'] for sid in p['source_ids']}, {'tsa-mmj'})
            self.assertTrue(any('airport' in a['result'].lower() for a in city_guides.load(name)['attempts']))

    def test_cleveland_cites_the_city_smoking_rule_and_the_national_park(self):
        d, page = city_guides.load('cleveland.html'), build('cleveland.html')
        self.assertIn('cle-235', {sid for s in d['sections'] for p in s['points'] for sid in p['source_ids']})
        federal = next(s for s in d['sections'] if s['id'] == 'federal-land')
        self.assertEqual({sid for p in federal['points'] for sid in p['source_ids']}, {'nps-mj', 'cuva-comp'})
        self.assertIn('Outdoor areas the City of Cleveland owns or controls', page)

    def test_toledo_says_michigan_weed_is_contraband_in_ohio(self):
        d, page = city_guides.load('toledo.html'), build('toledo.html')
        mi = next(s for s in d['sections'] if s['id'] == 'michigan')
        self.assertTrue(mi['short'].startswith('No. Michigan sells to adults 21 and older'))
        self.assertIn('contraband', mi['short'])
        self.assertEqual({sid for p in mi['points'] for sid in p['source_ids']}, {'mcl-27955', 'lsc-sb56', 'orc-3796-221'})
        self.assertIn('contraband', next(p['text'] for p in mi['points'] if p['source_ids'] == ['lsc-sb56']))
        self.assertNotIn('bring', [s['id'] for s in d['sections']])  # the Michigan answer replaces the general one
        for href in ('michigan.html', 'detroit.html'):
            self.assertIn(f'href="{href}"', page)
        self.assertIn('href="#michigan"', page)

    def test_dayton_cites_the_air_force_museum_for_wright_patterson(self):
        d, page = city_guides.load('dayton.html'), build('dayton.html')
        federal = next(s for s in d['sections'] if s['id'] == 'federal-land')
        self.assertEqual({sid for p in federal['points'] for sid in p['source_ids']}, {'nmusaf-dir', 'nmusaf-rules', 'tsa-mmj'})
        for sid in ('nmusaf-dir', 'nmusaf-rules'):
            self.assertTrue(next(s for s in d['sources'] if s['id'] == sid)['url'].startswith('https://www.nationalmuseum.af.mil/'))
        self.assertIn('Wright-Patterson Air Force Base and the Air Force museum', page)
        self.assertTrue(any('wright-patterson' in a['result'].lower() for a in d['attempts']))

    def test_akron_cites_the_national_park_service_for_cuyahoga_valley(self):
        d, page = city_guides.load('akron.html'), build('akron.html')
        federal = next(s for s in d['sections'] if s['id'] == 'federal-land')
        self.assertEqual({sid for p in federal['points'] for sid in p['source_ids']}, {'nps-mj', 'cuva-comp'})
        cle = {s['id']: s['url'] for s in city_guides.load('cleveland.html')['sources']}
        for s in d['sources']:
            if s['id'] in ('nps-mj', 'cuva-comp'):
                self.assertEqual(s['url'], cle[s['id']])  # the same sources the Cleveland guide cites
        self.assertIn('Cuyahoga Valley National Park and other federal land', page)
        self.assertIn('href="cleveland.html"', page)

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
