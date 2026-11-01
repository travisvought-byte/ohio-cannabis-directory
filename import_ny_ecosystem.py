"""Import the reviewed New York ecosystem manifest into the canonical directory; no network access.

The manifest (data/sources/new-york-ecosystem-2026-11-01.json) holds every New York organization,
service, rule and event with the page that supports each claim. It follows the Pennsylvania
manifest pattern (import_pa_ecosystem.py) and adds dated events. Running it twice leaves the
canonical tree unchanged.
"""
import hashlib,json
from directory_data import ROOT
from import_pa_ecosystem import upsert
MANIFEST=ROOT/'data/sources/new-york-ecosystem-2026-11-01.json'
DIRECTORY=ROOT/'data/directory.json'
STATE='NY'
PREFIX='ev-ny26-'
def evidence_id(subject,claim,source,value):
 return PREFIX+hashlib.sha256('|'.join((subject,claim,source,value)).encode()).hexdigest()[:12]
def make_evidence(subject,spec,sources,reviewed,recheck):
 src=sources[spec['source']]
 return dict(id=evidence_id(subject,spec['claim'],spec['source'],spec['value']),subject_id=subject,claim=spec['claim'],value=spec['value'],source_url=src['url'],source_kind=src['source_kind'],status='source-reviewed',reviewed_on=reviewed,recorded_on=reviewed,recheck_on=recheck,limitations=(spec['limitations']+' '+src['limitations']) if 'limitations' in spec else src['limitations'])
def build(data,manifest):
 sources=manifest['sources'];reviewed=manifest['reviewed_on'];recheck=manifest['recheck_on']
 ev=lambda subject,spec:make_evidence(subject,spec,sources,reviewed,recheck)
 orgs={o['id']:o for o in data['organizations']}
 for spec in manifest['organizations']:
  org=orgs.get(spec['id'])
  if org is None:
   org=dict(id=spec['id'],name=spec['name'],kind=spec['kind'],legacy_ids=[],contacts=[]);data['organizations'].append(org);orgs[org['id']]=org
  if 'legacy_record' in org:raise ValueError(f'{spec["id"]}: manifest must not overwrite an Ohio directory record')
  org.update(name=spec['name'],kind=spec['kind'],website=spec['website'],contacts=spec['contacts'],scope='public')
 new_services=[];new_rules=[];new_events=[];new_evidence=[]
 for spec in manifest['services']:
  if spec['organization_id'] not in orgs:raise ValueError(f'{spec["id"]}: unknown organization')
  sid=spec['id'];evidence=[ev(sid,e) for e in spec['evidence']];coverage=[]
  for geo in spec.get('coverage',[]):
   if geo.get('state')!=STATE:raise ValueError(f'{sid}: coverage outside New York')
   e=ev(sid,dict(claim='service-coverage',source=geo['source'],value=geo['value']))
   if e['id'] not in {x['id'] for x in evidence}:evidence.append(e)
   coverage.append({k:geo[k] for k in ('kind','state','county') if k in geo}|{'evidence_ids':[e['id']]})
  attributes={}
  if 'provider_details' in spec:
   d=spec['provider_details'];src=sources[d['source']]
   e=ev(sid,dict(claim='provider-contact',source=d['source'],value=d['contact_note']));evidence.append(e)
   attributes['provider_details']=dict(serves=d['serves'],coverage_note=d['coverage_note'],contact_note=d['contact_note'],source_url=src['url'],reviewed_on=reviewed)
  new_services.append(dict(id=sid,organization_id=spec['organization_id'],location_ids=[],pathway_ids=spec['pathway_ids'],name=spec['name'],coverage=coverage,audiences=spec['audiences'],eligibility=spec['eligibility'],next_step=spec['next_step'],availability='unknown',attributes=attributes,fulfillment=[],evidence_ids=[e['id'] for e in evidence],origin='organization-profile',listed_in=[STATE],description=spec['description']))
  new_evidence+=evidence
 for spec in manifest['rules']:
  evidence=[ev(spec['id'],e) for e in spec['evidence']]
  new_rules.append(dict(id=spec['id'],state=STATE,topic=spec['topic'],summary=spec['summary'],effective_on=spec['effective_on'],evidence_ids=[e['id'] for e in evidence],next_step_url=spec['next_step_url']))
  new_evidence+=evidence
 for spec in manifest['events']:
  if any(o not in orgs for o in spec['organization_ids']):raise ValueError(f'{spec["id"]}: unknown organizer')
  evidence=[ev(spec['id'],e) for e in spec['evidence']]
  new_events.append(dict(id=spec['id'],name=spec['name'],state=STATE,starts_on=spec['starts_on'],ends_on=spec['ends_on'],organization_ids=spec['organization_ids'],next_step_url=spec['next_step_url'],evidence_ids=[e['id'] for e in evidence]))
  new_evidence+=evidence
 subjects={x['id'] for x in new_services+new_rules+new_events}
 data['services']=upsert(data['services'],new_services)
 data['rules']=upsert(data['rules'],new_rules)
 data['events']=upsert(data['events'],new_events)
 kept=[e for e in data['evidence'] if not (e['id'].startswith(PREFIX) and e['subject_id'] in subjects and e['id'] not in {n['id'] for n in new_evidence})]
 data['evidence']=upsert(kept,new_evidence)
 return data
def main():
 data=json.loads(DIRECTORY.read_text());manifest=json.loads(MANIFEST.read_text())
 build(data,manifest)
 DIRECTORY.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
 print(f'Imported New York ecosystem: {len(manifest["organizations"])} organizations, {len(manifest["services"])} services, {len(manifest["rules"])} rules, {len(manifest["events"])} events')
if __name__=='__main__':main()
