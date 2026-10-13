# v4.35 - October 13, 2026

- Corrected three Ohio street-address geography labels without claiming verified service coverage or a new review.
- Standardized banking capability labels across 32 records; existing category filters remain unchanged.
- Replaced internal workbook/row-number notes in 13 records with reader-facing descriptions; preserved originals in the editorial audit.
- Clarified current versus historical counts and repository-only rebuild instructions. No inclusion or endorsement changes.

# v4.34 - October 13, 2026

- Removed the Libertarian Party of Ohio listing’s special sorting priority. It now appears alphabetically with other organizations, including filtered results and the full text index; the endorsement text, label and stable organization ID are preserved.

# v4.33 - October 13, 2026

- Added eight business-help shortcuts and moved the full category shortcut list into an expandable section; shareable category filters and directory-first entry remain intact.
- Completed 42 scoped first-party contact/service reviews, including 40 previously undated providers. Four public listings still lack a date; blocked sources remain documented without new dates. Reviewed cards now show audiences, inquiry routes and coverage limits.
- Added 15 operator-published store menu routes, distinguishing medical and adult-use menus where the operator supplies both. Imported menus carry evidence and review dates; stock, prices and live license status remain unverified.
- Added event submission email and issue-form routes, organizer-published registration links, dated reviews and a maintenance process; Women’s Expo remains featured first beneath search.
- Added three dated seed-supplier shipping/return summaries and public support routes, plus stock/delivery inquiry templates and a pre-order checklist. No Ohio delivery or stock guarantee implied.
- Withdrew PreventionFIRST! from public listings, state cards, intake and CSV exports at its request and the directory owner’s confirmation. All 564 original identities remain in canonical history: 515 public, 48 retained, one withdrawn.
- Updated validation for provider/menu evidence and listing withdrawal. Browser checks wait for assessment file-import completion before reading its status, preventing the earlier intermittent CI failure.

# v4.32 - October 13, 2026

- Restored a prominent upcoming-events section directly below the main directory search, with readable dates, venues and organizer detail links.
- Featured the Women’s Cannabis & Wellness Expo first, followed by other upcoming events; retained the next-three-month window and automatic expired-event removal.
- Rechecked MedicateOH’s November 7 expo and October 27 industry-night pages and linked directly to each organizer page.

# v4.31 - October 13, 2026

- Fixed missing-website review prioritization: a dated listing without a website now enters P1 independently of its other review flags.
- Restored website/contact routes for Pisgah Peaks Ventures, Subsidio, U.S. Hemp Roundtable and Curaleaf Ohio. Corrected the Hemp Roundtable inbox spelling; added Subsidio’s published phone and Pisgah’s founder/services. Undated public records fell from 46 to 44; missing websites fell from eight to four. Blocked or unresolved website research remains documented.
- Corrected four geographic filter labels from their existing evidence text without changing editorial inclusion or historical review dates.
- Exposed 228 government-map phone numbers with snapshot labels. Added 20 first-party-reviewed store phone/site routes and public-brand directory links while keeping original legal entities and map evidence intact. Contacts have scoped dates and supporting evidence; replacement-map changes require review before reuse.
- Corrected Terrasana Garfield Heights to the operator-published 9601 Vista Way and excluded its old coordinates from distance sorting. No live license-status or inventory claim added.
- Added Strains to shared primary navigation, footer and root fallback. Fixed the release helper to accept a real publication date and rebuild advocacy, lawmakers and the review queue.
- Added regression checks for dated missing websites, conservative geography, reviewed versus snapshot contacts, changed store identities and mobile store-to-directory navigation.

# v4.30 - October 12, 2026

- Prioritized evidence reviews over expansion; added a reproducible P1/P2 backlog and field-scoped audit records.
- Reviewed 10 previously undated providers against first-party pages; public undated records fell from 56 to 46. Added Indoor Gardens website, public store phones and sales email; updated Brent Evans’ role and Our Community Harvest’s public contact.
- Logged Ohio Clean Leaf roster retrieval and Ohio Women’s Cannabis Chamber domain blockers without claiming new verification. Retained historical contacts, licenses and editorial inclusion with explicit review limits.
- Reconciled release metadata to October 12 and retained the published advocacy/lawmaker additions below.

# Advocacy addition - October 12, 2026

