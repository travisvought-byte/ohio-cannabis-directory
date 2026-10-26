import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('guard', ROOT / 'scripts/codex_research_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
config_spec = importlib.util.spec_from_file_location('research_config', ROOT / 'scripts/codex_research_config.py')
research_config = importlib.util.module_from_spec(config_spec)
config_spec.loader.exec_module(research_config)


class ResearchGuardTests(unittest.TestCase):
    def setUp(self):
        self.task = dict(base_sha='a'*40, issue=21, run_id='9', auth={'files':['data/research/banking.json']})
        self.bundle = dict(base_sha='a'*40, issue=21, run_id='9', files=[{'path':'data/research/banking.json','content':'[]'}], summary='Reviewed', limitations=[])

    def test_identity_scope_and_payload_rejections(self):
        guard.check(self.task, self.bundle)
        mutations = [lambda b:b.update(run_id='another'), lambda b:b.update(base_sha='b'*40), lambda b:b.update(files=[]),
                     lambda b:b['files'].append(copy.deepcopy(b['files'][0])), lambda b:b['files'][0].update(path='data/directory.json'),
                     lambda b:b['files'][0].update(path='data/research/../banking.json'), lambda b:b['files'][0].update(content='NaN'),
                     lambda b:b['files'][0].update(content='\x00'), lambda b:b['files'][0].update(content='x'*100001),
                     lambda b:b.update(summary='x'*8001), lambda b:b.update(limitations=['x'*1001]), lambda b:b.update(extra=True)]
        for mutate in mutations:
            b=copy.deepcopy(self.bundle);mutate(b)
            with self.subTest(bundle=b.keys()), self.assertRaises((AssertionError, ValueError)):
                guard.check(self.task,b)

    def test_real_git_export_and_materialization(self):
        old=os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            try:
                os.chdir(d)
                def git(*args): return subprocess.check_output(['git',*args],stderr=subprocess.DEVNULL)
                git('init');git('config','user.email','tests@example.org');git('config','user.name','Tests')
                Path('README.md').write_text('base');git('add','.');git('commit','-m','base')
                self.task['base_sha']=git('rev-parse','HEAD').decode().strip()
                self.bundle['base_sha']=self.task['base_sha']
                Path('data/research').mkdir(parents=True)
                p=Path('data/research/banking.json');p.write_text('[]')
                report={'status':'completed','summary':'Reviewed','limitations':[]}
                self.assertEqual(guard.export(self.task,report),self.bundle)
                p.chmod(0o755)
                with self.assertRaises(AssertionError): guard.export(self.task,report)
                p.chmod(0o644);p.unlink();p.symlink_to('../../README.md')
                with self.assertRaises(AssertionError): guard.export(self.task,report)
                p.unlink();p.write_text('[]');Path('README.md').write_text('outside scope')
                with self.assertRaises(AssertionError): guard.export(self.task,report)
                git('checkout','--','README.md');p.unlink()
                guard.materialize(self.task,self.bundle)
                self.assertEqual(p.read_text(),'[]')
                with self.assertRaises(AssertionError): guard.materialize(self.task,self.bundle)
                p.unlink()
                with self.assertRaises(AssertionError): guard.export(self.task,{**report,'status':'blocked'})
            finally: os.chdir(old)

    def test_workflow_separates_credentials_and_disables_schedules(self):
        text=(ROOT/'.github/workflows/codex-issue-runner.yml').read_text()
        self.assertNotIn('schedule:',text)
        self.assertNotIn('pull_request_target',text)
        execute=text.split('  execute:\n',1)[1].split('  validate:\n',1)[0]
        validate=text.split('  validate:\n',1)[1].split('  deliver:\n',1)[0]
        self.assertNotIn('CODEX_APP_PRIVATE_KEY',execute+validate)
        self.assertNotIn('OPENAI_API_KEY',validate)
        self.assertIn('cancel-in-progress: false',text)
        self.assertIn("codex-version: '0.164.0'",execute)
        self.assertIn('permission-profile: research',execute)
        self.assertIn('python scripts/codex_research_config.py',execute)
        self.assertIn('timeout-minutes: 20',execute)

    def test_generated_profile(self):
        for domains in ([],['example.org','www.example.org']):
            config=tomllib.loads(research_config.configuration(domains))
            profile=config['permissions']['research']
            self.assertEqual(profile['extends'],':read-only')
            self.assertEqual(profile['filesystem'],{'/opt/codex-runner':'read',':workspace_roots':{'data/research':'write'}})
            self.assertEqual(profile['network'],{'enabled':True,'domains':dict.fromkeys(domains,'allow')})
            self.assertTrue(config['features']['network_proxy'])
            self.assertEqual(config['web_search'],'live')

    def test_preclaim_configuration_and_retry_checks(self):
        text=(ROOT/'.github/workflows/codex-issue-runner.yml').read_text()
        before_checkout=text.split('      - uses: actions/checkout@v4',1)[0]
        script=textwrap.dedent(before_checkout.split('        run: |\n',1)[1])
        configured=dict(PATH=os.environ['PATH'],APP_ID='123',MODEL='test-model',
                        HAS_APP_KEY='true',HAS_PROVIDER_KEY='true',RUN_ATTEMPT='1',
                        TRIGGERING_ACTOR='owner',OWNER='owner')
        result=subprocess.run(['bash','-e','-c',script],env=configured,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        for key,value in [('APP_ID',''),('MODEL',''),('HAS_APP_KEY','false'),
                          ('HAS_PROVIDER_KEY','false'),('RUN_ATTEMPT','2'),
                          ('TRIGGERING_ACTOR','collaborator')]:
            with self.subTest(setting=key):
                result=subprocess.run(['bash','-e','-c',script],env={**configured,key:value},capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)


if __name__=='__main__': unittest.main()
