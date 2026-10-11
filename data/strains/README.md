# Growing cannabis strain library and ancestry

Open `ancestry.html` for 336 searchable profiles covering 318 distinct names. There is no fixed catalog cap. `strains.csv` exports every public profile for Excel; `ohio-flower.csv` exports dated flower menu observations. `ancestry.csv` exports attributed claims; `ancestry.json` is canonical. Supporting parent references and breeder examples are excluded from the public catalog count.

## Selection and details

Reviewed October 10, 2026. This is an editorial, unranked collection of widely recognized classics, contemporary favorites and historically influential CBD-associated cultivars. Selection was informed by Leafly's best-selling-strains coverage, its all-time selection and Weedmaps' popular-strain coverage. It is not a claim that these are precisely the 100 biggest sellers, most searched strains, or available strains in Ohio. A complete independently verifiable national ranking was not available.

- https://www.leafly.com/news/strains-products/best-selling-weed-strains
- https://www.leafly.com/news/strains-products/top-100-marijuana-strains
- https://weedmaps.com/news/2020/05/12-of-the-most-popular-strains-on-weedmaps/

The original classics link to individually reviewed Leafly pages. Additions link to the reviewed producer profile or dated menu source. Producer sensory descriptors are attributed reports; missing effects and reader counts remain empty. Reader-report counts are a dated engagement snapshot, not sales, independent customers or a popularity rank across all strains. The optional review-count sort compares only this collection. Effects and flavors are reader-reported descriptors, not clinical claims. Profile terpene reports do not certify current batch chemistry; check product labels for cannabinoids and terpenes. No fixed THC/CBD numbers, therapeutic indications, product prices or live-stock promises are inferred.

Genetics and history use concise original summaries. Secondary ancestry claims are labeled as such. Where checked breeder or producer sources differ, the page displays attribution and review notes. No source descriptions, reviews or images are republished wholesale.

## Deconfliction rules

- A record represents a breeder line or identified cut, not every plant sharing a name. Keep seeds, clones and autoflower versions separate.
- Stable IDs survive spelling corrections. Name normalization finds review candidates; it never merges records or infers aliases.
- Store each source's parentage as an independent claim. Preserve superseded claims for audit; they do not participate in the current graph.
- A named parent of unknown breeder/cut is an unresolved reference. Sharing that reference does not prove shared genetics.
- Cross order does not imply maternal/paternal direction. The pilot accepts undirected, two-slot crosses; repeated parents permit documented self crosses. More complex pedigrees need explicitly sourced intermediate nodes.
- Multiple parent sets trigger review. They may reflect differences in specificity, not disagreement. Review the original sources before changing status to disputed.
- Keep separate same-name records unless evidence establishes identity. Record the decision and reason. Automatic merging is intentionally unsupported.
- Missing ancestry stays unknown. Never invent parents, percentage ancestry, breeder attribution, effects or Ohio stock.

## Add a sourced lineage

1. Search records and aliases for possible duplicates; check breeder and cut identity.
2. Add source URL, publisher and review date. Prefer breeder catalogs or documented breeder statements. Independently corroborate historical claims when possible.
3. Add strain records with unique IDs and the appropriate kind; use unresolved-parent when identity is incomplete.
4. Add a claim with two parent IDs, sources, status, limitations and unspecified parent roles.
5. Run `python strain_ancestry.py` and inspect name collisions and parentage review. Record identity decisions without deleting evidence.
6. Run `python tests/ancestry.py` and `python build_ancestry.py`.

Only concise factual claims and original notes are stored. Source descriptions and images are not copied. Public menus supply separate dated observations; they are not ancestry evidence or proof of current inventory.

## Current review examples

- Blue Dream: the general market-name profile stays separate from Barney's Farm and Humboldt Seed Organization lines. Shared labels do not establish clone identity.
- Biscotti: two incompatible published parent sets remain separate disputed claims.
- Cannatonic: Resin Seeds identifies Reina Madre × NYC Diesel. This breeder account takes priority over the different secondary profile; the earlier claim is retained as superseded and excluded from the current tree.
- Blueberry: Dutch Passion's broader ancestry account is displayed with the secondary source difference noted.
- Blueberry Muffin: Native Sun names Razzleberry while Leafly names Blueberry. Both attributed accounts remain visible for breeder review.

## Verification

Run `python tests/ancestry.py`, `node tests/ancestry.cjs` and `node tests/ancestry-browser.cjs`. Python checks profile completeness, source references, identity collisions, competing claims, graph cycles and deterministic HTML/CSV exports. UI checks cover aliases, filters, sorting, exact record links, pagination, competing trees and mobile layout. Run `python build_ancestry.py` after changing the canonical data or page builder.

## Ohio expansion: October 10, 2026

- 112 individually reviewed Klutch profiles, including its Cookies and Josh D collaborations. A verification wall blocked the Josh D OG detail page; it was not padded into the catalog.
- 36 individually reviewed Certified profiles, with producer-credited breeders and sensory notes. Sour Tangie is retained as a distinct producer context: Certified describes an RPO #3 phenotype, which must not inherit other same-name parentage.
- 45 individually reviewed Standard Wellness profiles. This is a multi-state producer catalog; it does not establish availability in Ohio. Gusher Mintz, Jungle Pie and Citrus Cookie Kush have internally inconsistent lineage descriptions. Sour Snow has inconsistent type labels. Review notes retain these differences; ambiguous expressions are not modeled as settled crosses.
- 20 Buckeye profiles from its consolidated current genetics page. Preserve its abbreviations; do not guess what every shorthand means. Only short names, type and factual crosses are retained from the consolidated page.
- 23 additional producer-specific menu profiles with unknown genetics, plus observations attached to existing exact producer/name contexts. There are 27 observations across Warren, Cincinnati and Columbus, with package-size duplicates collapsed. No prices, potency, demand, clinical effects or live-stock promises are inferred.

The Garden source explicitly shows an October 10, 6:02 PM update. Warren's public menu was reviewed on October 10 without a published update timestamp. Columbus product pages may reflect older cached listings. `checked_on` means source review, not inventory confirmation. Catalog inclusion and listing frequency are not statewide sales popularity. An older Firelands genetics sheet was located but not used to pad the current catalog.

### Maintaining the growing catalog

Add profiles with stable IDs, explicit producer context, sources and a review date. Set `catalog: true`; retain `popular` only as the original editorial-classics flag. Update selection profile/name counts as an audit snapshot, never as a catalog limit. Empty arrays mean unestablished effects, flavors or terpenes; `review_count: null` means no checked reader-report count.

For menu observations, record the profile, store, city, source, checked date and source update time when available. Keep `inventory_status: not-confirmed`. Evidence remains separate from lineage claims. Run the Python validator and ancestry tests, rebuild, then run UI/browser checks before publishing. Complex pedigrees remain text unless intermediate identities are explicitly sourced. Same-name producer profiles remain separate; only a documented identity decision can merge them.
