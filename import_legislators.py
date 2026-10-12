"""Refresh the Ohio roster from official directories, profiles and roll calls.

Run manually after reviewing the resulting diff. Downloads cache in /tmp;
the published JSON keeps field-level sources and historical voter identities.
"""
import concurrent.futures
import hashlib
import json
import re
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
CACHE = Path('/tmp/ohio-legislator-source-cache') / date.today().isoformat()
CACHE.mkdir(exist_ok=True)
CHECKED = date.today().isoformat()
BASES = {'House': 'https://ohiohouse.gov', 'Senate': 'https://ohiosenate.gov'}
VOTE_URL = BASES['House'] + '/legislation/136/sb56/votes'
STATUS_URL = BASES['House'] + '/legislation/136/sb56/status'

def clean(text):
    return re.sub(r'\s+', ' ', text.replace("\\'", "'")).strip()

def norm(text):
    return re.sub(r'[^a-z0-9]', '', clean(text).lower())

def fetch(url):
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + '.html')
    if path.exists():
        return BeautifulSoup(path.read_text(), 'html.parser')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read().decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            if soup.title and soup.title.get_text().strip() == 'Error':
                raise ValueError('Official site returned its error page')
            path.write_text(content)
            return soup
        except Exception:
            if attempt == 2:
                raise

def roster(chamber):
    url = BASES[chamber] + '/members/directory'
    soup = fetch(url)
    rows = []
    for a in soup.select('a'):
        name = a.select_one('.media-overlay-caption-text-line-1')
        district = a.select_one('.media-overlay-caption-text-line-2')
        if not name or not district:
            continue
        match = re.search(r'District\s+(\d+)', district.get_text(' ', strip=True))
        if not match:
            continue
        number = int(match[1])
        party = re.search(r'\b([RD])\s*$', district.get_text(' ', strip=True))
        name = clean(name.get_text(' ', strip=True))
        vacant = name == 'Vacant'
        rows.append({'id': f'{chamber.lower()}-{number:02}', 'name': name,
                     'chamber': chamber, 'district': number,
                     'party': None if vacant else {'R': 'Republican', 'D': 'Democratic'}[party[1]],
                     'vacant': vacant, 'profile_url': urljoin(url, a['href']),
                     'directory_source': url, 'checked_on': CHECKED,
                     'phone': None, 'contact_url': None, 'roles': [], 'votes': []})
    assert len(rows) == (99 if chamber == 'House' else 33), (chamber, len(rows))
    assert {r['district'] for r in rows} == set(range(1, len(rows) + 1))
    return rows

def contact(row):
    if row['vacant']:
        return row
    soup = fetch(row['profile_url'])
    text = clean(soup.get_text(' ', strip=True))
    match = re.search(r'Phone\s*:?\s*(\(\d{3}\)\s*\d{3}[- ]\d{4})', text)
    row['phone'] = match[1] if match else None
    row['phone_source'] = row['profile_url']
    links = [a for a in soup.select('a[href]') if clean(a.get_text(' ', strip=True)) == 'Contact']
    if not links:
        raise ValueError('Missing official contact link: ' + row['name'])
    row['contact_url'] = urljoin(row['profile_url'], links[0]['href'])
    row['contact_source'] = row['profile_url']
    if not row['phone']:
        contact_text = clean(fetch(row['contact_url']).get_text(' ', strip=True))
        match = re.search(r'Phone\s*:?\s*(\(\d{3}\)\s*\d{3}[- ]\d{4})', contact_text)
        if match:
            row['phone'] = match[1]
            row['phone_source'] = row['contact_url']
        else:
            row['phone_source'] = None
            row['contact_note'] = 'Office phone not published on the reviewed official profile or contact page.'
    row['contact_evidence'] = 'Phone: ' + (row['phone'] or 'not published') + '; Contact: ' + row['contact_url']
    return row

def add_roles(rows):
    by_name = {(r['chamber'], norm(r['name'])): r for r in rows if not r['vacant']}
    jobs = []
    for chamber in BASES:
        for side in ['majority', 'minority']:
            jobs.append((chamber, 'Leadership', BASES[chamber] + f'/members/{side}-leadership'))
        for committee in ['judiciary', 'finance', 'general-government', 'rules-and-reference']:
            jobs.append((chamber, committee.replace('-', ' ').title(), BASES[chamber] + '/committees/' + committee))
    def read(job):
        chamber, group, url = job
        return chamber, group, url, fetch(url)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for chamber, group, url, soup in pool.map(read, jobs):
            for a in soup.select('a'):
                name = a.select_one('.media-overlay-caption-text-line-1')
                if not name:
                    continue
                row = by_name.get((chamber, norm(name.get_text(' ', strip=True))))
                if not row:
                    continue
                position = a.select_one('.position-name, .committee-member-position, .leadership-role')
                title = clean(position.get_text(' ', strip=True)) if position else 'Member'
                label = title if group == 'Leadership' else group + ' — ' + title
                if label not in [r['label'] for r in row['roles']]:
                    row['roles'].append({'label': label, 'source': url, 'checked_on': CHECKED})

