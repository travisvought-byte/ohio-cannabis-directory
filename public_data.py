"""Lazy public data loader; builders retain crawlable source/CSV fallbacks."""
import json,re
from pathlib import Path
ROOT=Path(__file__).parent
LOADER='''async function loadPublicData(path){await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));const response=await fetch(path);if(!response.ok)throw Error('Data download failed');return response.json();}\n'''
def externalize(page,expression,value,path,persist=True):
 if persist:
  target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')
 assert expression in page,expression
 page=page.replace(expression,"await loadPublicData('"+path+"')",1)
 # Wrap just the script containing the asynchronous initializer, preserving classic function scope.
 pattern=r'<script>([^<]*(?:<(?!/script>)[^<]*)*)</script>'
 def wrap(m):
  code=m.group(1)
  if 'await loadPublicData(' not in code:return m.group(0)
  return '<script>'+LOADER+'async function initializePage(){\n'+code+"\n}\ninitializePage().catch(()=>{const target=document.getElementById('results')||document.getElementById('state-results')||document.getElementById('cards');if(target)target.textContent='Data could not load. Use the source or CSV links below.';});</script>"
 return re.sub(pattern,wrap,page)
