"""Import a saved government snapshot; no network access or freshness assumptions."""
import hashlib,json
from directory_data import ROOT
SOURCE=ROOT/'data/sources/ohio-dispensaries.json'
def stable(prefix,value):return prefix+hashlib.sha256(value.encode()).hexdigest()[:12]
def import_snapshot(data,snapshot):
 response=snapshot['response']
 if response.get('error') or response.get('exceededTransferLimit'):raise ValueError('Incomplete source response')
 rows=[f['attributes'] for f in response['features']]
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
  location={'id':lid,'organization_id':oid,'name':r['user_dispe'],'state':'OH','county':r['user_count'],'city':r['user_city'],'address':r['user_stree'],'postal_code':str(r['user_zip']).zfill(5),'latitude':lat,'longitude':lon,'license':{'number':r['user_licen'],'regulator':'Ohio Division of Cannabis Control','kind':'dual-use' if r['licensetype']=='Dual' else 'other','status':'unknown'},'evidence_ids':[eid]}
  if not valid_coordinates:
   location.pop('latitude');location.pop('longitude')
  # Source-listed is deliberately distinct from a current license verification.
  evidence={'id':eid,'subject_id':lid,'claim':'government-location-snapshot','value':r['user_dispe']+'; '+r['user_stree']+'; source license label '+r['user_lic_1'],'source_url':snapshot['source_url'],'source_kind':'government','status':'source-listed','recorded_on':snapshot['retrieved_on'],'recheck_on':'2026-11-09','limitations':snapshot['limitations']}
  data['locations']=[x for x in data['locations'] if x['id']!=lid]+[location]
  data['evidence']=[x for x in data['evidence'] if x['id']!=eid]+[evidence]
 return len(rows)
def main():
 data=json.loads((ROOT/'data/directory.json').read_text());count=import_snapshot(data,json.loads(SOURCE.read_text()))
 (ROOT/'data/directory.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print(f'Imported {count} source-listed locations; current license status unknown')
if __name__=='__main__':main()
