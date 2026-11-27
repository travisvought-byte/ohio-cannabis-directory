"""Visiting Las Vegas: cannabis rules for visitors, national/las-vegas.html on the-reefer.com.

Written for the people in town for MJBizCon (December 1 to 4, 2026) and every other Las Vegas visitor: whether a tourist
can buy, how much, where it can and can't be used (hotels, casinos, cars, federal land), consumption lounges, driving
and flying home. Canonical data: data/las-vegas.json. Every point carries a named official source and the date it was
checked; no business appears except as the Cannabis Compliance Board's own licensee list names it. Built through
build_national.pages(), so it shares the national page shell (navigation, footer and visit counter).
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/las-vegas.json'
NAME = 'las-vegas.html'
STATE = 'NV'

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
       '@media (max-width:760px){.lv-glance{grid-template-columns:1fr 1fr}}@media (max-width:480px){.lv-glance{grid-template-columns:1fr}.lv-places td.a{white-space:normal}}'
       '@media (prefers-color-scheme:dark){.mi{color:#a8dfbd}.lv-adult{color:var(--ink)}'
       '.yn.yes{background:rgba(46,125,79,.25);color:#a3e2bb}.yn.no{background:rgba(169,0,0,.25);color:#f3b0a6;border-color:#d0645a}'
       '.yn.maybe{background:rgba(184,134,11,.22);color:#f1d48a}.lv-mix .bar{background:#58a878}}'
       '@media print{.lv-show{display:none}}')


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def svg(name):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="{PATHS[name]}"/></svg>')


def show_box(nat, directory, contest, today=None):
    """During MJBizCon week: the free planner and the Silver Cup. Left out of builds after the show; a small script
    removes it from a page built earlier once the show's last day has passed."""
    event = next((e for e in directory.get('events', []) if e['id'] == nat.MJBIZCON_EVENT_ID), None)
    if not event:
        return ''
    start, end = date.fromisoformat(event['starts_on']), date.fromisoformat(event['ends_on'])
    if (today or date.today()) > end:
        return ''
    esc = nat.esc
    when = f'{start.strftime("%B")} {start.day} to {end.day}' if start.month == end.month else f'{start:%B} {start.day} to {end:%B} {end.day}'
    return (f'<aside class="lv-show" id="mjbizcon-week" data-ends="{end.isoformat()}" aria-labelledby="show-h">'
            f'<h2 id="show-h">{svg("calendar")}During MJBizCon week</h2>'
            f'<p>In town for <strong>{esc(event["name"])}</strong>, <time datetime="{start.isoformat()}">{esc(when)}</time>? '
            'Our free Attendee Planner lists every exhibitor with booth numbers, every session with times and rooms, and after-hours events. '
            f'And the <strong>Silver Cup</strong> runs the same days: the three best captains in our free pirate game win silver half dollars.</p>'
            '<p class="go">'
            f'<a class="cta" href="{esc(contest)}" data-track="las-vegas:silver-cup">See the Silver Cup</a>'
            f'<a href="{esc(nat.MJBIZCON_PLANNER)}/copy" target="_blank" rel="noopener" data-track="las-vegas:planner-copy">Get the free planner</a>'
            f'<a href="{esc(event["next_step_url"])}" target="_blank" rel="noopener" data-track="las-vegas:event">MJBizCon’s own site</a></p>'
            '</aside>'
            '<script>(function(){var b=document.getElementById("mjbizcon-week");if(!b)return;var d=new Date(),'
            't=d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2);'
            'if(t>b.getAttribute("data-ends"))b.remove()})();</script>')


def plain(point):
    return point['text']


