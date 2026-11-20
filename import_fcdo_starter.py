"""Starter pages for every country we have not reviewed in full yet.

Source: UK Foreign, Commonwealth & Development Office (FCDO) travel advice, read through the
GOV.UK Content API (https://www.gov.uk/api/content/foreign-travel-advice/<country>). It is
Crown copyright published under the Open Government Licence v3.0, which allows reuse with
attribution, so the drugs passages are kept in the FCDO's own words and credited on each page.

Two steps:

1. python import_fcdo_starter.py --raw DIR
   DIR holds one <slug>.json per country from the Content API. Writes the snapshot
   data/sources/fcdo-travel-advice-drugs-<date>.json: for each country, the advice's title,
   URL, the FCDO's own last-updated date and every section whose heading is about drugs
   (or, where there is none, the paragraphs that mention drugs or cannabis).
2. python import_fcdo_starter.py
   Writes data/world-starter.json for every roster country that has FCDO drugs text and no
   full guide yet, and marks those countries "basic" (starter page) in data/world-roster.json.
   A country keeps its place in the review queue; a full guide replaces the starter page.

A starter page adds no claim of our own: the core questions read "Not yet reviewed".
"""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOT_DATE = '2026-11-20'
SNAPSHOT = ROOT / f'data/sources/fcdo-travel-advice-drugs-{SNAPSHOT_DATE}.json'
OUT = ROOT / 'data/world-starter.json'
ROSTER = ROOT / 'data/world-roster.json'
WORLD = ROOT / 'data/world-permissions.json'

# FCDO slug -> ISO codes in our roster, where the names differ. One FCDO page can cover several places.
ALIASES = {
    'democratic-republic-of-the-congo': ['CD'], 'bonaire-st-eustatius-saba': ['BQ'], 'st-lucia': ['LC'],
    'cook-islands-tokelau-and-niue': ['CK', 'TK', 'NU'], 'st-vincent-and-the-grenadines': ['VC'], 'british-virgin-islands': ['VG'],
    'cape-verde': ['CV'], 'st-maarten': ['SX'], 'federated-states-of-micronesia': ['FM'], 'pitcairn-island': ['PN'],
    'st-kitts-and-nevis': ['KN'], 'turkey': ['TR'], 'antarctica-british-antarctic-territory': ['AQ'], 'falkland-islands': ['FK'],
    'st-pierre-and-miquelon': ['PM'], 'russia': ['RU'], 'the-gambia': ['GM'], 'south-georgia-and-south-sandwich-islands': ['GS'],
    'brunei': ['BN'], 'palestine': ['PS'], 'st-martin-and-st-barthelemy': ['MF', 'BL'], 'st-helena-ascension-and-tristan-da-cunha': ['SH'],
}
SKIP = {'usa'}  # the United States is covered state by state

LICENCE = ('Contains public sector information licensed under the Open Government Licence v3.0. '
           'Quoted from the UK government\'s travel advice for British travellers; the wording is theirs.')


def _clean(fragment):
    t = html.unescape(re.sub(r'<[^>]+>', ' ', fragment))
    return re.sub(r'\s+', ' ', t).strip()


def _blocks(body):
    """Paragraphs and list items, in order, as plain text."""
    return [_clean(m) for m in re.findall(r'<(?:p|li)[^>]*>(.*?)</(?:p|li)>', body, flags=re.S) if _clean(m)]


