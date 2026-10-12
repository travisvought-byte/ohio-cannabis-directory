"""Check complete district coverage, source boundaries and vote attribution."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent

def validate():
    data = json.loads((ROOT / 'data/legislators.json').read_text())
    members = data['members']
    assert len(members) == 132
    by_id = {m['id']: m for m in members}
    assert len(by_id) == len(members)
    events = {e['id']: e for e in data['vote_events']}
    assert len(events) == len(data['vote_events'])
    def official(url):
        assert urlparse(url).hostname in ['ohiohouse.gov', 'ohiosenate.gov'], url
    def normalize(name):
        return re.sub('[^a-z0-9]', '', name.lower())
    for chamber, count in [('House', 99), ('Senate', 33)]:
        rows = [m for m in members if m['chamber'] == chamber]
        assert {m['district'] for m in rows} == set(range(1, count + 1))
        assert len(rows) == count
        assert sum(e['is_final_agreement'] and e['chamber'] == chamber for e in events.values()) == 1
    for m in members:
        assert m['checked_on'] == data['checked_on']
        official(m['directory_source'])
        if m['vacant']:
            assert m['name'] == 'Vacant'
            assert not any([m['phone'], m['contact_url'], m['party'], m['votes'], m['roles']])
            continue
        assert m['name'] and m['party'] in ['Republican', 'Democratic']
        official(m['profile_url']); official(m['contact_url']); official(m['contact_source'])
        if m['phone']:
            assert len(re.sub(r'\D', '', m['phone'])) == 10
            official(m['phone_source'])
        else:
            assert m['contact_note']
        for role in m['roles']:
            assert role['label'] and role['checked_on'] == data['checked_on']
            official(role['source'])
        for vote in m['votes']:
            event = events[vote['event_id']]
            assert event['chamber'] == m['chamber']
            matches = [v for v in event['voters'] if v['current_member_id'] == m['id']]
            assert len(matches) == 1 and matches[0]['vote'] == vote['vote']
            assert normalize(matches[0]['name_as_recorded']) == normalize(m['name'])
    for event in events.values():
        official(event['source']); official(event['status_source'])
        assert sum(v['vote'] == 'Yea' for v in event['voters']) == event['yeas']
        assert sum(v['vote'] == 'Nay' for v in event['voters']) == event['nays']
        assert len({normalize(v['name_as_recorded']) for v in event['voters']}) == len(event['voters'])
        for vote in event['voters']:
            if vote['current_member_id']:
                member = by_id[vote['current_member_id']]
                assert normalize(member['name']) == normalize(vote['name_as_recorded'])
                assert not member['vacant'] and member['chamber'] == event['chamber']
        if event['is_final_agreement']:
            assert (event['chamber'], event['date']) in [('House', '2025-11-19'), ('Senate', '2025-12-09')]
    print('PASS: all 132 districts, official contacts and role sources, roll-call totals, exact identity attribution and vacancy boundaries.')

if __name__ == '__main__':
    validate()