- Added a searchable full Ohio legislative roster: 132 districts, 130 current lawmakers, two vacancies and 129 officially published office phones; source-linked contacts, leadership, selected committee roles and SB 56 sponsorship.
- Added all nine verified SB 56 roll calls, with final conference votes separated from earlier floor and committee actions and former-member identities preserved.
- Connected lawmaker cards to named letters, changed the builder to one initial issue and a resident/confirmed-constituent choice, and added call scripts, follow-up messages, suggested follow-up dates and private notes download.
- Added a manual official-source refresh script, data validation, complete non-JavaScript names/contact fallback and browser coverage for roster filters, member links and follow-up behavior.

- Added an Ohio advocacy page with the official lawmaker lookup, source-linked decision-maker guide and reform requests for consumption lounges, out-of-state product restrictions, ordinary accessories and clearer SB 56 rules.
- Added a private editable constituent-letter builder with copy fallback, text download and letter-only printing, plus instructions for commenting on proposed rules.
- Linked Advocacy in shared navigation and consumer resources. Added mobile, export, editing, clipboard fallback and privacy checks.

# v4.29 - October 11, 2026

- Supply calculator now accepts the amount bought in ounces, grams, items or mL and personal daily use; results show days and weeks.
- Replaced the gummy example with an ounce of flower at one gram per day, without setting any default daily amount.
- Added an optional method and per-use × uses-per-day helper. Methods carry through to the shopping plan and PDF without automatic dose or consumption conversions.
- Added tests for ounce conversion, daily-total calculation, unit changes and method-independent arithmetic.

# v4.28 - October 11, 2026

- Rebuilt the buyer guide around a first-time visitor’s shopping plan, simple questions to ask and large readable controls.
- Personalized PDF download and printing now include the visitor’s goal, experience, product interest, budget, question and optional supply estimate. Everything stays on the device.
- Replaced label arithmetic and weekly-use planning with one optional calculator: packages × items per package ÷ items used per day. Removed possession alerts from this tool.
- Mobile Lighthouse remains 100 performance / 100 accessibility for the homepage, buyer guide and assessment.
- PDF dependencies and font load only when downloading. Kept the longer education guide as an optional reference; corrected analytics action names.

# v4.27 - October 11, 2026

- Removed plant-material possession-limit copy and calculator alerts at Travis’s request, including the harvest-limit discussion in the unpublished home-growing draft.
- Supply-duration and shopping calculations remain available.

# v4.26 - October 11, 2026

- Load directory, locations, strain and state data after first paint; keep crawlable directory fallback and initial HTML below 200 KB on every page.
- Add shared page descriptions and Open Graph metadata using the existing VHG logo.
- Improve mobile tap targets and reading width; remove repeated calculator caveats.
- Document four analytics questions, privacy exclusions and Travis’s separate dashboard check.
- Mobile Lighthouse: 100 performance and 100 accessibility on homepage, buyer guide and assessment (local production HTML).
- Keep fixture rendering read-only so migration tests cannot overwrite public state data.
- Update browser tests for fetched data and add the historical review migration check to CI.

# v4.25 - October 11, 2026

- Restored 485 missing historical review dates; listed 61 records without dated evidence in data/review-migration-report.json. Preserved original service-area wording and added controlled labels plus a filter.
- Strain coverage and menu snapshot labels added. Leafly terms checked: 97 reference profiles retain links without republishing attributes or reader counts. Independently sourced ancestry and producer profiles remain.
- Added unpaid-listing disclosure policy; Travis reports no relationships needing disclosure.
- Displayed DCC October 5 state counts alongside the 230-record map snapshot; one-record gap is explicitly unreconciled.

# v4.24 - October 11, 2026

- New task-focused homepage with cross-catalog search, four task cards and two upcoming events. Full directory moved to directory.html; old index query/hash links redirect intact.
- Shared primary navigation and footer, including the Veteran Resident Guide in the primary navigation per Travis. Consistent Ohio Cannabis Directory name.
- Buyer guide uses three steps; self-check uses eight sections and a results screen. Weights and rating thresholds unchanged.
- Ohio basics use verified statutory wording; home-grow explanation held for review.

# v4.23 - October 11, 2026

- Corrected public assessment intro, ownership approval wording and medical/adult-use tax question, with per-question verification dates.
- Added gram-based cumulative possession alerts for plant material and extract, with boundary tests.
- Verified cited rules and tax changes against Ohio Laws, DOJ, Treasury and DEA; no rescheduling outcome predicted.

