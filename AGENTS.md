# Working agreement for AI assistants

Read this file in full before starting a task. The directory owner is Travis Vought (@travisvought-byte).

## What this repository is

The Ohio Cannabis Ecosystem Directory and the national section built from it: a free, source-linked public directory of organizations operating in or serving the cannabis market, with consumer resources, record-clearing guidance, a dispensary location finder, civic advocacy tools, and a page for every state built on the Ohio template. It is published under CC BY 4.0 on GitHub Pages. Its value is that every published claim can be traced to a named source. Protect that above speed.

## How work moves (owner direction, November 16, 2026)

Travis works on this repository directly through Claude. No other assistant or contributor is working on it. The earlier lanes, issue-claiming and pull-request rules were written for a multi-assistant setup and no longer apply.

1. **Claude has standing permission to work.** Keep going without asking for approval at each step. Pick the next most useful piece of work toward the owner's stated direction and do it.
2. **Commit directly to `main`.** No issue, branch or pull request is required. Use a pull request only when Travis asks for one.
3. **Run the checks before every push** (see Commands). Do not push a change that fails them.
4. **Ask only for decisions that are the owner's to make:** anything that cannot be undone, spends money, changes a domain or DNS, sends a message on his behalf, deletes records, or changes a rule in this file.
5. **Report what was done.** After a push, say plainly what changed, what was verified and what remains unconfirmed.
6. **Do not bump `release.json` or write release notes** unless Travis says to.

The evidence standard and the owner's inclusion rules below are unchanged. Working faster never loosens them.

## Sources of truth

- `data/directory.json` is canonical: organizations, locations, services, evidence, relationships, events, rules, pathways and routes.
- Everything below is **generated**. Do not hand-edit it; change the canonical data or the build script, then regenerate:
  - every `*.html` page at the repository root
  - every page in `national/` (built by `build_national.py` from `data/state-permissions.json` and `data/state-scorecard.json`; rebuild it whenever either file changes)
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

## Before each push

- [ ] Canonical data changed, generated files regenerated, none hand-edited
- [ ] Every new or changed claim has a dated source; blocked retrievals recorded as attempts
- [ ] All checks pass locally
- [ ] The commit message says what was verified and what remains unconfirmed
