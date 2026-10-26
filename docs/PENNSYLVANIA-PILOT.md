# Pennsylvania cannabis pilot: readiness and next steps

## October 26 readiness review — issue #58

The original staging work has reached `main` (`7eee75f`): advocacy #48/#51, referrals #53 (including #46), and queued research/comparison integration #55 (including #44/#39). No Pennsylvania implementation PR remains open as of this review. Issue #47 remains open because the original acceptance criteria included an interactive editable letter; the published page had only a static message starter. Issue #58 supplies that missing workflow without repeating the completed research or changing the comparison design.

The existing advocacy, Ohio advocacy entry and `state.html?state=PA` URLs returned HTTP 200 in the October 26 check. Main's `Validate directory` run 40161325367 and Pages deployment 40161324633 succeeded. These establish that the existing pilot is published, not that #58 is deployed.

The smallest complete advocacy pilot consists of:

- Existing source-linked proposal cards, dated snapshot and official legislator contact route.
- Existing five published patient/legal-help referrals, visible pilot labels and coverage gaps.
- Four visitor-selected questions drawn from the page's existing topics, optional town/district and personal reason, explicitly built/rebuilt editable draft, exact-text copy/download and letter-only print.
- Preserved edits when inputs change, manual copy fallback, clear-details control, no draft storage or sending, and usable static/no-JavaScript instructions.
- Deterministic build plus regression checks for the actual visitor workflow, privacy, mobile and print behavior.

The #58 implementation preserves all existing legal summaries and their October 24 review dates. The General Assembly portal was opened October 26 to confirm the existing contact entry; this is not a fresh review of every bill or service. No new policy outcomes, market-wide coverage or resident experiences are asserted.

Publication gate: review and merge the #58 PR, allow `Validate directory` and Pages deployment to pass, then check the live topic → build → edit → copy/download/print flow and PA referral link. Under `AGENTS.md`, Travis merges; this review does not merge or publish the new workflow. No release bump is required by this issue.

Validation for #58: deterministic generated-page/data/release checks, both foundation validators, foundation/migration/location/review-cleanup/ancestry regressions, strain ancestry validation (no errors), `npm test` and all ten `npm run test:browser` suites passed locally. New PA tests exercise exact edited copy/download/print output, explicit rebuild, clipboard denial fallback, clearing, no draft storage or personal text in requests/analytics, 320/390/1280px width and no-JavaScript instructions. The 390px composer screenshot was visually inspected. JavaScript syntax and `git diff --check` passed. A temporary workspace disconnect occurred during testing; it recovered and the complete browser suite subsequently passed.

### Work after the pilot, not launch blockers

- Reconcile the 28 research-only operator/provider candidates against permit and persistent organization identities before publication; nine initial proposed matches became eleven in #55, with the two already-published agency identities reused.
- Build dated topic-by-topic PA comparisons separately; the existing Ohio/Michigan licensing comparison does not constitute PA comparison coverage.
- Expand local ecosystem, suppliers, events and professional-service coverage only as source-reviewed routes become useful. Keep the seven pathway gaps visible.
- Refresh bill statuses and contact routes before promoting a later legislative snapshot; never advance the legal review date from a failed fetch.

## Earlier staging record

Updated October 24, 2026. The pilot begins with a source-linked advocacy entry point in `pennsylvania-advocacy.html`. It is intentionally a first-stage page: business/operator coverage remains research work. Issue #52 publishes five reviewed patient and legal-help referral routes in the shared state view, with a labeled pilot and explicit gaps.

## What is established

