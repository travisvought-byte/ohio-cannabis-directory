"""Exercise scheduled diagnostic dates and the actual inline issue-queue builder."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_review_queue
ROOT = Path(__file__).resolve().parents[1]

class MaintenanceDates(unittest.TestCase):
    def test_current_date_diagnostic_and_reproducible_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'architecture').mkdir()
            shutil.copytree(ROOT / 'data/reviews', root / 'data/reviews')
            for name in ['data/directory.json', 'data/review-triggers.json', 'release.json']:
                shutil.copy(ROOT / name, root / name)
            original = (root / 'data/directory.json').read_bytes()
            with patch.object(build_review_queue, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                build_review_queue.main()
                baseline = json.loads((root / 'data/review-queue.json').read_text())
                self.assertEqual((root / 'data/review-queue.json').read_bytes(), (ROOT / 'data/review-queue.json').read_bytes())
                build_review_queue.main('2027-10-24')
                diagnostic = json.loads((root / 'data/review-queue.json').read_text())
                self.assertEqual(diagnostic['as_of'], '2027-10-24')
                self.assertGreater(len(diagnostic['queue']), len(baseline['queue']))
                self.assertEqual((root / 'data/directory.json').read_bytes(), original)
                with self.assertRaises(ValueError):
                    build_review_queue.main('invalid-date')

class IssueQueue(unittest.TestCase):
    def test_all_pages_bounded_selection_and_pr_links(self):
        workflow = (ROOT / '.github/workflows/agent-queue.yml').read_text()
        code = workflow.split("python - <<'PY'\n", 1)[1].split('          PY', 1)[0]
        code = '\n'.join(line[10:] for line in code.splitlines())
        def issue(number, **extra):
            return {'number':number, 'title':'Untrusted <title> #'+str(number), 'html_url':f'https://github.com/owner/repo/issues/{number}', **extra}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'issues.json').write_text(json.dumps([[issue(6),issue(2),issue(90,pull_request={})],[issue(1),issue(3),issue(4),issue(5),issue(7),issue(8)]]))
            prs = [[{'title':'Related #1', 'body':''}], [{'title':'Work', 'body':'Closes https://github.com/owner/repo/issues/2\nFixes owner/repo#3'}]]
            (root / 'prs.json').write_text(json.dumps(prs))
            env = dict(os.environ, GH_REPO='owner/repo', GITHUB_STEP_SUMMARY=str(root / 'summary.md'))
            subprocess.run([sys.executable, '-c', code], cwd=root, env=env, check=True)
            result = json.loads((root / 'agent-queue.json').read_text())
            self.assertEqual([r['number'] for r in result['selected']], [4,5,6])
            self.assertEqual(result['eligible_count'], 5)
            self.assertFalse(result['execution_enabled'])
            self.assertNotIn('<title>', (root / 'summary.md').read_text())
        self.assertIn('--paginate --slurp', workflow)
        self.assertNotIn('pull_request_target:', workflow)
        self.assertNotIn(': write', workflow)

if __name__ == '__main__':
    unittest.main()
