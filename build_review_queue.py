"""Build the evidence-review backlog from canonical records and scoped audits.

Review schedule (owner decision, October 21, 2026; see architecture/REVIEW_POLICY.md):
- Full review every 90 days for Ohio operators, testing labs and Ohio-based providers.
- Routine verification every 180 days for national and multistate vendors.
- Immediate review for any open trigger in data/review-triggers.json
  (closure, license action, ownership change or material correction).
"""
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FULL, ROUTINE = 'full-review', 'routine-verification'
INTERVAL_DAYS = {FULL: 90, ROUTINE: 180}
ALWAYS_FULL = ('Testing Labs', 'Cultivator / Processor / Dispensary')
NATIONAL_PREFIXES = ('Nationwide', 'Multistate')
TRIGGER_KINDS = {
    'closure': 'Reported closure',
    'license-action': 'Reported license action',
    'ownership-change': 'Reported ownership change',
    'material-correction': 'Reported material correction',
}
FORECAST_DAYS = 60
NEXT_ACTION = {
    FULL: 'Full review: confirm operating status, license where applicable, services, contacts and Ohio coverage from primary sources; record source dates and field-level limits.',
    ROUTINE: 'Routine verification: confirm the website resolves, the cannabis service page is live, a contact route works and Ohio service coverage is still stated; record as a routine verification, not a full review.',
}


def review_tier(row):
    """Ohio operators and Ohio-based providers get full reviews; national and multistate vendors get routine verification."""
    if row['Category'] in ALWAYS_FULL:
        return FULL
    return ROUTINE if row['Service Area'].startswith(NATIONAL_PREFIXES) else FULL


def load_triggers(public_ids):
    path = ROOT / 'data/review-triggers.json'
    triggers = json.loads(path.read_text())['triggers'] if path.exists() else []
    open_triggers = {}
    for t in triggers:
        if t['kind'] not in TRIGGER_KINDS:
            raise ValueError(f"Unknown review trigger kind {t['kind']!r} for {t['organization_id']}")
        if not t.get('reported_on') or not t.get('source'):
            raise ValueError(f"Review trigger for {t['organization_id']} needs reported_on and source")
        if t['organization_id'] not in public_ids:
            raise ValueError(f"Review trigger names an unknown or non-public organization: {t['organization_id']}")
        if not t.get('resolved_on'):
            open_triggers.setdefault(t['organization_id'], []).append(t)
    return open_triggers


