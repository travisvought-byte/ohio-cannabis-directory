"""Turn each downloaded source into a normalized, business-only snapshot.

Reads .pipeline-cache/raw/<source id>.<ext>, keeps only the rows the registry's "keep"
rules select (for example retail licenses that are active), maps the publisher's columns
onto the fields in pipeline/common.py, and writes data/sources/pipeline/<source id>.json.

Only business details are copied: names, the licensee entity, the street address, the
business phone and website, license number, type and status, and coordinates when the
regulator publishes them. Owner names, contact people and every other column are dropped.

Run: python -m pipeline.normalize [--only ID_OR_STATE ...]
"""
import argparse
import io
import json
import re
from collections import Counter

from pipeline.common import (EVIDENCE_LEVELS, FETCH_LOG, FIELDS, RAW, SNAPSHOTS, clean, load_json, phone, registry,
                             save_json, title_if_shouting, today, website, zip5)


def _key(col):
    return re.sub(r'[^a-z0-9]', '', str(col).lower())


def header_index(rows, needle):
    needle = _key(needle)
    for i, row in enumerate(rows[:60]):
        if any(_key(c) == needle for c in row if c is not None):
            return i
    raise ValueError(f'no header row containing {needle!r}')


def table_rows(matrix, header_contains):
    """A list of lists (from Excel or PDF) -> list of dicts, starting at the header row."""
    start = header_index(matrix, header_contains) if header_contains else 0
    header = [clean(h) or f'col{i}' for i, h in enumerate(matrix[start])]
    out = []
    for row in matrix[start + 1:]:
        if row is None or all(clean(c) is None for c in row):
            continue
        if [clean(c) for c in row[:len(header)]] == header:  # header repeated on a later page
            continue
        out.append({header[i]: row[i] for i in range(min(len(header), len(row)))})
    return out


def read_raw(source):
    spec, parse = source['fetch'], source.get('parse', {})
    ext = spec['then'] if spec['method'] == 'page-link' else ('json' if spec['method'] in ('socrata', 'arcgis') else spec['method'])
    path = RAW / f'{source["id"]}.{ext}'
    if not path.exists():
        raise FileNotFoundError(path)
    if ext == 'json':
        data = json.loads(path.read_text(encoding='utf-8'))
        for part in parse.get('records_path', []):
            data = data[part]
        return data
    import pandas as pd
    if ext == 'csv':
        df = pd.read_csv(path, dtype=str, skiprows=parse.get('skiprows', 0), encoding=parse.get('encoding', 'utf-8-sig'))
        return df.to_dict('records')
    if ext == 'xlsx':
        sheet = parse.get('sheet', 0)
        matrix = pd.read_excel(path, sheet_name=sheet, header=None, dtype=object).values.tolist()
        return table_rows(matrix, parse.get('header_contains'))
    if ext == 'html':
        tables = pd.read_html(io.StringIO(path.read_text(encoding='utf-8', errors='ignore')), match=parse.get('match', '.+'),
                              header=parse.get('header'))
        if parse.get('all_tables'):
            # Tables whose first header cell names them (e.g. "Southern Nevada Retail Stores"):
            # keep the ones matching table_title and give their first column one common name.
            frames = [f.rename(columns={f.columns[0]: parse.get('first_column', f.columns[0])}) for f in tables
                      if re.search(parse.get('table_title', '.'), str(f.columns[0]))]
        else:
            frames = [tables[i] for i in parse['tables']] if 'tables' in parse else [tables[parse.get('table', 0)]]
        return [r for f in frames for r in f.astype(object).to_dict('records')]
    if ext == 'pdf':
        import pdfplumber
        matrix = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    matrix.extend(table)
        return table_rows(matrix, parse.get('header_contains'))
    raise ValueError(f'cannot read {ext}')


def column(row, name):
    """Case- and punctuation-insensitive column lookup."""
    if name in row:
        return row[name]
    want = _key(name)
    for k, v in row.items():
        if _key(k) == want:
            return v
    return None


def value(row, rule):
    if rule is None:
        return None
    if isinstance(rule, str):
        return clean(column(row, rule))
    if isinstance(rule, list):
        parts = [clean(column(row, c)) for c in rule]
        return clean(' '.join(p for p in parts if p))
    if 'col_index' in rule and 'regex' not in rule:  # tables whose header names vary
        vals = list(row.values())
        return clean(vals[rule['col_index']]) if rule['col_index'] < len(vals) else None
    if 'path' in rule:  # nested JSON, e.g. {"path": ["location", "coordinates", 1]}
        v = row
        for part in rule['path']:
            try:
                v = v[part] if not isinstance(v, dict) else column(v, part)
            except (IndexError, KeyError, TypeError):
                return None
        return clean(v)
    if 'const' in rule:
        return rule['const']
    if 'template' in rule:
        text = re.sub(r'\{([^}]+)\}', lambda m: clean(column(row, m.group(1))) or '', rule['template'])
        return clean(re.sub(r'(\s*,)+', ',', text).strip(' ,'))
    if 'regex' in rule:
        src = list(row.values())[rule['col_index']] if 'col_index' in rule else column(row, rule['column'])
        text = clean(src) or ''
        m = re.search(rule['regex'], text)
        return clean(m.group(rule.get('group', 1))) if m else None
    raise ValueError(f'bad map rule {rule}')


