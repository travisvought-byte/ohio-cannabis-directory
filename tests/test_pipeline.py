"""The source pipeline (pipeline/): registry rules, normalizing, dedupe and the published output."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline import common, merge, normalize  # noqa: E402

REG = json.loads((ROOT / 'pipeline/registry.json').read_text(encoding='utf-8'))
PERM = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))
METHODS = {'socrata', 'arcgis', 'csv', 'xlsx', 'json', 'pdf', 'html', 'page-link', 'manual'}


class Registry(unittest.TestCase):
    def test_sources_are_complete_and_public(self):
        ids = set()
        for s in REG['sources']:
            self.assertNotIn(s['id'], ids)
            ids.add(s['id'])
            self.assertRegex(s['id'], r'^[a-z]{2}-[a-z0-9-]+$')
            self.assertIn(s['scope'], ('state', 'country'))
            if s['scope'] == 'state':
                self.assertIn(s['jurisdiction'], PERM['jurisdictions'])
            self.assertIn(s['status'], ('active', 'queued', 'blocked'))
            self.assertIn(s['evidence_level'], common.EVIDENCE_LEVELS)
            self.assertIn(s['fetch']['method'], METHODS)
            self.assertTrue(s['landing_url'].startswith('https://'), s['id'])
            self.assertTrue(s['publisher'] and s['title'])
            if s['status'] == 'active':
                self.assertNotEqual(s['fetch']['method'], 'manual', s['id'])
                self.assertTrue(s['fetch']['url'].startswith('https://'), s['id'])
                self.assertIn('name', s['map'], s['id'])
                self.assertTrue('street' in s['map'] or 'address' in s['map'], s['id'])
                self.assertTrue(s.get('label') and s.get('kept_rule'), s['id'])
            for field in s.get('map', {}):
                self.assertIn(field, common.FIELDS, (s['id'], field))

    def test_no_personal_name_fields_are_mapped(self):
        for s in REG['sources']:
            for field, rule in s.get('map', {}).items():
                if field in ('phone', 'website'):
                    continue
                text = json.dumps(rule).lower()
                self.assertNotRegex(text, r'contact|owner name|manager|agent name|first name|last name', s['id'])


class Normalizing(unittest.TestCase):
    SOURCE = {'id': 'us-xx-test', 'jurisdiction': 'CO', 'topic': 'retail',
              'keep': [{'column': 'License Type', 'match': 'retail'}, {'column': 'Status', 'match': 'active'}],
              'map': {'name': 'DBA', 'licensee': 'Licensee', 'street': 'Street', 'city': 'City', 'zip': 'ZIP',
                      'phone': 'Phone', 'license_number': 'License #'}}

    def test_keep_and_map(self):
        rows = [{'DBA': 'GREEN LEAF', 'Licensee': 'GREEN LEAF LLC', 'Street': '12 MAIN ST', 'City': 'DENVER', 'ZIP': '80202.0',
                 'Phone': '303.555.0100', 'License #': 'R-1', 'License Type': 'Retail Store', 'Status': 'Active', 'Contact': 'Jo Smith'},
                {'DBA': 'X', 'Street': '1 A St', 'License Type': 'Cultivation', 'Status': 'Active'}]
        kept = [r for r in rows if normalize.keep(r, self.SOURCE['keep'])]
        self.assertEqual(len(kept), 1)
        out = normalize.normalize_row(kept[0], self.SOURCE['map'], 'CO')
        self.assertEqual(out['name'], 'Green Leaf')
        self.assertEqual(out['licensee'], 'Green Leaf LLC')
        self.assertEqual(out['phone'], '(303) 555-0100')
        self.assertEqual(out['zip'], '80202')
        self.assertNotIn('Jo Smith', json.dumps(out))

    def test_merge_joins_the_same_store_on_two_lists(self):
        a = {'topic': 'retail', 'rows': [{'name': 'Green Leaf', 'street': '12 Main Street', 'city': 'Denver', 'state': 'CO', 'zip': '80202', 'license_number': 'R-1'}]}
        b = {'topic': 'medical-dispensary', 'rows': [{'name': 'Green Leaf Dispensary', 'street': '12 Main St', 'city': 'Denver', 'state': 'CO', 'zip': '80202', 'license_number': 'M-9'},
                                                     {'name': 'Other', 'street': '99 Elm St', 'city': 'Denver', 'state': 'CO', 'zip': '80202'}]}
        locs, dupes = merge.merge_state([a, b])
        self.assertEqual(dupes, 1)
        self.assertEqual(len(locs), 2)
        joined = next(l for l in locs if l['name'] == 'Green Leaf')
        self.assertEqual(joined['kind'], 'adult-use and medical')
        self.assertEqual(joined['licenses'], ['M-9', 'R-1'])


class Published(unittest.TestCase):
    def test_every_published_state_traces_to_a_regulator_list(self):
        path = ROOT / 'data/state-retail-locations.json'
        if not path.exists():
            self.skipTest('no pipeline output yet')
        data = json.loads(path.read_text(encoding='utf-8'))
        for s in data['states']:
            self.assertIn(s['state'], PERM['jurisdictions'])
            self.assertTrue(s['sources'])
            for src in s['sources']:
                self.assertEqual(src['kind'], 'regulator')
                self.assertTrue(src['url'].startswith('https://'))
                self.assertRegex(src['retrieved_on'], r'^\d{4}-\d{2}-\d{2}$')
                self.assertTrue((ROOT / f'data/sources/pipeline/{src["id"]}.json').exists(), src['id'])
            self.assertEqual(len(s['locations']), s['counts']['locations'])
            for loc in s['locations']:
                self.assertTrue(loc['name'].strip() and loc['address'].strip(), loc)
                self.assertFalse(set(loc) - {'name', 'licensee', 'address', 'city', 'phone', 'county', 'website',
                                             'lat', 'lon', 'opened', 'kind', 'licenses'}, loc)

    def test_snapshots_carry_only_normalized_fields(self):
        for path in (ROOT / 'data/sources/pipeline').glob('*.json'):
            if path.name.startswith('_'):
                continue
            snap = json.loads(path.read_text(encoding='utf-8'))
            self.assertTrue(snap['rows'])
            for row in snap['rows']:
                self.assertFalse(set(row) - set(common.FIELDS), (path.name, row))


if __name__ == '__main__':
    unittest.main()
