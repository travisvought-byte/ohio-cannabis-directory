"""Import the saved Pennsylvania Department of Health dispensary roster; no network access.

The roster names stores and addresses but publishes no permit number, permit holder or county.
Locations therefore carry a regulator listing instead of a license, and county and coordinates
come only from a strictly accepted U.S. Census Bureau Geocoder match.
"""
import hashlib,json,re
from urllib.parse import urlencode
from datetime import date
from directory_data import ROOT
SOURCE=ROOT/'data/sources/pennsylvania-dispensaries.json'
GEOCODES=ROOT/'data/sources/pennsylvania-dispensary-geocodes.json'
BRANDS=ROOT/'data/sources/pennsylvania-dispensary-brands.json'
CORRECTIONS=ROOT/'data/sources/pennsylvania-location-corrections.json'
REGULATOR='Pennsylvania Department of Health'
RECHECK='2026-11-27'
def stable(prefix,value):return prefix+hashlib.sha256(value.encode()).hexdigest()[:12]
def us_date(value):
 m,d,y=(int(p) for p in value.split('/'));return date(2000+y if y<100 else y,m,d).isoformat()

SUFFIX={'STREET':'ST','ROAD':'RD','AVENUE':'AVE','BOULEVARD':'BLVD','DRIVE':'DR','HIGHWAY':'HWY','LANE':'LN','PLACE':'PL','TRAIL':'TRL','PLAZA':'PLZ','SQUARE':'SQ','CIRCLE':'CIR','CENTER':'CTR','COMMONS':'CMNS'}
DIRECTIONS={'N':'N','NORTH':'N','S':'S','SOUTH':'S','E':'E','EAST':'E','W':'W','WEST':'W'}
ORDINALS={'FIRST':'1ST','SECOND':'2ND','THIRD':'3RD','FOURTH':'4TH','FIFTH':'5TH','SIXTH':'6TH','SEVENTH':'7TH','EIGHTH':'8TH','NINTH':'9TH','TENTH':'10TH'}
def street_parts(street):
 s=re.sub(r'(?<=[A-Z])-(?=[A-Z])',' ',street.upper().replace('.',' '))
 s=re.sub(r'\s*(,|\bUNIT\b|\bSUITE\b|\bSTE\b|#).*$','',s)
 s=re.sub(r'\bSR\s*(\d+)',r'RTE \1',s);s=re.sub(r'\bROUTE\b','RTE',s);s=re.sub(r'\bUS-(\d+)',r'US \1',s);s=re.sub(r'\bUS HWY\b','US',s);s=re.sub(r'\bSTATE RTE\b','RTE',s)
 words=s.split()
 if not words:return None
 rest=[re.sub(r'(\d+)N$',r'\1',ORDINALS.get(w,w)) for w in words[1:]]
 return words[0],[DIRECTIONS[w] for w in rest if w in DIRECTIONS],[SUFFIX.get(w,w) for w in rest if w not in DIRECTIONS]
def same_house(source,matched):
 m=re.fullmatch(r'(\d+)([A-Z]?)(?:-(\d+))?',source)
 if not m:return source==matched
 if m.group(3):
  low=m.group(1);high=m.group(3)
  high=int(low[:len(low)-len(high)]+high) if len(high)<len(low) else int(high)
  return matched.isdigit() and int(low)<=int(matched)<=high
 return matched==source
def accept_geocode(address,result):
 """Accept only one candidate with the same house number and street, found with city and ZIP.
 A direction the roster omits is tolerated; a different street name, suffix or direction is not."""
 if result.get('longitude') is None:return False,'no match'
 if result['candidates']!=1:return False,'multiple candidates'
 if 'city' not in result['query'] or 'zip' not in result['query']:return False,'matched without city or ZIP'
 source=street_parts(address);matched=street_parts(result['matched_address'].split(',')[0])
 if not source or not matched or not same_house(source[0],matched[0]):return False,'house number differs'
 if source[2]!=matched[2]:return False,'street differs'
 if source[1] and source[1]!=matched[1]:return False,'direction differs'
 return True,'accepted'

def brand_for(name,brands):
 for brand in brands:
  for prefix in brand['prefixes']:
   if name==prefix or re.match(re.escape(prefix)+r'(\s|-|–|$)',name):return brand
 raise ValueError('No reviewed brand grouping for roster name: '+name)

