"""Validate the consolidated Drive research without importing public records."""
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'data/research/pennsylvania-2026-10-30-drive-mining'


def validate():
    manifest = json.loads((PACKAGE / 'manifest.json').read_text())
    errors = []

    def need(condition, message):
        if not condition:
            errors.append(message)

    def url(value, blank=False):
        parsed = urlparse(value)
        return (blank and value == '') or (parsed.scheme in ('https', 'http') and bool(parsed.netloc))

    def checked(value):
        try:
            return date.fromisoformat(value) <= date.fromisoformat(manifest['snapshot_on'])
        except (TypeError, ValueError):
            return False

    need(manifest['publication_status'] == 'research-only', 'Manifest promotes research')
    payloads = {}
    for filename, entry in manifest['files'].items():
        need(Path(filename).name == filename and filename.endswith('.json'), 'Unsafe package filename')
        path = PACKAGE / filename
        raw = path.read_bytes()
        need(hashlib.sha256(raw).hexdigest() == entry['sha256'], f'{filename}: checksum mismatch')
        data = json.loads(raw)
        payloads[filename] = data
        need(data['publication_status'] == 'research-only', f'{filename}: publication boundary lost')
        need(data['source_spreadsheet_url'] == manifest['source_spreadsheet_url'], f'{filename}: Drive provenance mismatch')

    candidates = payloads['candidates.json']['candidates']
    need(len(candidates) == manifest['candidate_count'] == 178, 'Candidate count mismatch')
    ids = [c['candidate_id'] for c in candidates]
    need(len(ids) == len(set(ids)), 'Duplicate candidate IDs')
    need(set(ids) == {f'PA-N100-{i:03d}' for i in range(1, 101)} | {f'PA-9P-{i:03d}' for i in range(1, 79)}, 'Missing or reassigned Drive candidate IDs')
    need(dict(Counter(c['pa_connection_type'] for c in candidates)) == manifest['candidate_pa_connection_counts'], 'PA connection totals mismatch')
    need(dict(Counter(c['review_status'] for c in candidates)) == manifest['candidate_review_status_counts'], 'Review status totals mismatch')
    for candidate in candidates:
        cid = candidate['candidate_id']
        need(candidate['publication_status'] == 'research-only', f'{cid}: promoted candidate')
        need(candidate['review_status'] in ('Needs verification', 'Needs PA evidence'), f'{cid}: unexpected approval')
        need(bool(candidate['name_as_staged'] and candidate['category_as_staged']), f'{cid}: missing identity/category')
        need(checked(candidate['source_checked_on']), f'{cid}: invalid source date')
        need(url(candidate['discovery_source_url']), f'{cid}: invalid discovery source')
        for field in ('pa_corroboration_url', 'provider_url'):
            need(url(candidate[field], blank=True), f'{cid}: invalid {field}')
        need(bool(re.fullmatch(r'[0-9a-f]{64}', candidate['source_sha256'])), f'{cid}: invalid evidence hash')
        need(bool(candidate['identity_reconciliation'] and candidate['next_check']), f'{cid}: unresolved work missing')
        if candidate['pa_connection_type'] == 'Needs PA evidence':
            need(candidate['review_status'] == 'Needs PA evidence', f'{cid}: PA uncertainty erased')

    count_fields = {'historical-mentions.json': 'historical_mention_count',
                    'biocontrol-leads.json': 'biocontrol_discovery_lead_count',
                    'document-index.json': 'indexed_document_count',
                    'source-paths.json': 'source_path_count',
                    'mining-passes.json': 'mining_pass_count'}
    for filename, field in count_fields.items():
        need(len(payloads[filename]['records']) == manifest[field], f'{filename}: record count mismatch')

    passes = payloads['mining-passes.json']['records']
    need({p['Pass'] for p in passes} == set(range(1, 10)), 'Nine mining passes not preserved')
    additional = [c for c in candidates if c['drive_origin']['mining_pass'] is not None]
    for mining_pass in passes:
        records = [c for c in additional if c['drive_origin']['mining_pass'] == mining_pass['Pass']]
        need(len(records) == mining_pass['New candidates'], 'Pass yield mismatch')
        missing_pa = sum(c['pa_connection_type'] == 'Needs PA evidence' for c in records)
        need(missing_pa == mining_pass['Needs PA evidence'], 'Pass PA uncertainty mismatch')
        need(len(records) - missing_pa == mining_pass['PA connection documented'], 'Pass PA connection mismatch')

    documents = payloads['document-index.json']['records']
    need(len({d['Document ID'] for d in documents}) == len(documents), 'Duplicate application document IDs')
    for document in documents:
        need(document['Publication'] == 'Research only', 'Indexed application was promoted')
        need(url(document['PDF URL']), 'Invalid application URL')
    applications = {d['Application ID'] for d in documents}
    for mention in payloads['historical-mentions.json']['records']:
        need(mention['Application ID'] in applications, 'Historical mention has no indexed application')
        need(mention['Publication'] == 'Research only', 'Historical mention was promoted')
        need(isinstance(mention['PDF page'], int) and mention['PDF page'] > 0, 'Invalid PDF page')
        need(url(mention['Source URL']) and mention['Source URL'].endswith(f"#page={mention['PDF page']}"), 'Historical page link mismatch')
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS Drive mining: 178 research candidates, 9 passes, 39 historical mentions, '
          '24 biocontrol leads, 387 indexed PDFs; checksums, provenance and publication boundaries intact.')


if __name__ == '__main__':
    validate()
