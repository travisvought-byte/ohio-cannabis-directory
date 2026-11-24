"""Build the world section of the national site: a hub, one page per country and a travel
warning page (countries with harsh penalties, plus US states with no adult-use law).

Every answer, source and review date is read from data/world-permissions.json, and the US
state rows from data/state-permissions.json. Nothing here adds a claim. A missing answer
reads "Not yet reviewed".

Called by build_national.pages(); the pages land in national/ beside the state pages.
"""
import json
import re
from pathlib import Path

import build_national as nat
from permissions_page import chip

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/world-permissions.json'
HERITAGE = ROOT / 'data/world-heritage.json'
ROSTER = ROOT / 'data/world-roster.json'
NL_SHOPS = ROOT / 'data/world-coffeeshops-nl.json'
WHERE = ROOT / 'data/world-where-to-buy.json'
STARTER = ROOT / 'data/world-starter.json'
LANDING = json.loads((ROOT / 'data/landing-pages.json').read_text(encoding='utf-8'))['national_pages']

CSS = ('<style>.wcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:12px;margin:14px 0}'
       '.wcard{display:block;background:var(--card);border:1px solid var(--line);border-top:5px solid var(--green2);border-radius:12px;padding:14px 16px;text-decoration:none;color:var(--ink)}'
       '.wcard strong{display:block;font-size:1.15rem;color:var(--link)}.wcard p{margin:.4em 0 0;font-size:.95rem}'
       '.wcard.warn{border-top-color:#b4513a}.wcard:hover,.wcard:focus-visible{box-shadow:0 6px 18px rgba(23,35,30,.12)}'
       '.risk{display:inline-block;font-weight:800;font-size:.85rem;border-radius:6px;padding:1px 8px;background:#fbeaea;color:#7a0000;border:1px solid #a90000}'
       '.alert{background:#fbeaea;border-left:6px solid #b4513a;border-radius:10px;padding:10px 16px;margin:16px 0}'
       '.wcard.heritage{border-top-color:var(--gold)}.lr{display:inline-block;background:var(--mint);color:var(--green);border-radius:999px;padding:1px 10px;font-size:.85rem;font-weight:700;margin:2px 4px 2px 0}'
       '.story{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--gold);border-radius:12px;padding:6px 18px 12px;margin:14px 0}.story h2{margin-top:.5em}'
       '.lawnow{font-size:.92rem;background:var(--note);border-radius:8px;padding:4px 10px;display:inline-block}</style>')


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def answer_card(world, q, a, cites):
    if not a:
        return (f'<div class="card"><h3>{nat.esc(q["label"])}</h3><p>{chip(world, "not-reviewed")}</p></div>')
    return (f'<div class="card" id="{nat.esc(q["id"])}"><h3>{nat.esc(q["label"])}</h3>'
            f'<p>{chip(world, a["status"])} <span class="short">{nat.esc(a["short"])}</span></p>'
            f'<p>{nat.esc(a["detail"])} {cites.mark(a["source_ids"])}</p>'
            f'<p class="muted">{nat.esc(a["citation"])} · checked {nat.long_date(a["reviewed_on"])}</p></div>')


