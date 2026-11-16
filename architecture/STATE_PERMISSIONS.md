# State permissions: the national layer

Tracking: #60. Canonical data: [`data/state-permissions.json`](../data/state-permissions.json), validated by [`validate_permissions.py`](../validate_permissions.py) and rendered by [`permissions_page.py`](../permissions_page.py) into `compare.html`.

The default state, the 50-state list and the sources are rendered into the page so they read without JavaScript. The state switcher's data is generated into `data/public-permissions.json` by `build_compare.py` (never hand-edit it) and loaded after first paint, like the other large pages. That keeps `compare.html` under the 200,000-byte page budget in `tests/navigation.cjs` as answers are added. Any copy of the page, such as the OhioWeed mirror, must publish that file beside it.

## Owner direction

The national guide is built top-down (November 15, 2026). National sources that cover every state come first. Each state's own official sources come next and replace the national answer wherever they have been reviewed. States are not built from the bottom up.

## What the page shows, in order

1. **Across every state.** Federal rules, national help lines and national organizations that cover every state: federal scheduling, state law summaries (NORML), flying, patient travel (Americans for Safe Access), VA care, legal aid, record clearing (Clean Slate Initiative; Collateral Consequences Resource Center, link only under its terms), finding state legislators (Open States), Poison Help and the SAMHSA helpline. Business resources (NCIA) sit under their own heading. Each item links to the agency or organization that runs it. A listing is not an endorsement, and advocacy groups are named as such. On phones each item's description is collapsed under "What it covers"; it opens automatically on wide screens.
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
- `national`: items that apply in every state, sourced to the agency or organization that runs them. `audience` is `consumer` (default) or `business`; business items render under their own heading.

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

- Every adult-use answer now cites at least one state source (#146). Ten pair that source with the national compilations because the state source predates November 2026 or describes the law indirectly, so the compilations are what show nothing has changed since: Alabama (a February 2026 bill synopsis), Arkansas (a 2019 Sentencing Commission quotation), Hawaii (February 2024 Attorney General testimony), New Hampshire (a 2019 Attorney General brief), Oklahoma (the 2023 State Question 820 vote), South Dakota (a 2021 Legislative Research Council summary of penalties, beside a July 2026 Department of Health page on sales), Texas (a March 2025 Senate Research Center analysis), Utah (the statute as reprinted in a January 2026 bill), Tennessee (a 2016 Attorney General opinion) and Wisconsin (a December 2023 Legislative Reference Bureau analysis).
- The current statute pages for several of those states could not be read by an automated reader on November 15, 2026: the Code of Alabama (`alisondb.legislature.state.al.us`) and New Hampshire's RSA pages (`gc.nh.gov/rsa`, `gc.nh.gov/legislation`) are disallowed; Oklahoma's statutes (`oscn.net`) are disallowed and the Legislature's Title 63 file is too long to read through; South Dakota's codified laws and the Texas statutes viewer need JavaScript; searches turned up only a copy of Utah Code 58-37-8 marked superseded in 2025; and the Arkansas Code is published through LexisNexis.
- Hawaii's current statute page for HRS 712-1249 still shows the pre-2019 wording (history ending "gen ch 1993"), without the Act 273 (2019) rule that 3 grams or less is a violation. The answer follows the Attorney General's February 2024 description of current law; the act's own pages on `capitol.hawaii.gov` returned errors, and the statute page should be rechecked.
- The medical answer rests wholly on a national compilation for Tennessee, and partly for Colorado, Georgia and Texas. The Tennessee General Assembly's pages (`capitol.tn.gov`, `wapp.capitol.tn.gov`) are disallowed to automated readers, so the 2021 cannabidiol oil exception could not be reviewed from the state's own pages.
- No official state link has been reviewed yet for Tennessee. The only Tennessee page retrieved, the 2016 Attorney General opinion, is cited but is not a starting point for visitors.
- Some statute pages are disallowed to automated readers: Wisconsin's section pages for 961.41 and Washington's RCW chapter pages on `apps.leg.wa.gov`. The Legislative Reference Bureau analysis and the certified RCW 69.51A.210 PDF were used instead. Earlier retrievals of `hhs.nd.gov/medical-marijuana`, `hhs.iowa.gov/public-health/medical-cannabidiol` and `doh.wa.gov` failed; each state's current program page was retrieved instead.
- Detail rows (buying, possession, sharing, home grow, public use, driving) are filled only where an official page reviewed for this pass stated them. Every other cell reads "Not yet reviewed".
- Americans for Safe Access's state-by-state patient pages could not be retrieved on November 15, 2026 (`/states` returned an error; `/patient_guide` is disallowed to automated readers). Only its travel guide is listed.
- Employment and record relief are not in the shared question set yet. They need status wording that does not read as a verdict.
