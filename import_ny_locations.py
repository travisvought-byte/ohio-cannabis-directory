"""Import the saved New York OCM retail snapshot; no network access.

Denominator: rows in the Office of Cannabis Management 'Current OCM Licenses' export whose
Business Purpose includes retail sales, with a date opened to the public, License Status Active
and Operational Status Active. Each kept row is one licensed store. Registered Organization
medical dispensing facilities carry no opening date in the export and are not imported.

The export has county but no coordinates or phone numbers, so New York stores support city,
county and ZIP search but not distance search until a reviewed geocode pass is added.
"""
import hashlib,json
from directory_data import ROOT
from location_validation import validate_location_fields
SOURCE=ROOT/'data/sources/new-york-ocm-retail-2026-11-01.json'
REGULATOR='New York State Office of Cannabis Management'
RECHECK='2026-12-01'
KIND={'Adult-Use Retail Dispensary License':'adult-use','Adult-Use Conditional Retail Dispensary License':'adult-use','Adult-Use Microbusiness License':'adult-use'}
def stable(prefix,value):return prefix+hashlib.sha256(value.encode()).hexdigest()[:12]
def selected(snapshot):
 return [r for r in snapshot['rows'] if r['license_status']=='Active' and r['operational_status']=='Active' and r['opened_to_public_on'] and 'Retail Sales' in (r['business_purpose'] or '')]
def evidence_value(r):
 parts=[r['dba'] or r['entity_name'],'licensee '+r['entity_name'],f'{r["address_1"]}{", "+r["address_2"] if r["address_2"] else ""}, {r["city"]} {r["zip"]}, {r["county"]} County',
        f'{r["license_type"]} {r["license_number"]}',f'license status {r["license_status"]}, operational status {r["operational_status"]}',f'opened to public {r["opened_to_public_on"]}',
        'delivery reported' if r['delivery'] else 'no delivery reported']
 if r['website']:parts.append('website as reported '+r['website'])
 if r['hours']:parts.append('hours as reported: '+r['hours'])
 return '; '.join(parts)
def import_snapshot(data,snapshot):
 rows=selected(snapshot)
 if not rows:raise ValueError('No New York retail rows selected')
 licenses=[r['license_number'] for r in rows]
 if not all(licenses) or len(set(licenses))!=len(licenses):raise ValueError('Duplicate or missing New York license number')
 seen=set()
 for r in rows:
  if r['state']!='NY':raise ValueError('Unexpected source state for '+r['license_number'])
  if r['license_type'] not in KIND:raise ValueError('Unreviewed retail license type: '+r['license_type'])
  name=r['dba'] or r['entity_name']
  validate_location_fields({'state':'NY','county':r['county'],'city':r['city'],'name':name,'address':r['address_1'],'postal_code':r['zip']})
  key=(r['address_1'].casefold(),r['address_2'] or '',r['zip'])
  if key in seen:raise ValueError('Duplicate New York store address '+r['address_1'])
  seen.add(key)
 organizations=data['organizations']
 by_name={}
 for o in organizations:by_name.setdefault(o['name'].strip().casefold(),[]).append(o)
 for r in rows:
  legal=r['entity_name'].strip()
  matches=by_name.get(legal.casefold(),[])
  if len(matches)==1:oid=matches[0]['id']
  else:
   oid=stable('org-','new-york-location-legal:'+legal.casefold())
   if not any(o['id']==oid for o in organizations):
    org={'id':oid,'name':legal,'kind':'operator','scope':'reference-only','legacy_ids':[],'contacts':[]}
    organizations.append(org);by_name.setdefault(legal.casefold(),[]).append(org)
  lid=stable('loc-','NY:'+r['license_number']);eid=stable('ev-',lid+':government-location')
  address=r['address_1']+(', '+r['address_2'] if r['address_2'] else '')
  location={'id':lid,'organization_id':oid,'name':r['dba'] or r['entity_name'],'state':'NY','county':r['county'],'city':r['city'],'address':address,'postal_code':r['zip'],
            'license':{'number':r['license_number'],'regulator':REGULATOR,'kind':KIND[r['license_type']],'status':'unknown'},'evidence_ids':[eid]}
  # Source-listed is deliberately distinct from a current license verification.
  evidence={'id':eid,'subject_id':lid,'claim':'government-location-snapshot','value':evidence_value(r),'source_url':snapshot['source_url'],'source_kind':'government',
            'status':'source-listed','recorded_on':snapshot['retrieved_on'],'recheck_on':RECHECK,'limitations':snapshot['limitations']}
  for collection,item in (('locations',location),('evidence',evidence)):
   existing=next((i for i,x in enumerate(data[collection]) if x['id']==item['id']),None)
   if existing is None:data[collection].append(item)
   else:data[collection][existing]=item
 return len(rows)
def main():
 data=json.loads((ROOT/'data/directory.json').read_text());count=import_snapshot(data,json.loads(SOURCE.read_text()))
 (ROOT/'data/directory.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print(f'Imported {count} New York OCM retail locations; current license status unknown')
if __name__=='__main__':main()
