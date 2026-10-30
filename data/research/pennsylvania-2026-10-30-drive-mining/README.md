# Pennsylvania Drive mining consolidation

Research-only snapshot from the [PA staging master](https://docs.google.com/spreadsheets/d/1yZ-bWfHXEnYZL7UbIIiZl6ai5SnI6z29fHsDTwGqPNY/edit), copied after Travis authorized the consolidated GitHub update on October 30, 2026. Implements #76.

## Contents

| File | Records | Purpose |
| --- | ---: | --- |
| `candidates.json` | 178 | Initial 100 business candidates plus 78 from nine further mining passes |
| `mining-passes.json` | 9 | Sources examined, yields, exclusions and remaining checks |
| `historical-mentions.json` | 39 | Page-linked supplier mentions from 2018 PA applications |
| `biocontrol-leads.json` | 24 | Association-directory discovery leads, with PA service evidence still to establish |
| `document-index.json` | 387 | Public application PDF index; indexing does not mean content review |
| `source-paths.json` | 14 | Tested mining routes and their extraction/review status |
| `manifest.json` | — | Counts, provenance, scope and data-file SHA-256 checksums |

The 178 candidate trading identities include 127 PA distribution-channel leads, 18 PA event connections, 12 official hemp-registry connections, two PA provider claims and three firms with PA offices. Sixteen more have sector relevance but still need PA evidence. These are not 178 verified PA headquarters or distinct ultimate corporate parents. Research work order is not a statewide market ranking.

## Publication and evidence boundaries

No record in this package is approved for automatic public-directory import. Public organization IDs, approval flags, public counts and generated pages are unchanged. The package is not read by public build/export scripts.

- Event listings establish an organizer-listed association, not a current office, license or supply contract. Several vendors' offerings still require identification.
- Supplier catalogs establish a distribution lead. HTG's shipping policy identifies a Pennsylvania warehouse; Griffin lists a Morgantown branch. Neither establishes current stock, manufacturer location, a PA cannabis customer or authorization to use a product on cannabis.
- The PA Agriculture hemp-lab registry is dated **April 2026**. It lists 14 facilities corresponding to 13 research organizations. Coral Reef was already staged; the 12 additions combine SC Labs' California and Colorado entries. Hemp approval is separate from medical-marijuana testing approval.
- The 2018 application evidence includes proposed purchases, quotations, examples, generic checklists and historical applicant claims. It does not establish current contracts or deployed equipment.
- Source-check dates refer to the recorded source context. A failed provider retrieval is not a provider review. `provider_check`, identity notes and next steps preserve that distinction.
- National software, packaging, finance and service leads without demonstrated PA eligibility remain marked **Needs PA evidence**. Generic state-selection forms are not deployment evidence. Provider legal/compliance marketing is not adopted as current law.

Drive candidate IDs and sheet/row provenance are retained. Other snapshots preserve the original column labels and statuses; Sheets serial dates are normalized to ISO dates. No applicant personal contacts, payment details, full source pages or application PDFs are copied.

## Validation

Run `python scripts/validate_pa_drive_mining.py`. It checks file integrity, stable IDs, source links/dates, pass yields, historical application references and research-only publication boundaries. These checks verify the package structure; they do not replace entity reconciliation or current PA service verification.
