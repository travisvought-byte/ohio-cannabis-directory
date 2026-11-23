"""Run the whole pipeline: fetch -> normalize -> merge -> coverage.

python -m pipeline.run                 every active source
python -m pipeline.run --only MA CO    just these states (or source ids)
python -m pipeline.run --offline       skip downloads; rebuild from what is cached/committed
"""
import argparse

from pipeline import coverage, fetch, merge, normalize


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--offline', action='store_true')
    args = ap.parse_args(argv)
    only = ['--only', *args.only] if args.only else []
    if not args.offline:
        fetch.main(only)
        normalize.main(only)
    merged = merge.build()
    for s in merged['states']:
        print(f'{s["state"]}: {s["counts"]["locations"]} locations ({s["counts"]["duplicates_merged"]} duplicates merged); first rows:')
        for loc in s['locations'][:3]:  # business fields only; safe for public logs
            print('   ', loc)
    data = coverage.build()
    print(f'Coverage: {len(data["source_queue"])} sources queued; thinnest state: {data["states"][0]["name"]}.')


if __name__ == '__main__':
    main()
