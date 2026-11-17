"""Build the national portal: home, help by need, about, one comparison page per law
question, and one page per state and DC.

Ohio is the template. Every state page has the same two parts: the shared questions
about the law (data/state-permissions.json) and the seven directory pathways measured
by the state completion standard (data/state-scorecard.json). A state with no directory
pack yet shows its pathways as "Not started", never as absent help.

Nothing here adds a claim. Every answer, source and review date is read from the
canonical data; a missing answer reads "Not yet reviewed".

Output goes to national/ (generated; do not hand-edit). Pages use relative links, so the
folder can be served from any address. Set NATIONAL_ORIGIN (for example
https://the-reefer.com) once that domain serves these pages; until then the pages carry
no canonical address and ask search engines not to index them.

Run: python build_national.py
"""
import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse

from directory_brand import DEFAULT_SITE_ORIGIN, EMAIL, OHIO_HOME
from permissions_page import KIND_LABEL, LEVEL_TEXT, chip
from validate_permissions import evidence_level

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / 'national'
SITE_NAME = 'The Reefer'
TAGLINE = 'Cannabis information and resources for every state'
ORIGIN = os.environ.get('NATIONAL_ORIGIN', '').rstrip('/')
REPO = 'https://github.com/travisvought-byte/ohio-cannabis-directory'
LEVELS = {'starter': 'Starter', 'partial': 'Partial', 'broad': 'Broad'}
PACK_LABEL = {'live': 'Full state guide', 'pilot': 'Pilot state guide'}

