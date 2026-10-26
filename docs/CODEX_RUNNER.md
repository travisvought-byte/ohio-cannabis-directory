# Opt-in issue-to-PR research runner

The `Opt-in Codex research runner` workflow implements the manual pilot for issue
#56. It does not change the candidate queue, add a schedule, merge PRs, publish
the site, or delegate arbitrary code changes. Existing `AGENTS.md` review rules
continue to apply. The public directory and release metadata are unchanged.

## What one run does

1. The owner dispatches one issue from **main**. Repository variables must enable
   the runner and acknowledge the provider budget configuration. Required setting
   presence and the dispatch attempt are checked before claiming an issue; missing
   configuration cannot consume its authorization. Use a new dispatch after
   recovery, not GitHub's **Re-run jobs** button.
2. A control job verifies the issue, owner-applied execution label, exact approved
   research filenames, all paginated comments/events/open PRs, and absence of
   unresolved claims. It records its claim and immutable main commit.
3. A fresh job runs the pinned official Codex Action with CLI **0.164.0**, a
   configured model, live hosted search, and command retrieval restricted to the
   owner's approved hostnames. The model has no GitHub write token. Its command
   filesystem profile allows writes only under `data/research`.
4. A root-owned exporter rejects changes outside the exact approved files,
   committed changes, deletions, symlinks, executable files, invalid JSON, large
   output, a blocked report, and an empty result. Only text content is exported;
   Git configuration, executable code, patches and credentials are not delivered.
5. A separate job repeats scope checks on the original main commit, installs
   validation dependencies and runs the repository's Python, Node and browser
   checks, including the runner regression tests. No model/API/App secrets are
   supplied to validation.
6. A delivery job checks the artifact again and rechecks live issue authorization,
   comments, labels, PRs and main. A short-lived GitHub App token creates blobs,
   a commit, `codex/<issue>-automated-research`, and one PR with `Closes #N`.
   It never executes model-written code or merges. Main advancing blocks delivery.
7. A final job reports success/failure to the issue when possible. An interrupted
   run can leave a claim or branch; recovery requires human inspection.

This is a research-only pilot. Source correctness, actual service coverage and
whether a source was fully reviewed still require evidence review. Software
checks do not prove those claims. The runner cannot determine that an old issue
has already been satisfied; the owner must reconcile it before authorization.

The classifier workflow also runs a credential-free Ubuntu permission smoke
test against CLI 0.164.0 and the same generated profile as execution. It checks
that research writes succeed while source, workflow and Git metadata writes are
denied. It makes no model call and needs no API billing configuration. This does
not replace the manual pilot's provider/proxy, network and delivery checks.

## Owner setup after reviewing and merging the implementation

In the repository's Actions secrets/variables settings, configure:

| Setting | Type | Value/purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Secret | Dedicated funded provider key; never paste it in issues or chat |
| `CODEX_APP_PRIVATE_KEY` | Secret | Private key for a GitHub App installed on this repository only |
| `CODEX_APP_ID` | Variable | The App's numeric ID |
| `CODEX_RUNNER_MODEL` | Variable | An explicit model available to that API project |
| `CODEX_BUDGET_CONFIRMED` | Variable | `true` only after configuring acceptable provider/gateway cost controls |
| `CODEX_RUNNER_ENABLED` | Variable | `true` to allow owner-dispatched manual runs; absent/false disables them |

The App installation needs **Contents: read/write**, **Issues: read/write**, and
**Pull requests: read/write**. Each job requests only its own subset, and tokens
are revoked by the token action's cleanup. No Administration, Actions-write,
Workflows-write or branch-protection bypass permission is needed. Create the
`codex-execute` label if it does not exist.

Verify protection/rulesets on main require the normal validation checks and owner
review, with no bot bypass. These settings and secrets cannot be verified by
reading repository files. Retain branch protections while testing the pilot.

### Create the GitHub App

In your GitHub account's **Settings → Developer settings → GitHub Apps**, create
an App owned by your account. Use this repository's URL for its homepage and
disable the webhook: this runner mints installation tokens and needs no webhook
server, callback URL or user authorization flow. Limit installation to your
account. Set the three repository permissions above; Metadata read access is
implicit. Leave organization/account permissions and event subscriptions unset.

Generate a private key and save the complete downloaded PEM as the Actions secret
`CODEX_APP_PRIVATE_KEY`. Save the numeric **App ID**, not its Client ID, as
`CODEX_APP_ID`. Install the App with **Only select repositories**, selecting only
`ohio-cannabis-directory`. Approve updated installation permissions if you change
them later. Do not give this App a main-branch ruleset bypass. Repository Actions
policy must allow the actions used here, including the pinned Codex Action.

### API billing and cost controls

