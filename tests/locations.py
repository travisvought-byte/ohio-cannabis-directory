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
assert sum('latitude' not in l for l in locations)==3
assert all(l['license']['kind']=='dual-use' for l in locations)
by_license={l['license']['number']:l for l in locations}
assert by_license['CCD000176-00']['city']=='Cincinnati'
assert by_license['CCD000176-00']['postal_code']=='45219'
assert by_license['CCD000271-00']['county']=='Delaware'
assert by_license['CCD000174-00']['county']=='Lake'
assert by_license['CCD000241-00']['city']=='Middletown'
for change in ['truncated','duplicate','county','city','zip','changed-correction']:
 bad=copy.deepcopy(snapshot)
 if change=='truncated':bad['response']['exceededTransferLimit']=True
 elif change=='duplicate':bad['response']['features'].append(bad['response']['features'][0])
 elif change=='county':bad['response']['features'][0]['attributes']['user_count']='Lewis Center'
 elif change=='city':bad['response']['features'][0]['attributes']['user_city']='Some Cannabis Dispensary'
 elif change=='zip':bad['response']['features'][0]['attributes']['user_zip']=12345
 else:next(f['attributes'] for f in bad['response']['features'] if f['attributes']['user_licen']=='CCD000176-00')['user_city']='Unexpected change'
 try:import_snapshot(copy.deepcopy(data),bad)
 except ValueError:pass
 else:raise AssertionError(change)
print('PASS location snapshot: stable import, 230 unique licenses, 3 rejected coordinate pairs and incomplete-feed rejection')
