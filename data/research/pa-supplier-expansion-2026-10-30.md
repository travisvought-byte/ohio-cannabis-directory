# Pennsylvania supplier expansion, October 30, 2026

Issue #74. Six additional company profiles and business routes bring the proposed company view to 100 identities and Pennsylvania resource routes to 154 (101 business routes). Four organization identities are new. ARCO and Talaria reuse their permanent national identities without changing their Ohio legacy records, contacts or service coverage. The 200-location Pennsylvania dispensary roster is unchanged.

## Public-source review

Public provider pages were retrieved and read directly on October 30; the web-search service returned errors, so it supplied no evidence. The manifest `data/sources/pa-suppliers-2026-10-30.json` lists each reviewed URL, claim, limitation and inquiry route. No private Drive rows, owner decisions or raw backlog exports are included.

| Provider | Supported addition | Important limitation |
| --- | --- | --- |
| ARCO National Construction | Provider-reported completed cultivation facility in McKeesport; current inquiry page and Pittsburgh office | Confidential customer remains unnamed; image is illustrative; no current contract or performance claim |
| Graves Design Group | Architecture/engineering for PurePenn's McKeesport cultivation buildings; business inquiry form | Historical portfolio experience, not a current engagement or credential check; recruiting email is not used as a general sales contact |
| HiTechTrader | Extraction/laboratory equipment; provider-stated inventory in Pennsylvania; sales phone and email | No inventory guarantee, ROI/savings claim or approved-laboratory status |
| Dellinger Horticulture | Greenhouse construction for cannabis/horticulture; completed Pennsylvania greenhouse projects | Cannabis offering and general PA project experience are separate facts; no PA cannabis customer is named |
| Talaria | Explicit Pennsylvania cannabis distribution footprint and general inquiry/demo route | Distribution and cash-service geography remain distinct; no interstate transport permission, current contract or banking charter is inferred |
| Innovative Industrial Properties | Regulated-cannabis real estate and property transactions; provider-listed Chambersburg property; acquisitions inquiry email | No tenant/lease/title verification, financing offer or investment recommendation; placeholder text and broken portfolio counters excluded |

Other pages inspected were InSpire's about/consultation pages and Plant Productions' home page. InSpire's PA service marketing is explicit, but its existing organization is retained outside Ohio referral scope; publishing it needs a state-specific scope resolution rather than silently changing its global record. Plant Productions establishes general hydroponic supplies, but this batch did not confirm a cannabis-specific offering. Neither is added here. Verder's former cannabis URL returned 404 and receives no fresh reviewed date.

## Reproduction and checks

Run `python import_pa_suppliers_oct30.py`, `python export_directory.py`, `python build_review_queue.py`, `python build_pa_companies.py`, and `python build_state.py`. The generic supplier importer now preserves existing record order across separate batches and accepts optional cited business facts. Tests require both the October 29 and October 30 imports to be unchanged on repeat and to preserve each other's records and shared Ohio profiles.

This expansion is based on PR #70's identity/importer/link corrections. Its old Insureon URL regression remains covered. No canonical schema or release-metadata changes. New evidence uses October 30 source-review dates; earlier records retain their dates. Overall snapshot and PA state-pack review dates advance to accommodate the new claims; this is not a fresh review of existing laws or every directory record.
