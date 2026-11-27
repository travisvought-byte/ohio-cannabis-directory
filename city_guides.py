"""City visitor guides on the-reefer.com: the cannabis rules for people visiting a city, one page per city.

Each guide answers the questions visitors ask (can a tourist buy, how much, where it can and can't be used, hotels,
cars and driving, federal land, flying home, out-of-state medical cards, edibles), with quick-answer tiles, an
adults-21+ notice, a yes/no table of places, FAQPage markup and a numbered, dated source list. Every point names an
official source and the date it was checked; no business appears except as a regulator's own licensee list names it.

render() draws any guide. las_vegas.py uses it with its own extras (the MJBizCon-week box and the Nevada
flower-and-products chart). The other cities are plain data: data/denver.json, data/chicago.json,
data/new-york-city.json, data/los-angeles.json, data/detroit.json, data/boston.json, data/seattle.json,
data/phoenix.json, data/miami.json, data/san-francisco.json, data/portland.json, data/new-orleans.json and
data/washington-dc.json, each with a
"page" block that names the page, its state and its "Where to go next" links. A state can have more than one guide
(California: Los Angeles and San Francisco); its page links them all in one visitor-guide box.
A state with no adult-use sales (Florida, for Miami; Louisiana, for New Orleans; the District of Columbia, which allows
possession but sells only through its medical program) needs the page to say so before anything else. Its "page" block
can add a "status" notice (heading, text, source_ids) shown under the adults-21+ line, and "places_caption" and
"places_header" to reword the yes/no table; guides without them render exactly as before.
All of them are built through build_national.pages(), so they share the national page shell.

hub() draws visiting.html, the list of every guide (Las Vegas included) with whether adults 21 and older can buy there,
read from each guide's own "Can tourists buy" answer; every guide links back to it in a "More city guides" line.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The data-only guides, in the order they are linked (November 27, 2026).
GUIDES = {
    'denver.html': ROOT / 'data/denver.json',
    'chicago.html': ROOT / 'data/chicago.json',
    'new-york-city.html': ROOT / 'data/new-york-city.json',
    'los-angeles.html': ROOT / 'data/los-angeles.json',
    'detroit.html': ROOT / 'data/detroit.json',
    'boston.html': ROOT / 'data/boston.json',
    'seattle.html': ROOT / 'data/seattle.json',
    'phoenix.html': ROOT / 'data/phoenix.json',
    'miami.html': ROOT / 'data/miami.json',
    'san-francisco.html': ROOT / 'data/san-francisco.json',
    'portland.html': ROOT / 'data/portland.json',
    'new-orleans.html': ROOT / 'data/new-orleans.json',
    'washington-dc.html': ROOT / 'data/washington-dc.json',
}
HUB = 'visiting.html'  # every visitor guide on one page (November 27, 2026)

# Line icons, decorative only (aria-hidden): every icon sits next to text that says the same thing.
PATHS = {
    'id': 'M3 5h18v14H3zM8 11a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM5 16a3 3 0 0 1 6 0M14 9h4M14 13h4',
    'scale': 'M12 3v18M6 21h12M4 7h16M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z',
    'nosmoke': 'M3 3l18 18M3 14h11v3H3zM17 14h1v3h-1M20 14h1v3h-1M17 10c0-2 2-2 2-4',
    'lounge': 'M4 12V9a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v3M2 12a2 2 0 0 1 4 0v2h12v-2a2 2 0 0 1 4 0v5H2zM5 17v3M19 17v3',
    'car': 'M5 16h14M6 16l1.5-5h9L18 16M4 16v3h3v-3M17 16v3h3v-3M8 13.5h.01M16 13.5h.01',
    'plane': 'M2 16l20-6-2-3-7 2-5-6-2 1 3 6-5 1.5-2-2-1.5.5 1.5 4z',
    'pin': 'M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12zM12 11.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
    'hotel': 'M4 21V4h11v17M15 9h5v12M2 21h20M7 7h2M11 7h2M7 11h2M11 11h2M7 15h2M11 15h2M17 13h1M17 17h1',
    'mountain': 'M2 20l7-12 4 6 3-4 6 10zM9 8l1.5 2.5',
    'card': 'M3 6h18v12H3zM3 10h18M7 15h4',
    'clock': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2',
    'calendar': 'M4 6h16v14H4zM4 10h16M9 3v4M15 3v4',
    'check': 'M4 12l5 5L20 6',
    'x': 'M6 6l12 12M18 6L6 18',
    'half': 'M12 3a9 9 0 1 0 0 18zM12 3a9 9 0 0 1 0 18',
    'shield': 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM8.5 12l2.5 2.5 4.5-5',
    'store': 'M3 9l2-5h14l2 5M3 9h18M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M5 12v9h14v-9M10 21v-5h4v5',
}
MARK = {'yes': 'check', 'no': 'x', 'maybe': 'half'}

CSS = ('.lv-sr{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}'
       '.lv-adult{display:inline-flex;align-items:center;gap:10px;background:var(--note);color:var(--ink);border-radius:10px;padding:8px 14px;font-size:.95rem;max-width:none}'
       '.lv-adult .age{flex:none;display:grid;place-items:center;min-width:44px;height:30px;border-radius:999px;background:#7a1010;color:#fff;font-weight:800;font-size:.9rem}'
       '.lv-glance{list-style:none;padding:0;margin:16px 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}'
       '.lv-glance a{display:flex;gap:12px;align-items:flex-start;height:100%;min-height:44px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;text-decoration:none;color:var(--ink)}'
       '.lv-glance a:hover,.lv-glance a:focus-visible{border-color:var(--green2);box-shadow:0 6px 18px rgba(23,35,30,.1)}'
       '.lv-glance strong{display:block;font-size:1.2rem;line-height:1.2;color:var(--link)}.lv-glance span.t{display:block;font-size:.93rem;color:var(--soft);margin-top:2px}'
       '.mi{display:grid;place-items:center;width:40px;height:40px;border-radius:10px;background:var(--mint);color:var(--green);flex:none}.mi svg{width:24px;height:24px}'
       '.lv-show{background:#10291f;color:#f4f1e8;border-left:6px solid var(--gold);border-radius:14px;padding:14px 18px;margin:18px 0}'
       '.lv-show h2{margin:.1em 0 .3em;font-size:1.25rem;color:#fff;display:flex;align-items:center;gap:8px}.lv-show h2 svg{width:24px;height:24px;color:var(--gold)}'
       '.lv-show p{margin:.35em 0}.lv-show a{color:#fff;font-weight:700}.lv-show .go{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:10px}'
       '.lv-show .go a{display:inline-flex;align-items:center;min-height:44px}.lv-show .go a.cta{background:var(--gold);color:#221c08;border-radius:8px;padding:0 16px;text-decoration:none}'
       '.lv-sec{scroll-margin-top:12px}.lv-sec h2{display:flex;align-items:center;gap:10px}.lv-sec h2 .mi{width:36px;height:36px}'
       '.lv-pts{padding-left:1.2em;max-width:72ch}.lv-pts li{margin:.45em 0}'
       '.lv-places{margin:12px 0;max-width:820px}.lv-places caption{text-align:left;font-weight:700;padding:0 0 6px}.lv-places td.a{white-space:nowrap}'
       '.yn{display:inline-flex;align-items:center;gap:6px;font-weight:700;border-radius:999px;padding:2px 10px 2px 4px;border:1px solid}'
       '.yn svg{width:18px;height:18px;border-radius:50%;padding:2px;color:#fff;flex:none}'
       '.yn.yes{background:#e7f3eb;border-color:#2e7d4f;color:#1d5a37}.yn.yes svg{background:#2e7d4f}'
       '.yn.no{background:#fbeaea;border-color:#a90000;color:#7a0000}.yn.no svg{background:#a90000}'
       '.yn.maybe{background:#fff4dc;border-color:#b8860b;color:#664a00}.yn.maybe svg{background:#8a6400}'
       '.lv-mix{max-width:720px;margin:12px 0}.lv-mix caption{text-align:left;font-weight:700;padding:0 0 6px}.lv-mix td.n{white-space:nowrap;font-variant-numeric:tabular-nums}'
       '.lv-mix .bar{display:block;height:14px;border-radius:7px;background:var(--green2);min-width:2px}'
       '.lv-more{background:var(--mint);border-radius:14px;padding:14px 18px;margin:26px 0}.lv-more h2{margin:0 0 .3em;font-size:1.2rem}.lv-more ul{margin:.3em 0;padding-left:1.2em}'
       '.lv-allguides{margin:.6em 0 0}.lv-allguides a{display:inline-flex;align-items:center;min-height:44px;font-weight:700}'
       '@media (max-width:760px){.lv-glance{grid-template-columns:1fr 1fr}}@media (max-width:480px){.lv-glance{grid-template-columns:1fr}.lv-places td.a{white-space:normal}}'
       '@media (prefers-color-scheme:dark){.mi{color:#a8dfbd}.lv-adult{color:var(--ink)}'
       '.yn.yes{background:rgba(46,125,79,.25);color:#a3e2bb}.yn.no{background:rgba(169,0,0,.25);color:#f3b0a6;border-color:#d0645a}'
       '.yn.maybe{background:rgba(184,134,11,.22);color:#f1d48a}.lv-mix .bar{background:#58a878}}'
       '@media print{.lv-show{display:none}}')
# Only on a page with a "status" notice (a medical-only state), so the other guides' styles stay as they were.
STATUS_CSS = ('.lv-status{background:var(--card);color:var(--ink);border:2px solid #a90000;border-left-width:6px;border-radius:14px;padding:12px 18px;margin:16px 0;max-width:820px}'
              '.lv-status h2{margin:.1em 0 .3em;font-size:1.25rem;display:flex;align-items:center;gap:10px}.lv-status h2 .mi{width:36px;height:36px}'
              '.lv-status p{margin:.3em 0;max-width:72ch}'
              '@media (prefers-color-scheme:dark){.lv-status{border-color:#d0645a}}')


def svg(name):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="{PATHS[name]}"/></svg>')


def load(name):
    return json.loads(GUIDES[name].read_text(encoding='utf-8'))


def render(nat, d, intro, cfg, top='', after_section=None):
    """One visitor guide. d is the guide's data (glance, sections, sources); cfg names the page:
    name, state_name, state_page, crumb, h1, title, description, adult, prefix, place, more [(href, label, rest)]
    and business_note, plus the optional status {heading, text, source_ids, icon}, places_caption and places_header
    for a medical-only state. top is HTML placed after the tiles; after_section(section, mark) adds HTML inside a section."""
    esc = nat.esc
    name, prefix = cfg['name'], cfg['prefix']
    srcs = {s['id']: s for s in d['sources']}
    order = []

    def mark(ids):
        out = []
        for sid in ids:
            assert sid in srcs, f'{name}: unknown source {sid}'
            if sid not in order:
                order.append(sid)
            n = order.index(sid) + 1
            out.append(f'<a href="#{prefix}source-{n}" aria-label="Source {n}">[{n}]</a>')
        return ' <span class="cites">' + ''.join(out) + '</span>' if out else ''

    def point(p):
        link = f' <a href="{esc(p["link"]["href"])}">{esc(p["link"]["label"])}</a>' if p.get('link') else ''
        return f'<li>{esc(p["text"])}{mark(p["source_ids"])}{link}</li>'

    body = [f'<p class="crumbs"><a href="index.html">Home</a> › <a href="{esc(cfg["state_page"])}">{esc(cfg["state_name"])}</a> › {esc(cfg["crumb"])}</p>',
            f'<h1>{esc(cfg["h1"])}</h1>', nat.for_you(esc(intro)),
            f'<p class="lv-adult"><span class="age" aria-hidden="true">21+</span><span>{esc(cfg["adult"])}</span></p>']
    status = cfg.get('status')
    if status:
        body.append(f'<section class="lv-status" aria-labelledby="{prefix}status-h"><h2 id="{prefix}status-h">'
                    f'<span class="mi">{svg(status.get("icon", "card"))}</span>{esc(status["heading"])}</h2>'
                    f'<p>{esc(status["text"])}{mark(status["source_ids"])}</p></section>')
    caption = cfg.get('places_caption', 'Can you use cannabis here?')
    header = cfg.get('places_header', 'Allowed?')
    body.append('<ul class="lv-glance" aria-label="The rules at a glance">' + ''.join(
        f'<li><a href="{esc(g["href"])}"><span class="mi">{svg(g["icon"])}</span><span><strong>{esc(g["big"])}</strong>'
        f'<span class="t">{esc(g["text"])}</span></span></a></li>' for g in d['glance']) + '</ul>')
    body.append(top)
    body.append('<nav class="onpage" aria-label="On this page">' + ''.join(
        f'<a href="#{esc(s["id"])}">{esc(s["question"])}</a>' for s in d['sections']) + f'<a href="#{prefix}sources">Sources</a></nav>')

    faq = []
    for s in d['sections']:
        body.append(f'<section class="lv-sec" id="{esc(s["id"])}" aria-labelledby="{esc(s["id"])}-h">'
                    f'<h2 id="{esc(s["id"])}-h"><span class="mi">{svg(s["icon"])}</span>{esc(s["question"])}</h2>'
                    f'<div class="answer"><p><strong>{esc(s["short"])}</strong></p></div>'
                    '<ul class="lv-pts">' + ''.join(point(p) for p in s['points']) + '</ul>')
        if after_section:
            body.append(after_section(s, mark))
        if s.get('places'):
            body.append(f'<div class="scroll"><table class="lv-places"><caption>{esc(caption)}</caption>'
                        f'<thead><tr><th scope="col">Place</th><th scope="col">{esc(header)}</th></tr></thead><tbody>'
                        + ''.join(f'<tr><th scope="row">{esc(r["place"])}</th><td class="a"><span class="yn {esc(r["answer"])}">'
                                  f'{svg(MARK[r["answer"]])}{esc(r["label"])}</span>{mark(r["source_ids"])}</td></tr>' for r in s['places'])
                        + '</tbody></table></div>')
        body.append('</section>')
        faq.append({'@type': 'Question', 'name': s['question'],
                    'acceptedAnswer': {'@type': 'Answer', 'text': s['short'] + ' ' + ' '.join(p['text'] for p in s['points'])}})

    body.append('<aside class="lv-more" aria-labelledby="more-h"><h2 id="more-h">Where to go next</h2><ul>'
                + ''.join(f'<li><a href="{esc(href)}">{esc(label)}</a>{esc(rest)}</li>' for href, label, rest in cfg['more'])
                + '</ul>'
                f'<p class="lv-allguides"><strong>More city guides:</strong> <a href="{HUB}">Cannabis rules for visitors, city by city</a></p></aside>')
    body.append(f'<p class="muted">Checked {nat.long_date(d["as_of"])}. Laws and lists change; each source below shows the date it was checked. '
                f'{esc(cfg["business_note"])}</p>')
    body.append(f'<h2 id="{prefix}sources">Sources</h2><ol class="sources">' + ''.join(
        f'<li id="{prefix}source-{n}"><a href="{esc(srcs[sid]["url"])}" target="_blank" rel="noopener">{esc(srcs[sid]["title"])}</a> · '
        f'{esc(srcs[sid]["publisher"])} · {"primary" if srcs[sid]["kind"] == "primary" else "secondary"} source · checked {nat.long_date(srcs[sid]["checked"])}</li>'
        for n, sid in enumerate(order, 1)) + '</ol>')

    ld = [nat.breadcrumbs([('Home', ''), (cfg['state_name'], cfg['state_page'])], name, cfg['crumb'])]
    if nat.ORIGIN:
        ld.append({'@type': 'FAQPage', '@id': nat.page_url(name) + '#faq', 'url': nat.page_url(name),
                   'isPartOf': {'@id': nat.ORIGIN + '/#website'}, 'mainEntity': faq})
    return nat.shell(cfg['title'], cfg['description'], ''.join(body), name, cfg['place'], ld=ld,
                     css=CSS + (STATUS_CSS if status else ''))


def page(nat, name, landing):
    """A data-only city guide (every city in GUIDES)."""
    d = load(name)
    p = d['page']
    cfg = dict(p, name=name, more=[(m['href'], m['label'], m.get('rest', '')) for m in p['more']])
    return render(nat, d, landing['intro'], cfg)


def state_boxes():
    """{state code: [(page, heading, text), ...]} for the visitor-guide box near the top of each state's page,
    one entry per guide in that state, in GUIDES order."""
    out = {}
    for name in GUIDES:
        d = load(name)
        out.setdefault(d['page']['state'], []).append((name, d['page']['crumb'] + '?', d['state_box']))
    return out


def home_links():
    """[(page, label)] for the home page's "Also" line, in GUIDES order."""
    return [(name, load(name)['page']['crumb']) for name in GUIDES]


