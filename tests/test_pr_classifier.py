import unittest
from scripts.classify_pr import eligible

class ClassifierTests(unittest.TestCase):
    def test_allowed_modified_docs(self):
        self.assertTrue(eligible([{"filename": "docs/README.md", "status": "modified"}]))

    def test_fail_closed(self):
        bad = [
            [], [{"filename": "AGENTS.md", "status": "modified"}],
            [{"filename": "docs/README.md", "status": "added"}],
            [{"filename": "docs/README.md", "status": "removed"}],
            [{"filename": "docs/README.md", "status": "renamed", "previous_filename": "x"}],
            [{"filename": "docs/README.md", "status": "modified", "previous_filename": "x"}],
            [{"filename": "docs/../data/directory.json", "status": "modified"}],
            [{"filename": "DOCS/README.md", "status": "modified"}],
            [{"filename": ".github/workflows/validate.yml", "status": "modified"}],
            [{"filename": "release.json", "status": "modified"}],
            [{"filename": "docs/README.md", "status": "modified"}, {"filename": "data/directory.json", "status": "modified"}],
            [{"filename": "docs/README.md", "status": "modified"}, {"filename": "docs/CONTRIBUTING.md", "status": "added"}],
            [{"filename": None, "status": "modified"}],
        ]
        for case in bad:
            with self.subTest(case=case):
                self.assertFalse(eligible(case))
        self.assertFalse(eligible(None))
        self.assertFalse(eligible([{"filename": "docs/README.md"}]))

if __name__ == "__main__":
    unittest.main()