def province_table(world, cites):
    rows = []
    for p in world['canada_provinces']:
        age = (f'{nat.esc(p["age"])} {cites.mark(p["age_source_ids"])}' if p['age'] else '<span class="muted">Not yet reviewed</span>')
        grow = (f'{nat.esc(p["home_grow"])} {cites.mark(p["home_grow_source_ids"])}' if p['home_grow'] else '<span class="muted">Not yet reviewed</span>')
        retail = f'{nat.esc(p["retail"])} {cites.mark(p["retail_source_ids"])}'
        rows.append(f'<tr><th scope="row">{nat.esc(p["name"])}</th><td>{age}</td><td>{retail}</td><td>{grow}</td></tr>')
    return ('<h2 id="provinces">Province by province</h2><p>Provinces and territories set their own minimum age and home-grow rules. '
            'Ages and store models are as Health Canada lists them; growing rules come from each province. "Not yet reviewed" means that territory\'s own rule has not been checked yet; the federal limit of 4 plants is the ceiling.</p>'
            '<div class="scroll"><table><thead><tr><th scope="col">Province or territory</th><th scope="col">Minimum age</th><th scope="col">Where to buy</th><th scope="col">Growing at home</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


# The store maps (assets/place-map.js): Leaflet and its pin grouping are served from this site; only the street
# pictures come from OpenStreetMap, which the privacy page says. Rows with a map point carry data-lat and data-lon;
# the map shows them, follows the table's search, and lists the closest ones beside it. Without JavaScript the
# section stays hidden and the table, with its own "Map" link per row, is the list.
MAP_ASSETS = ('<link rel="stylesheet" href="../assets/vendor/leaflet.css"><link rel="stylesheet" href="../assets/vendor/markercluster.css">'
              '<link rel="stylesheet" href="../assets/place-map.css"><script src="../assets/vendor/leaflet.js" defer></script>'
              '<script src="../assets/vendor/leaflet.markercluster.js" defer></script><script src="../assets/place-map.js" defer></script>')


def map_section(table_id, input_id, noun, what):
    """An empty map beside the table it shows. noun is 'store,stores'; what names the places for screen readers."""
    one, many = noun.split(',')
    return (f'<section class="placemap pm-dark" data-table="{table_id}" data-input="{input_id}" data-unit="km" data-noun="{noun}" '
            f'aria-label="Map of {nat.esc(what)}" hidden>'
            f'<div class="pm-tools"><button type="button" class="pm-locate" hidden>Show {many} near me</button><span class="pm-status" role="status"></span></div>'
            f'<div class="pm-body"><div class="pm-mapcol"><div class="pm-map" role="region" aria-label="Map of {nat.esc(what)}. Pins close together are grouped; '
            f'the closest {many} are listed next to the map, and every one is in the table below."></div>'
            '<p class="pm-note">Map pictures come from OpenStreetMap, which sees your IP address and which area you look at. '
            'Your location, if you share it, is used only inside this page and is never stored or sent. <a href="privacy.html#map">Privacy</a></p></div>'
            '<div class="pm-side"><h4 class="pm-head">Closest to the middle of the map</h4><p class="pm-count"></p><ul class="pm-list"></ul></div></div></section>')


def map_attrs(lat, lon, sub):
    if lat is None or lon is None:
        return ''
    return f' data-lat="{lat}" data-lon="{lon}" data-sub="{nat.esc(sub)}"'


def load_nl_shops():
    return json.loads(NL_SHOPS.read_text(encoding='utf-8'))


NL_CSS = ('<style>.bars{list-style:none;padding:0;margin:12px 0}.bars li{display:grid;grid-template-columns:9.5em 1fr 3em;gap:8px;align-items:center;margin:4px 0;font-size:.95rem}'
          '.bars .bar{height:16px;border-radius:4px;background:var(--green2)}.bars .bar.exp{background:var(--gold)}.bars .n{font-weight:800;text-align:right}'
          '.stat{display:inline-block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px 16px;margin:4px 8px 4px 0}.stat b{display:block;font-size:1.6rem;color:var(--green)}'
          '.filter{width:100%;max-width:420px;padding:8px 10px;font-size:1rem;border:1px solid var(--line);border-radius:8px;margin:6px 0 10px}'
          '.tag{display:inline-block;font-size:.8rem;font-weight:700;border-radius:999px;padding:0 8px;background:var(--note)}'
          'td.num{text-align:right}</style>')


def coffeeshop_section(cs, cites):
    """Netherlands only: the official count for every town and Amsterdam's permit register shop by shop."""
    nat_count = cs['national']
    towns = cs['towns']
    shops = cs['amsterdam']['shops']
    granted = [s for s in shops if s['permit'] == 'granted']
    other = [s for s in shops if s['permit'] != 'granted']
    ams = next(t['count_2024'] for t in towns if t['name'] == 'Amsterdam')
    exp_n = sum(t['count_2024'] for t in towns if t['experiment'])
    out = [NL_CSS, '<h2 id="coffeeshops">Coffeeshops: where they are</h2>',
           f'<p>At the end of 2024 the Netherlands had <strong>{nat_count["coffeeshops"]} tolerated coffeeshops</strong> in {nat_count["towns_with_policy"]} of its '
           f'{nat_count["municipalities"]} municipalities. Most towns allow none. Amsterdam alone had {ams}, about {round(ams * 10 / nat_count["coffeeshops"])} in every 10. '
           f'{cites.mark(nat_count["source_ids"])}</p>',
           f'<p><span class="stat"><b>{nat_count["coffeeshops"]}</b>coffeeshops</span><span class="stat"><b>{nat_count["towns_with_policy"]}</b>towns that allow them</span>'
           f'<span class="stat"><b>{len(shops)}</b>Amsterdam shops listed below</span></p>',
           '<div class="pills"><a class="pill" href="#amsterdam-shops">Amsterdam, shop by shop</a><a class="pill" href="#every-town">Every town and its count</a>'
           '<a class="pill" href="#experiment-towns">Towns selling state-grown cannabis</a></div>']
    top = sorted(towns, key=lambda t: (-t['count_2024'], t['name']))[:15]
    peak = top[0]['count_2024']
    bars = ''.join(f'<li><span>{nat.esc(t["name"])}</span><span class="bar{" exp" if t["experiment"] else ""}" style="width:{max(2, round(100 * t["count_2024"] / peak))}%"></span>'
                   f'<span class="n">{t["count_2024"]}</span></li>' for t in top)
    out.append(f'<h3>The 15 towns with the most coffeeshops</h3><ul class="bars" aria-label="Coffeeshops per town, end of 2024">{bars}</ul>'
               f'<p class="muted">Gold bars are towns in the legal-supply experiment. Counts on December 31, 2024. {cites.mark(cs["towns_source_ids"])}</p>')

    def row(s):
        until = nat.long_date(s['permit_until']) if s['permit_until'] else '<span class="muted">Not stated</span>'
        where = (f'<a href="https://www.openstreetmap.org/?mlat={s["lat"]}&amp;mlon={s["lon"]}#map=18/{s["lat"]}/{s["lon"]}" target="_blank" rel="noopener">Map</a>'
                 if s['lat'] is not None else '<span class="muted">No map point</span>')
        return (f'<tr{map_attrs(s["lat"], s["lon"], ", ".join(x for x in (s["address"], s["postcode"]) if x))}><th scope="row">{nat.esc(s["name"])}</th><td>{nat.esc(s["address"])}</td><td>{nat.esc(s["postcode"])}</td>'
                f'<td>{until}</td><td>{where}</td></tr>')

    head = '<thead><tr><th scope="col">Name in the city register</th><th scope="col">Address</th><th scope="col">Postcode</th><th scope="col">Permit runs to</th><th scope="col">Where</th></tr></thead>'
    out.append(f'<h3 id="amsterdam-shops">Amsterdam coffeeshops, shop by shop</h3>'
               f'<p>Every business the City of Amsterdam lists as a coffeeshop in its open operating-permit register: {len(granted)} with a granted permit, and '
               f'{len(other)} more listed without a permit status. Names are as the city records them, which is sometimes the company name rather than the sign over the door. '
               f'Sorted by postcode, so shops near each other sit together. '
               f'{cites.mark(cs["amsterdam"]["source_ids"])}</p>'
               f'<p class="muted">The register is the city\'s permit list, not a guide to opening hours, menus or whether a shop admits visitors. '
               f'Its total differs from the national count above because the two are kept for different purposes and on different dates. Downloaded {nat.long_date(cs["amsterdam"]["retrieved_on"])}.</p>'
               '<label for="cs-filter"><strong>Find a shop</strong> by name, street or postcode</label><br>'
               '<input id="cs-filter" class="filter" type="search" placeholder="e.g. Bulldog, Haarlemmerstraat, 1012" autocomplete="off">'
               f'<p class="muted" id="cs-count" aria-live="polite">{len(granted)} shops with a granted permit</p>'
               + MAP_ASSETS + map_section('cs-table', 'cs-filter', 'coffeeshop,coffeeshops', 'Amsterdam coffeeshops with a granted permit') +
               f'<div class="scroll"><table id="cs-table">{head}<tbody>{"".join(row(s) for s in granted)}</tbody></table></div>'
               f'<details class="az"><summary>Listed without a permit status ({len(other)})</summary><p class="muted">These records name the business as a coffeeshop but leave the permit status blank, and the register does not say why.</p>'
               f'<div class="scroll"><table>{head}<tbody>{"".join(row(s) for s in other)}</tbody></table></div></details>'
               '<script>(function(){var i=document.getElementById("cs-filter"),t=document.getElementById("cs-table"),c=document.getElementById("cs-count");if(!i||!t)return;'
               'var rows=t.tBodies[0].rows;i.addEventListener("input",function(){var q=i.value.trim().toLowerCase(),n=0;for(var k=0;k<rows.length;k++){var hit=!q||rows[k].textContent.toLowerCase().indexOf(q)>-1;'
               'rows[k].hidden=!hit;if(hit)n++}c.textContent=q?n+" of "+rows.length+" shops match":rows.length+" shops with a granted permit"})})();</script>')

    exp = [t for t in towns if t['experiment']]
    out.append(f'<h3 id="experiment-towns">Towns selling state-grown cannabis</h3>'
               f'<p>In these {len(exp)} towns every coffeeshop takes part in the legal-supply experiment, so what is on the menu comes from government-designated growers. '
               f'Together they had {exp_n} coffeeshops at the end of 2024. {cites.mark(cs["experiment_source_ids"] + ["nl-gov-exp"] + cs["towns_source_ids"])}</p>'
               '<div class="pills">' + ''.join(f'<span class="pill">{nat.esc(t["name"])} ({t["count_2024"]})</span>' for t in sorted(exp, key=lambda t: t['name'])) + '</div>')

    rows = ''.join(f'<tr><th scope="row">{nat.esc(t["name"])}</th><td class="num">{t["count_2024"]}</td>'
                   f'<td>{"<span class=tag>Yes</span>" if t["experiment"] else ""}</td></tr>' for t in sorted(towns, key=lambda t: t['name']))
    out.append(f'<h3 id="every-town">Every town that allows coffeeshops</h3>'
               f'<p>The official count for each of the {len(towns)} towns, December 31, 2024. So far this page lists shops one by one only for Amsterdam, from the city\'s open data; '
               f'for any other town, its own website or town hall is the place to check. {cites.mark(cs["towns_source_ids"])}</p>'
               f'<details class="az" open><summary>All {len(towns)} towns, A to Z</summary><div class="scroll"><table><thead><tr><th scope="col">Town (municipality)</th>'
               f'<th scope="col">Coffeeshops</th><th scope="col">Experiment</th></tr></thead><tbody>{rows}</tbody></table></div></details>')
    return ''.join(out)


def load_where():
    return json.loads(WHERE.read_text(encoding='utf-8'))


FILTER_JS = ('<script>(function(){document.querySelectorAll("input[data-filter]").forEach(function(i){var t=document.getElementById(i.getAttribute("data-filter"));'
             'var c=document.getElementById(i.getAttribute("data-filter")+"-count");if(!t)return;var rows=t.tBodies[0].rows;i.addEventListener("input",function(){'
             'var q=i.value.trim().toLowerCase(),n=0;for(var k=0;k<rows.length;k++){var hit=!q||rows[k].textContent.toLowerCase().indexOf(q)>-1;rows[k].hidden=!hit;if(hit)n++}'
             'if(c)c.textContent=q?n+" of "+rows.length+" match":rows.length+" listed"})})})();</script>')


def _cell(key, r):
    v = r.get(key)
    if key == 'map':
        if r.get('lat') is None:
            return '<span class="muted">No map point</span>'
        return (f'<a href="https://www.openstreetmap.org/?mlat={r["lat"]}&amp;mlon={r["lon"]}#map=18/{r["lat"]}/{r["lon"]}" target="_blank" rel="noopener">Map</a>')
    if not v:
        return ''
    if key in ('website',):
        url = v if v.startswith('http') else 'https://' + v
        label = re.sub(r'^https?://(www\.)?', '', v).rstrip('/')
        return f'<a href="{nat.esc(url)}" target="_blank" rel="noopener nofollow">{nat.esc(label)}</a>'
    if key == 'email':
        return f'<a href="mailto:{nat.esc(v)}">{nat.esc(v)}</a>'
    if key == 'phone':
        return f'<a href="tel:{nat.esc(re.sub(r"[^0-9+]", "", v))}">{nat.esc(v)}</a>'
    return nat.esc(v)


def wtb_table(t, cites, searchable):
    head = ''.join(f'<th scope="col">{nat.esc(label)}</th>' for _, label in t['columns'])
    mapped = any(r.get('lat') is not None for r in t['rows'])
    rows = ''.join('<tr' + (map_attrs(r.get('lat'), r.get('lon'), ', '.join(r[k] for k in ('address', 'city') if r.get(k))) if mapped else '') + '>' + ''.join((f'<th scope="row">{_cell(k, r)}</th>' if n == 0 else f'<td>{_cell(k, r)}</td>') for n, (k, _) in enumerate(t['columns'])) + '</tr>'
                   for r in t['rows'])
    tid = 'wtb-' + t['id']
    search = (f'<label for="{tid}-q"><strong>Search</strong> by name, street or town</label><br><input id="{tid}-q" class="filter" type="search" data-filter="{tid}" autocomplete="off">'
              f'<p class="muted" id="{tid}-count" aria-live="polite">{len(t["rows"])} listed</p>') if searchable and len(t['rows']) > 15 else ''
    note = f'<p class="muted">{nat.esc(t["note"])}</p>' if t.get('note') else ''
    place = MAP_ASSETS + map_section(tid, f'{tid}-q', 'store,stores', t['caption']) if mapped and search else ''
    return (f'<h3 id="{nat.esc(t["id"])}">{nat.esc(t["caption"])}</h3>{note}<p class="muted">Source: {cites.mark(t["source_ids"])}</p>{search}{place}'
            f'<div class="scroll"><table id="{tid}"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>')


def where_section(entry, cites, page_link=False):
    out = [NL_CSS, f'<h2 id="where-to-buy">{nat.esc(entry["heading"])}</h2>', f'<p>{nat.esc(entry["intro"])} {cites.mark(entry["source_ids"])}</p>']
    for link in entry.get('links', []):
        out.append(f'<p class="lawnow"><a href="{nat.esc(link["url"])}" target="_blank" rel="noopener">{nat.esc(link["label"])}</a> {cites.mark(link["source_ids"])}</p>')
    if entry.get('gap'):
        out.append(f'<p class="muted">{nat.esc(entry["gap"])}</p>')
    if page_link:
        items = ''.join(f'<li><a href="{nat.esc(entry["page"])}#{nat.esc(t["id"])}">{nat.esc(t["caption"])}</a></li>' for t in entry['tables'])
        out.append(f'<p><a class="pill" href="{nat.esc(entry["page"])}"><strong>See every store, province by province</strong></a></p><ul>{items}</ul>')
    else:
        out.extend(wtb_table(t, cites, True) for t in entry['tables'])
        if any(len(t['rows']) > 15 for t in entry['tables']):
            out.append(FILTER_JS)
    return ''.join(out)


def stores_page(world, sources, code, entry):
    c = world['countries'][code]
    cites = nat.Cites(sources)
    pills = ''.join(f'<a class="pill" href="#{nat.esc(t["id"])}">{nat.esc(t["caption"].split(":")[0])}</a>' for t in entry['tables'])
    body = [CSS, NL_CSS, f'<p class="crumbs"><a href="index.html">Home</a> › <a href="world.html">Around the world</a> › <a href="{nat.esc(c["page"])}">{nat.esc(c["name"])}</a> › Stores</p>',
            f'<h1>{nat.esc(entry["page_title"])}</h1>', f'<p class="lede">{nat.esc(entry["page_intro"])}</p>', f'<div class="pills">{pills}</div>',
            '<h2 id="by-region">' + ('Stores by province' if code == 'CA' else 'Stores by region') + '</h2>']
    body.extend(wtb_table(t, cites, True) for t in entry['tables'])
    body.append(FILTER_JS)
    body.append(f'<p class="muted">Copied from each regulator\'s list on {nat.long_date(world_where_as_of())}. Not legal advice.</p>')
    body.append(cites.render())
    ld = [nat.breadcrumbs([('Home', ''), ('Around the world', 'world.html'), (c['name'], c['page'])], entry['page'], 'Stores')]
    return nat.shell(entry['page_title'], entry['page_intro'][:300], ''.join(body), entry['page'], entry['page_title'], ld=ld)


def world_where_as_of():
    return load_where()['as_of']


def load_starter():
    return json.loads(STARTER.read_text(encoding='utf-8'))


# Names that read with "the" in a sentence ("traveling to the Netherlands").
THE_NAMES = {'Netherlands', 'Bahamas', 'Philippines', 'Maldives', 'Comoros', 'Seychelles', 'United Kingdom', 'United Arab Emirates',
             'Dominican Republic', 'Central African Republic', 'Federated States of Micronesia'}


def in_sentence(name):
    return f'the {name}' if name in THE_NAMES or name.endswith('Islands') else name


def first_sentence(text):
    m = re.match(r'(.+?[.!?])(\s|$)', text.strip())
    return m.group(1) if m else text.strip()


def country_intro(c, where, code):
    """The opening for a country page, written to a traveler (or someone who lives there), from the
    country's own cited short answers, each linked to its full answer and source below."""
    a = c['answers']
    link = lambda q: f'<a href="#{q}">{nat.esc(a[q]["short"].rstrip("."))}</a>' if q in a else ''
    facts = [f'{label}: {link(q)}' for label, q in (('Adults', 'adult-use'), ('Buying', 'buying'), ('Carrying', 'possession'), ('At the border', 'border')) if link(q)]
    first = f'Planning a trip to {nat.esc(in_sentence(c["name"]))}, or live there? ' + (' · '.join(facts) + '.' if facts else 'Here is what is known so far, each answer with its source.')
    if code == 'NL':
        second = 'The <a href="#coffeeshops">coffeeshop list</a>, town by town, is further down.'
    elif where:
        # The section's own heading ("Where to join: licensed clubs"), so a club-only country never reads as having shops.
        head, _, what = where['heading'].partition(': ')
        second = f'{nat.esc(head)}' + (f' ({nat.esc(what)})' if what else '') + ' is <a href="#where-to-buy">just below</a>.'
    else:
        second = ''
    return f'{first} {second}'.strip()


def starter_page(world, sources, code, st, licence):
    """A country without a full guide yet: the UK government's drugs advice, credited, and the core questions marked not reviewed."""
    cites = nat.Cites(sources)
    name = st['name']
    lead = first_sentence(st['sections'][0]['paragraphs'][0])
    body = [CSS, f'<p class="crumbs"><a href="index.html">Home</a> › <a href="world.html">Around the world</a> › {nat.esc(name)}</p>',
            f'<h1>Cannabis laws in {nat.esc(in_sentence(name))}</h1>',
            nat.for_you(f'Traveling to {nat.esc(in_sentence(name))}? Before you pack, here is how the UK government sums up drugs there: '
                        f'“{nat.esc(lead)}” {cites.mark([st["source_id"]])}'),
            f'<p>This is a starter page. We have not reviewed the cannabis law in {nat.esc(in_sentence(name))} in full yet, so the answers below are marked "Not yet reviewed". '
            'Until we do, here is what the UK government tells travellers about drugs there, in its own words.</p>',
            '<p class="alert"><strong>Travelling?</strong> Never carry cannabis across an international border, even between two places where it is legal. '
            '<a href="travel-warnings.html">See where it can land you in prison</a>.</p>',
            f'<div class="story"><h2 id="travel-advice">What the UK government tells travellers about drugs</h2>']
    for sec in st['sections']:
        if sec['heading']:
            body.append(f'<h3>{nat.esc(sec["heading"])}</h3>')
        body.append(''.join(f'<p>{nat.esc(p)}</p>' for p in sec['paragraphs']))
    body.append(f'<p class="muted">{nat.esc(st["fcdo_title"])} travel advice, last updated by the FCDO on {nat.long_date(st["updated"])}. {cites.mark([st["source_id"]])} '
                f'{nat.esc(licence)}</p></div>')
    for q in world['questions']:
        if q['id'] in ('adult-use', 'medical', 'possession', 'home-grow'):
            body.append(answer_card(world, q, None, cites))
    body.append('<p class="muted">A full guide for this country is on our list. Know the law here, or spot something out of date? Use "Fix or reuse" below.</p>')
    body.append(cites.render())
    title = f'Cannabis laws in {in_sentence(name)}'
    desc = f'Traveling to {in_sentence(name)}? {lead} What the UK government tells visitors about drugs there, credited and dated.'
    if len(desc) > 300:
        desc = f'Traveling to {in_sentence(name)}? What the UK government tells visitors about drugs and cannabis there, credited and dated.'
    ld = [nat.breadcrumbs([('Home', ''), ('Around the world', 'world.html')], st['page'], name)]
    return nat.shell(title, desc, ''.join(body), st['page'], name, ld=ld)


def country_page(world, sources, code):
    c = world['countries'][code]
    cites = nat.Cites(sources)
    body = [CSS, f'<p class="crumbs"><a href="index.html">Home</a> › <a href="world.html">Around the world</a> › {nat.esc(c["name"])}</p>',
            f'<h1>Cannabis laws in {nat.esc(in_sentence(c["name"]))}</h1>', nat.for_you(country_intro(c, load_where()['countries'].get(code), code)),
            f'<p>{nat.esc(c["summary"])}</p>']
    if c.get('note'):
        body.append(f'<p class="muted">{nat.esc(c["note"])}</p>')
    if c.get('differences'):
        d = c['differences']
        pts = ''.join(f'<li>{nat.esc(x)}</li>' for x in d['points'])
        body.append(f'<div class="story"><h2>{nat.esc(d["title"])}</h2><ul>{pts}</ul><p>{cites.mark(d["source_ids"])}</p></div>')
    if code == 'NL':
        body.append('<p class="lawnow"><a href="#coffeeshops">Jump to the coffeeshop list: every town, and Amsterdam shop by shop</a></p>')
    body.append('<p class="alert"><strong>Travelling?</strong> Never carry cannabis across an international border, even between two places where it is legal. '
                '<a href="travel-warnings.html">See where it can land you in prison</a>.</p>')
    where = load_where()['countries'].get(code)
    if where:
        body.append(where_section(where, cites, page_link=bool(where.get('page'))))
    # The answer cards are h3s; they sit under their own h2 so headings never skip a level (WCAG 1.3.1).
    body.append(f'<h2 id="the-law">The law in {nat.esc(in_sentence(c["name"]))}</h2>')
    for q in world['questions']:
        a = c['answers'].get(q['id'])
        if a or q['id'] in ('adult-use', 'medical', 'possession', 'home-grow'):
            body.append(answer_card(world, q, a, cites))
    if code == 'CA':
        body.append(province_table(world, cites))
    if code == 'NL':
        body.append(coffeeshop_section(load_nl_shops(), cites))
    if c.get('experiment'):
        e = c['experiment']
        body.append(f'<h2 id="context">Good to know</h2><p>{nat.esc(e["text"])} {cites.mark(e["source_ids"])}</p>')
    region = next((r for r in load_heritage()['regions'] if r.get('country_page') == c['page']), None)
    if region:
        body.append(f'<p class="lawnow">Heritage: <a href="heritage.html#{nat.esc(region["id"])}">where {nat.esc(region["place"])} fits in cannabis history</a></p>')
    body.append('<p class="muted">Summaries of the cited sources, each with the date it was checked. Not legal advice.</p>')
    body.append(cites.render())
    title = f'Cannabis laws in {in_sentence(c["name"])}'
    desc = f'Visiting {in_sentence(c["name"])}? {c["summary"]} Sourced, plain-English answers, checked {nat.long_date(world["as_of"])}.'
    ld = [nat.breadcrumbs([('Home', ''), ('Around the world', 'world.html')], c['page'], c['name'])]
    return nat.shell(title, desc[:300], ''.join(body), c['page'], c['name'], ld=ld)


def country_card(world, c):
    a = c['answers'].get('adult-use')
    status = chip(world, a['status']) + ' ' + nat.esc(a['short']) if a else chip(world, 'not-reviewed')
    return f'<a class="wcard" href="{nat.esc(c["page"])}"><strong>{nat.esc(c["name"])}</strong><p>{status}</p><p>{nat.esc(c["summary"])}</p></a>'


def hub_page(world, sources):
    groups = []
    for g in world['groups']:
        cards = ''.join(country_card(world, world['countries'][code]) for code in g['codes'])
        groups.append(f'<h2 id="{nat.esc(g["id"])}">{nat.esc(g["label"])}</h2><div class="wcards">{cards}</div>')
    extra = ('<div class="wcards"><a class="wcard heritage" href="learn.html"><strong>Cannabis 101</strong>'
             '<p>THC, CBD, terpenes, product forms, hash and rosin, reading a label, and safer use.</p></a>'
             '<a class="wcard heritage" href="heritage.html"><strong>Where weed comes from</strong>'
             '<p>The landraces, the places they grew and the people who kept the tradition: India, the Hindu Kush, the Rif, the Bekaa, southern Africa, Jamaica, Thailand, Mexico and Colombia.</p></a>'
             '<a class="wcard warn" href="travel-warnings.html"><strong>Where weed can put you in prison</strong>'
             '<p>Countries with death-penalty or long-prison drug laws, and the strictest US states.</p></a></div>')
    roster = json.loads(ROSTER.read_text(encoding='utf-8'))
    blocks = []
    for st, label in roster['statuses'].items():
        rows = [r for r in roster['countries'] if r['status'] == st]
        if st == 'queued':
            rows.sort(key=lambda r: r['queue'])
        items = ''.join((f'<li><a href="{nat.esc(r["page"])}">{nat.esc(r["display"])}</a></li>' if r['page'] else f'<li>{nat.esc(r["display"])}</li>') for r in rows)
        blocks.append(f'<details class="az"{" open" if st in ("deep", "basic", "queued") else ""}><summary>{nat.esc(label)} ({len(rows)})</summary>'
                      f'<{"ol" if st == "queued" else "ul"}>{items}</{"ol" if st == "queued" else "ul"}></details>')
    roster_html = ('<h2 id="every-country">Every country, and how far we have got</h2>'
                   f'<p>All {len(roster["countries"])} countries and territories. We go one country at a time, in the order below. '
                   'This shows our coverage, not whether cannabis is legal there.</p>' + ''.join(blocks))
    body = (CSS + '<p class="crumbs"><a href="index.html">Home</a> › Around the world</p><h1>Cannabis laws around the world</h1>'
            + nat.for_you(nat.esc(LANDING['world.html']['intro'])) +
            '<p>The same plain answers as the state pages, for other countries, plus the history of where cannabis comes from. Every answer names its source and the date it was checked.</p>'
            + extra + ''.join(groups) + roster_html +
            '<p class="muted">Not legal advice. Laws change; check the cited source before you act on anything here.</p>')
    return nat.shell('Cannabis laws around the world', 'Cannabis laws country by country: Canada, Uruguay, Germany, the Netherlands, Mexico, Thailand and the UK, plus where weed comes from and where it can mean prison. Sourced and dated.',
                     body, 'world.html', 'world', ld=[nat.breadcrumbs([('Home', '')], 'world.html', 'Around the world')])


def us_rows(perm, cites, status):
    """States whose reviewed adult-use answer has this status, alphabetically."""
    by_state = nat.answers_by_state(perm)
    rows = []
    for code, name in sorted(perm['jurisdictions'].items(), key=lambda kv: kv[1]):
        a = by_state.get(code, {})
        adult = a.get('adult-use')
        if not adult or adult['status'] != status:
            continue
        med = a.get('medical')
        med_text = (chip(perm, med['status']) + ' ' + nat.esc(med['short'])) if med else chip(perm, 'not-reviewed')
        rows.append(f'<li><span class="state"><a href="{nat.esc(nat.slug(name))}.html">{nat.esc(name)}</a></span>'
                    f'<span>{nat.esc(adult["detail"])} {cites.mark(adult["source_ids"])}</span>'
                    f'<p class="meta">Medical: {med_text} · checked {nat.long_date(adult["reviewed_on"])}</p></li>')
    return rows


def warnings_page(world, perm, sources):
    cites = nat.Cites(sources)
    cards = []
    for w in world['travel_warnings']:
        cards.append(f'<div class="card"><h3>{nat.esc(w["place"])} <span class="risk">{nat.esc(w["risk"])}</span></h3>'
                     f'<p>{nat.esc(w["detail"])} {cites.mark(w["source_ids"])}</p><p class="muted">Checked {nat.long_date(w["reviewed_on"])}</p></div>')
    tx = world['texas_concentrates']
    rows = us_rows(perm, cites, 'not-permitted')
    med_rows = us_rows(perm, cites, 'medical-only')
    body = (CSS + '<p class="crumbs"><a href="index.html">Home</a> › <a href="world.html">Around the world</a> › Travel warnings</p>'
            '<h1>Where weed can put you in prison</h1>'
            + nat.for_you(nat.esc(LANDING['travel-warnings.html']['intro'])) +
            '<p class="alert"><strong>The short version:</strong> don\'t fly with it, don\'t cross a border with it, and check whether a country tests travellers before you go. '
            'That includes CBD and vape cartridges.</p>'
            '<h2 id="countries">Countries with the harshest penalties</h2>' + ''.join(cards) +
            '<h2 id="us-states">The strictest US states</h2>'
            f'<p>These {len(rows)} states have no adult-use law and no full medical program, and some penalties reach felony level. '
            'Each answer comes from the state page and links to its source.</p>'
            f'<div class="alert"><strong>Texas: vapes and edibles are felonies.</strong> {nat.esc(tx["text"])} {cites.mark(tx["source_ids"])}'
            f'<br><span class="muted">{nat.esc(tx["citation"])}</span></div>'
            f'<ul class="rows">{"".join(rows)}</ul>'
            '<h2 id="medical-only-states">Medical card only</h2>'
            f'<p>In these {len(med_rows)} states, cannabis is legal only for registered patients. Without a card, the state\'s criminal penalties apply.</p>'
            f'<ul class="rows">{"".join(med_rows)}</ul>'
            '<p class="muted">Summaries of the cited sources, each with the date it was checked. Not legal advice.</p>' + cites.render())
    return nat.shell('Where weed can put you in prison', 'Countries where cannabis can mean the death penalty or years in prison, and the strictest US states, including Texas. Sourced and dated.',
                     body, 'travel-warnings.html', 'travel warnings',
                     ld=[nat.breadcrumbs([('Home', ''), ('Around the world', 'world.html')], 'travel-warnings.html', 'Travel warnings')])


def load_heritage():
    return json.loads(HERITAGE.read_text(encoding='utf-8'))


def hash_section(her, cites):
    h = her['hash']
    items = ''.join(f'<div class="card"><h3>{nat.esc(m["name"])}</h3><p class="muted">{nat.esc(m["where"])}</p>'
                    f'<p>{nat.esc(m["text"])} {cites.mark(m["source_ids"])}</p></div>' for m in h['methods'])
    return (f'<h2 id="hash">{nat.esc(h["title"])}</h2><p>{nat.esc(h["intro"])}</p>{items}'
            '<p class="muted">Modern solventless forms such as ice-water hash and rosin are explained in <a href="learn.html#processing">Cannabis 101</a>.</p>')


KNOWLEDGE = ROOT / 'data/knowledge.json'
LEARN_SKIP = {'hemp'}  # Ohio-specific rules stay on the Ohio guide


def learn_page():
    """Cannabis 101 for the national site, read from the directory's reviewed knowledge records."""
    k = json.loads(KNOWLEDGE.read_text(encoding='utf-8'))
    srcs = {s['id']: s for s in k['sources']}
    order = []

    def mark(ids):
        out = []
        for sid in ids:
            if sid not in order:
                order.append(sid)
            n = order.index(sid) + 1
            out.append(f'<a href="#ksource-{n}" aria-label="Source {n}">[{n}]</a>')
        return '<span class="cites">' + ''.join(out) + '</span>'

    secs = [s for s in k['sections'] if s['id'] not in LEARN_SKIP]
    nav = ' · '.join(f'<a href="#{nat.esc(s["id"])}">{nat.esc(s["title"])}</a>' for s in secs)
    body = [CSS, '<p class="crumbs"><a href="index.html">Home</a> › Cannabis 101</p><h1>Cannabis 101</h1>', nat.for_you(nat.esc(LANDING['learn.html']['intro'])),
            '<p>Plain-language explanations of cannabis words, product forms, processing, labels and safer use. '
            f'Reviewed {nat.long_date(k["reviewed_on"])}. For product literacy, not a personal treatment or dosing plan.</p>',
            f'<p class="onpage">{nav}</p>']
    for s in secs:
        body.append(f'<h2 id="{nat.esc(s["id"])}">{nat.esc(s["title"])}</h2>')
        if s.get('lead'):
            body.append(f'<p>{nat.esc(s["lead"])}</p>')
        for it in s['items']:
            body.append(f'<div class="card" id="{nat.esc(s["id"])}-{nat.esc(it["id"])}"><h3>{nat.esc(it["title"])}</h3>'
                        f'<p>{nat.esc(it["text"])} {mark(it.get("sources", []))}</p></div>')
    body.append('<p>More: <a href="heritage.html">where weed comes from</a> · <a href="world.html">laws around the world</a> · '
                '<a href="https://ohioweed.org/knowledge.html">the Ohio guide, with Ohio\'s hemp rules</a></p>')
    body.append('<h2 id="sources">Sources</h2><ol class="sources">' + ''.join(
        f'<li id="ksource-{n}"><a href="{nat.esc(srcs[sid]["url"])}" target="_blank" rel="noopener">{nat.esc(srcs[sid]["title"])}</a></li>'
        for n, sid in enumerate(order, 1)) + '</ol>')
    return nat.shell('Cannabis 101: words, products, labels and safer use',
                     'THC, CBD, terpenes, flower, edibles, vapes, kief, hash, rosin, lab reports and safer use, explained in plain language with sources.',
                     ''.join(body), 'learn.html', 'Cannabis 101',
                     ld=[nat.breadcrumbs([('Home', '')], 'learn.html', 'Cannabis 101')])


def heritage_page(her, sources):
    cites = nat.Cites(sources)
    o, l = her['origin'], her['landrace']
    cards = []
    for r in her['regions']:
        lrs = ''.join(f'<span class="lr">{nat.esc(x)}</span>' for x in r['landraces'])
        law = f'<p class="lawnow">Law today: {nat.esc(r["law_now"])}</p>' if r.get('law_now') else ''
        more = f' <a href="{nat.esc(r["country_page"])}">Full law page</a>' if r.get('country_page') else ''
        cards.append(f'<div class="card" id="{nat.esc(r["id"])}"><h3>{nat.esc(r["place"])}</h3>'
                     f'<p><strong>People and traditions:</strong> {nat.esc(r["peoples"])}</p><p>{lrs}</p>'
                     f'<p>{nat.esc(r["story"])} {cites.mark(r["source_ids"])}</p>{law}{more}</div>')
    jump = ' · '.join(f'<a href="#{nat.esc(r["id"])}">{nat.esc(r["place"])}</a>' for r in her['regions'])
    body = (CSS + '<p class="crumbs"><a href="index.html">Home</a> › <a href="world.html">Around the world</a> › Where weed comes from</p>'
            '<h1>Where weed comes from</h1>'
            + nat.for_you(nat.esc(LANDING['heritage.html']['intro'])) +
            f'<div class="story"><h2>{nat.esc(o["title"])}</h2><p>{nat.esc(o["text"])} {cites.mark(o["source_ids"])}</p></div>'
            f'<div class="story"><h2>{nat.esc(l["title"])}</h2><p>{nat.esc(l["text"])} {cites.mark(l["source_ids"])}</p></div>'
            f'<p class="onpage">{jump} · <a href="#hash">Hash traditions</a></p>' + ''.join(cards) + hash_section(her, cites) +
            '<p class="muted">History drawn from the cited research, government records and reporting. Strain names are traditional market names, not verified genetics.</p>' + cites.render())
    return nat.shell('Where weed comes from: landraces and the people behind them',
                     'The origin of cannabis, the classic landraces (Afghani, Hindu Kush, Thai, Durban Poison, Acapulco Gold, Colombian Gold, beldiya) and the peoples who kept the tradition. Sourced.',
                     body, 'heritage.html', 'the heritage page',
                     ld=[nat.breadcrumbs([('Home', ''), ('Around the world', 'world.html')], 'heritage.html', 'Where weed comes from')])


def announcement():
    """Site-wide news banner for the world launch. Counts come from the data, so they stay true as countries are added."""
    world = load()
    n = len(world['countries'])
    full = [c['name'] for c in world['countries'].values() if c.get('differences')]
    charted = (f'{" and ".join(full)} charted in full' if len(full) <= 2
               else f'{len(full)} of them charted in full')
    return ('<aside class="ahoy" aria-label="Announcement"><div class="wrap"><p>'
            '<span class="flag" aria-hidden="true">🏴‍☠️</span> <strong>Ahoy! The Reefer has set sail.</strong> '
            f'We crossed the seven seas and hauled back the cannabis laws of {n} countries, '
            f'{charted}, and more ports on the map. '
            'We dug up where the old landraces were buried, and marked the waters where weed can land ye in the brig. '
            '<a href="world.html">Board the ship →</a></p></div></aside>')


def home_block():
    """The home page's way into the world section: every country, grouped, plus history and travel warnings."""
    world = load()
    groups = []
    for g in world['groups']:
        links = ' · '.join(f'<a href="{nat.esc(world["countries"][c]["page"])}">{nat.esc(world["countries"][c]["name"])}</a>' for c in g['codes'])
        groups.append(f'<p><strong>{nat.esc(g["label"])}:</strong> {links}</p>')
    return ('<section class="block" id="world"><h2>Around the world</h2>'
            '<p>Same plain answers for other countries, the history of where weed comes from, and where it can land you in prison.</p>'
            + ''.join(groups) +
            '<div class="pills"><a class="pill" href="world.html">All countries</a><a class="pill" href="heritage.html">Where weed comes from</a>'
            '<a class="pill" href="travel-warnings.html">Where weed can put you in prison</a><a class="pill" href="learn.html">Cannabis 101</a></div></section>')


def pages(perm, base_sources):
    world = load()
    sources = dict(base_sources)
    sources.update({s['id']: s for s in world['sources']})
    her = load_heritage()
    sources.update({s['id']: s for s in her['sources']})
    sources.update({s['id']: s for s in load_nl_shops()['sources']})
    sources.update({s['id']: s for s in load_where()['sources']})
    starter = load_starter()
    sources.update({s['id']: s for s in starter['sources']})
    out = {'world.html': hub_page(world, sources), 'travel-warnings.html': warnings_page(world, perm, sources),
           'heritage.html': heritage_page(her, sources), 'learn.html': learn_page()}
    for code, c in world['countries'].items():
        out[c['page']] = country_page(world, sources, code)
    for code, st in starter['countries'].items():
        out[st['page']] = starter_page(world, sources, code, st, starter['licence'])
    for code, entry in load_where()['countries'].items():
        if entry.get('page'):
            out[entry['page']] = stores_page(world, sources, code, entry)
    return out
