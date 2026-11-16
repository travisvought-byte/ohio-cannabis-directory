"""Build the national section: one home page and one page per state and DC.

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
TAGLINE = 'Cannabis law, directories and help for every state'
ORIGIN = os.environ.get('NATIONAL_ORIGIN', '').rstrip('/')
REPO = 'https://github.com/travisvought-byte/ohio-cannabis-directory'
LEVELS = {'starter': 'Starter', 'partial': 'Partial', 'broad': 'Broad'}
PACK_LABEL = {'live': 'Full state guide', 'pilot': 'Pilot state guide'}

CSS = '''
:root{--ink:#16221e;--soft:#55605c;--line:#cfd6d9;--link:#215b76;--bg:#f6f7f8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}
a{color:var(--link);text-underline-offset:3px}header.site,main,footer.site{max-width:1040px;margin:0 auto;padding:16px 20px}
header.site{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 18px;border-bottom:1px solid var(--line)}
header.site .name{font-size:1.25rem;font-weight:800;text-decoration:none;color:var(--ink)}header.site .tag{color:var(--soft);font-size:.9rem}
header.site nav{margin-left:auto;display:flex;flex-wrap:wrap;gap:0 16px}header.site nav a,footer.site a{display:inline-flex;align-items:center;min-height:44px}
h1{font-size:clamp(26px,4vw,38px);line-height:1.15;margin:.6em 0 .3em}h2{margin:1.6em 0 .4em;font-size:1.4rem}h3{margin:1.2em 0 .4em;font-size:1.1rem}
p{max-width:70ch}.muted{color:var(--soft);font-size:.9rem}.crumbs{font-size:.9rem;margin:8px 0 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:8px 0;min-width:0}.card h3,.card h4{margin:0 0 6px;font-size:1rem;line-height:1.35}.card p{margin:.25rem 0}
.chip{display:inline-block;border:1px solid;border-radius:999px;padding:0 10px;font-size:.82rem;font-weight:700;line-height:1.7;white-space:nowrap}
.chip.allowed,.chip.positive,.chip.broad{background:#e7f3eb;border-color:#2e7d4f;color:#1d5a37}.chip.medical-only,.chip.limited,.chip.varies-locally,.chip.partial,.chip.starter{background:#fff4dc;border-color:#b8860b;color:#664a00}
.chip.not-permitted,.chip.negative{background:#fbeaea;border-color:#a90000;color:#7a0000}.chip.not-reviewed,.chip.not-started{background:#f0f0f0;border-color:#888;color:#444}
.level{display:inline-block;font-size:.78rem;font-weight:700;border-radius:4px;padding:0 6px;background:#eef3fb;color:#24426e}.level.compilation{background:#fff4dc;color:#664a00}
.short{font-weight:650}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,290px),1fr));gap:8px;list-style:none;padding:0;margin:12px 0}
.grid li{background:#fff;border:1px solid var(--line);border-radius:8px;padding:9px 12px;min-width:0}.grid li[hidden]{display:none}.grid .state{font-weight:700;font-size:1.05rem;display:inline-flex;min-height:36px;align-items:center}
.grid .chips{display:flex;flex-wrap:wrap;gap:4px 6px;font-size:.85rem;align-items:center}.grid .meta{font-size:.82rem;color:var(--soft);margin:4px 0 0}
select{font:inherit;min-height:44px;padding:6px 9px;border:1px solid #888;border-radius:5px;background:#fff}
table{border-collapse:collapse;width:100%;background:#fff}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}.scroll{overflow-x:auto}
.sources{font-size:.9rem;padding-left:1.6em}.sources li{margin:.3em 0;overflow-wrap:anywhere}.cites a{font-size:.82rem;margin-left:2px}
footer.site{border-top:1px solid var(--line);margin-top:32px;font-size:.9rem;color:var(--soft)}footer.site nav{display:flex;flex-wrap:wrap;gap:0 18px}
@media print{header.site nav,footer.site nav,select,label{display:none}}
'''

FILTER_JS = ('<script>(function(){var f=document.getElementById("state-filter");if(!f)return;'
             'f.addEventListener("change",function(){document.querySelectorAll("#states li").forEach(function(li){'
             'li.hidden=!!f.value&&li.getAttribute("data-adult")!==f.value&&li.getAttribute("data-guide")!==f.value})})})();</script>')


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


def correction_url(place):
    body = 'Page or state:\r\n\r\nAddition or correction:\r\n\r\nWebsite or source:\r\n\r\n'
    return 'mailto:' + EMAIL + '?' + urlencode({'subject': f'{SITE_NAME}: correction for {place}', 'body': body}, quote_via=quote)


def shell(title, description, body, name, place):
    head = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            f'<title>{esc(title)} | {esc(SITE_NAME)}</title>',
            f'<meta name="description" content="{esc(description)}">',
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(SITE_NAME)}">',
            f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}">']
    if ORIGIN:
        href = ORIGIN + '/' + ('' if name == 'index.html' else name)
        head.append(f'<link rel="canonical" href="{esc(href)}"><meta property="og:url" content="{esc(href)}">')
    else:
        head.append('<meta name="robots" content="noindex,follow">')
    head.append(f'<style>{CSS}</style></head><body>')
    top = (f'<header class="site"><a class="name" href="index.html">{esc(SITE_NAME)}</a><span class="tag">{esc(TAGLINE)}</span>'
           '<nav aria-label="Primary"><a href="index.html#states">All states</a><a href="index.html#national">Across every state</a>'
           '<a href="index.html#progress">Build progress</a></nav></header>')
    foot = ('<footer class="site"><nav aria-label="More">'
            f'<a href="{esc(correction_url(place))}">Suggest a correction</a>'
            f'<a href="{REPO}#readme">Methods &amp; sources</a>'
            f'<a href="{REPO}/blob/main/architecture/STATE_COMPLETION_STANDARD.md">State completion standard</a>'
            f'<a href="{OHIO_HOME}/">OhioWeed.org</a></nav>'
            '<p>Summaries of the cited sources, each with the date it was checked. Not legal advice. A missing answer means not yet reviewed, '
            'never that something is prohibited. Free to use under CC BY 4.0. Created and maintained by Travis Vought, shared in support of Veteran Home Guardians.</p></footer>')
    return ''.join(head) + top + '<main>' + body + '</main>' + foot + '</body></html>\n'


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
                out.append(f'<article class="card" data-question="{esc(q["id"])}"><h4>{esc(q["question"])}</h4>{note}'
                           f'<p>{chip(perm, "not-reviewed")} <span class="muted">No reviewed source yet. This does not mean it is prohibited.</span></p></article>')
                continue
            level = evidence_level(a, sources)
            effective = f' · in effect {long_date(a["effective_on"])}' if a.get('effective_on') else ''
            out.append(f'<article class="card" data-question="{esc(q["id"])}"><h4>{esc(q["question"])}</h4>{note}'
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
                   '<a href="index.html#national">National resources that cover every state</a> are available now.</p>')
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


def state_page(perm, score, directory, code, answers, sources):
    name = perm['jurisdictions'][code]
    state_answers = answers.get(code, {})
    cites = Cites(sources)
    card = score['states'].get(code)
    pack = next((s for s in directory['states'] if s['code'] == code), None)
    adult, medical = state_answers['adult-use'], state_answers['medical']
    body = [f'<p class="crumbs"><a href="index.html#states">All states</a> › {esc(name)}</p>',
            f'<h1>{esc(name)} cannabis guide</h1>',
            f'<p>Adult use {chip(perm, adult["status"])} <span class="short">{esc(adult["short"])}</span><br>'
            f'Medical program {chip(perm, medical["status"])} <span class="short">{esc(medical["short"])}</span></p>']
    link = perm['official_links'].get(code)
    if link:
        s = sources[link['source_id']]
        body.append(f'<p>Official state site: <a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a> '
                    f'<span class="muted">({esc(s["publisher"])}, checked {long_date(s["retrieved_on"])})</span></p>')
    else:
        body.append('<p>Official state site: <span class="muted">not yet reviewed</span></p>')
    if code == 'OH':
        body.append(f'<p><strong>Ohio’s full guide lives at <a href="{OHIO_HOME}/">OhioWeed.org</a></strong>: business directory, dispensary finder, record clearing, advocacy and more.</p>')
    body.append(law_section(perm, code, state_answers, cites, sources))
    body.append(pathway_section(code, name, directory['pathways'], card, pack))
    body.append(cites.render())
    answered = len(state_answers)
    description = f'{name} cannabis law in plain language: {answered} of {len(perm["questions"])} questions answered from named sources, plus directory and local help.'
    return shell(f'{name} cannabis guide', description, ''.join(body), slug(name) + '.html', name)


def national_section(perm, cites):
    def item(i):
        return (f'<article class="card" data-national="{esc(i["id"])}"><p class="muted" style="margin:0;font-weight:700;text-transform:uppercase;font-size:.78rem">{esc(i["need"])}</p>'
                f'<h3><a href="{esc(i["url"])}" target="_blank" rel="noopener">{esc(i["title"])}</a></h3><p>{esc(i["text"])}</p>'
                f'<p class="muted">Checked {long_date(i["reviewed_on"])} {cites.mark(i["source_ids"])}</p></article>')
    consumer = [i for i in perm['national'] if i.get('audience', 'consumer') == 'consumer']
    business = [i for i in perm['national'] if i.get('audience', 'consumer') == 'business']
    out = ['<h2 id="national">Across every state</h2><p>Federal rules, national help lines and organizations that cover every state. '
           'Each links to the agency or organization that runs it. A listing is not an endorsement; advocacy groups are named as such.</p>']
    out += [item(i) for i in consumer]
    if business:
        out.append('<h3 id="national-business">For cannabis businesses</h3>')
        out += [item(i) for i in business]
    return ''.join(out)


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


def home_page(perm, score, directory, answers, sources):
    names = perm['jurisdictions']
    total = len(perm['questions'])
    cites = Cites(sources)
    body = [f'<h1>{esc(TAGLINE)}</h1>',
            f'<p>Pick a state for its cannabis law in plain language, each answer traced to a named source and the date it was checked. '
            f'As of {long_date(perm["as_of"])}.</p>',
            '<h2 id="states">All 50 states and DC</h2>',
            '<label for="state-filter">Show</label> <select id="state-filter"><option value="">All states and DC</option>'
            '<option value="allowed">Adult use allowed</option><option value="medical-only">Medical patients only</option>'
            '<option value="not-permitted">Not permitted</option><option value="guide">States with a directory guide</option></select>',
            '<ul class="grid" id="states">']
    for code in sorted(names, key=lambda c: names[c]):
        a = answers[code]
        card = score['states'].get(code)
        guide = f' · {esc(PACK_LABEL[card["publication_status"]])}' if card else ''
        body.append(f'<li data-state="{esc(code)}" data-adult="{esc(a["adult-use"]["status"])}" data-guide="{"guide" if card else ""}">'
                    f'<a class="state" href="{slug(names[code])}.html">{esc(names[code])}</a>'
                    f'<span class="chips">Adult use {chip(perm, a["adult-use"]["status"])} Medical {chip(perm, a["medical"]["status"])}</span>'
                    f'<p class="meta">{len(a)} of {total} questions answered{guide}</p></li>')
    body.append('</ul>')
    body.append(national_section(perm, cites))
    body.append(progress_section(perm, score, directory, answers))
    body.append(cites.render())
    body.append(FILTER_JS)
    description = 'Cannabis law for all 50 states and DC in plain language, each answer traced to a named source, with state directories built on the Ohio template.'
    return shell(TAGLINE, description, ''.join(body), 'index.html', 'the national pages')


def pages():
    """Every generated page as {file name: text}."""
    perm, score, directory = load()
    sources = {s['id']: s for s in perm['sources']}
    answers = answers_by_state(perm)
    out = {'index.html': home_page(perm, score, directory, answers, sources)}
    for code, name in perm['jurisdictions'].items():
        out[slug(name) + '.html'] = state_page(perm, score, directory, code, answers, sources)
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
    print(f'Built national/: home page and {len(built) - 1} state pages')


if __name__ == '__main__':
    main()
