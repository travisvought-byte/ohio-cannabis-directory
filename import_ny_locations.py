"""Import the saved New York OCM retail snapshot; no network access.

Denominator: rows in the Office of Cannabis Management 'Current OCM Licenses' export whose
Business Purpose includes retail sales, with a date opened to the public, License Status Active
and Operational Status Active. Each kept row is one licensed store. Registered Organization
medical dispensing facilities carry no opening date in the export and are not imported.

The export has county but no coordinates or phone numbers, so New York stores support city,
county and ZIP search but not distance search until a reviewed geocode pass is added.

Medical: the open facilities on OCM's dispensing-facilities page (registered organizations) are
imported separately with their OCM registration numbers and listed phones. Temporarily closed
facilities are counted in the source but not published.
"""
import hashlib,json,re
from urllib.parse import urlencode
from directory_data import ROOT
from location_validation import validate_location_fields
SOURCE=ROOT/'data/sources/new-york-ocm-retail-2026-11-01.json'
MEDICAL=ROOT/'data/sources/new-york-medical-dispensing-facilities-2026-11-01.json'
GEOCODES=ROOT/'data/sources/new-york-location-geocodes-2026-11-01.json'
# Reviewed brand reuse: the DBA printed by OCM matches an existing national identity, as in the PA roster import.
MEDICAL_BRANDS={'Rise':'org-364a9eed8729','Verilife':'org-aefe1b952bc0','the Botanist or Acreage NY':'org-7022b334ede8','Remedy-NY or Sunnyside':'org-667af67557f3'}
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
def upsert(data,collection,item):
 existing=next((i for i,x in enumerate(data[collection]) if x['id']==item['id']),None)
 if existing is None:data[collection].append(item)
 else:data[collection][existing]=item
def import_medical(data,source):
 rows=source['rows']
 regs=[r['registration_number'] for r in rows]
 if not all(re.fullmatch(r'MM\d{4}D',x) for x in regs) or len(set(regs))!=len(regs):raise ValueError('Invalid or duplicate medical registration number')
 open_rows=[r for r in rows if not r['temporarily_closed']]
 retail={(l['address'].casefold(),l['postal_code']) for l in data['locations'] if l['state']=='NY' and l.get('license',{}).get('kind')=='adult-use'}
 orgs={o['id']:o for o in data['organizations']}
 for r in open_rows:
  name=r['dba'] or r['registered_organization']
  validate_location_fields({'state':'NY','county':r['county'],'city':r['city'],'name':name,'address':r['address'],'postal_code':r['zip']})
  if (r['address'].casefold(),r['zip']) in retail:raise ValueError('Medical facility duplicates an adult-use store: '+r['registration_number'])
  oid=MEDICAL_BRANDS.get(r['dba'])
  if oid and oid not in orgs:raise ValueError('Missing reused identity '+oid)
  if not oid:
   oid=stable('org-','new-york-registered-organization:'+r['registered_organization'].casefold())
   if oid not in orgs:
    org={'id':oid,'name':r['registered_organization'],'kind':'operator','scope':'reference-only','legacy_ids':[],'contacts':[]};data['organizations'].append(org);orgs[oid]=org
  lid=stable('loc-','NY-MED:'+r['registration_number']);eid=stable('ev-',lid+':government-location')
  location={'id':lid,'organization_id':oid,'name':(r['dba'].split(' or ')[0].replace('the Botanist','The Botanist') if r['dba'] else r['registered_organization']),'state':'NY','county':r['county'],'city':r['city'],'address':r['address'],'postal_code':r['zip'],
            'license':{'number':r['registration_number'],'regulator':REGULATOR,'kind':'medical','status':'unknown'},'evidence_ids':[eid],'snapshot_phone':r['phone']}
  evidence={'id':eid,'subject_id':lid,'claim':'government-location-snapshot','value':'OCM medical dispensing facility: '+r['row_text'],'source_url':source['source_url'],'source_kind':'government',
            'status':'source-listed','recorded_on':source['retrieved_on'],'recheck_on':RECHECK,'limitations':source['limitations']}
  upsert(data,'locations',location);upsert(data,'evidence',evidence)
 return len(open_rows)
def geocode_street(address):
 """First comma-separated part that begins with a number: drops suite and plaza text."""
 parts=[p.strip() for p in address.split(',')]
 return next((p for p in parts if re.match(r'\d',p)),parts[0])