def parse_raw(d):
    out = {'snapshot_date': SNAPSHOT_DATE, 'api': 'https://www.gov.uk/api/content/foreign-travel-advice/<slug>', 'countries': {}}
    for f in sorted(d.glob('*.json')):
        data = json.loads(f.read_text(encoding='utf-8'))
        slug = f.stem
        sections = []
        for part in data['details'].get('parts', []):
            pieces = re.split(r'(<h[2-4][^>]*>.*?</h[2-4]>)', part['body'], flags=re.S)
            heading = None
            for piece in pieces:
                m = re.match(r'<h([2-4])[^>]*>(.*?)</h\1>', piece, flags=re.S)
                if m:
                    heading = _clean(m.group(2))
                    continue
                if heading and re.search(r'drug|cannabis|narcotic', heading, flags=re.I):
                    paras = _blocks(piece)
                    if paras:
                        sections.append({'part': part['slug'], 'heading': heading, 'paragraphs': paras})
        if not sections:  # no drugs heading: keep only paragraphs that are about drugs
            for part in data['details'].get('parts', []):
                paras = [p for p in _blocks(part['body']) if re.search(r'\b(drugs?|cannabis|marijuana|narcotics?)\b', p, flags=re.I)]
                if paras:
                    sections.append({'part': part['slug'], 'heading': '', 'paragraphs': paras})
        out['countries'][slug] = {'title': data['title'].replace(' travel advice', ''), 'url': 'https://www.gov.uk' + data['base_path'],
                                  'updated': (data.get('public_updated_at') or '')[:10], 'sections': sections}
    SNAPSHOT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('snapshot:', len(out['countries']), 'countries,', sum(1 for c in out['countries'].values() if c['sections']), 'with drugs text')


def _norm(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z]+', '-', s).strip('-')


def _page(title):
    return 'world-' + _norm(re.sub(r'\s*\(.*?\)', '', title)) + '.html'


def build():
    snap = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    roster = json.loads(ROSTER.read_text(encoding='utf-8'))
    deep = set(json.loads(WORLD.read_text(encoding='utf-8'))['countries'])
    by_name = {}
    for r in roster['countries']:
        by_name.setdefault(_norm(r['name']), r['iso'])
        by_name.setdefault(_norm(r['display']), r['iso'])
    starter, sources = {}, []
    for slug, c in sorted(snap['countries'].items()):
        if slug in SKIP or not c['sections']:
            continue
        codes = ALIASES.get(slug) or ([by_name[slug]] if slug in by_name else [by_name[_norm(c['title'])]] if _norm(c['title']) in by_name else [])
        sid = f'fcdo-{slug}'
        used = False
        for code in codes:
            if code in deep:
                continue
            name = next(r['display'] for r in roster['countries'] if r['iso'] == code) if len(codes) > 1 else re.sub(r'\s*\(.*?\)', '', c['title'])
            starter[code] = {'name': name, 'page': _page(name), 'fcdo_title': c['title'], 'source_id': sid, 'updated': c['updated'], 'sections': c['sections']}
            used = True
        if used:
            sources.append({'id': sid, 'kind': 'government', 'publisher': 'UK Foreign, Commonwealth & Development Office (GOV.UK)',
                            'title': f'{c["title"]} travel advice (last updated by the FCDO {c["updated"]})', 'url': c['url'], 'retrieved_on': SNAPSHOT_DATE})
    pages = [s['page'] for s in starter.values()]
    assert len(pages) == len(set(pages)), 'two starter pages would share a file name'
    for r in roster['countries']:
        if r['iso'] in starter:
            r['status'], r['page'] = 'basic', starter[r['iso']]['page']
        elif r['status'] == 'basic':
            r['status'], r['page'] = ('queued' if r.get('queue') else 'not-started'), None
    ROSTER.write_text(json.dumps(roster, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    OUT.write_text(json.dumps({'schema_version': 1, 'as_of': SNAPSHOT_DATE, 'licence': LICENCE,
                               'purpose': 'Starter pages: what the UK government tells travellers about drugs, for countries without a full guide yet. Generated by import_fcdo_starter.py; do not hand-edit.',
                               'countries': starter, 'sources': sources}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('starter pages:', len(starter))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', type=Path, help='folder of GOV.UK Content API files, one per country; refreshes the snapshot first')
    a = ap.parse_args()
    if a.raw:
        parse_raw(a.raw)
    build()
