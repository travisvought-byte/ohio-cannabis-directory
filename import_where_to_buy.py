"""Where to buy legally, country by country: build data/world-where-to-buy.json.

Two steps:

1. python import_where_to_buy.py --raw DIR
   Parses the official files downloaded on SNAPSHOT_DATE (listed in RAW below) into one
   normalized snapshot, data/sources/where-to-buy-<date>.json. Only business details are kept:
   names, addresses, towns, licence numbers, business phone, email and website. Personal names
   (managers, representatives, board members) are never copied.
2. python import_where_to_buy.py
   Reads that snapshot and writes data/world-where-to-buy.json, which build_world.py renders on
   each country page (and, for Canada, on its own store page). Nothing in the output is added
   by hand except the plain-English framing below, and every block names its source.

Countries whose official list could not be downloaded keep a link and say so; a failed
retrieval is not a review.
"""
import argparse
import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAPSHOT_DATE = '2026-11-20'
SNAPSHOT = ROOT / f'data/sources/where-to-buy-{SNAPSHOT_DATE}.json'
OUT = ROOT / 'data/world-where-to-buy.json'

RAW = {  # file in --raw DIR: where it came from
    'on.csv': 'https://www.agco.ca/sites/default/files/opendata/AGCOWebSiteCRSANewProcessMapData.csv',
    'bc.xlsx': 'https://www2.gov.bc.ca/assets/gov/employment-business-and-economic-development/business-management/liquor-regulation-licensing/reports/cannabis_retail_stores_in_bc.xlsx',
    'ab.bin': 'https://aglc.ca/cannabis/cannabis-licensee-report/EXCEL',
    'sk.xlsx': 'https://www.slga.com/-/media/slga/files/permits-and-licences/cannabis/retailer-supplier-lists/slga-cannabis-retailers-excel--nov-13.xlsx',
    'mb.html': 'https://lgcamb.ca/cannabis/store-list',
    'chra.html': 'https://aruc.mt/operational-chras/',
    'ni.html': 'https://www.lwk-niedersachsen.de/cannabis/kcanglist',
    'hh.pdf': 'https://www.hamburg.de/resource/blob/1157502/2d48e644828ee04ee2db5f6f2d21b6ba/anbauvereinigungen-whitelist-data.pdf',
    'ch-*.html': 'https://www.bag.admin.ch/de/uebersicht-ueber-die-bewilligten-pilotversuche-mit-cannabis',
}

