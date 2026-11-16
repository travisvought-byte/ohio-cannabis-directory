"""Validate the consumer permissions data (data/state-permissions.json).

One shared question set, answered once per jurisdiction for all 50 states and DC.
Every answer names its sources and review date. A missing answer means
"not yet reviewed" and is never stored as a prohibition. Run:
python validate_permissions.py
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATH = ROOT / 'data/state-permissions.json'

STATUSES = {'allowed', 'medical-only', 'limited', 'not-permitted', 'varies-locally', 'not-reviewed'}
SOURCE_KINDS = {'statute', 'regulator', 'government', 'organization', 'compilation', 'news'}
OFFICIAL_KINDS = {'statute', 'regulator', 'government'}
SCOPES = {'state', 'national'}
AUDIENCES = {'consumer', 'business'}
JURISDICTION_COUNT = 51  # 50 states and the District of Columbia


def _date(value, where):
    assert isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), f'{where}: expected YYYY-MM-DD, got {value!r}'
    return date.fromisoformat(value)


def _text(value, where):
    assert isinstance(value, str) and value.strip(), f'{where}: text is required'


def evidence_level(answer, sources):
    """'official' when every source is a state or federal primary source, 'compilation' when none is."""
    kinds = {sources[sid]['kind'] in OFFICIAL_KINDS for sid in answer['source_ids']}
    if kinds == {True}:
        return 'official'
    if kinds == {False}:
        return 'compilation'
    return 'mixed'


def validate(data):
    as_of = _date(data['as_of'], 'as_of')
    assert set(data['statuses']) == STATUSES, 'statuses must be exactly ' + ', '.join(sorted(STATUSES))
    jurisdictions = data['jurisdictions']
    assert len(jurisdictions) == JURISDICTION_COUNT, f'expected {JURISDICTION_COUNT} jurisdictions, found {len(jurisdictions)}'
    assert all(re.fullmatch(r'[A-Z]{2}', code) for code in jurisdictions), 'jurisdiction codes are two capital letters'

    sources = {}
    for s in data['sources']:
        sid = s['id']
        assert sid not in sources, f'duplicate source id {sid}'
        assert s['kind'] in SOURCE_KINDS, f'{sid}: unknown source kind {s["kind"]!r}'
        assert s['scope'] in SCOPES, f'{sid}: scope must be state or national'
        assert s['url'].startswith('https://'), f'{sid}: source URL must be https'
        _text(s['title'], sid); _text(s['publisher'], sid)
        assert _date(s['retrieved_on'], sid) <= as_of, f'{sid}: retrieved after as_of'
        sources[sid] = s
    used = set()

    def cite(ids, where, kinds=None):
        assert ids, f'{where}: at least one source is required'
        for sid in ids:
            assert sid in sources, f'{where}: unknown source {sid!r}'
            if kinds:
                assert sources[sid]['kind'] in kinds, f'{where}: source {sid} must be one of {sorted(kinds)}'
        used.update(ids)

    groups = {g['id'] for g in data['groups']}
    questions = {}
    for q in data['questions']:
        assert q['id'] not in questions, f'duplicate question {q["id"]}'
        assert q['group'] in groups, f'{q["id"]}: unknown group {q["group"]!r}'
        _text(q['question'], q['id'])
        questions[q['id']] = q
    required = data['required_questions']
    assert required and set(required) <= set(questions), 'required_questions must name known questions'

    seen = set()
    for n, a in enumerate(data['answers']):
        where = f'answer {n} {a.get("state")}/{a.get("question")}'
        assert a['state'] in jurisdictions, f'{where}: unknown jurisdiction'
        assert a['question'] in questions, f'{where}: unknown question'
        key = (a['state'], a['question'])
        assert key not in seen, f'{where}: duplicate answer'
        seen.add(key)
        assert a['status'] in STATUSES and a['status'] != 'not-reviewed', \
            f'{where}: store only reviewed answers; omit the answer to show "Not yet reviewed"'
        _text(a['short'], where); _text(a['detail'], where); _text(a['citation'], where)
        assert len(a['short']) <= 60, f'{where}: short answer must fit a phone row (60 characters)'
        assert _date(a['reviewed_on'], where) <= as_of, f'{where}: reviewed after as_of'
        if a.get('effective_on') is not None:
            _date(a['effective_on'], where)
        cite(a['source_ids'], where)
        if a['question'] == 'medical' and a['status'] == 'not-permitted':
            assert any(sources[sid]['kind'] in OFFICIAL_KINDS for sid in a['source_ids']), \
                f'{where}: "not permitted" for medical use needs a state source showing there is no program'
        for sid in a['source_ids']:
            assert _date(sources[sid]['retrieved_on'], sid) <= _date(a['reviewed_on'], where), \
                f'{where}: reviewed before its source {sid} was retrieved'

    for code in jurisdictions:
        for q in required:
            assert (code, q) in seen, f'{code}: the top-level question {q!r} needs a reviewed answer'

    for code, link in data['official_links'].items():
        assert code in jurisdictions, f'official link for unknown jurisdiction {code}'
        cite([link['source_id']], f'official link {code}', OFFICIAL_KINDS)
        assert sources[link['source_id']]['scope'] == 'state', f'official link {code} must be a state source'

    national_ids = set()
    for item in data['national']:
        where = f'national {item["id"]}'
        assert item['id'] not in national_ids, f'duplicate national item {item["id"]}'
        national_ids.add(item['id'])
        for key in ('need', 'title', 'text'):
            _text(item[key], where)
        assert item['url'].startswith('https://'), f'{where}: URL must be https'
        assert _date(item['reviewed_on'], where) <= as_of, f'{where}: reviewed after as_of'
        cite(item['source_ids'], where, OFFICIAL_KINDS | {'organization'})
        assert item.get('audience', 'consumer') in AUDIENCES, f'{where}: audience must be consumer or business'
        assert item['url'] in {sources[s]['url'] for s in item['source_ids']}, f'{where}: link to the reviewed source'

    unused = set(sources) - used
    assert not unused, f'sources listed but never cited: {sorted(unused)}'
    return data


def main():
    data = validate(json.loads(PATH.read_text(encoding='utf-8')))
    print(f'state-permissions.json OK: {len(data["jurisdictions"])} jurisdictions, '
          f'{len(data["questions"])} questions, {len(data["answers"])} reviewed answers, {len(data["sources"])} sources')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        sys.exit(f'Invalid state-permissions.json: {e}')
