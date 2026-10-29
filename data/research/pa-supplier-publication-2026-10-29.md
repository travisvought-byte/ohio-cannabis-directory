# Pennsylvania supplier update, October 29, 2026

Prepared for issue #72 at the owner's request to update GitHub after Drive staging.

## Proposed directory additions

Sixteen PA company profiles and business routes, backed by 96 new claim-level evidence records. Fifteen organization identities are new; Epstein reuses `org-f73d6f8cdebe` and retains its existing Ohio profile, contacts and service records. This brings the proposed PA company view from 78 to 94 identities, the business pathway from 79 to 95 routes, and all PA resource routes from 132 to 148. The existing 200 dispensary roster locations are unchanged.

The additions are JR Peters, Boyle Construction, Titanium Security & Surveillance, Automated Security Corporation, MJ Freeway / MJ Platform, McKim & Creed, Epstein, Wooster & Associates, Palmer Construction, Panacea Payroll, LabRepCo, Buglady Consulting, Corcoran Printing, JPAK International, Paragon Engineering Services and Kinsley Energy Systems.

The source manifest records each offering, category, role, Pennsylvania connection, inquiry URL, source review date and limitation. Sources were opened on October 29. Historical completed project experience is described as such; Wooster's project remains proposed. None of these profiles establishes current client intake, a current customer contract, statewide service availability or regulatory approval. Buglady's Pennsylvania location is attributed to the ANBP member directory, a secondary source, while the cannabis offering and inquiry page are first party. MJ Platform's published Leaf PA support route does not prove the current state contract.

Run `python import_pa_suppliers.py`, `python export_directory.py`, `python build_review_queue.py`, `python build_pa_companies.py` and `python build_state.py` to reproduce the update. The importer preserves existing organizations and is idempotent. No shared schema or release metadata changes.

## Publication boundary

Only the sixteen public-source provider profiles and their citations are included in this update. The private Drive backlog, owner decisions and raw evidence export are excluded. The manifest records this PR's sixteen proposed additions; it does not rewrite private staging decisions or mark an unmerged PR as imported.

Historical application references and unresolved provider leads are excluded. A 2017/2018 application establishes what an applicant described or planned; it does not establish an order, installed equipment, an approved product, an operating permit, or a current PA customer.

Three attempted candidates were deferred: Rycon's project page and Verder's cannabis application page returned inconsistent results, including a 404 on repeat retrieval; Pocono Hydroponic timed out. Successful PA office retrieval for Verder alone did not refresh its cannabis-offering review. The manifest records these attempts separately and assigns them no new reviewed date.

## Coverage limits

The seven pathways retain their existing coverage labels. The added companies deepen the business pathway; they do not establish statewide ecosystem completeness. No defensible denominator exists for all ancillary suppliers, so this addition should not be presented as a statewide completion percentage. Waste services, staffing and sanitation/PPE still need stronger PA cannabis-specific evidence. Rules, patient resources, legal help, community and seed-related routes retain their existing evidence and limitations.
