"""Render the national layer and the consumer permissions table for compare.html.

Canonical data: data/state-permissions.json (validated by validate_permissions.py).
Order on the page is top-down: what applies in every state, one state in detail,
then every state at a glance. The default state is rendered server-side so the
answers read without JavaScript. The state switcher loads data/public-permissions.json
after first paint (written by build_compare.py), which keeps compare.html under the
page-size budget as answers are added.
"""
import html
import json
from datetime import date

from public_data import LOADER
from validate_permissions import evidence_level

HOME = 'OH'
DATA_PATH = 'data/public-permissions.json'
LEVEL_TEXT = {
    'official': 'Official source',
    'mixed': 'Official source and national compilation',
    'compilation': 'National compilation: confirm with the state',
}
KIND_LABEL = {'statute': 'Law', 'regulator': 'Regulator', 'government': 'Government',
              'organization': 'Organization', 'compilation': 'National compilation', 'news': 'News report'}

CSS = '''
.chip{display:inline-block;border:1px solid;border-radius:999px;padding:0 10px;font-size:.82rem;font-weight:700;line-height:1.7;white-space:nowrap}
.chip.allowed{background:#e7f3eb;border-color:#2e7d4f;color:#1d5a37}.chip.medical-only,.chip.limited,.chip.varies-locally{background:#fff4dc;border-color:#b8860b;color:#664a00}
.chip.not-permitted{background:#fbeaea;border-color:#a90000;color:#7a0000}.chip.not-reviewed{background:#f0f0f0;border-color:#888;color:#444}
.national-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:12px}.national-item{background:#fff;border:1px solid #ccc;border-radius:10px;padding:14px 16px;min-width:0}
.national-more summary{cursor:pointer;color:#a90000;font-size:.9rem}.national-more p{margin:.35rem 0}
.national-item .need{font-size:.78rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#555;margin:0}.national-item h3{margin:.2rem 0 .3rem}.national-item p{margin:.2rem 0}
.perm-controls{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;align-items:end}.perm-controls select,.perm-controls input{width:100%;font:inherit;padding:9px;border:1px solid #888;border-radius:5px;background:#fff}
.perm-official{margin:10px 0 0}.perm-group h3{margin:24px 0 8px;font-size:1.15rem}.perm-row{background:#fff;border:1px solid #ccc;border-radius:10px;padding:12px 16px 8px;margin:8px 0;min-width:0}
.perm-row h4{margin:0 0 6px;font-size:1rem;line-height:1.35}.perm-cells{display:grid;gap:10px}.perm-cells.two{grid-template-columns:repeat(2,minmax(0,1fr))}.perm-cell{min-width:0}.perm-cell>p{margin:.15rem 0}
.perm-state{font-size:.82rem;font-weight:700;color:#555}.perm-cells:not(.two) .perm-state{display:none}.perm-short{font-weight:650}
.perm-cell details{margin:2px 0 0}.perm-cell details>summary{padding:2px 0}.perm-cell summary{cursor:pointer;color:#a90000;font-size:.9rem}.perm-cell details p{margin:.35rem 0}.perm-row[hidden],.perm-group[hidden],.glance li[hidden]{display:none!important}
.level{display:inline-block;font-size:.78rem;font-weight:700;border-radius:4px;padding:0 6px;background:#eef3fb;color:#24426e}.level.compilation{background:#fff4dc;color:#664a00}.level.mixed{background:#eef3fb;color:#24426e}
.glance{list-style:none;padding:0;margin:12px 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr));gap:6px}.glance li{background:#fff;border:1px solid #ccc;border-radius:8px;padding:7px 12px;min-width:0}
.glance li{display:flex;flex-wrap:wrap;align-items:center;gap:2px 8px}.glance strong{flex:1 1 auto}.glance .chips{display:flex;flex-wrap:wrap;gap:4px 6px;font-size:.85rem;align-items:center;flex-basis:100%}
body .glance .glance-pick{background:none;border:0;color:#a90000;padding:3px 0;min-height:24px;font-size:.88rem;text-decoration:underline;cursor:pointer}
.legend{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:.88rem;margin:8px 0}
@media(max-width:800px){.perm-controls{grid-template-columns:1fr}}
@media(max-width:700px){.perm-cells.two{grid-template-columns:1fr}.perm-cells.two .perm-cell+.perm-cell{border-top:1px solid #ddd;padding-top:8px}}
'''


def esc(value):
    return html.escape(str(value), quote=True)


def long_date(value):
    d = date.fromisoformat(value)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def numbering(data):
    return {s['id']: n for n, s in enumerate(data['sources'], 1)}


