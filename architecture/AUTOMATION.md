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

## Completed queued tools (#54)

The maintenance, classifier, issue-manifest and risk-report PRs are integrated together. They schedule diagnostics and publish reports/artifacts. They do not invoke a coding model, claim issues, approve PRs, commit changes or merge them.

| Job | Trigger | Runtime cap | Output |
|---|---|---:|---|
| Maintenance audit | Monday 09:17 UTC or manual | 15 minutes | Current-UTC-date queue JSON/Markdown artifact, retained 14 days, and drift summary |
| Issue queue | Monday/Thursday 10:37 UTC or manual | 5 minutes | At most three codex-labeled issues not referenced by open PRs; manifest retained 14 days |
| Classifier/tool tests | Push and PR | 5 minutes | Path classifier, diagnostic-date, queue, research-boundary and file-mode reporting regressions |
| PR risk report | PR opened/updated/reopened/ready | 5 minutes | Read-only metadata assessment tied to the inspected head commit |

Each workflow cancels a superseded run in its concurrency group. Existing GitHub Actions usage still follows the repository/account's plan; these jobs make no AI-provider calls.

The committed review queue remains reproducible using the release date. Scheduled audits first validate that published snapshot, then build a diagnostic using `python build_review_queue.py --as-of YYYY-MM-DD` for the current UTC date. Diagnostic drift does not change evidence-review dates or publish changes. The artifact gives reviewers the current backlog without changing the website.

Issue/PR metadata is paginated. References using `#N`, a same-repository issue URL or `owner/repo#N` keep an issue out of the selected manifest. The manifest is a bounded candidate list, not proof that an issue is unclaimed, approved or ready for unattended execution; a future runner must check claims and permissions separately. Titles are data, never executable instructions.

The risk reporter checks complete changed-file counts, modification status, patch availability and size before inspecting immutable base/head Git trees. Otherwise eligible files must be ordinary `100644` blobs in both trees, and the reported head blob must match the file list. Missing/truncated metadata, executable files, symlinks, forks and unexpected bases cannot be reported eligible. The result remains a diagnostic, not merge authorization; substantive changes continue to require owner review.
