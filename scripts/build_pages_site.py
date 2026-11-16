#!/usr/bin/env python3
"""Assemble what the-reefer.com publishes (this repository's GitHub Pages site).

Owner direction, November 16, 2026: this repository hosts the national cannabis site.

- The national pages (build_national.py) are published at the site root: the home page
  and one page per state and DC, with the-reefer.com as their canonical address.
- The Ohio guide lives at ohioweed.org. Each Ohio page here forwards to its own
  ohioweed.org page, so there is one canonical copy.
- Every other page (the shared state page and the Pennsylvania pages) is published as
  built, with the old weed.vethomeguard.org address replaced by the-reefer.com.
- Data files and assets are served, so download links keep working.

Nothing here changes a committed file; the swap happens only in the published copy.

Usage: python3 scripts/build_pages_site.py [--out _site]
"""
import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OHIO_HOME = 'https://ohioweed.org'
SITE = 'https://the-reefer.com'
OLD_SITE = 'https://weed.vethomeguard.org'
TEXT_SUFFIXES = {'.html', '.json', '.xml', '.txt', '.csv', '.md', '.js'}

# Ohio pages keep their own address at ohioweed.org; each one here forwards to it.
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


def stub(url: str) -> str:
    """A forwarding page. GitHub Pages cannot send a 301, so this is the usable equivalent."""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>This page moved</title>'
        f'<link rel="canonical" href="{url}">'
        f'<meta http-equiv="refresh" content="0; url={url}">'
        '<meta name="robots" content="noindex,follow">'
        '<style>body{font:16px/1.5 system-ui,sans-serif;margin:3rem auto;max-width:34rem;padding:0 1rem;color:#16221e}'
        'a{color:#215b76}</style></head><body>'
        '<h1>This page moved</h1>'
        f'<p>The guide now lives at <a href="{url}">{url}</a>. '
        'You should be sent there automatically.</p></body></html>\n'
    )


def swap_origin(text):
    """Published copies name the-reefer.com wherever the build named the old address."""
    return text.replace(OLD_SITE, SITE).replace(OLD_SITE.split('//')[1], SITE.split('//')[1])


def not_found():
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found | The Reefer</title>'
            '<meta name="robots" content="noindex"><style>body{font:16px/1.5 system-ui,sans-serif;margin:3rem auto;max-width:34rem;padding:0 1rem;color:#16221e}'
            'a{color:#215b76}</style></head><body><h1>Page not found</h1>'
            f'<p>Start from <a href="{SITE}/">the list of all states</a>, or go to the Ohio guide at <a href="{OHIO_HOME}/">OhioWeed.org</a>.</p></body></html>\n')


def build(out):
    import sys
    sys.path.insert(0, str(ROOT))
    import build_national

    out = Path(out).resolve()
    check_forward_list()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT, out, ignore=shutil.ignore_patterns(*SKIP))

    missing = [n for n in FORWARD if not (ROOT / n).exists()]
    if missing:
        raise SystemExit(f'expected these pages in the repo: {missing}')

    # Published text names the-reefer.com, not the retired address.
    for path in out.rglob('*'):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding='utf-8', errors='surrogateescape')
            if OLD_SITE.split('//')[1] in text:
                path.write_text(swap_origin(text), encoding='utf-8', errors='surrogateescape')

    # Ohio pages forward to their own ohioweed.org page.
    for name in FORWARD:
        (out / name).write_text(stub(f'{OHIO_HOME}/{name}'), encoding='utf-8')

    # National pages go to the site root with the-reefer.com as their canonical address.
    previous = build_national.ORIGIN
    build_national.ORIGIN = SITE
    try:
        national = build_national.pages()
    finally:
        build_national.ORIGIN = previous
    clash = sorted(set(national) & (set(FORWARD) | {'404.html'}))
    if clash:
        raise SystemExit(f'national pages would overwrite: {clash}')
    shutil.rmtree(out / 'national', ignore_errors=True)
    (out / 'national').mkdir()
    for name, text in national.items():
        (out / name).write_text(text.replace('href="../', 'href="').replace('src="../', 'src="').replace('srcset="../', 'srcset="'), encoding='utf-8')
        (out / 'national' / name).write_text(stub(f'{SITE}/' + ('' if name == 'index.html' else name)), encoding='utf-8')

    (out / '404.html').write_text(not_found(), encoding='utf-8')
    (out / 'CNAME').write_text(SITE.split('//')[1] + '\n', encoding='utf-8')

    real = sorted(p.name for p in out.glob('*.html') if p.name not in FORWARD and p.name != '404.html')
    urls = [f'{SITE}/' + ('' if n == 'index.html' else n) for n in real]
    (out / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n', encoding='utf-8')
    (out / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
    return {'out': out, 'national': sorted(national), 'forwarded': list(FORWARD), 'real': real}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=ROOT / '_site')
    result = build(ap.parse_args().out)
    print(f'Site ready in {result["out"]}: {len(result["national"])} national pages at the root, '
          f'{len(result["forwarded"])} Ohio pages forwarded to ohioweed.org, '
          f'{len(result["real"]) - len(result["national"])} other pages published as built, plus 404.html and sitemap.xml.')


if __name__ == '__main__':
    main()
