# Pennsylvania provider gaps: second research batch

Reviewed October 28, 2026. Parent roadmap: #42. Bounded issue: #65.
Baseline: `c112e97bc51adfdd1ad6ff9d16de8b8bae139c3f`, after expansion PRs #63 and #64 merged.

Six candidates are staged for review. Two match existing permanent identities;
four need final deduplication before receiving IDs. These files do not add public
listings. The accompanying JSON records contain claim-specific source references,
review dates, two provider-listed addresses, limitations and promotion requirements.

## Candidates and next steps

| Candidate | Reviewed offering | PA connection | Identity | Next step |
|---|---|---|---|---|
| Dura-Pack | Pouches and packaging automation | Dedicated PA supplier page | Proposed new | [Packaging inquiry](https://dura-pack.com/contact-us/) |
| Dutchie | Ecommerce menu integration | Documentation explicitly addresses PA dispensaries | Reuse `org-a06c1362a303` | [Integration documentation](https://support.dutchie.com/hc/en-us/articles/34041385932179-DOMO-Dutchie-E-Commerce-How-to-set-up-integration) |
| SD Associates, P.C. | Cannabis accounting | Names five PA local service areas | Proposed new | [Practice page](https://www.sdaccounting.com/industries-we-serve/cannabis/) |
| GreenGrowth CPAs | Cannabis accounting | Dedicated PA service page | Reuse `org-9ed4875dc1d5` | [PA practice page](https://greengrowthcpas.com/pennsylvania-cannabis-accounting/) |
| Alpine Packaging, Inc. | CBD labels | Provider-listed North Versailles address | Proposed new | [CBD label inquiry](https://www.alpinepackaging.com/products-custom-printed-labels-cbd-labels/) |
| Thar Process | Extraction equipment | Provider-listed Pittsburgh office | Proposed new | [Equipment inquiry](https://www.tharprocess.com/contact) |

Category memberships overlap: packaging 2, equipment 2, accounting 2 and
technology 1. Dura-Pack appears in both packaging and equipment; there are six
organizations, not seven. An office address proves local presence, not statewide
delivery. No county, coordinates, pickup point, plant-handling license or new
customer relationship is inferred. No form was submitted or phone call made.

## Evidence and limits

Eleven primary pages were opened and read. Eight support the six candidates;
three support the reasons for holding two other suppliers as leads. The source
map distinguishes source review from direct confirmation. No current-law review
is claimed, and provider legal, tax, medical, certification and performance
language is not adopted as independent evidence.

- Dura-Pack's PA page is undated and retains old contextual material. Its
  trailing-slash URL initially returned 403; the URL without that slash opened
  successfully. Both outcomes are recorded separately.
- Dutchie's claim stays limited to the documented integration. It does not
  establish every product feature or a live deployment.
- SD's service reach stays limited to its named areas. GreenGrowth's PA page
  contains inconsistent template text; its existing tax-source caution remains.
- Alpine stays a CBD-label candidate. Thar stays an equipment candidate. Neither
  is represented as an approved medical-marijuana processor or packaging product.
- BPI and Premier remain leads because reviewed pages did not establish PA reach.
  Green Mill's primary website was inaccessible; it receives no new review date.

## Relationship to the published pilot

The October 24 batch is historical research, not the current inventory. The
merged expansion already supplies 200 roster dispensaries, six law summaries,
patient routes, selected business providers, community groups and local legal
help including Allegheny. This batch targets business gaps left by that expansion.

The following counts describe **this batch only**, not the pilot's coverage:

| Pathway | New candidates | Remaining work |
|---|---:|---|
| Dispensaries | 0 | Current permit-holder reconciliation and the 37 unmatched roster geocodes remain outside this batch. |
| Seeds/growing | 0 | Equipment research supplies no consumer seed, shipping or home-grow route. |
| Legal/records | 0 | Central and most western PA local-help gaps remain. |
| Rules | 0 | Local ordinances, hemp-product rules, regulations and court orders need separate review. |
| Medical/patient | 0 | Clinician fees and local accessibility remain unreviewed. |
| Business | 6 | Review and promote these candidates; continue wider vendor and permit-holder research. No completeness denominator. |
| Community/events | 0 | No new event verified. Preserve the pilot's dated search limitations. |

## Promotion requirements

Use a separate bounded implementation issue after owner review. Reconcile new
identities, preserve the two existing IDs, and create service, coverage and contact
evidence with their actual scopes. Apply existing schema and importer conventions;
regenerate affected pages and run data, isolation and visitor-flow checks. Retain
the pilot labels and gaps. No release bump or automatic publication is proposed.

## Validation

The existing validator can inspect this batch without changing its original CLI:

```bash
python - <<'PY'
import json
from pathlib import Path
from scripts.validate_pa_research import validate
root = Path('.')
research = root / 'data/research'
batch = json.loads((research / 'pennsylvania-2026-10-28-business-candidates.json').read_text())
sources = json.loads((research / 'pennsylvania-2026-10-28-business-sources.json').read_text())
directory = json.loads((root / 'data/directory.json').read_text())
errors = validate(batch, sources, directory)
if errors:
    raise SystemExit('\n'.join(errors))
print('PASS: PA business research references, dates, identities, counts and research-only boundary')
PY
```

Repository-wide validation results are recorded in the pull request. Public data,
generated files, shared code, release metadata and the original research batch
are unchanged.
