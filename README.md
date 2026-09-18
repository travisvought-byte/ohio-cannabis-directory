Ohio Cannabis Ecosystem Directory

A source-verified map of who serves what in Ohio cannabis: operators, service providers, nonprofits, and cannabis-adjacent organizations, each traced to a named source.

Live searchable directory: https://travisvought-byte.github.io/ohio-cannabis-directory/

The current dataset contains 511 organizations, including 465 publishable organizations across 16 categories and 46 deliberately retained out-of-scope records so renamed, acquired, superseded, or otherwise relevant organizations remain findable. It also includes 60 documented business-to-business relationships.

Maintained by Travis Vought.

What this is

A flat, categorized market map, not a CRM. One row represents one organization. Each entry records what the organization does, how to reach it, where the information came from, and a capabilities field for problem-oriented searching.

If you need mold remediation, cash logistics, packaging, MRB banking, staffing, compliance support, or another specific service, search the capability rather than guessing the category.

Repository contents

|File                         |Contents                                                                                         |
|-----------------------------|-------------------------------------------------------------------------------------------------|
|`index.html`                 |Main searchable directory. Self-contained and usable offline.                                    |
|`intake.html`                |Field/offline intake page for capturing and exporting candidate organizations.                   |
|`ohio-cannabis-directory.csv`|All 511 directory rows with contact, provenance, notes, verification, and capability fields.     |
|`b2b-relationships.csv`      |60 documented organization-to-organization relationships with supporting evidence.               |
|`build_directory.py`         |Regenerates the searchable directory HTML from the master workbook.                              |
|`build_intake.py`            |Regenerates the field intake page from the master workbook.                                      |
|`.github/ISSUE_TEMPLATE/`    |Structured public intake forms for additions, corrections, status changes, and B2B relationships.|
|`CONTRIBUTING.md`            |Contribution, sourcing, and verification standards.                                              |
|`CHANGELOG.md`               |Release and version history.                                                                     |
|`CITATION.cff`               |Machine-readable citation metadata for the dataset.                                              |
|`LICENSE`                    |CC BY 4.0 terms for data and MIT terms for code.                                                 |
|`.zenodo.json`               |Metadata used by Zenodo when archiving a GitHub release.                                         |

The public HTML pages contain the directory data they need, so the searchable site does not depend on a live database or external API at runtime.

How entries are verified

The directory was seeded from the Ohio Cannabis Expo CRM, then expanded category by category through structured research passes and deduplicated against organization name and website domain.

Contact information is separated into Email, Phone, and Website fields. Verification evidence is stored separately in Source(s), and each entry retains a Seed Source showing how it first entered the dataset.

Verification Tier distinguishes source-verified rows from records carrying a specific open issue. When something is unresolved, the Needs Research field identifies the unresolved fact rather than expressing general uncertainty.

The headline count is a count of publishable rows, not a claim that every retained row is a distinct currently operating company. Aliases, acquired brands, superseded names, and provenance-preserving out-of-scope records may remain searchable by design.

Corrections and additions

Use the repository’s Add or correct a listing intake:

https://github.com/travisvought-byte/ohio-cannabis-directory/issues/new/choose

Choose the form that matches what you found:

• add an organization
• correct an existing record
• report a closure, rename, acquisition, merger, or other status change
• add or correct a documented B2B relationship

Include a named source whenever possible. Submissions are treated as research leads until verified and are not automatically promoted into the published dataset.

GitHub issue forms require a GitHub account. intake.html is a separate field/offline capture tool; it stores records on the device until they are exported.

Rebuilding

The build scripts currently expect the local master workbook used to generate this release. If you are rebuilding from another copy, update the source and output paths near the top of each script before running it.

```bash
pip install pandas openpyxl
python build_directory.py
python build_intake.py
```

Licensing

Directory data is released under CC BY 4.0. You may copy it, build on it, redistribute it, or use it commercially with attribution.

The site code and build scripts are released under the MIT License.

Attribution: Ohio Cannabis Ecosystem Directory, compiled by Travis Vought.