Create a dedicated OpenAI API project and a project-scoped key for this runner.
API usage is billed separately from a ChatGPT subscription or Codex Cloud use;
GitHub Actions runtime/storage accounting is separate again. Choose a Codex-
compatible model available to that project and put its exact model ID in
`CODEX_RUNNER_MODEL`. Model tokens and hosted search can both incur API charges;
check current [API pricing](https://openai.com/api/pricing/) and project usage.

The 20-minute model-step timeout is a runtime bound, **not a hard dollar or token
cap**. The budget-confirmation variable is an acknowledgement, not metering.
Configure provider limits suitable for this key; some project budget settings
only send alerts. If a strict per-run dollar/token ceiling is required, keep the
runner disabled until a metered gateway or other enforced cap is integrated.
No API spending or successful live run is implied by the offline tests.

Set project budget alerts and appropriate model/rate limits in the API project's
settings, and review any prepaid-credit/automatic-recharge settings. A project
monthly budget is normally an alert threshold, not a request-blocking cap;
rate limits constrain throughput, not total dollars. Do not treat a prepaid
balance as a guaranteed exact cutoff either. Set `CODEX_BUDGET_CONFIRMED=true`
only when those limitations are acceptable or an enforced external limit is in
place. Keep `CODEX_RUNNER_ENABLED=false` until setup is complete. No part of this
workflow buys credits, changes billing, or provisions a metered gateway.

## Authorize a bounded pilot

Issue #21 (insurance/banking research) is a candidate after checking its current
state. Do not authorize the multi-state roadmap #42 as one run. Reconcile the
existing claim and already published work in #47 before creating a new task.

Before authorizing #21, recheck that it is open, unassigned, not already claimed
or completed, and has no linked open PR or existing
`codex/21-automated-research` branch. The implementation must first be reviewed
and merged to main by the owner; dispatching PR #57's branch is intentionally
rejected. Configuration can be prepared before that merge, with execution off.

The **owner personally** applies both `codex` and `codex-execute` labels and adds
one exact command comment, for example (replace the date with the actual run
date and add approved primary-source hostnames if command retrieval is needed):

```text
/codex-run {"files":["data/research/provider-candidates-insurance-banking-2026-10-26.json"],"domains":[]}
```

Allow 1–3 exact filenames directly in `data/research`, ending in `.json` or `.md`.
Wildcards, nested paths, traversal and executable files are rejected. Each file
is limited to 100 KB and the full result to 200 KB. At most 20 exact hostnames
are allowed for command retrieval; add redirect hostnames explicitly. An empty
domain list, as in this example, permits hosted search and its page retrieval but
blocks command retrieval. If command retrieval is needed, replace the list with
actual approved primary-source hostnames. Hosted search
and its page access use OpenAI's separate service policy; this hostname list is
not a global filter on that tool. Blocked source access must remain a limitation.

The pilot conservatively treats other issue comments as potential discussion or
claims. After reviewing an old comment and confirming its worker is inactive,
the owner may acknowledge it explicitly in another comment:

```text
/codex-release-comment 123456789
```

Use the real comment ID; preserve its history. Unassign existing assignees only
after coordination. Never acknowledge a claim while its worker is still active.

Open **Actions → Opt-in Codex research runner → Run workflow**, select **main**,
and supply the issue number. Execution is serialized; do not queue many manual
dispatches because GitHub concurrency keeps a limited pending queue.

For the first pilot, set `CODEX_BUDGET_CONFIRMED=true` only after the cost-control
review, set `CODEX_RUNNER_ENABLED=true`, and dispatch issue number `21` once.
Turn `CODEX_RUNNER_ENABLED` back to `false` after the pilot while reviewing its
results. Disabling this variable prevents future starts; it does not cancel an
already running model step. To stop current spending, cancel the active run in
Actions (and revoke the API key if needed).

## Inspect the first run

- Check the claim, model outcome, `codex-task-*`, `codex-result-*`, and
  `codex-validation-*` artifacts and job logs. Artifacts are retained 14 days;
  source records and the PR are the durable research record.
- Confirm only authorized research files changed and inspect every source/date.
- Confirm **Validate directory** and **Validate PR classifier** actually trigger
  and pass on the App-created branch/PR. The default `GITHUB_TOKEN` cannot simply
  replace the App token: its event-trigger restrictions can suppress downstream CI.
- Review and merge the research PR personally if it is correct.

The GitHub-hosted runner installs its own tools. It does not inherit a published
Codex Cloud environment or this chat's authentication. This workflow uses GitHub
Actions and API access; it does not occupy a ChatGPT scheduled-task slot.

## Failure and retry

Failed, blocked or canceled work never delivers a PR unless independent checks
and delivery rechecks succeed. The best-effort report lists the failed stage;
check Actions if reporting itself failed. No failed retrieval changes a public
verification date. No exception automatically releases another agent's claim.
PR delivery is recorded before the separate notification job, so a comment
outage does not turn a confirmed PR creation into a delivery failure. A failed
report job still needs inspection in Actions.

Before retrying, inspect the run and any existing branch/PR. Never overwrite or
delete someone else's work. The runner refuses an existing issue branch and
never force-pushes. If delivery pushed a branch but failed before creating its PR,
review that branch and open the PR manually instead of rerunning. If there is
an open linked PR, continue through its review rather than start another run.

After resolving an unsuccessful run, acknowledge its claim/report comments with
`/codex-release-comment COMMENT_ID` and post a **new** `/codex-run` authorization.
Editing an authorization during a run invalidates delivery. Rerun the entire
workflow as a new dispatch after recovery; rerunning only failed jobs is not a
supported continuation because artifacts are scoped to the run attempt.

## Scheduling comes after the pilot

No cron trigger is present. After a successful manual end-to-end run, use a
separate reviewed change to add owner-approved queue selection, priority,
stale-claim handling, credential/budget controls and a daily cadence. That work
can use GitHub scheduling independently of ChatGPT task limits. Automatic merge
remains a separate decision and implementation.

The intended later cadence is daily around **08:00 America/New_York**, accounting
for daylight saving time (08:00 corresponds to 12:00 UTC during EDT and 13:00 UTC
during EST). A fixed UTC cron alone will shift local time seasonally. The later
scheduling change must prevent duplicate daily runs, honor the enable/budget
switches, and retain owner authorization and review. GitHub scheduled starts can
be delayed; 08:00 is a target, not an exact-time guarantee. Keep scheduling absent
until the manual pilot has passed model startup, delivery, downstream CI and
human evidence review. This pilot still writes research only; general directory
code/publication changes need a separately reviewed expansion of scope.

References: [official Codex Action](https://github.com/openai/codex-action),
[Codex permissions](https://learn.chatgpt.com/docs/permissions),
[repository automation plan](../architecture/AUTOMATION.md).
