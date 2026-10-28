"""Import the reviewed Pennsylvania ecosystem manifest into the canonical directory; no network access.

The manifest (data/sources/pennsylvania-ecosystem-2026-10-28.json) holds every new Pennsylvania
organization, service, rule and claim with the page that supports it. Sources reread on the
manifest date carry that review date; sources reused from the October 24 research batch keep
their original review date. Running the importer twice leaves the canonical tree unchanged.
"""
import hashlib,json
from directory_data import ROOT
MANIFEST=ROOT/'data/sources/pennsylvania-ecosystem-2026-10-28.json'
RESEARCH=ROOT/'data/research/pennsylvania-2026-10-24-sources.json'
DIRECTORY=ROOT/'data/directory.json'
KIND={'official':'government','first-party':'provider','provider':'provider','secondary':'secondary','government':'government'}
PREFIX='ev-pa26-'

def evidence_id(subject,claim,source,value):
 return PREFIX+hashlib.sha256('|'.join((subject,claim,source,value)).encode()).hexdigest()[:12]

def resolve_sources(manifest):
 sources={}
 for key,s in manifest['sources'].items():
  sources[key]=dict(url=s['url'],source_kind=s['source_kind'],reviewed_on=manifest['reviewed_on'],limitations=s['limitations'])
 for s in json.loads(RESEARCH.read_text())['sources']:
  if s.get('retrieval_status')!='reviewed' or not s.get('reviewed_on'):continue
  sources.setdefault(s['id'],dict(url=s['url'],source_kind=KIND[s['source_kind']],reviewed_on=s['reviewed_on'],limitations=s['limitations']))
 return sources

def make_evidence(subject,spec,sources,recheck):
 src=sources[spec['source']]
 return dict(id=evidence_id(subject,spec['claim'],spec['source'],spec['value']),subject_id=subject,claim=spec['claim'],value=spec['value'],source_url=src['url'],source_kind=src['source_kind'],status='source-reviewed',reviewed_on=src['reviewed_on'],recorded_on=src['reviewed_on'],recheck_on=recheck,limitations=(spec['limitations']+' '+src['limitations']) if 'limitations' in spec else src['limitations'])

def build(data,manifest):
 sources=resolve_sources(manifest);recheck=manifest['recheck_on']
 orgs={o['id']:o for o in data['organizations']}
 for spec in manifest['organizations']:
  org=orgs.get(spec['id'])
  if org is None:
   org=dict(id=spec['id'],name=spec['name'],kind=spec['kind'],legacy_ids=[],contacts=[]);data['organizations'].append(org);orgs[org['id']]=org
  if 'legacy_record' in org:raise ValueError(f'{spec["id"]}: manifest must not overwrite an Ohio directory record')
  org.update(name=spec['name'],kind=spec['kind'],website=spec['website'],contacts=spec['contacts'],scope='public')
  if not org['website']:org.pop('website')
 service_ids={s['id'] for s in manifest['services']};rule_ids={r['id'] for r in manifest['rules']}
 data['services']=[s for s in data['services'] if s['id'] not in service_ids]
 data['rules']=[r for r in data['rules'] if r['id'] not in rule_ids]
 data['evidence']=[e for e in data['evidence'] if not (e['id'].startswith(PREFIX) and (e['subject_id'] in service_ids or e['subject_id'] in rule_ids))]
 new_evidence=[]
 for spec in manifest['services']:
  if spec['organization_id'] not in orgs:raise ValueError(f'{spec["id"]}: unknown organization')
  sid=spec['id'];evidence=[make_evidence(sid,e,sources,recheck) for e in spec['evidence']];coverage=[]
  for geo in spec.get('coverage',[]):
   ev=make_evidence(sid,dict(claim='service-coverage',source=geo['source'],value=geo['value']),sources,recheck)
   if ev['id'] not in {e['id'] for e in evidence}:evidence.append(ev)
   coverage.append({k:geo[k] for k in ('kind','state','county') if k in geo}|{'evidence_ids':[ev['id']]})
  attributes={}
  if 'provider_details' in spec:
   d=spec['provider_details'];src=sources[d['source']]
   ev=make_evidence(sid,dict(claim='provider-contact',source=d['source'],value=d['contact_note']),sources,recheck);evidence.append(ev)
   attributes['provider_details']=dict(serves=d['serves'],coverage_note=d['coverage_note'],contact_note=d['contact_note'],source_url=src['url'].replace('http://','https://',1),reviewed_on=src['reviewed_on'])
   ev['source_url']=attributes['provider_details']['source_url']
  data['services'].append(dict(id=sid,organization_id=spec['organization_id'],location_ids=[],pathway_ids=spec['pathway_ids'],name=spec['name'],coverage=coverage,audiences=spec['audiences'],eligibility=spec['eligibility'],next_step=spec['next_step'],availability='unknown',attributes=attributes,fulfillment=[],evidence_ids=[e['id'] for e in evidence],origin=spec.get('origin','organization-profile'),listed_in=['PA'],description=spec['description']))
  new_evidence+=evidence
 for spec in manifest['rules']:
  evidence=[make_evidence(spec['id'],e,sources,recheck) for e in spec['evidence']]
  data['rules'].append(dict(id=spec['id'],state='PA',topic=spec['topic'],summary=spec['summary'],effective_on=spec['effective_on'],evidence_ids=[e['id'] for e in evidence],next_step_url=spec['next_step_url']))
  new_evidence+=evidence
 data['evidence']+=new_evidence
 pa=next(s for s in data['states'] if s['code']=='PA')
 for p in pa['pathways']:
  key=p['pathway_id']
  if key in manifest['pathways']:
   p.clear();p.update(pathway_id=key,**manifest['pathways'][key])
 pa['reviewed_on']=max(pa['reviewed_on'],manifest['reviewed_on'])
 return data

def main():
 data=json.loads(DIRECTORY.read_text());manifest=json.loads(MANIFEST.read_text())
 build(data,manifest)
 DIRECTORY.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
 print(f'Imported Pennsylvania ecosystem: {len(manifest["organizations"])} organizations, {len(manifest["services"])} services, {len(manifest["rules"])} rules')
if __name__=='__main__':main()