def payload(data):
    """Everything the browser needs, keyed for lookup; no personal data."""
    order = numbering(data)
    sources = {s['id']: s for s in data['sources']}
    answers = {}
    for a in data['answers']:
        item = {k: a[k] for k in ('status', 'short', 'detail', 'citation', 'reviewed_on')}
        if a.get('effective_on'):
            item['effective_on'] = a['effective_on']
        item['cites'] = [order[sid] for sid in a['source_ids']]
        item['level'] = evidence_level(a, sources)
        answers.setdefault(a['state'], {})[a['question']] = item
    official = {}
    for code, link in data['official_links'].items():
        s = sources[link['source_id']]
        official[code] = {'title': s['title'], 'publisher': s['publisher'], 'url': s['url'], 'checked': s['retrieved_on']}
    return {'home': HOME, 'statuses': data['statuses'], 'groups': data['groups'], 'questions': data['questions'],
            'jurisdictions': data['jurisdictions'], 'official': official, 'answers': answers, 'levels': LEVEL_TEXT}


def chip(data, status):
    return f'<span class="chip {esc(status)}">{esc(data["statuses"][status])}</span>'


def cites(numbers):
    return '<span class="cites">' + ''.join(
        f'<a href="#psource-{n}" aria-label="State table source {n}">[s{n}]</a>' for n in numbers) + '</span>'


def cell(data, code, answer):
    head = f'<p class="perm-state">{esc(data["jurisdictions"][code])}</p>'
    if not answer:
        return (f'<div class="perm-cell" data-state="{esc(code)}">{head}<p>{chip(data, "not-reviewed")} '
                '<span class="muted">No reviewed source yet.</span></p></div>')
    effective = f' · in effect {long_date(answer["effective_on"])}' if answer.get('effective_on') else ''
    return (f'<div class="perm-cell" data-state="{esc(code)}">{head}<p>{chip(data, answer["status"])} '
            f'<span class="perm-short">{esc(answer["short"])}</span></p>'
            f'<details><summary>Details and source</summary><p>{esc(answer["detail"])}</p>'
            f'<p class="muted">{esc(answer["citation"])}{effective} · checked {long_date(answer["reviewed_on"])} {cites(answer["cites"])}</p>'
            f'<p><span class="level {esc(answer["level"])}">{esc(LEVEL_TEXT[answer["level"]])}</span></p></details></div>')


def official_line(data, info, codes):
    parts = []
    for code in codes:
        name = esc(data['jurisdictions'][code])
        link = info['official'].get(code)
        if link:
            parts.append(f'{name} official site: <a href="{esc(link["url"])}" target="_blank" rel="noopener">{esc(link["title"])}</a> '
                         f'<span class="muted">({esc(link["publisher"])}, checked {long_date(link["checked"])})</span>')
        else:
            parts.append(f'{name} official site: <span class="muted">not yet reviewed</span>')
    return '<br>'.join(parts)


def table(data, info, codes):
    out = []
    for group in data['groups']:
        rows = [q for q in data['questions'] if q['group'] == group['id']]
        out.append(f'<div class="perm-group" data-group="{esc(group["id"])}"><h3>{esc(group["label"])}</h3>')
        for q in rows:
            search = f'{q["question"]} {q.get("keywords", "")} {group["label"]}'.lower()
            cls = 'perm-cells two' if len(codes) > 1 else 'perm-cells'
            out.append(f'<article class="perm-row" data-question="{esc(q["id"])}" data-search="{esc(search)}"><h4>{esc(q["question"])}</h4><div class="{cls}">')
            out += [cell(data, code, info['answers'].get(code, {}).get(q['id'])) for code in codes]
            out.append('</div></article>')
        out.append('</div>')
    return ''.join(out)


def national_item(item, order):
    return (f'<article class="national-item" data-national="{esc(item["id"])}" data-audience="{esc(item.get("audience", "consumer"))}">'
            f'<p class="need">{esc(item["need"])}</p>'
            f'<h3><a href="{esc(item["url"])}" target="_blank" rel="noopener">{esc(item["title"])}</a></h3>'
            f'<details class="national-more"><summary>What it covers</summary><p>{esc(item["text"])}</p>'
            f'<p class="muted">Checked {long_date(item["reviewed_on"])} {cites(order[s] for s in item["source_ids"])}</p></details></article>')


def render_national(data):
    order = numbering(data)
    consumer = [i for i in data['national'] if i.get('audience', 'consumer') == 'consumer']
    business = [i for i in data['national'] if i.get('audience', 'consumer') == 'business']
    out = ['<section id="national" aria-labelledby="national-title"><h2 id="national-title">Across every state</h2>',
           '<p>Federal rules, national help lines and organizations that cover every state. Each links to the agency or organization that runs it. '
           'A listing is not an endorsement; advocacy groups are named as such.</p><div class="national-grid">']
    out += [national_item(item, order) for item in consumer]
    out.append('</div>')
    if business:
        out.append('<h3 id="national-business">For cannabis businesses</h3><div class="national-grid">')
        out += [national_item(item, order) for item in business]
        out.append('</div>')
    out.append('</section>')
    return ''.join(out)