CSS = '''
:root{--ink:#17231e;--soft:#56625d;--line:#d9ddd6;--link:#1d5c7a;--bg:#f7f6f1;--green:#1d4a37;--green2:#2f6d50;--gold:#e9b949;--mint:#e6f0e9}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--link);text-underline-offset:3px}.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.site{background:var(--green);color:#fff}header.site .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:0 22px;min-height:62px}
.brand{display:inline-flex;align-items:center;gap:10px;color:#fff;text-decoration:none;font-weight:800;font-size:1.22rem;min-height:48px}.brand img{width:40px;height:40px;border-radius:8px;flex:none}
header.site nav{margin-left:auto;display:flex;flex-wrap:wrap;gap:0 20px}header.site nav a{color:#fff;text-decoration:none;min-height:44px;display:inline-flex;align-items:center;font-weight:600;opacity:.9}
header.site nav a:hover,header.site nav a:focus-visible{opacity:1;text-decoration:underline}
main{max-width:1080px;margin:0 auto;padding:6px 20px 24px}
h1{font-size:clamp(26px,4vw,38px);line-height:1.15;margin:.6em 0 .3em}h2{margin:1.6em 0 .4em;font-size:1.45rem;line-height:1.25}h3{margin:1.2em 0 .4em;font-size:1.1rem}
p{max-width:70ch}.muted{color:var(--soft);font-size:.9rem}.crumbs{font-size:.9rem;margin:14px 0 0}.lede{font-size:1.08rem}
.hero{position:relative;overflow:hidden;background:linear-gradient(155deg,var(--green) 0%,var(--green2) 100%);color:#fff}
.hero .wrap{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);align-items:center;gap:24px;padding-top:34px;padding-bottom:46px}
.hero h1{font-size:clamp(32px,5.2vw,52px);line-height:1.06;margin:.25em 0 .35em;max-width:15ch}.hero p{color:#e2eee6;font-size:1.08rem;margin:.4em 0}
.hero .eyebrow{color:var(--gold);font-size:.82rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase}
.hero .art img{display:block;width:100%;max-width:460px;height:auto;margin:0 auto;border-radius:18px;box-shadow:0 16px 34px rgba(0,0,0,.35)}
.pick{background:#fff;color:var(--ink);border-radius:14px;padding:14px 16px 16px;margin-top:22px;max-width:520px;box-shadow:0 12px 30px rgba(0,0,0,.2)}
.pick label{display:block;font-weight:800;margin-bottom:6px}.pick .row{display:flex;gap:8px}.pick select{flex:1;min-width:0;font-size:1.05rem}
.pick button{font:inherit;font-weight:800;min-height:48px;padding:0 22px;border:0;border-radius:8px;background:var(--gold);color:#221c08;cursor:pointer}
.pick button:hover,.pick button:focus-visible{background:#f3cb63}.hero .pick p.muted{margin:8px 0 0;color:var(--soft);font-size:.9rem}
section.block{margin:38px 0}section.block>h2{margin-top:0}
.tasks{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:14px 0 10px}
.task{display:flex;flex-direction:column;gap:6px;background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 14px;text-decoration:none;color:var(--ink);transition:transform .12s,box-shadow .12s,border-color .12s}
.task:hover,.task:focus-visible{transform:translateY(-2px);box-shadow:0 8px 22px rgba(23,35,30,.1);border-color:var(--green2)}
.task .ic{width:46px;height:46px;border-radius:12px;background:var(--mint);color:var(--green);display:grid;place-items:center}.task .ic svg{width:26px;height:26px}
.task strong{font-size:1.02rem;line-height:1.25}.task .d{font-size:.88rem;color:var(--soft);line-height:1.35}
.also{font-size:.95rem}.also a{white-space:nowrap}
.mapbox{display:grid;grid-template-columns:minmax(0,640px) minmax(0,1fr);gap:28px;align-items:start}
.usmap{display:grid;grid-template-columns:repeat(11,minmax(0,1fr));gap:4px;margin:10px 0;max-width:640px}
.tile{aspect-ratio:1;display:grid;place-items:center;border-radius:6px;font-weight:800;font-size:clamp(10px,1.7vw,15px);text-decoration:none;color:#fff;background:#9aa3a0}
.tile:hover,.tile:focus-visible{outline:3px solid var(--ink);outline-offset:1px}
.tile.allowed,.tile.positive,.tile.broad,.sw.allowed,.sw.positive,.sw.broad{background:#2f7d4f}.tile.medical-only,.sw.medical-only{background:#3b7fa0}
.tile.limited,.tile.varies-locally,.tile.partial,.tile.starter,.sw.limited,.sw.varies-locally,.sw.partial,.sw.starter{background:#e3b23c;color:#2a2108}
.tile.not-permitted,.tile.negative,.sw.not-permitted,.sw.negative{background:#b4513a}.tile.not-reviewed,.tile.not-started,.sw.not-reviewed,.sw.not-started{background:#d4d8d5;color:#3b4541}
.legend{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:6px 18px;margin:8px 0;font-size:.93rem}.legend .sw{display:inline-block;width:15px;height:15px;border-radius:4px;vertical-align:-2px;margin-right:7px}
details.az{margin:10px 0}details.az summary{cursor:pointer;font-weight:700;color:var(--link);min-height:44px;display:flex;align-items:center}
.az ul{columns:4 150px;list-style:none;padding:0;margin:6px 0}.az li{break-inside:avoid}.az a{display:inline-flex;min-height:34px;align-items:center}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.pill{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:6px 15px;border-radius:999px;background:#fff;border:1px solid var(--line);text-decoration:none;color:var(--ink);font-weight:650}
.pill small{color:var(--soft);font-weight:500}.pill:hover,.pill:focus-visible{border-color:var(--green2);background:var(--mint)}
.guides{display:grid;gap:10px}.guide{display:block;background:#fff;border:1px solid var(--line);border-left:5px solid var(--green2);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--ink)}
.guide strong{color:var(--link);text-decoration:underline;text-underline-offset:3px}.guide span{display:block;font-size:.9rem;color:var(--soft)}
.family{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,250px),1fr));gap:12px;margin:12px 0}
.site-card{display:block;background:#fff;border:1px solid var(--line);border-top:5px solid var(--gold);border-radius:12px;padding:14px 16px;text-decoration:none;color:var(--ink)}
.site-card strong{display:block;font-size:1.05rem;color:var(--link)}.site-card .u{font-size:.85rem;color:var(--soft)}.site-card p{margin:.35em 0 0;font-size:.93rem}
.site-card:hover,.site-card:focus-visible,.guide:hover,.guide:focus-visible{box-shadow:0 6px 18px rgba(23,35,30,.1)}
.glance{background:#fff;border:1px solid var(--line);border-radius:14px;padding:4px 16px;margin:14px 0}.glance ul{list-style:none;margin:0;padding:0}
.glance li{border-top:1px solid #eceee9}.glance li:first-child{border-top:0}
.glance a{display:grid;grid-template-columns:minmax(0,210px) 1fr;gap:2px 14px;padding:10px 0;text-decoration:none;color:var(--ink);align-items:baseline}.glance .q{font-weight:650;color:var(--link)}
.onpage{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:.95rem;margin:8px 0}.onpage a{min-height:40px;display:inline-flex;align-items:center}
.medcard{background:#fff;border:1px solid var(--line);border-left:6px solid #3b7fa0;border-radius:14px;padding:6px 18px 12px;margin:18px 0}.medcard h2{margin-top:.6em}.steps{padding-left:1.3em}.steps li{margin:.3em 0}.facts{display:grid;grid-template-columns:minmax(0,170px) 1fr;gap:6px 16px;margin:12px 0}.facts dt{font-weight:700}.facts dd{margin:0}.mednote{background:#fff4dc;border-radius:8px;padding:8px 12px}.medlinks{display:flex;flex-wrap:wrap;gap:8px}@media(max-width:560px){.facts{grid-template-columns:1fr}.facts dd{margin-bottom:6px}}.next{background:var(--mint);border-radius:14px;padding:14px 18px;margin:26px 0}.next h2{margin:0 0 .3em;font-size:1.2rem}.next ul{margin:.3em 0;padding-left:1.2em}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:8px 0;min-width:0;scroll-margin-top:12px}.card h3,.card h4{margin:0 0 6px;font-size:1rem;line-height:1.35}.card p{margin:.25rem 0}
.chip{display:inline-block;border:1px solid;border-radius:999px;padding:0 10px;font-size:.82rem;font-weight:700;line-height:1.7;white-space:nowrap}
.chip.allowed,.chip.positive,.chip.broad{background:#e7f3eb;border-color:#2e7d4f;color:#1d5a37}.chip.medical-only{background:#e5f1f7;border-color:#3b7fa0;color:#1d4f68}
.chip.limited,.chip.varies-locally,.chip.partial,.chip.starter{background:#fff4dc;border-color:#b8860b;color:#664a00}
.chip.not-permitted,.chip.negative{background:#fbeaea;border-color:#a90000;color:#7a0000}.chip.not-reviewed,.chip.not-started{background:#f0f0f0;border-color:#888;color:#444}
.level{display:inline-block;font-size:.78rem;font-weight:700;border-radius:4px;padding:0 6px;background:#eef3fb;color:#24426e}.level.compilation{background:#fff4dc;color:#664a00}
.short{font-weight:650}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,290px),1fr));gap:8px;list-style:none;padding:0;margin:12px 0}
.grid li{background:#fff;border:1px solid var(--line);border-radius:8px;padding:9px 12px;min-width:0}.grid li[hidden]{display:none}.grid .state{font-weight:700;font-size:1.05rem;display:inline-flex;min-height:36px;align-items:center}
.grid .chips{display:flex;flex-wrap:wrap;gap:4px 6px;font-size:.85rem;align-items:center}.grid .meta{font-size:.82rem;color:var(--soft);margin:4px 0 0}
select{font:inherit;min-height:48px;padding:6px 9px;border:1px solid #888;border-radius:8px;background:#fff;color:var(--ink)}
table{border-collapse:collapse;width:100%;background:#fff}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}.scroll{overflow-x:auto}
.sources{font-size:.9rem;padding-left:1.6em}.sources li{margin:.3em 0;overflow-wrap:anywhere}.cites a{font-size:.82rem;margin-left:2px}
.needs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,230px),1fr));gap:10px;margin:12px 0}
.need{display:block;background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--ink)}
.need strong{display:block;color:var(--link);text-decoration:underline;text-underline-offset:3px}.need span{display:block;font-size:.9rem;color:var(--soft);margin-top:2px}
.need:hover,.need:focus-visible{border-color:var(--link)}
.rows{list-style:none;padding:0;margin:12px 0}.rows li{background:#fff;border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:6px 0;display:grid;grid-template-columns:minmax(120px,190px) 1fr;gap:4px 14px;align-items:baseline}
.rows li[hidden]{display:none}.rows .state{font-weight:700}.rows .meta{grid-column:2;font-size:.82rem;color:var(--soft);margin:0}.tally{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin:8px 0}
footer.site{background:#13261d;color:#c9d7cf;margin-top:44px;font-size:.92rem}footer.site .wrap{padding:26px 20px 30px}footer.site a{color:#fff}
footer.site h2{font-size:1rem;color:var(--gold);margin:0 0 .3em;text-transform:uppercase;letter-spacing:.07em}
footer.site .cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:18px}footer.site ul{list-style:none;padding:0;margin:0}footer.site li a{display:inline-flex;min-height:36px;align-items:center}
footer.site p{max-width:none;margin:18px 0 0;color:#a9bcb1}
@media(max-width:900px){.tasks{grid-template-columns:repeat(3,minmax(0,1fr))}.mapbox{grid-template-columns:1fr;gap:6px}}
@media(max-width:720px){.hero .wrap{grid-template-columns:1fr;padding-top:24px;padding-bottom:34px}.hero .art{order:-1}.hero .art img{max-width:340px;margin:0}}
@media(max-width:560px){header.site nav{margin-left:0;gap:0 16px}header.site .wrap{padding-bottom:4px}.tasks{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.task{padding:12px}
.usmap{gap:3px}.tile{border-radius:4px}.glance a{grid-template-columns:1fr}.needs{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.need{padding:10px 11px}.rows li{grid-template-columns:1fr}.rows .meta{grid-column:1}}
@media print{header.site nav,footer.site,select,label,.pick{display:none}}
'''

ASSETS = '../assets/the-reefer/'  # national/ pages; the published copy sits at the root (see scripts/build_pages_site.py)
LOGO_ALT = 'The-Reefer.com logo: a pirate skull in a red bandana and eye patch over crossed bones and a cannabis leaf'

