"""Validate the state comparison data (data/state-comparison.json).

Every fact must name its sources; every law entry needs a citation, a review
date and at least one primary source (statute, regulator or government);
every assessment needs a likelihood from the scale, a confidence level, a
stated basis and a review date. Run: python validate_comparison.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATH = ROOT / 'data/state-comparison.json'
SOURCE_KINDS = {'statute', 'regulator', 'government', 'news', 'research'}
PRIMARY_KINDS = {'statute', 'regulator', 'government'}
CHECK_STATUSES = {'present', 'partial', 'absent', 'unknown'}
MAX_REVIEW_DAYS = 120


def _date(value, where):
    assert isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), f'{where}: expected YYYY-MM-DD, got {value!r}'
    return date.fromisoformat(value)


def _text(value, where):
    assert isinstance(value, str) and value.strip(), f'{where}: text is required'


def validate(data):
    as_of = _date(data['as_of'], 'as_of')
    states = data['states']
    assert data['home_state'] in states, 'home_state must be a listed state'
    scale, levels = data['likelihood_scale'], data['confidence_levels']
    sources = {}
    for s in data['sources']:
        assert s['id'] not in sources, f"duplicate source id {s['id']}"
        assert s['kind'] in SOURCE_KINDS, f"{s['id']}: unknown source kind {s['kind']!r}"
        assert s['url'].startswith('https://'), f"{s['id']}: source URL must be https"
        _text(s['title'], s['id']); _text(s['publisher'], s['id'])
        assert _date(s['retrieved_on'], s['id']) <= as_of, f"{s['id']}: retrieved after as_of"
        sources[s['id']] = s
    used = set()

    def cite(item, where, primary=False):
        ids = item.get('source_ids') or []
        assert ids, f'{where}: at least one source is required'
        for sid in ids:
            assert sid in sources, f'{where}: unknown source {sid!r}'
        used.update(ids)
        if primary:
            assert any(sources[sid]['kind'] in PRIMARY_KINDS for sid in ids), f'{where}: law entries need a statute, regulator or government source'

    topic_ids = set()
    for topic in data['topics']:
        assert topic['id'] not in topic_ids, f"duplicate topic {topic['id']}"
        topic_ids.add(topic['id'])
        _text(topic['label'], topic['id']); _text(topic['question'], topic['id'])
        seen = set()
        for e in topic['entries']:
            where = f"{topic['id']}/{e['state']}"
            assert e['state'] in states, f'{where}: unknown state'
            assert e['state'] not in seen, f'{where}: duplicate state entry'
            seen.add(e['state'])
            _text(e['summary'], where); _text(e['citation'], where)
            assert _date(e['reviewed_on'], where) <= as_of, f'{where}: reviewed after as_of'
            if e.get('effective_on') is not None:
                _date(e['effective_on'], where)
            cite(e, where, primary=True)

    for lesson in data['lessons']:
        lid = lesson['id']
        _text(lesson['title'], lid); _text(lesson['summary'], lid)
        assert lesson['example_state'] in states, f'{lid}: unknown example state'
        for key in ('what_happened', 'ohio_trend'):
            assert lesson[key], f'{lid}: {key} needs at least one item'
            for n, item in enumerate(lesson[key]):
                _text(item['text'], f'{lid}/{key}/{n}'); cite(item, f'{lid}/{key}/{n}')
        conditions = {}
        for c in lesson['conditions']:
            _text(c['label'], f"{lid}/{c['id']}"); _text(c['text'], f"{lid}/{c['id']}"); cite(c, f"{lid}/condition/{c['id']}")
            conditions[c['id']] = c
        checked = set()
        for chk in lesson['ohio_check']:
            where = f"{lid}/ohio_check/{chk['condition_id']}"
            assert chk['condition_id'] in conditions, f'{where}: unknown condition'
            assert chk['status'] in CHECK_STATUSES, f"{where}: status must be one of {sorted(CHECK_STATUSES)}"
            _text(chk['finding'], where); cite(chk, where)
            checked.add(chk['condition_id'])
        assert checked == set(conditions), f'{lid}: every condition needs an Ohio check'
        assessed_on = _date(lesson['assessed_on'], f'{lid}/assessed_on')
        review_by = _date(lesson['review_by'], f'{lid}/review_by')
        assert assessed_on <= as_of, f'{lid}: assessed after as_of'
        assert 0 < (review_by - assessed_on).days <= MAX_REVIEW_DAYS, f'{lid}: review_by must fall within {MAX_REVIEW_DAYS} days of the assessment'
        assert lesson['assessments'], f'{lid}: at least one assessment is required'
        for n, a in enumerate(lesson['assessments']):
            where = f'{lid}/assessment/{n}'
            _text(a['judgment'], where); _text(a['basis'], where)
            assert a['likelihood'] in scale, f"{where}: likelihood must be one of {scale}"
            assert a['confidence'] in levels, f"{where}: confidence must be one of {levels}"
        for w in lesson['watch']:
            _text(w, f'{lid}/watch')
        for r in lesson['responses']:
            assert r['state'] in states, f"{lid}/response: unknown state {r['state']}"
            _text(r['text'], f"{lid}/response/{r['state']}"); cite(r, f"{lid}/response/{r['state']}")
        letter = lesson['letter']
        for key in ('subject', 'opening', 'closing'):
            _text(letter[key], f'{lid}/letter/{key}')
        ask_ids = [a['id'] for a in letter['asks']]
        assert ask_ids and len(ask_ids) == len(set(ask_ids)), f'{lid}: letter asks need unique ids'
        for a in letter['asks']:
            _text(a['label'], f"{lid}/ask/{a['id']}"); _text(a['text'], f"{lid}/ask/{a['id']}")

    market_path = ROOT / 'data/state-market-observations.json'
    if market_path.exists():
        from market_observations import validate_market
        market = json.loads(market_path.read_text(encoding='utf-8'))
        validate_market(data, market['observations'])
        for row in market['observations']:
            used.update(row['source_ids'])
    unused = set(sources) - used
    assert not unused, f'sources listed but never cited: {sorted(unused)}'
    return {'topics': len(data['topics']), 'lessons': len(data['lessons']), 'sources': len(sources)}


def main():
    data = json.loads(PATH.read_text(encoding='utf-8'))
    try:
        counts = validate(data)
    except AssertionError as error:
        print(f'FAIL: {error}')
        sys.exit(1)
    from market_observations import validate_market
    market_path = ROOT / 'data/state-market-observations.json'
    market = json.loads(market_path.read_text(encoding='utf-8'))
    n = validate_market(data, market['observations'])
    print(f'PASS: market observations - {n} verified records')
    print(f"PASS: state comparison - {counts['topics']} law topics, {counts['lessons']} market lessons, {counts['sources']} sources, every claim cited")


if __name__ == '__main__':
    main()