def main(as_of=None):
    data = json.loads((ROOT / 'data/directory.json').read_text())
    as_of = as_of or json.loads((ROOT / 'release.json').read_text())['released_on']
    as_of_date = date.fromisoformat(as_of)
    public = [o for o in data['organizations'] if o['scope'] == 'public' and 'legacy_record' in o]
    open_triggers = load_triggers({o['id'] for o in public})
    attempts = {}
    for path in sorted((ROOT / 'data/reviews').glob('*.json')):
        for item in json.loads(path.read_text()).get('blocked', []):
            attempts[item['organization_id']] = item
    queue, upcoming = [], []
    tiers = Counter()
    for org in public:
        row = org['legacy_record']
        tier = review_tier(row)
        tiers[tier] += 1
        due_on = None
        if row['Last Reviewed']:
            due_on = date.fromisoformat(row['Last Reviewed']) + timedelta(days=INTERVAL_DAYS[tier])
        reasons = []
        triggers = open_triggers.get(org['id'], [])
        for t in triggers:
            reasons.append(f"{TRIGGER_KINDS[t['kind']]} ({t['reported_on']}): review immediately")
        if row['Verification Tier'] == 'Open issue':
            reasons.append('Resolve the named open issue')
        if not row['Website'].strip():
            reasons.append('No published website or contact-page route')
        if not row['Last Reviewed']:
            reasons.append('No recorded evidence-review date')
        elif due_on <= as_of_date:
            reasons.append(f"{'Full review' if tier == FULL else 'Routine verification'} due ({INTERVAL_DAYS[tier]}-day cycle)")
        if not reasons:
            if due_on and due_on <= as_of_date + timedelta(days=FORECAST_DAYS):
                upcoming.append({'organization_id': org['id'], 'tier': tier, 'category': row['Category'], 'due_on': due_on.isoformat()})
            continue
        direct_use = row['Category'] in ('Testing Labs', 'Cultivator / Processor / Dispensary', 'Nonprofit & Advocacy')
        missing_route = not row['Website'].strip()
        if triggers:
            priority = 'P0'
        elif row['Verification Tier'] == 'Open issue' or direct_use or missing_route:
            priority = 'P1'
        else:
            priority = 'P2'
        attempt = attempts.get(org['id'])
        queue.append({'organization_id': org['id'], 'name': row['Organization / Business Name'],
                      'priority': priority, 'tier': tier, 'category': row['Category'], 'reasons': reasons,
                      'last_reviewed': row['Last Reviewed'] or None,
                      'due_on': due_on.isoformat() if due_on else None,
                      'website': row['Website'], 'sources': row['Source(s)'], 'notes': row['Notes'],
                      'triggers': triggers, 'last_attempt': attempt,
                      'next_action': attempt['next_action'] if attempt else NEXT_ACTION[tier]})
    queue.sort(key=lambda r: (r['priority'], not bool(r['last_attempt']), r['category'], r['name'].casefold()))
    upcoming.sort(key=lambda r: (r['due_on'], r['tier'], r['category']))
    forecast = {}
    for item in upcoming:
        week = date.fromisoformat(item['due_on'])
        week_start = (week - timedelta(days=week.weekday())).isoformat()
        forecast.setdefault(week_start, Counter())[item['tier']] += 1
    policy = ('P0: open review triggers (reported closure, license action, ownership change or material correction), reviewed immediately. '
              'P1: open issues, operators/labs/community resources due or undated, or missing websites. P2: remaining due or undated business providers. '
              'Ohio operators, testing labs and Ohio-based providers receive a full review every 90 days; national and multistate vendors receive a routine verification every 180 days. '
              'Blocked retrieval is an attempt, not a verified review.')
    result = {'as_of': as_of, 'policy': policy,
              'intervals_days': INTERVAL_DAYS,
              'public_organizations': len(public),
              'public_by_tier': dict(tiers),
              'public_without_review_date': sum(not o['legacy_record']['Last Reviewed'] for o in public),
              'public_open_issues': sum(o['legacy_record']['Verification Tier'] == 'Open issue' for o in public),
              'open_triggers': sum(len(v) for v in open_triggers.values()),
              'priority_counts': dict(Counter(r['priority'] for r in queue)),
              'forecast_window_days': FORECAST_DAYS,
              'forecast_by_week': {week: dict(counts) for week, counts in sorted(forecast.items())},
              'queue': queue, 'upcoming': upcoming}
    (ROOT / 'data/review-queue.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    lines = ['# Evidence review queue', '', f'As of {as_of}. Regenerate with `python build_review_queue.py`. Policy: [REVIEW_POLICY.md](REVIEW_POLICY.md).', '',
             policy, '',
             f"{len(public)} published listings: {tiers[FULL]} on the 90-day full-review cycle, {tiers[ROUTINE]} on the 180-day routine-verification cycle. "
             f"{result['public_without_review_date']} lack a review date; {result['public_open_issues']} have a named open issue; {result['open_triggers']} open review triggers. Overlapping records appear once.", '',
             'Historical evidence and editorial inclusion remain intact. A review date identifies the latest scoped evidence review; the audit records which fields were checked and which still need work.', '',
             '| Priority | Listing | Reason | Last review |', '| --- | --- | --- | --- |']
    for r in queue:
        name = r['name'].replace('|', '\\|')
        lines.append(f"| {r['priority']} | [{name}](https://travisvought-byte.github.io/ohio-cannabis-directory/directory.html?org={r['organization_id']}) | {'; '.join(r['reasons'])} | {r['last_reviewed'] or 'Not recorded'} |")
    lines += ['', f'## Coming due in the next {FORECAST_DAYS} days', '']
    if forecast:
        lines += ['| Week of | Full reviews | Routine verifications |', '| --- | --- | --- |']
        for week, counts in sorted(forecast.items()):
            lines.append(f"| {week} | {counts[FULL]} | {counts[ROUTINE]} |")
    else:
        lines.append('Nothing else comes due in this window.')
    lines += ['', '## Retrieval blockers', '']
    for item in attempts.values():
        lines += [f"- **{item['name']}** ({item['attempted_on']}): {item['result']} Next: {item['next_action']}"]
    lines += ['', '## Completed reviews', '', 'See `data/reviews/` for dated source reviews, exact field changes and remaining limitations. A failed fetch does not establish closure.', '']
    (ROOT / 'architecture/REVIEW_QUEUE.md').write_text('\n'.join(lines))
    print(f"Review queue: {len(queue)} records; {result['priority_counts']}; {len(upcoming)} more due within {FORECAST_DAYS} days; tiers {dict(tiers)}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', help='ISO date for a read-only diagnostic; defaults to the reproducible release date')
    main(parser.parse_args().as_of)
