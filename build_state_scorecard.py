"""Measure every published state against the state completion standard.

Reads data/directory.json and data/state-standard.json and writes
data/state-scorecard.json and architecture/STATE_SCORECARD.md. Each pathway
gets an earned level (starter, partial or broad) computed from the data, the
measurements behind it and what is needed for the next level.
"""
import json
from datetime import date, timedelta
from pathlib import Path

import build_review_queue as review_schedule

ROOT = Path(__file__).resolve().parent
LEVELS = ['not-reviewed', 'starter', 'partial', 'broad']
PATHWAYS = ['dispensaries', 'seeds', 'records', 'rules', 'medical', 'business', 'community']
ROUTINE_DAYS = 180


def pct(n, d):
    return round(n / d, 3) if d else 0.0


def measure(data, standard, code):
    as_of = date.fromisoformat(data['as_of'])
    cfg = standard['states'][code]
    t = standard['thresholds']
    orgs = {o['id']: o for o in data['organizations']}
    evidence = {e['id']: e for e in data['evidence']}

    def services(pathway):
        # Business listings count only when published; consumer routes may belong to
        # organizations kept out of the business listings (scope 'retained').
        allowed = ('public',) if pathway == 'business' else ('public', 'retained', 'reference-only')
        return [s for s in data['services'] if code in s.get('listed_in', []) and pathway in s['pathway_ids']
                and orgs.get(s['organization_id'], {}).get('scope', 'public') in allowed]

    def gov(item):
        return any(evidence.get(k, {}).get('source_kind') == 'government' for k in item.get('evidence_ids', []))

    def state_coverage(s):
        return any(g['kind'] == 'state' and g.get('state') == code for g in s['coverage'])

    out = {}

    # Dispensaries: regulator-listed locations against the regulator's count.
    den = cfg['dispensary_denominator']
    locs = [l for l in data['locations'] if l['state'] == code and gov(l)]
    share = pct(len(locs), den['count'])
    age = (as_of - date.fromisoformat(cfg['location_source_retrieved_on'])).days
    lookup = bool(services('dispensaries')) or bool(next(s for s in data['states'] if s['code'] == code).get('official_regulator_url'))
    level = 'not-reviewed'
    if lookup:
        level = 'starter'
    if lookup and share >= t['dispensaries']['partial_share']:
        level = 'partial'
    if level == 'partial' and share >= t['dispensaries']['broad_share'] and age <= t['dispensaries']['max_source_age_days']:
        level = 'broad'
    out['dispensaries'] = dict(level=level, measures={'regulator_listed_locations': len(locs), 'regulator_count': den['count'],
        'regulator_count_as_of': den['as_of'], 'share': share, 'location_source_age_days': age},
        next=None if level == 'broad' else (f"Refresh locations from the regulator (source is {age} days old)" if share >= t['dispensaries']['broad_share']
            else f"List {max(0, round(t['dispensaries']['broad_share'] * den['count']) - len(locs))} more regulator-listed locations"))

    # Rules: core topics with government evidence and an effective date.
    aliases = standard['rule_topic_aliases']
    topics = {aliases.get(r['topic'], r['topic']) for r in data['rules'] if r['state'] == code and r.get('effective_on') and gov(r)}
    core = standard['core_rule_topics']
    have = [x for x in core if x in topics]
    missing = [x for x in core if x not in topics]
    n = len(have)
    level = 'broad' if n >= t['rules']['broad_topics'] else 'partial' if n >= t['rules']['partial_topics'] else 'starter' if (n or services('rules')) else 'not-reviewed'
    out['rules'] = dict(level=level, measures={'core_topics_covered': n, 'core_topics': len(core), 'missing_topics': missing},
        next=None if level == 'broad' else 'Add dated, officially sourced rules for: ' + ', '.join(missing))

    # Records: statewide route, service count, county-specific reach.
    rec = services('records')
    statewide = sum(state_coverage(s) for s in rec)
    counties = {g.get('county') for s in rec for g in s['coverage'] if g['kind'] == 'county' and g.get('state') == code}
    courts_file = ROOT / 'data/record-clearing-courts.json'
    if code == 'OH' and courts_file.exists():
        # Ohio's county court-search guide is county-specific record-relief help.
        counties |= {c['county'] for c in json.loads(courts_file.read_text())['courts']}
    cshare = pct(len(counties), cfg['counties'])
    level = 'not-reviewed'
    if rec:
        level = 'starter'
    if len(rec) >= t['records']['partial_services'] and statewide:
        level = 'partial'
    if level == 'partial' and cshare >= t['records']['broad_county_share']:
        level = 'broad'
    nxt = None
    if level != 'broad':
        need = []
        if len(rec) < t['records']['partial_services']:
            need.append(f"{t['records']['partial_services'] - len(rec)} more record-relief services")
        if not statewide:
            need.append('statewide coverage evidence on at least one route')
        if level == 'partial' or not need:
            need.append(f"county-specific help in {max(0, round(t['records']['broad_county_share'] * cfg['counties']) - len(counties))} more counties")
        nxt = '; '.join(need)
    out['records'] = dict(level=level, measures={'services': len(rec), 'statewide_routes': statewide, 'counties_with_specific_help': len(counties),
        'counties': cfg['counties'], 'county_share': cshare}, next=nxt)

    # Medical: official routes and patient support.
    med = services('medical')
    g = sum(gov(s) for s in med)
    ng = len(med) - g
    m = t['medical']
    level = 'not-reviewed'
    if med:
        level = 'starter'
    if len(med) >= m['partial_services'] and g >= m['partial_government']:
        level = 'partial'
    if level == 'partial' and len(med) >= m['broad_services'] and g >= m['broad_government'] and ng >= m['broad_non_government']:
        level = 'broad'
    out['medical'] = dict(level=level, measures={'services': len(med), 'government_sourced': g, 'support_organizations': ng},
        next=None if level == 'broad' else (f"Reach {m['partial_services']} medical routes with {m['partial_government']} officially sourced" if level != 'partial'
            else f"Reach {m['broad_services']} routes, {m['broad_government']} official and {m['broad_non_government']} patient-support organization"))

    # Community: groups plus current events.
    groups = services('community')
    upcoming = [e for e in data['events'] if e.get('state') == code and date.fromisoformat(e.get('ends_on') or e['starts_on']) >= as_of]
    items = len(groups) + len(upcoming)
    c = t['community']
    level = 'broad' if items >= c['broad_items'] and len(upcoming) >= c['broad_upcoming_events'] else 'partial' if items >= c['partial_items'] else 'starter' if items else 'not-reviewed'
    out['community'] = dict(level=level, measures={'groups': len(groups), 'upcoming_events': len(upcoming), 'items': items},
        next=None if level == 'broad' else (f"Reach {c['partial_items']} groups or upcoming events" if level != 'partial'
            else f"Reach {c['broad_items']} items with at least {c['broad_upcoming_events']} upcoming event"))

    # Seeds: no regulator denominator exists, so the ceiling is partial.
    seeds = services('seeds')
    with_fulfillment = sum(bool(s.get('fulfillment')) for s in seeds)
    level = 'partial' if with_fulfillment >= t['seeds']['partial_services'] else 'starter' if seeds else 'not-reviewed'
    out['seeds'] = dict(level=level, measures={'services': len(seeds), 'with_fulfillment_recorded': with_fulfillment},
        next='Broad needs a documented denominator; none exists for seed sellers' if level == 'partial'
            else f"Reach {t['seeds']['partial_services']} seed routes with fulfillment recorded")

    # Business: size, confirmed coverage, direct contact, categories, current reviews.
    biz = services('business')
    covered = contact = categorized = current = 0
    for s in biz:
        o = orgs[s['organization_id']]
        row = o.get('legacy_record')
        if row:
            covered += row['Service Area'] != 'Multistate, Ohio unconfirmed'
            categorized += bool(row.get('Category'))
            if row.get('Last Reviewed'):
                due = date.fromisoformat(row['Last Reviewed']) + timedelta(days=review_schedule.INTERVAL_DAYS[review_schedule.review_tier(row)])
                current += due > as_of
        else:
            covered += any(g2.get('state') == code for g2 in s['coverage'])
            categorized += bool(s.get('attributes', {}).get('category'))
            dates = [evidence[k]['reviewed_on'] for k in s.get('evidence_ids', []) if evidence.get(k, {}).get('reviewed_on')]
            current += bool(dates) and date.fromisoformat(max(dates)) + timedelta(days=ROUTINE_DAYS) > as_of
        contact += any(x['kind'] in ('phone', 'email') for x in o.get('contacts', []))
    nb = len(biz)
    b = t['business']
    ms = {'services': nb, 'coverage_confirmed_share': pct(covered, nb), 'direct_contact_share': pct(contact, nb),
          'categorized_share': pct(categorized, nb), 'current_review_share': pct(current, nb)}
    level = 'starter' if nb else 'not-reviewed'
    if nb >= b['partial_services'] and ms['coverage_confirmed_share'] >= b['partial_coverage_share'] and ms['direct_contact_share'] >= b['partial_contact_share']:
        level = 'partial'
    if (level == 'partial' and nb >= b['broad_services'] and ms['coverage_confirmed_share'] >= b['broad_coverage_share'] and ms['direct_contact_share'] >= b['broad_contact_share']
            and ms['categorized_share'] >= b['broad_categorized_share'] and ms['current_review_share'] >= b['broad_current_review_share']):
        level = 'broad'
    gaps = []
    target = 'broad' if level == 'partial' else 'partial'
    if nb < b[f'{target}_services']:
        gaps.append(f"{b[f'{target}_services'] - nb} more listings")
    checks = [('coverage', 'coverage_confirmed_share', covered, 'listings with confirmed in-state coverage'),
              ('contact', 'direct_contact_share', contact, 'listings with a phone or email'),
              ('categorized', 'categorized_share', categorized, 'categorized listings'),
              ('current_review', 'current_review_share', current, 'listings reviewed within policy')]
    for key, measure_key, have_n, label in checks:
        th = b.get(f'{target}_{key}_share')
        if th is not None and ms[measure_key] < th:
            need = -(-int(round(th * nb * 1000)) // 1000) - have_n
            gaps.append(f'{max(1, need)} more {label} (to {round(th * 100)}%)')
    out['business'] = dict(level=level, measures=ms, next=None if level == 'broad' else '; '.join(gaps) or None)
    return out


def build(data=None, standard=None):
    data = data or json.loads((ROOT / 'data/directory.json').read_text())
    standard = standard or json.loads((ROOT / 'data/state-standard.json').read_text())
    result = {'as_of': data['as_of'], 'standard_version': standard['version'], 'states': {}}
    for pack in data['states']:
        code = pack['code']
        if code not in standard['states'] or pack['publication_status'] not in ('live', 'pilot'):
            continue
        earned = measure(data, standard, code)
        declared = {p['pathway_id']: p['coverage_status'] for p in pack['pathways']}
        result['states'][code] = {'name': pack['name'], 'publication_status': pack['publication_status'],
            'pathways': {p: dict(declared=declared.get(p), **earned[p]) for p in PATHWAYS}}
    codes = list(result['states'])
    lines = ['# State scorecard', '', f"As of {result['as_of']}. Standard version {result['standard_version']}: [STATE_COMPLETION_STANDARD.md](STATE_COMPLETION_STANDARD.md). "
             'Regenerate with `python build_state_scorecard.py`. Levels are earned from the data; a state is complete when every pathway is broad, except seeds, whose ceiling is partial.', '',
             '| Pathway | ' + ' | '.join(result['states'][c]['name'] for c in codes) + ' |', '| --- |' + ' --- |' * len(codes)]
    for p in PATHWAYS:
        lines.append(f'| {p} | ' + ' | '.join(result['states'][c]['pathways'][p]['level'] for c in codes) + ' |')
    for c in codes:
        st = result['states'][c]
        lines += ['', f"## {st['name']} ({st['publication_status']})", '', '| Pathway | Earned | Measures | Next level needs |', '| --- | --- | --- | --- |']
        for p in PATHWAYS:
            r = st['pathways'][p]
            meas = '; '.join(f"{k.replace('_', ' ')}: {', '.join(v) if isinstance(v, list) else v}" for k, v in r['measures'].items())
            lines.append(f"| {p} | {r['level']} | {meas} | {r['next'] or '—'} |")
    return result, json.dumps(result, indent=2, ensure_ascii=False) + '\n', '\n'.join(lines) + '\n'


def main():
    result, json_text, md_text = build()
    (ROOT / 'data/state-scorecard.json').write_text(json_text)
    (ROOT / 'architecture/STATE_SCORECARD.md').write_text(md_text)
    for code, st in result['states'].items():
        print(code, {p: v['level'] for p, v in st['pathways'].items()})
        for p, v in st['pathways'].items():
            if v['declared'] != v['level']:
                print(f"  {p}: declared {v['declared']}, earned {v['level']}")


if __name__ == '__main__':
    main()
