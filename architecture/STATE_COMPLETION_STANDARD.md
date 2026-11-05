# State completion standard

Version 1.0.0, adopted 2026-11-05. Thresholds and denominators live in [`data/state-standard.json`](../data/state-standard.json). [`build_state_scorecard.py`](../build_state_scorecard.py) measures every published state against them and writes [STATE_SCORECARD.md](STATE_SCORECARD.md).

## Purpose

Ohio is the reference state. A state is finished when it meets the same bar Ohio is held to. Coverage labels (`starter`, `partial`, `broad`) are earned from the data under this standard, not chosen by hand. A test fails if a state pack's published label differs from the level its data earns.

The [state directory contract](STATE_DIRECTORY_CONTRACT.md) defines the data model and the seven visitor pathways. This standard defines how complete each pathway must be. Neither label ever means exhaustive coverage.

## Principles

1. **Measure against a dated count where one exists.** A "broad" dispensary claim needs the regulator's own count and date. Where no count exists (seed sellers), the ceiling is `partial`.
2. **Count only what the data supports.** Rules need official evidence and an effective date. Coverage counts only when recorded on the record, not implied by an address.
3. **The same thresholds apply to every state.** Denominators differ by state; thresholds do not.
4. **Missing records mean unknown, not absent.** A low level is a work list, not a claim that help does not exist.

## Levels by pathway

| Pathway | Starter | Partial | Broad |
| --- | --- | --- | --- |
| Dispensaries | Official lookup route | Regulator-listed locations for at least 50% of the regulator's current count | At least 95% of the regulator's count, from a source retrieved within 90 days |
| Rules | At least one officially sourced rule or law route | 4 of the 7 core topics | All 7 core topics, each with official evidence and an effective date |
| Records | At least one record-relief route | 5 or more routes, at least one with recorded statewide coverage | Partial, plus county-specific help in at least 50% of the state's counties |
| Medical | At least one route | 3 or more routes, 2 officially sourced | 8 or more routes, 3 officially sourced and at least 1 patient-support organization |
| Business | At least one listing | 25 or more listings; at least 75% with confirmed in-state coverage; at least 60% with a phone or email | 150 or more listings; at least 90% confirmed coverage; at least 80% phone or email; at least 95% categorized; at least 90% reviewed within the review policy |
| Community | At least one group or upcoming event | 5 or more groups and upcoming events | 15 or more, including at least 1 upcoming event |
| Seeds | At least one route | 5 or more routes with fulfillment recorded | Not available until a documented denominator exists |

Core rule topics: adult-use possession, home grow, public consumption, driving, employment, medical use and record relief (expungement or sealing).

## How measures are counted

- **Dispensaries:** state locations carrying government evidence, divided by the regulator count recorded in `data/state-standard.json`. Update the count and its date whenever the regulator publishes a new list.
- **Business:** published listings only (scope `public`). For legacy Ohio records, confirmed coverage means any service area other than "Multistate, Ohio unconfirmed", and reviews are current under [REVIEW_POLICY.md](REVIEW_POLICY.md). For other states, confirmed coverage means a recorded state or county coverage entry, and reviews are current when the newest evidence is under 180 days old. Categorized means the listing carries a business category.
- **Records:** county-specific help counts recorded county coverage, plus, for Ohio, the counties in the court-search guide (`data/record-clearing-courts.json`).
- **Medical, community, records and seeds:** routes may belong to organizations kept out of the business listings (scope `retained`); withdrawn organizations never count.
- **Community:** events count while their end date (or start date) is on or after the directory's `as_of` date.

## Maintaining the standard

- Raising or lowering a threshold is an owner decision. Change `data/state-standard.json`, bump its version, rerun the scorecard and update any state labels the change affects in the same pull request.
- Adding a state: add its county count, regulator dispensary count with date and source, and its location-source retrieval date to `data/state-standard.json`. The scorecard picks the state up once its pack is `pilot` or `live`.
- A pilot state is ready to drop the pilot label when every pathway matches Ohio's level or higher.
