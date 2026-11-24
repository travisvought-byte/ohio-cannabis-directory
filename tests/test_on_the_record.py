"""The "On the record" section (data/on-the-record.json, owner direction November 24, 2026).

Checks: every entry links to the official record; every group and every side is rendered in the same
format; self-represented witnesses are not named; people appear only in official public roles; the
OHCANN directory record keeps its ID and carries the new evidence; blocked sources are recorded as
attempts; and the scorecard and the advocacy page both link to the section.
"""
import html
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / 'data/on-the-record.json').read_text(encoding='utf-8'))
PAGE = (ROOT / 'lawmakers.html').read_text(encoding='utf-8')
DETAIL = (ROOT / 'on-the-record.html').read_text(encoding='utf-8')
LEG = json.loads((ROOT / 'data/legislators.json').read_text(encoding='utf-8'))
POSITIONS = {'Sponsor', 'Proponent', 'Opponent', 'Interested Party'}


class OnTheRecord(unittest.TestCase):
    def test_testimony_entries_link_to_the_official_record(self):
        bills = {b['id'] for b in DATA['bills']}
        ids = [t['id'] for t in DATA['testimony']]
        self.assertEqual(len(ids), len(set(ids)))
        for t in DATA['testimony']:
            self.assertIn(t['bill'], bills)
            self.assertIn(t['position'], POSITIONS, t['id'])
            self.assertRegex(t['hearing_date'], r'^\d{4}-\d{2}-\d{2}$')
            if t['document_url']:
                self.assertEqual(urlparse(t['document_url']).hostname, 'search-prod.lis.state.oh.us', t['id'])
            self.assertTrue(t['quote'] or t['note'], t['id'])
        for b in DATA['bills']:
            for key in ('official_page', 'committee_page', 'status_page'):
                self.assertIn(urlparse(b[key]).hostname, ('ohiohouse.gov', 'www.ohiosenate.gov'), b['id'])

    def test_self_represented_witnesses_are_not_named(self):
        for t in DATA['testimony']:
            if t['individual']:
                self.assertIsNone(t['witness'], t['id'])
                self.assertIsNone(t['organization'], t['id'])
            else:
                self.assertTrue(t['witness'] and t['organization'] not in ('', 'Self'), t['id'])
        self.assertNotIn('<td>Self</td>', PAGE)
        self.assertNotIn('<td>Self</td>', DETAIL)

    def test_every_entry_is_rendered_in_the_same_format(self):
        section = PAGE[PAGE.index('id="on-the-record"'):]
        for t in DATA['testimony']:
            row = re.search(r'<tr id="%s">(.*?)</tr>' % re.escape(t['id']), section, re.S)
            self.assertIsNotNone(row, t['id'])
            self.assertEqual(row.group(1).count('<td data-label='), 6, t['id'])
            if t['quote']:
                self.assertIn(html.escape(t['quote']), row.group(1), t['id'])
        for lob in DATA['lobbying']:
            self.assertTrue(lob['employers'])
            self.assertEqual(urlparse(lob['search_url']).hostname, 'www2.jlec-olig.state.oh.us')
            block = DETAIL[DETAIL.index('id="lobby-%s"' % lob['bill']):]
            block = block[:block.index('</section>')]
            self.assertEqual(block.count('<tr><td data-label="Employer">'), len(lob['employers']), lob['bill'])
            for e in lob['employers']:
                self.assertIn(html.escape(e['employer']), block, e['employer'])
        for org in DATA['nonprofit_filings']:
            self.assertRegex(org['ein'], r'^\d{2}-\d{7}$')
            self.assertTrue(org['filings'], org['label'])
            self.assertIn('id="f990-%s"' % org['ein'], DETAIL)

    def test_people_appear_only_in_official_roles(self):
        text = json.dumps(DATA)
        # No street addresses, personal email addresses or phone numbers in the data.
        self.assertIsNone(re.search(r'\b\d{3,5} [A-Z][a-z]+ (Street|St|Avenue|Ave|Road|Rd|Place|Drive|Dr|Lane|Ln)\b', text))
        self.assertIsNone(re.search(r'[\w.]+@[\w.]+\.(com|org|net)', text))
        self.assertIsNone(re.search(r'\(\d{3}\) \d{3}-\d{4}', text))

    def test_ohcann_profile_and_directory_record(self):
        o = DATA['ohcann']
        self.assertEqual(o['directory_record_id'], 'org-28996af4250a')
        directory = json.loads((ROOT / 'data/directory.json').read_text(encoding='utf-8'))
        org = next(x for x in directory['organizations'] if x['id'] == 'org-28996af4250a')
        self.assertIn('org-28996af4250a', org['legacy_ids'])
        svc = next(x for x in directory['services'] if x['id'] == 'svc-profile-28996af4250a')
        new = [e for e in svc['evidence_ids'] if e.startswith('ev-otr-28996af4250a-')]
        self.assertEqual(len(new), 7)
        evidence = {e['id']: e for e in directory['evidence']}
        for key in new:
            self.assertEqual(evidence[key]['status'], 'source-reviewed')
            self.assertEqual(evidence[key]['reviewed_on'], DATA['as_of'])
        self.assertEqual(set(o['positions']), {b['id'] for b in DATA['bills']})
        self.assertIn('id="ohcann"', DETAIL)
        self.assertIn('id="ohcann-summary"', PAGE)

    def test_blocked_sources_are_recorded_as_attempts(self):
        sources = ' '.join(a['source'] + ' ' + a['result'] for a in DATA['retrieval_attempts'])
        self.assertIn('Secretary of State', sources)
        self.assertIn('Blocked', sources)
        for a in DATA['retrieval_attempts']:
            self.assertEqual(a['attempted_on'], DATA['as_of'])

    def test_hb611_record_on_lawmaker_cards(self):
        events = [e for e in LEG['vote_events'] if e['bill'] == 'HB 611']
        self.assertEqual(len(events), 2)
        self.assertFalse(any(e['is_final_agreement'] for e in events))
        sponsors = [s for m in LEG['members'] for s in m.get('sponsorships', [])]
        self.assertEqual(sum(s['role'] == 'Primary sponsor' for s in sponsors), 2)

    def test_pages_link_to_the_section(self):
        self.assertIn('href="#on-the-record"', PAGE)
        self.assertIn('href="https://the-reefer.com/on-the-record.html#lobbying"', PAGE)
        self.assertIn('href="https://ohioweed.org/lawmakers.html#on-the-record"', DETAIL)
        advocacy = (ROOT / 'advocacy.html').read_text(encoding='utf-8')
        self.assertIn('href="lawmakers.html#on-the-record"', advocacy)
        self.assertIn('href="https://the-reefer.com/on-the-record.html"', advocacy)

    def test_each_page_stays_inside_the_html_budget(self):
        for name in ('lawmakers.html', 'on-the-record.html'):
            self.assertLess((ROOT / name).stat().st_size, 200000, name)


if __name__ == '__main__':
    unittest.main()
