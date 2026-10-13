"""Import stability and conservative source handling."""
import sys,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from import_locations import import_snapshot,SOURCE
from directory_data import load_directory
snapshot=json.loads(SOURCE.read_text());data=load_directory();before=copy.deepcopy(data)
assert import_snapshot(data,snapshot)==230
assert data==before,'Repeated import must preserve the canonical tree'
locations=data['locations'];assert len(locations)==230
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
