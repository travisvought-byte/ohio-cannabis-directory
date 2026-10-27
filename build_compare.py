"""Build compare.html: Ohio's cannabis laws beside other states, and lessons from other markets.

Canonical data: data/state-comparison.json (validated by validate_comparison.py).
"""
import html
import json
import re
from datetime import date
from pathlib import Path

from directory_brand import brand_page
from validate_comparison import validate
from policy_portal import render as render_policy_portal

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'compare.html'
DATA = ROOT / 'data/state-comparison.json'

KIND_LABEL = {'statute': 'Law', 'regulator': 'Regulator', 'government': 'Government', 'news': 'News report', 'research': 'Research'}
STATUS_LABEL = {
    'absent': ('Ohio does not share this condition', 'ok'),
    'partial': ('Ohio partly shares this condition', 'part'),
    'present': ('Ohio shares this condition', 'risk'),
    'unknown': ('Not yet known for Ohio', 'part'),
}
DESCRIPTION = ("Compare cannabis policy across states, learn from other markets, "
               "and propose changes to your own state lawmakers. Facts are sourced and dated.")

CSS = '''
*{box-sizing:border-box}body{margin:0;background:#f5f5f3;color:#252525;font:17px/1.6 system-ui}main{max-width:1080px;margin:auto;padding:28px}
a{color:#a90000;overflow-wrap:anywhere}h1{font-size:clamp(2rem,5vw,3.1rem);line-height:1.12;margin:.4rem 0}h2{line-height:1.25;margin-top:0}h3{font-size:1.1rem;line-height:1.3;margin:0 0 .4rem}
.lead{font-size:1.15rem}.review,.muted,.cites{font-size:.86rem;color:#555}.cites a{text-decoration:none;font-weight:600}
section{margin:36px 0;scroll-margin-top:20px}.card{background:#fff;border:1px solid #ccc;border-radius:10px;padding:22px;min-width:0}
.states{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:12px}.state{background:#fff;border:1px solid #ccc;border-radius:10px;padding:16px;min-width:0}
.state.home{border:2px solid #a90000}.state[hidden],.topic[hidden],.coverage-item[hidden]{display:none!important}.coverage-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:14px}.coverage-item{display:grid;gap:3px}.coverage-item span{font-size:.85rem;color:#555}.coverage-track{height:9px;background:#e4e4e4;border-radius:99px;overflow:hidden}.coverage-fill{height:100%;background:#a90000}#compare-topic-filter{width:100%;padding:10px;border:1px solid #888;border-radius:6px;font:inherit}.state h4{margin:0 0 .3rem;font-size:1rem}.state p{margin:.3rem 0}.state.missing{background:#fafafa;color:#666}
.topic{margin:22px 0}.topic>p{margin:.2rem 0}
.lesson h3{font-size:1.25rem}.lesson h4{font-size:1rem;margin:20px 0 6px}ul.facts{padding-left:1.2rem;margin:.2rem 0}ul.facts li{margin:.35rem 0}
.check{border-left:4px solid #888;padding:6px 0 6px 14px;margin:10px 0}.check.ok{border-color:#2e7d4f}.check.part{border-color:#b8860b}.check.risk{border-color:#a90000}
.status{font-weight:650}
.assessment{background:#fff8e6;border:1px solid #e3c977;border-radius:10px;padding:16px 18px;margin:12px 0}.assessment .tag{display:inline-block;font-size:.78rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#7a5a00}
.estimate{margin:10px 0}.estimate strong{display:block}.badge{display:inline-block;border:1px solid #7a5a00;border-radius:999px;padding:0 10px;font-size:.85rem;margin:.2rem 0}
fieldset{border:1px solid #ccc;border-radius:8px;margin:14px 0;padding:10px 14px}legend{font-weight:650}.ask{display:flex;gap:12px;align-items:flex-start;margin:10px 0;font-weight:400}.ask input{width:22px;height:22px;min-height:22px;flex:none;margin-top:3px}
label{display:block;font-weight:600;margin:12px 0 5px}input[type=text],textarea{width:100%;max-width:100%;font:inherit;padding:10px;border:1px solid #888;border-radius:5px}textarea{resize:vertical;min-height:300px}
.fields{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
.button,button{display:inline-flex;align-items:center;justify-content:center;border:1px solid #a90000;border-radius:6px;padding:10px 16px;background:#a90000;color:#fff;font:inherit;text-decoration:none;cursor:pointer}.secondary{background:#fff;color:#a90000}
ol.sources{padding-left:1.4rem;font-size:.92rem}ol.sources li{margin:.4rem 0}
a:focus-visible,button:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid #3367b1;outline-offset:3px}
__VHG_CSS__
body .cites a,body ol.sources a,body .jump a{display:inline;min-height:0}body .cites a{padding:2px 3px}ol.sources .meta{display:block;font-size:.86rem;color:#555}
@media(max-width:800px){.states{grid-template-columns:1fr}}
@media(max-width:650px){main{padding:16px}.card{padding:16px}.fields{grid-template-columns:1fr}}
@media print{.actions,fieldset,.fields,label[for^=letter]{display:none!important}body{background:#fff}}
'''

