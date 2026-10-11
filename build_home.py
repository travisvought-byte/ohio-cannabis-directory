"""Build the task-focused front door; old directory URLs redirect intact."""
from pathlib import Path
import json,html
from directory_brand import brand_page
from directory_data import load_records,load_event_routes,RELEASE,RELEASE_DATE
ROOT=Path(__file__).parent
OUT=ROOT/'index.html'
def main():
 records=load_records();strains=json.loads((ROOT/'data/strains/ancestry.json').read_text())['strains']
 search=[{'name':r['Organization / Business Name'].lstrip('! '),'text':' '.join([r['Organization / Business Name'],r['Capabilities / Keywords'],r['Service Area']]).lower(),'url':'directory.html?org='+r['Record ID'],'kind':'Business'} for r in records if not r['Category'].startswith('Out of scope')]
 search += [{'name':s['name'],'text':' '.join([s['name'],*s.get('aliases',[]),s.get('lineage_text','')]).lower(),'url':'ancestry.html?strain='+s['id'],'kind':'Strain'} for s in strains if s.get('catalog') or s.get('popular')]
 (ROOT/'data/home-search.json').write_text(json.dumps(search,ensure_ascii=False,separators=(',',':')))
 events=[e for e in load_event_routes() if e['date']>=RELEASE_DATE.isoformat()][:2]
 event_html=''.join('<p><a href="'+html.escape(e['url'],quote=True)+'">'+html.escape(e['name'])+'</a> · '+e['date']+'</p>' for e in events) or '<p>No confirmed upcoming dates.</p>'
 body='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Home | Ohio Cannabis Directory</title><style>body{margin:0;background:#faf9f6;color:#252525;font:16px/1.6 system-ui}main{max-width:950px;margin:auto;padding:24px}a{color:#a90000}h1{font-size:clamp(30px,5vw,46px);line-height:1.15}.tasks{display:grid;grid-template-columns:1fr 1fr;gap:12px}.tasks a{display:flex;align-items:center;min-height:90px;padding:16px;border:1px solid #ccc;border-radius:8px;background:white;font-weight:650;text-decoration:none}input{width:100%;box-sizing:border-box;padding:12px;font:inherit}.events{border-top:1px solid #ccc;margin-top:24px}.events p{margin:8px 0}__VHG_CSS__@media(max-width:500px){main{padding:16px}.tasks a{min-height:70px;padding:12px}h1{margin:18px 0 10px}}</style><script>if(location.search||location.hash){location.replace('directory.html'+location.search+location.hash);}</script></head><body><main>__VHG_BRAND__<h1>Ohio Cannabis Directory</h1><p>Find Ohio cannabis businesses, dispensaries and plain-language guides, each traced to a source.</p><label for="home-search">Search businesses, capabilities and strains</label><input id="home-search" type="search" placeholder="Try banking, gummies or Blue Dream" autocomplete="off"><p id="search-status" role="status"></p><ul id="home-results"></ul><div class="tasks"><a href="locations.html" data-track="home-dispensary">Find a dispensary</a><a href="buyer-guide.html" data-track="home-plan">Plan a dispensary visit</a><a href="resources.html#business" data-track="home-business">Find a business service</a><a href="assessment.html" data-track="home-assessment">Check my business’s readiness</a></div><section class="events"><h2>Upcoming events</h2>__EVENTS__<a href="resources.html#community">See all events</a></section><noscript><p><a href="directory.html">Browse the business directory</a> · <a href="ancestry.html">Browse strains</a></p></noscript></main><script>
let catalog=null;const input=document.getElementById('home-search'),results=document.getElementById('home-results'),status=document.getElementById('search-status');
async function search(){const query=input.value.trim().toLowerCase();results.replaceChildren();if(!query){status.textContent='';return;}try{catalog=catalog||await fetch('data/home-search.json').then(r=>{if(!r.ok)throw Error();return r.json();});if(input.value.trim().toLowerCase()!==query)return;const matches=catalog.filter(r=>query.split(/\\s+/).every(t=>r.text.includes(t)));status.textContent=matches.length?matches.length+' matches. Showing up to 8.':'No matches. Try a broader term.';for(const r of matches.slice(0,8)){const li=document.createElement('li'),a=document.createElement('a');a.href=r.url;a.textContent=r.name+' · '+r.kind;li.append(a);results.append(li);}}catch(_){status.textContent='Search unavailable. Use the task links or browse the business directory.';}}
input.addEventListener('input',search);
</script></body></html>'''.replace('__EVENTS__',event_html)
 # The footer carries the current release without adding another front-page box.
 body=brand_page(body).replace('Project roles</a></p>', 'Project roles</a> · release v'+RELEASE['version']+'</p>')
 OUT.write_text(body)
if __name__=='__main__':main()
