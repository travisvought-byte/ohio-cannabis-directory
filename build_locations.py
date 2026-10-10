"""Reusable physical-location view sourced from canonical locations and state packs."""
from directory_data import ROOT,load_directory,script_json
from directory_brand import brand_page
OUT=ROOT/'locations.html'
def build_page(data):
 states=[s for s in data['states'] if s['publication_status'] in ('live','pilot')]
 codes={s['code'] for s in states};evidence={e['id']:e for e in data['evidence']}
 locations=[dict(l,sources=[evidence[e] for e in l['evidence_ids']]) for l in data['locations'] if l['state'] in codes]
 return brand_page((ROOT/'templates/locations.html').read_text().replace('__DATA__',script_json(dict(states=states,locations=locations))))
def main():OUT.write_text(build_page(load_directory()));print('Built locations.html')
if __name__=='__main__':main()
