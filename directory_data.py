"""Shared directory data and release metadata for reproducible public builds."""
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_OF_SCOPE = 'Out of scope — flagged for removal or separate list'
RELEASE = json.loads((ROOT / 'release.json').read_text())
RELEASE_DATE = date.fromisoformat(RELEASE['released_on'])

def load_directory():
    return json.loads((ROOT / 'data/directory.json').read_text())

def load_records():
    return [r['legacy_record'] for r in load_directory()['organizations'] if 'legacy_record' in r]

def load_relationship_records():
    return [r['legacy_record'] for r in load_directory()['relationships']]

def load_seed_records():
    return [r['legacy_seed_record'] for r in load_directory()['services'] if r.get('origin') == 'seed-profile']

def load_resource_routes():
    return [(r['pathway_id'], r['title'], [(i['name'], i['url'], i['description']) for i in r['items']]) for r in load_directory()['resource_routes']]

def load_event_routes():
    return load_directory()['event_routes']

def script_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')

def relationship_id(row):
    key = '|'.join(row[k] for k in ('Organization A', 'Organization B / Counterparty', 'Relationship Type'))
    return 'rel-' + hashlib.sha256(key.encode()).hexdigest()[:12]
