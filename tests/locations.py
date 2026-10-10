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
for change in ['truncated','duplicate']:
 bad=copy.deepcopy(snapshot)
 if change=='truncated':bad['response']['exceededTransferLimit']=True
 else:bad['response']['features'].append(bad['response']['features'][0])
 try:import_snapshot(copy.deepcopy(data),bad)
 except ValueError:pass
 else:raise AssertionError(change)
print('PASS location snapshot: stable import, 230 unique licenses, 3 rejected coordinate pairs and incomplete-feed rejection')
