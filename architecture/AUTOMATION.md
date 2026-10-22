# Guarded automation plan

Status: phase 1, audit only. No autonomous merge or agent execution is enabled by this document.

## Operating model
- Weekly scheduled workflow regenerates the review queue locally, validates data and reports drift. It has read-only repository permissions and does not commit.
- Issue-based research agents may prepare one branch and pull request per issue following AGENTS.md.
- Human approval remains required for all pull requests until an explicit, independently tested merge gate is deployed.
- Future auto-merge may apply only to a strict allowlist of low-risk, non-generated documentation/metadata files after all required checks pass, with no source, legal, directory, site, code, dependency, or workflow changes.
- Changes to `data/**`, `*.html`, `*.py`, `*.js`, `*.cjs`, `.github/**`, `AGENTS.md`, `release.json`, `CHANGELOG.md`, legal guidance, advocacy and review policy always require owner approval.
- PR labels and agent claims of safety are never sufficient to authorize auto-merge; classify the actual changed paths and content.
- Never grant write credentials to untrusted pull-request code or use `pull_request_target` to execute it.

## Before phase 2
1. Configure required Validate directory checks and branch protection/rulesets on main.
2. Decide bot identity and narrowly scoped token permissions; avoid long-lived broad secrets.
3. Build a deny-by-default merge gate and test it against adversarial file changes.
4. Set run-time and spend caps, agent concurrency limit of one per file area, and failure alerts.
5. Amend AGENTS.md in a separately approved PR to describe delegated routine merges.
6. Pilot on low-risk changes and audit the first ten runs.

Human review remains mandatory for substantive content and every v4.37 release change.
