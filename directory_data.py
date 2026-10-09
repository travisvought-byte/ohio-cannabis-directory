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

def load_records():
    with (ROOT / 'ohio-cannabis-directory.csv').open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def script_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')

def relationship_id(row):
    key = '|'.join(row[k] for k in ('Organization A', 'Organization B / Counterparty', 'Relationship Type'))
    return 'rel-' + hashlib.sha256(key.encode()).hexdigest()[:12]