SCRIPT = r'''
<script>
(function(){
  var lessons=JSON.parse(document.getElementById('letter-data').textContent);
  function val(id){var el=document.getElementById(id);return el?el.value.trim():''}
  function build(key){
    var L=lessons[key],form=document.getElementById('form-'+key);
    var chosen=[].slice.call(form.querySelectorAll('input[name="ask"]:checked')).map(function(i){return L.asks[i.value]});
    var to=val('to-'+key)||'Representative / Senator [Name]',town=val('town-'+key)||'[your Ohio town]',name=val('name-'+key)||'[Your name]';
    var body=chosen.length?chosen.join('\n\n'):'[Keep the requests you agree with and delete the rest.]\n\n'+Object.keys(L.asks).map(function(k){return L.asks[k]}).join('\n\n');
    document.getElementById('letter-'+key).value='Dear '+to+',\n\nI live in '+town+', Ohio. '+L.opening+'\n\n'+body+'\n\n'+L.closing+'\n\nThank you,\n'+name;
  }
  Object.keys(lessons).forEach(function(key){
    var form=document.getElementById('form-'+key),edited=false,status=document.getElementById('status-'+key);
    function refresh(e){if(e.target.id==='letter-'+key)return;if(edited){status.textContent='Your edits are kept. Press \u201cStart over\u201d to rebuild the letter from your choices.';return}build(key)}
    form.addEventListener('input',function(e){if(e.target.id==='letter-'+key){edited=true;return}refresh(e)});
    form.addEventListener('change',refresh);
    document.getElementById('rebuild-'+key).addEventListener('click',function(){edited=false;build(key);status.textContent='Letter rebuilt from your choices.'});
    document.getElementById('copy-'+key).addEventListener('click',function(){
      var box=document.getElementById('letter-'+key),status=document.getElementById('status-'+key);
      function done(){status.textContent='Letter copied. Paste it into your lawmaker’s contact form or email.'}
      if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(box.value).then(done,function(){box.select();document.execCommand('copy');done()})}
      else{box.select();document.execCommand('copy');done()}
    });
    build(key);
  });
})();
</script>
'''


def esc(value):
    return html.escape(value, quote=True)


def long_date(value):
    d = date.fromisoformat(value)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def default_letter(letter):
    """Letter shown before any choice is made, and to visitors without JavaScript."""
    asks = '\n\n'.join(a['text'] for a in letter['asks'])
    return ('Dear Representative / Senator [Name],\n\nI live in [your Ohio town], Ohio. ' + letter['opening'] +
            '\n\n[Keep the requests you agree with and delete the rest.]\n\n' + asks +
            '\n\n' + letter['closing'] + '\n\nThank you,\n[Your name]')


