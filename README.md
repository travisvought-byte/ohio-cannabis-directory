# Ohio Cannabis Ecosystem Directory

A source-verified map of who serves what in Ohio cannabis: operators, service providers, nonprofits, and cannabis-adjacent organizations, each traced to a named source.

**Live searchable directory:** https://travisvought-byte.github.io/ohio-cannabis-directory/

The current dataset contains **565 organizations**, including **516 publishable organizations across 16 categories**, 48 deliberately retained out-of-scope records, and one withdrawn public listing. Those retained records keep renamed, acquired, superseded, or otherwise relevant organizations findable. The repository also includes 60 documented business-to-business relationships.

**Current site release:** 4.37 · October 21, 2026.

Searches and filters persist in shareable URLs. Every organization has a permanent record link. [Who works with whom?](https://travisvought-byte.github.io/ohio-cannabis-directory/relationships.html) makes all 60 documented relationships searchable, with organization links and source evidence.

**Directory-first navigation:** the root URL takes visitors directly to the searchable Ohio industry directory. Its search covers organizations, named contacts, services and locations; filters, permanent record URLs, and the full source-linked directory remain available. Upcoming events appear prominently beneath the directory search, with the Women’s Cannabis & Wellness Expo featured first and expired events removed automatically. Eight business-help shortcuts offer banking, accounting, legal/licensing, testing, packaging, staffing, insurance and security routes. Reviewed provider cards show whom they serve and what coverage still needs confirmation. Consumer resources and educational tools remain available through shared navigation.

The site uses an Ohio State scarlet-and-gray color palette with accessible contrast and no university logos or marks.

![Veteran Home Guardians](assets/vhg-logo.png)

Created and maintained by [Travis Vought](https://travisvought-byte.github.io/ohio-cannabis-directory/work-with-travis.html), and shared in support of [Veteran Home Guardians](https://vethomeguard.org/). [Project stewardship and reuse](PROJECT_STEWARDSHIP.md).

The Libertarian Party of Ohio appears as a neutral political-party and cannabis-policy listing in normal alphabetical order. Ohio event speakers, sponsors, partners and direct contacts may be retained as ecosystem connections; that evidence does not by itself establish Ohio service coverage.

## November 2026 retail fundraiser

Invite retailers to run a voluntary roundup, top-up or donation campaign for Veteran Home Guardians during November, celebrating the **Marine Corps birthday (November 10)** and **Veterans Day (November 11)**. [Campaign options and contact](https://travisvought-byte.github.io/ohio-cannabis-directory/november-campaign.html). Coordinate with **travis@vethomeguard.org** before launching.

## What this is

The canonical dataset retains every original organization ID. Owner-confirmed withdrawals are excluded from public listing views, intake indexes and compatibility CSVs; the original record remains in repository history. Its canonical source is now `data/directory.json`, separating organizations, service routes, evidence, relationships, rules and state configuration. Compatibility CSVs preserve the original fields, IDs and provenance.

If you need mold remediation, cash logistics, packaging, MRB banking, staffing, compliance support, or another specific service, search the capability rather than guessing the category.

Historical counts in the changelog describe those releases, not the current dataset. Published GitHub archives are listed on the [Releases page](https://github.com/travisvought-byte/ohio-cannabis-directory/releases); a site version does not automatically create an archived release. Zenodo metadata is prepared in the repository, but no issued DOI is claimed.

## Repository contents

| File | Contents |
| --- | --- |
| `index.html` | Directory-first entry point that forwards visitors to `directory.html` while preserving query parameters and record links. |
| `intake.html` | Field/offline intake page for capturing and exporting candidate organizations; duplicate checks use the 564 non-withdrawn records. |
| `relationships.html` | Searchable relationships, organization links and supporting evidence. |
| `release.json` | Shared version and publication date; changing this does not imply re-verifying every record. |
| `ohio-cannabis-directory.csv` | 564 non-withdrawn directory rows with contact, provenance, notes, verification, capability, permanent Record ID and Last Reviewed fields. |
| `b2b-relationships.csv` | 60 documented organization-to-organization relationships with supporting evidence. |
| `build_directory.py` | Regenerates the searchable `directory.html` from the repository data. |
| `build_intake.py` | Regenerates the field intake page. |
| `.github/ISSUE_TEMPLATE/` | Structured public intake forms for additions, corrections, status changes, and B2B relationships. |
| `CONTRIBUTING.md` | Contribution, sourcing, and verification standards. |
| `CHANGELOG.md` | Release and version history. |
| `CITATION.cff` | Machine-readable citation metadata for the dataset. |
| `LICENSE` | CC BY 4.0 terms for data and MIT terms for code. |
| `.zenodo.json` | Metadata used by Zenodo when archiving a GitHub release. |

The public site works without an external directory API. The primary industry directory loads its published organization data from a static JSON file; its query and filters run locally in the browser.

## Evidence-review priorities

Review work is prioritized ahead of catalog expansion. Under the [review policy](architecture/REVIEW_POLICY.md), Ohio operators, testing labs and Ohio-based providers receive a full review every 90 days, national and multistate vendors a routine verification every 180 days, and any reported closure, license action, ownership change or material correction an immediate review. The [review queue](architecture/REVIEW_QUEUE.md) ranks named open issues, undated Ohio operators/labs/community resources, missing websites, and remaining business providers. The October 12 batch reviewed 10 previously undated listings. The October 13 contact batch added four missing website routes and dated two more previously undated listings. A further 42 scoped contact/service reviews established dates for 40 previously undated listings, leaving four public listings without a recorded review date and four without a website. Eight attempted reviews remain blocked or incomplete; blocked attempts receive no fresh date. Missing websites now enter P1 independently of an existing review date. Field-level sources, changes and unresolved limits are preserved in `data/reviews/`; a review date does not imply that every contact, license, inventory or shipping claim was reverified. Blocked retrievals remain in the queue without a new review date. Regenerate with `python build_review_queue.py`.

## How entries are verified

The directory was seeded from the Ohio Cannabis Expo CRM, then expanded category by category through structured research passes and deduplicated against organization name and website domain.

Contact information is separated into `Email`, `Phone`, and `Website` fields. Verification evidence is stored separately in `Source(s)`, and each entry retains a `Seed Source` showing how it first entered the dataset.

`Verification Tier` distinguishes source-verified rows from records carrying a specific open issue. When something is unresolved, the `Notes` field identifies the unresolved fact rather than expressing general uncertainty.

The headline count is a count of publishable rows, not a claim that every retained row is a distinct currently operating company. Aliases, acquired brands, superseded names, and provenance-preserving out-of-scope records may remain searchable by design.

## Corrections and additions

Email listing additions, corrections or relationship updates to [VeteranHomeGuardians@gmail.com](mailto:VeteranHomeGuardians@gmail.com). Include the organization name or listing link, the requested change and a website or source. For several updates, attach the exported intake CSV.

Submit Ohio events using the directory’s event email link or the event issue form. Dates, venues and organizer links are reviewed before publication; see [event maintenance](architecture/EVENT_MAINTENANCE.md).

You can also use the repository's [GitHub issue forms](https://github.com/travisvought-byte/ohio-cannabis-directory/issues/new/choose).

Choose the form that matches what you found:

- Add an organization.
- Correct an existing record.
- Report a closure, rename, acquisition, merger, or other status change.
- Add or correct a documented B2B relationship.

Include a named source whenever possible. Submissions are treated as research leads until verified and are not automatically promoted into the published dataset.

GitHub issue forms require a GitHub account. `intake.html` is a separate field/offline capture tool; it stores records on the device until they are exported.

## Rebuilding

The directory builder generates `directory.html`; `build_home.py` generates the root `index.html` entry point, which forwards readers to the industry directory.

```bash
pip install -r requirements.txt
python export_directory.py
python release_tools.py 4.37 2026-10-21
python tests/check_data.py
npm ci
npm test
npm run test:browser
```

`Last Reviewed` records an established evidence-review date, not a promise of present availability. Eight October 6 additions have dates supported by their audit; undated legacy records keep their original provenance until a review date is established. Preserve Record ID when correcting or renaming an existing organization.

The rebuild requires only files in this repository, with `data/directory.json` as the authoritative source; no local workbook is needed. `export_directory.py` regenerates the compatibility downloads. Use the existing version/date from `release.json` when rebuilding without publishing a new version.

The public build uses the date in `release.json` and is reproducible. GitHub Actions verifies CSV/page synchronization, release metadata, phone normalization, URL filters, relationship navigation, offline intake/export, mobile width and print behavior.

## Licensing

Directory data is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may copy it, build on it, redistribute it, or use it commercially with attribution.

The site code and build scripts are released under the MIT License.

**Attribution:** Ohio Cannabis Ecosystem Directory, compiled by Travis Vought.

**Independent work:** The free directory and existing open licenses remain unchanged. Customized implementations, new research, training, and other separately commissioned professional services are distinct from VHG donations or sponsorships. See [project stewardship](PROJECT_STEWARDSHIP.md).

## Consumer resources

The secondary [consumer resources](https://travisvought-byte.github.io/ohio-cannabis-directory/resources.html) page offers six need-based routes: dispensaries, seeds and growing supplies, record clearing, medical patients, Ohio rules, and community connections. Sources reviewed October 10, 2026. Opportunity Port is labeled Franklin County only; seed catalogs do not imply verified Ohio delivery. These referral resources are separate from organization counts. Regenerate with `python build_resources.py`. The location finder now offers optional distance sorting over a dated government-map snapshot; operating status and completeness still need confirmation.

Seed supplier expansion: `seeds.html` offers 11 entries (10 seed providers and one Ohio grow-supply / retailer lead), location and seed-type filters, text search and downloadable source data in `seed-suppliers.json`. Regenerate with `python build_seeds.py`. Shipping evidence is labeled without inferring legal eligibility.

## Multi-state foundation (stage one)

The [shared directory contract](architecture/STATE_DIRECTORY_CONTRACT.md) defines seven visitor pathways, organization/location/service boundaries, claim-level evidence and state publication gates. The schema and validated seed/supply pilot live in `schemas/` and `data/foundation/`. The stage-one pilot remains available as a contract fixture. The full Ohio migration now uses the same contract; no additional state coverage is announced. Run `python validate_foundation.py` and `python tests/foundation.py`.

## Shared state view (stage two)

[Explore by state and need](https://travisvought-byte.github.io/ohio-cannabis-directory/state.html?state=OH). One shared template serves reviewed state packs. Ohio is currently the only public state. `data/directory.json` is authoritative; the CSVs and seed JSON are generated compatibility downloads. All 564 original organization records and 60 relationship IDs are preserved. See [migration and maintenance instructions](architecture/STAGE_TWO_MIGRATION.md).

### Location search

[Find dispensary locations](https://travisvought-byte.github.io/ohio-cannabis-directory/locations.html?state=OH) supports city, county, address/ZIP search, shareable filters, directions and optional straight-line distance sorting. The 230 records are a government map snapshot retrieved 2026-10-10, not a claim of complete or currently operational coverage. Source update date is unknown; license status remains unknown. Cards now expose 228 government-snapshot phones, explicitly labeled when not freshly reviewed. Fifteen stores also have operator-published menu links, with medical and adult-use routes distinguished where supplied. Prices and stock remain on the operator’s site. Twenty stores have first-party-reviewed phones, store websites and brand links to the business directory, checked October 13, 2026. The Garfield Heights Terrasana address is corrected to the operator-published 9601 Vista Way. Three invalid source coordinate pairs and the superseded Garfield Heights coordinate pair are omitted from distance sorting.

`data/sources/ohio-dispensaries.json` preserves the original response. Run `python import_locations.py`, `python validate_foundation.py data/directory.json`, then `python build_locations.py` after reviewing a replacement snapshot. Stable location IDs derive from state and license number; legal entities match only by exact unique name. No store hours or inventory claims are imported. `data/sources/location-contacts.json` preserves reviewed store contacts separately; importing a replacement map rejects changed address/city matches until the contact overlay is re-reviewed. The original map legal entity remains separate from the public brand link.

## Growing strain guide and ancestry repository

`ancestry.html` contains 336 source-linked profiles covering 318 distinct names, starting with 100 classics and adding producer-specific flower catalogs and dated Ohio menu observations. Filters cover producer, menu evidence, type, sensory reports and review status. This is an unranked educational selection, with no fixed count cap or live-stock claim. `data/strains/strains.csv` exports the profiles; `ohio-flower.csv` exports 27 dated observations. The canonical JSON retains attributed ancestry, separate identities and conflict-review notes. See `data/strains/README.md` for research and maintenance rules.

### Cannabis knowledge

`knowledge.html` provides 30 searchable explanations and buying tips covering definitions, product forms, processing, label units, batch reports and storage. General concepts cite public-health agencies and testing laboratories; Ohio labeling guidance cites the September 11, 2026 rule. A direct Strains link now appears in shared primary navigation and the footer, connecting every directory page with the strain library and knowledge hub. Rebuild with `python build_knowledge.py`; content and sources live in `data/knowledge.json`.

## State comparison

[Compare Ohio with other states](https://travisvought-byte.github.io/ohio-cannabis-directory/compare.html) has two layers. **Laws side by side** shows each state's rule on a topic with its citation, effective date and the date it was checked. **Lessons from other markets** records what happened elsewhere, the conditions that drove it, whether Ohio shares those conditions, and the directory's assessment of whether Ohio is likely to face the same problem. Assessments are labeled as analysis and use a fixed likelihood scale, a stated confidence level and a review date. Each lesson ends with a letter Ohio residents can send their own lawmakers. The first lesson covers oversupply and falling prices in Michigan, compared with Ohio and Oregon.

Canonical data is `data/state-comparison.json`. `python validate_comparison.py` rejects uncited facts, law entries without a statute, regulator or government source, assessments outside the scale, and reviews older than 120 days. Regenerate the page with `python build_compare.py`.

## Ohio cannabis advocacy

[Have a say in Ohio cannabis policy](https://travisvought-byte.github.io/ohio-cannabis-directory/advocacy.html) connects readers to the official state lawmaker lookup, explains legislative, DCC, JCARR and local decision-making, and offers source-linked reform requests for consumption lounges, out-of-state product restrictions, ordinary accessories and clearer SB 56 rules. Sources checked October 12, 2026. Reform requests are distinguished from current law.

The letter builder starts with one issue, offers a confirmed-constituent or Ohio-resident introduction, and supports an editable draft, clipboard fallback, text download and letter-only printing. Call scripts, follow-up messages, a suggested follow-up date and downloadable private notes help readers complete the next step. It does not send messages, store entries or send personal text to analytics. Hearing and rule-comment guides direct readers to official notices for current submission details. Regenerate with `python build_advocacy.py` and verify with `node tests/advocacy-browser.cjs`.

[Ohio lawmakers and SB 56 votes](https://travisvought-byte.github.io/ohio-cannabis-directory/lawmakers.html) covers all 132 state legislative districts: 130 named current lawmakers and two vacancies in the official October 12, 2026 roster. Search by name, district or role; filter by chamber, party, selected committee/leadership/sponsor role and final SB 56 vote. Each occupied-seat card links to the official contact form and a pre-addressed letter. The snapshot includes 129 published office phones; Sean Hutson's reviewed profile/contact page has no published office phone, so his listing uses the official form.

`data/legislators.json` preserves official field sources, review dates and all nine SB 56 roll calls. Final conference votes are distinguished from earlier floor and committee actions. Former members remain in historical votes without inheriting those votes into the current district holder's listing. Roles cover chamber leadership, SB 56 sponsorship, and Judiciary, Finance, General Government, and Rules and Reference; this is not a full committee inventory. `import_legislators.py` refreshes official sources with a date-scoped temporary cache; review its resulting diff before publishing. Run `python validate_legislators.py`, `python build_lawmakers.py`, and `node tests/lawmakers-browser.cjs`. The generated HTML includes a complete names/contact fallback when JavaScript or the data fetch is unavailable.

## Veteran and family resources

Visit the [VHG Veteran Resident Guide](https://travisvought-byte.github.io/vhg-veteran-resident-guide/) for veteran, senior and disability support resources.

## Shopping guide, business assessment and click analytics

`buyer-guide.html` builds a personalized first-visit plan for printing or PDF download, with questions to ask the dispensary and an optional supply calculator: amount purchased ÷ personal daily use, with ounce-to-gram conversion and a per-use × uses-per-day helper. PDF libraries and the embedded font load locally only when downloading; answers stay on the device. Rebuild with `python build_tools.py`. The longer educational reference remains at `assets/dispensary-shopping-guide.pdf` (rebuild that reference with `python build_buyer_pdf.py`, requiring ReportLab).

`assessment.html` adapts Travis Vought's 33-question **Cannabis Financial Access & Compliance Readiness Assessment v2** from Google Drive, dated August 27, 2026. Only blank questions, evidence prompts and weights are imported into `data/business-assessment.json`; regulatory references remain explicitly dated. Scores and notes live in browser memory, with export and print controls. Unanswered questions do not count as zero and incomplete assessments receive a partial score without an overall rating. This does not certify compliance or bank eligibility.

`assets/analytics.js` sends aggregate GoatCounter events for navigation, downloads, external domains, contact actions, filters and search use. It does not transmit search text, form answers, evidence notes, coordinates or destination query strings. Pageview paths exclude query strings. Events appear as `action:<page>:<action>` in the existing GoatCounter dashboard. Counts begin after deployment and may be reduced by blockers or a failed analytics script. See `architecture/ANALYTICS.md`.

### Expungement and record sealing

[Record-clearing guide](https://travisvought-byte.github.io/ohio-cannabis-directory/expungement.html), reviewed October 18, 2026: a route finder, marijuana-specific and general pathways, common waiting periods, route-specific fees and indigency relief, court preparation, printable checklist, and follow-up. Opportunity Port remains Franklin County only. Route suggestions are not eligibility determinations; no personal case information is collected or stored by the guide. Sources are linked beside the content; local forms come from the filing court. Rebuild with `python build_expungement.py`.

The expanded walkthrough reads actual Franklin Municipal and Hamilton Municipal/Common Pleas application packets: record-request and packet-confirmation scripts, field-by-field application help, filing/service responsibilities, investigation and hearing preparation, a fictional marijuana worked example, and a printable per-case worksheet. Delaware Common Pleas confidential-identifier requirements and Morrow Municipal service rules are distinguished from unverified local packet details. Older general forms are not presented as confirmed 2953.321 forms. Research provenance is recorded in `data/research/record-clearing-2026-10-18.json`.

The default record-clearing page is a six-step checklist in plain language. Detailed route rules, court packets, worked example and worksheet are collapsed behind specific help questions; links open the relevant explanation. Printing produces the short checklist instead of the full research material.

Step one includes county-filtered official online case-search links and application/filing links for selected courts in Morrow, Knox, Delaware, Franklin and Hamilton counties. The all-county court directory and BCI personal-record instructions provide fallback routes. Instructions distinguish confirmed links from packets/search screens not fully inspected. Maintain the source links and review dates in `data/record-clearing-courts.json`; the builder includes a complete no-JavaScript list.

Each of the six record-clearing steps now includes collapsed, task-specific help, concrete completion checks, and a route for missing information or setbacks. Added general eligibility interview, accepted-form fallback, official fee-waiver forms, service/filing confirmation, interpreter and local accommodation help, record correction, background-report disputes, and lawyer referral if aid cannot assist. External-link availability and remaining local verification limits are tracked in `data/research/record-clearing-step-audit-2026-10-18.json`.