## October 11, 2026 - Practical tool improvements

- Assessment: critical-gap rating override, domain scores, evidence action plan, local draft save and JSON import.
- Buyer guide: THC/CBD label calculations and a two-page visit handoff and experience journal.
- Analytics: one counter loader, sanitized referrers and debounced searches without query text.

# October 11 consumer tools completion

- Added THC/CBD label-content arithmetic for pieces, mL, whole-package fractions and weight percentages, with unit-specific validation.
- Published the existing two-page visit companion: one-page shopping handoff plus personal experience journal.
- Linked the companion from the shopping guide; calculator inputs remain private and are not saved or sent to analytics.

# October 11, 2026 follow-up

- Critical zero-score gaps now force a RED assessment rating, even when the weighted percentage is high.
- Added private, opt-in device save/resume, clear controls, section percentages and a prioritized action plan.
- Deferred GoatCounter initialization until the page is parsed to avoid duplicate trackers; seed search now recognizes hidden empty results.
- Verified private saved answers stay out of analytics.

# October 11, 2026 additions

- Added public business assessment adapted from the August 27 v2 workbook.
- Added printable dispensary shopping plan and private browser supply calculator.
- Added aggregate GoatCounter action events without collecting worksheet answers or search text.

# v4.22 — October 10, 2026

Corrected VHG counties and current program description, MIF online-resource scope and Detroit equipment tags. Excluded two duplicate cross-references from distinct public organization counts while preserving their IDs and evidence. Clarified documented Ohio expo contacts and CannAscend’s dated parent-company route. Existing curator choices and inclusion decisions preserved. 564 retained rows: 516 public organizations and 48 reference records.

# CHANGELOG

## v4.21 — 2026-10-09

- Added Veteran Home Guardians branding to the directory, relationships and intake pages. Public update requests now open a prefilled email to VeteranHomeGuardians@gmail.com; GitHub issue forms remain available in the repository.

- Fixed multi-number and vanity-number dialing links without changing published contact evidence.
- Added shareable search/filter URLs and permanent organization links.
- Published a searchable, cross-linked view of all 60 documented B2B relationships, preserving their evidence, geography and recorded status.
- Rebuilt offline intake from the current 564-record CSV and aligned candidate exports with its columns. Existing device captures are retained.
- Added permanent record IDs and an explicit Last Reviewed field; October 6 dates are populated for the eight additions documented by that audit. Other dates are left blank until established.
- Synchronized release metadata and added build/data, DOM and browser checks. Organization counts and verification tiers are unchanged.

## v4.20 — 2026-10-06

- Reconciled all 72 recorded OCHBS contact records across 63 organizations against the current dataset.
- Added eight omitted organizations: SCM Promotions, Tom & Berry Premium Reserve, GLEAF / Gleaf Group, Mood Leaf, SIPE Promotional Products, Precise TB Solutions, Courier Pro Logistics, and Ohio Women’s Cannabis Chamber of Commerce.
- Verified SCM against its official business site and OCHBS exhibitor profile, Tom & Berry against its official brand site and exhibitor profile, and Gleaf Group against its official exhibitor profile. Five other additions retain explicit Open issue notes and firsthand event provenance.
- Kept unverified individual card emails and phones in the private tracker. Public SCM and Tom & Berry contact routes are independently published by those businesses.
- Preserved every existing dataset row and the GoatCounter tracker; added GoatCounter to the build template so future rebuilds preserve it.
- Prepared dataset: 564 total records, 518 publishable, 46 retained out-of-scope records, 16 categories. These records are published in the live directory.

## v4.5 — 2026-09-29

- Rebuilt from the corrected category data: Hefestus USA Inc. remains under Packaging & Labeling, and Expo records remain under Events & Expos; neither Automation Technology nor Events & Conferences is a standalone directory category.
- Made the Women’s Cannabis & Wellness Expo appear as a visible, pre-rendered home-screen event item, while keeping the three-month date filter current when the page opens.
- Updated the Expo’s directory link to MedicateOH’s current event page.
- Retained the Ohio State scarlet-and-gray palette and Midwest CannaWomen home-screen link.
- Dataset remains 556 total records: 510 publishable organizations across 16 categories and 46 retained out-of-scope records.

## v4.4 — 2026-09-29

