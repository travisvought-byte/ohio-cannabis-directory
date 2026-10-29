"""Company identity, public-contact provenance and reproducible company exports."""
import copy
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_pa_companies import build_model, build_page
from directory_data import load_directory

data = load_directory()
cards = build_model(data)
assert len(cards) == 94
assert len({c['id'] for c in cards}) == len(cards)
by_id = {c['id']: c for c in cards}
assert by_id['org-afa309caf39c']['name'] == 'INSA'
assert by_id['org-90725b1d60a7']['name'] == 'FarmaceuticalRx'
assert by_id['org-cannagas-supply']['roles'] == ['Supplier']
assert by_id['org-cozen-oconnor']['categories'] == ['Legal & licensing']
assert any('jbedwick@cozen.com' == f['value'] for f in by_id['org-cozen-oconnor']['facts'])
assert any('Johnstown' in f['value'] for f in by_id['org-hanging-gardens']['facts'])
assert not any(c['name'] in ('Calypso Enterprises', 'Whole Plants', 'Parea Biosciences') for c in cards)
assert all(c['sources'] for c in cards)
assert all(f['source_url'].startswith('https://') and f['reviewed_on'] for c in cards for f in c['facts'])
# An additional service for one company must not become another company card.
fixture = copy.deepcopy(data)
extra = copy.deepcopy(next(s for s in fixture['services'] if s['organization_id'] == 'org-htg-supply'))
extra['id'] = 'svc-test-second-htg-route'
fixture['services'].append(extra)
assert len(build_model(fixture)) == len(cards)
assert len(next(c for c in build_model(fixture) if c['id'] == 'org-htg-supply')['routes']) == 2
# Reverted unpublished identities stay out of the public company view.
next(o for o in fixture['organizations'] if o['id'] == 'org-htg-supply')['scope'] = 'reference-only'
assert 'org-htg-supply' not in {c['id'] for c in build_model(fixture)}
before = (ROOT / 'data/public-pa-companies.json').read_bytes()
assert json.loads(before) == cards
assert build_page(data) == (ROOT / 'pennsylvania-directory.html').read_text()
assert (ROOT / 'data/public-pa-companies.json').read_bytes() == before
rows = list(csv.DictReader(io.StringIO((ROOT / 'pennsylvania-companies.csv').read_text(encoding='utf-8-sig'))))
assert len(rows) == len(cards)
assert {r['Organization ID'] for r in rows} == set(by_id)
assert any('contact@pennhgroup.com' in r['Public business facts'] for r in rows)
print('PASS PA companies: unique identities, cited contacts, brand search inputs, publication isolation and deterministic exports.')
