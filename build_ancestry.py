"""Build the searchable, offline ancestry pilot and spreadsheet export."""
import csv
import html
import json
from pathlib import Path
from strain_ancestry import DATA, ROOT, analyze
OUT = ROOT / 'ancestry.html'

def main():
    data = json.loads(DATA.read_text())
    report = analyze(data)
    if report['errors']:
        raise ValueError(report['errors'])
    payload = json.dumps({'data': data, 'report': report}, ensure_ascii=False).replace('<', '\\u003c')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cannabis ancestry library</title>
<style>body{font:17px/1.6 system-ui;background:#f5f5f3;color:#242424;margin:0}main{max-width:1000px;margin:auto;padding:24px}a{color:#a00}input,select{font:inherit;padding:12px;box-sizing:border-box;max-width:100%}input{width:100%}article,.notice{background:white;border:1px solid #ccc;border-radius:10px;padding:20px;margin:18px 0}.parents{display:flex;flex-wrap:wrap;gap:12px}.node{border:1px solid #aaa;border-radius:8px;padding:10px;flex:1;min-width:140px}.muted{color:#555}button{font:inherit;background:#a00;color:white;border:0;border-radius:5px;padding:10px;cursor:pointer}h1{line-height:1.2}h2{margin-top:0}.tag{font-size:14px;color:#555}summary{cursor:pointer}@media print{input,select,button{display:none}}</style>
<main><a href="index.html">← Ohio Cannabis Directory</a><h1>Cannabis ancestry library</h1><p>Follow the parents. Compare breeder lines. See where the evidence stops.</p><div class="notice"><strong>Research pilot</strong><p>Breeder-reported ancestry, not DNA verification. Same-name strains stay separate. Parent labels with unknown breeder or cut are unresolved references, not verified shared ancestors. This catalog does not indicate Ohio availability.</p><a href="data/strains/ancestry.csv" download>Download ancestry CSV</a> · <a href="data/strains/ancestry.json" download>Download source records</a></div>
<label for="q">Search strain, alias, breeder or parent</label><input id="q" type="search" placeholder="Try Blue Dream or Haze"><label for="mode">Show</label> <select id="mode"><option value="all">All records</option><option value="review">Parentage needs review</option><option value="lines">Breeder lines</option></select><p id="count" aria-live="polite"></p><div id="results"></div><h2>Identity decisions</h2><div id="decisions"></div></main><script id="model" type="application/json">__DATA__</script>
<script>
const {data,report}=JSON.parse(document.getElementById('model').textContent),byId=Object.fromEntries(data.strains.map(s=>[s.id,s])),sources=Object.fromEntries(data.sources.map(s=>[s.id,s]));
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const label=s=>escape(s.name)+' · '+escape(s.breeder||'breeder/cut unresolved');
const needs=new Set(report.parentage_review.map(r=>r.child_id));
function tree(id,seen=new Set(),depth=0){if(seen.has(id)||depth>=8)return '<p>Further ancestry not expanded.</p>';let next=new Set(seen);next.add(id);let claims=data.claims.filter(c=>c.child_id===id&&c.status!=='superseded');if(!claims.length)return '<p class="muted">No sourced parentage recorded.</p>';return claims.map(c=>'<section><p class="tag">'+escape(c.status)+' · parent direction unspecified</p><div class="parents">'+c.parent_ids.map(p=>'<div class="node"><strong>'+label(byId[p])+'</strong>'+tree(p,next,depth+1)+'</div>').join('')+'</div><p>'+escape(c.notes)+'</p><p>'+c.source_ids.map(id=>'<a href="'+escape(sources[id].url)+'" target="_blank" rel="noopener">'+escape(sources[id].publisher)+'</a> · checked '+escape(sources[id].reviewed_on)).join(' / ')+'</p></section>').join('');}
function render(){const q=document.getElementById('q').value.toLowerCase(),mode=document.getElementById('mode').value;const matches=data.strains.filter(s=>{const claims=data.claims.filter(c=>c.child_id===s.id);const text=[s.name,s.breeder,...s.aliases,...claims.flatMap(c=>c.parent_ids.map(p=>byId[p].name))].join(' ').toLowerCase();return text.includes(q)&&(mode!=='review'||needs.has(s.id))&&(mode!=='lines'||s.kind!=='unresolved-parent');});document.getElementById('count').textContent=matches.length+' records';document.getElementById('results').innerHTML=matches.map(s=>'<article id="'+escape(s.id)+'"><h2>'+escape(s.name)+'</h2><p>'+escape(s.breeder||'Unresolved parent reference')+' · '+escape(s.kind)+'</p>'+(needs.has(s.id)?'<p><strong>Parentage specificity needs review</strong> — alternatives are shown separately.</p>':'')+tree(s.id)+'</article>').join('')||'<p>No matching records.</p>';}
document.getElementById('decisions').innerHTML=data.resolutions.map(r=>'<article><strong>'+escape(r.decision)+'</strong><p>'+r.strain_ids.map(id=>label(byId[id])).join('<br>')+'</p><p>'+escape(r.reason)+'</p></article>').join('');document.getElementById('q').addEventListener('input',render);document.getElementById('mode').addEventListener('change',render);render();
</script></html>'''.replace('__DATA__', payload)
    OUT.write_text(page)
    with (ROOT / 'data/strains/ancestry.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['claim_id','child_id','strain','breeder','parent_1','parent_2','status','source_urls','reviewed_on','notes'])
        strains = {s['id']:s for s in data['strains']}
        sources = {s['id']:s for s in data['sources']}
        for c in data['claims']:
            child = strains[c['child_id']]
            writer.writerow([c['id'],child['id'],child['name'],child['breeder'],*c['parent_ids'],c['status'],' | '.join(sources[s]['url'] for s in c['source_ids']),data['reviewed_on'],c['notes']])
    print('Built ancestry.html and ancestry.csv')
if __name__ == '__main__':
    main()
