"""Exercise dangerous data errors the shared contract must reject."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from validate_foundation import validate
base=json.loads((ROOT/'data/foundation/directory.json').read_text());assert not validate(base)
def rejects(change,expected):
 d=copy.deepcopy(base);change(d);errors=validate(d);assert any(expected in e for e in errors),errors
rejects(lambda d:d['organizations'].append(dict(d['organizations'][0],name='Different name, same ID')),'Duplicate identity')
rejects(lambda d:d['services'][0].update(organization_id='org-missing'),'missing organizations reference')
rejects(lambda d:d['services'][0]['coverage'].append({'kind':'county','state':'OH','evidence_ids':[d['evidence'][0]['id']]}),'county coverage requires')
rejects(lambda d:d['evidence'][0].update(reviewed_on='2027-01-01'),'future review date')
rejects(lambda d:d['services'][0]['fulfillment'][0].update(status='confirmed',evidence_ids=[]),'fulfillment status requires evidence')
rejects(lambda d:d['states'][0]['pathways'][0].update(coverage_status='not-reviewed'),'unreviewed route cannot be public')
rejects(lambda d:d['states'][0].update(publication_status='research-only'),'unreviewed route cannot be public')
rejects(lambda d:d['services'][0].update(pathway_ids=['imaginary']),'unknown pathway')
rejects(lambda d:d['services'][0]['fulfillment'][0].update(status='confirmed'),'matching claim-level evidence')
print('PASS foundation regression: identity, references, geography, dates, unsupported fulfillment and publication gates.')