def render_permissions(data):
    info = payload(data)
    names = data['jurisdictions']
    ordered = sorted(names, key=lambda c: names[c])
    options = ''.join(f'<option value="{esc(c)}"{" selected" if c == HOME else ""}>{esc(names[c])}</option>' for c in ordered)
    compare = '<option value="">No comparison</option>' + ''.join(f'<option value="{esc(c)}">{esc(names[c])}</option>' for c in ordered)
    legend = ''.join(chip(data, s) for s in data['statuses'])
    return ''.join([
        '<section id="permissions" aria-labelledby="permissions-title"><h2 id="permissions-title">What you can do in one state</h2>',
        '<p>Pick a state, or two to compare. Every state answers the same questions. Open “Details and source” to see the law or agency behind an answer and the date it was checked.</p>',
        '<div class="perm-controls"><div><label for="perm-state">State</label>',
        f'<select id="perm-state" data-track="permissions-state">{options}</select></div>',
        '<div><label for="perm-compare">Compare with (optional)</label>',
        f'<select id="perm-compare" data-track="permissions-compare">{compare}</select></div>',
        '<div><label for="perm-filter">Find a question</label><input type="search" id="perm-filter" placeholder="e.g. grow, driving" aria-controls="perm-table"></div></div>',
        f'<p class="perm-official muted" id="perm-official">{official_line(data, info, [HOME])}</p>',
        f'<div class="legend" aria-label="Answer labels">{legend}</div>',
        f'<div id="perm-table" aria-live="polite">{table(data, info, [HOME])}</div>',
        '<p class="muted">“Not yet reviewed” means no source has been checked for that answer. It never means the activity is prohibited. '
        'Answers marked “National compilation” come from national lists that cover every state; confirm them with the state before relying on them.</p>',
        '</section>',
    ])


def render_glance(data):
    info = payload(data)
    names = data['jurisdictions']
    out = ['<section id="all-states" aria-labelledby="all-states-title"><h2 id="all-states-title">All 50 states and DC at a glance</h2>',
           '<p>The two top-level answers for every jurisdiction. The first chip is adult use (21 and older, no medical card); the second is the state medical program.</p>',
           '<label for="glance-filter">Show</label><select id="glance-filter" data-track="permissions-glance-filter">'
           '<option value="">All states and DC</option><option value="allowed">Adult use allowed</option>'
           '<option value="medical-only">Medical patients only</option><option value="not-permitted">Not permitted</option></select>',
           '<ul class="glance">']
    for code in sorted(names, key=lambda c: names[c]):
        answers = info['answers'].get(code, {})
        adult, medical = answers.get('adult-use'), answers.get('medical')
        out.append(f'<li data-state="{esc(code)}" data-adult="{esc(adult["status"])}"><strong>{esc(names[code])}</strong>'
                   f'<button type="button" class="glance-pick" data-state="{esc(code)}" aria-label="All answers for {esc(names[code])}" hidden>All answers</button>'
                   f'<span class="chips">Adult use {chip(data, adult["status"])} Medical {chip(data, medical["status"])}</span></li>')
    out.append('</ul></section>')
    return ''.join(out)


def render_sources(data):
    out = ['<h3>Sources for the state-by-state answers and national items</h3><ol class="sources">']
    for n, s in enumerate(data['sources'], 1):
        out.append(f'<li id="psource-{n}"><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a>'
                   f'<span class="meta">{esc(s["publisher"])} · {KIND_LABEL[s["kind"]]} · retrieved {long_date(s["retrieved_on"])}</span></li>')
    out.append('</ol><p class="muted">Data: <a href="https://github.com/travisvought-byte/ohio-cannabis-directory/blob/main/data/state-permissions.json" target="_blank" rel="noopener">state-permissions.json</a> (CC BY 4.0).</p>')
    return ''.join(out)


# The national items and the 50-state list work without the state data; the switcher waits for it.
PAGE_SCRIPT = r'''
<script>
(function(){
 if(window.matchMedia&&matchMedia('(min-width: 800px)').matches)document.querySelectorAll('.national-more').forEach(function(d){d.open=true});
 var gf=document.getElementById('glance-filter');
 gf.addEventListener('change',function(){document.querySelectorAll('.glance li').forEach(function(li){li.hidden=!!gf.value&&li.getAttribute('data-adult')!==gf.value})});
})();
</script>'''

