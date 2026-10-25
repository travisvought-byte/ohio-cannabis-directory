"""Check the PA research batch without promoting it to public directory data."""
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]

def validate(batch, source_map, directory):
    errors = []
    def need(ok, message):
        if not ok: errors.append(message)
    def valid_date(value):
        try: return date.fromisoformat(value)
        except (TypeError, ValueError): return None
    def public_url(value):
        return isinstance(value, str) and urlparse(value).scheme in ('http', 'https') and bool(urlparse(value).netloc)
    need(batch['batch_id'] == source_map['batch_id'], 'batch IDs do not match')
    need(batch['publication_status'] == 'research-only', 'research batch must remain research-only')
    cutoff = valid_date(batch['reviewed_on'])
    need(bool(cutoff), 'batch review date is invalid')
    sources = {s['id']:s for s in source_map['sources']}
    need(len(sources) == len(source_map['sources']), 'duplicate source IDs')
    for s in sources.values():
        need(public_url(s['url']) and bool(s.get('publisher')), s['id']+': missing source URL or publisher')
        reviewed = valid_date(s.get('reviewed_on'))
        retrieved = valid_date(s.get('retrieved_on'))
        if s['retrieval_status'] == 'reviewed':
            need(bool(reviewed and retrieved and cutoff and reviewed <= cutoff and retrieved <= cutoff), s['id']+': invalid review/retrieval dates')
        else:
            need(s.get('reviewed_on') is None, s['id']+': failed attempt cannot have a review date')
    def references(claim, owner):
        ids = claim.get('source_ids', [])
        need(bool(ids), owner+': missing source references')
        for sid in ids:
            need(sid in sources, owner+': unknown source '+sid)
            if sid in sources: need(sources[sid]['retrieval_status'] == 'reviewed', owner+': unreviewed source '+sid)
        reviewed = valid_date(claim.get('reviewed_on'))
        need(bool(reviewed and cutoff and reviewed <= cutoff), owner+': invalid claim review date')
    ids = set()
    permanent = {o['id'] for o in directory['organizations']}
    pathways = {p['id'] for p in directory['pathways']}
    for c in batch['candidates']:
        need(c['candidate_id'] not in ids, 'duplicate candidate '+c['candidate_id']);ids.add(c['candidate_id'])
        need(c['publication_status'] == 'research-only', c['candidate_id']+': candidate must remain research-only')
        need(c['state'] == 'PA' and set(c['pathway_ids']) <= pathways, c['candidate_id']+': invalid geography or pathway')
        need(public_url(c['next_step_url']), c['candidate_id']+': invalid next step')
        need(c['existing_organization_id'] is None or c['existing_organization_id'] in permanent, c['candidate_id']+': unknown permanent identity')
        for claim in c['claims']+c['locations']: references(claim, c['candidate_id'])
    summary = batch['summary']
    need(summary['candidate_count'] == len(batch['candidates']), 'candidate count does not reconcile')
    need(summary['proposed_existing_identity_matches'] == sum(bool(c['existing_organization_id']) for c in batch['candidates']), 'existing identity count does not reconcile')
    need(summary['sample_location_count'] == sum(len(c['locations']) for c in batch['candidates']), 'location count does not reconcile')
    need({p['pathway_id'] for p in batch['pathway_summary']} == pathways, 'all pathways must report coverage')
    for p in batch['pathway_summary']:
        need(p['candidate_count'] == sum(p['pathway_id'] in c['pathway_ids'] for c in batch['candidates']), p['pathway_id']+': count does not reconcile')
    for attempt in source_map['retrieval_attempts']:
        need(attempt.get('reviewed_on') is None, 'failed retrieval must not receive a review date')
    return errors

def main():
    batch = json.loads((ROOT/'data/research/pennsylvania-2026-10-24-candidates.json').read_text())
    sources = json.loads((ROOT/'data/research/pennsylvania-2026-10-24-sources.json').read_text())
    directory = json.loads((ROOT/'data/directory.json').read_text())
    errors = validate(batch, sources, directory)
    if errors: raise SystemExit('\n'.join(errors))
    print(f"PASS PA research: {len(batch['candidates'])} candidates, {len(sources['sources'])} sources, stable identity references, claim dates and publication boundaries.")
if __name__ == '__main__': main()
