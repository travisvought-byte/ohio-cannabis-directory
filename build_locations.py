"""Reusable physical-location view sourced from canonical locations and state packs."""
from directory_data import ROOT,load_directory,script_json
from directory_brand import brand_page
from public_data import externalize
OUT=ROOT/'locations.html'
def build_page(data):
 # Referral offices are not dispensaries. Offer only states with licensed or regulator-listed location records.
 listed=lambda l:bool(l.get('license',{}).get('number') or l.get('regulator_listing'))
 location_states={l['state'] for l in data['locations'] if listed(l)}
 states=[s for s in data['states'] if s['publication_status'] in ('live','pilot') and s['code'] in location_states]
 codes={s['code'] for s in states};evidence={e['id']:e for e in data['evidence']}
 locations=[dict(l,sources=[evidence[e] for e in l['evidence_ids']]) for l in data['locations'] if l['state'] in codes and listed(l)]
 for location in locations:
  if any(s['claim']=='location-geocode' for s in location['sources']):location['approximate_point']=True
 organizations={o['id']:o for o in data['organizations']}
 for location in locations:
  linked=organizations.get(location.get('contact',{}).get('directory_organization_id'))
  if linked and linked.get('scope')=='public' and 'legacy_record' in linked:
   location['directory_listing']={'id':linked['id'],'name':linked['name']}
 payload=dict(states=states,locations=locations)
 page=(ROOT/'templates/locations.html').read_text().replace('<script id="location-data" type="application/json">__DATA__</script>','').replace("JSON.parse(document.getElementById('location-data').textContent)",script_json(payload))
 return brand_page(externalize(page,script_json(payload),payload,'data/public-locations.json'))
def main():OUT.write_text(build_page(load_directory()));print('Built locations.html')
if __name__=='__main__':main()