SOURCES = [
    {'id': 'wtb-agco', 'kind': 'regulator', 'publisher': 'Alcohol and Gaming Commission of Ontario (AGCO)',
     'title': 'Cannabis retail store authorizations, open data map file',
     'url': 'https://www.agco.ca/sites/default/files/opendata/AGCOWebSiteCRSANewProcessMapData.csv', 'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-bc', 'kind': 'regulator', 'publisher': 'Government of British Columbia, Liquor and Cannabis Regulation Branch',
     'title': 'Cannabis store locations and buy legal information (Excel report of cannabis stores)',
     'url': 'https://www2.gov.bc.ca/gov/content/employment-business/business/liquor-regulation-licensing/cannabis-licences/cannabis-store-locations-and-buy-legal-information',
     'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-aglc', 'kind': 'regulator', 'publisher': 'Alberta Gaming, Liquor and Cannabis (AGLC)',
     'title': 'Cannabis licensee search, licensee list (Excel export)',
     'url': 'https://aglc.ca/cannabis/retail-cannabis/cannabis-licensee-search', 'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-slga', 'kind': 'regulator', 'publisher': 'Saskatchewan Liquor and Gaming Authority (SLGA)',
     'title': 'Saskatchewan cannabis retailers (Excel list, November 13)',
     'url': 'https://www.slga.com/cannabis/cannabis-permits/authorized-saskatchewan-cannabis-sellers-and-distributors', 'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-lgca', 'kind': 'regulator', 'publisher': 'Liquor, Gaming and Cannabis Authority of Manitoba (LGCA)',
     'title': 'Legal cannabis stores in Manitoba', 'url': 'https://lgcamb.ca/cannabis/store-list', 'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-aruc', 'kind': 'regulator', 'publisher': 'Authority for the Responsible Use of Cannabis (ARUC), Malta',
     'title': 'Registry for Cannabis Harm Reduction Associations with an operating permit',
     'url': 'https://aruc.mt/operational-chras/', 'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-bag', 'kind': 'government', 'publisher': 'Federal Office of Public Health (BAG), Switzerland',
     'title': 'Übersicht über die bewilligten Pilotversuche mit Cannabis (overview of approved cannabis pilot trials)',
     'url': 'https://www.bag.admin.ch/de/uebersicht-ueber-die-bewilligten-pilotversuche-mit-cannabis', 'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-lwk-ni', 'kind': 'regulator', 'publisher': 'Landwirtschaftskammer Niedersachsen (licensing authority, Lower Saxony)',
     'title': 'Genehmigte Anbauvereinigungen (approved cultivation associations)',
     'url': 'https://www.lwk-niedersachsen.de/cannabis/kcanglist', 'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-hamburg', 'kind': 'regulator', 'publisher': 'Bezirksamt Hamburg-Altona (licensing authority, Hamburg)',
     'title': 'Anbauvereinigungen mit Erlaubnis nach § 11 KCanG, Stand Juli 2026',
     'url': 'https://www.hamburg.de/resource/blob/1157502/2d48e644828ee04ee2db5f6f2d21b6ba/anbauvereinigungen-whitelist-data.pdf',
     'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-uy-news', 'kind': 'news', 'publisher': 'Montevideo Portal',
     'title': 'Ircca evalúa extender la venta de marihuana legal a turistas (Dec 6, 2025)',
     'url': 'https://www.montevideo.com.uy/Noticias/Ircca-evalua-extender-la-venta-de-marihuana-legal-a-turistas--El-centro-de-la-discusion--uc945642',
     'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-uy-list-news', 'kind': 'news', 'publisher': 'Montevideo Portal',
     'title': 'IRCCA dice que farmacias tienen "todas las variedades" (May 29, 2025)',
     'url': 'https://www.montevideo.com.uy/Noticias/IRCCA-dice-que-farmacias-tienen-todas-las-variedades--cual-es-el-precio-de-cada-una--uc925347',
     'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-th-thairath', 'kind': 'news', 'publisher': 'Thairath Online',
     'title': 'MC-GIS licence and location checks at cannabis-gis.dtam.moph.go.th (2026)',
     'url': 'https://en.thairath.co.th/scoop/theissue/2935772', 'retrieved_on': SNAPSHOT_DATE},
    {'id': 'wtb-th-nation', 'kind': 'news', 'publisher': 'The Nation (Thailand)',
     'title': 'Public Health Ministry tightens cannabis controls with GIS mapping (Apr 23, 2026)',
     'url': 'https://www.nationthailand.com/health-wellness/40065379', 'retrieved_on': SNAPSHOT_DATE},
]

DE_MONTHS = {'Januar': 'January', 'Februar': 'February', 'März': 'March', 'April': 'April', 'Mai': 'May', 'Juni': 'June', 'Juli': 'July',
             'August': 'August', 'September': 'September', 'Oktober': 'October', 'November': 'November', 'Dezember': 'December'}
DE_OUTLETS = {'Spezialisierte Fachgeschäfte': 'specialist shops', 'Spezialisiertes Fachgeschäft': 'a specialist shop', 'Apotheken': 'pharmacies',
              'Online-Bestellung mit Versand': 'online order with delivery', 'Social Clubs': 'social clubs',
              'Drogeninformationszentrum Zürich (DIZ)': 'the Zurich drug information centre (DIZ)'}
DE_CANTONS = {'Waadt': 'Vaud', 'Genf': 'Geneva', 'Basel-Land': 'Basel-Landschaft', 'Luzern': 'Lucerne'}


