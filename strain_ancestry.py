"""Validate and report source-attributed ancestry without collapsing names."""
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/strains/ancestry.json'

def normalize(name):
    return re.sub(r'[^a-z0-9]', '', name.casefold())

def analyze(data):
    errors = []
    maps = {}
    for table in ('strains', 'claims', 'sources', 'resolutions'):
        rows = data.get(table, [])
        maps[table] = {r['id']: r for r in rows}
        if len(maps[table]) != len(rows):
            errors.append(f'Duplicate IDs in {table}')
    strains, sources = maps['strains'], maps['sources']
    names, parents, adjacency = defaultdict(set), defaultdict(set), defaultdict(set)
    for s in strains.values():
        if s['kind'] not in ('seed-line', 'clone', 'landrace', 'unresolved-parent', 'market-name', 'producer-profile'):
            errors.append(f"Invalid kind: {s['id']}")
        for name in [s['name'], *s['aliases']]:
            names[normalize(name)].add(s['id'])
    popular = [s for s in strains.values() if s.get('popular')]
    catalog = [s for s in strains.values() if s.get('catalog') or s.get('popular')]
    if data.get('version', 1) >= 3:
        if len(catalog) != data.get('selection', {}).get('expected_profile_count'):
            errors.append('Catalog count differs from reviewed selection metadata')
        distinct = len({normalize(s['name']) for s in catalog})
        if distinct != data.get('selection', {}).get('distinct_name_count'):
            errors.append('Distinct name count differs from reviewed selection metadata')
        for s in catalog:
            for field in ('category', 'lineage_text', 'history', 'review_note', 'profile_source_ids', 'reviewed_on'):
                if not s.get(field) and not (s.get('source_link_only') and field in ('lineage_text','history','reported_effects','reported_flavors')):
                    errors.append(f"Missing profile field {field}: {s['id']}")
            for field in ('reported_effects', 'reported_flavors', 'reported_terpenes', 'ohio_evidence'):
                if not isinstance(s.get(field), list):
                    errors.append(f"Invalid profile list {field}: {s['id']}")
            if s.get('category') not in ('indica', 'sativa', 'hybrid') and not (s.get('source_link_only') and s.get('category')=='unknown'):
                errors.append(f"Invalid category: {s['id']}")
            if any(ref not in sources for ref in s.get('profile_source_ids', [])):
                errors.append(f"Missing profile source: {s['id']}")
            if s.get('kind') == 'producer-profile' and not s.get('producer'):
                errors.append(f"Missing producer identity: {s['id']}")
            if s.get('review_count') is not None and (not isinstance(s['review_count'], int) or s['review_count'] <= 0):
                errors.append(f"Invalid review count: {s['id']}")
            for evidence in s.get('ohio_evidence', []):
                if evidence.get('source_id') not in sources or evidence.get('kind') not in ('producer-catalog', 'ohio-menu'):
                    errors.append(f"Invalid Ohio evidence: {s['id']}")
        observation_ids = set()
        for observation in data.get('observations', []):
            if observation['id'] in observation_ids:
                errors.append('Duplicate menu observation ID')
            observation_ids.add(observation['id'])
            if observation.get('strain_id') not in strains or observation.get('source_id') not in sources:
                errors.append(f"Invalid menu reference: {observation['id']}")
            if observation.get('state') != 'OH' or observation.get('form') != 'flower' or observation.get('inventory_status') != 'not-confirmed':
                errors.append(f"Unsupported inventory claim: {observation['id']}")
            try:
                if date.fromisoformat(observation['checked_on']) > date.today():
                    errors.append(f"Future menu date: {observation['id']}")
            except (ValueError, KeyError):
                errors.append(f"Invalid menu date: {observation['id']}")
    if data.get('version', 1) >= 2:
        if data.get('version') == 2 and (len(popular) != 100 or len({normalize(s['name']) for s in popular}) != 100):
            errors.append('Popular catalog must contain 100 distinct display names')
        for s in popular:
            for field in ('category', 'lineage_text', 'history', 'review_note', 'profile_source_ids', 'reported_effects', 'reported_flavors', 'reviewed_on'):
                if not s.get(field) and not (s.get('source_link_only') and field in ('lineage_text','history','reported_effects','reported_flavors')):
                    errors.append(f"Missing profile field {field}: {s['id']}")
            if s.get('category') not in ('indica', 'sativa', 'hybrid') and not (s.get('source_link_only') and s.get('category')=='unknown'):
                errors.append(f"Invalid category: {s['id']}")
            if any(ref not in sources for ref in s.get('profile_source_ids', [])):
                errors.append(f"Missing profile source: {s['id']}")
            if not s.get('source_link_only') and (not isinstance(s.get('review_count'), int) or s.get('review_count', 0) <= 0):
                errors.append(f"Invalid review count: {s['id']}")
    for source in sources.values():
        if not source['url'].startswith('https://'):
            errors.append(f"Invalid source URL: {source['id']}")
        try:
            if date.fromisoformat(source['reviewed_on']) > date.today():
                errors.append(f"Future source date: {source['id']}")
        except ValueError:
            errors.append(f"Invalid source date: {source['id']}")
    for c in maps['claims'].values():
        child = c['child_id']
        if child not in strains or any(p not in strains for p in c['parent_ids']):
            errors.append(f"Unknown strain reference: {c['id']}")
        if not c['source_ids'] or any(s not in sources for s in c['source_ids']):
            errors.append(f"Missing source: {c['id']}")
        if c['status'] not in ('breeder-reported', 'producer-reported', 'secondary-reported', 'disputed', 'superseded'):
            errors.append(f"Invalid claim status: {c['id']}")
        if c['relationship'] != 'cross' or c['parent_roles'] != 'unspecified':
            errors.append(f"Unsupported relationship or parent roles: {c['id']}")
        if len(c['parent_ids']) != 2:
            errors.append(f"Cross must have two parent slots: {c['id']}")
        if c['status'] != 'superseded':
            parents[child].add(tuple(sorted(c['parent_ids'])))
            adjacency[child].update(c['parent_ids'])
    for r in maps['resolutions'].values():
        if any(s not in strains for s in r['strain_ids']) or not r['reason']:
            errors.append(f"Invalid resolution: {r['id']}")
        if r['decision'] != 'keep-separate':
            errors.append(f"Unsupported resolution: {r['id']}")
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            errors.append(f'Ancestry cycle involving {node}')
            return
        if node in visited:
            return
        visiting.add(node)
        for parent in sorted(adjacency[node]):
            visit(parent)
        visiting.remove(node)
        visited.add(node)
    for node in strains:
        visit(node)
    return {'errors': sorted(set(errors)), 'name_collisions': [{'name_key': n, 'strain_ids': sorted(ids)} for n, ids in sorted(names.items()) if len(ids) > 1], 'parentage_review': [{'child_id': c, 'alternatives': [list(p) for p in sorted(ps)]} for c, ps in sorted(parents.items()) if len(ps) > 1]}

if __name__ == '__main__':
    report = analyze(json.loads(DATA.read_text()))
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report['errors']))