- Added a home-screen panel for confirmed events taking place within the next three months; dated events age out automatically.
- Featured Midwest CannaWomen as the women’s cannabis group, linking to its official resource hub.
- Added the source-confirmed Women’s Cannabis & Wellness Expo on November 7, 2026, with its organizer’s current event-details page.
- Recolored the directory in Ohio State scarlet and gray with light gray surfaces and dark, readable text; no university logo or mark was added.
- Kept the directory dataset unchanged at 556 total records: 510 publishable organizations across 16 categories and 46 retained out-of-scope records.
- Updated the site builder, README, citation, and archive metadata for v4.4.

## v4.3 — 2026-09-29

- Consolidated the Ohio Cannabis Expo entry into the existing Events & Expos category.
- Classified Hefestus USA Inc. under Packaging & Labeling, retaining pre-roll equipment and packaging automation as searchable capabilities.
- Moved Quality Extractions Group from Technology to Hemp / CBD Products & Ancillary; extraction solvents and processing supplies remain searchable capabilities.
- Restored the source-verified Ohio Cannabis Expo and Ohio Cannabis Live listings in the transfer bundle; the Expo addition no longer creates a one-off Events & Conferences category.
- Kept extraction discoverable through capability keywords rather than adding a one-record top-level category.
- Updated the dataset to 556 total records: 510 publishable organizations across 16 categories and 46 retained out-of-scope records.
- Updated the searchable page, repository summary, citation, and Zenodo metadata for v4.3.

## v4.2 — 2026-09-28

- Reconciled listing details against direct email replies received after OCHBS.
- Corrected Hefestus USA Inc. name, Automation Technology category, product description, and contact details.
- Corrected Package My Bud to Packaging & Labeling, added its confirmed contact and primary site, and added PMB PROMOS as the separate promotional-goods listing.
- Added Atomic Credit Union’s confirmed business-development contact and direct line.
- Added RobMejia.com to the Our Community Harvest record and clarified the two sites’ distinct roles.
- Added a source-verified Libertarian Party of Ohio listing as the directory maintainer’s clearly labeled personal, unpaid endorsement of Don Kissick for Governor; it sorts first by default.
- Updated the dataset to 554 total records: 508 publishable organizations across 17 categories and 46 retained out-of-scope records.
- Updated the searchable page, repository summary, citation, and Zenodo metadata for v4.2.

Older entries below record historical dataset counts and the workbook-based workflow at that time. Current builds use `data/directory.json`; see the README for current counts and rebuild instructions.

## v4.1 — 2026-09-26

- Reconciled OCHBS 2026 direct-contact and exhibitor evidence against the public directory.
- Added 41 approved organizations, increasing the dataset to 552 total records: 506 publishable organizations across 16 categories and 46 retained out-of-scope records.
- Updated 20 existing organization records with event provenance, current operating status or verified organizational contact information.
- Corrected the ACT LAB point of contact, recorded the Klutch Grandview opening, the Herbal Wellness Center Jackson reopening, and the Thrive Columbus/Reynoldsburg opening.
- Kept nine unresolved additions out of publication pending research or scope decisions.
- Preserved private CRM-only contact information outside the public dataset.
- Updated `build_directory.py` to rebuild the site directly from the repository CSV.

## v4.0 — 2026-09-18

- Prepared the first GitHub Pages release of the searchable directory\.
- Dataset at v4.0: 511 total records, 465 publishable organizations across 16 categories, and 46 deliberately retained out-of-scope records.
- Includes 60 documented business\-to\-business relationships\.
- Added `LICENSE` with CC BY 4\.0 terms for directory data and MIT terms for code\.
- Added `CITATION.cff` and Zenodo release metadata\.
- Added structured GitHub issue forms for additions, corrections, status changes, and B2B relationship submissions\.
- Kept public submissions separate from publication: proposed changes remain research leads until independently verified\.

## v3\.0

- Public release\. Distributed via LinkedIn and Ohio cannabis groups\.

## v2\.2

- 469 organizations\. Contributor submissions accepted and verified\.

## v2\.1

- Corrected version label\. Removed an internal out\-of\-scope tab that had remained publicly visible\.

## v1\.0

- First public release, 422 organizations, CC BY 4\.0\.

## Consumer resource update — 2026-10-09

