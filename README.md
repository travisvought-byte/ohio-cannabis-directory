# Ohio Cannabis Ecosystem Directory

A source-verified map of who serves what in Ohio cannabis: operators, service providers, nonprofits, and cannabis-adjacent organizations, each traced to a named source.

**Live searchable directory:** https://travisvought-byte.github.io/ohio-cannabis-directory/

The current dataset contains **564 organizations**, including **518 publishable organizations across 16 categories** and 46 deliberately retained out-of-scope records. Those retained records keep renamed, acquired, superseded, or otherwise relevant organizations findable. The repository also includes 60 documented business-to-business relationships.

**Current site release:** 4.21 · October 9, 2026.

Searches and filters persist in shareable URLs. Every organization has a permanent record link. [Who works with whom?](https://travisvought-byte.github.io/ohio-cannabis-directory/relationships.html) makes all 60 documented relationships searchable, with organization links and source evidence.

The home screen lists confirmed events within the next three months directly in the generated HTML and refreshes that date window when opened. It also features the Midwest CannaWomen community.

The site uses an Ohio State scarlet-and-gray color palette with accessible contrast and no university logos or marks.

![Veteran Home Guardians](assets/vhg-logo.png)

A [Veteran Home Guardians](https://vethomeguard.org/) resource, maintained by Travis Vought.

The election-season Libertarian Party of Ohio entry is a clearly labeled personal, unpaid endorsement by the directory maintainer, not a paid placement or party sponsorship.

## What this is

This is a flat, categorized market map, not a CRM. One row represents one organization. Each entry records what the organization does, how to reach it, where the information came from, and capability keywords for problem-oriented searching.

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

## Consumer resources

The homepage now offers six need-based routes through [consumer resources](https://travisvought-byte.github.io/ohio-cannabis-directory/resources.html): dispensaries, seeds and growing supplies, record clearing, medical patients, Ohio rules, and community connections. Sources reviewed October 9, 2026. Opportunity Port is labeled Franklin County only; seed catalogs do not imply verified Ohio delivery. These referral resources are separate from organization counts. Regenerate with `python build_resources.py`. Nearby distance search and a current statewide location import remain future work.

Seed supplier expansion: `seeds.html` offers 11 entries (10 seed providers and one Ohio grow-supply / retailer lead), location and seed-type filters, text search and downloadable source data in `seed-suppliers.json`. Regenerate with `python build_seeds.py`. Shipping evidence is labeled without inferring legal eligibility.

## Multi-state foundation (stage one)

The [shared directory contract](architecture/STATE_DIRECTORY_CONTRACT.md) defines seven visitor pathways, organization/location/service boundaries, claim-level evidence and state publication gates. The schema and validated seed/supply pilot live in `schemas/` and `data/foundation/`. This is preparation for stage-two migration, not a replacement for the current Ohio dataset or an announcement of additional state coverage. Run `python validate_foundation.py` and `python tests/foundation.py`.
