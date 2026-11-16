# State permissions: the national layer

Tracking: #60. Canonical data: [`data/state-permissions.json`](../data/state-permissions.json), validated by [`validate_permissions.py`](../validate_permissions.py) and rendered by [`permissions_page.py`](../permissions_page.py) into `compare.html`.

The default state, the 50-state list and the sources they cite are rendered into the page so they read without JavaScript. The state switcher's data is generated into `data/public-permissions.json` by `build_compare.py` (never hand-edit it) and loaded after first paint, like the other large pages. That keeps `compare.html` under the 200,000-byte page budget in `tests/navigation.cjs` as answers are added. Any copy of the page, such as the OhioWeed mirror, must publish that file beside it.

The page lists only the sources its own text cites: the national items and the default state (#158). A visitor without JavaScript cannot switch state, so those are every citation they can see. When the switcher shows another state it adds that state's sources to the list from the same file, under the same `[sN]` numbers and `#psource-N` anchors, and a link to any `#psource-N` still lands on it. Adding a source for another state therefore adds nothing to `compare.html`.

## Owner direction

The national guide is built top-down (November 15, 2026). National sources that cover every state come first. Each state's own official sources come next and replace the national answer wherever they have been reviewed. States are not built from the bottom up.

## What the page shows, in order

1. **Across every state.** Federal rules, national help lines and national organizations that cover every state: federal scheduling, state law summaries (NORML), flying, patient travel (Americans for Safe Access), VA care, legal aid, record clearing (Clean Slate Initiative; Collateral Consequences Resource Center, link only under its terms), finding state legislators (Open States), Poison Help and the SAMHSA helpline. Business resources (NCIA) sit under their own heading. Each item links to the agency or organization that runs it. A listing is not an endorsement, and advocacy groups are named as such. On phones each item's description is collapsed under "What it covers"; it opens automatically on wide screens.
2. **One state in detail.** The same consumer questions for every jurisdiction, with an optional second state for comparison. The view can be shared as a link (`?state=TX&compare=OH`).
3. **All 50 states and DC at a glance.** The two top-level answers (adult use and medical program) for every jurisdiction.

The policy portal, business-policy law cards, market data and lessons follow unchanged.

## Data model

- `jurisdictions`: exactly 51 (50 states and DC). The validator fails on any other count.
- `questions`: one shared set, grouped for display. `required_questions` (adult use, medical) must be answered for every jurisdiction. A question may carry a `note`, shown under it, and its own `statuses` (see "Questions that word their own labels").
- `answers`: one record per jurisdiction and question, never pairwise. Each has a `status`, a short answer of 60 characters or fewer, a detail, a citation, `reviewed_on`, optional `effective_on` and `source_ids`.
- `statuses`: `allowed`, `medical-only`, `limited`, `not-permitted`, `varies-locally`, `not-reviewed`. A `not-reviewed` answer is never stored: a missing answer renders as "Not yet reviewed" and never as a prohibition.
- `sources`: kind (`statute`, `regulator`, `government`, `organization`, `compilation`, `news`), scope (`state` or `national`) and retrieval date. Every listed source must be cited. An answer may cite only official kinds and national compilations, the two things its evidence label names; an organization's page can support a national item, not an answer.
- `official_links`: each state's official starting point, which must be a reviewed state primary source.
- `national`: items that apply in every state, sourced to the agency or organization that runs them. `audience` is `consumer` (default) or `business`; business items render under their own heading.

## Questions that word their own labels

"Allowed" and "Not permitted" read as a verdict on the visitor when the question is about a protection or a process. The employment and record-relief questions (#150, schema 1.1.0) therefore define their own statuses, each with a `label` and a `tone` (`positive`, `partial` or `negative`) that picks the chip colour. The label always carries the meaning; colour only repeats it.

| Question | Label | Use it when the cited state law |
| --- | --- | --- |
| Does state law protect workers who use cannabis off the job? | Protected | limits what employers may do about lawful use away from work. Exceptions go in the short answer and the detail. |
| | Partly protected | protects only some people or some decisions, such as registered medical patients only. |
| | Not protected | says employers may act on cannabis use. |
| Can a past cannabis record be cleared? | Automatic | clears or seals eligible records without an application. |
| | By application | provides a petition, motion or application. |
| | No process | is shown by an official source to provide none. |

Rules the validator enforces:

- An answer to one of these questions uses that question's statuses. The shared statuses are rejected there, and these are rejected everywhere else.
- "Not protected" and "No process" are claims about what the law lacks, so they need an official source (`needs_official_source`), like "Not permitted" for a medical program. Silence in a national list is not enough: leave the answer out and it reads "Not yet reviewed".
- The two top-level questions keep the shared statuses, because the 50-state list and its filter read them.

Where a state has an automatic route and an application route (New York), the label names the automatic one and the detail gives the other. A record-relief answer says when the law covers criminal records in general and is not specific to cannabis (Pennsylvania's Clean Slate).

## Evidence levels

Computed from an answer's sources and shown on every answer:

- **Official source**: every source is a statute, regulator or government page.
- **Official source and national compilation**: a mix.
- **National compilation: confirm with the state**: only national compilations (currently Ballotpedia's adult-use list, DISA's state legality map and, for employment, the Marijuana Policy Project's two state charts). The Marijuana Policy Project is an advocacy group; every answer that rests on its charts alone names it and says the state's own law has not been checked.

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
- Every state with legal adult use, and DC, answers all six detail questions (buying, possession, sharing, home grow, public use, driving) from official sources (#148): 150 of 150 cells. For states without adult use, detail rows are filled only where an official page reviewed for this pass stated them; every other cell reads "Not yet reviewed".
- Some official pages lag the law. Vermont's Cannabis Control Board FAQ still gives a 1-ounce sale limit, which Act 176 raised to 2 ounces on July 1, 2026. Delaware's Office of the Marijuana Commissioner pages still say sales are expected in 2025; they began August 1, 2025. Illinois's FAQ gives residents both 60 grams and 30 grams; the possession answer keeps the FAQ's 60 grams, and 410 ILCS 705/10-10 could not be read to settle it because `ilga.gov` is disallowed to automated readers. The other answers follow the law and the dated announcements.
- A few detail answers rest on secondary official text: Washington's sharing limits come from RCW 69.50.4013 as reprinted in a January 2026 Senate bill (the RCW page is disallowed, and the reprint's drink and concentrate items were cut off, so only the flower and solid-edible limits are named); Maryland's sharing rule comes from a 2024 legislative fiscal note's description of current law; California's possession and sharing amounts come from the Judicial Council's summary of Proposition 64 (the section page on `leginfo.legislature.ca.gov` returned an error); New Mexico's statute text is the regulator's August 2023 posting; and Oregon's ORS 475C.305 is the 2025 edition, not checked against 2026 session changes.
- Several driving answers repeat only what the cited page says (for example, open containers in California and use while driving in New Mexico). They are not a full statement of each state's impaired-driving law.
- Americans for Safe Access's state-by-state patient pages could not be retrieved on November 15, 2026 (`/states` returned an error; `/patient_guide` is disallowed to automated readers). Only its travel guide is listed.
- The Ohio, Pennsylvania and New York answers for employment and record relief (#150) come from the reviewed rule summaries in `data/directory.json` and keep the dates of those reviews (October 9 to November 5, 2026). The same summaries stay in `data/directory.json`, which the state pages are built from, so a later review should update both. Record relief is unanswered for the other 48 jurisdictions (#160).
- Employment, first top-down pass (#159): 29 of 51 jurisdictions are answered. Eight rest on official sources: Ohio, Pennsylvania and New York, plus California (Civil Rights Department FAQ, January 2024), Connecticut (the state's adult-use cannabis site), Minnesota (Minn. Stat. § 181.938), Montana (Mont. Code Ann. § 39-2-313) and Rhode Island (R.I. Gen. Laws § 21-28.11-29). Twenty-one rest on the Marijuana Policy Project's undated state charts alone: New Jersey, Nevada, Washington and DC, and 17 states its medical chart lists as protecting patients. Their own laws are the next step.
- The other 22 jurisdictions read "Not yet reviewed" for employment. The charts list no known protection for Alabama, Alaska, Colorado, Florida, Georgia, Hawaii, Kentucky, Michigan, Mississippi, Nebraska, North Dakota, Oregon and Texas; a list's silence is not enough for "Not protected", which needs an official source saying employers may act. The charts have no row for Idaho, Indiana, Iowa, Kansas, North Carolina, South Carolina, Tennessee, Wisconsin and Wyoming.
- Employment answers to recheck: California's FAQ dates from January 2024, and a 2024 bill (SB 1264) proposed a law-enforcement exception whose outcome was not checked. Connecticut's answer follows the state's plain-language pages; the statute (Conn. Gen. Stat. §§ 21a-422o to 21a-422s) was seen only in search results. The dates when Minnesota and Montana added cannabis to their lawful-product laws were not confirmed and are left blank. The medical chart's own count conflicts (27 of 41 states in its text, 24 in its page description), and its Utah citation (§ 26-61a-111) should be checked against the current code.
- Left out of those answers because no official source was reviewed for them: New York's Clean Slate waiting periods (the earlier review took three years for misdemeanors and eight for felonies from a legal-information site; a court-system page that appears to state them, `nycourts.gov/FORMS/criminal-record-sealing.shtml`, was found on November 15, 2026 and has not been reviewed), and, for Pennsylvania, two parts of the law that turned up in a November 15, 2026 search of the General Assembly's site and were not reviewed: a 10-year rule for "qualifying offense" convictions in 18 Pa.C.S. § 9122.2(a)(1.1) and the petition route in § 9122.1. Pennsylvania's answer cites the statute alone; the legal-aid FAQ that had confirmed its dates is not carried over.
- Ohio's "Not protected" rests on ORC 3796.28, which speaks only for Chapter 3796 ("nothing in this chapter"). No other Ohio employment law was reviewed.