NY_WORDS={'COURT':'CT','PARKWAY':'PKWY','PKY':'PKWY','TURNPIKE':'TPKE','EXPRESSWAY':'EXPY','TERRACE':'TER','HIGHWAY':'HWY'}
def ny_normalize(street):
 """Spelled-out suffixes the Pennsylvania normalizer does not cover, County Road as CO RD, and trailing
 floor/space/store unit text. Route types are left as written: Route 9 and US Hwy 9 still differ."""
 s=re.sub(r'\s+(FL|FLOOR|SPC|STORE)\b.*$','',street,flags=re.I)
 s=re.sub(r'\bCOUNTY\s+ROAD\b','CO RD',s,flags=re.I)
 return ' '.join(NY_WORDS.get(w.upper().strip('.'),w) for w in s.split())
def accept_ny_geocode(street,result,county):
 """Pennsylvania acceptance rule with two New York cases: Queens-style house numbers written without the
 hyphen (16203 for 162-03) are the same house, and spelled-out suffixes are abbreviated first.
 The Census county must also match the regulator's county."""
 from import_pa_locations import accept_geocode,street_parts
 if result.get('longitude') is None:return False,'no match'
 matched_street=(result['matched_address'] or '').split(',')[0]
 source=street_parts(ny_normalize(street));matched=street_parts(ny_normalize(matched_street))
 if source and matched and '-' in matched[0] and source[0].replace('-','')==matched[0].replace('-',''):
  if result['candidates']!=1:return False,'multiple candidates'
  if 'city' not in result['query'] or 'zip' not in result['query']:return False,'matched without city or ZIP'
  if source[2]!=matched[2]:return False,'street differs'
  if source[1] and source[1]!=matched[1]:return False,'direction differs'
  ok,reason=True,'accepted'
 else:ok,reason=accept_geocode(ny_normalize(street),dict(result,matched_address=ny_normalize(matched_street)+','))
 if ok and result['county'].removesuffix(' County').replace('.','')!=county:return False,'county differs'
 return ok,reason
def apply_geocodes(data,geocodes):
 results={g['key']:g for g in geocodes['results']}
 accepted=0
 order=['id','organization_id','name','state','county','city','address','postal_code','latitude','longitude','license','evidence_ids','snapshot_phone']
 for location in data['locations']:
  if location['state']!='NY' or not location.get('license'):continue
  g=results.get(location['license']['number'])
  if not g or g['street']!=geocode_street(location['address']) or g['zip']!=location['postal_code'] or g['city']!=location['city']:
   raise ValueError('Geocode does not match New York location '+location['license']['number']+'; geocode again')
  ok,_=accept_ny_geocode(g['street'],g,location['county'])
  if not ok:continue
  gid=stable('ev-',location['id']+':census-geocode')
  merged=dict(location,latitude=round(g['latitude'],6),longitude=round(g['longitude'],6))
  if gid not in merged['evidence_ids']:merged['evidence_ids']=merged['evidence_ids']+[gid]
  location.clear();location.update({k:merged[k] for k in order if k in merged})
  upsert(data,'evidence',{'id':gid,'subject_id':location['id'],'claim':'location-geocode','value':f'{g["matched_address"]}; {location["latitude"]}, {location["longitude"]}; {g["county"]}',
   'source_url':geocodes['endpoint']+'?'+urlencode({'street':g['street'],'city':g['city'],'state':'NY','zip':g['zip'],'benchmark':geocodes['benchmark'],'vintage':geocodes['vintage'],'layers':geocodes['layers'],'format':'json'}),
   'source_kind':'government','status':'source-listed','recorded_on':geocodes['retrieved_on'],'recheck_on':RECHECK,'limitations':geocodes['limitations']})
  accepted+=1
 return accepted
def main():
 data=json.loads((ROOT/'data/directory.json').read_text());count=import_snapshot(data,json.loads(SOURCE.read_text()));medical=import_medical(data,json.loads(MEDICAL.read_text()));points=apply_geocodes(data,json.loads(GEOCODES.read_text()))
 (ROOT/'data/directory.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print(f'Imported {count} New York OCM retail locations and {medical} open medical dispensing facilities ({points} with accepted map points); current license status unknown')
if __name__=='__main__':main()