- Added six homepage routes and a source-reviewed consumer resource page.
- Added Ohio and national seed catalogs with availability/delivery qualifications.
- Added statewide record-sealing guidance, Franklin County-only Opportunity Port, and the current marijuana-specific expungement statute.
- Added medical registration steps, current home-grow summary and official law links.
- Retained organization counts; no historical dispensary feed imported as a current complete list.

## Seed supplier expansion — 2026-10-09

Expanded from two seed catalogs to ten seed providers plus one Ohio grow-supply / retailer lead. Added dedicated search, location/type filters, shareable searches, downloadable source data and provider-specific shipping/pickup evidence. Ohio walk-in seed stock remains unconfirmed.

## Multi-state foundation — 2026-10-09

Defined the shared data contract and seven visitor pathways; added a JSON schema, cross-record validator, negative regression tests, state research template and conservative seed/supply pilot. CI validates the foundation alongside the current public builders. Full dataset migration and shared state renderers remain stage two.

## Canonical migration and shared state pages — 2026-10-09

- Migrated the full 564-record Ohio dataset and 60 relationships into canonical structured data, preserving original IDs, fields and exports.
- Unified seed and referral identities, preserving an alias for Indoor Gardens and separating reference-only counterparties.
- Added reusable state/need presentation, seven pathways, public-state gates, permanent service links and independent seed sex/flowering filters.
- Added claim-specific shipping/storefront evidence, historical-source labels, active filters and expired-event handling.
- Added compatibility export generation, migration checks and shared-state browser/mobile regressions. No complete physical location import or additional state launch is claimed.

## Location search — 2026-10-10

- Added 230 source-listed Ohio dispensary locations, reusable state-aware city/county search, directions and optional approximate distance sorting.
- Preserved government source snapshot, unknown freshness and unknown current license status; rejected three invalid coordinate pairs.
- Added idempotent importer and snapshot, UI and mobile-browser checks. Original 564 organization records and 60 relationships remain preserved.

## Location field cleanup — 2026-10-10

- Corrected four source records: city/county swaps for Painesville Township and Lewis Center, Nectar name/city swap and operator-confirmed ZIP, and Middletown spelling. Original government snapshot remains unchanged; license-keyed corrections record original values and supporting sources.
- Normalized all three source dual-use labels; corrected 17 locations previously displayed as other.
- Added canonical/import checks for Ohio counties, missing fields, malformed ZIPs and business names in city fields; changed source values require correction re-review. All 230 license identities remain preserved.

## Upcoming event line — 2026-10-10

- Replaced the compact event card with a full-width horizontal chronological event line, swipeable on small screens. Dates and links remain readable without moving text.
- The rolling three-month window now refreshes every minute and when the tab becomes visible, automatically removing past events while the page stays open. Event additions remain source-reviewed publication updates.

## Event research — 2026-10-10

- Added organizer-listed Buds & Balance (Columbus, October 18) and Gardening Industry Night (Cincinnati, October 27); rechecked MedicateOH’s November 7 expo date. The homepage line and shared community view use the same reviewed event records.
- Excluded past events and Dayton 2027 from the rolling window; organizer pages conflict on the Dayton date.

## 2026-10-10 event review

- Removed Buds & Balance from upcoming listings because its ticket link could not be reliably verified; cancellation is not confirmed.
- Removed the standalone Midwest CannaWomen homepage promotion; its directory record remains available.

## 2026-10-10 strain guide

- Expanded the ancestry pilot to 100 unranked popular strain profiles with original genetics/history summaries, reader-reported sensory/effect tags, individual sources and review dates.
- Added type, effect, flavor and ancestry-review filters, review-count sorting, pagination and exact profile links.
- Kept breeder versions and unresolved ancestry references separate from the 100 market-name profiles; retained conflicting and superseded parentage claims.
- Added a 100-row Excel-compatible profile export and deterministic build, UI and mobile-browser checks.

## October 10, 2026 — Cannabis knowledge

- Added a source-linked knowledge hub with 30 searchable topics and a practical label-reading checklist.
- Linked learning resources throughout the directory and strain guide.
- Published the curated 100-strain guide with attributed ancestry and downloadable data.

## October 10, 2026 — Growing Ohio-relevant strain library

- Removed the fixed 100-profile limit; expanded to 336 profiles and 318 distinct names.
- Added sourced producer catalogs, 27 dated Ohio flower observations, producer/menu filters and a separate observation CSV.
- Preserved producer identities, unknown fields and conflicting lineage notes; no popularity ranking or live inventory inferred.