ICON_PATHS = {
    'scale': 'M12 3v18M6 21h12M4 7h16M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z',
    'bag': 'M5 8h14l-1 12H6zM9 8V6a3 3 0 0 1 6 0v2',
    'sprout': 'M12 21v-9M12 12C12 8 9 6 5 6c0 4 3 6 7 6zM12 12c0-4 3-7 7-7 0 4-3 7-7 7z',
    'plane': 'M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z',
    'record': 'M7 3h7l5 5v13H7zM14 3v5h5M10 14.5l2 2 4-4',
    'star': 'M12 3l2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3l-5.5 2.9 1-6.2L3 9.6l6.2-.9z',
    'heart': 'M12 20s-7-4.4-9-9a4.5 4.5 0 0 1 9-3 4.5 4.5 0 0 1 9 3c-2 4.6-9 9-9 9zM12 10v5M9.5 12.5h5',
    'person': 'M4 21c0-3.3 3.6-5.5 8-5.5s8 2.2 8 5.5M12 12.5a4.25 4.25 0 1 0 0-8.5 4.25 4.25 0 0 0 0 8.5z',
    'megaphone': 'M3 10v4h3l7 4V6l-7 4zM16.5 9.5a3.5 3.5 0 0 1 0 5M19 7a7 7 0 0 1 0 10',
    'briefcase': 'M3 8h18v12H3zM9 8V5h6v3M3 13h18',
    'card': 'M3 6h18v12H3zM3 10h18M7 15h4M15 13.5v3M13.5 15h3',
}


def icon(name):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="{ICON_PATHS[name]}"/></svg>')


# A tile map: every state the same size, placed roughly where it sits on a US map (row, column).
TILES = {
    'AK': (0, 0), 'ME': (0, 10), 'WI': (1, 5), 'VT': (1, 9), 'NH': (1, 10),
    'WA': (2, 0), 'ID': (2, 1), 'MT': (2, 2), 'ND': (2, 3), 'MN': (2, 4), 'IL': (2, 5), 'MI': (2, 6), 'NY': (2, 8), 'MA': (2, 9),
    'OR': (3, 0), 'NV': (3, 1), 'WY': (3, 2), 'SD': (3, 3), 'IA': (3, 4), 'IN': (3, 5), 'OH': (3, 6), 'PA': (3, 7), 'NJ': (3, 8), 'CT': (3, 9), 'RI': (3, 10),
    'CA': (4, 0), 'UT': (4, 1), 'CO': (4, 2), 'NE': (4, 3), 'MO': (4, 4), 'KY': (4, 5), 'WV': (4, 6), 'VA': (4, 7), 'MD': (4, 8), 'DE': (4, 9),
    'AZ': (5, 1), 'NM': (5, 2), 'KS': (5, 3), 'AR': (5, 4), 'TN': (5, 5), 'NC': (5, 6), 'SC': (5, 7), 'DC': (5, 8),
    'OK': (6, 3), 'LA': (6, 4), 'MS': (6, 5), 'AL': (6, 6), 'GA': (6, 7),
    'HI': (7, 0), 'TX': (7, 3), 'FL': (7, 8),
}


def tone_of(question, status):
    own = (question or {}).get('statuses', {}).get(status)
    return own['tone'] if own else status


def tile_map(perm, question, answers, caption):
    """Each state colored by its answer to one question; a state with no reviewed answer is grey, never 'prohibited'."""
    names = perm['jurisdictions']
    cells, tally = [], {}
    for code, (row, col) in TILES.items():
        a = answers.get(code, {}).get(question['id'])
        status = a['status'] if a else 'not-reviewed'
        tally[status] = tally.get(status, 0) + 1
        label = status_label(perm, question, status) + (f': {a["short"]}' if a else '')
        cells.append(f'<a class="tile {esc(tone_of(question, status))}" data-track="map-state" style="grid-row:{row + 1};grid-column:{col + 1}" '
                     f'href="{slug(names[code])}.html" title="{esc(names[code])}: {esc(label)}" aria-label="{esc(names[code])}: {esc(label)}">{code}</a>')
    order = [st for st in list(question.get('statuses', {})) + list(perm['statuses']) if st in tally]
    legend = ''.join(f'<li><span class="sw {esc(tone_of(question, st))}"></span>{esc(status_label(perm, question, st))} ({tally[st]})</li>' for st in order)
    return (f'<div class="usmap" role="group" aria-label="{esc(caption)}">' + ''.join(cells) + '</div>',
            f'<ul class="legend" aria-label="Map key">{legend}</ul>')


# The other sites in the same family. Every page links to them.
FAMILY = [
    (OHIO_HOME + '/', 'OhioWeed.org', 'ohioweed.org', 'The complete Ohio guide: business directory, dispensary finder, record clearing and advocacy.'),
    ('https://mobilitytalk.org/', 'Mobility Talk', 'mobilitytalk.org', 'Mobility resources and advocacy for people across the country.'),
    ('https://findbingo.org/', 'Find Bingo', 'findbingo.org', 'Find bingo games and halls near you.'),
    ('https://vethomeguard.org/', 'Veteran Home Guardians', 'vethomeguard.org', 'The veteran nonprofit this work is shared in support of.'),
    ('https://travisvought.com/', 'All sites by Travis Vought', 'travisvought.com', 'Every directory, guide and project in one place.'),
]

def esc(value):
    return html.escape(str(value), quote=True)


def long_date(value):
    d = date.fromisoformat(value)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def load():
    read = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))
    return read('data/state-permissions.json'), read('data/state-scorecard.json'), read('data/directory.json')


def load_medical():
    """Patient guides for the medical-only states (data/medical-programs.json), keyed by state code."""
    data = json.loads((ROOT / 'data/medical-programs.json').read_text(encoding='utf-8'))
    return data, {p['state']: p for p in data['states']}


def load_coverage():
    """Who pays for medical cannabis (data/medical-coverage.json)."""
    return json.loads((ROOT / 'data/medical-coverage.json').read_text(encoding='utf-8'))


MEDICAL_ROWS = [('who', 'Who can get one'), ('fee', 'Cost'), ('card_length', 'How long it lasts'), ('caregivers', 'Caregivers'),
                ('visitors', 'Visiting patients'), ('buy', 'Where patients buy')]


def medical_section(prog, cites, name):
    """How patients get a card, each fact marked with its regulator source."""
    out = [f'<section class="medcard" id="medical-card" aria-labelledby="medical-card-h"><h2 id="medical-card-h">How patients get a medical card in {esc(name)}</h2>',
           f'<p class="muted">From {esc(prog["agency"])}. Adults without a card cannot buy here.</p>']
    if prog.get('note'):
        out.append(f'<p class="mednote">{esc(prog["note"]["text"])} {cites.mark([prog["note"]["source"]])}</p>')
    if prog.get('steps'):
        out.append('<h3>Steps</h3><ol class="steps">' + ''.join(f'<li>{esc(x)}</li>' for x in prog['steps']['items'])
                   + f'</ol><p class="muted">Steps as the state describes them {cites.mark([prog["steps"]["source"]])}</p>')
    rows = [(label, prog[key]) for key, label in MEDICAL_ROWS if prog.get(key)]
    if rows:
        out.append('<dl class="facts">' + ''.join(f'<dt>{esc(label)}</dt><dd>{esc(f["text"])} {cites.mark([f["source"]])}</dd>' for label, f in rows) + '</dl>')
    missing = [label for key, label in MEDICAL_ROWS if not prog.get(key)]
    if missing:
        out.append(f'<p class="muted">Not stated on the state pages we checked: {esc(", ".join(m.lower() for m in missing))}. Check with the state.</p>')
    out.append('<p><a href="coverage.html">Does Medicaid, Medicare or insurance pay for it?</a></p>')
    out.append('<p class="medlinks">' + ''.join(f'<a class="pill" href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["label"])}</a>' for l in prog['links']) + '</p>')
    out.append('</section>')
    return ''.join(out)


def correction_url(place):
    body = 'Page or state:\r\n\r\nAddition or correction:\r\n\r\nWebsite or source:\r\n\r\n'
    return 'mailto:' + EMAIL + '?' + urlencode({'subject': f'{SITE_NAME}: correction for {place}', 'body': body}, quote_via=quote)