def _text(s):
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', s, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', '\n', s))


def parse_raw(d):
    import openpyxl
    import xlrd
    out = {'snapshot_date': SNAPSHOT_DATE, 'files': RAW}
    with (d / 'on.csv').open(encoding='utf-8-sig', errors='replace') as f:
        out['ontario'] = [{'licence': r['LicenceNumber'] or r['FileNumber'], 'name': r['PremisesName'].strip(), 'address': r['StreetAddress'].strip(),
                           'city': r['City'].strip().title(), 'postal': r['PostalCode'].strip(), 'status': r['ApplicationStatusEn'].strip(),
                           'lat': round(float(r['Latitude']), 5) if r['Latitude'] else None, 'lon': round(float(r['Longitude']), 5) if r['Longitude'] else None,
                           'website': r['WebsiteEn'].strip()} for r in csv.DictReader(f)]
    rows = list(openpyxl.load_workbook(d / 'bc.xlsx', read_only=True).worksheets[0].iter_rows(values_only=True))
    h = rows[0]
    out['british_columbia'] = [{'licence': str(r[0]), 'name': (r[2] or '').strip(), 'address': (r[3] or '').strip(), 'city': (r[4] or '').strip(),
                                'postal': (r[5] or '').strip(), 'type': r[6], 'open': r[7], 'expires': r[9].date().isoformat() if r[9] else None}
                               for r in rows[1:] if r[0] and h[0] == 'Licence Number']
    s = xlrd.open_workbook(str(d / 'ab.bin')).sheet_by_index(0)
    ab = []
    for i in range(1, s.nrows):
        r = s.row_values(i)
        phone = str(int(r[9])) if isinstance(r[9], float) else str(r[9]).strip()
        ab.append({'licence': str(int(r[0])) if isinstance(r[0], float) else str(r[0]), 'city': str(r[1]).strip().title(), 'name': str(r[2]).strip(),
                   'address': ' '.join(x for x in (str(r[5]).strip(), str(r[6]).strip()) if x).title(), 'province': str(r[7]).strip(),
                   'postal': str(r[8]).strip(), 'phone': f'{phone[:3]}-{phone[3:6]}-{phone[6:]}' if len(phone) == 10 else phone,
                   'online_sales': str(r[10]).strip()})
    out['alberta'] = ab
    rows = list(openpyxl.load_workbook(d / 'sk.xlsx', read_only=True).worksheets[0].iter_rows(values_only=True))
    out['saskatchewan'] = [{'licence': r[0], 'city': (r[1] or '').strip(), 'name': (r[2] or '').strip(), 'address': (r[3] or '').strip(),
                            'website': '' if (r[4] or '').strip() in ('', 'N/A') else r[4].strip()} for r in rows[1:] if r[0]]
    s = (d / 'mb.html').read_text(errors='ignore')
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', s, flags=re.S)
    i = s.find('Check with stores for their opening times')
    seg = s[i:s.find('MEDICAL CANNABIS', i)]
    seg = re.sub(r'</li>', '\n', re.sub(r'<li[^>]*>', '\n@@', seg))
    t = re.sub(r'[ \t\xa0]+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', seg)))
    mb, town, pending = [], None, False
    for raw in t.split('\n')[1:]:
        line = raw.strip()
        if not line:
            continue
        if line.startswith('@@'):
            line = line[2:].strip()
            if not line:
                pending = True
                continue
            pending = False
        elif pending:
            pending = False
        else:
            town = line.rstrip(':').strip()
            continue
        name, addr = (line.split(',', 1) if ',' in line else line.split(' - ', 1) if ' - ' in line else (line, ''))
        mb.append({'city': town, 'name': name.strip(), 'address': addr.strip()})
    out['manitoba'] = mb
    s = (d / 'chra.html').read_text(errors='ignore')

    def cf(h_):
        k = int(h_[:2], 16)
        return ''.join(chr(int(h_[j:j + 2], 16) ^ k) for j in range(2, len(h_), 2))
    s = re.sub(r'<a[^>]*data-cfemail="([0-9a-f]+)"[^>]*>.*?</a>', lambda m: cf(m.group(1)), s, flags=re.S)
    t = re.sub(r'\n\s*\n+', '\n', re.sub(r'[ \t]+', ' ', _text(s)))
    body = t[t.find('residence'):t.find('About\nCareer')]
    out['malta'] = [{'name': n.strip(), 'licence': c, 'email': e.strip(), 'phone': p.strip(), 'locality': loc.strip()} for n, c, e, p, loc in
                    re.findall(r'\n\s*([^\n]+?)\s*\n\s*(CHRA \d+)\s*\n\s*E:\s*\n?\s*([^\s|]+)\s*\n?\s*\|\s*\n?\s*T:\s*([^|]+?)\s*\|\s*\n?\s*L:\s*([^|]+?)\s*\|', body)]
    s = (d / 'ni.html').read_text(errors='ignore')
    ni = []
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', s, flags=re.S):
        cells = [html.unescape(re.sub(r'<[^>]+>', ' ', c)).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', r, flags=re.S)]
        if len(cells) >= 2 and cells[0]:
            ni.append({'name': re.sub(r'\s+', ' ', cells[0]), 'district': re.sub(r'\s+', ' ', cells[1])})
    out['lower_saxony'] = ni
    import subprocess
    pdf = subprocess.run(['pdftotext', '-layout', str(d / 'hh.pdf'), '-'], capture_output=True, text=True, check=True).stdout
    names = pdf.split('erteilt:', 1)[1].split('Einige weitere', 1)[0]
    out['hamburg'] = [{'name': re.sub(r'\s+', ' ', n).replace('ﬂ', 'fl').strip()} for n in names.split('\n') if n.strip()]
    trials = []
    for f in sorted(d.glob('ch-*.html')):
        s = f.read_text(errors='ignore')
        links = sorted(set(re.findall(r'href="(https?://(?!www\.bag|www\.admin|www\.google|www\.facebook|x\.com|www\.instagram|www\.youtube|www\.linkedin|www\.edi)[^"]+)"', s)))
        lines = [x.strip() for x in _text(s).split('\n') if x.strip()]
        stops = {'Gemeinde(n)', 'Geplante Laufzeit der Studie', 'Art der Verkaufsstellen', 'Studientyp', 'Stichprobengrösse', 'Geldgeber', 'Links', 'Kanton(e)', 'Weiterführende Themen', 'Stichprobe'}

        def after(label):
            if label not in lines:
                return []
            k, got = lines.index(label) + 1, []
            while k < len(lines) and lines[k] not in stops:
                got.append(lines[k])
                k += 1
            return got
        g = [k for k, x in enumerate(lines) if x == 'Gebärdensprache']
        trials.append({'slug': f.stem[3:], 'title': lines[g[1] + 1], 'cantons': after('Kanton(e)'),
                       'towns': [t_.strip() for x in after('Gemeinde(n)') for t_ in x.split(',')], 'period': ' '.join(after('Geplante Laufzeit der Studie')),
                       'outlets': after('Art der Verkaufsstellen'), 'links': links})
    out['switzerland'] = trials
    SNAPSHOT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('snapshot:', {k: len(v) for k, v in out.items() if isinstance(v, list)})


def _period(p):
    for de, en in DE_MONTHS.items():
        p = p.replace(de, en)
    return p.replace(' bis ', ' to ')


def build():
    snap = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    on = [r for r in snap['ontario'] if r['status'] == 'Authorized to Open']
    bc = [r for r in snap['british_columbia'] if r['open'] == 'Yes']
    ab = [r for r in snap['alberta'] if r['province'] == 'AB']
    trials = []
    for t in snap['switzerland']:
        site = next((u for u in t['links'] if not re.search(r'addictionsuisse|lausanne\.ch/$|isgf|bs\.ch|dkf|upk\.ch', u)), t['links'][0] if t['links'] else '')
        trials.append({'name': re.split(r'\s*–\s|\s-\s', t['title'])[0].strip(), 'canton': ', '.join(DE_CANTONS.get(c, c) for c in t['cantons']),
                       'towns': ', '.join(t['towns']), 'outlets': ', '.join(DE_OUTLETS.get(o, o) for o in t['outlets']), 'period': _period(t['period']), 'website': site})

    def table(tid, caption, columns, rows, source_ids, note=''):
        rows = sorted(rows, key=lambda r: ((r.get('city') or r.get('district') or r.get('locality') or '').lower(), r['name'].lower()))
        return {'id': tid, 'caption': caption, 'columns': columns, 'rows': rows, 'source_ids': source_ids, 'note': note}

    countries = {
        'CA': {
            'heading': 'Where to buy: legal stores by province',
            'intro': 'Every province runs its own legal stores or licenses private ones. The official lists from five provincial regulators are on a separate page, store by store, with a search box.',
            'page': 'world-canada-stores.html', 'page_title': 'Legal cannabis stores in Canada',
            'page_intro': ('These are the stores each provincial regulator lists as licensed or authorized. A store on these lists can sell legally; '
                           'a shop that is not on its province\'s list is not a legal store. Lists change often, so check the regulator\'s own list before you rely on one entry. '
                           'For provinces not listed here yet, the province table on the Canada page says how legal sales work there.'),
            'tables': [
                table('ontario', f'Ontario: {len(on):,} stores authorized to open', [['name', 'Store'], ['address', 'Address'], ['city', 'City'], ['postal', 'Postal code'], ['map', 'Where']],
                      on, ['wtb-agco'], 'Stores the AGCO lists as "Authorized to Open". Its file also lists applications in progress and cancelled stores; those are left out here.'),
                table('british-columbia', f'British Columbia: {len(bc):,} licensed stores marked open', [['name', 'Store'], ['address', 'Address'], ['city', 'City'], ['postal', 'Postal code']],
                      bc, ['wtb-bc'], 'Licensed stores the province marks as open. Government-run BC Cannabis Stores are licensed too and appear in the same list.'),
                table('alberta', f'Alberta: {len(ab):,} licensed retailers', [['name', 'Store'], ['address', 'Address'], ['city', 'City'], ['postal', 'Postal code'], ['phone', 'Phone'], ['online_sales', 'Sells online']],
                      ab, ['wtb-aglc'], 'Licensees with an Alberta address in the AGLC licensee list. Managers\' names in the list are not copied here.'),
                table('saskatchewan', f'Saskatchewan: {len(snap["saskatchewan"])} permitted retailers', [['name', 'Store'], ['address', 'Address'], ['city', 'City'], ['website', 'Website']],
                      snap['saskatchewan'], ['wtb-slga'], 'Retailers that have completed SLGA\'s permit process.'),
                table('manitoba', f'Manitoba: {len(snap["manitoba"])} licensed stores', [['name', 'Store'], ['address', 'Address'], ['city', 'Town']],
                      snap['manitoba'], ['wtb-lgca'], 'The LGCA says licensed stores can also take online and telephone orders; check with each store for opening times.'),
            ],
        },
        'MT': {
            'heading': 'Where to join: licensed associations',
            'intro': ('Malta has no shops. The regulator publishes the associations that hold an operating permit, and only these may enrol members. '
                      'An ID card or residence card issued by the Maltese Government is needed to join, and the regulator says tourists may not become members.'),
            'tables': [table('malta', f'{len(snap["malta"])} associations with an operating permit', [['name', 'Association'], ['licence', 'Licence'], ['locality', 'Where'], ['phone', 'Phone'], ['email', 'Email']],
                             snap['malta'], ['wtb-aruc'], 'Contact details are the ones the regulator publishes for each association. The names of association representatives are not copied here.')],
        },
        'CH': {
            'heading': 'Where to buy: the pilot trials',
            'intro': ('Buying is legal only inside an approved scientific trial, and only for people enrolled in it. Each trial recruits its own participants in its own towns. '
                      'The Federal Office of Public Health lists every approved trial; to take part, go to the trial\'s own site.'),
            'tables': [table('switzerland', f'{len(trials)} approved trials', [['name', 'Trial'], ['canton', 'Canton'], ['towns', 'Towns'], ['outlets', 'Sold through'], ['period', 'Planned period'], ['website', 'Trial site']],
                             trials, ['wtb-bag'], 'Planned periods are as the overview lists them; a trial can be extended, as the buying answer above notes for Bern, Biel and Lucerne.')],
        },
        'DE': {
            'heading': 'Where to join: licensed clubs',
            'intro': ('Germany has no cannabis shops. Adults get it by joining a licensed non-profit cultivation association near them. Each state licenses its own clubs, '
                      'and most do not publish a list. Lower Saxony and Hamburg do, and both lists are below.'),
            'tables': [
                table('lower-saxony', f'Lower Saxony: {len(snap["lower_saxony"])} approved associations', [['name', 'Association'], ['district', 'District']],
                      snap['lower_saxony'], ['wtb-lwk-ni']),
                table('hamburg', f'Hamburg: {len(snap["hamburg"])} associations licensed by Hamburg', [['name', 'Association']],
                      snap['hamburg'], ['wtb-hamburg'], 'Hamburg says some clubs licensed by neighbouring states also run distribution points in the city; they are not on its list.'),
            ],
        },
        'UY': {
            'heading': 'Where to buy: pharmacies',
            'intro': ('Registered residents buy at pharmacies that have joined the official network. Montevideo Portal reported in December 2025 that 24 pharmacies sell four varieties '
                      'and that visitors are not allowed to buy. The regulator, IRCCA, publishes the list of pharmacies on its website.'),
            'links': [{'label': 'IRCCA, the regulator (pharmacy list)', 'url': 'https://www.ircca.gub.uy/', 'source_ids': ['wtb-uy-list-news']}],
            'source_ids': ['wtb-uy-news', 'wtb-uy-list-news'],
            'gap': f'We could not download the pharmacy list from the IRCCA site on {SNAPSHOT_DATE}; the site refused the connection. The list will be added once it can be retrieved.',
        },
        'TH': {
            'heading': 'Where to buy: check the official licence map',
            'intro': ('Only licensed outlets may sell cannabis flower, and only against a prescription. The Department of Thai Traditional and Alternative Medicine runs a public map, MC-GIS, '
                      'that shows every licensed shop and cultivation site and when each licence expires. It is also available through the Mor Prom app.'),
            'links': [{'label': 'MC-GIS licence map (Department of Thai Traditional and Alternative Medicine)', 'url': 'https://cannabis-gis.dtam.moph.go.th/', 'source_ids': ['wtb-th-thairath']}],
            'source_ids': ['wtb-th-nation', 'wtb-th-thairath'],
            'gap': f'We could not open the map ourselves on {SNAPSHOT_DATE}; the site refused the connection. The address comes from the news reports cited.',
        },
    }
    for c in countries.values():
        c.setdefault('tables', [])
        c.setdefault('links', [])
        c.setdefault('source_ids', sorted({s for t in c['tables'] for s in t['source_ids']}))
    data = {'schema_version': 1, 'as_of': SNAPSHOT_DATE,
            'purpose': 'Legal places to buy or join, country by country, from each regulator\'s own list. Generated by import_where_to_buy.py; do not hand-edit.',
            'countries': countries, 'sources': SOURCES}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('built:', {k: [len(t['rows']) for t in v['tables']] for k, v in countries.items()})


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', type=Path, help='folder holding the downloaded official files; refreshes the snapshot first')
    a = ap.parse_args()
    if a.raw:
        parse_raw(a.raw)
    build()