def rollcalls(rows):
    soup = fetch(VOTE_URL)
    status_text = clean(fetch(STATUS_URL).get_text(' ', strip=True))
    assert 'Conference report agreed to' in status_text
    by_name = {(r['chamber'], norm(r['name'])): r for r in rows if not r['vacant']}
    for header in soup.find_all(['h2', 'h3']):
        label = clean(header.get_text())
        if label not in ['Primary Sponsors', 'Cosponsors']:
            continue
        for a in header.parent.select('a'):
            name = clean(a.get_text())
            matches = [row for (chamber, key), row in by_name.items() if key == norm(name)]
            if len(matches) == 1:
                role = 'SB 56 — ' + ('Primary sponsor' if label == 'Primary Sponsors' else 'Cosponsor')
                matches[0]['roles'].append({'label': role, 'source': VOTE_URL, 'checked_on': CHECKED})
    events = []
    for cell in soup.select('.date-cell'):
        tr = cell.parent
        chamber = clean(tr.select_one('.chamber-cell').get_text())
        raw_date = clean(cell.get_text())
        month, day, year = map(int, raw_date.split('/'))
        when = date(year, month, day).isoformat()
        result = clean(tr.select_one('.result-cell').get_text())
        breakdown = tr.select_one('.vote-breakdown')
        counts = {re.search(r'(Yeas|Nays):', s.get_text())[1]: int(re.search(r':\s*(\d+)', s.get_text())[1])
                  for s in tr.select('.vote-count-column')}
        final = (chamber, when) in [('House', '2025-11-19'), ('Senate', '2025-12-09')]
        stage = 'Conference report — final chamber agreement' if final else (
            'Floor passage — earlier version' if result == 'Passed' else
            'Concurrence on House amendments — failed' if when == '2025-10-29' else
            'Committee action — ' + result.lower())
        event = {'id': f'sb56-{chamber.lower()}-{when}-{len(events)+1}', 'bill': 'SB 56',
                 'general_assembly': 136, 'chamber': chamber, 'date': when, 'stage': stage,
                 'official_action': result, 'is_final_agreement': final,
                 'yeas': counts['Yeas'], 'nays': counts['Nays'], 'voters': [],
                 'source': VOTE_URL, 'status_source': STATUS_URL, 'checked_on': CHECKED}
        for heading in breakdown.select('h4'):
            choice = {'Yeas': 'Yea', 'Nays': 'Nay'}[clean(heading.get_text())]
            table = heading.find_next_sibling('table')
            for td in table.select('td'):
                name = clean(td.get_text(' ', strip=True))
                if not name:
                    continue
                row = by_name.get((chamber, norm(name)))
                event['voters'].append({'name_as_recorded': name, 'vote': choice,
                                        'current_member_id': row['id'] if row else None})
                if row:
                    row['votes'].append({'event_id': event['id'], 'vote': choice})
        assert sum(v['vote'] == 'Yea' for v in event['voters']) == event['yeas'], event['id']
        assert sum(v['vote'] == 'Nay' for v in event['voters']) == event['nays'], event['id']
        events.append(event)
    assert len([e for e in events if e['is_final_agreement']]) == 2
    return events

def main():
    rows = roster('House') + roster('Senate')
    print('Reading contacts for', sum(not r['vacant'] for r in rows), 'current lawmakers', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(contact, rows))
    add_roles(rows)
    events = rollcalls(rows)
    data = {'schema_version': 1, 'checked_on': CHECKED, 'general_assembly': 136,
            'scope': 'Ohio state House and Senate; current roster with historical SB 56 roll calls',
            'role_scope': 'Chamber leadership, SB 56 sponsorship, plus Judiciary, Finance, General Government, and Rules and Reference membership; not every committee.',
            'members': rows, 'vote_events': events}
    (ROOT / 'data/legislators.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('Saved', len(rows), 'districts;', len(events), 'verified roll calls;',
          sum(bool(r['phone']) for r in rows), 'office phones', flush=True)

if __name__ == '__main__':
    main()
