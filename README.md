# Ohio Cannabis Ecosystem Directory

A source-verified map of who serves what in Ohio cannabis: operators, service providers, nonprofits, and cannabis-adjacent organizations, each traced to a named source.

**Live searchable directory:** https://travisvought-byte.github.io/ohio-cannabis-directory/  
*The link will become active once GitHub Pages is enabled for the repository from the `main` branch root.*

The current dataset contains **511 organizations**, including **465 publishable organizations across 16 categories** and **46 deliberately retained out-of-scope records** so renamed, acquired, superseded, or otherwise relevant organizations remain findable. It also includes **60 documented business-to-business relationships**.

Maintained by Travis Vought.

## What this is

A flat, categorized market map, not a CRM. One row represents one organization. Each entry records what the organization does, how to reach it, where the information came from, and a capabilities field for problem-oriented searching.

If you need mold remediation, cash logistics, packaging, MRB banking, staffing, compliance support, or another specific service, search the capability rather than guessing the category.

## Repository contents

| File | Contents |
| --- | --- |
| `index.html` | Main searchable directory. Self-contained and usable offline. |
| `intake.html` | Field intake page for capturing and exporting candidate organizations. |
| `ohio-cannabis-directory.csv` | All 511 directory rows with contact, provenance, notes, verification, and capability fields. |
| `b2b-relationships.csv` | 60 documented organization-to-organization relationships with supporting evidence. |
| `build_directory.py` | Regenerates the searchable directory HTML from the master workbook. |
| `build_intake.py` | Regenerates the intake page from the master workbook. |
| `Changelog.md` | Release and version history. |
| `.zenodo.json` | Metadata for future Zenodo archiving and DOI publication. |

The public HTML pages contain the directory data they need, so the searchable site does not depend on a live database or external API at runtime.

## How entries are verified

The directory was seeded from the Ohio Cannabis Expo CRM, then expanded category by category through structured research passes and deduplicated against organization name and website domain.

Contact information is separated into Email, Phone, and Website fields. Verification evidence is stored separately in `Source(s)`, and each entry retains a Seed Source showing how it first entered the dataset.

`Verification Tier` distinguishes source-verified rows from records carrying a specific open issue. When something is unresolved, the `Needs Research` field identifies the unresolved fact rather than expressing general uncertainty.

The headline count is a count of publishable rows, not a claim that every retained row is a distinct currently operating company. Aliases, acquired brands, superseded names, and provenance-preserving out-of-scope records may remain searchable by design.

## Corrections and additions

Open a GitHub issue for:

- an organization that belongs in the directory but is missing
- changed contact information
- an organization that has closed, merged, been acquired, or renamed
- a category or capability that appears incorrect
- a source or relationship that should be added or corrected

Include a source whenever possible. Submissions and corrections should be verified against a named source before being incorporated into the directory.

## Rebuilding

The build scripts currently expect the local master workbook used to generate this release. If you are rebuilding from another copy, update the source and output paths near the top of each script before running it.

```bash
pip install pandas openpyxl
python build_directory.py
python build_intake.py
```

## Licensing

Directory data is released under **CC BY 4.0**. You may copy it, build on it, redistribute it, or use it commercially with attribution.

The site code and build scripts are released under the **MIT License**.

**Attribution:** Ohio Cannabis Ecosystem Directory, compiled by Travis Vought.