def page_url(name):
    return ORIGIN + '/' + ('' if name == 'index.html' else name)


def json_ld(nodes):
    """Structured data for search engines. Only text already shown on the page; absolute URLs need ORIGIN."""
    if not ORIGIN or not nodes:
        return ''
    data = {'@context': 'https://schema.org', '@graph': nodes}
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return f'<script type="application/ld+json">{text}</script>'


def breadcrumbs(trail, name, title):
    """BreadcrumbList matching the visible crumbs: trail is [(label, page)], the current page comes last."""
    items = [{'@type': 'ListItem', 'position': i, 'name': label, 'item': ORIGIN + '/' + page}
             for i, (label, page) in enumerate(trail, 1)]
    items.append({'@type': 'ListItem', 'position': len(items) + 1, 'name': title, 'item': page_url(name)})
    return {'@type': 'BreadcrumbList', '@id': page_url(name) + '#breadcrumb', 'itemListElement': items}


def website_node():
    return {'@type': 'WebSite', '@id': ORIGIN + '/#website', 'url': ORIGIN + '/', 'name': SITE_NAME,
            'alternateName': 'The-Reefer.com', 'description': TAGLINE, 'inLanguage': 'en-US',
            'license': 'https://creativecommons.org/licenses/by/4.0/',
            'creator': {'@type': 'Person', 'name': 'Travis Vought', 'url': 'https://travisvought.com/'}}


def shell(title, description, body, name, place, hero='', ld=None):
    head = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            f'<title>{esc(title)} | {esc(SITE_NAME)}</title>',
            f'<meta name="description" content="{esc(description)}">',
            '<meta name="theme-color" content="#1d4a37">',
            f'<link rel="icon" type="image/png" href="{ASSETS}favicon-64.png"><link rel="apple-touch-icon" href="{ASSETS}apple-touch-icon.png">',
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(SITE_NAME)}">',
            f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}">']
    if ORIGIN:
        href = page_url(name)
        head.append(f'<link rel="canonical" href="{esc(href)}"><meta property="og:url" content="{esc(href)}">'
                    f'<meta property="og:image" content="{ORIGIN}/assets/the-reefer/logo-share.jpg"><meta property="og:image:width" content="1200">'
                    f'<meta property="og:image:height" content="800"><meta property="og:image:alt" content="{esc(LOGO_ALT)}"><meta name="twitter:card" content="summary_large_image">')
    else:
        head.append('<meta name="robots" content="noindex,follow">')
    if ld and ORIGIN:
        head.append(json_ld(ld))
    head.append(f'<style>{CSS}</style></head><body>')
    top = (f'<header class="site"><div class="wrap"><a class="brand" href="index.html" aria-label="{esc(SITE_NAME)} home"><img src="{ASSETS}mark-96.png" alt="" width="40" height="40"><span>{esc(SITE_NAME)}</span></a>'
           '<nav aria-label="Primary"><a href="index.html#map">Your state</a><a href="medical.html">Medical cards</a><a href="index.html#compare">Compare laws</a>'
           '<a href="help.html">Get help</a><a href="about.html">About</a></nav></div></header>')
    family = ''.join(f'<li><a href="{esc(url)}">{esc(label)}</a></li>' for url, label, _, _ in FAMILY)
    foot = ('<footer class="site"><div class="wrap"><div class="cols">'
            '<nav aria-label="This site"><h2>This site</h2><ul><li><a href="index.html#map">Pick your state</a></li>'
            '<li><a href="index.html#compare">Compare the law</a></li><li><a href="help.html">Get help</a></li><li><a href="about.html">About and methods</a></li></ul></nav>'
            f'<nav aria-label="Our other sites"><h2>Our other sites</h2><ul>{family}</ul></nav>'
            '<nav aria-label="Corrections and data"><h2>Fix or reuse</h2><ul>'
            f'<li><a href="{esc(correction_url(place))}">Suggest a correction</a></li>'
            f'<li><a href="{REPO}#readme">Methods &amp; sources</a></li>'
            f'<li><a href="{REPO}/blob/main/architecture/STATE_COMPLETION_STANDARD.md">State completion standard</a></li></ul></nav></div>'
            '<p>Summaries of the cited sources, each with the date it was checked. Not legal advice. A missing answer means not yet reviewed, '
            'never that something is prohibited. Free to use under CC BY 4.0. Created and maintained by Travis Vought, shared in support of Veteran Home Guardians.</p></div></footer>')
    return ''.join(head) + top + hero + '<main>' + body + '</main>' + foot + '<script src="../assets/analytics.js" defer></script></body></html>\n'

class Cites:
    """Per-page source numbering, in order of first use."""

    def __init__(self, sources):
        self.sources, self.order = sources, []

    def mark(self, ids):
        out = []
        for sid in ids:
            if sid not in self.order:
                self.order.append(sid)
            n = self.order.index(sid) + 1
            out.append(f'<a href="#source-{n}" aria-label="Source {n}">[{n}]</a>')
        return '<span class="cites">' + ''.join(out) + '</span>'

    def render(self):
        if not self.order:
            return ''
        out = ['<h2 id="sources">Sources</h2><ol class="sources">']
        for n, sid in enumerate(self.order, 1):
            s = self.sources[sid]
            out.append(f'<li id="source-{n}"><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a> · {esc(s["publisher"])} · '
                       f'{esc(KIND_LABEL[s["kind"]])} · retrieved {long_date(s["retrieved_on"])}</li>')
        out.append('</ol>')
        return ''.join(out)


def answers_by_state(perm):
    out = {}
    for a in perm['answers']:
        out.setdefault(a['state'], {})[a['question']] = a
    return out


def pack_link(code, pack, pathway_id):
    """Where a built pathway lives today. Ohio is published at ohioweed.org; pilots use the shared state page."""
    if code == 'OH':
        url = next((p.get('public_url') for p in pack['pathways'] if p['pathway_id'] == pathway_id), None)
        return (OHIO_HOME + (urlparse(url).path.replace('/index.html', '/') or '/') + ('#' + urlparse(url).fragment if urlparse(url).fragment else '')
                if url and url.startswith(DEFAULT_SITE_ORIGIN) else OHIO_HOME + '/')
    return f'../state.html?state={code}&pathway={pathway_id}'


def law_section(perm, code, state_answers, cites, sources):
    name = perm['jurisdictions'][code]
    out = [f'<h2 id="law">The law in {esc(name)}</h2>',
           f'<p>The same {len(perm["questions"])} questions are asked of every state. Each answer names its source and the date it was checked.</p>']
    for group in perm['groups']:
        out.append(f'<h3>{esc(group["label"])}</h3>')
        for q in (q for q in perm['questions'] if q['group'] == group['id']):
            a = state_answers.get(q['id'])
            note = f'<p class="muted">{esc(q["note"])}</p>' if q.get('note') else ''
            if not a:
                out.append(f'<article class="card" id="q-{esc(q["id"])}" data-question="{esc(q["id"])}"><h4>{esc(q["question"])}</h4>{note}'
                           f'<p>{chip(perm, "not-reviewed")} <span class="muted">No reviewed source yet. This does not mean it is prohibited.</span></p></article>')
                continue
            level = evidence_level(a, sources)
            effective = f' · in effect {long_date(a["effective_on"])}' if a.get('effective_on') else ''
            out.append(f'<article class="card" id="q-{esc(q["id"])}" data-question="{esc(q["id"])}"><h4>{esc(q["question"])}</h4>{note}'
                       f'<p>{chip(perm, a["status"], q)} <span class="short">{esc(a["short"])}</span></p><p>{esc(a["detail"])}</p>'
                       f'<p class="muted">{esc(a["citation"])}{effective} · checked {long_date(a["reviewed_on"])} {cites.mark(a["source_ids"])} '
                       f'<span class="level {esc(level)}">{esc(LEVEL_TEXT[level])}</span></p></article>')
    return ''.join(out)


