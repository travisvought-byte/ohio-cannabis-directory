# State permissions: the national layer

Tracking: #60. Canonical data: [`data/state-permissions.json`](../data/state-permissions.json), validated by [`validate_permissions.py`](../validate_permissions.py) and rendered by [`permissions_page.py`](../permissions_page.py) into `compare.html`.

## Owner direction

The national guide is built top-down (November 15, 2026). National sources that cover every state come first. Each state's own official sources come next and replace the national answer wherever they have been reviewed. States are not built from the bottom up.

## What the page shows, in order

1. **Across every state.** Federal rules and national help lines: federal scheduling, flying, VA care, legal aid, Poison Help and the SAMHSA helpline. Each item links to the agency or organization that runs it.
2. **One state in detail.** The same consumer questions for every jurisdiction, with an optional second state for comparison. The view can be shared as a link (`?state=TX&compare=OH`).
3. **All 50 states and DC at a glance.** The two top-level answers (adult use and medical program) for every jurisdiction.

The policy portal, business-policy law cards, market data and lessons follow unchanged.

## Data model

- `jurisdictions`: exactly 51 (50 states and DC). The validator fails on any other count.
- `questions`: one shared set, grouped for display. `required_questions` (adult use, medical) must be answered for every jurisdiction.
- `answers`: one record per jurisdiction and question, never pairwise. Each has a `status`, a short answer of 60 characters or fewer, a detail, a citation, `reviewed_on`, optional `effective_on` and `source_ids`.
- `statuses`: `allowed`, `medical-only`, `limited`, `not-permitted`, `varies-locally`, `not-reviewed`. A `not-reviewed` answer is never stored: a missing answer renders as "Not yet reviewed" and never as a prohibition.
- `sources`: kind (`statute`, `regulator`, `government`, `organization`, `compilation`, `news`), scope (`state` or `national`) and retrieval date. Every listed source must be cited.
- `official_links`: each state's official starting point, which must be a reviewed state primary source.
- `national`: items that apply in every state, sourced to the agency or organization that runs them.

## Evidence levels

Computed from an answer's sources and shown on every answer:

- **Official source**: every source is a statute, regulator or government page.
- **Official source and national compilation**: a mix.
- **National compilation: confirm with the state**: only national compilations (currently Ballotpedia's adult-use list and DISA's state legality map).

A national compilation is a secondary source under the [working agreement](../AGENTS.md). It is the starting layer, not the finish line. Replacing it with the state's own source is the next research step for each state.

## Updating an answer

1. Retrieve the official source. A blocked or failed retrieval is not a review: record the attempt in the pull request and leave the answer as it is.
2. Edit the answer and add or update the source with its retrieval date. Keep the answer under the same jurisdiction and question; do not add pairwise records.
3. Run `python validate_permissions.py`, `python build_compare.py` and the checks in [AGENTS.md](../AGENTS.md).

## Known gaps (November 15, 2026)

- The adult-use answer rests on national compilations for 26 jurisdictions: the 25 states without adult use other than Pennsylvania (which has a statute-level answer), plus Montana.
- The medical answer rests wholly on a national compilation for Idaho, Indiana, Iowa, Kansas, Louisiana, Montana, Nebraska, North Carolina, North Dakota, South Carolina, Tennessee, Washington, Wisconsin and Wyoming, and partly for Colorado, Georgia and Texas.
- No official state link has been reviewed yet for Idaho, Indiana, Iowa, Kansas, Louisiana, Nebraska, North Carolina, North Dakota, South Carolina, Tennessee, Wisconsin and Wyoming. Retrieval of the North Dakota, Iowa and Washington health department pages failed on November 15, 2026.
- Detail rows (buying, possession, sharing, home grow, public use, driving) are filled only where an official page reviewed for this pass stated them. Every other cell reads "Not yet reviewed".
- Employment and record relief are not in the shared question set yet. They need status wording that does not read as a verdict.