def import_roster(data,source,geocodes,brands,corrections):
 rows=source['rows']
 if len(rows)!=len({r['row'] for r in rows}) or [r['row'] for r in rows]!=list(range(1,len(rows)+1)):raise ValueError('Roster rows must be complete and numbered')
 if any(r['state']!='Pennsylvania' for r in rows):raise ValueError('Unexpected source state')
 geo={g['row']:g for g in geocodes['results']}
 fixes={}
 for c in corrections['corrections']:
  row=rows[c['row']-1]
  if row[c['field']]!=c['original']:raise ValueError(f'Roster row {c["row"]} changed; re-review correction')
  fixes.setdefault(c['row'],[]).append(c)
 organizations={o['id']:o for o in data['organizations']}
 for brand in brands['brands']:
  if brand['organization_id'] in organizations:continue
  if 'name' not in brand:raise ValueError('Missing reused identity '+brand['organization_id'])
  org={'id':brand['organization_id'],'name':brand['name'],'kind':'operator','scope':'reference-only','legacy_ids':[],'contacts':[]}
  data['organizations'].append(org);organizations[org['id']]=org
 roster_id='ev-pa-doh-dispensary-roster-'+source['roster_dated'].replace('-','')
 seen=set();count=0
 for raw in rows:
  r=dict(raw)
  for c in fixes.get(r['row'],[]):r[c['field']]=c['corrected']
  if not re.fullmatch(r'\d{5}',r['zip']) or not 150<=int(r['zip'][:3])<=196:raise ValueError(f'Invalid Pennsylvania ZIP in roster row {r["row"]}')
  for key in ('name','address','city'):
   if not r[key].strip():raise ValueError(f'Missing {key} in roster row {r["row"]}')
  g=geo.get(r['row'])
  if not g or g['address']!=raw['address'] or g['zip']!=raw['zip']:raise ValueError(f'Geocode does not match roster row {r["row"]}; geocode again')
  key=r['address'].casefold()+'|'+r['zip']
  if key in seen:raise ValueError('Duplicate roster address '+key)
  seen.add(key)
  brand=brand_for(r['name'],brands['brands'])
  lid=stable('loc-','PA-DOH:'+key);eid=stable('ev-',lid+':government-location')
  location={'id':lid,'organization_id':brand['organization_id'],'name':r['name'],'state':'PA','city':r['city'],'address':r['address'],'postal_code':r['zip'],
            'regulator_listing':{'regulator':REGULATOR,'kind':'medical','roster_dated':source['roster_dated'],'listed_open_on':us_date(r['open_on'])},'evidence_ids':[eid],'snapshot_phone':r['phone']}
  evidence={'id':eid,'subject_id':lid,'claim':'government-location-snapshot','value':f'{raw["name"]}; {raw["address"]}, {raw["city"]} {raw["zip"]}; phone {raw["phone"]}; open on {raw["open_on"]}; product available as of roster date: {raw["product_available"]}; roster row {raw["row"]}',
            'source_url':source['source_url'],'source_kind':'government','status':'source-listed','recorded_on':source['retrieved_on'],'recheck_on':RECHECK,'limitations':source['limitations']}
  for c in fixes.get(r['row'],[]):evidence['limitations']+=f' Field correction reviewed {c["reviewed_on"]}: {c["field"]} {c["original"]} → {c["corrected"]}. {c["reason"]} Supporting source: {c["source_url"]}'
  items=[('locations',location),('evidence',evidence)]
  ok,_=accept_geocode(raw['address'],g)
  if ok:
   gid=stable('ev-',lid+':census-geocode')
   location['evidence_ids'].append(gid)
   geocoded={'county':g['county'].removesuffix(' County'),'latitude':round(g['latitude'],6),'longitude':round(g['longitude'],6)}
   order=['id','organization_id','name','state','county','city','address','postal_code','latitude','longitude','regulator_listing','evidence_ids','snapshot_phone']
   merged=dict(location,**geocoded);location.clear();location.update({k:merged[k] for k in order})
   items.append(('evidence',{'id':gid,'subject_id':lid,'claim':'location-geocode','value':f'{g["matched_address"]}; {location["latitude"]}, {location["longitude"]}; {g["county"]}',
                 'source_url':geocodes['endpoint']+'?'+urlencode({'street':raw['address'],'city':raw['city'],'state':'PA','zip':raw['zip'],'benchmark':geocodes['benchmark'],'vintage':geocodes['vintage'],'layers':geocodes['layers'],'format':'json'}),
                 'source_kind':'government','status':'source-listed','recorded_on':geocodes['retrieved_on'],'recheck_on':RECHECK,'limitations':geocodes['limitations']}))
  for collection,item in items:
   existing=next((i for i,x in enumerate(data[collection]) if x['id']==item['id']),None)
   if existing is None:data[collection].append(item)
   else:data[collection][existing]=item
  count+=1
 return count

def load_sources():
 return [json.loads(p.read_text()) for p in (SOURCE,GEOCODES,BRANDS,CORRECTIONS)]
def main():
 data=json.loads((ROOT/'data/directory.json').read_text());count=import_roster(data,*load_sources())
 (ROOT/'data/directory.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print(f'Imported {count} Pennsylvania roster locations; permit status unknown')
if __name__=='__main__':main()
