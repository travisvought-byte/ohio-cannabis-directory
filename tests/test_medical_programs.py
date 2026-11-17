"""Patient guides for medical-only states (data/medical-programs.json) meet the evidence standard."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build_national  # noqa: E402

DATA = json.loads((ROOT / 'data/medical-programs.json').read_text(encoding='utf-8'))
PERM = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))
FACTS = ('who', 'fee', 'fee_help', 'card_length', 'caregivers', 'visitors', 'buy', 'note')
COVERAGE = json.loads((ROOT / 'data/medical-coverage.json').read_text(encoding='utf-8'))


class MedicalPrograms(unittest.TestCase):
    def test_covers_every_medical_only_state_and_only_states_with_a_program(self):
        status = {q: {a['state']: a['status'] for a in PERM['answers'] if a['question'] == q} for q in ('adult-use', 'medical')}
        medical_only = {s for s, v in status['adult-use'].items() if v == 'medical-only'}
        covered = [p['state'] for p in DATA['states']]
        self.assertEqual(len(covered), len(set(covered)))
        self.assertFalse(medical_only - set(covered))
        for state in covered:
            self.assertIn(status['medical'].get(state), ('allowed', 'medical-only'), state)

    def test_every_fact_names_an_existing_regulator_source(self):
        sources = {s['id']: s for s in DATA['sources']}
        self.assertEqual(len(sources), len(DATA['sources']), 'duplicate source ids')
        for s in DATA['sources']:
            self.assertIn(s['kind'], ('regulator', 'government', 'statute'), s['id'])
            self.assertTrue(s['url'].startswith('https://'), s['id'])
            self.assertRegex(s['retrieved_on'], r'^\d{4}-\d{2}-\d{2}$')
            self.assertNotIn(s['id'], {x['id'] for x in PERM['sources']}, 'clashes with a permissions source id')
        used = set()
        for p in DATA['states']:
            self.assertTrue(p['agency'].strip(), p['state'])
            for key in FACTS:
                if key in p:
                    self.assertTrue(p[key]['text'].strip(), (p['state'], key))
                    self.assertIn(p[key]['source'], sources, (p['state'], key))
                    used.add(p[key]['source'])
            if 'steps' in p:
                self.assertTrue(p['steps']['items'], p['state'])
                self.assertIn(p['steps']['source'], sources, p['state'])
                used.add(p['steps']['source'])
            self.assertTrue(p['links'], p['state'])
            for link in p['links']:
                self.assertTrue(link['url'].startswith(('https://', 'tel:+1')) and link['label'].strip(), (p['state'], link))
            self.assertTrue(any(k in p for k in FACTS + ('steps',)), p['state'])
        self.assertEqual(used, set(sources), 'every listed source is used')

    def test_unknown_fields_are_rejected(self):
        allowed = {'state', 'agency', 'steps', 'links'} | set(FACTS)
        for p in DATA['states']:
            self.assertFalse(set(p) - allowed, p['state'])

    def test_pages_show_the_patient_guide_with_numbered_sources(self):
        pages = build_national.pages()
        self.assertIn('medical.html', pages)
        for p in DATA['states']:
            page = pages[build_national.slug(PERM['jurisdictions'][p['state']]) + '.html']
            self.assertIn('id="medical-card"', page, p['state'])
            self.assertIn(f'{build_national.slug(PERM["jurisdictions"][p["state"]])}.html#medical-card', pages['medical.html'])
            for link in p['links']:
                self.assertIn(build_national.esc(link['url']), page)
        self.assertNotIn('id="medical-card"', pages['idaho.html'])
        self.assertNotIn('Adults without a card cannot buy here', pages['ohio.html'])
        self.assertIn('href="medical.html"', pages['index.html'])

    def test_coverage_answers_cite_known_sources_and_render(self):
        known = {s['id'] for s in DATA['sources']} | {s['id'] for s in PERM['sources']} | {s['id'] for s in COVERAGE['sources']}
        for s in COVERAGE['sources']:
            self.assertIn(s['kind'], ('regulator', 'government', 'statute'), s['id'])
            self.assertRegex(s['retrieved_on'], r'^\d{4}-\d{2}-\d{2}$')
        page = build_national.pages()['coverage.html']
        for item in COVERAGE['items']:
            self.assertTrue(any(p['source'] for p in item['points']), item['id'])
            self.assertIn(f'id="{item["id"]}"', page)
            for point in item['points']:
                if point['source']:
                    self.assertIn(point['source'], known, item['id'])
                self.assertIn(build_national.esc(point['text']), page)
        for p in DATA['states']:
            if 'fee_help' in p:
                self.assertIn(build_national.esc(p['fee_help']['text']), page)
        self.assertIn('href="coverage.html"', build_national.pages()['index.html'])


if __name__ == '__main__':
    unittest.main()
