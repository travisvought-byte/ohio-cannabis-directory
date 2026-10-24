# Pennsylvania structured starter pack

Issue #45; parent #42; research predecessor PR #44. Reviewed October 24, 2026.

## Implemented

The existing schema now contains a research-only PA state pack, three reference-only organizations, five consumer service routes, one legal-aid office and 17 claim-level evidence records. No schema, release or public route changes. Source rechecks are scheduled for November 23, 2026; that date is a review trigger, not a validity guarantee.

| Organization | Permanent ID | Service routes |
|---|---|---|
| Pennsylvania Department of Health | `org-pa-department-health` | Patient/caregiver registration; MMAP assistance information; official dispensary list |
| North Penn Legal Services | `org-north-penn-legal-services` | Monroe/Pike legal-help intake for record-related employment barriers |
| Pennsylvania State Police | `org-pennsylvania-state-police` | Individual record access and court referral |

All three names and identities were checked against existing canonical organizations before insertion; none existed. DOH and PSP correspond to the first-batch `pa-doh` and `pa-psp` source subjects. North Penn is a new local addition. Do not create new identities for these agencies when importing other candidates. No operator brands or subsidiaries have been merged.

## Evidence and task checks

Primary pages were opened and read. Canonical evidence records carry source URLs, reviewed/recorded dates, supported claims and limitations.

- **Patient registration:** the DOH registration guide links to the state registry. Following that link reached the login/registration choices, including adult patient and caregiver routes. No account created, form submitted, practitioner certification or successful enrollment tested. Contact: the guide's program help line.
- **Assistance:** the MMAP agency page distinguishes fee relief from purchase assistance; the latter is restricted to eligible PACE/PACENET patients. The service points to criteria rather than promising benefits or encoding a dollar amount.
- **Find a dispensary:** the official roster PDF opened successfully and is dated September 16, 2026. The next step links directly to this PDF. No current inventory, completeness, legal parent, or October operating status is inferred.
- **Local record help:** North Penn's Stroudsburg office page confirms Monroe and Pike civil legal intake and 877-953-4250. Its employment-barriers page states that NPLS helps with eligible sealing and expungement, but services vary by county and cases require acceptance. This is a local screening route, not a promise that every record case qualifies. Its older FAQ legal summaries and expedited-pardon references were not adopted as current law.
- **Individual record access:** the PSP guide and linked SP 4-170 form both opened. The form is for the record subject/legal representative. Record access and a court petition are separate steps; the service does not claim that requesting the record expunges it. No application submitted.

### Retrieval limitation

The North Penn online application link failed with an internal retrieval error on October 24, 2026. It has no assigned review date or verified-functionality claim. The independently reviewed office page and published phone intake are the next step. No calls were made. The registry login page displayed a JavaScript capability notice alongside readable registration links; end-to-end registration was not tested.

## Publication boundary

`PA.publication_status` remains `research-only`, with no `public_url` on any pathway. The three organizations use `reference-only` scope and have no Ohio legacy rows. Existing renderer behavior excludes their cards. The location renderer excludes PA because it is not public. Canonical JSON remains a repository-accessible research dataset; research-only is a visitor-routing gate, not confidentiality.

Ohio CSVs, public organization counts, state cards, location finder, home search and release metadata must remain unchanged after regeneration. The migration regression now uses Washington as the synthetic new-state fixture and checks the actual PA pack's absence from public data. This avoids inserting a duplicate PA state in the existing test. Ohio snapshot assertions now explicitly select Ohio locations, so a PA legal-aid office is not counted as an Ohio dispensary; the repeated-import preservation assertion still checks the entire canonical tree.

## Coverage and remaining work

- Starter: dispensary referral, patient access, record-help referral.
- Not reviewed in this canonical pack: seeds, legal rule summaries, business services, community/events. The separate PR #44 candidates remain research; candidate discovery does not count as imported service coverage.
- Full legal review must reconcile enacted statutes, agency rules and relevant court orders before adding rule summaries.
- The designated reconciliation reviewer should resolve brand/license identities before operator imports. This batch makes no permit or ownership determination.
- Next page implementation should use shared state rendering and visibly label PA as a pilot only after source and destination review. Explicitly assess publication of these reference-only service organizations; changing only the state status will not expose their cards.
- Continue with verified Pocono-area dispensaries, broader legal-aid coverage and independently supported business-service routes. No paid placement, ranking, outreach or event announcement is introduced.

## Validation

Run the repository checks listed in AGENTS.md and the ancestry checks used in CI. Verify generated files are unchanged and review the source limits above before owner merge. PR records final test results.