SCRIPT = r'''
<script>
__LOADER__(async function(){
 var D=await loadPublicData('__DATA_PATH__');
 var M=['January','February','March','April','May','June','July','August','September','October','November','December'];
 function e(v){return String(v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
 function d(v){var p=v.split('-');return M[+p[1]-1]+' '+(+p[2])+', '+p[0]}
 function chip(s){return '<span class="chip '+e(s)+'">'+e(D.statuses[s])+'</span>'}
 function cites(ns){return '<span class="cites">'+ns.map(function(n){return '<a href="#psource-'+n+'" aria-label="State table source '+n+'">[s'+n+']</a>'}).join('')+'</span>'}
 function cell(code,a){
  var head='<p class="perm-state">'+e(D.jurisdictions[code])+'</p>';
  if(!a)return '<div class="perm-cell" data-state="'+e(code)+'">'+head+'<p>'+chip('not-reviewed')+' <span class="muted">No reviewed source yet.</span></p></div>';
  var eff=a.effective_on?' · in effect '+d(a.effective_on):'';
  return '<div class="perm-cell" data-state="'+e(code)+'">'+head+'<p>'+chip(a.status)+' <span class="perm-short">'+e(a.short)+'</span></p>'+
   '<details><summary>Details and source</summary><p>'+e(a.detail)+'</p><p class="muted">'+e(a.citation)+eff+' · checked '+d(a.reviewed_on)+' '+cites(a.cites)+'</p>'+
   '<p><span class="level '+e(a.level)+'">'+e(D.levels[a.level])+'</span></p></details></div>';
 }
 function official(codes){return codes.map(function(code){var l=D.official[code],n=e(D.jurisdictions[code]);
  return l?n+' official site: <a href="'+e(l.url)+'" target="_blank" rel="noopener">'+e(l.title)+'</a> <span class="muted">('+e(l.publisher)+', checked '+d(l.checked)+')</span>':n+' official site: <span class="muted">not yet reviewed</span>'}).join('<br>')}
 var state=document.getElementById('perm-state'),compare=document.getElementById('perm-compare'),filter=document.getElementById('perm-filter');
 function codes(){var c=[state.value];if(compare.value&&compare.value!==state.value)c.push(compare.value);return c}
 function applyFilter(){var t=filter.value.trim().toLowerCase();document.querySelectorAll('#perm-table .perm-group').forEach(function(g){var any=false;
  g.querySelectorAll('.perm-row').forEach(function(r){var show=!t||r.getAttribute('data-search').indexOf(t)>-1;r.hidden=!show;if(show)any=true});g.hidden=!any})}
 function render(){var c=codes(),out='';
  D.groups.forEach(function(g){out+='<div class="perm-group" data-group="'+e(g.id)+'"><h3>'+e(g.label)+'</h3>';
   D.questions.filter(function(q){return q.group===g.id}).forEach(function(q){var s=(q.question+' '+(q.keywords||'')+' '+g.label).toLowerCase();
    out+='<article class="perm-row" data-question="'+e(q.id)+'" data-search="'+e(s)+'"><h4>'+e(q.question)+'</h4><div class="'+(c.length>1?'perm-cells two':'perm-cells')+'">'+
     c.map(function(code){return cell(code,(D.answers[code]||{})[q.id])}).join('')+'</div></article>'});out+='</div>'});
  document.getElementById('perm-table').innerHTML=out;document.getElementById('perm-official').innerHTML=official(c);applyFilter();
  var p=new URLSearchParams(location.search);p.set('state',c[0]);if(c[1])p.set('compare',c[1]);else p.delete('compare');
  history.replaceState(null,'',location.pathname+'?'+p.toString()+location.hash)}
 var q=new URLSearchParams(location.search);
 if(D.jurisdictions[q.get('state')])state.value=q.get('state');
 if(D.jurisdictions[q.get('compare')])compare.value=q.get('compare');
 state.addEventListener('change',render);compare.addEventListener('change',render);filter.addEventListener('input',applyFilter);
 if(state.value!==D.home||compare.value)render();
 document.querySelectorAll('.glance-pick').forEach(function(b){b.hidden=false;b.addEventListener('click',function(){state.value=b.getAttribute('data-state');render();
  document.getElementById('permissions').scrollIntoView();state.focus({preventScroll:true})})});
 document.getElementById('permissions').setAttribute('data-ready','');
})().catch(function(){var n=document.getElementById('perm-official');
 if(n)n.insertAdjacentHTML('afterend','<p class="muted" role="status">The state switcher could not load. This table shows Ohio; every state is in the list below.</p>')});
</script>'''


def render_script(data):
    """The page loads the state data from DATA_PATH after first paint, like the other large pages."""
    return PAGE_SCRIPT + SCRIPT.replace('__LOADER__', LOADER).replace('__DATA_PATH__', DATA_PATH)


def public_json(data):
    return json.dumps(payload(data), ensure_ascii=False, separators=(',', ':')) + '\n'
