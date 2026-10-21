# Working agreement for AI assistants

This file is read by every AI assistant that works on this repository (Codex, Claude, and any other). Read it in full before starting a task. The directory owner is Travis Vought (@travisvought-byte). He approves and merges every change.

## What this repository is

The Ohio Cannabis Ecosystem Directory: a free, source-linked public directory of organizations operating in or serving the Ohio cannabis market, with consumer resources, record-clearing guidance, a dispensary location finder, and civic advocacy tools. It is published under CC BY 4.0 on GitHub Pages. Its value is that every published claim can be traced to a named source. Protect that above speed.

## Lanes

Each assistant works only in its lane. Two assistants never work on the same files at the same time.

| Assistant | Lane |
| --- | --- |
| **Claude** | Data structure and schema changes, review policy, multi-state comparison design, reconciliation against regulator data, and reviewing pull requests before merge. |
| **Codex** | Implementing GitHub issues labeled `codex`: research batches, data additions in reviewable form, page and script changes with written acceptance criteria. |
| **Grok / X** | Leads only: bill news, event announcements, outreach drafts. Nothing from X is published or committed as evidence. |

## How work moves

1. **Claim the issue.** Work only from a GitHub issue. Comment on it when you start. If an issue is already claimed, do not start it.
2. **One branch and one pull request per issue.** Name branches `codex/<issue-number>-<short-slug>` or `claude/<issue-number>-<short-slug>`. Reference the issue in the pull request (`Closes #N`).
3. **Stay inside the issue's scope.** If you find something else that needs fixing, open a new issue instead of widening the pull request.
4. **The `Validate directory` workflow must pass.** Run the checks locally first (see Commands).
5. **Never merge your own pull request.** Travis merges. Claude may review and comment before he does.
6. **Do not bump `release.json` or write release notes** unless the issue says to.

## Sources of truth

- `data/directory.json` is canonical: organizations, locations, services, evidence, relationships, events, rules, pathways and routes.
- Everything below is **generated**. Do not hand-edit it; change the canonical data or the build script, then regenerate:
  - every `*.html` page at the repository root
  - `ohio-cannabis-directory.csv`, `b2b-relationships.csv`, `seed-suppliers.json`
  - `data/public-*.json`, `data/home-search.json`, `data/review-queue.json`, `architecture/REVIEW_QUEUE.md`
- Keep existing record IDs. Never reuse or renumber an ID.

## Evidence standard

- **Every published claim needs a named source** recorded as evidence with the date it was reviewed.
- **Prefer primary sources:** the regulator (Ohio Division of Cannabis Control), the statute or administrative code, the organization's own website, or the organizer's own event page. Secondary sources may support a claim but should be labeled as secondary.
- **Laws and rules carry a citation and an "as of" date.** Statute or code section plus the date it was checked.
- **Social media posts, AI output and search snippets are leads, not evidence.** Confirm them against a primary source before they enter the data.
- **A failed or blocked retrieval is not a review.** Record the attempt; do not assign a fresh review date.
- **Never invent** a contact, address, license number, date or count. If a source does not establish it, leave it blank and say what is missing.
- **Respect source terms.** Some sources prohibit copying (for example Leafly and the Collateral Consequences Resource Center). Link to and cite them; do not copy their content into the data.

## Inclusion rules set by the owner

- An organization's paid or exhibiting presence at an Ohio cannabis trade show is sufficient evidence of being cannabis-adjacent for inclusion, even without other web corroboration. Do not drop such entries for lacking open-source verification.
- Contact details collected at trade shows were provided by those businesses for listing. Do not strip or redact existing contact details from records.
- Records are not silently deleted. Closed, merged or withdrawn organizations change scope and keep their history (see `data/listing-withdrawals.json`).
- No paid placement, paid ranking or paid verification.

## Advocacy and state comparison content

- Present each state's law side by side and factually, with citations. Do not editorialize about which approach is better; visitors decide.
- Letters are written in the visitor's voice and state the visitor's view, not the directory's.
- Stay nonpartisan. Treat every party and lawmaker the same way.

## Commands

```bash
pip install -r requirements.txt
npm ci

# after changing data/directory.json
python export_directory.py
python build_review_queue.py
python build_directory.py      # plus any other build_*.py the change affects

# checks (the same ones CI runs)
python tests/check_data.py
python validate_foundation.py data/directory.json
python tests/foundation.py
python tests/migration.py
python tests/locations.py
python tests/review_cleanup.py
npm test
npm run test:browser
```

See `CONTRIBUTING.md` for field rules and `architecture/` for the directory contract, review queue, event maintenance and analytics.

## Pull request checklist

- [ ] Linked to its issue and stays within its scope
- [ ] Canonical data changed, generated files regenerated, none hand-edited
- [ ] Every new or changed claim has a dated source; blocked retrievals recorded as attempts
- [ ] All checks pass locally
- [ ] The description lists what was verified and what remains unconfirmed
