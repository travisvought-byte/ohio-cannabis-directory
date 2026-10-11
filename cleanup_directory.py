"""Restore historical review dates and normalize geography without a fresh-review claim."""
import json,re,collections
from pathlib import Path
ROOT=Path(__file__).parent
def normalize(area):
 s=area.casefold().strip()
 if not s:return 'Multistate, Ohio unconfirmed'
 if any(x in s for x in ['no verified','no current ohio','not identified','not publicly identified','to confirm','no ohio client','unconfirmed']):return 'Multistate, Ohio unconfirmed'
 if s in ['out of state','oregon-based','los angeles, ca'] or (any(x in s for x in ['michigan only','outside ohio','not ohio']) and 'ohio-market' not in s):return 'Outside Ohio'
 if any(x in s for x in ['nationwide','all 50 states','all u.s. states','including ohio','national','united states','north america']) and not any(x in s for x in ['no ohio','unconfirmed']):return 'Nationwide incl. Ohio' if any(x in s for x in ['nationwide','all 50','all u.s.','including ohio']) or ('ohio' in s and any(x in s for x in ['national','united states'])) else 'Multistate, Ohio unconfirmed'
 if 'statewide' in s:return 'Ohio statewide'
 if 'ohio' in s or any(x in s for x in ['columbus','cleveland','cincinnati','dayton','toledo','akron','portsmouth','mount orab','morrow','knox','willoughby','springdale','wilmington']):return 'Ohio regional: '+(area if s!='ohio' else 'Ohio (extent unspecified)')
 return 'Multistate, Ohio unconfirmed'
def main():
 p=ROOT/'data/directory.json';d=json.loads(p.read_text());changed=[];unknown=[]
 for o in d['organizations']:
  if 'legacy_record' not in o:continue
  r=o['legacy_record'];dates=re.findall(r'(\d{4}-\d{2}-\d{2}); source pages retrieved and reviewed',r['Seed Source'])
  existing=r.get('Last Reviewed','');date=max(dates+[existing]) if dates or existing else ''
  if date!=existing:changed.append({'id':o['id'],'name':o['name'],'old':existing,'restored_date':date})
  r['Last Reviewed']=date
  if not date:unknown.append({'id':o['id'],'name':o['name']})
  original=r.get('Service Area (as published)',r['Service Area']);r['Service Area (as published)']=original;r['Service Area']=normalize(original)
 p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 report={'checked_on':'2026-10-11','method':'Most recent dated source-pages-retrieved-and-reviewed audit in Seed Source, or a more recent existing review. Not a new review. Service-area labels are conservative normalizations of historical text, not verified fulfillment.','restored_review_dates':changed,'rows_without_dated_review':unknown,'coverage_counts':dict(collections.Counter(o['legacy_record']['Service Area'] for o in d['organizations'] if 'legacy_record' in o))}
 (ROOT/'data/review-migration-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(len(changed),'dates restored;',len(unknown),'without dated evidence')
if __name__=='__main__':main()
