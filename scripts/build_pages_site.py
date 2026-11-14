#!/usr/bin/env python3
"""Assemble what weed.vethomeguard.org publishes.

The repository keeps building every page, because OhioWeed mirrors the Ohio ones and
the test suite checks them. This script decides what the Pennsylvania site actually
serves: Ohio pages become forwards to ohioweed.org, so the same content is not
published on two domains, and the home page becomes Pennsylvania's.

Usage: python3 scripts/build_pages_site.py [--out _site]
"""
import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OHIO_HOME = 'https://ohioweed.org'

# Ohio pages now published at ohioweed.org. directory.html joins them: OhioWeed carries
# the same organizations with its own search, so weed should not serve a second copy.
FORWARD = [
    'advocacy.html', 'ancestry.html', 'assessment.html', 'buyer-guide.html', 'compare.html',
    'directory.html', 'expungement.html', 'intake.html', 'knowledge.html', 'lawmakers.html',
    'locations.html', 'november-campaign.html', 'relationships.html', 'resources.html',
    'seeds.html', 'work-with-travis.html',
]
SKIP = {'.git', '.github', 'node_modules', '__pycache__', '_site', '.pytest_cache'}


def check_forward_list():
    """Fail loudly if this list drifts from the canonical Ohio set in directory_brand."""
    import sys
    sys.path.insert(0, str(ROOT))
    try:
        from directory_brand import OHIO_PAGES
    except (ImportError, AttributeError):
        return  # predates the canonical work; the list below stands on its own
    extra = set(OHIO_PAGES) - set(FORWARD)
    if extra:
        raise SystemExit(f'these Ohio pages are canonical to ohioweed.org but still '
                         f'published here: {sorted(extra)}')


def stub(name: str) -> str:
    """A forwarding page. GitHub Pages cannot send a 301, so this is the usable equivalent."""
    url = f'{OHIO_HOME}/{name}'
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
        f'<p>The Ohio guide now lives at <a href="{url}">{url}</a>. '
        'You should be sent there automatically.</p></body></html>\n'
    )


HOME = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pennsylvania Cannabis Directory and Policy Guide</title>
<meta name="description" content="Source-linked Pennsylvania cannabis resources: a company directory, a policy and advocacy starting point, and a state-by-state resource view.">
<link rel="canonical" href="https://weed.vethomeguard.org/">
<meta property="og:type" content="website">
<meta property="og:title" content="Pennsylvania Cannabis Directory and Policy Guide">
<meta property="og:description" content="Source-linked Pennsylvania cannabis resources: a company directory, a policy and advocacy starting point, and a state-by-state resource view.">
<meta property="og:url" content="https://weed.vethomeguard.org/">
<style>
:root{--ink:#16221e;--teal:#215b76;--line:#cfd6d9;--soft:#f4f6f7}
*{box-sizing:border-box}
body{font:16px/1.6 system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--ink);margin:0;background:#fff}
.wrap{max-width:60rem;margin:0 auto;padding:0 1.25rem}
header{background:var(--teal);color:#fff;padding:3rem 0 2.5rem}
header p{max-width:46ch;color:#dbe8ee;margin:.75rem 0 0}
h1{font-size:clamp(1.9rem,4.5vw,2.7rem);line-height:1.15;margin:0}
h2{margin:0 0 .35rem;font-size:1.15rem;color:var(--teal)}
main{padding:2.5rem 0 3rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem;margin:1.5rem 0 2rem}
.card{border:1px solid var(--line);border-radius:12px;padding:1.1rem;text-decoration:none;color:inherit;display:block}
.card:hover{border-color:var(--teal)}
.card p{margin:0;color:#4b5a5e;font-size:.94rem}
.note{background:var(--soft);border-left:4px solid var(--teal);border-radius:0 10px 10px 0;padding:1rem 1.1rem;margin:0 0 2rem}
footer{border-top:1px solid var(--line);padding:1.5rem 0 2.5rem;color:#5c6a6e;font-size:.9rem}
footer a{color:var(--teal)}
a{min-height:44px}
</style></head><body>
<header><div class="wrap">
<h1>Pennsylvania cannabis resources</h1>
<p>A source-linked directory of Pennsylvania cannabis companies, a policy starting point, and a state-by-state view. Maintained by Travis Vought for Veteran Home Guardians.</p>
</div></header>
<main><div class="wrap">
<div class="note"><strong>The Ohio guide moved.</strong> Ohio businesses, dispensary locations, rules, strains, record clearing and advocacy are now at <a href="https://ohioweed.org/">ohioweed.org</a>. Old Ohio links on this site forward there.</div>
<div class="cards">
<a class="card" href="pennsylvania-directory.html"><h2>Pennsylvania company directory</h2><p>Operators, suppliers and business providers with public contacts, brands and sources.</p></a>
<a class="card" href="pennsylvania-advocacy.html"><h2>Pennsylvania policy and advocacy</h2><p>Understand the policy landscape, find the decision-makers and prepare what you want to say.</p></a>
<a class="card" href="state.html?state=PA"><h2>Resources by state and need</h2><p>Pick a state and a need, then follow the evidence to a next step.</p></a>
<a class="card" href="https://ohioweed.org/"><h2>Ohio guide &#8599;</h2><p>The full Ohio directory, dispensary map, rules and advocacy, now on its own site.</p></a>
</div>
<p>Corrections and additions: <a href="mailto:VeteranHomeGuardians@gmail.com">VeteranHomeGuardians@gmail.com</a></p>
</div></main>
<footer><div class="wrap">
<p>Shared in support of <a href="https://vethomeguard.org/">Veteran Home Guardians</a> &#183;
<a href="https://github.com/travisvought-byte/ohio-cannabis-directory#readme">Methods and sources</a> &#183;
<a href="https://ohioweed.org/">Ohio guide</a></p>
</div></footer></body></html>
'''


def link_direct(text: str) -> str:
    """Point links on the pages that stay straight at ohioweed.org, skipping the forward."""
    def swap(m):
        target = m.group(2)
        path = target.split('#')[0].split('?')[0]
        if path in FORWARD:
            return f'{m.group(1)}="{OHIO_HOME}/{target}"'
        return m.group(0)
    return re.sub(r'(href)="([^"]+)"', swap, text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=ROOT / '_site')
    out = ap.parse_args().out.resolve()
    check_forward_list()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT, out, ignore=shutil.ignore_patterns(*SKIP))

    for name in FORWARD:
        (out / name).write_text(stub(name), encoding='utf-8')
    (out / 'index.html').write_text(HOME, encoding='utf-8')

    kept = [p for p in out.glob('*.html') if p.name not in FORWARD and p.name != 'index.html']
    for p in kept:
        p.write_text(link_direct(p.read_text(encoding='utf-8')), encoding='utf-8')

    missing = [n for n in FORWARD if not (ROOT / n).exists()]
    if missing:
        raise SystemExit(f'expected these pages in the repo: {missing}')
    print(f'Site ready in {out}: {len(FORWARD)} forwards, a Pennsylvania home, '
          f'{len(kept)} pages kept ({", ".join(sorted(p.name for p in kept))})')


if __name__ == '__main__':
    main()
