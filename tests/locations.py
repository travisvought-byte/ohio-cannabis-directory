"""Import stability and conservative source handling."""
import sys,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from import_locations import import_snapshot,SOURCE
from directory_data import load_directory
snapshot=json.loads(SOURCE.read_text());data=load_directory();before=copy.deepcopy(data)
assert import_snapshot(data,snapshot)==230
assert data==before,'Repeated import must preserve the canonical tree'
# Snapshot assertions concern Ohio dispensaries, not other states' service offices.
locations=[l for l in data['locations'] if l['state']=='OH'];assert len(locations)==230
assert all(l['license']['status']=='unknown' for l in locations)
assert sum('latitude' not in l for l in locations)==4
assert sum(bool(l.get('snapshot_phone')) for l in locations)==228
assert sum(bool(l.get('contact')) for l in locations)==20
assert all(l['license']['kind']=='dual-use' for l in locations)
by_license={l['license']['number']:l for l in locations}
assert by_license['CCD000176-00']['city']=='Cincinnati'
assert by_license['CCD000176-00']['postal_code']=='45219'
assert by_license['CCD000271-00']['county']=='Delaware'
assert by_license['CCD000174-00']['county']=='Lake'
assert by_license['CCD000241-00']['city']=='Middletown'
assert by_license['CCD000139-00']['address']=='9601 Vista Way'
assert 'latitude' not in by_license['CCD000139-00']
assert by_license['CCD000075-00']['contact']['phone']=='740-200-0760'
assert by_license['CCD000209-00']['contact']['public_name']=='Greenlight South Point'
for change in ['truncated','duplicate','county','city','zip','changed-correction','changed-contact']:
 bad=copy.deepcopy(snapshot)
 if change=='truncated':bad['response']['exceededTransferLimit']=True
 elif change=='duplicate':bad['response']['features'].append(bad['response']['features'][0])
 elif change=='county':bad['response']['features'][0]['attributes']['user_count']='Lewis Center'
 elif change=='city':bad['response']['features'][0]['attributes']['user_city']='Some Cannabis Dispensary'
 elif change=='zip':bad['response']['features'][0]['attributes']['user_zip']=12345
 elif change=='changed-contact':next(f['attributes'] for f in bad['response']['features'] if f['attributes']['user_licen']=='CCD000075-00')['user_stree']='New address requiring review'
 else:next(f['attributes'] for f in bad['response']['features'] if f['attributes']['user_licen']=='CCD000176-00')['user_city']='Unexpected change'
 try:import_snapshot(copy.deepcopy(data),bad)
 except ValueError:pass
 else:raise AssertionError(change)
from validate_foundation import validate
bad=copy.deepcopy(data);next(l for l in bad['locations'] if l.get('contact'))['contact']['phone']='999-999-9999'
assert any('matching location-contact evidence' in e for e in validate(bad))
print('PASS location snapshot: stable import, 230 unique licenses, 228 snapshot phones, 20 reviewed contacts, corrected address and incomplete-feed rejection')

assert sum(bool(l.get("contact",{}).get("menu_links")) for l in data["locations"])==15
bad=copy.deepcopy(data);next(l for l in bad["locations"] if l.get("contact",{}).get("menu_links"))["contact"]["menu_links"][0]["url"]="https://example.org/wrong-store"
assert any("matching location-menu evidence" in e for e in validate(bad))
# Pennsylvania: the Department of Health roster has no permit numbers, so locations carry a regulator listing.
from import_pa_locations import import_roster,load_sources,accept_geocode
pa_sources=load_sources();pa_data=load_directory();pa_before=copy.deepcopy(pa_data)
assert import_roster(pa_data,*copy.deepcopy(pa_sources))==200
assert pa_data==pa_before,'Repeated Pennsylvania import must preserve the canonical tree'
pa=[l for l in pa_data['locations'] if l.get('regulator_listing')];assert len(pa)==200
assert all(l['state']=='PA' and 'license' not in l and l['regulator_listing']['roster_dated']=='2026-09-16' for l in pa)
assert sum('latitude' in l for l in pa)==163 and all(('county' in l)==('latitude' in l) for l in pa)
by_name={(l['name'],l['address']):l for l in pa}
assert by_name[('RISE - King of Prussia','445 West DeKalb Pike')]['postal_code']=='19406'
assert by_name[('RISE - Carlisle','1186 Harrisburg Pike')]['postal_code']=='17013'
assert by_name[('Sunnyside - Butler County','201 Pillow Street')]['city']=='Butler'
assert by_name[('Sunnyside - Butler County','201 Pillow Street')]['organization_id']=='org-667af67557f3'
assert 'latitude' not in by_name[('Ethos - Fayette (Pittsburg)','470 Home Drive')],'A different street from the geocoder must not supply coordinates'
assert not any(l['organization_id'] in ('org-6bb8b2a3ca4e','org-171927b374cf') for l in pa),'Ohio-only identities are not reused'
orgs={o['id']:o for o in pa_data['organizations']}
assert all(orgs[l['organization_id']]['scope'] in ('public','reference-only') for l in pa)
assert accept_geocode('130 Mall Circle Drive',{'candidates':1,'query':'street+city+state+zip','matched_address':'130 MALL BLVD, MONROEVILLE, PA, 15146','longitude':-79.7,'latitude':40.4})==(False,'street differs')
assert accept_geocode('1538-40 E. Lancaster Ave',{'candidates':1,'query':'street+city+state+zip','matched_address':'1538 E LANCASTER AVE, PAOLI, PA, 19301','longitude':-75.4,'latitude':40.0})==(True,'accepted')
assert accept_geocode('201 Lancaster Ave',{'candidates':2,'query':'street+city+state+zip','matched_address':'201 E LANCASTER AVE, READING, PA, 19611','longitude':-75.9,'latitude':40.3})[0] is False
for change in ['row-text','zip','geocode','brand','duplicate']:
 bad=copy.deepcopy(pa_sources);roster,geo,brands,corrections=bad
 if change=='row-text':roster['rows'][58]['zip']='19407'
 elif change=='zip':roster['rows'][0]['zip']='12345';geo['results'][0]['zip']='12345'
 elif change=='geocode':geo['results'][5]['address']='Changed address'
 elif change=='brand':roster['rows'][3]['name']='Unknown Brand - Somewhere'
 else:roster['rows'][1]=dict(roster['rows'][0],row=2);geo['results'][1]=dict(geo['results'][0],row=2)
 try:import_roster(copy.deepcopy(pa_data),*bad)
 except ValueError:pass
 else:raise AssertionError('pa '+change)
print('PASS Pennsylvania roster: 200 regulator-listed locations, 163 accepted geocodes, 3 reviewed corrections and change rejection')