def pathway_section(code, name, pathways, card, pack):
    out = [f'<h2 id="directory">Directory and local help in {esc(name)}</h2>']
    if card:
        out.append(f'<p>{esc(name)} has a {esc(PACK_LABEL[card["publication_status"]].lower())}. Levels are earned from the data under the '
                   f'<a href="{REPO}/blob/main/architecture/STATE_COMPLETION_STANDARD.md">state completion standard</a>; none of the levels means exhaustive coverage.</p>')
    else:
        out.append(f'<p>The {esc(name)} directory has not been started. Ohio is the template: these are the seven parts every state guide is built toward. '
                   '“Not started” means no records have been reviewed yet, not that help does not exist. '
                   '<a href="help.html">National resources that cover every state</a> are available now.</p>')
    for p in pathways:
        row = (card or {}).get('pathways', {}).get(p['id'])
        if row:
            nxt = f'<p class="muted">Next level needs: {esc(row["next"])}</p>' if row.get('next') else ''
            out.append(f'<article class="card" data-pathway="{esc(p["id"])}"><h3><a href="{esc(pack_link(code, pack, p["id"]))}">{esc(p["label"])}</a></h3>'
                       f'<p><span class="chip {esc(row["level"])}">{esc(LEVELS[row["level"]])}</span> {esc(p["task"])}</p>{nxt}</article>')
        else:
            out.append(f'<article class="card" data-pathway="{esc(p["id"])}"><h3>{esc(p["label"])}</h3>'
                       f'<p><span class="chip not-started">Not started</span> {esc(p["task"])}</p></article>')
    return ''.join(out)


def glance(perm, state_answers, name):
    """Every question in one short list, each linking to its full answer below. No new wording: the short answer as published."""
    rows = []
    for q in perm['questions']:
        a = state_answers.get(q['id'])
        right = (f'{chip(perm, a["status"], q)} {esc(a["short"])}' if a else chip(perm, 'not-reviewed'))
        rows.append(f'<li><a href="#q-{esc(q["id"])}"><span class="q">{esc(LAW_BLURB.get(q["id"], q["question"]))}</span><span>{right}</span></a></li>')
    return (f'<section class="glance" id="glance" aria-label="{esc(name)} at a glance"><ul>' + ''.join(rows) + '</ul></section>')


def state_page(perm, score, directory, code, answers, sources, medical=None):
    name = perm['jurisdictions'][code]
    state_answers = answers.get(code, {})
    cites = Cites(sources)
    card = score['states'].get(code)
    pack = next((s for s in directory['states'] if s['code'] == code), None)
    body = [f'<p class="crumbs"><a href="index.html#map">All states</a> › {esc(name)}</p>',
            f'<h1>{esc(name)} cannabis guide</h1>']
    link = perm['official_links'].get(code)
    if link:
        s = sources[link['source_id']]
        body.append(f'<p>Official state site: <a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a> '
                    f'<span class="muted">({esc(s["publisher"])}, checked {long_date(s["retrieved_on"])})</span></p>')
    else:
        body.append('<p>Official state site: <span class="muted">not yet reviewed</span></p>')
    if code == 'OH':
        body.append(f'<p><strong>Ohio’s full guide lives at <a href="{OHIO_HOME}/">OhioWeed.org</a></strong>: business directory, dispensary finder, record clearing, advocacy and more.</p>')
    prog = (medical or {}).get(code)
    body.append('<nav class="onpage" aria-label="On this page">' + ('<a href="#medical-card">Get a medical card</a>' if prog else '')
                + '<a href="#glance">At a glance</a><a href="#law">The law in detail</a><a href="#directory">Local help</a><a href="#sources">Sources</a></nav>')
    if prog:
        body.append(medical_section(prog, cites, name))
    body.append(glance(perm, state_answers, name))
    body.append(law_section(perm, code, state_answers, cites, sources))
    body.append(pathway_section(code, name, directory['pathways'], card, pack))
    guide = (f'<li><a href="{guide_link(code, name)}">The full {esc(name)} guide</a>: directory and local help</li>' if card else '')
    body.append(f'<aside class="next" aria-label="Where to go next"><h2>Where to go next</h2><ul>{guide}'
                '<li><a href="help.html">National help</a>: travel, veterans, legal aid, health and safety</li>'
                '<li><a href="index.html#compare">Compare a rule across every state</a></li>'
                '<li><a href="index.html#map">Pick another state</a></li></ul></aside>')
    body.append(cites.render())
    answered = len(state_answers)
    description = f'{name} cannabis law in plain language: {answered} of {len(perm["questions"])} questions answered from named sources, plus directory and local help.'
    page, title = slug(name) + '.html', f'{name} cannabis guide'
    ld = [breadcrumbs([('All states', '')], page, name)]
    faq = faq_node(perm, state_answers, page)
    if faq:
        ld.append(faq)
    return shell(title, description, ''.join(body), page, name, ld=ld)


def faq_node(perm, state_answers, page):
    """The answered law questions as FAQPage data: the question, short answer, detail and citation shown on the page."""
    entries = []
    for q in perm['questions']:
        a = state_answers.get(q['id'])
        if not a:
            continue
        effective = f', in effect {long_date(a["effective_on"])}' if a.get('effective_on') else ''
        text = (f'{a["short"].rstrip(".")}. {a["detail"]} '
                f'Source: {a["citation"]}{effective}, checked {long_date(a["reviewed_on"])}.')
        entries.append({'@type': 'Question', 'name': q['question'], 'acceptedAnswer': {'@type': 'Answer', 'text': text}})
    if not entries:
        return None
    return {'@type': 'FAQPage', '@id': page_url(page) + '#law', 'url': page_url(page),
            'isPartOf': {'@id': ORIGIN + '/#website'}, 'mainEntity': entries}


NEED_BLURB = {
    'Federal law': 'Where federal scheduling stands',
    'State laws': 'A national guide to each state’s laws and penalties',
    'Travel': 'What the TSA says about flying',
    'Patients traveling': 'Using a medical card away from home',
    'Veterans': 'VA care and state cannabis programs',
    'Legal help': 'Find free civil legal aid',
    'Record clearing': 'National guides to sealing and expungement',
    'Contact lawmakers': 'Find your state legislators by address',
    'Health and safety': 'Poison Help and the national helpline',
    'Business': 'The national industry association',
}
LAW_BLURB = {
    'adult-use': 'Is adult use legal?',
    'medical': 'Is there a medical program?',
    'buying': 'Where adults can buy',
    'possession': 'How much an adult can have',
    'sharing': 'Sharing and gifting',
    'home-grow': 'Growing at home',
    'public-use': 'Using it in public',
    'driving': 'Driving rules',
    'employment': 'Work and off-the-job use',
    'record-relief': 'Clearing a past record',
}


def law_page_name(question_id):
    return f'law-{question_id}.html'


def needs_in_order(perm):
    seen = []
    for item in perm['national']:
        if item['need'] not in seen:
            seen.append(item['need'])
    return seen


def status_label(perm, question, status):
    own = question.get('statuses', {}).get(status)
    return own['label'] if own else perm['statuses'][status]


