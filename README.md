# Ohio Cannabis Ecosystem Directory

A source-verified map of who serves what in Ohio cannabis: operators, service providers, nonprofits, and cannabis-adjacent organizations, each traced to a named source.

**Live searchable directory:** https://travisvought-byte.github.io/ohio-cannabis-directory/

The current dataset contains **564 organizations**, including **518 publishable organizations across 16 categories** and 46 deliberately retained out-of-scope records. Those retained records keep renamed, acquired, superseded, or otherwise relevant organizations findable. The repository also includes 60 documented business-to-business relationships.

The home screen lists confirmed events within the next three months directly in the generated HTML and refreshes that date window when opened. It also features the Midwest CannaWomen community.

The site uses an Ohio State scarlet-and-gray color palette with accessible contrast and no university logos or marks.

Maintained by Travis Vought.

The election-season Libertarian Party of Ohio entry is a clearly labeled personal, unpaid endorsement by the directory maintainer, not a paid placement or party sponsorship.

## What this is

This is a flat, categorized market map, not a CRM. One row represents one organization. Each entry records what the organization does, how to reach it, where the information came from, and capability keywords for problem-oriented searching.

If you need mold remediation, cash logistics, packaging, MRB banking, staffing, compliance support, or another specific service, search the capability rather than guessing the category.

## Repository contents

| File | Contents |
| --- | --- |
| `index.html` | Main searchable directory. Self-contained and usable offline. |
| `intake.html` | Field/offline intake page for capturing and exporting candidate organizations. |
| `ohio-cannabis-directory.csv` | All 564 directory rows with contact, provenance, notes, verification, and capability fields. |
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

Use the repository's [Add or correct a listing intake](https://github.com/travisvought-byte/ohio-cannabis-directory/issues/new/choose).

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
```

## Licensing

Directory data is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may copy it, build on it, redistribute it, or use it commercially with attribution.

The site code and build scripts are released under the MIT License.

**Attribution:** Ohio Cannabis Ecosystem Directory, compiled by Travis Vought.