def buy_answer(d):
    """(mark, words) for "Can adults 21 and older buy here?", from the guide's own "buy" answer: its opening sentence,
    and the next one too when the first is a bare Yes or No. Yes is adult-use; No and Only (a patient) are medical-only."""
    short = next(s['short'] for s in d['sections'] if s['id'] == 'buy')
    parts = short.split('. ')
    words = parts[0] if len(parts) == 1 else parts[0] + '.'
    if words in ('Yes.', 'No.') and len(parts) > 1:
        words += ' ' + parts[1].rstrip('.') + '.'
    first = short.split()[0].rstrip('.,').lower()
    assert first in ('yes', 'no', 'only'), f'unclear buy answer: {short[:40]}'
    return {'yes': 'yes', 'no': 'no', 'only': 'maybe'}[first], words


def hub_rows():
    """Every guide as {page, city, state, state_page, mark, label, words, as_of}, Las Vegas included."""
    import las_vegas  # imported here: las_vegas imports this module
    rows = [(las_vegas.NAME, las_vegas.load(), las_vegas.PAGE)] + [(name, load(name), load(name)['page']) for name in GUIDES]
    out = []
    for name, d, p in rows:
        mark, words = buy_answer(d)
        out.append({'page': name, 'city': p['crumb'].removeprefix('Visiting '), 'crumb': p['crumb'], 'state': p['state_name'],
                    'state_page': p['state_page'], 'mark': mark, 'label': {'yes': 'Yes', 'no': 'No', 'maybe': 'Only as a patient'}[mark],
                    'words': words, 'as_of': d['as_of']})
    return sorted(out, key=lambda r: r['city'])


