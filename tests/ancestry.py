import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from strain_ancestry import DATA, analyze
x=json.loads(DATA.read_text());r=analyze(x)
assert not r['errors']
assert r['name_collisions'][0]['strain_ids']==['blue-dream-barneys','blue-dream-hso']
assert r['parentage_review'][0]['child_id']=='blue-dream-hso'
y=copy.deepcopy(x);y['claims'][0]['source_ids']=['missing'];assert any('Missing source' in e for e in analyze(y)['errors'])
y=copy.deepcopy(x);y['claims'][0]['parent_ids'][0]='missing';assert any('Unknown strain' in e for e in analyze(y)['errors'])
y=copy.deepcopy(x);y['claims'].append({**y['claims'][0],'id':'cycle','child_id':'blueberry-unspecified','parent_ids':['blue-dream-barneys','haze-selected-hso']});assert any('cycle' in e for e in analyze(y)['errors'])
y=copy.deepcopy(x);y['claims'].append(y['claims'][0]);assert any('Duplicate' in e for e in analyze(y)['errors'])
y=copy.deepcopy(x);y['claims'][2]['status']='superseded';assert not analyze(y)['parentage_review']
print('PASS ancestry: references, sources, name collisions, alternatives, cycles and superseded claims')
