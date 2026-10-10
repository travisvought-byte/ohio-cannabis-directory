"""Test lossless migration, aliases, shared templates and publication isolation."""
import copy,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from directory_data import load_directory,load_records,load_relationship_records,load_seed_records,relationship_id
from build_state import build_page
from validate_foundation import validate
import re

def csvrows(name):return list(csv.DictReader((ROOT/name).open(encoding='utf-8-sig')))
data=load_directory();assert not validate(data)
assert load_records()==csvrows('ohio-cannabis-directory.csv')
assert load_relationship_records()==csvrows('b2b-relationships.csv')
assert load_seed_records()==json.loads((ROOT/'seed-suppliers.json').read_text())
assert len(load_records())==564 and len(load_relationship_records())==60
assert [r['id'] for r in data['relationships']]==[relationship_id(r) for r in load_relationship_records()]
assert len({o['id'] for o in data['organizations']})==len(data['organizations'])
assert sum(o.get('legacy_record',{}).get('Record ID')==o['id'] for o in data['organizations'] if 'legacy_record' in o)==564
assert sum(o['name']=='Indoor Gardens' for o in data['organizations'])==1
assert sum(a['old_id'].startswith('org-seed') for a in data['aliases'])==1
assert all(not s['coverage'] for s in data['services'] if s['origin']=='organization-profile')
assert all(e['status']=='source-listed' for e in data['evidence'] if e['claim']=='organization-profile')
# The same renderer accepts another state pack without copied code. Fixtures never publish.
fixture=copy.deepcopy(data);pa=copy.deepcopy(fixture['states'][0]);pa.update(code='PA',name='Pennsylvania',publication_status='research-only');
for p in pa['pathways']:p.pop('public_url',None);p['coverage_status']='not-reviewed'
fixture['states'].append(pa);assert not validate(fixture)
page=build_page(fixture);assert '<option value="PA">' not in page
pa.update(publication_status='pilot',official_regulator_url='https://example.org/test-regulator');pa['pathways'][0].update(coverage_status='starter',public_url='https://example.org/test-route');assert not validate(fixture)
assert '<option value="PA">Pennsylvania (pilot)</option>' in build_page(fixture)
assert all('PA' not in s.get('listed_in',[]) for s in fixture['services'])
# A profile source cannot support a shipping badge.
bad=copy.deepcopy(data);seed=next(s for s in bad['services'] if s.get('origin')=='seed-profile');seed['fulfillment'][0]['status']='confirmed';assert any('matching claim-level evidence' in e for e in validate(bad))
print('PASS migration: exact legacy exports, stable IDs, 60 relationship IDs, seed aliases, conservative coverage and state-template isolation.')
