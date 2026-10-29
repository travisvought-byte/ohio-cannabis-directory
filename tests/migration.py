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
assert load_records(include_withdrawn=False)==csvrows('ohio-cannabis-directory.csv')
assert load_relationship_records()==csvrows('b2b-relationships.csv')
assert load_seed_records()==json.loads((ROOT/'seed-suppliers.json').read_text())
assert len(load_records())==565 and len(load_relationship_records())==60
assert [r['id'] for r in data['relationships']]==[relationship_id(r) for r in load_relationship_records()]
assert len({o['id'] for o in data['organizations']})==len(data['organizations'])
assert sum(o.get('legacy_record',{}).get('Record ID')==o['id'] for o in data['organizations'] if 'legacy_record' in o)==565
assert sum(o['name']=='Indoor Gardens' for o in data['organizations'])==1
assert sum(a['old_id'].startswith('org-seed') for a in data['aliases'])==1
# Legacy Ohio profiles keep conservative coverage; Pennsylvania services carry their own claim-level coverage.
assert all(not s['coverage'] for s in data['services'] if s['origin']=='organization-profile' and 'OH' in s.get('listed_in',[]) and s['id']!='svc-profile-36e94688f898')
# New Ohio coverage is backed by reviewed first-party claim-level evidence.
dizpot=next(s for s in data['services'] if s['id']=='svc-profile-36e94688f898')
assert dizpot['coverage']==[{'kind':'state','state':'OH','evidence_ids':['ev-dizpot-ohio-20261022']}]
assert next(e for e in data['evidence'] if e['id']=='ev-dizpot-ohio-20261022')['status']=='source-reviewed'
assert all(e['status']=='source-listed' for e in data['evidence'] if e['claim']=='organization-profile' and e['id']!='ev-dizpot-profile-20261022')
# The same renderer accepts another state pack without copied code. Fixtures never publish.
public_state_before=(ROOT/'data/public-state.json').read_bytes()
fixture=copy.deepcopy(data);state_fixture=copy.deepcopy(fixture['states'][0]);state_fixture.update(code='WA',name='Washington',publication_status='research-only');
for p in state_fixture['pathways']:p.pop('public_url',None);p['coverage_status']='not-reviewed'
fixture['states'].append(state_fixture);assert not validate(fixture)
page=build_page(fixture);assert '<option value="WA">' not in page
state_fixture.update(publication_status='pilot',official_regulator_url='https://example.org/test-regulator');state_fixture['pathways'][0].update(coverage_status='starter',public_url='https://example.org/test-route');assert not validate(fixture)
assert '<option value="WA">Washington (pilot)</option>' in build_page(fixture)
assert all('WA' not in s.get('listed_in',[]) for s in fixture['services'])
assert (ROOT/'data/public-state.json').read_bytes()==public_state_before, 'Fixture render must not overwrite public state data'
# The real Pennsylvania pilot reports every pathway with reviewed routes and states its gaps.
pa_pack=next(s for s in data['states'] if s['code']=='PA')
assert pa_pack['publication_status']=='pilot'
assert {p['pathway_id']:p['coverage_status'] for p in pa_pack['pathways']}=={'dispensaries':'broad','seeds':'starter','records':'partial','rules':'starter','medical':'partial','business':'partial','community':'partial'}
assert {p['pathway_id'] for p in pa_pack['pathways'] if p.get('public_url')}=={'dispensaries','seeds','records','rules','medical','business'}
pa_services=[s for s in data['services'] if 'PA' in s.get('listed_in',[])]
assert len(pa_services)==148
orgs={o['id']:o for o in data['organizations']}
assert all(orgs[s['organization_id']]['scope']=='public' for s in pa_services)
assert all(s['listed_in']==['PA'] for s in pa_services)
assert all(s['evidence_ids'] for s in pa_services)
evidence={e['id']:e for e in data['evidence']}
assert all(evidence[k]['claim']=='service-coverage' and evidence[k]['subject_id']==s['id'] for s in pa_services for g in s['coverage'] for k in g['evidence_ids'])
assert all(all(evidence[k]['status']=='source-reviewed' and evidence[k]['reviewed_on'] in ('2026-10-24','2026-10-28','2026-10-29') for k in s['evidence_ids']) for s in pa_services)
# Pennsylvania services never write Pennsylvania text onto Ohio directory records.
pa_details={json.dumps(s['attributes']['provider_details'],sort_keys=True) for s in pa_services if s['attributes'].get('provider_details')}
ohio_cards=json.loads((ROOT/'data/public-organizations.json').read_text())
assert pa_details and not any(json.dumps(r.get('provider'),sort_keys=True) in pa_details for r in ohio_cards)
assert not any(s['id']=='svc-pa-lab-act' for s in pa_services if s['organization_id']!='org-439251489828')
pa_rules=[r for r in data['rules'] if r['state']=='PA']
assert {r['topic'] for r in pa_rules}=={'medical-use','adult-use-possession','home-grow','employment','driving','record-sealing'}
assert all(any(evidence[k]['source_kind']=='government' for k in r['evidence_ids']) for r in pa_rules)
intake=next(s for s in pa_services if s['id']=='svc-pa-npls-record-help')
assert {(c['state'],c['county']) for c in intake['coverage']}=={('PA','Monroe'),('PA','Pike')}
lasp=next(s for s in pa_services if s['id']=='svc-pa-lasp-record-clearing')
assert {c['county'] for c in lasp['coverage']}=={'Bucks','Chester','Delaware','Montgomery'}
# Repeating the import changes nothing.
from import_pa_ecosystem import build as import_pa,MANIFEST
# The baseline importer remains repeatable and preserves separately reviewed additions.
again=import_pa(copy.deepcopy(data),json.loads(MANIFEST.read_text()))
assert import_pa(copy.deepcopy(again),json.loads(MANIFEST.read_text()))==again
base_ids={s['id'] for s in json.loads(MANIFEST.read_text())['services']}
assert all(next(a for a in again['services'] if a['id']==s['id'])==s for s in pa_services if s['id'] in base_ids)
new_services=[s for s in pa_services if s['id'].startswith('svc-pa-drive-')]
assert len(new_services)==76
assert all(next(a for a in again['services'] if a['id']==s['id'])==s for s in new_services)
assert all(next(o for o in again['organizations'] if o['id']==s['organization_id'])==orgs[s['organization_id']] for s in new_services)
assert not next(s for s in new_services if s['id']=='svc-pa-drive-b5-inland')['coverage'], 'A PA facility must not imply statewide coverage'
assert next(s for s in new_services if s['id']=='svc-pa-drive-b2-dutchie')['organization_id']=='org-a06c1362a303'
assert next(s for s in new_services if s['id']=='svc-pa-drive-b6-summit')['organization_id']==next(s for s in new_services if s['id']=='svc-pa-drive-b6-washington-pardon')['organization_id']
public_state=json.loads(public_state_before)
assert 'PA' in {s['code'] for s in public_state['states']}
assert {s['id'] for s in pa_services}=={s['id'] for s in public_state['cards'] if 'PA' in s['listed_in']}
assert not any('PA' in c['listed_in'] and 'OH' in c['listed_in'] for c in public_state['cards'])
# A reverted research pack remains hidden: publication still requires an explicit promotion.
hidden=copy.deepcopy(data);hidden_pa=next(s for s in hidden['states'] if s['code']=='PA');hidden_pa['publication_status']='research-only'
for p in hidden_pa['pathways']:p.pop('public_url',None)
for o in hidden['organizations']:
 if o['id'] in {s['organization_id'] for s in pa_services}:o['scope']='reference-only'
assert not validate(hidden)
assert '<option value="PA">' not in build_page(hidden)
public_locations=json.loads((ROOT/'data/public-locations.json').read_text())
assert sum(l['state']=='PA' for l in public_locations['locations'])==200
assert not any(l['state']=='PA' and l.get('organization_id')=='org-north-penn-legal-services' for l in public_locations['locations']),'Referral offices are not dispensaries'
# A profile source cannot support a shipping badge.
bad=copy.deepcopy(data);seed=next(s for s in bad['services'] if s.get('origin')=='seed-profile');seed['fulfillment'][0]['status']='confirmed';assert any('matching claim-level evidence' in e for e in validate(bad))
print('PASS migration: exact legacy exports, stable IDs, 60 relationship IDs, seed aliases, conservative coverage and state-template isolation.')
