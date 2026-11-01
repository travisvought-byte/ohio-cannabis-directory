# New York state pack: scoping and work plan

Prepared November 1, 2026. New York is added to `data/directory.json` as a **research-only** state pack. All seven pathways are `not-reviewed`, no route is public, and the state picker does not show New York. Staged sources are in `data/research/new-york-2026-11-01-sources.json`; nothing there is read by the public build.

The snapshot `as_of` date moves from October 30 to November 1, 2026 so the new state pack's review date validates. This is not a fresh review of existing records; no other record, count, review date or generated page changes.

## How New York differs from Pennsylvania

| Topic | Pennsylvania (pilot) | New York (research-only) |
| --- | --- | --- |
| Market | Medical only (Department of Health) | Adult-use since 2022 plus medical, both under the Office of Cannabis Management (OCM) and Cannabis Control Board |
| Location source | 200-row DOH roster PDF, no permit numbers or counties | OCM open dataset with license numbers, county, operational status, opening date and hours (3,040 rows incl. applicants and non-retail; updated Oct 31, 2026). OCM page states 757 adult-use dispensaries; 30 medical dispensing facilities |
| Home grow | Not allowed | Adults 21+: 3 mature / 3 immature, 6 / 6 per household. Patients 18+ under S3294A (implementation to confirm) |
| Records | Clean Slate sealing, petitions, pardons | MRTA automatic expungement of listed marijuana offenses; Clean Slate sealing in effect since Nov 16, 2024, implementation due by Nov 16, 2027 |
| Advocacy | Live adult-use bills (HB 20, HB 1200, SB 120) | Market-structure issues (inversion, enforcement, microbusiness, medical reciprocity, hemp). 2025–2026 bills expire at session end; the 2027 session opens in January |

The seeds pathway is the biggest change: unlike Pennsylvania, New York has a lawful home-grow audience, so the existing seed-supplier pages become relevant once New York shipping statements are reviewed.

## Established facts (staged, not yet canonical evidence)

- Adults 21+ may possess 3 oz of cannabis and 24 g of concentrate; consumption is allowed in private homes and most places tobacco may be smoked, but not in vehicles. Source: OCM adult-use information page. Statute citations still needed.
- Medical program: 69,031 registered patients and 4,820 certifying practitioners as of October 1, 2026; up to five caregivers per patient. Source: OCM medical page.
- OCM announced enactment of S3294A on November 25, 2025: out-of-state patient purchases, patient home grow at 18+, two-year certifications.
- A10140/S9155 (signed February 2026, per secondary source) codified door-to-door distance measurement for retailers near schools and houses of worship.

## Work order (GitHub issues to open)

Under `AGENTS.md`, Codex implements labeled research/import issues; Claude handles schema, comparison design and PR review; Travis merges. Suggested issues, in order:

1. **NY location import (`codex`).** Write `import_ny_locations.py` reading the Current OCM Licenses CSV. Filter to retail dispensary license types with Operational Status = Active and a date opened to public; record the filter, row counts and retrieval date as the denominator. Reconcile the 30 medical dispensing facilities. Geocode with the Census geocoder as for PA. Do not publish the primary-contact name column. Acceptance: deterministic re-import, a test mirroring the PA roster test, `location_source` with `count_note` comparing the dataset count with OCM's stated 757.
2. **NY rules and medical pack (`codex`).** Six to eight dated rule cards cited to the Cannabis Law and Penal Law Article 222 (possession, consumption, driving, sharing vs. gifting, home cultivation, employment, medical certification, reciprocity). Confirm S3294A's chapter number and which provisions are in effect. Medical routes: certification, practitioner dataset, caregiver registration, dispensing facilities.
3. **NY record clearing (`codex`).** MRTA expungement (offense list from the court's Marijuana and Expungement page and CPL 160.50), Clean Slate status, CPL 160.59 petitions, DCJS record review, and reviewed regional legal-aid routes. State the coverage gaps by region, as PA does.
4. **NY seeds and home grow (`codex`).** Review which existing seed suppliers state New York shipping; review whether OCM publishes which licensed retailers sell seeds or immature plants. Keep fulfillment labels seller-stated.
5. **NY business and community seed set (`codex`).** Reconcile licensed operators from the dataset to persistent identities (reuse national IDs such as Ascend, Curaleaf, Verano). Confirm trade associations (CANY, ANYCP, ECMA, NYMCIA, CRANY, CAURD Inc., NYCRA, BCIA), NORML chapters and veteran groups on their own pages. Events only with organizer-confirmed dates.
6. **NY comparison and advocacy (`claude`).** Add New York to the state comparison as the adult-use reference for Ohio and Pennsylvania visitors (licensing structure, home grow, expungement, social equity). Advocacy page waits for the 2027 session bill filings.

Publication gate: switch `publication_status` to `pilot` only after issue 1 and at least the rules or records pathway have reviewed, usable routes. Keep unfinished pathways visible as gaps.

## Retrieval limitation

The repository workspace used for this scoping could not download from data.ny.gov (egress refused). Dataset rows were not counted or imported; only published metadata was read. A failed retrieval is not a review.
