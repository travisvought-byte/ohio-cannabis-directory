"""Budtender training guide: national/budtender-guide.html on the-reefer.com.

Owner direction, November 28, 2026: what front-line budtenders need to know, so a customer never has to name a product
category to get help. The page follows the owner's six-step intake: what they want out of it, their requirements,
beliefs to clear up, their preference, the pros and cons of each form when they have none, and the strains customers
commonly report for that use. Canonical data: data/budtender-guide.json. Every fact carries a named source and the date
it was checked; strain notes are breeder descriptions or user reports, labeled as such, never medical claims.
Built through build_national.pages(), so it shares the national page shell (navigation, footer and visit counter).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/budtender-guide.json'
NAME = 'budtender-guide.html'

# Line icons, decorative only (aria-hidden): every icon sits next to text that says the same thing.
PATHS = {
    'target': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM12 12h.01',
    'list': 'M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2',
    'bulb': 'M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z',
    'heart': 'M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z',
    'grid': 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
    'leaf': 'M5 19C5 11 10 5 20 4c-1 10-7 15-15 15zM5 19l7-7',
    'moon': 'M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z',
    'wave': 'M3 9c3-3 6 3 9 0s6 3 9 0M3 15c3-3 6 3 9 0s6 3 9 0',
    'hand': 'M8 13V5a1.5 1.5 0 0 1 3 0v6M11 10V4a1.5 1.5 0 0 1 3 0v6M14 10V5a1.5 1.5 0 0 1 3 0v7M17 9a1.5 1.5 0 0 1 3 0v4a8 8 0 0 1-8 8h-1a6 6 0 0 1-5-3l-2.5-4.5a1.5 1.5 0 0 1 2.6-1.5L8 14',
    'people': 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 20a6 6 0 0 1 12 0M17 11a2.5 2.5 0 1 0 0-5M16 14a5 5 0 0 1 5 6',
    'sun': 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4',
    'fork': 'M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M17 21V3c-2 1-3 4-3 7h3',
    'drop': 'M12 3s-6 6.5-6 11a6 6 0 0 0 12 0c0-4.5-6-11-6-11z',
    'nosmoke': 'M3 3l18 18M3 14h11v3H3zM17 14h1v3h-1M20 14h1v3h-1M17 10c0-2 2-2 2-4',
    'eyeoff': 'M3 3l18 18M10.6 6.1A10 10 0 0 1 12 6c5 0 9 6 9 6a17 17 0 0 1-2.6 3.2M6.6 6.6A17 17 0 0 0 3 12s4 6 9 6a9 9 0 0 0 4.4-1.1M9.9 9.9a3 3 0 0 0 4.2 4.2',
    'bolt': 'M13 2 4 14h7l-1 8 9-12h-7z',
    'clock': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2',
    'dollar': 'M12 2v20M17 6H10a3 3 0 0 0 0 6h4a3 3 0 0 1 0 6H6',
    'flask': 'M9 3h6M10 3v6L4.5 18.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.5L14 9V3M7 15h10',
    'shuffle': 'M3 7h4l10 10h4M3 17h4l3-3M14 10l3-3h4M18 4l3 3-3 3M18 14l3 3-3 3',
    'gauge': 'M4 17a8 8 0 1 1 16 0M12 17l4-5M8 17h.01M16 17h.01',
    'hourglass': 'M6 3h12M6 21h12M7 3c0 5 10 5 10 9s-10 4-10 9M17 3c0 5-10 5-10 9s10 4 10 9',
    'calendar': 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
    'shield': 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM8.5 12l2.5 2.5 4.5-5',
    'tag': 'M3 12V3h9l9 9-9 9zM7.5 7.5h.01',
    'joint': 'M3 15l13-6 2 4-13 6zM18 11l3-1.5M19 6c0-1.5 1-2 1-3.5',
    'cloud': 'M7 18a4 4 0 0 1-.5-8A6 6 0 0 1 18 9a4.5 4.5 0 0 1-.5 9z',
    'gem': 'M6 3h12l3 6-9 12L3 9zM3 9h18M12 21 9 9l3-6 3 6z',
    'candy': 'M8 8a5.7 5.7 0 0 1 8 8 5.7 5.7 0 0 1-8-8zM8 8 5 5 3 7l2 2zM16 16l3 3-2 2-2-2z',
    'cup': 'M6 3h12l-1.5 17a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1zM6.5 8h11',
    'dropper': 'M15 3l6 6M18 6l-9.5 9.5-3 1 1-3L16 4M7 17l-3 4',
    'sprout': 'M12 21v-9M12 12C12 7 8 5 4 5c0 4 3 7 8 7zM12 12c0-4 3-6 8-6 0 4-3 6-8 6',
    'cross': 'M9 3h6v6h6v6h-6v6H9v-6H3V9h6z',
    'gift': 'M3 9h18v4H3zM5 13v8h14v-8M12 9v12M12 9c-2-4-6-4-6-1s6 1 6 1zM12 9c2-4 6-4 6-1s-6 1-6 1z',
    'alert': 'M12 3 2 20h20zM12 10v4M12 17h.01',
    'id': 'M3 5h18v14H3zM8 11a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM5 16a3 3 0 0 1 6 0M14 9h4M14 13h4',
    'scale': 'M12 3v18M6 21h12M4 7h16M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z',
    'car': 'M5 16V11l2-5h10l2 5v5M3 16h18v3H3zM7 19v2M17 19v2M5 11h14M7.5 13.5h.01M16.5 13.5h.01',
    'lock': 'M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4M12 15v2',
    'phone': 'M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z',
    'book': 'M4 4h6a2 2 0 0 1 2 2v14a2 2 0 0 0-2-2H4zM20 4h-6a2 2 0 0 0-2 2v14a2 2 0 0 1 2-2h6z',
    'check': 'M4 12l5 5L20 6',
    'x': 'M6 6l12 12M18 6L6 18',
    'chat': 'M4 5h16v11H9l-5 4z',
    'print': 'M7 9V3h10v6M7 17H4v-7h16v7h-3M7 14h10v7H7z',
}

CSS = ('.mi{display:grid;place-items:center;width:40px;height:40px;border-radius:10px;background:var(--mint);color:var(--green);flex:none}.mi svg{width:24px;height:24px}'
       '.mi.sm{width:32px;height:32px;border-radius:8px}.mi.sm svg{width:19px;height:19px}'
       '.bt-hero{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--gold);border-radius:14px;padding:16px 20px;margin:12px 0}'
       '.bt-hero p{margin:.3em 0}.bt-hero .big{font-size:1.2rem;font-weight:750}'
       '.steps{list-style:none;padding:0;margin:12px 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;counter-reset:s}'
       '.steps li{counter-increment:s;margin:0}.steps a{display:flex;gap:10px;align-items:center;min-height:56px;padding:10px 12px;background:var(--card);border:1px solid var(--line);border-radius:12px;text-decoration:none;color:var(--ink);font-weight:650}'
       '.steps a{height:100%}.steps a:hover,.steps a:focus-visible{border-color:var(--green2);text-decoration:underline}.steps a span.t::before{content:counter(s) ". ";color:var(--green2)}'
       '.step{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin:18px 0;scroll-margin-top:16px}'
       '.step>header{display:flex;gap:12px;align-items:center}.step>header h2{margin:0;font-size:1.35rem}.step .num{font-size:.85rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--soft);display:block}'
       '.say{list-style:none;padding:0;margin:10px 0}.say li{display:flex;gap:8px;align-items:flex-start;margin:6px 0;font-style:italic}.say li svg{width:20px;height:20px;flex:none;margin-top:4px;color:var(--green2)}'
       '.why{margin:8px 0 0;color:var(--soft)}'
       '.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0}'
       '.tile{display:flex;gap:12px;align-items:flex-start;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:12px}.tile h3{margin:0 0 .15em;font-size:1.02rem}.tile p{margin:0}'
       '.myths{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0}'
       '.myth{background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:12px 14px}.myth h3{margin:.3em 0;font-size:1.02rem}.myth p{margin:.3em 0}'
       '.badge{display:inline-flex;align-items:center;gap:4px;font-size:.8rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase;padding:2px 9px;border-radius:999px}'
       '.badge svg{width:14px;height:14px}.badge.heard{background:#7a1010;color:#fff}.badge.real{background:var(--green);color:#fff}.badge.say{background:var(--note);color:#4a3a08}'
       '.forms{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0}'
       '.form{background:var(--bg);border:1px solid var(--line);border-radius:14px;padding:14px 16px;scroll-margin-top:16px}.form>header{display:flex;gap:10px;align-items:center}.form h3{margin:0;font-size:1.12rem}'
       '.form dl{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;margin:10px 0;font-size:.95rem}.form dt{font-weight:700}.form dd{margin:0}'
       '.pc{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pc h4{margin:.2em 0;font-size:.95rem;display:flex;gap:6px;align-items:center}.pc h4 svg{width:18px;height:18px}'
       '.pc ul{margin:0;padding-left:1.1em;font-size:.95rem}.pc .pro h4{color:var(--green2)}.pc .con h4{color:#8a1c12}.fit{margin:8px 0 0;font-size:.95rem}'
       '.strains{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0}'
       '.strain{background:var(--bg);border:1px solid var(--line);border-radius:14px;padding:14px 16px}.strain>header{display:flex;gap:10px;align-items:center}.strain h3{margin:0;font-size:1.05rem}'
       '.strain ul{padding-left:1.1em;margin:8px 0}.strain li{margin:4px 0}'
       '.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.qcard{background:var(--card);border:2px dashed var(--green2);border-radius:14px;padding:14px 16px;break-inside:avoid}'
       '.qcard h3{margin:0 0 .4em;display:flex;gap:8px;align-items:center}.qcard table{font-size:.92rem}.qcard caption{text-align:left;font-weight:700;padding:0 0 4px}'
       '.scen{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0}'
       '.sc{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}.sc>header{display:flex;gap:10px;align-items:center}.sc h3{margin:0;font-size:1.05rem}'
       '.sc dl{margin:8px 0 0}.sc dt{font-weight:700;font-size:.9rem;color:var(--soft);text-transform:uppercase;letter-spacing:.04em;margin-top:6px}.sc dd{margin:0}'
       '.convo{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:12px 0}.convo figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}'
       '.convo figure.bad{border-top:6px solid #8a1c12}.convo figure.good{border-top:6px solid var(--green2)}.convo figcaption{font-weight:800;display:flex;gap:8px;align-items:center;margin-bottom:6px}'
       '.convo figcaption svg{width:22px;height:22px}.convo .bad figcaption{color:#8a1c12}.convo .good figcaption{color:var(--green2)}'
       '.convo dl{margin:0}.convo dt{font-weight:700;font-size:.9rem;margin-top:8px}.convo dd{margin:0}.convo .lesson{margin:10px 0 0;font-size:.95rem;color:var(--soft)}'
       '.printbtn{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 18px;border-radius:999px;border:2px solid var(--green);background:var(--card);color:var(--green);font:inherit;font-weight:700;cursor:pointer}'
       '.printbtn svg{width:20px;height:20px}.printbtn:focus-visible{outline:3px solid var(--gold);outline-offset:2px}'
       '@media (max-width:760px){.steps,.tiles,.myths,.forms,.strains,.cards,.scen,.convo{grid-template-columns:1fr}}'
       '@media (max-width:420px){.pc{grid-template-columns:1fr}}'
       '@media (prefers-color-scheme:dark){.mi{color:#a8dfbd}.pc .con h4,.convo .bad figcaption{color:#f3b0a6}.pc .pro h4,.convo .good figcaption,.steps a span.t::before,.say li svg{color:#a8dfbd}'
       '.badge.say{background:#e9b949;color:#221c08}.printbtn{color:#a8dfbd;border-color:#a8dfbd}}'
       '@media print{header.site,footer.site,.skip,.printbtn,.steps,.crumbs{display:none!important}body{background:#fff;color:#000;font-size:12pt}'
       '.step,.form,.qcard,.sc,.myth,.strain{break-inside:avoid}a{color:#000}}')

PRINT = ('<script>(function(){var b=document.getElementById("bt-print");if(b){b.hidden=false;'
         'b.addEventListener("click",function(){window.print()})}})();</script>')


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def svg(name):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="{PATHS[name]}"/></svg>')


def icon(name, small=False):
    return f'<span class="mi{" sm" if small else ""}">{svg(name)}</span>'


def page(nat, landing):
    d = load()
    esc = nat.esc
    srcs = {s['id']: s for s in d['sources']}
    order = []

    def mark(ids):
        out = []
        for sid in ids or []:
            assert sid in srcs, f'budtender-guide: unknown source {sid}'
            if sid not in order:
                order.append(sid)
            n = order.index(sid) + 1
            out.append(f'<a href="#bsource-{n}" aria-label="Source {n}">[{n}]</a>')
        return ' <span class="cites">' + ''.join(out) + '</span>' if out else ''

    steps = {s['id']: s for s in d['intake']}

    def step_open(sid, n):
        s = steps[sid]
        say = ''.join(f'<li>{svg("chat")}<span>“{esc(q)}”</span></li>' for q in s['ask'])
        return (f'<section class="step" id="{esc(sid)}" aria-labelledby="{esc(sid)}-h"><header>{icon(s["icon"])}'
                f'<div><span class="num">Step {n} of 6</span><h2 id="{esc(sid)}-h">{esc(s["title"])}</h2></div></header>'
                f'<ul class="say" aria-label="What to ask">{say}</ul>'
                f'<p>{esc(s["listen"])}</p><p class="why"><strong>Why it matters:</strong> {esc(s["why"])}</p>')

    body = ['<p class="crumbs"><a href="index.html">Home</a> › <a href="learn.html">Cannabis 101</a> › Budtender training guide</p>',
            '<h1>Budtender training guide: help every customer find the right product</h1>', nat.for_you(esc(landing['intro'])),
            f'<div class="bt-hero"><p class="big">{esc(d["promise"])}</p>'
            '<p>Six questions, in this order, get almost anyone to the right shelf. Bookmark this page, or print the quick cards for the counter.</p></div>',
            '<nav aria-label="The six-step intake"><ol class="steps">']
    for s in d['intake']:
        body.append(f'<li><a href="#{esc(s["id"])}">{icon(s["icon"], True)}<span class="t">{esc(s["title"])}</span></a></li>')
    body.append('</ol></nav><p>Also on this page: <a href="#cards">Quick cards</a> · <a href="#scenarios">Customer scenarios</a> · '
                '<a href="#example">Good and bad, side by side</a> · <a href="#rules">The rules of the counter</a> · <a href="#sources">Sources</a></p>')

    # 1. Goal
    body.append(step_open('goal', 1) + '<h3>Common goals and where they point</h3><div class="tiles">')
    for g in d['goals']:
        body.append(f'<div class="tile">{icon(g["icon"], True)}<div><h4 style="margin:0 0 .15em;font-size:1rem">{esc(g["label"])}</h4>'
                    f'<p>{esc(g["steer"])}{mark(g.get("source_ids"))}</p></div></div>')
    body.append('</div></section>')

    # 2. Requirements
    body.append(step_open('needs', 2) + '<div class="tiles">')
    for r in d['requirements']:
        body.append(f'<div class="tile">{icon(r["icon"], True)}<div><h3>{esc(r["need"])}</h3><p>{esc(r["steer"])}{mark(r.get("source_ids"))}</p></div></div>')
    body.append('</div></section>')

    # 3. Beliefs
    body.append(step_open('beliefs', 3) + '<div class="myths">')
    for m in d['notions']:
        body.append(f'<article class="myth">{icon(m["icon"], True)}'
                    f'<p><span class="badge heard">{svg("x")}What they heard</span></p><h3>“{esc(m["myth"])}”</h3>'
                    f'<p><span class="badge real">{svg("check")}What’s true</span> {esc(m["fact"])}{mark(m["source_ids"])}</p>'
                    f'<p><span class="badge say">{svg("chat")}Try saying</span> “{esc(m["say"])}”</p></article>')
    body.append('</div></section>')

    # 4. Preference
    body.append(step_open('preference', 4) + '<p>Already know their form? Jump to its card: '
                + ' · '.join(f'<a href="#form-{esc(f["id"])}">{esc(f["name"])}</a>' for f in d['forms']) + '.</p></section>')

    # 5. Forms
    body.append(step_open('forms', 5) + '<div class="forms">')
    for f in d['forms']:
        pros = ''.join(f'<li>{esc(p)}</li>' for p in f['pros'])
        cons = ''.join(f'<li>{esc(c)}</li>' for c in f['cons'])
        body.append(f'<article class="form" id="form-{esc(f["id"])}" aria-labelledby="form-{esc(f["id"])}-h"><header>{icon(f["icon"], True)}<h3 id="form-{esc(f["id"])}-h">{esc(f["name"])}</h3></header>'
                    f'<p style="margin:.5em 0 0">{esc(f["how"])}</p>'
                    f'<dl><dt>Feel it</dt><dd>{esc(f["onset"])}</dd><dt>Lasts</dt><dd>{esc(f["lasts"])}{mark(f["source_ids"])}</dd></dl>'
                    f'<div class="pc"><div class="pro"><h4>{svg("check")}Pros</h4><ul>{pros}</ul></div>'
                    f'<div class="con"><h4>{svg("x")}Cons</h4><ul>{cons}</ul></div></div>'
                    f'<p class="fit"><strong>Good fit:</strong> {esc(f["fit"])}</p></article>')
    body.append('</div><p>More on each form and how to read a label: <a href="learn.html#forms">Cannabis 101</a>.</p></section>')

    # 6. Strains
    body.append(step_open('strains', 6)
                + '<p><strong>These are what other customers and breeders report, not medical claims or guarantees.</strong> '
                  'The same name can mean different plants from different growers, so the batch label is the final word.</p><div class="strains">')
    for s in d['strains']:
        items = ''.join(f'<li><strong>{esc(e["name"])}:</strong> {esc(e["note"])}{mark(e["source_ids"])}</li>' for e in s['examples'])
        body.append(f'<article class="strain"><header>{icon(s["icon"], True)}<h3>{esc(s["goal"])}</h3></header><ul>{items}</ul>'
                    f'<p class="muted" style="margin:0">{esc(s["tip"])}{mark(s.get("tip_source_ids"))}</p></article>')
    body.append('</div><p>Look up a strain’s reported family tree in the <a href="https://ohioweed.org/ancestry.html">strain library</a>, '
                'and learn <a href="learn.html#labels">how to read a lab report</a>.</p></section>')

    # Quick cards
    rows = ''.join(f'<tr><th scope="row">{esc(t["form"])}</th><td>{esc(t["start"])}</td><td>{esc(t["peak"])}</td><td>{esc(t["lasts"])}</td></tr>' for t in d['timing'])
    body.append('<h2 id="cards">Quick cards for the counter</h2>'
                f'<p><button type="button" class="printbtn" id="bt-print" hidden>{svg("print")}Print this guide</button></p><div class="cards">'
                f'<div class="qcard" style="grid-column:1/-1"><h3>{icon("clock", True)}How fast, how long</h3><div class="scroll"><table>'
                '<caption>Typical timing by how it’s taken' + mark(['hc-using', 'hc-know']) + '</caption>'
                f'<thead><tr><th scope="col">How it’s taken</th><th scope="col">Starts</th><th scope="col">Strongest</th><th scope="col">Lasts</th></tr></thead><tbody>{rows}</tbody></table></div></div>'
                f'<div class="qcard"><h3>{icon("sprout", True)}Start low, go slow</h3><ul>'
                + ''.join(f'<li><strong>{esc(s["title"])}:</strong> {esc(s["text"])}{mark(s["source_ids"])}</li>' for s in d['start_low']) + '</ul></div>'
                f'<div class="qcard"><h3>{icon("list", True)}The six questions</h3><ol>'
                + ''.join(f'<li>{esc(s["title"])}</li>' for s in d['intake']) + '</ol>'
                '<p style="margin:0">Never make a customer name a category. Ask about the experience; you name the category.</p></div></div>')

    # Scenarios
    body.append('<h2 id="scenarios">Customer scenarios</h2><p>The same six questions, applied to the people who walk in every day.</p><div class="scen">')
    for s in d['scenarios']:
        body.append(f'<article class="sc"><header>{icon(s["icon"], True)}<h3>{esc(s["who"])}</h3></header><dl>'
                    f'<dt>They say</dt><dd>{esc(s["says"])}</dd><dt>You ask</dt><dd>{esc(s["ask"])}</dd><dt>Steer to</dt><dd>{esc(s["steer"])}</dd></dl></article>')
    body.append('</div>')

    # Example conversations
    def convo(lines):
        return '<dl>' + ''.join(f'<dt>{esc(who)}</dt><dd>{esc(text)}</dd>' for who, text in lines) + '</dl>'
    ex = d['example']
    body.append('<h2 id="example">Good and bad, side by side</h2><div class="convo">'
                f'<figure class="bad"><figcaption>{svg("x")}Not this</figcaption>{convo(ex["bad"])}'
                '<p class="lesson">The customer asked for an experience and got a quiz. They leave, or buy the wrong thing.</p></figure>'
                f'<figure class="good"><figcaption>{svg("check")}This</figcaption>{convo(ex["good"])}'
                '<p class="lesson">Goal, requirement and experience in two questions, then one clear pick with the timing explained.</p></figure></div>')

    # Rules
    body.append('<h2 id="rules">The rules of the counter</h2><div class="tiles">')
    for r in d['rules']:
        more = f' <a href="{esc(r["more"][1])}">{esc(r["more"][0])}</a>.' if r.get('more') else ''
        body.append(f'<div class="tile">{icon(r["icon"], True)}<div><h3>{esc(r["title"])}</h3><p>{esc(r["text"])}{mark(r["source_ids"])}{more}</p></div></div>')
    body.append('</div>')

    body.append('<p>More: <a href="learn.html">Cannabis 101</a> · <a href="hash-myths.html">Hash myths, busted</a> · '
                '<a href="law-buying.html">buying rules in every state</a> · <a href="law-public-use.html">where it’s legal to use</a></p>')
    body.append(f'<p class="muted">Checked {nat.long_date(d["as_of"])}. Ohio rules are quoted where named; check your own state’s rules and your store’s policies. '
                'This is training material, not medical or legal advice.</p>')
    body.append('<h2 id="sources">Sources</h2><ol class="sources">' + ''.join(
        f'<li id="bsource-{n}"><a href="{esc(srcs[sid]["url"])}" target="_blank" rel="noopener">{esc(srcs[sid]["title"])}</a> · '
        f'{"primary" if srcs[sid]["kind"] == "primary" else "secondary"} source · checked {nat.long_date(srcs[sid]["checked"])}</li>'
        for n, sid in enumerate(order, 1)) + '</ol>')
    body.append(PRINT)
    return nat.shell('Budtender training guide: help every customer find the right product',
                     'A six-question intake for budtenders: what the customer wants, their requirements, beliefs to clear up, '
                     'their preference, pros and cons of every product form, and strains customers commonly report. With quick cards and scenarios.',
                     ''.join(body), NAME, 'the budtender training guide',
                     ld=[nat.breadcrumbs([('Home', ''), ('Cannabis 101', 'learn.html')], NAME, 'Budtender training guide')], css=CSS)