def help_page(perm, sources):
    cites = Cites(sources)
    body = ['<p class="crumbs"><a href="index.html">Home</a> › Help by need</p>', '<h1>Help by need</h1>',
            '<p>Federal rules, national help lines and organizations that cover every state. Each links to the agency or organization that runs it. '
            'A listing is not an endorsement; advocacy groups are named as such. For state-specific help, <a href="index.html#map">pick your state</a>.</p>',
            '<nav class="pills" aria-label="Jump to a need">' + ''.join(f'<a class="pill" href="#{slug(n)}">{esc(n)}</a>' for n in needs_in_order(perm)) + '</nav>']
    for need in needs_in_order(perm):
        body.append(f'<h2 id="{slug(need)}">{esc(need)}</h2>')
        for i in (i for i in perm['national'] if i['need'] == need):
            body.append(f'<article class="card" data-national="{esc(i["id"])}"><h3><a href="{esc(i["url"])}" target="_blank" rel="noopener">{esc(i["title"])}</a></h3>'
                        f'<p>{esc(i["text"])}</p><p class="muted">Checked {long_date(i["reviewed_on"])} {cites.mark(i["source_ids"])}</p></article>')
    body.append(cites.render())
    return shell('Help by need', 'National cannabis help lines, federal rules and organizations that cover every state, grouped by what you need.',
                 ''.join(body), 'help.html', 'the help page', ld=[breadcrumbs([('Home', '')], 'help.html', 'Help by need')])


def medical_page(perm, med_data, medical, answers, sources):
    """Medical cards state by state: medical-only states first, each with cost, visitors and a link to its full patient guide."""
    names = perm['jurisdictions']
    grid, legend = tile_map(perm, next(x for x in perm['questions'] if x['id'] == 'adult-use'), answers,
                            'Map: adult use and medical-only states. Select a state to open its guide.')
    cites = Cites(sources)
    body = ['<p class="crumbs"><a href="index.html">Home</a> › Medical cards</p>',
            '<h1>Getting a medical cannabis card, state by state</h1>',
            f'<p class="lede">In {len(medical)} states, medical cannabis is legal but adult use is not, so a state card is the only legal way to buy. '
            'Each state below links to its patient guide: who qualifies, the steps, the cost and whether visiting patients can buy. Every fact comes from the state regulator.</p>',
            f'<div class="mapbox"><div>{grid}{legend}</div><div><h2 style="margin-top:0">Medical-only states</h2><p class="muted">Blue on the map. '
            f'Patient facts checked {long_date(med_data["as_of"])}.</p></div></div>',
            '<div class="guides">']
    for code in sorted(medical, key=lambda c: names[c]):
        prog = medical[code]
        bits = [f'Cost: {prog["fee"]["text"]}' if prog.get('fee') else '', f'Visitors: {prog["visitors"]["text"]}' if prog.get('visitors') else '',
                prog['note']['text'] if prog.get('note') and not prog.get('steps') else '']
        if not any(bits):
            bits = [f'Where patients buy: {prog["buy"]["text"]}' if prog.get('buy') else f'Who: {prog["who"]["text"]}']
        body.append(f'<a class="guide" href="{slug(names[code])}.html#medical-card"><strong>{esc(names[code])}</strong>'
                    + ''.join(f'<span>{esc(b)}</span>' for b in bits if b) + '</a>')
    body.append('</div>')
    limited = sorted(c for c in names if answers.get(c, {}).get('medical', {}).get('status') == 'limited')
    if limited:
        body.append('<h2>States with narrow programs</h2><p>These states allow only low-THC oil or CBD for certain conditions. Open a state to read its answer and source.</p><ul class="pills" style="list-style:none;padding:0">'
                    + ''.join(f'<li><a class="pill" href="{slug(names[c])}.html#q-medical">{esc(names[c])} <small>{esc(answers[c]["medical"]["short"])}</small></a></li>' for c in limited) + '</ul>')
    body.append('<h2>Paying for it</h2><p>Medicaid, Medicare and insurance generally do not pay for medical cannabis, but some states cut the card fee. '
                '<a href="coverage.html">See who pays and where the card costs less</a>.</p>')
    body.append('<h2>States where adults can buy</h2><p>Every adult-use state also has a medical program, often with lower taxes or higher limits for patients. '
                '<a href="law-medical.html">See every state’s medical program on one page</a>.</p>')
    body.append('<p class="muted">Summaries of state regulator pages, each linked on the state’s page. Not medical or legal advice. A blank fact means the state page we checked did not say.</p>')
    title = 'How to get a medical cannabis card in each state'
    return shell(title, 'How patients get a medical cannabis card in each medical-only state: who qualifies, steps, cost and visiting-patient rules, from state regulators.',
                 ''.join(body), 'medical.html', 'the medical cards page', ld=[breadcrumbs([('Home', '')], 'medical.html', 'Medical cards')])


def law_page(perm, question, answers, sources):
    names = perm['jurisdictions']
    total = len(names)
    rows, tally = [], {}
    for code in sorted(names, key=lambda c: names[c]):
        a = answers.get(code, {}).get(question['id'])
        page = slug(names[code]) + '.html'
        if not a:
            tally['not-reviewed'] = tally.get('not-reviewed', 0) + 1
            rows.append(f'<li data-state="{esc(code)}" data-status="not-reviewed"><a class="state" href="{page}">{esc(names[code])}</a>'
                        f'<span>{chip(perm, "not-reviewed")} <span class="muted">No reviewed source yet. This does not mean it is prohibited.</span></span></li>')
            continue
        tally[a['status']] = tally.get(a['status'], 0) + 1
        level = evidence_level(a, sources)
        rows.append(f'<li data-state="{esc(code)}" data-status="{esc(a["status"])}"><a class="state" href="{page}">{esc(names[code])}</a>'
                    f'<span>{chip(perm, a["status"], question)} <span class="short">{esc(a["short"])}</span></span>'
                    f'<p class="meta">Checked {long_date(a["reviewed_on"])} · {esc(LEVEL_TEXT[level])} · <a href="{page}#law">details and source</a></p></li>')
    order = [st for st in list(question.get('statuses', {})) + list(perm['statuses']) if st in tally]
    options = ''.join(f'<option value="{esc(st)}">{esc(status_label(perm, question, st))} ({tally[st]})</option>' for st in order)
    chips = ' '.join(f'<span>{chip(perm, st, question)} {tally[st]}</span>' for st in order)
    note = f'<p class="muted">{esc(question["note"])}</p>' if question.get('note') else ''
    answered = total - tally.get('not-reviewed', 0)
    map_grid = ''.join(tile_map(perm, question, answers, f'Map: {question["question"]} Select a state to open its guide.'))
    body = ['<p class="crumbs"><a href="index.html">Home</a> › <a href="index.html#compare">Compare the law</a></p>',
            f'<h1>{esc(question["question"])}</h1>',
            f'<p>Every state and DC, side by side. {answered} of {total} are answered from a named source; open a state for the full answer, its citation and its source.</p>{note}',
            map_grid, '<p class="muted">Tap a state for its full answer and source, or use the list below.</p>',
            f'<h2 id="list">Every state in a list</h2><div class="tally">{chips}</div>',
            f'<label for="status-filter">Show</label> <select id="status-filter"><option value="">All {total}</option>{options}</select>',
            '<ul class="rows" id="rows">' + ''.join(rows) + '</ul>',
            '<script>(function(){var f=document.getElementById("status-filter");f.addEventListener("change",function(){'
            'document.querySelectorAll("#rows li").forEach(function(li){li.hidden=!!f.value&&li.getAttribute("data-status")!==f.value})})})();</script>']
    description = f'{question["question"]} All 50 states and DC compared, each answer traced to a named source and the date it was checked.'
    page = law_page_name(question['id'])
    ld = [breadcrumbs([('Home', ''), ('Compare the law', '#compare')], page, question['question'])]
    return shell(question['question'], description, ''.join(body), page, 'the state comparison', ld=ld)


