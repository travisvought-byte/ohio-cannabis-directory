import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from strain_ancestry import DATA, analyze
full=json.loads(DATA.read_text());assert not analyze(full)['errors']
catalog=[s for s in full['strains'] if s.get('catalog') or s.get('popular')]
assert len(catalog)>=300
assert len(catalog)==full['selection']['expected_profile_count']
assert len(full['observations'])>=20
x={**full,'version':1,'strains':full['strains'][:5],'claims':full['claims'][:3],'sources':full['sources'][:2],'resolutions':full['resolutions'][:1]};r=analyze(x)
assert not r['errors']
assert r['name_collisions'][0]['strain_ids']==['blue-dream-barneys','blue-dream-hso']
assert r['parentage_review'][0]['child_id']=='blue-dream-hso'
y=copy.deepcopy(x);y['claims'][0]['source_ids']=['missing'];assert any('Missing source' in e for e in analyze(y)['errors'])
y=copy.deepcopy(x);y['claims'][0]['parent_ids'][0]='missing';assert any('Unknown strain' in e for e in analyze(y)['errors'])
y=copy.deepcopy(x);y['claims'].append({**y['claims'][0],'id':'cycle','child_id':'blueberry-unspecified','parent_ids':['blue-dream-barneys','haze-selected-hso']});assert any('cycle' in e for e in analyze(y)['errors'])
y=copy.deepcopy(x);y['claims'].append(y['claims'][0]);assert any('Duplicate' in e for e in analyze(y)['errors'])
y=copy.deepcopy(x);y['claims'][2]['status']='superseded';assert not analyze(y)['parentage_review']
print('PASS ancestry: references, sources, name collisions, alternatives, cycles and superseded claims')

# Validate the populated catalog and deterministic HTML/CSV builds.
y=copy.deepcopy(full);next(s for s in y['strains'] if s.get('popular'))['profile_source_ids']=['missing'];assert any('Missing profile source' in e for e in analyze(y)['errors'])
y=copy.deepcopy(full);y['selection']['expected_profile_count']+=1;assert any('Catalog count' in e for e in analyze(y)['errors'])
y=copy.deepcopy(full);y['observations'][0]['inventory_status']='in-stock';assert any('Unsupported inventory' in e for e in analyze(y)['errors'])
y=copy.deepcopy(full);y['observations'][0]['strain_id']='missing';assert any('Invalid menu reference' in e for e in analyze(y)['errors'])
y=copy.deepcopy(full);y['observations'].append(y['observations'][0]);assert any('Duplicate menu' in e for e in analyze(y)['errors'])
y=copy.deepcopy(full);next(s for s in y['strains'] if s.get('kind')=='producer-profile')['producer']='';assert any('Missing producer identity' in e for e in analyze(y)['errors'])
import tempfile
import build_ancestry
with tempfile.TemporaryDirectory() as tmp:
    build_ancestry.ROOT=Path(tmp);build_ancestry.OUT=Path(tmp)/'ancestry.html'
    (Path(tmp)/'data/strains').mkdir(parents=True)
    build_ancestry.main()
    for name in ('ancestry.html','data/strains/ancestry.csv','data/strains/strains.csv','data/strains/ohio-flower.csv'):
        assert (Path(tmp)/name).read_bytes()==(DATA.parents[2]/name).read_bytes(), name+' requires rebuild'
print('PASS growing source-linked catalog and deterministic HTML/CSV exports')
