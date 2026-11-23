"""Print each downloaded source's column names, row count and the values in its license
type and status columns, to write or fix a registry mapping. Prints no row contents beyond
those category counts, because Actions logs are public and some lists name people.

Run: python -m pipeline.probe [--only ID_OR_STATE ...]
"""
import argparse
from collections import Counter

from pipeline.common import FETCH_LOG, clean, load_json, registry
from pipeline.normalize import column, read_raw

CATEGORY_HINTS = ('type', 'status', 'class', 'category', 'activity', 'purpose', 'designation', 'kind', 'endorsement')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args(argv)
    log = load_json(FETCH_LOG, {})
    wanted = {o.upper() for o in (args.only or [])}
    for s in registry()['sources']:
        if wanted and s['id'].upper() not in wanted and s['jurisdiction'].upper() not in wanted:
            continue
        if s['fetch']['method'] == 'manual' or s['id'] not in log:
            continue
        try:
            rows = read_raw(s)
        except Exception as err:  # noqa: BLE001
            print(f'== {s["id"]}: cannot read ({err})')
            continue
        cols = list(rows[0]) if rows else []
        print(f'== {s["id"]}: {len(rows)} rows; columns: {cols}')
        for c in cols:
            if any(h in str(c).lower() for h in CATEGORY_HINTS):
                print(f'   {c}: {dict(Counter(clean(column(r, c)) or "(blank)" for r in rows).most_common(15))}')


if __name__ == '__main__':
    main()
