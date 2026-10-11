"""Build a source-linked, searchable cannabis consumer knowledge hub."""
import json
from html import escape
from pathlib import Path
from directory_brand import brand_page
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'knowledge.html'

def main():
    data = json.loads((ROOT / 'data/knowledge.json').read_text())
    sources = {s['id']: s for s in data['sources']}
    ids = [s['id'] for s in data['sections']] + [i['id'] for s in data['sections'] for i in s['items']]
    assert len(ids) == len(set(ids)), 'Duplicate knowledge anchors'
    assert all(s['url'].startswith('https://') for s in sources.values())
    sections = []
    for section in data['sections']:
        cards = []
        for item in section['items']:
            assert all(s in sources for s in item['sources'])
            links = ' · '.join(f'<a href="{escape(sources[s]["url"], quote=True)}">{escape(sources[s]["title"])}</a>' for s in item['sources'])
            cards.append(f'<article id="{item["id"]}" class="topic"><h3>{escape(item["title"])}</h3><p>{escape(item["text"])}</p>' + (f'<p class="sources">Sources: {links}</p>' if links else '') + '</article>')
        sections.append(f'<section id="{section["id"]}"><h2>{escape(section["title"])}</h2><p>{escape(section["lead"])}</p><div class="grid">'+''.join(cards)+'</div></section>')
    nav = ' '.join(f'<a href="#{s["id"]}">{escape(s["title"].split(",")[0])}</a>' for s in data['sections'])
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Understand cannabis product forms, processing, definitions and labels with a practical, source-linked buying guide."><title>Cannabis knowledge | Ohio Cannabis Directory</title><style>
:root{--ink:#252525;--ink-soft:#555;--red:#a90000}*{box-sizing:border-box}body{margin:0;background:#f5f5f3;color:var(--ink);font:17px/1.6 system-ui}main{max-width:1120px;margin:auto;padding:28px}a{color:var(--red);overflow-wrap:anywhere}h1{font-size:clamp(2.2rem,6vw,3.4rem);line-height:1.1}h2{font-size:1.8rem;line-height:1.2}h3{font-size:1.2rem;margin:0 0 10px}.lead{font-size:1.2rem;max-width:800px}.tag,.sources{font-size:.85rem;color:var(--ink-soft)}nav.topics{display:flex;flex-wrap:wrap;gap:10px 20px;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}article{background:white;border:1px solid #d7d7d3;border-radius:10px;padding:22px;min-width:0}section{margin:40px 0;scroll-margin-top:20px}article:target{outline:3px solid #a90000}article{scroll-margin-top:20px}input{font:inherit;width:100%;padding:12px;border:1px solid #888;border-radius:5px}a:focus-visible,input:focus-visible{outline:3px solid #3367b1;outline-offset:3px}[hidden]{display:none!important}footer{border-top:1px solid #ccc;padding-top:20px}__VHG_CSS__@media(max-width:650px){main{padding:16px}.grid{grid-template-columns:1fr}}@media print{#search,nav.topics,label[for=search]{display:none}.grid{display:block}article{break-inside:avoid}}
</style></head><body><main>__VHG_BRAND__<a href="index.html">← Ohio Cannabis Directory</a><p class="tag">Cannabis knowledge · reviewed October 10, 2026</p><h1>Understand what you’re buying.</h1><p class="lead">Plain-language explanations of cannabis words, product forms, processing and labels. Start with a question, explore a term, or use the buying checklist.</p><nav class="topics" aria-label="Knowledge topics">__NAV__</nav><label for="search">Find a term or product</label><input id="search" type="search" placeholder="Try rosin, THC, gummies or lab report"><p id="count" role="status" aria-live="polite"></p><noscript>All topics are available below without JavaScript.</noscript>__SECTIONS__<footer><p>Use this guide for product literacy, not a personal treatment or dosing plan. Canadian sources explain general product concepts; Ohio requirements are linked separately. Producer pages illustrate their processes and are not endorsements.</p><p>Explore genetics and strain history in the <a href="ancestry.html">100-strain library</a>, or <a href="locations.html">find Ohio dispensary locations</a>. Check the package and current rules for the product you are considering.</p><p><a href="data/knowledge.json" download>Download the knowledge source records</a> · <a href="__UPDATE_URL__">Suggest a correction</a></p></footer></main><script>
const input=document.getElementById('search'),cards=[...document.querySelectorAll('.topic')],sections=[...document.querySelectorAll('main>section')];
function filter(){const q=input.value.trim().toLowerCase();let n=0;for(const card of cards){card.hidden=!card.textContent.toLowerCase().includes(q);if(!card.hidden)n++;}for(const section of sections)section.hidden=![...section.querySelectorAll('.topic')].some(c=>!c.hidden);document.getElementById('count').textContent=q?(n?n+' matching topics':'No matching topics. Try another word.'):'Browse '+cards.length+' explanations and buying tips.';}
input.addEventListener('input',filter);document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>{input.value='';filter();}));filter();
</script></body></html>'''.replace('__NAV__',nav).replace('__SECTIONS__',''.join(sections))
    OUT.write_text(brand_page(page))
    print('Built cannabis knowledge hub:', len(ids)-len(data['sections']), 'topics')

if __name__ == '__main__':
    main()
