"""Combine each state's normalized snapshots into data/state-retail-locations.json.

One entry per state. When a state has more than one list (say adult-use and medical), the
same storefront can appear on both; those rows are merged into one location that carries
both kinds and every license number. Two rows are the same location when they share a
license number, or the same street address and ZIP with a matching name or licensee.

build_national.py renders this file as the "Where to buy" list on each state page.

Run: python -m pipeline.merge
"""
from collections import defaultdict

from pipeline.common import OUTPUT, SNAPSHOTS, load_json, norm_key, plus_days, registry, save_json, today

KIND = {'retail': 'adult-use', 'medical-dispensary': 'medical', 'retail-and-medical': 'adult-use and medical'}


def address_line(r):
    if r.get('address'):
        return r['address']
    tail = ' '.join(p for p in (r.get('state'), r.get('zip')) if p)
    return ', '.join(p for p in (r.get('street'), r.get('city'), tail) if p)


def similar(a, b):
    a, b = norm_key(a), norm_key(b)
    if not a or not b:
        return False
    return a in b or b in a


def same(x, y):
    lx, ly = set(x['_licenses']), set(y['_licenses'])
    if lx & ly:
        return True
    if x['_addr'] and x['_addr'] == y['_addr']:
        return (similar(x['name'], y['name']) or similar(x.get('licensee'), y.get('licensee'))
                or similar(x['name'], y.get('licensee')) or similar(x.get('licensee'), y['name']))
    return False


def merge_state(snaps):
    merged, dupes = [], 0
    by_addr = defaultdict(list)
    for snap in snaps:
        kind = KIND.get(snap['topic'], snap['topic'])
        for r in snap['rows']:
            loc = {k: r[k] for k in ('name', 'licensee', 'phone', 'county', 'website', 'lat', 'lon', 'opened') if r.get(k)}
            if loc.get('licensee') and norm_key(loc['licensee']) == norm_key(loc['name']):
                loc.pop('licensee')
            loc['address'] = address_line(r)
            loc['city'] = r.get('city')
            loc['kinds'] = [kind]
            loc['_licenses'] = [r['license_number']] if r.get('license_number') else []
            loc['_addr'] = norm_key(r.get('street') or r.get('address')) + (r.get('zip') or '') if (r.get('street') or r.get('address')) else ''
            match = next((m for m in by_addr.get(loc['_addr'], []) if same(m, loc)), None) if loc['_addr'] else None
            if match is None:
                match = next((m for m in merged if set(m['_licenses']) & set(loc['_licenses'])), None) if loc['_licenses'] else None
            if match is not None:
                dupes += 1
                for k in ('phone', 'county', 'website', 'lat', 'lon', 'licensee', 'opened'):
                    if not match.get(k) and loc.get(k):
                        match[k] = loc[k]
                match['kinds'] = sorted(set(match['kinds']) | set(loc['kinds']))
                match['_licenses'] = sorted(set(match['_licenses']) | set(loc['_licenses']))
                continue
            merged.append(loc)
            by_addr[loc['_addr']].append(loc)
    out = []
    for m in merged:
        m['licenses'] = m.pop('_licenses')
        m.pop('_addr')
        m['kind'] = ' and '.join(m.pop('kinds'))
        if not m['licenses']:
            m.pop('licenses')
        if not m.get('city'):
            m.pop('city', None)
        out.append(m)
    out.sort(key=lambda m: ((m.get('city') or '').lower(), m['name'].lower()))
    return out, dupes


def build():
    reg = registry()
    names = reg['us_jurisdictions']
    groups = defaultdict(list)
    for source in reg['sources']:
        if source['topic'] not in KIND or source['jurisdiction'] not in names:
            continue
        snap = load_json(SNAPSHOTS / f'{source["id"]}.json')
        if snap:
            groups[source['jurisdiction']].append((source, snap))
    states = []
    for code in sorted(groups):
        pairs = groups[code]
        locations, dupes = merge_state([s for _, s in pairs])
        retrieved = min(s['retrieved_on'] for _, s in pairs)
        cadence = min(src.get('cadence_days', 30) for src, _ in pairs)
        label = pairs[0][0]['label'] if len(pairs) == 1 else pairs[0][0].get('merged_label', 'licensed dispensaries')
        states.append({
            'state': code,
            'label': label,
            'retrieved_on': retrieved,
            'recheck_on': plus_days(retrieved, cadence),
            'evidence_level': pairs[0][1]['evidence_level'],
            'counts': {'source_rows': sum(s['export_rows'] for _, s in pairs),
                       'kept_rows': sum(s['kept_rows'] for _, s in pairs),
                       'duplicates_merged': dupes, 'locations': len(locations)},
            'sources': [{'id': src['id'], 'kind': 'regulator', 'scope': 'state', 'publisher': snap['publisher'],
                         'title': snap['title'], 'url': snap['landing_url'], 'download_url': snap['download_url'],
                         'retrieved_on': snap['retrieved_on'], 'evidence_level': snap['evidence_level'],
                         'kept_rule': snap['kept_rule'], 'limitations': snap['limitations']} for src, snap in pairs],
            'locations': locations,
        })
    data = {
        'schema_version': 1,
        'as_of': max((s['retrieved_on'] for s in states), default=today()),
        'purpose': ("Licensed cannabis stores state by state, copied by the source pipeline (pipeline/) from each "
                    "regulator's own published list. Generated by python -m pipeline.merge; do not hand-edit. "
                    "Names and addresses are as the regulator published them (all-capital text is softened to "
                    "title case). A store missing here may have opened after the list was retrieved."),
        'states': states,
    }
    save_json(OUTPUT, data)
    return data


def main():
    data = build()
    for s in data['states']:
        print(f'{s["state"]}: {s["counts"]["locations"]} locations ({s["counts"]["duplicates_merged"]} duplicates merged)')


if __name__ == '__main__':
    main()
