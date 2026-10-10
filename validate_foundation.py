"""Validate the shared contract and references; never infer missing coverage."""
import argparse,json
from datetime import date
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
ROOT=Path(__file__).resolve().parent
STATE_CODES=set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC'.split())
COLLECTIONS=('organizations','locations','services','evidence','rules','relationships','events')
def validate(data):
 schema=json.loads((ROOT/'schemas/directory.schema.json').read_text())
 Draft202012Validator.check_schema(schema)
 errors=[f'{"/".join(map(str,e.absolute_path))}: {e.message}' for e in Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(data)]
 if errors:return errors
 as_of=date.fromisoformat(data['as_of']);lookup={};groups={}
 for collection in COLLECTIONS:
  groups[collection]={}
  for item in data[collection]:
   key=item['id']
   if key in lookup:errors.append(f'Duplicate identity: {key}')
   lookup[key]=item;groups[collection][key]=item
 pathways={p['id'] for p in data['pathways']}
 if len(pathways)!=len(data['pathways']):errors.append('Duplicate pathway ID')
 codes=[s['code'] for s in data['states']]
 if len(codes)!=len(set(codes)):errors.append('Duplicate state code')
 def require(key,group,context):
  if key not in groups[group]:errors.append(f'{context}: missing {group} reference {key}')
 def evidence_refs(item):
  refs=item.get('evidence_ids',[])
  for key in refs:
   require(key,'evidence',item['id'])
   if key in groups['evidence'] and groups['evidence'][key]['subject_id']!=item['id']:errors.append(f'{item["id"]}: evidence {key} belongs to another subject')
  return refs
 for item in data['locations']:
  require(item['organization_id'],'organizations',item['id'])
  if item['state'] not in STATE_CODES:errors.append(f'{item["id"]}: invalid state')
  if ('latitude' in item)!=('longitude' in item):errors.append(f'{item["id"]}: coordinates require both latitude and longitude')
  refs=evidence_refs(item)
  if not refs:errors.append(f'{item["id"]}: a published location requires evidence')
  if item.get('license',{}).get('status')=='active' and not any(groups['evidence'].get(k,{}).get('source_kind')=='government' for k in refs):errors.append(f'{item["id"]}: active license requires government evidence')
 for item in data['services']:
  if any(code not in STATE_CODES for code in item.get('listed_in',[])):errors.append(f'{item["id"]}: invalid editorial state membership')
  require(item['organization_id'],'organizations',item['id'])
  if not item['pathway_ids']:errors.append(f'{item["id"]}: service needs a visitor pathway')
  for p in item['pathway_ids']:
   if p not in pathways:errors.append(f'{item["id"]}: unknown pathway {p}')
  for loc in item['location_ids']:
   require(loc,'locations',item['id'])
   if loc in groups['locations'] and groups['locations'][loc]['organization_id']!=item['organization_id']:errors.append(f'{item["id"]}: location belongs to another organization')
  for geo in item['coverage']:
   for key in geo['evidence_ids']:
    require(key,'evidence',item['id'])
    ev=groups['evidence'].get(key,{})
    if ev.get('subject_id')!=item['id'] or ev.get('claim')!='service-coverage':errors.append(f'{item["id"]}: coverage needs service-coverage evidence for this service')
   if geo['kind'] in ('state','county') and geo.get('state') not in STATE_CODES:errors.append(f'{item["id"]}: state/county coverage requires a valid state')
   if geo['kind']=='county' and not geo.get('county'):errors.append(f'{item["id"]}: county coverage requires a county')
   if geo['kind'] in ('national','online') and ('state' in geo or 'county' in geo):errors.append(f'{item["id"]}: national/online coverage cannot carry local fields')
  refs=evidence_refs(item)
  if item['availability']=='confirmed' and not refs:errors.append(f'{item["id"]}: confirmed service requires evidence')
  for f in item['fulfillment']:
   for key in f['evidence_ids']:require(key,'evidence',item['id'])
   if f['status'] in ('confirmed','seller-stated','manufacturer-listed') and not f['evidence_ids']:errors.append(f'{item["id"]}: fulfillment status requires evidence')
   if f['status'] in ('confirmed','seller-stated','manufacturer-listed'):
    for key in f['evidence_ids']:
     ev=groups['evidence'].get(key,{})
     if ev.get('subject_id')!=item['id'] or ev.get('claim')!='fulfillment-'+f['kind'] or ev.get('status') not in ('source-reviewed','firsthand-confirmed','source-listed'):errors.append(f'{item["id"]}: fulfillment requires matching claim-level evidence')
 for ev in data['evidence']:
  if ev['subject_id'] not in lookup or ev['subject_id'] in groups['evidence']:errors.append(f'{ev["id"]}: missing evidence subject')
  if ev.get('reviewed_on') and date.fromisoformat(ev['reviewed_on'])>as_of:errors.append(f'{ev["id"]}: future review date')
  if ev.get('reviewed_on') and date.fromisoformat(ev['recheck_on'])<date.fromisoformat(ev['reviewed_on']):errors.append(f'{ev["id"]}: recheck precedes review')
 for item in data['rules']:
  refs=evidence_refs(item)
  if item['state'] not in STATE_CODES:errors.append(f'{item["id"]}: invalid rule state')
  if not refs or not any(groups['evidence'].get(k,{}).get('source_kind')=='government' for k in refs):errors.append(f'{item["id"]}: rule requires official evidence')
 for item in data['relationships']:
  for field in ('organization_a_id','organization_b_id'):require(item[field],'organizations',item['id'])
  if item['organization_a_id']==item['organization_b_id']:errors.append(f'{item["id"]}: self relationship')
  if not evidence_refs(item):errors.append(f'{item["id"]}: relationship requires evidence')
 for item in data['events']:
  if item['state'] not in STATE_CODES:errors.append(f'{item["id"]}: invalid event state')
  if item['ends_on']<item['starts_on']:errors.append(f'{item["id"]}: event ends before it starts')
  for org in item['organization_ids']:require(org,'organizations',item['id'])
  if not evidence_refs(item):errors.append(f'{item["id"]}: event requires evidence')
 for item in data['states']:
  if item['code'] not in STATE_CODES:errors.append(f'{item["code"]}: invalid state code')
  if date.fromisoformat(item['reviewed_on'])>as_of:errors.append(f'{item["code"]}: future review date')
  ids=[p['pathway_id'] for p in item['pathways']]
  if len(ids)!=len(set(ids)):errors.append(f'{item["code"]}: duplicate pathway coverage')
  if set(ids)!=pathways:errors.append(f'{item["code"]}: state must report coverage for every shared pathway')
  if item['publication_status'] in ('live','pilot') and not item.get('official_regulator_url'):errors.append(f'{item["code"]}: public state needs official regulator')
  if item['publication_status'] in ('live','pilot') and not any(p['coverage_status']!='not-reviewed' and p.get('public_url') for p in item['pathways']):errors.append(f'{item["code"]}: public state needs at least one reviewed actionable route')
  for p in item['pathways']:
   if p.get('public_url') and (item['publication_status'] not in ('live','pilot') or p['coverage_status']=='not-reviewed'):errors.append(f'{item["code"]}: unreviewed route cannot be public')
 for alias in data.get('aliases',[]):
  require(alias['new_id'],'organizations','alias')
  if alias['old_id'] in lookup:errors.append('Alias old identity must not duplicate an active record')
 if len({a['old_id'] for a in data.get('aliases',[])})!=len(data.get('aliases',[])):errors.append('Duplicate alias')
 return errors
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('file',nargs='?',default=str(ROOT/'data/foundation/directory.json'));args=parser.parse_args()
 data=json.loads(Path(args.file).read_text());errors=validate(data)
 if errors:raise SystemExit('\n'.join(errors))
 print(f'PASS shared contract: {len(data["organizations"])} organizations, {len(data["services"])} services, {len(data["evidence"])} evidence references, {len(data["pathways"])} pathways. Scope: {data["scope"]}; physical locations: {len(data["locations"])}.')
