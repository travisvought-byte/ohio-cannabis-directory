# Ohio Cannabis Ecosystem Directory

A source-verified map of who serves what in Ohio cannabis: operators, service providers, nonprofits, and cannabis-adjacent organizations, each traced to a named source.

**Live searchable directory:** https://travisvought-byte.github.io/ohio-cannabis-directory/

The current dataset contains **564 organizations**, including **516 publishable organizations across 16 categories** and 48 deliberately retained out-of-scope records. Those retained records keep renamed, acquired, superseded, or otherwise relevant organizations findable. The repository also includes 60 documented business-to-business relationships.

**Current site release:** 4.29 · October 10, 2026.

Searches and filters persist in shareable URLs. Every organization has a permanent record link. [Who works with whom?](https://travisvought-byte.github.io/ohio-cannabis-directory/relationships.html) makes all 60 documented relationships searchable, with organization links and source evidence.

The home screen lists confirmed events within the next three months directly in the generated HTML and refreshes that date window when opened. Events with unverified links are withheld.

The site uses an Ohio State scarlet-and-gray color palette with accessible contrast and no university logos or marks.

![Veteran Home Guardians](assets/vhg-logo.png)

**Created, compiled, and maintained by Travis Vought.** Shared as a free public resource in support of [Veteran Home Guardians](https://vethomeguard.org/). This distinguishes Travis's project-development work from VHG's charitable use and outreach; see [Project stewardship, attribution, and reuse](PROJECT_STEWARDSHIP.md).

**Commission custom work:** [Research, market maps, custom directories, and data maintenance by Travis Vought](https://travisvought-byte.github.io/ohio-cannabis-directory/work-with-travis.html) are offered separately from VHG donations and sponsorships. The free public directory and its licenses are unchanged.

The election-season Libertarian Party of Ohio entry is a clearly labeled personal, unpaid endorsement by the directory maintainer, not a paid placement or party sponsorship.

## What this is

The public organization view retains one row per original organization. Its canonical source is now `data/directory.json`, separating organizations, service routes, evidence, relationships, rules and state configuration. Compatibility CSVs preserve the original fields, IDs and provenance.

If you need mold remediation, cash logistics, packaging, MRB banking, staffing, compliance support, or another specific service, search the capability rather than guessing the category.

## Repository contents

| File | Contents |
| --- | --- |
| `index.html` | Main searchable directory. Self-contained and usable offline. |
| `intake.html` | Field/offline intake page for capturing and exporting candidate organizations; duplicate checks use all 564 current records. |
| `relationships.html` | Searchable relationships, organization links and supporting evidence. |
| `release.json` | Shared version and publication date; changing this does not imply re-verifying every record. |
| `ohio-cannabis-directory.csv` | All 564 directory rows with contact, provenance, notes, verification, capability, permanent Record ID and Last Reviewed fields. |
| `b2b-relationships.csv` | 60 documented organization-to-organization relationships with supporting evidence. |
| `build_directory.py` | Regenerates `index.html` from the repository CSV. |
| `build_intake.py` | Regenerates the field intake page. |
| `.github/ISSUE_TEMPLATE/` | Structured public intake forms for additions, corrections, status changes, and B2B relationships. |
| `CONTRIBUTING.md` | Contribution, sourcing, and verification standards. |
| `CHANGELOG.md` | Release and version history. |
| `CITATION.cff` | Machine-readable citation metadata for the dataset. |
| `LICENSE` | CC BY 4.0 terms for data and MIT terms for code. |
| `.zenodo.json` | Metadata used by Zenodo when archiving a GitHub release. |

The public HTML pages contain the directory data they need, so the searchable site does not depend on a live database or external API at runtime. The upcoming-events card checks its date window in the visitor’s browser.

## How entries are verified

The directory was seeded from the Ohio Cannabis Expo CRM, then expanded category by category through structured research passes and deduplicated against organization name and website domain.

Contact information is separated into `Email`, `Phone`, and `Website` fields. Verification evidence is stored separately in `Source(s)`, and each entry retains a `Seed Source` showing how it first entered the dataset.

`Verification Tier` distinguishes source-verified rows from records carrying a specific open issue. When something is unresolved, the `Notes` field identifies the unresolved fact rather than expressing general uncertainty.

The headline count is a count of publishable rows, not a claim that every retained row is a distinct currently operating company. Aliases, acquired brands, superseded names, and provenance-preserving out-of-scope records may remain searchable by design.

## Corrections and additions

Email listing additions, corrections or relationship updates to [VeteranHomeGuardians@gmail.com](mailto:VeteranHomeGuardians@gmail.com). Include the organization name or listing link, the requested change and a website or source. For several updates, attach the exported intake CSV.

You can also use the repository's [GitHub issue forms](https://github.com/travisvought-byte/ohio-cannabis-directory/issues/new/choose).

Choose the form that matches what you found:

- Add an organization.
- Correct an existing record.
- Report a closure, rename, acquisition, merger, or other status change.
- Add or correct a documented B2B relationship.

Include a named source whenever possible. Submissions are treated as research leads until verified and are not automatically promoted into the published dataset.

GitHub issue forms require a GitHub account. `intake.html` is a separate field/offline capture tool; it stores records on the device until they are exported.

## Rebuilding

The directory build script reads the repository CSV and writes `index.html` in place.

```bash
pip install pandas
python build_directory.py
python build_intake.py
python build_relationships.py
python tests/check_data.py
npm ci
npm test
npm run test:browser
```

`Last Reviewed` records an established evidence-review date, not a promise of present availability. Eight October 6 additions have dates supported by their audit; undated legacy records keep their original provenance until a review date is established. Preserve Record ID when correcting or renaming an existing organization.

The public build uses the date in `release.json` and is reproducible. GitHub Actions verifies CSV/page synchronization, release metadata, phone normalization, URL filters, relationship navigation, offline intake/export, mobile width and print behavior.

## Licensing

Directory data is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may copy it, build on it, redistribute it, or use it commercially with attribution.

The site code and build scripts are released under the MIT License.

**Attribution:** Ohio Cannabis Ecosystem Directory, compiled by Travis Vought.

**Independent work:** The free directory and existing open licenses remain unchanged. Customized implementations, new research, training, and other separately commissioned professional services are distinct from VHG donations or sponsorships. See [project stewardship](PROJECT_STEWARDSHIP.md).

## Consumer resources

The homepage now offers six need-based routes through [consumer resources](https://travisvought-byte.github.io/ohio-cannabis-directory/resources.html): dispensaries, seeds and growing supplies, record clearing, medical patients, Ohio rules, and community connections. Sources reviewed October 10, 2026. Opportunity Port is labeled Franklin County only; seed catalogs do not imply verified Ohio delivery. These referral resources are separate from organization counts. Regenerate with `python build_resources.py`. The location finder now offers optional distance sorting over a dated government-map snapshot; operating status and completeness still need confirmation.

Seed supplier expansion: `seeds.html` offers 11 entries (10 seed providers and one Ohio grow-supply / retailer lead), location and seed-type filters, text search and downloadable source data in `seed-suppliers.json`. Regenerate with `python build_seeds.py`. Shipping evidence is labeled without inferring legal eligibility.

## Multi-state foundation (stage one)

The [shared directory contract](architecture/STATE_DIRECTORY_CONTRACT.md) defines seven visitor pathways, organization/location/service boundaries, claim-level evidence and state publication gates. The schema and validated seed/supply pilot live in `schemas/` and `data/foundation/`. The stage-one pilot remains available as a contract fixture. The full Ohio migration now uses the same contract; no additional state coverage is announced. Run `python validate_foundation.py` and `python tests/foundation.py`.

## Shared state view (stage two)

[Explore by state and need](https://travisvought-byte.github.io/ohio-cannabis-directory/state.html?state=OH). One shared template serves reviewed state packs. Ohio is currently the only public state. `data/directory.json` is authoritative; the CSVs and seed JSON are generated compatibility downloads. All 564 original organization records and 60 relationship IDs are preserved. See [migration and maintenance instructions](architecture/STAGE_TWO_MIGRATION.md).

### Location search

[Find dispensary locations](https://travisvought-byte.github.io/ohio-cannabis-directory/locations.html?state=OH) supports city, county, address/ZIP search, shareable filters, directions and optional straight-line distance sorting. The 230 records are a government map snapshot retrieved 2026-10-10, not a claim of complete or currently operational coverage. Source update date is unknown; license status remains unknown. Three invalid source coordinate pairs are omitted from distance sorting.

`data/sources/ohio-dispensaries.json` preserves the original response. Run `python import_locations.py`, `python validate_foundation.py data/directory.json`, then `python build_locations.py` after reviewing a replacement snapshot. Stable location IDs derive from state and license number; legal entities match only by exact unique name. No store hours or inventory claims are imported.

## Growing strain guide and ancestry repository

`ancestry.html` contains 336 source-linked profiles covering 318 distinct names, starting with 100 classics and adding producer-specific flower catalogs and dated Ohio menu observations. Filters cover producer, menu evidence, type, sensory reports and review status. This is an unranked educational selection, with no fixed count cap or live-stock claim. `data/strains/strains.csv` exports the profiles; `ohio-flower.csv` exports 27 dated observations. The canonical JSON retains attributed ancestry, separate identities and conflict-review notes. See `data/strains/README.md` for research and maintenance rules.

### Cannabis knowledge

`knowledge.html` provides 30 searchable explanations and buying tips covering definitions, product forms, processing, label units, batch reports and storage. General concepts cite public-health agencies and testing laboratories; Ohio labeling guidance cites the September 11, 2026 rule. Shared learning links connect every directory page with the strain library and knowledge hub. Rebuild with `python build_knowledge.py`; content and sources live in `data/knowledge.json`.

## Veteran and family resources

Visit the [VHG Veteran Resident Guide](https://travisvought-byte.github.io/vhg-veteran-resident-guide/) for veteran, senior and disability support resources.

## Shopping guide, business assessment and click analytics

`buyer-guide.html` builds a personalized first-visit plan for printing or PDF download, with questions to ask the dispensary and an optional supply calculator: amount purchased ÷ personal daily use, with ounce-to-gram conversion and a per-use × uses-per-day helper. PDF libraries and the embedded font load locally only when downloading; answers stay on the device. Rebuild with `python build_tools.py`. The longer educational reference remains at `assets/dispensary-shopping-guide.pdf` (rebuild that reference with `python build_buyer_pdf.py`, requiring ReportLab).

`assessment.html` adapts Travis Vought's 33-question **Cannabis Financial Access & Compliance Readiness Assessment v2** from Google Drive, dated August 27, 2026. Only blank questions, evidence prompts and weights are imported into `data/business-assessment.json`; regulatory references remain explicitly dated. Scores and notes live in browser memory, with export and print controls. Unanswered questions do not count as zero and incomplete assessments receive a partial score without an overall rating. This does not certify compliance or bank eligibility.

`assets/analytics.js` sends aggregate GoatCounter events for navigation, downloads, external domains, contact actions, filters and search use. It does not transmit search text, form answers, evidence notes, coordinates or destination query strings. Pageview paths exclude query strings. Events appear as `action:<page>:<action>` in the existing GoatCounter dashboard. Counts begin after deployment and may be reduced by blockers or a failed analytics script. See `architecture/ANALYTICS.md`.
