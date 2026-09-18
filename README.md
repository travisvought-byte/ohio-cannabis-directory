# Ohio Cannabis Ecosystem Directory

A source-verified map of who serves what in Ohio cannabis: operators, service
providers and nonprofits, each traced to a named source.

**Searchable version:** https://REPLACE-WITH-YOUR-URL

465 publishable organizations across 16 categories, plus 46 out-of-scope records
kept deliberately so that renamed, acquired and superseded organizations stay
findable. 60 documented business-to-business relationships.

Maintained by Travis Vought.

## What this is

A flat, categorized market map, not a CRM. One row per organization. Each entry
records what the organization does, how to reach it, where that came from, and a
capabilities field for problem-oriented searching. If you need mold remediation,
cash logistics, packaging, MRB banking or staffing, search the capability rather
than guessing the category.

## What's here

| Path | Contents |
| --- | --- |
| `index.html` | The searchable directory. Self-contained, no network calls, works offline. |
| `data/ohio-cannabis-directory.csv` | All 511 rows with full contact, provenance and notes fields. |
| `data/b2b-relationships.csv` | 60 documented organization-to-organization relationships with evidence. |
| `build/build_directory.py` | Regenerates `index.html` from the master workbook. |
| `CHANGELOG.md` | What changed in each version and why. |

## How entries are verified

Seeded from the Ohio Cannabis Expo CRM, then expanded category by category
through structured research passes and deduplicated against organization name
and website domain. Contact detail is split into Email, Phone and Website;
verification evidence lives separately in `Source(s)`. Every entry carries a
Seed Source recording how it first entered the dataset.

`Verification Tier` separates source-verified rows from rows carrying a named
open issue. Where something is unresolved, the `Needs Research` field names the
specific unresolved fact rather than expressing general doubt.

The headline count is publishable rows, not a claim that every row is a distinct
currently operating company. Aliases, acquired brands and provenance-preserving
out-of-scope records remain searchable by design.

## Corrections and additions

Open an issue. Useful ones include:

- an organization that belongs here and isn't
- contact detail that has changed
- an organization that has closed, been acquired or renamed
- a category or capability that's wrong

Include a source where you can. Everything gets verified against a named source
before it goes in, including corrections from the organization itself. That is
the whole point of the dataset, and it does not get relaxed for convenience.

## Rebuilding

```bash
pip install pandas openpyxl
python build/build_directory.py
```

Edit the paths at the top of the script to point at your copy of the master
workbook.

## Licensing

Directory data in `data/` is released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Copy it, build on it,
sell services around it, keep the attribution.

Site code in `index.html` and `build/` is released under the MIT license.

Attribution: Ohio Cannabis Ecosystem Directory, compiled by Travis Vought.
