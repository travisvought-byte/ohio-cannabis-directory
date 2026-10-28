#!/usr/bin/env bash
set -euo pipefail
python tests/check_data.py
python validate_foundation.py
python validate_foundation.py data/directory.json
python tests/foundation.py
python tests/migration.py
python tests/locations.py
python tests/review_cleanup.py
python tests/ancestry.py
python strain_ancestry.py
python -m unittest discover -s tests -p 'test_automation*.py' -v
python -m unittest discover -s tests -p 'test_pr_classifier.py' -v
python -m unittest discover -s tests -p 'test_research_batch.py' -v
python -m unittest discover -s tests -p 'test_codex_runner.py' -v
python scripts/validate_pa_research.py
node tests/pr-risk-report.cjs
node tests/codex-runner.cjs
npm test
npm run test:browser