def progress_section(perm, score, directory, answers):
    pathways = directory['pathways']
    total = len(perm['questions'])
    full = sum(len(answers.get(c, {})) == total for c in perm['jurisdictions'])
    out = ['<h2 id="progress">Build progress</h2>',
           f'<p>Ohio is the template. Every state is built toward the same seven-part guide and measured by the same standard. '
           f'{full} of {len(perm["jurisdictions"])} jurisdictions have all {total} law questions answered; '
           f'{len(score["states"])} have a state guide. Scorecard as of {long_date(score["as_of"])}.</p>',
           '<div class="scroll"><table><thead><tr><th scope="col">State guide</th>']
    out += [f'<th scope="col">{esc(p["label"])}</th>' for p in pathways]
    out.append('</tr></thead><tbody>')
    for code, card in score['states'].items():
        out.append(f'<tr><th scope="row"><a href="{slug(card["name"])}.html">{esc(card["name"])}</a> <span class="muted">({esc(card["publication_status"])})</span></th>')
        out += [f'<td><span class="chip {esc(card["pathways"][p["id"]]["level"])}">{esc(LEVELS[card["pathways"][p["id"]]["level"]])}</span></td>' for p in pathways]
        out.append('</tr>')
    out.append('</tbody></table></div><p class="muted">Every other state shows “Not started” for these seven parts until its records are reviewed.</p>')
    return ''.join(out)


def about_page(perm, score, directory, answers):
    total_answers = len(perm['answers'])
    body = ['<p class="crumbs"><a href="index.html">Home</a> › About</p>', f'<h1>About {esc(SITE_NAME)}</h1>',
            f'<p>{esc(SITE_NAME)} is a free cannabis information and resource portal for all 50 states and DC. It grew out of the Ohio Cannabis Directory at '
            f'<a href="{OHIO_HOME}/">OhioWeed.org</a>, which is the template every state is built toward.</p>',
            '<h2 id="method">How the information is checked</h2>',
            f'<p>Every answer names its source and the date it was checked. The site holds {total_answers} reviewed answers from {len(perm["sources"])} sources, as of {long_date(perm["as_of"])}. Each answer carries one of three labels:</p><ul>'
            + ''.join(f'<li><span class="level {esc(k)}">{esc(v)}</span></li>' for k, v in LEVEL_TEXT.items()) +
            '</ul><p>A missing answer reads “Not yet reviewed”. It never means something is prohibited. Summaries are not legal advice; the linked source is the authority.</p>',
            '<h2 id="rules">Ground rules</h2><ul><li>No paid placement, paid ranking or paid verification.</li>'
            '<li>State laws are presented side by side and factually. The site does not rank states or say which approach is better.</li>'
            '<li>Nonpartisan: every party and lawmaker is treated the same way.</li></ul>',
            progress_section(perm, score, directory, answers),
            '<h2 id="corrections">Corrections and reuse</h2>'
            f'<p>Found something wrong or out of date? <a href="{esc(correction_url("the site"))}">Send a correction</a> with a link to the source. '
            f'Everything here is free to use under CC BY 4.0, and the data and build scripts are public on <a href="{REPO}">GitHub</a>.</p>'
            '<p>Created and maintained by Travis Vought, shared in support of Veteran Home Guardians.</p>']
    return shell(f'About {SITE_NAME}', f'How {SITE_NAME} checks its information, what its labels mean, how far each state guide has been built, and how to send a correction.',
                 ''.join(body), 'about.html', 'the site', ld=[breadcrumbs([('Home', '')], 'about.html', 'About')])


# What a visitor came for, each with one place to go. Help-page needs are linked by their section.
def coverage_page(perm, medical, sources):
    """Who pays for medical cannabis, question by question, then the states that lower the card fee."""
    data, names, cites = load_coverage(), perm['jurisdictions'], Cites(sources)
    body = ['<p class="crumbs"><a href="index.html">Home</a> › <a href="medical.html">Medical cards</a> › Medicaid and insurance</p>',
            '<h1>Does Medicaid, Medicare or insurance pay for medical cannabis?</h1>',
            '<p class="lede">Short answer: patients pay for dispensary cannabis themselves. What can change is the cost of the card, '
            'and a few cannabis medicines are ordinary prescriptions. Each answer below comes from the agency’s own page.</p>',
            '<nav class="pills" aria-label="On this page">' + ''.join(f'<a class="pill" href="#{esc(i["id"])}">{esc(i["question"])}</a>' for i in data['items'])
            + '<a class="pill" href="#fee-help">Card fee help by state</a></nav>']
    for item in data['items']:
        body.append(f'<article class="card" id="{esc(item["id"])}"><h2 style="margin:.2em 0">{esc(item["question"])}</h2><p class="short">{esc(item["short"])}</p><ul>')
        for point in item['points']:
            body.append(f'<li>{esc(point["text"])}' + (f' {cites.mark([point["source"]])}' if point['source'] else '') + '</li>')
        body.append('</ul></article>')
    helped = sorted((c for c in medical if medical[c].get('fee_help')), key=lambda c: names[c])
    body.append('<h2 id="fee-help">Card fee help by state</h2><p>States that lower or waive the patient card fee for people on Medicaid or with low income, and for veterans, '
                'among the state programs reviewed so far.</p><ul class="rows">')
    for code in helped:
        f = medical[code]['fee_help']
        body.append(f'<li><a class="state" href="{slug(names[code])}.html#medical-card">{esc(names[code])}</a><span>{esc(f["text"])} {cites.mark([f["source"]])}</span></li>')
    body.append('</ul><p class="muted">A state missing from this list has not been reviewed for fee help yet, or its regulator page did not state any. '
                f'Checked {long_date(data["as_of"])}. Not medical, legal or tax advice.</p>')
    body.append('<aside class="next"><h2>Where to go next</h2><ul><li><a href="medical.html">How to get a medical card in your state</a></li>'
                '<li><a href="help.html#veterans">Veterans: VA care and state programs</a></li><li><a href="index.html#map">Pick your state</a></li></ul></aside>')
    body.append(cites.render())
    title = 'Does Medicaid, Medicare or insurance cover medical cannabis?'
    faq = {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': i['question'],
           'acceptedAnswer': {'@type': 'Answer', 'text': i['short'] + ' ' + ' '.join(p['text'] for p in i['points'] if p['source'])}} for i in data['items']]}
    return shell(title, 'Whether Medicaid, Medicare, private insurance or the VA pay for medical cannabis, which cannabis medicines are prescriptions, and which states cut the card fee.',
                 ''.join(body), 'coverage.html', 'the Medicaid and insurance page',
                 ld=[breadcrumbs([('Home', ''), ('Medical cards', 'medical.html')], 'coverage.html', 'Medicaid and insurance'), faq])


