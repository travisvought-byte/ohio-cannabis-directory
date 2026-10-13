"""Build the evidence-review backlog from canonical records and scoped audits."""
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    data = json.loads((ROOT / 'data/directory.json').read_text())
    as_of = json.loads((ROOT / 'release.json').read_text())['released_on']
    public = [o for o in data['organizations'] if o['scope'] == 'public' and 'legacy_record' in o]
    attempts = {}
    for path in sorted((ROOT / 'data/reviews').glob('*.json')):
        for item in json.loads(path.read_text()).get('blocked', []):
            attempts[item['organization_id']] = item
    queue = []
    for org in public:
        row = org['legacy_record']
        reasons = []
        if row['Verification Tier'] == 'Open issue':
            reasons.append('Resolve the named open issue')
        if not row['Website'].strip():
            reasons.append('No published website or contact-page route')
        if not row['Last Reviewed']:
            reasons.append('No recorded evidence-review date')
        elif (date.fromisoformat(as_of) - date.fromisoformat(row['Last Reviewed'])).days >= 90:
            reasons.append('Evidence review is at least 90 days old')
        if not reasons:
            continue
        direct_use = row['Category'] in ('Testing Labs', 'Cultivator / Processor / Dispensary', 'Nonprofit & Advocacy')
        missing_route = not row['Website'].strip()
        priority = 'P1' if row['Verification Tier'] == 'Open issue' or direct_use or missing_route else 'P2'
        attempt = attempts.get(org['id'])
        queue.append({'organization_id': org['id'], 'name': row['Organization / Business Name'],
                      'priority': priority, 'category': row['Category'], 'reasons': reasons,
                      'last_reviewed': row['Last Reviewed'] or None, 'website': row['Website'],
                      'sources': row['Source(s)'], 'notes': row['Notes'],
                      'last_attempt': attempt,
                      'next_action': attempt['next_action'] if attempt else
                      'Read primary sources; check identity, actionable contact, service relevance and Ohio coverage. Record field-level limits; do not infer license, shipping or current stock.'})
    queue.sort(key=lambda r: (r['priority'], not bool(r['last_attempt']), r['category'], r['name'].casefold()))
    result = {'as_of': as_of, 'policy': 'P1: open issues, undated operators/labs/community resources or missing websites. P2: remaining undated business providers. Reviews at least 90 days old also enter the backlog. Blocked retrieval is an attempt, not a verified review.',
              'public_organizations': len(public),
              'public_without_review_date': sum(not o['legacy_record']['Last Reviewed'] for o in public),
              'public_open_issues': sum(o['legacy_record']['Verification Tier'] == 'Open issue' for o in public),
              'priority_counts': dict(Counter(r['priority'] for r in queue)), 'queue': queue}
    (ROOT / 'data/review-queue.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    lines = ['# Evidence review queue', '', f'As of {as_of}. Regenerate with `python build_review_queue.py`.', '',
             result['policy'], '', f"{result['public_without_review_date']} published listings lack a review date; {result['public_open_issues']} have a named open issue. Overlapping records appear once.", '',
             'Historical evidence and editorial inclusion remain intact. A review date identifies the latest scoped evidence review; the audit records which fields were checked and which still need work.', '',
             '| Priority | Listing | Reason | Last review |', '| --- | --- | --- | --- |']
    for r in queue:
        name = r['name'].replace('|', '\\|')
        lines.append(f"| {r['priority']} | [{name}](https://travisvought-byte.github.io/ohio-cannabis-directory/directory.html?org={r['organization_id']}) | {'; '.join(r['reasons'])} | {r['last_reviewed'] or 'Not recorded'} |")
    lines += ['', '## Retrieval blockers', '']
    for item in attempts.values():
        lines += [f"- **{item['name']}** ({item['attempted_on']}): {item['result']} Next: {item['next_action']}"]
    lines += ['', '## Completed reviews', '', 'See `data/reviews/` for dated source reviews, exact field changes and remaining limitations. A failed fetch does not establish closure.', '']
    (ROOT / 'architecture/REVIEW_QUEUE.md').write_text('\n'.join(lines))
    print(f"Review queue: {len(queue)} records; {result['priority_counts']}; {result['public_without_review_date']} public undated")


if __name__ == '__main__':
    main()
