# New York state pack

Updated November 1, 2026. New York is a labeled **pilot** with all seven pathways reporting reviewed starting routes. Every published claim cites a page read on November 1, 2026. Earlier scoping notes and leads are in `data/research/new-york-2026-11-01-sources.json`.

## What is published

| Pathway | Coverage | What a visitor gets | Known gaps |
| --- | --- | --- | --- |
| Dispensaries | broad | 698 OCM-licensed adult-use stores and 24 open medical dispensing facilities in the location finder; OCM's own adult-use and medical lists | No map points, so no distance search; 11 registered-organization adult-use sites with no opening date; 6 medical facilities marked temporarily closed |
| Seeds | starter | Home-grow rule; OCM's statement that licensed retailers, microbusinesses and registered organizations may sell seeds and immature plants; patient home grow | No store-level availability or online supplier reviewed |
| Records | partial | Court routes for automatic marijuana expungement, CPL 440.46-a motions, CPL 160.59 sealing and Clean Slate status; Legal Action Center phone help | No regional legal-aid office confirmed for record cases |
| Rules | starter | Eight dated summaries tied to statute text or official pages | Local rules, hemp, packaging and business rules; S3294A provision dates |
| Medical | partial | Certification, provider finder, caregivers, home grow, dispensing facilities | Provider rows, fees and discounts not reviewed; reciprocity not confirmed in effect |
| Business | starter | OCM licensing hub (renewals, nursery license, showcase permits) | No providers reviewed for New York service; trade associations remain leads |
| Community | starter | Three NORML chapters; OCM clinical symposium, November 19-20, 2026, Tarrytown | Chapter activity unconfirmed; no trade, veteran or industry events reviewed |

## How it is built

- `scripts/snapshot_ny_ocm_licenses.py <export.xlsx|csv> <date>` turns a downloaded Current OCM Licenses export into `data/sources/new-york-ocm-retail-<date>.json`. It keeps retail rows with an opening date (751 of 3,040) and drops the primary-contact name and equity-category columns. The raw export is not committed.
- `data/sources/new-york-medical-dispensing-facilities-2026-11-01.json` holds all 30 rows of OCM's medical dispensing-facility table, read in a browser.
- `import_ny_locations.py` publishes the 698 adult-use stores (Active license and operational status) and the 24 open medical facilities. Licensees are `reference-only` identities, so they stay out of the Ohio directory, exports and intake index. Medical facilities reuse the existing Rise (Green Thumb), Verilife (PharmaCann), The Botanist (Acreage) and Sunnyside (Cresco) identities, matched by the DBA OCM prints. License status shows as not verified.
- `data/sources/new-york-ecosystem-2026-11-01.json` and `import_ny_ecosystem.py` add 6 organizations, 14 services, 8 rules and 1 event, following the Pennsylvania manifest pattern.
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

1. **Map points:** Census geocodes with the Pennsylvania acceptance rule, so distance search works for New York.
2. **Regional record help:** confirm which legal-aid offices take sealing and expungement cases (Legal Aid Society of NYC, LawNY, LASNNY, Legal Services of Central NY, Neighborhood Legal Services).
3. **Seeds:** review which existing seed suppliers state New York shipping; check OCM's nursery license rollout.
4. **Business and community:** confirm trade associations (CANY, ANYCP, ECMA, NYMCIA, CRANY, CAURD Inc., NYCRA, BCIA) on their own pages, veteran groups and organizer-confirmed events.
5. **Comparison and advocacy:** add New York to the state comparison as the adult-use reference for Ohio and Pennsylvania visitors. The advocacy page waits for 2027 session bill filings; 2025–2026 bills expire when the session ends.
6. **Reconcile the count:** OCM's page states 757 adult-use dispensaries; the export yields 698 active, opened stores.
