# Replicable cannabis directory: stage-one contract

Contract version: 1.0.0. Stage one defines the data model and visitor pathways. Stage two is now implemented: `data/directory.json` is canonical, with adapters preserving Ohio counts and permanent links. See `STAGE_TWO_MIGRATION.md` for current maintenance instructions. The separate foundation pilot below remains a contract fixture.

## Visitor pathways

Every state reports coverage for the same seven tasks. Do not make people choose an industry category before telling us their need.

| ID | Visitor task | Useful destination | Main filters |
|---|---|---|---|
| dispensaries | Find a dispensary | Official lookup or suitable licensed location | State, city, county, medical/adult-use |
| seeds | Find seeds or growing supplies | Catalog, supplier contact or confirmed pickup | Coverage, seed sex, flowering behavior, fulfillment |
| records | Get legal or record-clearing help | Relevant assistance or application | County, eligibility, service status |
| rules | Understand state rules | Dated explanation and official source | State, topic, effective date |
| medical | Find patient/caregiver support | Official registration or support route | State, eligibility, service kind |
| business | Find business services | Provider contact and documented capabilities | Capability, coverage, organization type |
| community | Find groups or events | Contact, registration or participation page | Location, date, audience |

Pathway definitions and task-success criteria are machine-readable in `data/foundation/directory.json`. They describe a reusable interface contract; shared UI templates are implemented in stage two.

## Data boundaries

- **Organization:** one persistent identity. A national company is not copied into a new identity for every state. Preserve current `org-*` IDs when migrating existing CSV records. Do not regenerate IDs from mutable names or URLs after import.
- **Location:** one physical address belonging to an organization. Location-specific licenses, coordinates and services belong here. A mailing address is not automatically a store. Coordinates must be supplied as a pair; do not invent them.
- **Service:** an actionable offering tied to an organization, optional locations, pathways, audience, eligibility, availability and next step. Location and service coverage are different facts.
- **Coverage:** explicit state, county, national or online service reach. Empty coverage means unknown. A business's Ohio address does not prove Ohio shipping; “online” does not mean nationwide.
- **Evidence:** claim-level source, subject, value, source type, review date, effective date when applicable, recheck date and limitations. A reviewed catalog cannot establish active license, stock, quality, lawful shipment or pickup.
- **Rule:** state, topic, summary, effective date, official evidence and source action. Do not copy Ohio law into another state. Store future-effective rules separately from current requirements when implementing presentation.
- **Relationship:** references two existing organizations and evidence; not another organization row.
- **Event:** dated participation route, state, organizers and evidence; expired events must not remain “upcoming.”
- **State pack:** publication status, regulator, pathway coverage and existing public routes. Future templates consume state configuration rather than duplicated state-specific code.

`schemas/directory.schema.json` enforces the field contract. `validate_foundation.py` adds uniqueness, cross-reference, geography, evidence, date and publication checks. Unsupported fields are rejected so misspellings do not disappear silently.

## Verification vocabulary

Evidence status:

- `source-reviewed`: named source actually reviewed; only the stated claim is covered.
- `firsthand-confirmed`: documented direct confirmation, with a source record.
- `source-listed`: manufacturer/directory listing; direct policy or availability not confirmed.
- `unverified`: retained research lead; do not display as verified.
- `disputed`: conflicting evidence remains unresolved.

Fulfillment status is independent: `confirmed`, `seller-stated`, `manufacturer-listed`, `unverified`, `unavailable`. Public presentation should translate these into readable labels and show the supporting source. A seller's all-state shipping policy is a seller statement, not a legal opinion. Coverage requires evidence with claim `service-coverage`; supported fulfillment requires `fulfillment-shipping`, `fulfillment-pickup`, `fulfillment-in-person` or `fulfillment-online` for the same service. Profile-only evidence cannot support these badges.

Seed sex (`regular`, `feminized`) and flowering behavior (`autoflower`, `photoperiod`) are separate future UI facets. `triploid` is a distinct genetics attribute. The pilot preserves current catalog tags; stage two will split the flat list into these facets without implying every possible combination is sold.

## Publication and coverage

State publication statuses: `not-started`, `research-only`, `pilot`, `live`. Only pilot/live packs may supply public routes. The public picker must not advertise research-only or not-started states. Pilot options must be visibly labeled.

Every state declares pathway coverage: `not-reviewed`, `starter`, `partial`, `broad`. These labels never mean exhaustive coverage. Always retain limitations; future “broad” claims need a documented denominator and review method. Missing records mean unknown coverage, not absence of service.

Adding a new state:

1. Copy `data/foundation/state-template.json`, replace placeholder identity and date, and add the official regulator.
2. Review authoritative state-specific rules, medical registration, dispensary lookup and legal-help routes; record claim-level sources.
3. Reuse existing organization IDs; add local locations/services and explicit coverage only where supported.
4. Report all seven pathways, including unreviewed gaps. Keep the pack research-only while validating.
5. Validate and exercise real user tasks. Publish a clearly labeled pilot only when its advertised routes are usable and reviewed; do not fill missing routes with Ohio referrals.

## Pilot and migration limits

The foundation pilot contains the existing 11 seed/supply organizations, 11 service routes and their source references. It intentionally has no location, rule, relationship or event rows yet. Existing Ohio pages still provide those resources. No existing source records, organization counts or links were removed.

The imported seed evidence is explicitly labeled `supplier-profile`; individual shipping, address, inventory and catalog claims have not been decomposed into separate evidence rows. Fulfillment remains `unverified` and coverage empty in this pilot, even when the existing page quotes a seller policy. Stage two must split these claims before using them for fulfillment or coverage filters. In stage two, the seed JSON becomes a generated compatibility download; the public seed builder reads a lossless canonical adapter.

Pilot IDs use a deterministic initial import key because the seed list had no IDs. Once created, these IDs persist through name/website changes. Before merging pilot organizations into the master CSV, match existing identities and create aliases; do not create duplicate companies. The foundation validator does not perform fuzzy deduplication.

Recheck date is a queue trigger, not a claim that a source is valid until that date. Pilot entries use a 30-day review queue. During migration, prioritize rules and licensing changes, service closures, fulfillment restrictions, and dated events; monitor official changes as well as scheduled reviews.

## Stage two acceptance criteria and ongoing data work

- Shared renderers and per-state configuration; no copy-and-edit state code.
- Reviewed adapter preserving existing CSV IDs, source text, scope flags and relationship links.
- Separate physical location and organization counts; distinguish unknown coverage from confirmed statewide reach.
- Claim-specific evidence for fields exposed as filters or verification badges.
- Existing organization URLs preserved or redirected via aliases; no dependency on array index.
- Service cards answer who qualifies, where it works, what to do next and what remains uncertain.
- Visible active filters, separate seed sex/flowering facets, readable statuses and mobile controls.
- Regression tests for search, URLs, exports, evidence links, publication gates, mobile and print.
- Task checks for a nearby dispensary, relevant record-clearing help, and a supplier serving the selected state; successful task means reaching a relevant next step, not viewing a card.
- One additional state demonstrates replication before wider rollout.

Run `python validate_foundation.py` and `python tests/foundation.py`. Existing site tests continue to validate the current public build.
