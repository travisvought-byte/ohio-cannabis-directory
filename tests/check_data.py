"""Validate evidence preservation, stable IDs, release labels and deterministic builds."""
import csv
import importlib
import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from directory_data import RELEASE, RELEASE_DATE, load_records, relationship_id
rows = load_records()
assert len(rows) == 564
assert sum(not r['Category'].startswith('Out of scope') for r in rows) == 518
assert len({r['Record ID'] for r in rows}) == len(rows)
assert all(re.fullmatch(r'org-[0-9a-f]{12}', r['Record ID']) for r in rows)
assert all(r['Source(s)'] and r['Capabilities / Keywords'] for r in rows)
assert sum(r['Verification Tier'] == 'Open issue' for r in rows) == 6
for row in rows:
    if row['Last Reviewed']:
        assert date.fromisoformat(row['Last Reviewed']) <= RELEASE_DATE
        assert row['Last Reviewed'] in row['Source(s)'] + row['Seed Source']
assert sum(bool(r['Last Reviewed']) for r in rows) == 8
with (ROOT / 'b2b-relationships.csv').open(encoding='utf-8-sig') as f:
    relationships = list(csv.DictReader(f))
assert len(relationships) == 60
assert len({relationship_id(r) for r in relationships}) == 60
with tempfile.TemporaryDirectory() as temp:
    for module_name, filename in [('build_directory','index.html'),('build_intake','intake.html'),('build_relationships','relationships.html'),('build_resources','resources.html')]:
        module = importlib.import_module(module_name)
        module.OUT = Path(temp) / filename
        module.main()
        assert module.OUT.read_text() == (ROOT / filename).read_text(), f'{filename} requires rebuild'
for name in ['.zenodo.json','zenodo.json']:
    archive = json.loads((ROOT / name).read_text())
    assert archive['version'] == RELEASE['version']
    assert archive['publication_date'] == RELEASE['released_on']
citation = (ROOT / 'CITATION.cff').read_text()
assert f"version: '{RELEASE['version']}'" in citation
assert f"date-released: '{RELEASE['released_on']}'" in citation
assert f'release v{RELEASE["version"]}' in (ROOT / 'index.html').read_text()
assert f'Current site release:** {RELEASE["version"]}' in (ROOT / 'README.md').read_text()
assert 'relationships.html' in (ROOT / 'sitemap.xml').read_text()
print('PASS: record counts, IDs, review-date evidence, verification tiers, relationship coverage, generated pages and release metadata.')
