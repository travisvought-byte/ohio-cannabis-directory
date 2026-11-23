# The Reefer source pipeline

Keeps every state page on the-reefer.com filling with **checked** listings, taken from each
regulator's own published list, the same way the Ohio directory was built: every row traces to
a named public source with the date it was retrieved and an evidence level.

```
pipeline/registry.json  ->  fetch  ->  .pipeline-cache/raw/<source>.<ext>    (raw, never committed)
                            normalize ->  data/sources/pipeline/<source>.json  (business fields only)
                            merge     ->  data/state-retail-locations.json     (deduped, one entry per state)
                            coverage  ->  data/pipeline-coverage.json + architecture/PIPELINE_COVERAGE.md
build_national.py renders state-retail-locations.json as "Where to buy" on each state page.
```

## Run it cold

The state sites are reached from GitHub's servers, so the normal way is the Actions workflow:

1. GitHub → Actions → **Mine state sources** → Run workflow.
2. Leave "only" blank for every active source, or type state codes (`MA CO MI`) or source ids.
3. Leave "publish" ticked. The run pulls, normalizes, merges, rebuilds `national/`, runs the
   checks, commits to `main` and starts the Pages deploy. Untick it for a dry run; the log still
   shows what each source returned (`pipeline.probe` prints column names and category counts only).

On a computer with internet access:

```bash
pip install -r requirements.txt -r pipeline/requirements.txt
python -m pipeline.run                 # everything active
python -m pipeline.run --only MA CO    # some states
python -m pipeline.run --offline       # rebuild from committed snapshots, no downloads
python -m pipeline.probe --only MA     # columns + license type/status counts of a download
python build_national.py               # regenerate the state pages
python -m unittest discover -s tests -p 'test_*.py'
```

## Add or fix a source

Add an entry to `pipeline/registry.json` → `sources`:

| Field | Meaning |
| --- | --- |
| `id` | `us-<state>-<what>`, never reused |
| `jurisdiction`, `scope` | state code (or ISO country code) and `state` / `country` |
| `topic` | `retail`, `medical-dispensary` or `retail-and-medical` (store lists) |
| `publisher`, `title`, `landing_url` | the regulator and the public page a person can check |
| `fetch` | `method` = `socrata`, `arcgis`, `csv`, `xlsx`, `json`, `pdf`, `html`, `page-link` (follow the first link on `url` matching `link_pattern`, then read it as `then`), or `manual` |
| `parse` | `header_contains` (a header cell, for Excel/PDF), `sheet`, `skiprows`, `table`, `records_path` |
| `keep` | rules `{column, match (regex), not}`, all must hold, e.g. retail license types that are active |
| `kept_rule` | the same rule in plain words, published with the snapshot |
| `map` | normalized field → source column, list of columns, `{template}`, `{const}` or `{regex, column}` |
| `count_columns` | columns whose value counts are kept as the denominator |
| `label` | how the state page names the list ("retailers the Commission lists as licensed") |
| `evidence_level` | one of `EVIDENCE_LEVELS` in `pipeline/common.py` |
| `cadence_days` | how often the list should be re-pulled |
| `status` | `active`, `queued` (known source, not yet automatable) or `blocked` (turned the runner away) |

Normalized fields are fixed in `pipeline/common.py` (`FIELDS`). Anything else a source publishes,
including owner and contact names, is dropped.

## Rules the pipeline keeps

- **Public sources only.** No sign-ins, no accounts, no forms submitted, no messages sent.
- **Regulator first.** Store lists come from the regulator or the state's official open-data
  portal. A business's own page can support a listing at `business-own-page` level only.
- **A blocked retrieval is not a review.** A 403, login wall or bot check marks the source
  `blocked` in `_fetch-log.json` and the coverage queue. Nothing tries another route (no
  mirrors, caches, archives or third-party copies). A person looks at it.
- **Dated, not live.** Every snapshot keeps its retrieval date, the download address, a SHA-256
  of the raw file, the whole-file row counts and the rule used to keep rows.
- **Owner coverage rules** (from the Ohio directory): a business's own in-state office address
  counts as county coverage on state pages; trade-show exhibiting counts as cannabis-adjacent
  evidence; semi-legitimate local sources are listable with their evidence level; Ohio operators
  get full evidence reviews every 90 days, national vendors a routine check every 180 days.
- **Ohio, Pennsylvania and New York** keep their own full guides and store finders; the pipeline
  does not replace those lists on their pages.
- No paid placement and no ads on cannabis pages.

## Countries

Country store and club lists are still imported by `import_where_to_buy.py` (Canada's provinces,
Malta, Switzerland, Germany, Uruguay, Thailand). They are in the registry with `scope: country`
so the coverage report ranks them; moving each into the automatic fetch is listed in the queue.
