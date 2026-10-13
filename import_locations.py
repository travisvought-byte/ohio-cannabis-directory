"""Import a saved government snapshot; no network access or freshness assumptions."""
import hashlib,json,re
from location_validation import validate_location_fields
from directory_data import ROOT
SOURCE=ROOT/'data/sources/ohio-dispensaries.json'
CONTACTS=ROOT/'data/sources/location-contacts.json'
def stable(prefix,value):return prefix+hashlib.sha256(value.encode()).hexdigest()[:12]
def normalize_row(row):
 r=dict(row)
 for key,value in r.items():
  if isinstance(value,str):r[key]=' '.join(value.split())
 for correction in json.loads((ROOT/'data/sources/location-corrections.json').read_text()):
  if r['user_licen']!=correction['license']:continue
  if all(r.get(k)==v for k,v in correction['original'].items()):r.update(correction['corrected'])
  elif not all(r.get(k)==v for k,v in correction['corrected'].items()):raise ValueError('Source changed; re-review correction '+r['user_licen'])
 return r
def import_snapshot(data,snapshot):
 response=snapshot['response']
 if response.get('error') or response.get('exceededTransferLimit'):raise ValueError('Incomplete source response')
 rows=[normalize_row(f['attributes']) for f in response['features']]
 for r in rows:validate_location_fields({'state':'OH','county':r['user_count'],'city':r['user_city'],'name':r['user_dispe'] or r['user_busin'],'address':r['user_stree'],'postal_code':str(r['user_zip'])})
 licenses=[r['user_licen'] for r in rows]
 if len(set(licenses))!=len(licenses) or not all(licenses):raise ValueError('Duplicate or missing license identity')
 for r in rows:
  if r['user_state'] not in ('Ohio','OH'):raise ValueError('Unexpected source state')
  r=dict(r);r['user_dispe']=r.get('user_dispe') or r['user_busin']
  legal=r['user_busin'].strip(); oid=stable('org-','ohio-location-legal:'+legal.casefold())
  matches=[o for o in data['organizations'] if o['name'].strip().casefold()==legal.casefold()]
  if len(matches)==1:oid=matches[0]['id']
  elif not any(o['id']==oid for o in data['organizations']):data['organizations'].append({'id':oid,'name':legal,'kind':'operator','scope':'public','legacy_ids':[],'contacts':[]})
  lid=stable('loc-','OH:'+r['user_licen']);eid=stable('ev-',lid+':government-location')
  lat,lon=r['user_lat'],r['user_lon']
  valid_coordinates=isinstance(lat,(int,float)) and isinstance(lon,(int,float)) and 38<=lat<=43 and -85<=lon<=-80
  location={'id':lid,'organization_id':oid,'name':r['user_dispe'],'state':'OH','county':r['user_count'],'city':r['user_city'],'address':r['user_stree'],'postal_code':str(r['user_zip']).zfill(5),'latitude':lat,'longitude':lon,'license':{'number':r['user_licen'],'regulator':'Ohio Division of Cannabis Control','kind':'dual-use' if r['licensetype'] in ('Dual','Dual Use','Dual Use Dispensary') else 'other','status':'unknown'},'evidence_ids':[eid]}
  phone=str(r.get('user_phone') or '').strip()
  digits=re.sub(r'\D','',phone)
  if len(digits)==10 or (len(digits)==11 and digits.startswith('1')):
   location['snapshot_phone']=phone
  if not valid_coordinates:
   location.pop('latitude');location.pop('longitude')
  # Source-listed is deliberately distinct from a current license verification.
  evidence={'id':eid,'subject_id':lid,'claim':'government-location-snapshot','value':r['user_dispe']+'; '+r['user_stree']+'; source license label '+r['user_lic_1'],'source_url':snapshot['source_url'],'source_kind':'government','status':'source-listed','recorded_on':snapshot['retrieved_on'],'recheck_on':'2026-11-09','limitations':snapshot['limitations']}
  correction=next((c for c in json.loads((ROOT/'data/sources/location-corrections.json').read_text()) if c['license']==r['user_licen']),None)
  if correction:evidence['limitations']+=' Field correction reviewed '+correction['reviewed_on']+': '+correction['reason']+' Supporting source: '+correction['source_url']
  for key,item in [('locations',location),('evidence',evidence)]:
   existing=next((i for i,x in enumerate(data[key]) if x['id']==item['id']),None)
   if existing is None:data[key].append(item)
   else:data[key][existing]=item
 apply_contact_reviews(data)
 return len(rows)

def apply_contact_reviews(data):
 if not CONTACTS.exists():return
 locations={l['license']['number']:l for l in data['locations'] if l.get('license')}
 organizations={o['id']:o for o in data['organizations']}
 for review in json.loads(CONTACTS.read_text())['reviews']:
  location=locations.get(review['license'])
  if not location or any(location.get(k)!=v for k,v in review['expected_location'].items()):
   raise ValueError('Location changed; re-review store contact '+review['license'])
  linked=organizations.get(review['directory_organization_id'])
  if not linked or linked.get('scope')!='public' or 'legacy_record' not in linked:
   raise ValueError('Store contact needs a public directory listing: '+review['license'])
  location['contact']={k:review[k] for k in ['public_name','website','phone','reviewed_on','directory_organization_id']}
  if review.get('menu_links'):
   location['contact'].update({k:review[k] for k in ['menu_links','menu_source_url','menu_reviewed_on']})
   menu_id=stable('ev-',location['id']+':store-menu')
   menu_evidence={'id':menu_id,'subject_id':location['id'],'claim':'location-menu','value':' | '.join(link['url'] for link in review['menu_links']),'source_url':review['menu_source_url'],'source_kind':'provider','status':'source-reviewed','recorded_on':review['menu_reviewed_on'],'reviewed_on':review['menu_reviewed_on'],'recheck_on':review['recheck_on'],'limitations':'Menu links are published by the operator for this store. Destination prices, stock, ordering availability and customer eligibility are not verified by this directory.'}
   if menu_id not in location['evidence_ids']:location['evidence_ids'].append(menu_id)
   previous=next((i for i,x in enumerate(data['evidence']) if x['id']==menu_id),None)
   if previous is None:data['evidence'].append(menu_evidence)
   else:data['evidence'][previous]=menu_evidence
  eid=stable('ev-',location['id']+':store-contact')
  evidence={'id':eid,'subject_id':location['id'],'claim':'location-contact','value':review['public_name']+'; '+review['website']+'; '+review['phone']+'; directory listing '+review['directory_organization_id'],
            'source_url':review['source_url'],'source_kind':'provider','status':'source-reviewed','recorded_on':review['reviewed_on'],'reviewed_on':review['reviewed_on'],'recheck_on':review['recheck_on'],'limitations':review['limitations']}
  if eid not in location['evidence_ids']:location['evidence_ids'].append(eid)
  existing=next((i for i,x in enumerate(data['evidence']) if x['id']==eid),None)
  if existing is None:data['evidence'].append(evidence)
  else:data['evidence'][existing]=evidence
def main():
 data=json.loads((ROOT/'data/directory.json').read_text());count=import_snapshot(data,json.loads(SOURCE.read_text()))
 (ROOT/'data/directory.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print(f'Imported {count} source-listed locations; current license status unknown')
if __name__=='__main__':main()
