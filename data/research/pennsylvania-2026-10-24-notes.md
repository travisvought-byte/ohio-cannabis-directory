# Pennsylvania cannabis directory — first research batch

Research date: October 24, 2026. Parent roadmap: #42. Bounded research issue: #43.

This batch stages 28 source-reviewed candidates, nine proposed existing-identity matches, and eight sample locations for owner review. These are candidate organizations/brands and referral routes, not 28 license holders, sales prospects ranked by value, or a complete market map. Public Pennsylvania pages and canonical data have not changed.

## Files and evidence method

- `pennsylvania-2026-10-24-candidates.json`: batch-local candidate IDs, categories, pathways, next steps, identity matches, supported claims and gaps.
- `pennsylvania-2026-10-24-sources.json`: publishers, URLs, retrieval/review dates, supported claims and limitations; failed and JavaScript-only attempts retain no review date.
- Existing permanent IDs remain unchanged. National brand identities are reused where supported; state-specific subsidiaries require their own legal-entity reconciliation. The ACT group match is provisional and does not merge a Pennsylvania permit into an Ohio entity.
- Primary pages were opened and read; search snippets were discovery leads only. Source review means only the specified claim was supported. It does not certify current availability, fees, ownership or completeness.

## Starting ecosystem

| Candidate | Category | Existing identity |
|---|---|---|
| Pennsylvania Department of Health — Medical Marijuana Program | Regulator and patient access | Proposed new; deduplicate before import |
| Cresco Labs / Sunnyside | Medical operator / dispensary | org-667af67557f3 |
| Green Thumb Industries / RISE | Medical operator / dispensary | org-364a9eed8729 |
| Jushi / Beyond Hello | Medical operator / dispensary | org-c081c812feb2 |
| Verano / Zen Leaf | Medical operator / dispensary | org-2412bd73869d |
| PharmaCann / Verilife | Medical operator / dispensary | org-aefe1b952bc0 |
| Ascend Cannabis | Medical operator / dispensary | org-9878f97747e7 |
| Ethos Cannabis | Medical operator / dispensary | org-3a4a21b3faf4 |
| Vytal Options | Medical operator / dispensary | Proposed new; deduplicate before import |
| Organic Remedies | Medical operator / dispensary | Proposed new; deduplicate before import |
| Maitri Medicinals | Medical operator / dispensary | Proposed new; deduplicate before import |
| Standard Farms | Cultivation / processing | Proposed new; deduplicate before import |
| ACT Laboratories of Pennsylvania LLC | Laboratory | org-439251489828 |
| Keystone State Testing LLC | Laboratory | Proposed new; deduplicate before import |
| Steep Hill Pennsylvania | Laboratory | Proposed new; deduplicate before import |
| US Cannalytics, LLC | Laboratory | Proposed new; deduplicate before import |
| Coral Reef Labs | Laboratory | Proposed new; deduplicate before import |
| Pennsylvania Cannabis Coalition | Trade association | Proposed new; deduplicate before import |
| ResponsiblePA | Advocacy coalition | Proposed new; deduplicate before import |
| Cannaspire | Compliance / operations consulting | org-ce7e40ed878d |
| Duane Morris LLP | Legal / regulatory | Proposed new; deduplicate before import |
| Cannabis Law Solutions / HMS Legal | Legal / regulatory | Proposed new; deduplicate before import |
| First Commonwealth Federal Credit Union | Banking | Proposed new; deduplicate before import |
| Parke Bank | Banking | Proposed new; deduplicate before import |
| Balanced Veterans Network — Operation 1620 | Veteran / patient support | Proposed new; deduplicate before import |
| Community Legal Services of Philadelphia | Legal aid / record clearing | Proposed new; deduplicate before import |
| Legal Aid of Southeastern Pennsylvania | Legal aid / record clearing | Proposed new; deduplicate before import |
| Pennsylvania State Police — record access and expungement | Official record-clearing route | Proposed new; deduplicate before import |

## Coverage by visitor task

Counts overlap: a candidate may serve several pathways. Coverage below describes research readiness, not published statewide coverage.

