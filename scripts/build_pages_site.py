#!/usr/bin/env python3
"""Assemble what weed.vethomeguard.org publishes.

The Ohio guide lives at ohioweed.org and the Pennsylvania work is shelved, so this
domain no longer publishes pages of its own. Every page forwards: Ohio pages to their
ohioweed.org counterpart, everything else to the ohioweed.org home. Data files and
assets stay served, so existing download links keep working.

The repository still builds and keeps every page. Nothing here deletes anything, so the
Pennsylvania data is ready to move to its own repository whenever that happens.

Usage: python3 scripts/build_pages_site.py [--out _site]
"""
import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OHIO_HOME = 'https://ohioweed.org'

# Ohio pages keep their own address at ohioweed.org. Anything else, including the
# shelved Pennsylvania pages, forwards to the ohioweed.org home.
FORWARD = [
    'advocacy.html', 'ancestry.html', 'assessment.html', 'buyer-guide.html', 'compare.html',
    'directory.html', 'expungement.html', 'intake.html', 'knowledge.html', 'lawmakers.html',
    'locations.html', 'november-campaign.html', 'relationships.html', 'resources.html',
    'seeds.html', 'work-with-travis.html',
]
SKIP = {'.git', '.github', 'node_modules', '__pycache__', '_site', '.pytest_cache'}


def check_forward_list():
    """Every Ohio page should forward to its own address, not the home. Catch drift."""
    import sys
    sys.path.insert(0, str(ROOT))
    try:
        from directory_brand import OHIO_PAGES
    except (ImportError, AttributeError):
        return  # predates the canonical work; the list below stands on its own
    extra = set(OHIO_PAGES) - set(FORWARD)
    if extra:
        raise SystemExit(f'these Ohio pages would forward to the ohioweed.org home instead '
                         f'of their own page; add them to FORWARD: {sorted(extra)}')


def destination(name: str) -> str:
    """Where this page's readers should end up."""
    return f'{OHIO_HOME}/{name}' if name in FORWARD else f'{OHIO_HOME}/'


def stub(url: str) -> str:
    """A forwarding page. GitHub Pages cannot send a 301, so this is the usable equivalent."""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Moved to OhioWeed</title>'
        f'<link rel="canonical" href="{url}">'
        f'<meta http-equiv="refresh" content="0; url={url}">'
        '<meta name="robots" content="noindex,follow">'
        '<style>body{font:16px/1.5 system-ui,sans-serif;margin:3rem auto;max-width:34rem;padding:0 1rem;color:#16221e}'
        'a{color:#215b76}</style></head><body>'
        '<h1>This page moved</h1>'
        f'<p>The guide now lives at <a href="{url}">{url}</a>. '
        'You should be sent there automatically.</p></body></html>\n'
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=ROOT / '_site')
    out = ap.parse_args().out.resolve()
    check_forward_list()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT, out, ignore=shutil.ignore_patterns(*SKIP))

    missing = [n for n in FORWARD if not (ROOT / n).exists()]
    if missing:
        raise SystemExit(f'expected these pages in the repo: {missing}')

    pages = sorted(p.name for p in out.glob('*.html'))
    for name in pages:
        (out / name).write_text(stub(destination(name)), encoding='utf-8')
    # Catches any address this domain no longer has a page for.
    (out / '404.html').write_text(stub(f'{OHIO_HOME}/'), encoding='utf-8')

    to_ohio = [n for n in pages if n in FORWARD]
    print(f'Site ready in {out}: {len(pages)} pages forwarded '
          f'({len(to_ohio)} to their ohioweed.org page, {len(pages) - len(to_ohio)} to the home), '
          f'plus 404.html. Data files and assets still served.')


if __name__ == '__main__':
    main()
