#!/usr/bin/env python3
"""Build a searchable public view of the existing documented relationships."""
import csv
import html
from pathlib import Path
from build_directory import TEMPLATE as DIRECTORY_TEMPLATE
from directory_data import ROOT, RELEASE, load_records, load_relationship_records, relationship_id, script_json
from directory_brand import brand_page

OUT = ROOT / 'relationships.html'

def name_key(name):
    return name.removeprefix('! ').strip().casefold()

def main():
    organizations = load_records()
    lookup = {}
    for r in organizations:
        # Exact names and explicit parenthetical aliases only; no fuzzy identity matching.
        for name in (r['Organization / Business Name'], r['Organization / Business Name'].split(' (')[0]):
            lookup.setdefault(name_key(name), []).append(r)
    def match(name):
        candidates = {r['Record ID']: r for r in lookup.get(name_key(name), [])}
        return next(iter(candidates.values())) if len(candidates) == 1 else None
    source = load_relationship_records()
    records = []
    for r in source:
        a, b = match(r['Organization A']), match(r['Organization B / Counterparty'])
        item = dict(id=relationship_id(r), a=r['Organization A'], b=r['Organization B / Counterparty'],
                    kind=r['Relationship Type'], geography=r['Project / Geography'], status=r['Status'],
                    summary=r['Evidence Summary'], sources=r['Directory Row Source(s) — row-level context'],
                    provenance=r['Pass / Provenance'], a_id=a['Record ID'] if a else '', b_id=b['Record ID'] if b else '')
        item['_s'] = ' '.join(str(v) for v in item.values()).lower() + ' ' + ' '.join(
            r['Organization / Business Name'].removeprefix('! ').lower() for r in (a, b) if r)
        records.append(item)
    records.sort(key=lambda r:(r['a'].casefold(),r['b'].casefold(),r['kind'].casefold()))
    style = DIRECTORY_TEMPLATE.split('<style>')[1].split('</style>')[0]
    page = brand_page(TEMPLATE.replace('__STYLE__', style)).replace('__DATA__', script_json(records))
    page = page.replace('__VERSION__', RELEASE['version']).replace('__DATE__', RELEASE['released_on']).replace('__COUNT__', str(len(records)))
    OUT.write_text(page)
    print(f'wrote {OUT} — {len(records)} relationships')

TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Who Works With Whom? | Ohio Cannabis Ecosystem Directory</title>
<meta name="description" content="Explore 60 documented cannabis business relationships, including banking, technology, construction and brand partnerships.">
<link rel="canonical" href="https://travisvought-byte.github.io/ohio-cannabis-directory/relationships.html">
<style>__STYLE__</style></head><body>
<header><div class="wrap masthead">__VHG_BRAND__<p><a href="index.html">← Ohio Cannabis Ecosystem Directory</a></p>
<h1>Who works with whom?</h1><p class="standfirst">__COUNT__ documented relationships. Explore partners, projects and the evidence behind them. Status is shown as recorded in the source research.</p>
<div class="searchbox"><input id="q" type="search" aria-label="Search relationships" placeholder="Company, partner or service…"><button id="clear" aria-label="Clear search" type="button">×</button></div>
<div class="actions"><button class="btn" id="share">Copy search link</button><a class="btn" href="b2b-relationships.csv" download>Download relationships CSV</a><a class="btn" href="__RELATIONSHIP_UPDATE_URL__">Email a relationship update</a><span id="share-status" role="status" aria-live="polite"></span></div>
<p id="tally" role="status" aria-live="polite"></p></div></header>
<main class="wrap" id="results"></main>
<noscript><p class="wrap">Read the <a href="b2b-relationships.csv">relationship CSV</a> for all documented relationships and evidence.</p></noscript>
<footer class="wrap"><p>A Veteran Home Guardians resource, compiled and maintained by Travis Vought. Release v__VERSION__ · __DATE__. <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</p><p class="update-contact">Additions and corrections: <a href="__RELATIONSHIP_UPDATE_URL__">__VHG_EMAIL__</a>.</p></footer>
<script>
const RELATIONSHIPS=__DATA__;
const $=id=>document.getElementById(id),esc=s=>String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const safeURL=s=>{try{const u=new URL(s);return ['https:','http:'].includes(u.protocol)?u.href:''}catch{return ''}};
let selected='';
function organizationLink(name,id){return '<a href="index.html?'+(id?'org='+encodeURIComponent(id):'q='+encodeURIComponent(name))+'">'+esc(name)+'</a>'}
function filteredRelationships(q,id=''){const terms=q.toLowerCase().trim().split(/\s+/).filter(Boolean);return RELATIONSHIPS.filter(r=>(!id||r.id===id)&&terms.every(t=>r._s.includes(t)))}
function searchURL(){const u=new URL(location.href);u.search='';u.hash='';if($('q').value.trim())u.searchParams.set('q',$('q').value.trim());if(selected)u.searchParams.set('relationship',selected);return u}
function loadSearch(){const p=new URLSearchParams(location.search);$('q').value=p.get('q')||'';selected=RELATIONSHIPS.some(r=>r.id===p.get('relationship'))?p.get('relationship'):''}
function render(){const rows=filteredRelationships($('q').value,selected);$('tally').textContent=rows.length+' of '+RELATIONSHIPS.length+' relationships';$('clear').style.display=$('q').value||selected?'block':'none';history.replaceState(null,'',searchURL());$('results').innerHTML=rows.map(r=>'<article id="'+esc(r.id)+'"><h2>'+organizationLink(r.a,r.a_id)+' &amp; '+organizationLink(r.b,r.b_id)+'</h2><p class="keys">'+esc(r.kind)+'</p><p class="line">'+esc(r.geography)+' · '+esc(r.status)+'</p><p>'+esc(r.summary)+'</p><p class="line"><a href="?relationship='+encodeURIComponent(r.id)+'">Link to this relationship</a></p><details><summary>Evidence and research history</summary><div class="prov">'+r.sources.split('|').map(s=>s.trim()).filter(Boolean).map(s=>safeURL(s)?'<p><a href="'+esc(safeURL(s))+'" target="_blank" rel="noopener">'+esc(s)+'</a></p>':'<p>'+esc(s)+'</p>').join('')+'<p>'+esc(r.provenance)+'</p></div></details></article>').join('')||'<p class="empty">No documented relationships match. Try a company name or a broader service.</p>'}
$('q').addEventListener('input',()=>{selected='';render()});$('clear').onclick=()=>{selected='';$('q').value='';render();$('q').focus()};
$('share').onclick=async()=>{try{await navigator.clipboard.writeText(searchURL().href);$('share-status').textContent='Link copied.'}catch{$('share-status').textContent='Copy the page address to share this search.'}};
window.addEventListener('popstate',()=>{loadSearch();render()});loadSearch();render();
</script><script data-goatcounter="https://travisvought.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script></body></html>'''

if __name__ == '__main__':
    main()
