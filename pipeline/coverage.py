"""Rank thin state and country pages, so the next mining batch goes where it matters most.

Reads the published data (nothing is fetched) and writes:
  data/pipeline-coverage.json         machine-readable, one row per state and country
  architecture/PIPELINE_COVERAGE.md   the same, readable, with the source queue

A page is "thin" when it has a legal market but is missing what a visitor needs: a store
list from the regulator, a fresh copy of it, the official state link, answers to the
shared law questions, or a patient guide where medical use is legal.

Priority = market weight x gap points. Market weight: adult use 3, medical only 2,
limited or varies locally 1, not permitted 0 (a closed market has nothing to list).

Run: python -m pipeline.coverage
"""
from datetime import date

from pipeline.common import COVERAGE_JSON, COVERAGE_MD, FETCH_LOG, ROOT, load_json, registry, save_json, today

WEIGHT = {'allowed': 3, 'medical-only': 2, 'limited': 1, 'varies-locally': 1, 'not-permitted': 0, 'not-reviewed': 1}
STALE_DAYS = 60


def age(iso, ref):
    return (date.fromisoformat(ref) - date.fromisoformat(iso)).days if iso else None


def us_rows(reg, log, ref):
    perm = load_json(ROOT / 'data/state-permissions.json')
    answers = {}
    for a in perm['answers']:
        answers.setdefault(a['state'], {})[a['question']] = a
    total_q = len(perm['questions'])
    medical_guides = {s['state'] for s in load_json(ROOT / 'data/medical-programs.json')['states']}
    hand = {s['state']: s for s in load_json(ROOT / 'data/medical-dispensaries.json')['states']}
    mined = {s['state']: s for s in (load_json(ROOT / 'data/state-retail-locations.json', {'states': []})['states'])}
    packs = load_json(ROOT / 'data/public-locations.json')['locations']
    pack_counts = {}
    for loc in packs:
        pack_counts[loc['state']] = pack_counts.get(loc['state'], 0) + 1
    state_packs = set(load_json(ROOT / 'data/state-scorecard.json')['states'])
    rows = []
    for code, name in perm['jurisdictions'].items():
        a = answers.get(code, {})
        adult = a.get('adult-use', {}).get('status', 'not-reviewed')
        medical = a.get('medical', {}).get('status', 'not-reviewed')
        market = adult if adult == 'allowed' else ('medical-only' if medical in ('allowed', 'medical-only') else adult)
        if code in pack_counts:
            stores, list_from, list_age = pack_counts[code], 'state directory pack', None
        elif code in mined:
            stores, list_from, list_age = mined[code]['counts']['locations'], 'source pipeline', age(mined[code]['retrieved_on'], ref)
        elif code in hand:
            stores, list_from, list_age = len(hand[code]['locations']), 'hand-copied regulator list', age(hand[code]['source']['retrieved_on'], ref)
        else:
            stores, list_from, list_age = 0, None, None
        srcs = [s for s in reg['sources'] if s['jurisdiction'] == code]
        gaps = []
        if WEIGHT.get(market, 0):
            if not stores:
                gaps.append(('no store list', 3))
            elif list_age is not None and list_age > STALE_DAYS:
                gaps.append((f'store list {list_age} days old', 1))
        if code not in perm['official_links']:
            gaps.append(('no official state link', 1))
        missing = total_q - len(a)
        if missing:
            gaps.append((f'{missing} law questions unanswered', 1 + missing // 4))
        if medical in ('allowed', 'medical-only') and code not in medical_guides:
            gaps.append(('no patient guide', 1))
        if code not in state_packs:
            gaps.append(('no full state guide (business, records, community)', 1))
        points = sum(p for _, p in gaps)
        rows.append({
            'code': code, 'name': name, 'market': market, 'stores': stores, 'store_list_from': list_from,
            'store_list_age_days': list_age, 'law_answers': f'{len(a)}/{total_q}',
            'registry': {st: sum(1 for s in srcs if s.get('status') == st) for st in ('active', 'queued', 'blocked') if any(s.get('status') == st for s in srcs)},
            'last_fetch': {s['id']: ('ok' if log.get(s['id'], {}).get('ok') else ('blocked' if log.get(s['id'], {}).get('blocked') else ('failed' if s['id'] in log else 'not run'))) for s in srcs if s['fetch']['method'] != 'manual'},
            'gaps': [g for g, _ in gaps], 'priority': WEIGHT.get(market, 0) * points,
        })
    rows.sort(key=lambda r: (-r['priority'], r['name']))
    return rows


def world_rows(reg):
    world = load_json(ROOT / 'data/world-permissions.json')
    wtb = load_json(ROOT / 'data/world-where-to-buy.json')['countries']
    total_q = len(world['questions'])
    rows = []
    for code, c in world['countries'].items():
        a = c.get('answers', {})
        adult = a.get('adult-use', {}).get('status', 'not-reviewed')
        medical = a.get('medical', {}).get('status', 'not-reviewed')
        market = adult if adult == 'allowed' else ('medical-only' if medical in ('allowed', 'medical-only') else adult)
        gaps = []
        has_list = code in wtb
        if WEIGHT.get(market, 0) >= 2 and not has_list:
            gaps.append(('no official store or club list', 3))
        missing = total_q - len(a)
        if missing:
            gaps.append((f'{missing} law questions unanswered', 1 + missing // 4))
        srcs = [s for s in reg['sources'] if s['jurisdiction'] == code and s.get('scope') == 'country']
        points = sum(p for _, p in gaps)
        rows.append({'code': code, 'name': c['name'], 'market': market, 'store_list': has_list,
                     'law_answers': f'{len(a)}/{total_q}', 'registry_sources': len(srcs),
                     'gaps': [g for g, _ in gaps], 'priority': WEIGHT.get(market, 0) * points})
    rows.sort(key=lambda r: (-r['priority'], r['name']))
    return rows


def queue(reg, log):
    out = []
    for s in reg['sources']:
        entry = log.get(s['id'], {})
        if s.get('status') != 'active' or (entry and not entry.get('ok')):
            out.append({'id': s['id'], 'jurisdiction': s['jurisdiction'], 'status': 'blocked' if entry.get('blocked') else s.get('status'),
                        'why': entry.get('error') or s.get('queue_note', ''), 'landing_url': s['landing_url']})
    return out


def build(ref=None):
    ref = ref or today()
    reg, log = registry(), load_json(FETCH_LOG, {})
    data = {'as_of': ref, 'method': __doc__.split('Run:')[0].strip(), 'states': us_rows(reg, log, ref),
            'countries': world_rows(reg), 'source_queue': queue(reg, log)}
    save_json(COVERAGE_JSON, data)
    lines = [f'# Coverage report, {ref}', '', 'Generated by `python -m pipeline.coverage`; do not hand-edit. '
             'Higher priority means a legal market with more missing. See `pipeline/README.md`.', '',
             '## States, thinnest first', '', '| Priority | State | Market | Stores listed | List from | Law answers | Gaps |', '|---|---|---|---|---|---|---|']
    for r in data['states']:
        lines.append(f'| {r["priority"]} | {r["name"]} | {r["market"]} | {r["stores"]} | {r["store_list_from"] or "none"} | {r["law_answers"]} | {"; ".join(r["gaps"]) or "none"} |')
    lines += ['', '## Countries, thinnest first (top 30)', '', '| Priority | Country | Market | Official list | Law answers | Gaps |', '|---|---|---|---|---|---|']
    for r in data['countries'][:30]:
        lines.append(f'| {r["priority"]} | {r["name"]} | {r["market"]} | {"yes" if r["store_list"] else "no"} | {r["law_answers"]} | {"; ".join(r["gaps"]) or "none"} |')
    lines += ['', '## Source queue (not yet pulled automatically)', '', '| Source | Where | Status | Why |', '|---|---|---|---|']
    for q in data['source_queue']:
        lines.append(f'| {q["id"]} | {q["jurisdiction"]} | {q["status"]} | {q["why"].replace("|", "/")} |')
    COVERAGE_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return data


if __name__ == '__main__':
    d = build()
    print(f'{len(d["states"])} states and {len(d["countries"])} countries ranked; {len(d["source_queue"])} sources queued.')
    for r in d['states'][:10]:
        print(f'  {r["priority"]:>3}  {r["name"]}: {"; ".join(r["gaps"])}')
