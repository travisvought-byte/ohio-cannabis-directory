"""Validate evidence preservation, stable IDs, release labels and deterministic builds."""
import csv
import importlib
import json
import re
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from directory_data import RELEASE, RELEASE_DATE, load_records, relationship_id, load_directory
from validate_legislators import validate as validate_legislators
validate_legislators()
rows = load_records()
assert len(rows) == 565
assert sum(not r['Category'].startswith('Out of scope') for r in load_records(include_withdrawn=False)) == 516
assert len({r['Record ID'] for r in rows}) == len(rows)
assert all(re.fullmatch(r'org-[0-9a-f]{12}', r['Record ID']) for r in rows)
assert all(r['Source(s)'] and r['Capabilities / Keywords'] for r in rows)
assert sum(r['Verification Tier'] == 'Open issue' for r in rows) == 6
for row in rows:
    if row['Last Reviewed']:
        assert date.fromisoformat(row['Last Reviewed']) <= date.fromisoformat(load_directory()['as_of'])
        assert row['Last Reviewed'] in row['Source(s)'] + row['Seed Source']
audits = [json.loads(p.read_text()) for p in (ROOT / 'data/reviews').glob('*.json')]
newly_dated = {r['organization_id'] for a in audits for r in a['completed'] if not r['prior_last_reviewed']}
assert sum(bool(r['Last Reviewed']) for r in rows) == 503 + len(newly_dated)
by_id = {r['Record ID']: r for r in rows}
for audit in audits:
    for reviewed in audit['completed']:
        record = by_id[reviewed['organization_id']]
        assert record['Last Reviewed'] >= reviewed['reviewed_on']
        assert reviewed['sources'] and reviewed['finding'] and reviewed['limitations']
        assert all(url in record['Source(s)'] for url in reviewed['sources'])
assert all(r['Service Area (as published)'] is not None for r in rows)
queue=json.loads((ROOT/'data/review-queue.json').read_text())
queued={r['organization_id']:r for r in queue['queue']}
assert queue['as_of']==RELEASE['released_on']
for row in rows:
    if not row['Category'].startswith('Out of scope') and not row['Website'].strip():
        assert row['Record ID'] in queued, 'Missing website must trigger review independently of its existing review date'
        assert queued[row['Record ID']]['priority']=='P1'
import build_review_queue as review_schedule
assert queue['intervals_days']=={'full-review':90,'routine-verification':180}
for row in rows:
    if row['Category'].startswith('Out of scope'):
        continue
    tier = review_schedule.review_tier(row)
    if row['Category'] in review_schedule.ALWAYS_FULL or not row['Service Area'].startswith(review_schedule.NATIONAL_PREFIXES):
        assert tier=='full-review', f"{row['Record ID']} must be on the 90-day full-review cycle"
    else:
        assert tier=='routine-verification', f"{row['Record ID']} must be on the 180-day routine-verification cycle"
    if row['Record ID'] in queued and row['Last Reviewed']:
        assert queued[row['Record ID']]['due_on']==(date.fromisoformat(row['Last Reviewed'])+timedelta(days=queue['intervals_days'][tier])).isoformat()
triggers=json.loads((ROOT/'data/review-triggers.json').read_text())['triggers']
for trigger in triggers:
    assert trigger['kind'] in review_schedule.TRIGGER_KINDS and trigger['reported_on'] and trigger['source']
    if not trigger.get('resolved_on'):
        assert queued[trigger['organization_id']]['priority']=='P0', 'Open review triggers must be reviewed immediately'
assert queue['open_triggers']==sum(not t.get('resolved_on') for t in triggers)
with (ROOT / 'b2b-relationships.csv').open(encoding='utf-8-sig') as f:
    relationships = list(csv.DictReader(f))
assert len(relationships) == 60
assert len({relationship_id(r) for r in relationships}) == 60
with tempfile.TemporaryDirectory() as temp:
    for module_name, filename in [('build_expungement','expungement.html'),('build_lawmakers','lawmakers.html'),('build_advocacy','advocacy.html'),('build_pennsylvania_advocacy','pennsylvania-advocacy.html'),('build_directory','directory.html'),('build_home','index.html'),('build_intake','intake.html'),('build_relationships','relationships.html'),('build_resources','resources.html'),('build_seeds','seeds.html'),('build_state','state.html'),('build_locations','locations.html'),('build_knowledge','knowledge.html'),('build_compare','compare.html')]:
        module = importlib.import_module(module_name)
        module.OUT = Path(temp) / filename
        module.main()
        generated = module.OUT.read_text()
        committed = (ROOT / filename).read_text()
        if generated != committed:
            first = next((i for i, (a, b) in enumerate(zip(generated, committed)) if a != b), min(len(generated), len(committed)))
            print(f'{filename} mismatch at character {first}', flush=True)
            print('expected:', repr(generated[max(0, first-100):first+250]), flush=True)
            print('committed:', repr(committed[max(0, first-100):first+250]), flush=True)
            raise AssertionError(f'{filename} requires rebuild')
for name in ['.zenodo.json']:
    archive = json.loads((ROOT / name).read_text())
    assert archive['version'] == RELEASE['version']
    assert archive['publication_date'] == RELEASE['released_on']
citation = (ROOT / 'CITATION.cff').read_text()
assert f"version: '{RELEASE['version']}'" in citation
assert f"date-released: '{RELEASE['released_on']}'" in citation
assert f'release v{RELEASE["version"]}' in (ROOT / 'index.html').read_text()
assert f'Current site release:** {RELEASE["version"]}' in (ROOT / 'README.md').read_text()
assert 'relationships.html' in (ROOT / 'sitemap.xml').read_text()
assert 'compare.html' in (ROOT / 'sitemap.xml').read_text()
from validate_comparison import validate as validate_comparison
validate_comparison(json.loads((ROOT / 'data/state-comparison.json').read_text(encoding='utf-8')))
print('PASS: record counts, IDs, review-date evidence, verification tiers, relationship coverage, generated pages and release metadata.')

withdrawn={o["id"] for o in load_directory()["organizations"] if o.get("scope")=="withdrawn"}
assert withdrawn=={"org-ab854d60bdb3"}
assert not any(r["Record ID"] in withdrawn for r in load_records(include_withdrawn=False))
assert "PreventionFIRST!" not in (ROOT/"directory.html").read_text()
assert "PreventionFIRST!" not in (ROOT/"data/public-organizations.json").read_text()
assert "PreventionFIRST!" not in (ROOT/"data/public-state.json").read_text()