def keep(row, rules):
    for rule in rules:
        text = clean(column(row, rule['column'])) or ''
        hit = re.search(rule['match'], text, re.I) is not None
        if hit == bool(rule.get('not')):
            return False
    return True


def normalize_row(row, mapping, state):
    out = {}
    for field in FIELDS:
        v = value(row, mapping.get(field))
        if v is None:
            continue
        if field in ('name', 'licensee', 'street', 'city', 'county', 'address'):
            v = title_if_shouting(v)
        elif field == 'phone':
            v = phone(v)
        elif field == 'website':
            v = website(v)
        elif field == 'zip':
            v = zip5(v)
        elif field in ('lat', 'lon'):
            try:
                v = round(float(v), 6)
            except ValueError:
                v = None
        if v not in (None, ''):
            out[field] = v
    out.setdefault('state', state)
    if out.get('county'):
        out['county'] = re.sub(r'\s+county$', '', out['county'], flags=re.I)
    if out.get('state') and len(out['state']) > 2:
        out['state'] = state
    if out.get('licensee') and (not out.get('name') or re.match(r'^\d+\s', out['name'])):
        out['name'] = out.pop('licensee')  # some lists put the street in the trade-name column
    if out.get('address'):  # "Portland Or 97214" after title-casing -> "Portland, OR 97214"
        out['address'] = re.sub(r',?\s+%s\s+(\d{5})' % re.escape(state.title()), r', %s \1' % state, out['address'])
    return out


def snapshot(source, log_entry):
    rows = read_raw(source)
    rules = source.get('keep', [])
    kept = [r for r in rows if keep(r, rules)]
    counts = {}
    for col in source.get('count_columns', []):
        counts[col] = dict(Counter((clean(column(r, col)) or '(blank)') for r in rows).most_common(40))
    normalized, dropped = [], 0
    for r in kept:
        n = normalize_row(r, source['map'], source['jurisdiction'])
        if not n.get('name') or not (n.get('street') or n.get('address')):
            dropped += 1
            continue
        normalized.append(n)
    normalized.sort(key=lambda r: ((r.get('city') or '').lower(), r['name'].lower(), r.get('street') or r.get('address') or ''))
    if not normalized:
        raise RuntimeError(f'{source["id"]}: no rows kept from {len(rows)} (columns: {sorted(rows[0]) if rows else "none"})')
    return {
        'source_id': source['id'],
        'jurisdiction': source['jurisdiction'],
        'topic': source['topic'],
        'publisher': source['publisher'],
        'title': source['title'],
        'landing_url': source['landing_url'],
        'download_url': log_entry.get('resolved_url') or source['fetch'].get('url'),
        'retrieved_on': log_entry.get('fetched_at', today())[:10],
        'sha256': log_entry.get('sha256'),
        'evidence_level': source['evidence_level'],
        'evidence_meaning': EVIDENCE_LEVELS[source['evidence_level']],
        'export_rows': len(rows),
        'export_counts': counts,
        'kept_rule': source.get('kept_rule', 'All rows.'),
        'kept_rows': len(normalized),
        'dropped_incomplete_rows': dropped,
        'limitations': source.get('limitations', 'A dated copy of the regulator\'s list, not a live license verification. Hours and inventory are not copied; confirm with the store.'),
        'rows': normalized,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args(argv)
    log = load_json(FETCH_LOG, {})
    wanted = {o.upper() for o in (args.only or [])}
    for source in registry()['sources']:
        if wanted and source['id'].upper() not in wanted and source['jurisdiction'].upper() not in wanted:
            continue
        entry = log.get(source['id'])
        if not entry or not entry.get('ok'):
            continue
        try:
            snap = snapshot(source, entry)
        except Exception as err:  # noqa: BLE001
            entry.update(ok=False, error=f'normalize: {type(err).__name__}: {err}')
            print(f'FAILED   {source["id"]}: {err}')
            continue
        save_json(SNAPSHOTS / f'{source["id"]}.json', snap)
        print(f'ok       {source["id"]}: kept {snap["kept_rows"]} of {snap["export_rows"]} rows')
    from pipeline.common import save_json as _s
    _s(FETCH_LOG, log)


if __name__ == '__main__':
    main()
