"""Build the world section of the national site: a hub, one page per country and a travel
warning page (countries with harsh penalties, plus US states with no adult-use law).

Every answer, source and review date is read from data/world-permissions.json, and the US
state rows from data/state-permissions.json. Nothing here adds a claim. A missing answer
reads "Not yet reviewed".

Called by build_national.pages(); the pages land in national/ beside the state pages.
"""
import json
from pathlib import Path

import build_national as nat
from permissions_page import chip

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/world-permissions.json'
HERITAGE = ROOT / 'data/world-heritage.json'

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
        rows.append(f'<tr><th scope="row">{nat.esc(p["name"])}</th><td>{age}</td><td>{grow}</td></tr>')
    return ('<h2 id="provinces">Province by province</h2><p>Provinces and territories set their own minimum age and home-grow rules. '
            'Rows marked "Not yet reviewed" have not been checked against that province\'s own site yet; the federal rules above still apply there.</p>'
            '<div class="scroll"><table><thead><tr><th scope="col">Province or territory</th><th scope="col">Minimum age</th><th scope="col">Growing at home</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def country_page(world, sources, code):
    c = world['countries'][code]
    cites = nat.Cites(sources)
    body = [CSS, f'<p class="crumbs"><a href="index.html">Home</a> › <a href="world.html">Around the world</a> › {nat.esc(c["name"])}</p>',
            f'<h1>Cannabis laws in {nat.esc(c["name"])}</h1>', f'<p class="lede">{nat.esc(c["summary"])}</p>']
    if c.get('note'):
        body.append(f'<p class="muted">{nat.esc(c["note"])}</p>')
    body.append('<p class="alert"><strong>Travelling?</strong> Never carry cannabis across an international border, even between two places where it is legal. '
                '<a href="travel-warnings.html">See where it can land you in prison</a>.</p>')
    for q in world['questions']:
        a = c['answers'].get(q['id'])
        if a or q['id'] in ('adult-use', 'medical', 'possession', 'home-grow'):
            body.append(answer_card(world, q, a, cites))
    if code == 'CA':
        body.append(province_table(world, cites))
    if c.get('experiment'):
        e = c['experiment']
        body.append(f'<h2 id="context">Good to know</h2><p>{nat.esc(e["text"])} {cites.mark(e["source_ids"])}</p>')
    region = next((r for r in load_heritage()['regions'] if r.get('country_page') == c['page']), None)
    if region:
        body.append(f'<p class="lawnow">Heritage: <a href="heritage.html#{nat.esc(region["id"])}">where {nat.esc(region["place"])} fits in cannabis history</a></p>')
    body.append('<p class="muted">Summaries of the cited sources, each with the date it was checked. Not legal advice.</p>')
    body.append(cites.render())
    title = f'Cannabis laws in {c["name"]}'
    desc = f'{c["summary"]} Sourced, plain-English answers, checked {nat.long_date(world["as_of"])}.'
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
    nxt = ', '.join(nat.esc(n) for n in world['next_up'])
    body = (CSS + '<p class="crumbs"><a href="index.html">Home</a> › Around the world</p><h1>Cannabis laws around the world</h1>'
            '<p class="lede">The same plain answers as the state pages, for other countries, plus the history of where cannabis comes from. Every answer names its source and the date it was checked.</p>'
            + extra + ''.join(groups) +
            f'<h2>Coming next</h2><p>{nxt}.</p>'
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
            '<p class="lede">Legal at home does not mean legal where you land. Some countries treat any amount, or cannabis still in your bloodstream, as a serious crime.</p>'
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
    body = [CSS, '<p class="crumbs"><a href="index.html">Home</a> › Cannabis 101</p><h1>Cannabis 101</h1>',
            '<p class="lede">Plain-language explanations of cannabis words, product forms, processing, labels and safer use. '
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
            '<p class="lede">Every strain on a shelf today goes back to plants that farmers in particular places selected over generations. These are the places, the landraces and the people who carried the tradition.</p>'
            f'<div class="story"><h2>{nat.esc(o["title"])}</h2><p>{nat.esc(o["text"])} {cites.mark(o["source_ids"])}</p></div>'
            f'<div class="story"><h2>{nat.esc(l["title"])}</h2><p>{nat.esc(l["text"])} {cites.mark(l["source_ids"])}</p></div>'
            f'<p class="onpage">{jump} · <a href="#hash">Hash traditions</a></p>' + ''.join(cards) + hash_section(her, cites) +
            '<p class="muted">History drawn from the cited research, government records and reporting. Strain names are traditional market names, not verified genetics.</p>' + cites.render())
    return nat.shell('Where weed comes from: landraces and the people behind them',
                     'The origin of cannabis, the classic landraces (Afghani, Hindu Kush, Thai, Durban Poison, Acapulco Gold, Colombian Gold, beldiya) and the peoples who kept the tradition. Sourced.',
                     body, 'heritage.html', 'the heritage page',
                     ld=[nat.breadcrumbs([('Home', ''), ('Around the world', 'world.html')], 'heritage.html', 'Where weed comes from')])


def pages(perm, base_sources):
    world = load()
    sources = dict(base_sources)
    sources.update({s['id']: s for s in world['sources']})
    her = load_heritage()
    sources.update({s['id']: s for s in her['sources']})
    out = {'world.html': hub_page(world, sources), 'travel-warnings.html': warnings_page(world, perm, sources),
           'heritage.html': heritage_page(her, sources), 'learn.html': learn_page()}
    for code, c in world['countries'].items():
        out[c['page']] = country_page(world, sources, code)
    return out
