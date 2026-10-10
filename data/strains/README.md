# Cannabis ancestry repository

This is a source-attributed pilot, not a complete genealogy or DNA certification. Open `ancestry.html` for search and expandable ancestry; the CSV opens in Excel. Two marketed Blue Dream breeder lines and three unresolved parent labels demonstrate the model.

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

Only concise factual claims and original notes are stored. Source descriptions and images are not copied. Public menus can later supply a separate last-seen availability table; they are not ancestry evidence.

## Current review

Barney's Farm lists Blueberry × Super Silver Haze. Humboldt Seed Organization gives the same cross in its specification table and a less specific selected-Haze parent in prose. Both HSO formulations remain visible for a specificity review. The breeder lines remain separate; neither is mapped to the historic clone or Ohio products.
