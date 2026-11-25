"""Hash myths, busted: national/hash-myths.html on the-reefer.com.

Owner direction, November 24, 2026: a myth-buster on mechanical hash making, built from Travis's own dry sift runs.
Canonical data: data/hash-myths.json. Figures from Travis's own runs are labeled as his; every other claim carries a
named source and the date it was checked. Built through build_national.pages(), so it shares the national page shell.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/hash-myths.json'
NAME = 'hash-myths.html'

# Line icons, decorative only (aria-hidden): every icon sits next to text that says the same thing.
PATHS = {
    'scale': 'M12 3v18M6 21h12M4 7h16M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z',
    'repeat': 'M4 11V9a3 3 0 0 1 3-3h12l-3-3M20 13v2a3 3 0 0 1-3 3H5l3 3',
    'snow': 'M12 2v20M4.5 6.5l15 11M19.5 6.5l-15 11M9.5 3.5 12 6l2.5-2.5M9.5 20.5 12 18l2.5 2.5',
    'filter': 'M3 4h18l-7 8v6l-4 2v-8z',
    'drop': 'M12 3s-6 6.5-6 11a6 6 0 0 0 12 0c0-4.5-6-11-6-11z',
    'gavel': 'M12 6l2.5-2.5 6 6L18 12zM15 9 4 20M13 21h8',
    'leaf': 'M5 19C5 11 10 5 20 4c-1 10-7 15-15 15zM5 19l7-7',
    'shake': 'M4 6h16M6 6l1 4h10l1-4M8 14h.01M12 15h.01M16 14h.01M10 18h.01M14 18h.01',
    'tray': 'M3 9h18l-2 9H5zM3 9l2-4h14l2 4',
    'layers': 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5M3 17l9 5 9-5',
}

CSS = ('.myth-hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;align-items:center;margin:10px 0 6px}'
       '.myth-hero figure{margin:0}.myth-hero img{width:100%;height:auto;border-radius:14px;display:block}.myth-hero figcaption{font-size:.88rem;color:var(--soft);margin-top:6px}'
       '.yield{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}.yield .big{font-size:2.4rem;font-weight:800;line-height:1.1;margin:0;color:var(--green)}'
       '.ybar{display:grid;grid-template-columns:5.5em 1fr;gap:8px;align-items:center;margin:8px 0;font-size:.95rem}'
       '.ybar span.b{display:block;height:18px;border-radius:9px;background:var(--green2)}.ybar span.b.out{background:var(--gold)}'
       '.flow{list-style:none;padding:0;margin:14px 0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;counter-reset:s}'
       '.flow li{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;counter-increment:s}'
       '.flow li strong{display:block}.flow li strong::before{content:counter(s) ". "}.flow li p{margin:4px 0 0;font-size:.92rem}'
       '.mi{display:grid;place-items:center;width:40px;height:40px;border-radius:10px;background:var(--mint);color:var(--green);margin-bottom:6px}.mi svg{width:24px;height:24px}'
       '.myths{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}'
       '.myth{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;scroll-margin-top:16px}'
       '.myth h3{margin:.2em 0 .3em}.verdict{display:inline-block;font-weight:800;font-size:.85rem;letter-spacing:.04em;text-transform:uppercase;'
       'padding:3px 10px;border-radius:999px;background:#7a1010;color:#fff}.verdict::before{content:"\\2715\\00a0"}'
       '.firsthand{display:inline-block;font-size:.82rem;font-weight:700;padding:2px 8px;border-radius:999px;background:var(--note);color:#4a3a08;margin-left:6px}'
       '.method{background:var(--mint);border-radius:14px;padding:18px;margin:22px 0}.method .pts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}'
       '.bottom{font-size:1.15rem;font-weight:700;border-left:5px solid var(--gold);padding:8px 14px;background:var(--card)}'
       '@media (max-width:760px){.myth-hero,.myths,.method .pts{grid-template-columns:1fr}.flow{grid-template-columns:1fr}}'
       '@media (prefers-color-scheme:dark){.mi{color:#a8dfbd}.firsthand{color:#4a3a08}.method{color:var(--ink)}}')


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def svg(name):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="{PATHS[name]}"/></svg>')


def page(nat, landing):
    d = load()
    esc = nat.esc
    srcs = {s['id']: s for s in d['sources']}
    order = []

    def mark(ids):
        out = []
        for sid in ids:
            assert sid in srcs, f'hash-myths: unknown source {sid}'
            if sid not in order:
                order.append(sid)
            n = order.index(sid) + 1
            out.append(f'<a href="#hsource-{n}" aria-label="Source {n}">[{n}]</a>')
        return ' <span class="cites">' + ''.join(out) + '</span>' if out else ''

    p, y = d['photo'], d['yield']
    share = round(100 * y['out_grams'] / y['in_grams'])
    body = ['<p class="crumbs"><a href="index.html">Home</a> › <a href="learn.html">Cannabis 101</a> › Hash myths</p>',
            '<h1>Hash myths, busted</h1>', nat.for_you(esc(landing['intro'])),
            '<div class="myth-hero"><figure><picture>'
            f'<source srcset="{nat.ASSETS}{esc(p["webp"])}" type="image/webp">'
            f'<img src="{nat.ASSETS}{esc(p["jpg"])}" alt="{esc(p["alt"])}" width="{p["width"]}" height="{p["height"]}" loading="lazy"></picture>'
            f'<figcaption>{esc(p["caption"])}</figcaption></figure>'
            f'<div class="yield" role="group" aria-labelledby="yield-h"><h2 id="yield-h" style="margin-top:0">One ounce in, real hash out</h2>'
            f'<p class="big">~{y["out_grams"]} g</p><p>of dry sift from {y["in_grams"]} g (one ounce) of flower, about {share}% back.</p>'
            f'<div class="ybar"><span>Flower in</span><span class="b" style="width:100%"></span></div>'
            f'<div class="ybar"><span>Sift out</span><span class="b out" style="width:{max(share, 4)}%"></span></div>'
            f'<p class="muted"><span class="firsthand">From Travis\'s own runs</span> {esc(y["note"])}</p></div></div>',
            '<h2 id="how">How dry sift works, in five steps</h2><ol class="flow">']
    for s in d['steps']:
        body.append(f'<li><span class="mi">{svg(s["icon"])}</span><strong>{esc(s["title"])}</strong><p>{esc(s["text"])}</p></li>')
    body.append('</ol><h2 id="myths">The myths</h2><p class="onpage">'
                + ' · '.join(f'<a href="#{esc(m["id"])}">{esc(m["myth"])}</a>' for m in d['myths']) + '</p><div class="myths">')
    for m in d['myths']:
        tag = '<span class="firsthand">From Travis\'s own runs</span>' if m.get('first_hand') else ''
        body.append(f'<article class="myth" id="{esc(m["id"])}"><span class="mi">{svg(m["icon"])}</span>'
                    f'<p style="margin:0"><span class="verdict">{esc(m["verdict"])}</span>{tag}</p>'
                    f'<h3>Myth: “{esc(m["myth"])}”</h3><p>{esc(m["text"])}{mark(m["source_ids"])}</p></article>')
    body.append('</div>')
    me = d['method']
    body.append(f'<section class="method" id="method" aria-labelledby="method-h"><h2 id="method-h" style="margin-top:0">{esc(me["title"])}</h2><p>{esc(me["view"])}</p><div class="pts">')
    for pt in me['points']:
        body.append(f'<div><span class="mi">{svg(pt["icon"])}</span><h3 style="margin-top:0">{esc(pt["title"])}</h3><p>{esc(pt["text"])}</p></div>')
    body.append(f'</div><p class="muted">{esc(me["label"])}</p></section>')
    body.append(f'<p class="bottom">{esc(d["bottom_line"])}</p>')
    body.append('<p>More: <a href="learn.html#processing">how cannabis is processed</a> · <a href="heritage.html#hash">hash traditions around the world</a> · '
                '<a href="law-home-grow.html">home grow law in every state</a></p>')
    body.append(f'<p class="muted">Checked {nat.long_date(d["as_of"])}. Home processing rules differ by state; check yours before you start. Not legal advice.</p>')
    body.append('<h2 id="sources">Sources</h2><ol class="sources">' + ''.join(
        f'<li id="hsource-{n}"><a href="{esc(srcs[sid]["url"])}" target="_blank" rel="noopener">{esc(srcs[sid]["title"])}</a> · '
        f'{"primary" if srcs[sid]["kind"] == "primary" else "secondary"} source · checked {nat.long_date(srcs[sid]["checked"])}</li>'
        for n, sid in enumerate(order, 1)) + '</ol>')
    return nat.shell('Hash myths, busted: dry sift, ice water and what you really need',
                     'You do not need pounds of weed or 80 pounds of ice to make clean hash. Dry sift, filter bags and a press, with real yields from one ounce and Ohio\'s home processing law.',
                     ''.join(body), NAME, 'the hash myths page',
                     ld=[nat.breadcrumbs([('Home', ''), ('Cannabis 101', 'learn.html')], NAME, 'Hash myths')], css=CSS)
