import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.validate_pa_research import validate

class ResearchBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=json.loads((ROOT/'data/research/pennsylvania-2026-10-24-candidates.json').read_text())
        cls.sources=json.loads((ROOT/'data/research/pennsylvania-2026-10-24-sources.json').read_text())
        cls.directory=json.loads((ROOT/'data/directory.json').read_text())
    def test_current_batch(self):
        self.assertEqual(validate(self.batch,self.sources,self.directory),[])
    def test_reject_bad_identity_and_unknown_claim_source(self):
        b=copy.deepcopy(self.batch);b['candidates'][0]['existing_organization_id']='missing'
        b['candidates'][0]['claims'][0]['source_ids']=['unknown']
        errors=validate(b,self.sources,self.directory)
        self.assertTrue(any('identity' in e for e in errors));self.assertTrue(any('unknown source' in e for e in errors))
    def test_research_cannot_silently_publish(self):
        b=copy.deepcopy(self.batch);b['candidates'][0]['publication_status']='public'
        self.assertTrue(any('research-only' in e for e in validate(b,self.sources,self.directory)))
    def test_failed_attempts_and_incorrect_counts(self):
        s=copy.deepcopy(self.sources);s['retrieval_attempts'][0]['reviewed_on']='2026-10-24'
        b=copy.deepcopy(self.batch);b['summary']['candidate_count']=0
        self.assertGreaterEqual(len(validate(b,s,self.directory)),2)
if __name__=='__main__':unittest.main()
