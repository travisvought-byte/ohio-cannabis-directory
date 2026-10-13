"""Synchronize release metadata and rebuild public pages."""
import json,re,importlib,sys
from datetime import date
from pathlib import Path
ROOT=Path(__file__).parent

def release(version,released_on=None):
 released_on=released_on or date.today().isoformat()
 published=date.fromisoformat(released_on)
 (ROOT/'release.json').write_text(json.dumps({'version':version,'released_on':released_on},indent=2)+'\n')
 for name in ['.zenodo.json','zenodo.json']:
  p=ROOT/name;d=json.loads(p.read_text());d['version']=version;d['publication_date']=released_on;p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 p=ROOT/'CITATION.cff';s=p.read_text();s=re.sub(r"version: '[^']+'",f"version: '{version}'",s);s=re.sub(r"date-released: '[^']+'",f"date-released: '{released_on}'",s);p.write_text(s)
 p=ROOT/'README.md';s=p.read_text();s=re.sub(r'\*\*Current site release:\*\* [^\n]+',f'**Current site release:** {version} · {published.strftime("%B %-d, %Y")}.',s);p.write_text(s)
 for name in ['directory','intake','relationships','resources','seeds','state','locations','knowledge','ancestry','tools','advocacy','lawmakers']:
  importlib.import_module('build_'+name).main()
 if (ROOT/'build_home.py').exists():importlib.import_module('build_home').main()
 importlib.import_module('build_review_queue').main()
if __name__=='__main__':release(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)