TASKS = [
    ('scale', 'Is it legal where I am?', 'Adult use and medical rules, every state', 'law-adult-use.html'),
    ('card', 'Get a medical card', 'How patients apply, in the 15 medical-only states', 'medical.html'),
    ('bag', 'Where can I buy?', 'Stores, dispensaries and who may shop', 'law-buying.html'),
    ('sprout', 'Can I grow my own?', 'Home-grow rules by state', 'law-home-grow.html'),
    ('plane', 'Traveling', 'What the TSA says about flying', 'help.html#travel'),
    ('record', 'Clear an old record', 'Sealing and expungement by state', 'law-record-relief.html'),
    ('star', 'Veterans', 'VA care and state cannabis programs', 'help.html#veterans'),
    ('heart', 'Medicaid and insurance', 'Who pays for medical cannabis, and card fee help', 'coverage.html'),
    ('megaphone', 'Speak up', 'Find your state lawmakers', 'help.html#contact-lawmakers'),
    ('briefcase', 'Cannabis business', 'Industry association and state directories', 'help.html#business'),
]


def guide_link(code, name):
    return (OHIO_HOME + '/') if code == 'OH' else slug(name) + '.html'


def home_page(perm, score, directory, answers, sources):
    names = perm['jurisdictions']
    ordered = sorted(names, key=lambda c: names[c])
    jump = ''.join(f'<option value="{slug(names[c])}.html">{esc(names[c])}</option>' for c in ordered)
    hero = ('<section class="hero"><div class="wrap"><div class="copy">'
            '<p class="eyebrow">Free · All 50 states and DC · Every answer sourced</p>'
            '<h1>Cannabis answers for your state, in plain language.</h1>'
            '<p>What’s legal, where to buy, how to clear a record and where to get help. Each answer links to the law or agency it comes from.</p>'
            '<form class="pick" id="pick"><label for="state-jump">Pick your state</label><div class="row">'
            f'<select id="state-jump" name="state"><option value="">Choose a state</option>{jump}</select><button type="submit">Go</button></div>'
            f'<p class="muted">Or tap your state on the <a href="#map">map below</a>. Checked as of {long_date(perm["as_of"])}.</p></form></div>'
            f'<div class="art"><picture><source type="image/webp" srcset="{ASSETS}logo-960.webp">'
            f'<img src="{ASSETS}logo-960.jpg" alt="{esc(LOGO_ALT)}" width="960" height="640" fetchpriority="high"></picture></div></div></section>')

    body = ['<section class="block" id="tasks"><h2>What brings you here?</h2><div class="tasks">']
    for ic, title, desc, href in TASKS:
        body.append(f'<a class="task" href="{href}" data-track="task:{slug(title)}"><span class="ic">{icon(ic)}</span><strong>{esc(title)}</strong><span class="d">{esc(desc)}</span></a>')
    linked = {href.split('#')[1] for *_, href in TASKS if '#' in href}
    more = [f'<a href="help.html#{slug(n)}">{esc(n)}</a>' for n in needs_in_order(perm) if slug(n) not in linked]
    more.append(f'<a href="{OHIO_HOME}/knowledge.html">Learn the basics</a>')
    body.append('</div><p class="also">Also: ' + ' · '.join(more) + ' · <a href="help.html">All national help</a></p></section>')

    adult = next(q for q in perm['questions'] if q['id'] == 'adult-use')
    grid, legend = tile_map(perm, adult, answers, 'Map: adult use by state. Select a state to open its guide.')
    guides = []
    for code, card in score['states'].items():
        what = ('Business directory, dispensary finder, record clearing and advocacy on OhioWeed.org' if code == 'OH'
                else f'{PACK_LABEL[card["publication_status"]]}: directory and local help, being built out')
        guides.append(f'<a class="guide" href="{guide_link(code, card["name"])}"><strong>{esc(card["name"])}</strong><span>{esc(what)}</span></a>')
    body.append('<section class="block" id="map"><h2>Where adults can use cannabis</h2>'
                '<p>Tap a state for its full guide: the law in plain language, with the source for every answer.</p>'
                f'<div class="mapbox"><div>{grid}{legend}</div><div><h3>States with a full local guide</h3>'
                '<p class="muted">Directories of businesses, dispensaries and local help. More states are added over time.</p>'
                f'<div class="guides">{"".join(guides)}</div></div></div>'
                '<details class="az"><summary>List all states A–Z</summary><ul>'
                + ''.join(f'<li><a href="{slug(names[c])}.html">{esc(names[c])}</a></li>' for c in ordered) + '</ul></details></section>')

    body.append('<section class="block" id="compare"><h2>Compare one rule across every state</h2>'
                '<p>Pick a question to see every state side by side, on a map and in a list.</p><div class="pills">')
    for q in perm['questions']:
        answered = sum(q['id'] in answers.get(c, {}) for c in names)
        body.append(f'<a class="pill" href="{law_page_name(q["id"])}">{esc(LAW_BLURB.get(q["id"], q["question"]))} <small>{answered}/{len(names)}</small></a>')
    body.append('</div><p class="muted">The number shows how many states have a reviewed answer so far. A missing answer means not yet reviewed, never that something is prohibited.</p></section>')

    body.append('<section class="block" id="family"><h2>More from the same team</h2><div class="family">')
    for url, label, host, text in FAMILY:
        body.append(f'<a class="site-card" href="{esc(url)}" data-track="family:{esc(host)}"><strong>{esc(label)}</strong><span class="u">{esc(host)}</span><p>{esc(text)}</p></a>')
    body.append('</div><p class="muted">How this site checks its information, and its ground rules: <a href="about.html">About</a>. No paid placement or ranking.</p></section>')
    body.append('<script>(function(){var f=document.getElementById("pick"),j=document.getElementById("state-jump");'
                'function go(){if(!j.value)return;if(window.directoryTrack)window.directoryTrack("state-picker");location.href=j.value}f.addEventListener("submit",function(e){e.preventDefault();go()});j.addEventListener("change",go)})();</script>')
    description = 'Free, plain-language cannabis answers for all 50 states and DC: what is legal, where to buy, record clearing and where to get help, each answer traced to a named source.'
    return shell(TAGLINE, description, ''.join(body), 'index.html', 'the home page', hero, ld=[website_node()])

def state_names(perm):
    return {slug(name) + '.html' for name in perm['jurisdictions'].values()}


def pages():
    """Every generated page as {file name: text}."""
    perm, score, directory = load()
    sources = {s['id']: s for s in perm['sources']}
    answers = answers_by_state(perm)
    med_data, medical = load_medical()
    sources.update({s['id']: s for s in med_data['sources']})
    sources.update({s['id']: s for s in load_coverage()['sources']})
    out = {'index.html': home_page(perm, score, directory, answers, sources),
           'medical.html': medical_page(perm, med_data, medical, answers, sources),
           'coverage.html': coverage_page(perm, medical, sources),
           'help.html': help_page(perm, sources),
           'about.html': about_page(perm, score, directory, answers)}
    for q in perm['questions']:
        out[law_page_name(q['id'])] = law_page(perm, q, answers, sources)
    for code, name in perm['jurisdictions'].items():
        out[slug(name) + '.html'] = state_page(perm, score, directory, code, answers, sources, medical)
    return out


def main(out_dir=None):
    out_dir = Path(out_dir or OUT_DIR)
    built = pages()
    if out_dir.exists():
        for old in out_dir.glob('*.html'):
            if old.name not in built:
                old.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in built.items():
        (out_dir / name).write_text(text, encoding='utf-8')
    print(f'Built national/: {len(built)} pages (home, help, about, medical cards, coverage, {len(built) - 56} law comparisons, 51 states)')


if __name__ == '__main__':
    main()