def page(nat, landing, directory, today=None):
    d = load()
    esc = nat.esc
    srcs = {s['id']: s for s in d['sources']}
    order = []

    def mark(ids):
        out = []
        for sid in ids:
            assert sid in srcs, f'las-vegas: unknown source {sid}'
            if sid not in order:
                order.append(sid)
            n = order.index(sid) + 1
            out.append(f'<a href="#lvsource-{n}" aria-label="Source {n}">[{n}]</a>')
        return ' <span class="cites">' + ''.join(out) + '</span>' if out else ''

    def point(p):
        link = f' <a href="{esc(p["link"]["href"])}">{esc(p["link"]["label"])}</a>' if p.get('link') else ''
        return f'<li>{esc(p["text"])}{mark(p["source_ids"])}{link}</li>'

    body = ['<p class="crumbs"><a href="index.html">Home</a> › <a href="nevada.html">Nevada</a> › Visiting Las Vegas</p>',
            '<h1>Visiting Las Vegas? The cannabis rules for visitors</h1>', nat.for_you(esc(landing['intro'])),
            '<p class="lv-adult"><span class="age" aria-hidden="true">21+</span><span>For adults 21 and older. '
            'Plain summaries of Nevada and federal sources, each linked below. Not legal advice.</span></p>']
    body.append('<ul class="lv-glance" aria-label="The rules at a glance">' + ''.join(
        f'<li><a href="{esc(g["href"])}"><span class="mi">{svg(g["icon"])}</span><span><strong>{esc(g["big"])}</strong>'
        f'<span class="t">{esc(g["text"])}</span></span></a></li>' for g in d['glance']) + '</ul>')
    body.append(show_box(nat, directory, d['event']['contest'], today))
    body.append('<nav class="onpage" aria-label="On this page">' + ''.join(
        f'<a href="#{esc(s["id"])}">{esc(s["question"])}</a>' for s in d['sections']) + '<a href="#lvsources">Sources</a></nav>')

    faq = []
    for s in d['sections']:
        body.append(f'<section class="lv-sec" id="{esc(s["id"])}" aria-labelledby="{esc(s["id"])}-h">'
                    f'<h2 id="{esc(s["id"])}-h"><span class="mi">{svg(s["icon"])}</span>{esc(s["question"])}</h2>'
                    f'<div class="answer"><p><strong>{esc(s["short"])}</strong></p></div>'
                    '<ul class="lv-pts">' + ''.join(point(p) for p in s['points']) + '</ul>')
        if s['id'] == 'limits':
            m = d['mix']
            top = max(r['mg'] for r in m['rows'])
            body.append(f'<div class="scroll"><table class="lv-mix"><caption>{esc(m["caption"])}{mark(m["source_ids"])}</caption>'
                        '<thead><tr><th scope="col">Flower you have</th><th scope="col">THC allowed in other products</th><th scope="col"><span class="lv-sr">Share of the 7,087 mg limit</span></th></tr></thead><tbody>'
                        + ''.join(f'<tr><th scope="row">{esc(r["flower"])} <span class="muted">({esc(r["grams"])} g)</span></th>'
                                  f'<td class="n">{r["mg"]:,} mg</td><td style="width:40%"><span class="bar" style="width:{round(100 * r["mg"] / top)}%" aria-hidden="true"></span></td></tr>'
                                  for r in m['rows'])
                        + f'</tbody></table></div><p class="muted">{esc(m["note"])}</p>')
        if s.get('places'):
            body.append('<div class="scroll"><table class="lv-places"><caption>Can you use cannabis here?</caption>'
                        '<thead><tr><th scope="col">Place</th><th scope="col">Allowed?</th></tr></thead><tbody>'
                        + ''.join(f'<tr><th scope="row">{esc(r["place"])}</th><td class="a"><span class="yn {esc(r["answer"])}">'
                                  f'{svg(MARK[r["answer"]])}{esc(r["label"])}</span>{mark(r["source_ids"])}</td></tr>' for r in s['places'])
                        + '</tbody></table></div>')
        body.append('</section>')
        faq.append({'@type': 'Question', 'name': s['question'],
                    'acceptedAnswer': {'@type': 'Answer', 'text': s['short'] + ' ' + ' '.join(plain(p) for p in s['points'])}})

    body.append('<aside class="lv-more" aria-labelledby="more-h"><h2 id="more-h">Where to go next</h2><ul>'
                '<li><a href="nevada.html">The full Nevada guide</a>: the state’s law, store list and local help</li>'
                '<li><a href="law-public-use.html">Public use in every state</a>: where you can and can’t use it back home</li>'
                '<li><a href="law-driving.html">Driving and cannabis in every state</a></li>'
                '<li><a href="travel-warnings.html">Travel warnings</a>: the countries and states where any amount can land you in trouble</li>'
                '<li><a href="help.html#travel">Flying with cannabis</a>: what TSA says</li></ul></aside>')
    body.append(f'<p class="muted">Checked {nat.long_date(d["as_of"])}. Laws and lists change; each source below shows the date it was checked. '
                'A business named here is named only because the state’s own list names it.</p>')
    body.append('<h2 id="lvsources">Sources</h2><ol class="sources">' + ''.join(
        f'<li id="lvsource-{n}"><a href="{esc(srcs[sid]["url"])}" target="_blank" rel="noopener">{esc(srcs[sid]["title"])}</a> · '
        f'{esc(srcs[sid]["publisher"])} · {"primary" if srcs[sid]["kind"] == "primary" else "secondary"} source · checked {nat.long_date(srcs[sid]["checked"])}</li>'
        for n, sid in enumerate(order, 1)) + '</ol>')

    ld = [nat.breadcrumbs([('Home', ''), ('Nevada', 'nevada.html')], NAME, 'Visiting Las Vegas')]
    if nat.ORIGIN:
        ld.append({'@type': 'FAQPage', '@id': nat.page_url(NAME) + '#faq', 'url': nat.page_url(NAME),
                   'isPartOf': {'@id': nat.ORIGIN + '/#website'}, 'mainEntity': faq})
    return nat.shell('Visiting Las Vegas: cannabis rules for visitors (2026)',
                     'Can tourists buy weed in Las Vegas? Yes, at 21 with ID. Limits, where you can and can’t use it (hotels, casinos, cars, '
                     'Red Rock, Lake Mead, Hoover Dam), lounges, driving and flying home, from official sources.',
                     ''.join(body), NAME, 'the Las Vegas visitor page', ld=ld, css=CSS)