def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    validate(data)
    states, home = data['states'], data['home_state']
    order = {s['id']: n for n, s in enumerate(data['sources'], 1)}

    def cites(ids):
        links = ''.join(f'<a href="#source-{order[i]}" aria-label="Source {order[i]}">[{order[i]}]</a>' for i in ids)
        return f'<span class="cites">{links}</span>'

    out = ['<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>Compare cannabis policy and propose changes in your state</title>',
           f'<meta name="description" content="{esc(DESCRIPTION)}">',
           '<style>' + CSS + '</style></head><body><main>__VHG_BRAND__',
           f'<p class="review">State comparison · facts checked {long_date(data["as_of"])}</p>',
           '<h1>Compare states. Shape your cannabis policy.</h1>',
           '<p class="lead">Compare legal approaches, examine what happened in other markets, and write to your own lawmakers about the changes you want.</p>',
           '<p class="muted">Every fact links to its source and carries the date it was checked. Assessments are the directory’s analysis, labeled as such, with a stated likelihood, confidence level and reasoning. They are reviewed on a schedule and may change as evidence changes.</p>',
           '<p class="jump"><a href="#policy-portal">Propose a change</a> · <a href="#laws">Laws side by side</a> · <a href="#lessons">Lessons from other markets</a> · <a href="#sources">Sources</a></p>']

    out.append(render_policy_portal(data))
    out.append('<section id="laws"><h2>Laws side by side</h2><p>Choose which reviewed states appear in the comparison. Unreviewed topics are marked explicitly.</p><fieldset class="compare-state-controls"><legend>States to display</legend>' + ''.join(f'<label class="ask" style="display:inline-flex;margin-right:18px"><input type="checkbox" class="compare-state-toggle" value="{esc(code)}" checked> {esc(name)}</label>' for code,name in states.items()) + '</fieldset>')
    shown = [home] + [s for s in states if s != home]
    total_topics = len(data['topics'])
    out.append('<div class="card" aria-label="Reviewed coverage by state"><h3>Research coverage</h3><p class="muted">Number of policy topics with source-linked reviews. This measures coverage, not how favorable a state's laws are.</p><div class="coverage-grid">')
    for code in shown:
        reviewed = sum(any(e['state'] == code for e in topic['entries']) for topic in data['topics'])
        pct = round(100 * reviewed / total_topics) if total_topics else 0
        out.append(f'<div class="coverage-item" data-state="{esc(code)}"><strong>{esc(states[code])}</strong><span>{reviewed} of {total_topics} topics</span><div class="coverage-track" role="progressbar" aria-label="{esc(states[code])} reviewed topics" aria-valuenow="{reviewed}" aria-valuemin="0" aria-valuemax="{total_topics}"><div class="coverage-fill" style="width:{pct}%"></div></div></div>')
    out.append('</div></div>')
    out.append('<label for="compare-topic-filter">Find a policy topic</label><input type="search" id="compare-topic-filter" placeholder="e.g. licensing, cultivation" aria-controls="laws">')
    for topic in data['topics']:
        entries = {e['state']: e for e in topic['entries']}
        out.append(f'<div class="topic" data-topic-search="{esc(topic["label"] + " " + topic["question"])}" id="topic-{esc(topic["id"])}"><h3>{esc(topic["label"])}</h3><p class="muted">{esc(topic["question"])}</p><div class="states">')
        for code in shown:
            e = entries.get(code)
            cls = 'state home' if code == home else 'state'
            if not e:
                out.append(f'<div data-state="{esc(code)}" class="{cls} missing"><h4>{esc(states[code])}</h4><p>Not yet reviewed.</p></div>')
                continue
            effective = f' · in effect {long_date(e["effective_on"])}' if e.get('effective_on') else ''
            out.append(f'<div data-state="{esc(code)}" class="{cls}"><h4>{esc(states[code])}</h4><p>{esc(e["summary"])}</p>'
                       f'<p class="muted">{esc(e["citation"])}{effective} · checked {long_date(e["reviewed_on"])} {cites(e["source_ids"])}</p></div>')
        out.append('</div></div>')
    out.append('''<script>(function(){const controls=document.querySelectorAll('.compare-state-toggle');function update(){const chosen=new Set(Array.from(controls).filter(c=>c.checked).map(c=>c.value));document.querySelectorAll('#laws .state[data-state]').forEach(card=>{card.hidden=!chosen.has(card.dataset.state)});document.querySelectorAll('#laws .coverage-item[data-state]').forEach(item=>{item.hidden=!chosen.has(item.dataset.state)});document.querySelectorAll('#laws .states').forEach(grid=>{grid.style.gridTemplateColumns='repeat(auto-fit,minmax(min(100%,260px),1fr))'});}controls.forEach(c=>c.addEventListener('change',update));const filter=document.getElementById('compare-topic-filter');filter.addEventListener('input',()=>{const q=filter.value.trim().toLowerCase();document.querySelectorAll('#laws .topic').forEach(item=>{item.hidden=!item.dataset.topicSearch.toLowerCase().includes(q)})});update();})();</script></section>''')

    out.append('<section id="lessons"><h2>Market lessons: Michigan, with an Ohio assessment</h2><p>What happened elsewhere, why it happened, and whether Ohio has the same conditions.</p>')
    letters = {}
    for lesson in data['lessons']:
        key = lesson['id']
        example = states[lesson['example_state']]
        out.append(f'<article class="card lesson" id="{esc(key)}"><h3>{esc(lesson["title"])}</h3><p>{esc(lesson["summary"])}</p>')
        out.append(f'<h4>What happened in {esc(example)}</h4><ul class="facts">')
        out += [f'<li>{esc(i["text"])} {cites(i["source_ids"])}</li>' for i in lesson['what_happened']]
        out.append('</ul><h4>Why it happened</h4><ul class="facts">')
        out += [f'<li>{esc(c["text"])} {cites(c["source_ids"])}</li>' for c in lesson['conditions']]
        out.append('</ul><h4>Does Ohio share these conditions?</h4>')
        conditions = {c['id']: c for c in lesson['conditions']}
        for chk in lesson['ohio_check']:
            label, cls = STATUS_LABEL[chk['status']]
            out.append(f'<div class="check {cls}"><p class="status">{esc(conditions[chk["condition_id"]]["label"])}: {esc(label.lower().replace('ohio', 'Ohio'))}</p>'
                       f'<p>{esc(chk["finding"])} {cites(chk["source_ids"])}</p></div>')
        out.append('<h4>Ohio so far</h4><ul class="facts">')
        out += [f'<li>{esc(i["text"])} {cites(i["source_ids"])}</li>' for i in lesson['ohio_trend']]
        out.append(f'</ul><div class="assessment"><span class="tag">Directory assessment · analysis, not fact</span>')
        for a in lesson['assessments']:
            out.append(f'<div class="estimate"><strong>{esc(a["judgment"])}</strong><span class="badge">{esc(a["likelihood"].capitalize())} · {esc(a["confidence"])} confidence</span><p>{esc(a["basis"])}</p></div>')
        out.append(f'<p class="muted">Assessed {long_date(lesson["assessed_on"])} · next review by {long_date(lesson["review_by"])}</p></div>')
        out.append('<h4>Signals to watch</h4><ul class="facts">' + ''.join(f'<li>{esc(w)}</li>' for w in lesson['watch']) + '</ul>')
        out.append('<h4>How other states responded</h4><ul class="facts">')
        out += [f'<li><strong>{esc(states[r["state"]])}:</strong> {esc(r["text"])} {cites(r["source_ids"])}</li>' for r in lesson['responses']]
        out.append('</ul>')
        letter = lesson['letter']
        letters[key] = {'opening': letter['opening'], 'closing': letter['closing'], 'asks': {a['id']: a['text'] for a in letter['asks']}}
        out.append(f'<h4 id="write-{esc(key)}">Write to your Ohio lawmakers</h4><p>Choose what you want to ask for. The letter is yours to edit; it states your view, not the directory’s.</p>'
                   f'<form id="form-{esc(key)}" onsubmit="return false"><fieldset><legend>What should Ohio do?</legend>')
        out += [f'<label class="ask"><input type="checkbox" name="ask" value="{esc(a["id"])}" data-track="compare-ask-{esc(a["id"])}">{esc(a["label"])}</label>' for a in letter['asks']]
        out.append(f'</fieldset><div class="fields"><div><label for="to-{esc(key)}">Lawmaker’s name (optional)</label><input type="text" id="to-{esc(key)}" maxlength="160" placeholder="Representative / Senator [Name]"></div>'
                   f'<div><label for="town-{esc(key)}">Your Ohio town (optional)</label><input type="text" id="town-{esc(key)}" maxlength="160" autocomplete="address-level2"></div>'
                   f'<div><label for="name-{esc(key)}">Your name (optional)</label><input type="text" id="name-{esc(key)}" maxlength="160" autocomplete="name"></div></div>'
                   f'<label for="letter-{esc(key)}">Your letter: edit before sending</label><textarea id="letter-{esc(key)}" rows="14" spellcheck="true">{esc(default_letter(letter))}</textarea>'
                   f'<div class="actions"><button type="button" id="copy-{esc(key)}" data-track="compare-copy-letter">Copy letter</button>'
                   f'<button type="button" class="secondary" id="rebuild-{esc(key)}">Start over</button>'
                   f'<a class="button secondary" href="https://legislature.ohio.gov/members/district-maps" target="_blank" rel="noopener" data-track="compare-find-lawmakers">Find my representative and senator</a>'
                   f'<a class="button secondary" href="lawmakers.html" data-track="compare-browse-lawmakers">Browse lawmakers and votes</a></div>'
                   f'<p id="status-{esc(key)}" role="status" aria-live="polite"></p></form></article>')
    out.append('<p class="muted">More issues, such as illicit-market persistence, lab testing integrity, intoxicating hemp and local opt-outs, will be added as they are researched and sourced. <a href="advocacy.html">See the Ohio advocacy guide</a>.</p></section>')

    out.append('<section id="sources"><h2>Sources</h2><ol class="sources">')
    for s in data['sources']:
        out.append(f'<li id="source-{order[s["id"]]}"><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a><span class="meta">{esc(s["publisher"])} · {KIND_LABEL[s["kind"]]} · retrieved {long_date(s["retrieved_on"])}</span></li>')
    out.append('</ol><p class="muted">Data: <a href="data/state-comparison.json">state-comparison.json</a> (CC BY 4.0). Spot an error or a newer source? Use “Suggest a correction” below.</p></section>')

    out.append('<script type="application/json" id="letter-data">' + json.dumps(letters, ensure_ascii=False).replace('</', '<\\/') + '</script>')
    out.append(SCRIPT + '</main></body></html>\n')
    page = '\n'.join(out)
    built = brand_page(page)
    built = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="' + esc(DESCRIPTION) + '">', built)
    OUT.write_text(built, encoding='utf-8')
    print(f'Built compare.html: {len(data["topics"])} law topics, {len(data["lessons"])} market lessons')


if __name__ == '__main__':
    main()
