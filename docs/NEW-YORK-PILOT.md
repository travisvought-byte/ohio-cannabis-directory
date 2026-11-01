# New York state pack

Updated November 1, 2026. New York is a labeled **pilot** with all seven pathways reporting reviewed starting routes. Every published claim cites a page read on November 1, 2026. Earlier scoping notes and leads are in `data/research/new-york-2026-11-01-sources.json`.

## What is published

| Pathway | Coverage | What a visitor gets | Known gaps |
| --- | --- | --- | --- |
| Dispensaries | broad | 698 OCM-licensed adult-use stores and 24 open medical dispensing facilities in the location finder, 644 with Census map points for distance sorting; OCM's own adult-use and medical lists | 78 locations without a map point; 11 registered-organization adult-use sites with no opening date; 6 medical facilities marked temporarily closed |
| Seeds | starter | Home-grow rule; OCM's statement that licensed retailers, microbusinesses and registered organizations may sell seeds and immature plants; patient home grow | No store-level availability or online supplier reviewed |
| Records | partial | Court routes for automatic marijuana expungement, CPL 440.46-a motions, CPL 160.59 sealing and Clean Slate status; Legal Action Center (statewide); Legal Aid Society Case Closed, CSS Next Door Project, Youth Represent, The Bronx Defenders and Brooklyn Defender Services (NYC); Center for Community Alternatives (Syracuse, Rochester) | No listed route for Long Island, Hudson Valley, Capital Region, North Country or Western NY outside Rochester |
| Rules | starter | Eight dated summaries tied to statute text or official pages | Local rules, hemp, packaging and business rules; S3294A provision dates |
| Medical | partial | Certification, provider finder, caregivers, home grow, dispensing facilities | Provider rows, fees and discounts not reviewed; reciprocity not confirmed in effect |
| Business | partial | OCM licensing hub; all 11 OCM-permitted testing labs (with scope); all 13 OCM-approved sampling firms; 20 banks and credit unions from OCM's Cannabis Banking Directory | Insurance, legal, accounting, security, packaging and technology providers not reviewed; trade associations remain leads |
| Community | starter | Three NORML chapters; OCM clinical symposium, November 19-20, 2026, Tarrytown | Chapter activity unconfirmed; no trade, veteran or industry events reviewed |

## How it is built

- `scripts/snapshot_ny_ocm_licenses.py <export.xlsx|csv> <date>` turns a downloaded Current OCM Licenses export into `data/sources/new-york-ocm-retail-<date>.json`. It keeps retail rows with an opening date (751 of 3,040) and drops the primary-contact name and equity-category columns. The raw export is not committed.
- `data/sources/new-york-medical-dispensing-facilities-2026-11-01.json` holds all 30 rows of OCM's medical dispensing-facility table, read in a browser.
- `import_ny_locations.py` publishes the 698 adult-use stores (Active license and operational status) and the 24 open medical facilities. Licensees are `reference-only` identities, so they stay out of the Ohio directory, exports and intake index. Medical facilities reuse the existing Rise (Green Thumb), Verilife (PharmaCann), The Botanist (Acreage) and Sunnyside (Cresco) identities, matched by the DBA OCM prints. License status shows as not verified.
- `data/sources/new-york-suppliers-2026-11-01.json` adds 44 business routes from three OCM lists (labs, sampling firms, banking directory); ACT, Jonestown Bank & Trust and Regent Bank reuse existing identities. `import_ny_ecosystem.py` imports every file in `MANIFESTS`.
- `data/sources/new-york-ecosystem-2026-11-01.json` and `import_ny_ecosystem.py` add 6 organizations, 14 services, 8 rules and 1 event, following the Pennsylvania manifest pattern.
- `data/sources/new-york-location-geocodes-2026-11-01.json` holds one Census Geocoder result per location (street, city, NY, ZIP). `apply_geocodes` accepts a point only for a single candidate with the same house number and street and a Census county that matches the regulator's. New York additions to the Pennsylvania rule: hyphenless Queens house numbers (16203 = 162-03), spelled-out suffixes (Court, Parkway, Turnpike, Expressway, Terrace, Highway), County Road as CO RD, and trailing floor/space/store text. Route types are not equated (Route 9 and US Hwy 9 still differ). 644 accepted; 29 no match, 25 street differs, 9 county differs, 8 multiple candidates, 5 house number differs, 2 direction differs.
- New York county and ZIP checks are in `location_validation.py`. Tests: `tests/locations.py`, `tests/migration.py`, `tests/locations.cjs`, `tests/directory.cjs`.
- The snapshot `as_of` date is November 1, 2026 so New York's review dates validate. No other record or review date changed.

Rebuild after any change:

```bash
python import_ny_locations.py && python import_ny_ecosystem.py
python export_directory.py && python build_review_queue.py
for b in build_*.py; do python "$b"; done
```

To refresh the store list, download the export again, run the snapshot script with the new date, point `SOURCE` in `import_ny_locations.py` at the new file, rerun the import and builds, and update test counts.

## Next work

1. **Remaining map points:** review the 78 unmatched addresses; the 9 county disagreements (for example, 6850 Main St, Williamsville listed as Onondaga) may be OCM data errors worth reporting.
2. **Regional record help outside NYC, Syracuse and Rochester:** LawNY, LASNNY and the Legal Aid Bureau of Buffalo were checked November 1 and their pages do not say they handle sealing; Long Island (Breaking Barriers, Suffolk), Hudson Valley and North Country providers still need review.
3. **Seeds:** review which existing seed suppliers state New York shipping; check OCM's nursery license rollout.
4. **Business and community:** confirm trade associations (CANY, ANYCP, ECMA, NYMCIA, CRANY, CAURD Inc., NYCRA, BCIA) on their own pages, veteran groups and organizer-confirmed events.
5. **Comparison and advocacy:** add New York to the state comparison as the adult-use reference for Ohio and Pennsylvania visitors. The advocacy page waits for 2027 session bill filings; 2025–2026 bills expire when the session ends.
6. **Reconcile the count:** OCM's page states 757 adult-use dispensaries; the export yields 698 active, opened stores.
