import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from directory_data import load_records
from cleanup_directory import normalize
rows=load_records();report=json.loads((ROOT/'data/review-migration-report.json').read_text());assert len(report['restored_review_dates'])==485;assert len(report['rows_without_dated_review'])==61
for r in rows:
 dates=re.findall(r'(\d{4}-\d{2}-\d{2}); source pages retrieved and reviewed',r['Seed Source'])
 if dates:assert r['Last Reviewed']>=max(dates)
 assert r['Service Area']==normalize(r['Service Area (as published)'])
assert normalize('Nationwide; no Ohio client identified')=='Multistate, Ohio unconfirmed'
assert normalize('Ohio statewide')=='Ohio statewide'
assert normalize('Central Ohio').startswith('Ohio regional:')
x=json.loads((ROOT/'data/strains/ancestry.json').read_text())
for s in x['strains']:
 if s.get('source_link_only'):assert not s['reported_effects'] and not s['history'] and s['review_count'] is None
print('PASS: historical dates, controlled geography, original wording and link-only reference profiles.')