- Pennsylvania's current statewide cannabis program is medical, administered by the Department of Health.
- HB 20 (2025–2026), sponsored by Rep. Emily Kinkead with Rep. Abby Major and others, proposes a Keystone Cannabis Authority and private-market framework. Its last listed action is referral to House Health July 14, 2025. Source: https://www.palegis.us/legislation/bills/2025/hb20 .
- HB 1200 (2025–2026) is a current-session adult-use proposal. The House passed it 102–101 on May 7, 2025; the Senate referred it to Law & Justice, where a motion to report it was defeated 3–7 on May 13, 2025.
- Rep. Rick Krajewski is HB 1200's prime sponsor.
- SB 120 (2025–2026), with Sen. Daniel Laughlin as prime sponsor and Sen. Sharif Street as a co-sponsor, proposes a Cannabis Control Board and adult-use framework. Referred to Senate Law & Justice July 10, 2025; a discharge resolution was presented June 29, 2026 and dropped from the calendar October 19, 2026. This is not a vote defeating the bill. Source: https://www.palegis.us/legislation/bills/2025/sb0120 .
- SB 846, sponsored by Sen. Daniel Laughlin with Sen. Sharif Street and others, belongs to the 2023–2024 session and must be shown as historical.
- The official General Assembly portal is the route to legislator lookup, bill search, committee calendars and current contacts.

These facts are linked to official sources on the page. The HB 1200 outcome is bill-specific; it must not be generalized into a claim that all adult-use bills or future proposals failed.

## Four staging reviews

1. **Policy accuracy — pass with correction.** Review found that the first draft emphasized HB 1200 and underrepresented HB 20. A later review identified omitted SB 120; issue #50 corrects that gap. The page covers HB 20, HB 1200 and SB 120 with distinct sponsors, committees and procedural histories.
2. **Source integrity — pass.** The official bill histories, PA Department of Health program page and General Assembly portal are linked. HB 1200's 2025 Senate committee vote is scoped to that bill; SB 846 is clearly labeled historical.
3. **Usability and privacy — pass at source review.** The page uses responsive CSS, semantic headings, keyboard-focus styling, plain-language next steps and an editable message starter. It does not collect or send visitor information. This is a code review; no browser/print rendering review is claimed.
4. **Repository integration — corrected.** The page is generated from `templates/pennsylvania-advocacy.html` by `build_pennsylvania_advocacy.py`, uses shared navigation/footer/analytics, links from the Ohio advocacy page and appears in the sitemap. Reproducibility validation includes the new builder. Full validation and rendering evidence are recorded in PR #48. This supports an advocacy pilot launch; the five reviewed PA referral services are promoted under #52; operator candidates remain gated under #44.

## Expansion after the advocacy pilot

1. **Advocacy entry point:** publish source-linked status, identify decision routes, and offer editable constituent questions without collecting or sending information.
2. **PA policy and comparison pack:** extract current medical-program rules and proposed adult-use provisions into dated, cited topic cards. Compare each topic with Ohio and at least one relevant neighboring market. Separate enacted law, proposed bill text, observed market outcomes and editorial analysis.
3. **PA ecosystem seed set:** research a deliberately small, actionable set of organizations across licensed operators, independent business and professional services, patient/community advocacy, labor, research/public health, and government. Use first-party or official sources, persistent IDs, claim-level evidence, and explicit coverage limits. Do not infer that a company operates in Pennsylvania from a national brand page or a bill's mention of an industry.
4. **Publication gate:** run the repository's state/data validation, confirm source links and dates, add PA to the shared state renderer only when its seven need pathways have truthful coverage labels, and connect the advocacy entry point through navigation. Keep the state marked pilot until the public directory has useful referrals and transparent gaps.

## Suggested first research batches

- **Decision-makers:** current sponsors and committee assignment for each live bill, committee chair and membership from official sources, leadership, and official legislator contact routes.
- **Market and regulator:** Department of Health medical program, current permit/location sources, official program statistics and rulemaking.
- **Business and community:** named Pennsylvania operators and independent providers from official permit information and first-party sites; statewide advocacy, patient, labor, research and public-health organizations from their own publications.
- **Comparison:** market structure, licensing, medical-to-adult-use transition, expungement, social-equity provisions, local authority and tax/reinvestment. Each comparison needs a dated source and a clearly labeled inference where outcomes are not directly comparable.

The selected current-session bills have distinct sponsors, market structures and committee histories; do not collapse them into one proposal or describe the stalled HB 1200 vote as the outcome of HB 20. The first public iteration should not claim a complete market map, current bill momentum, eligibility, service coverage, sales, or political support beyond what the cited sources establish.