| Pathway | Candidates | Remaining work |
|---|---:|---|
| dispensaries | 11 | Reconcile full official roster to present-day legal owners; verify local contact pages, addresses and county coverage. |
| seeds | 0 | No verified seed or growing-supply service candidates. Review applicable home-grow/hemp rules before listing shipping or cultivation claims. |
| records | 3 | Need northeast/Pocono and western Pennsylvania intake routes plus eligibility citations; no blanket cannabis expungement claim. |
| rules | 1 | Entry points reviewed, but topic-level statutes, effective dates and current injunctions still need a separate legal review. |
| medical | 2 | Official access and assistance plus one veteran support route; provider fees, eligibility and local accessibility need further work. |
| business | 23 | Need approved grower/processor roster, accounting, insurance, security, packaging, equipment and technology providers with PA-specific evidence. |
| community | 3 | Trade/advocacy/veteran organizations only; no future event verified. |

## What the official sources establish

The Department of Health publishes a retail roster dated September 16, 2026 and an approved-laboratory list. Those are different populations; do not count stores as organizations or treat an application archive as a current operational roster. The first batch uses the roster for brand presence and samples six laboratory addresses; it does not import every store or extrapolate a market total.

The program hub links patient registration, caregiver access, regulations and assistance. Purchase assistance is limited, not a benefit for every veteran. The veteran-support candidate is a provider-stated route subject to eligibility, funding and capacity.

Regulator notices matter alongside regulations. The program hub describes a testing-rule stay, and the grower page reports a botanical-terpene injunction and a revised per-permit API request process. A later legal pack must resolve statutes, regulations, court orders and effective dates together. No current adult-use, home-grow or federal rescheduling determination is made by this batch.

Record-clearing links are practical referral routes. LASP covers four named counties and says it is not currently assisting with pardon applications. Record access, sealing, expungement and pardon are distinct steps; none of these sources establishes blanket eligibility for all cannabis convictions.

## Pocono AI discovery hypotheses — not validated demand

These ideas connect the ecosystem research to the owner's proposed business. No customer interviews, price validation, quantified compliance-spend estimate, partnership, endorsement or sales outreach has occurred.

| Possible offering | Source anchor | Concrete first demonstration | What discovery must establish |
|---|---|---|---|
| Bank due-diligence document organizer | `pa-dobs`, `pa-firstcom`, `pa-parke` | Assemble a synthetic operator evidence packet: entity/owner documents, dated permit references, expected activity and a missing-document checklist. | Which documents operators and banks repeatedly request; who pays; security requirements; manual review and actual time saved. The DoBS page includes legacy federal-law language and cannot supply a current legal conclusion. |
| Regulatory update and SOP review assistant | `pa-doh`, `pa-growers`, `pa-regulations`, `pa-cannaspire`, `pa-duane` | Produce a source-linked change memo showing an agency notice, the affected procedure and questions for an authorized compliance reviewer. | Existing monitoring tools, review frequency, legal-review responsibility, error tolerance and willingness to pay. No autonomous legal determinations. |
| Operator reporting preparation | `pa-growers`, `pa-doh` | Reconcile synthetic exports, flag missing fields and prepare a draft reporting checklist without writing to the state system. | Actual export format, access permissions, current incumbent software and repeated reporting pain. Any API integration depends on the state's per-permit approval process. |

Begin discovery with the Pennsylvania Cannabis Coalition, a local compliance practice, and a Pennsylvania operator, using the directory to identify relevant organizations. These are suggested interview routes, not confirmed relationships or permission to message anyone. Verify the Pocono AI business identity and proposed offering before creating its listing. The repository currently prohibits paid placement, paid ranking and paid verification; any advertising proposal needs a separately defined owner decision and disclosure policy.

## Proposed next implementation issue

1. Reconcile current grower/processor and retail legal entities with brand identities; verify the nine proposed existing matches and avoid duplicate subsidiary records.
2. Add a research-only PA state pack, claim-level evidence, services and the first verified local locations using the existing schema. Prefer northeast Pennsylvania routes around Mt. Pocono/Stroudsburg, while retaining useful statewide referrals.
3. Review the key legal topics and official next steps; fill northeast/western record-help gaps and independently confirm suppliers before adding seed or fulfillment claims.
4. Regenerate affected outputs and exercise real user tasks. Publish a clearly labeled pilot only when advertised routes work; leave incomplete pathways visibly limited. Owner reviews and merges.
5. Continue bounded batches for accounting, insurance, security, packaging, equipment, technology and future events. Do not add a future event without a verified date and organizer page.

## Validation

Validation results are recorded in the pull request. The batch is research-only: no canonical, schema, renderer, generated page, release metadata or public state-picker changes.
