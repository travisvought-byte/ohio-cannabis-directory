"""One shared renderer: state configuration and canonical service records are its inputs."""
import json,html
from pathlib import Path
from directory_data import ROOT,load_directory,script_json
from directory_brand import brand_page
from public_data import externalize
OUT=ROOT/'state.html'

def build_page(data,persist=False):
 public_states=[s for s in data['states'] if s['publication_status'] in ('live','pilot')]
 orgs={o['id']:o for o in data['organizations']};evidence={e['id']:e for e in data['evidence']};cards=[]
 for s in data['services']:
  org=orgs[s['organization_id']]
  if org.get('scope') in ('reference-only','withdrawn'):continue
  # Seed catalog entries have a dedicated origin; avoid repeated generic referral cards.
  if s.get('origin')=='consumer-resource' and 'seeds' in s['pathway_ids']:continue
  legacy=org.get('legacy_record',{})
  cards.append(dict(id=s['id'],org_id=org['id'],name=s['name'],scope=org.get('scope','public'),pathways=s['pathway_ids'],listed_in=s.get('listed_in',[]),description=s.get('description',''),url=s['next_step']['url'],eligibility=s['eligibility'],availability=s['availability'],coverage=s['coverage'],fulfillment=s['fulfillment'],types=s['attributes'].get('seed_types',[]),legacy_area=legacy.get('Service Area (as published)',legacy.get('Service Area','')),category=legacy.get('Category',''),legacy=bool(legacy),provider=s['attributes'].get('provider_details'),person=legacy.get('Contact Person',''),contacts=org['contacts'],sources=[{k:evidence[eid].get(k,'') for k in ['source_url','status','reviewed_on','claim','limitations']} for eid in s['evidence_ids']]))
 payload=dict(states=public_states,pathways=data['pathways'],cards=cards,aliases=data.get('aliases',[]),rules=data['rules'],events=data['events'])
 options=''.join(f'<option value="{s["code"]}">{html.escape(s["name"])}'+(' (pilot)' if s['publication_status']=='pilot' else '')+'</option>' for s in public_states)
 fallback=[]
 for state in public_states:
  if state['publication_status']!='pilot':continue
  routes=[c for c in cards if state['code'] in c['listed_in'] and c['scope']=='public']
  fallback.append('<h2>'+html.escape(state['name'])+' pilot referral routes</h2><p>Selected referrals only; other needs remain under research.</p><ul>'+''.join('<li><a href="'+html.escape(c['url'],quote=True)+'">'+html.escape(c['name'])+'</a> — '+html.escape(c['eligibility'])+'</li>' for c in routes)+'</ul>')
 page=(ROOT/'templates/state.html').read_text().replace('__STATE_OPTIONS__',options).replace('__DATA__',script_json(payload)).replace('__PILOT_NOJS__',''.join(fallback))
 return brand_page(externalize(page,script_json(payload),payload,"data/public-state.json",persist=persist))
def main():
 OUT.write_text(build_page(load_directory(),persist=True));print('Built shared state.html from state packs and canonical service records')
if __name__=='__main__':main()
