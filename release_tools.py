"""Synchronize release metadata and rebuild public pages."""
import json,re,importlib,sys
from pathlib import Path
ROOT=Path(__file__).parent

def release(version):
 old=json.loads((ROOT/'release.json').read_text())
 (ROOT/'release.json').write_text(json.dumps({'version':version,'released_on':'2026-10-11'},indent=2)+'\n')
 for name in ['.zenodo.json','zenodo.json']:
  p=ROOT/name;d=json.loads(p.read_text());d['version']=version;d['publication_date']='2026-10-11';p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 p=ROOT/'CITATION.cff';s=p.read_text();s=re.sub(r"version: '[^']+'",f"version: '{version}'",s);s=re.sub(r"date-released: '[^']+'","date-released: '2026-10-11'",s);p.write_text(s)
 p=ROOT/'README.md';s=p.read_text().replace('Current site release:** '+old['version'],'Current site release:** '+version);p.write_text(s)
 for name in ['directory','intake','relationships','resources','seeds','state','locations','knowledge','ancestry','tools']:
  importlib.import_module('build_'+name).main()
 if (ROOT/'build_home.py').exists():importlib.import_module('build_home').main()
if __name__=='__main__':release(sys.argv[1])
