"""Reusable physical-location view sourced from canonical locations and state packs."""
from directory_data import ROOT,load_directory,script_json
from directory_brand import brand_page
from public_data import externalize
OUT=ROOT/'locations.html'
def build_page(data):
 states=[s for s in data['states'] if s['publication_status'] in ('live','pilot')]
 codes={s['code'] for s in states};evidence={e['id']:e for e in data['evidence']}
 locations=[dict(l,sources=[evidence[e] for e in l['evidence_ids']]) for l in data['locations'] if l['state'] in codes]
 payload=dict(states=states,locations=locations)
 page=(ROOT/'templates/locations.html').read_text().replace('<script id="location-data" type="application/json">__DATA__</script>','').replace("JSON.parse(document.getElementById('location-data').textContent)",script_json(payload))
 return brand_page(externalize(page,script_json(payload),payload,'data/public-locations.json'))
def main():OUT.write_text(build_page(load_directory()));print('Built locations.html')
if __name__=='__main__':main()
