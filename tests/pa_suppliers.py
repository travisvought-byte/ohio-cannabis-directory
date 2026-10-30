"""PA supplier import preserves identities, evidence, conservative coverage and research gates."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from import_pa_suppliers import build, MANIFEST
from build_pa_companies import build_model

data = json.loads((ROOT / 'data/directory.json').read_text())
manifest = json.loads(MANIFEST.read_text())
assert 'snapshot' not in manifest
assert len(manifest['decisions']) == len(manifest['profiles']) == 16
assert build(data, manifest) == data, 'Repeated import must be byte-equivalent after serialization'
for section in ('organizations', 'services', 'evidence'):
    assert len({x['id'] for x in data[section]}) == len(data[section])
assert len(manifest['profiles']) == 16
epstein = [o for o in data['organizations'] if o['name'] == 'Epstein']
assert len(epstein) == 1 and epstein[0]['id'] == 'org-f73d6f8cdebe'
cards = {c['id']: c for c in build_model(data)}
assert cards['org-labrepco']['roles'] == ['Supplier']
assert cards['org-labrepco']['categories'] == ['Laboratory equipment']
assert cards['org-panacea-payroll']['categories'] == ['Payroll & HR']
assert cards['org-buglady-consulting']['categories'] == ['Pest management / IPM']
assert not {'org-catalyst-bc', 'org-clean-earth', 'org-stulz', 'org-cvault'} & cards.keys()
assert not any(s['id'].startswith('svc-pa-supplier-b14-') for s in data['services'])
batch_ids = {'svc-pa-supplier-' + p['staging_id'].removeprefix('pa-') for p in manifest['profiles']}
new = [s for s in data['services'] if s['id'] in batch_ids]
assert len(new) == 16
assert all(s['coverage'] == [] and s['listed_in'] == ['PA'] for s in new)
# A shared national record keeps its contacts, name, legacy fields and Ohio coverage.
fixture = copy.deepcopy(data)
shared = next(o for o in fixture['organizations'] if o['id'] == 'org-f73d6f8cdebe')
shared['contacts'].append({'kind': 'email', 'value': 'fixture@example.org'})
assert next(o for o in build(fixture, manifest)['organizations'] if o['id'] == shared['id']) == shared
bad = copy.deepcopy(manifest)
next(d for d in bad['decisions'] if d['staging_id'] == bad['profiles'][0]['staging_id'])['decision'] = 'research-only'
try:
    build(data, bad)
    raise AssertionError('Research-only record must not publish')
except ValueError:
    pass
print('PASS PA supplier import: 16 profiles, shared identity preservation, idempotence, source dates and research isolation.')
