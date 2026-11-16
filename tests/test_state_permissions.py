import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validate_permissions import validate, evidence_level  # noqa: E402
import permissions_page  # noqa: E402

DATA = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))


def broken(change):
    data = copy.deepcopy(DATA)
    change(data)
    return data


class StatePermissionsTest(unittest.TestCase):
    def test_repository_data_is_valid(self):
        validate(copy.deepcopy(DATA))

    def test_every_jurisdiction_answers_the_top_questions(self):
        answered = {(a['state'], a['question']) for a in DATA['answers']}
        self.assertEqual(len(DATA['jurisdictions']), 51)
        for code in DATA['jurisdictions']:
            for q in ('adult-use', 'medical'):
                self.assertIn((code, q), answered)

    def test_rejects_stored_not_reviewed_answers(self):
        def change(d): d['answers'][0]['status'] = 'not-reviewed'
        with self.assertRaises(AssertionError):
            validate(broken(change))

    def test_rejects_unknown_status_and_sources(self):
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['answers'][0].update(status='legal')))
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['answers'][0].update(source_ids=['no-such-source'])))
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['answers'][0].update(source_ids=[])))

    def test_rejects_missing_top_level_answer(self):
        def change(d):
            d['answers'] = [a for a in d['answers'] if not (a['state'] == 'WY' and a['question'] == 'medical')]
        with self.assertRaises(AssertionError):
            validate(broken(change))

    def test_rejects_uncited_sources_and_compilation_official_links(self):
        def extra(d):
            d['sources'].append(dict(d['sources'][0], id='unused-source'))
        with self.assertRaises(AssertionError):
            validate(broken(extra))
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['official_links'].update(ID={'source_id': 'natl-disa-map'})))

    def test_medical_not_permitted_needs_an_official_source(self):
        def change(d):
            for a in d['answers']:
                if (a['state'], a['question']) == ('ID', 'medical'):
                    a['source_ids'] = ['natl-disa-map']
        with self.assertRaises(AssertionError):
            validate(broken(change))
        sources = {s['id']: s for s in DATA['sources']}
        for a in DATA['answers']:
            if a['question'] == 'medical' and a['status'] == 'not-permitted':
                self.assertNotEqual(evidence_level(a, sources), 'compilation', a['state'])

    def test_official_links_cover_the_states_reviewed_for_issue_147(self):
        reviewed = ['ID', 'IN', 'IA', 'KS', 'LA', 'MT', 'NE', 'NC', 'ND', 'SC', 'WA', 'WI', 'WY']
        self.assertEqual([c for c in reviewed if c not in DATA['official_links']], [])

    def test_national_audience(self):
        audiences = {i['id']: i.get('audience', 'consumer') for i in DATA['national']}
        self.assertIn('business', audiences.values())
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['national'][0].update(audience='investors')))
        html = permissions_page.render_national(DATA)
        self.assertLess(html.index('data-audience="consumer"'), html.index('id="national-business"'))
        self.assertLess(html.index('id="national-business"'), html.index('data-audience="business"'))

    def test_evidence_levels(self):
        sources = {s['id']: s for s in DATA['sources']}
        levels = {(a['state'], a['question']): evidence_level(a, sources) for a in DATA['answers']}
        self.assertEqual(levels[('OH', 'adult-use')], 'official')
        # The rule itself, independent of which answers happen to rest on which sources today.
        official = next(s['id'] for s in DATA['sources'] if s['kind'] == 'statute')
        compiled = next(s['id'] for s in DATA['sources'] if s['kind'] == 'compilation')
        self.assertEqual(evidence_level({'source_ids': [official]}, sources), 'official')
        self.assertEqual(evidence_level({'source_ids': [compiled]}, sources), 'compilation')
        self.assertEqual(evidence_level({'source_ids': [official, compiled]}, sources), 'mixed')

    def test_every_adult_use_answer_cites_a_state_source(self):
        # Issue #146: no adult-use answer rests on national compilations alone.
        sources = {s['id']: s for s in DATA['sources']}
        for a in DATA['answers']:
            if a['question'] == 'adult-use':
                self.assertNotEqual(evidence_level(a, sources), 'compilation', a['state'])
                self.assertTrue(any(sources[sid]['scope'] == 'state' for sid in a['source_ids']), a['state'])

    def test_page_payload_cites_listed_sources(self):
        info = permissions_page.payload(DATA)
        count = len(DATA['sources'])
        for answers in info['answers'].values():
            for a in answers.values():
                self.assertTrue(all(1 <= n <= count for n in a['cites']))
        html = permissions_page.render_permissions(DATA)
        self.assertIn('Not yet reviewed', html)
        self.assertEqual(html.count('<option value='), 51 + 52)


if __name__ == '__main__':
    unittest.main()