HUB_CSS = ('.vg-table{max-width:980px}.vg-table caption{text-align:left;font-weight:700;padding:0 0 6px}'
           '.vg-table th[scope=row] a{font-weight:800;display:inline-flex;align-items:center;min-height:44px}'
           '.vg-table td .yn{margin:0 0 4px}.vg-table td p{margin:.2em 0 0;max-width:60ch}'
           '.vg-group h2{display:flex;align-items:center;gap:10px}.vg-group h2 .mi{width:36px;height:36px}'
           '.vg-count{font-size:1.05rem}')


def hub(nat, landing):
    """visiting.html: every visitor guide, grouped by whether adults 21 and older can buy at a licensed store,
    A to Z within each group, each with its own answer in words and a symbol."""
    esc = nat.esc
    rows = hub_rows()
    groups = [('adult-use', 'store', 'Adults 21 and older can buy at licensed stores',
               'These places have adult-use sales. Each guide says what ID to bring, how much you can buy and where you can and can’t use it.',
               [r for r in rows if r['mark'] == 'yes']),
              ('medical-only', 'card', 'No adult-use sales: medical only',
               'Here cannabis is sold only through a medical program. Each guide says whether a visitor can qualify, and what having it without a card means.',
               [r for r in rows if r['mark'] != 'yes'])]
    checked = sorted({r['as_of'] for r in rows})
    when = nat.long_date(checked[-1]) if len(checked) == 1 else f'between {nat.long_date(checked[0])} and {nat.long_date(checked[-1])}'
    body = ['<p class="crumbs"><a href="index.html">Home</a> › Visitor guides</p>',
            '<h1>Cannabis rules for visitors, city by city</h1>', nat.for_you(esc(landing['intro'])),
            '<p class="lv-adult"><span class="age" aria-hidden="true">21+</span><span>For adults 21 and older. Plain summaries of official sources, '
            'each linked in its guide. Not legal advice.</span></p>',
            f'<p class="vg-count">{len(rows)} city guides: {len(groups[0][4])} where adults 21 and older can buy, '
            f'{len(groups[1][4])} where cannabis is sold only through a medical program.</p>',
            '<nav class="onpage" aria-label="On this page">' + ''.join(f'<a href="#{gid}">{esc(head)}</a>' for gid, _, head, _, _ in groups) + '</nav>']
    for gid, ic, head, text, items in groups:
        body.append(f'<section class="vg-group lv-sec" id="{gid}" aria-labelledby="{gid}-h"><h2 id="{gid}-h"><span class="mi">{svg(ic)}</span>{esc(head)}</h2>'
                    f'<p>{esc(text)}</p><div class="scroll"><table class="vg-table"><caption>{esc(head)}, A to Z</caption>'
                    '<thead><tr><th scope="col">City guide</th><th scope="col">State or district</th><th scope="col">Can adults 21 and older buy there?</th></tr></thead><tbody>'
                    + ''.join(f'<tr><th scope="row"><a href="{esc(r["page"])}">{esc(r["crumb"])}</a></th>'
                              f'<td><a href="{esc(r["state_page"])}">{esc(r["state"])}</a></td>'
                              f'<td><span class="yn {r["mark"]}">{svg(MARK[r["mark"]])}{esc(r["label"])}</span><p>{esc(r["words"])}</p></td></tr>'
                              for r in items)
                    + '</tbody></table></div></section>')
    body.append('<aside class="lv-more" aria-labelledby="more-h"><h2 id="more-h">Where to go next</h2><ul>'
                '<li><a href="index.html#map">Your state’s full guide</a>: the law, record clearing and local help</li>'
                '<li><a href="law-public-use.html">Public use in every state</a></li>'
                '<li><a href="medical.html">Getting a medical cannabis card, state by state</a></li>'
                '<li><a href="travel-warnings.html">Travel warnings</a>: the countries and states where any amount can land you in trouble</li>'
                '<li><a href="help.html#travel">Flying with cannabis</a>: what TSA says</li></ul></aside>')
    body.append(f'<p class="muted">Every guide was checked {when}, and each lists its sources with the date it checked them. '
                'No business is named here; each guide links its regulator’s own list of licensed businesses.</p>')
    ld = [nat.breadcrumbs([('Home', '')], HUB, 'Visitor guides')]
    if nat.ORIGIN:
        ld.append({'@type': 'ItemList', '@id': nat.page_url(HUB) + '#guides', 'name': 'Cannabis rules for visitors, city by city',
                   'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': r['crumb'], 'url': nat.page_url(r['page'])}
                                       for i, r in enumerate([r for _, _, _, _, items in groups for r in items], 1)]})
    description = ('Can tourists buy weed? The cannabis rules for visitors in ' + str(len(rows)) + ' cities, from Las Vegas to Washington, DC: '
                   'who can buy, where it’s allowed, cars, federal land and flying, each from official sources.')
    return nat.shell('Cannabis rules for visitors, city by city (2026)', description, ''.join(body), HUB, 'the visitor guides page',
                     ld=ld, css=CSS + HUB_CSS)
