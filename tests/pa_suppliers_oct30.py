"""Expansion batches preserve each other, shared Ohio profiles and source-specific limits."""
import copy
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from import_pa_suppliers_oct30 import build, MANIFEST
from import_pa_suppliers import build as previous_import, MANIFEST as PREVIOUS
from build_pa_companies import build_model

data = json.loads((ROOT / 'data/directory.json').read_text())
manifest = json.loads(MANIFEST.read_text())
prior = json.loads(PREVIOUS.read_text())
assert len(manifest['profiles']) == 6
assert build(data, manifest) == data
assert previous_import(data, prior) == data, 'Older batch must preserve later additions and order'
assert build(previous_import(data, prior), manifest) == data
assert previous_import(build(data, manifest), prior) == data
cards = {c['id']:c for c in build_model(data)}
assert len(cards) == 100
assert cards['org-hitechtrader']['roles'] == ['Supplier']
assert cards['org-2b1d7f43aa6e']['categories'] == ['Logistics & distribution']
assert cards['org-547f01a174ca']['categories'] == ['Facility design & climate']
assert 'org-445c487eef5d' not in cards, 'Retained Ohio identity needs a separate PA-publication resolution'
fixture = copy.deepcopy(data)
arco = next(o for o in fixture['organizations'] if o['id'] == 'org-547f01a174ca')
arco['legacy_record']['Notes'] = 'Fixture: preserve separately reviewed Ohio profile'
assert next(o for o in build(fixture, manifest)['organizations'] if o['id'] == arco['id']) == arco
ids = {'svc-pa-supplier-' + p['staging_id'].removeprefix('pa-') for p in manifest['profiles']}
services = [s for s in data['services'] if s['id'] in ids]
assert len(services) == 6 and all(s['coverage'] == [] and s['availability'] == 'unknown' for s in services)
assert all(s['listed_in'] == ['PA'] for s in services)
assert len([s for s in data['services'] if 'PA' in s.get('listed_in',[])]) == 154
for kind in ('organizations','services','evidence'):
 assert len({x['id'] for x in data[kind]}) == len(data[kind])
assert any(f['value']=='sales@hitechtrader.com' for f in cards['org-hitechtrader']['facts'])
assert any('separate facts' in s['limitations'] for s in cards['org-dellinger-horticulture']['sources'])
assert any('placeholder' in s['limitations'] for s in cards['org-innovative-industrial-properties']['sources'])
print('PASS October 30 PA expansion: six profiles, stable multi-batch imports, reused identities, scoped claims and contacts.')
