#!/usr/bin/env python3
"""Assemble what the-reefer.com publishes (this repository's GitHub Pages site).

Owner direction, November 16, 2026: this repository hosts the national cannabis site.

- The national pages (build_national.py) are published at the site root: the home page
  and one page per state and DC, with the-reefer.com as their canonical address.
- The Ohio guide lives at ohioweed.org. Each Ohio page here forwards to its own
  ohioweed.org page, so there is one canonical copy.
- Every other page (the shared state page and the Pennsylvania pages) is published as
  built, with the old weed.vethomeguard.org address replaced by the-reefer.com and the
  Ohio directory's brand, menu and footer replaced by this site's (rebrand()).
- Data files and assets are served, so download links keep working.

Nothing here changes a committed file; the swap happens only in the published copy.

Usage: python3 scripts/build_pages_site.py [--out _site]
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from directory_brand import more_guides  # noqa: E402  the family's "More free guides" line, shared with every page
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
# Folders with a hand-built page of their own, published as written and listed in the sitemap.
EXTRA_FOLDERS = {'policy-weekend', 'pillage'}
SKIP = {'.git', '.github', 'node_modules', '__pycache__', '_site', '.pytest_cache'}


# Working files that belong in the repository but not on the public site: build and import
# scripts, tests, page templates (half-built copies of real pages), assistant and release
# instructions, and planning notes. They stay readable on GitHub. Only the site root is
# filtered, so documentation that pages link to inside data/ (data/strains/README.md) still serves.
WORKSHOP_DIRS = {'architecture', 'docs', 'research', 'schemas', 'scripts', 'templates', 'tests', 'tools'}
WORKSHOP_FILES = {'requirements.txt', 'package.json', 'package-lock.json', 'CITATION.cff',
                  'RELEASE_UPLOAD_INSTRUCTIONS.txt'}
WORKSHOP_SUFFIXES = {'.py', '.md'}


def remove_workshop_files(out: Path):
    for path in out.iterdir():
        if path.is_dir() and path.name in WORKSHOP_DIRS:
            shutil.rmtree(path)
        elif path.is_file() and (path.name in WORKSHOP_FILES or path.suffix in WORKSHOP_SUFFIXES):
            path.unlink()


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


# Pages published as built (the state portal and the Pennsylvania pages) were made for the Ohio
# directory. On the-reefer.com they carry this site's name, menu and footer instead.
REEFER_TOP = (
    '<div class="reefer-top" style="display:flex;flex-wrap:wrap;align-items:center;gap:.5rem 1.25rem;margin:0 0 1rem;padding:.6rem .9rem;'
    'background:#1d4a37;border-radius:12px">'
    '<a href="index.html" aria-label="The Reefer home" style="display:flex;align-items:center;gap:.6rem;color:#fff;text-decoration:none;font-weight:700;font-size:1.15rem">'
    '<img src="assets/the-reefer/mark-96.png" alt="" width="40" height="40" style="border-radius:8px"><span>The Reefer</span></a>'
    '<nav aria-label="Primary" style="display:flex;flex-wrap:wrap;gap:.25rem 1rem">'
    + ''.join(f'<a href="{href}" style="color:#fff;padding:.55rem 0;min-height:44px;display:inline-flex;align-items:center">{label}</a>' for href, label in (
        ('index.html#map', 'Your state'), ('medical.html', 'Medical cards'), ('index.html#compare', 'Compare laws'), ('help.html', 'Get help'),
        ('pennsylvania.html', 'Pennsylvania law'), ('pennsylvania-directory.html', 'Pennsylvania companies'), ('new-york.html', 'New York law'),
        ('about.html', 'About')))
    + '</nav></div>')
REEFER_FOOT = (
    '<footer class="site-footer"><nav aria-label="More resources">'
    '<a href="index.html">All states</a><a href="medical.html">Medical cards</a><a href="coverage.html">Medicaid and insurance</a><a href="help.html">Get help</a>'
    '<a href="partners.html">Partners</a><a href="privacy.html">Privacy</a><a href="pennsylvania-directory.html">Pennsylvania companies</a><a href="pennsylvania-advocacy.html">Pennsylvania advocacy</a>'
    '<a href="state.html?state=PA">Pennsylvania portal</a><a href="state.html?state=NY">New York portal</a>'
    f'<a href="{OHIO_HOME}/">OhioWeed.org</a><a href="https://mobilitytalk.org/">Mobility Talk</a><a href="https://findbingo.org/">Find Bingo</a></nav>'
    '<p>Created and maintained by <a href="https://travisvought.com/">Travis Vought</a> · Shared in support of '
    '<a href="https://vethomeguard.org/">Veteran Home Guardians</a> · '
    '<a href="https://www.zeffy.com/en-US/donation-form/giving-tuesday-no-veteran-left-isolated">Give to VHG on Giving Tuesday</a></p>'
    + more_guides() + '</footer>')


def rebrand(text):
    """Swap the Ohio directory's brand, menu and footer for this site's on a page published as built."""
    start = text.find('<a class="vhg-brand"')
    nav = text.find('<nav class="knowledge-links site-nav"', start)
    end = text.find('</nav>', nav)
    if min(start, nav, end) < 0:
        raise SystemExit('a page published as built has no Ohio menu to replace; check rebrand()')
    text = text[:start] + REEFER_TOP + text[end + len('</nav>'):]
    foot = text.rfind('<footer class="site-footer"')
    close = text.find('</footer>', foot)
    if min(foot, close) < 0:
        raise SystemExit('a page published as built has no site footer to replace; check rebrand()')
    text = text[:foot] + REEFER_FOOT + text[close + len('</footer>'):]
    return (text.replace(' | Ohio Cannabis Directory</title>', ' | The Reefer</title>')
            .replace(' | Ohio Cannabis Directory">', ' | The Reefer">')
            .replace('property="og:site_name" content="Ohio Cannabis Directory"', 'property="og:site_name" content="The Reefer"'))


# The page GitHub Pages serves for any missing address (owner direction, November 28, 2026: make it look like the
# rest of The Reefer). It uses the national pages' own shell (head, logo, menu, footer, skip link), so it keeps up
# with them. GitHub Pages serves it at whatever path was asked for, so every link and asset is root-relative.
NOT_FOUND_LINKS = [
    ('/#map', 'pin', 'Pick your state', 'The law, medical cards and stores, state by state.'),
    ('/medical.html', 'card', 'Medical cards', 'Who qualifies, the cost and how to apply.'),
    ('/#compare', 'scale', 'Compare laws', 'Line states up side by side on one question.'),
    ('/world.html', 'globe', 'World', 'What the law says in other countries.'),
    (f'{OHIO_HOME}/', 'leaf', 'The Ohio guide', 'OhioWeed.org: stores, laws and help in Ohio.'),
]
NOT_FOUND_CSS = ('.lost{max-width:760px;margin:0 auto;padding:18px 0 8px;text-align:center}'
                 '.lost .flag{display:inline-grid;place-items:center;width:84px;height:84px;border-radius:50%;background:var(--mint);color:var(--green);margin:8px 0 0}'
                 '.lost .flag svg{width:46px;height:46px}.lost p{font-size:1.1rem;color:var(--soft);margin:.2em auto 1em;max-width:40ch}'
                 '.tasks.lost-links{margin-top:18px}.lost-links .task{min-height:44px}'
                 '.lost-links .task:focus-visible{outline:3px solid var(--link);outline-offset:2px}'
                 '.lost-home{margin:22px 0 0;text-align:center}.lost-home a{display:inline-flex;align-items:center;min-height:44px;padding:0 6px;font-weight:700}'
                 '@media(prefers-color-scheme:dark){.lost .flag{color:#a8dfbd}}')
_RELATIVE = re.compile(r'\b(href|src|srcset)="(?!https?:|/|#|mailto:|tel:|data:)')


def not_found():
    import sys
    sys.path.insert(0, str(ROOT))
    import build_national as bn

    cards = ''.join(f'<a class="task" href="{href}"><span class="ic">{bn.icon(ic)}</span><strong>{label}</strong>'
                    f'<span class="d">{text}</span></a>' for href, ic, label, text in NOT_FOUND_LINKS)
    body = ('<section class="lost" aria-labelledby="lost-title"><span class="flag">' + bn.icon('warning') + '</span>'
            '<h1 id="lost-title">That page washed overboard.</h1>'
            '<p>The link may be old or mistyped. These will get you back on course.</p></section>'
            '<nav aria-label="Places to go from here"><div class="tasks lost-links">' + cards + '</div></nav>'
            '<p class="lost-home"><a href="/">Go to the home page</a></p>')
    previous = bn.ORIGIN
    bn.ORIGIN = ''  # no canonical address; the shell then marks the page noindex
    try:
        page = bn.shell('Page not found', 'This page could not be found on The Reefer.', body, '404.html',
                        'a missing page', css=NOT_FOUND_CSS)
    finally:
        bn.ORIGIN = previous
    page = page.replace('="../', '="/')
    page = _RELATIVE.sub(lambda m: f'{m.group(1)}="/', page)
    if 'noindex' not in page:
        raise SystemExit('the 404 page lost its noindex tag; check not_found()')
    return page


# A page's last-modified date in the sitemap is the newest date the page itself says a fact was checked
# ("checked November 20, 2026", "retrieved ...", "reviewed ...", "updated ...", "as of ..."). That comes from the
# data's own review dates, not the day the site was built. A page that shows no such date gets no lastmod, and a
# date after today (a data mistake) is never used.
CHECKED_DATE = re.compile(r'\b(?:checked|retrieved|reviewed|updated|as of)\b[^<\d]{0,24}?'
                          r'(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (20\d\d)',
                          re.I)
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']


def page_lastmod(text, today=None):
    from datetime import date
    today = today or date.today()
    visible = re.sub(r'<(script|style)\b.*?</\1>', ' ', text, flags=re.S | re.I)
    found = []
    for month, day, year in CHECKED_DATE.findall(visible):
        try:
            d = date(int(year), MONTHS.index(month.lower()) + 1, int(day))
        except ValueError:
            continue
        if d <= today:
            found.append(d)
    return max(found).isoformat() if found else None


def sitemap_entry(url, page):
    lastmod = page_lastmod(page.read_text(encoding='utf-8')) if page.is_file() else None
    return f'  <url><loc>{url}</loc>' + (f'<lastmod>{lastmod}</lastmod>' if lastmod else '') + '</url>\n'


def build(out):
    import sys
    sys.path.insert(0, str(ROOT))
    import build_national

    out = Path(out).resolve()
    check_forward_list()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT, out, ignore=shutil.ignore_patterns(*SKIP))
    remove_workshop_files(out)

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

    # Whatever is left at the root was built for the Ohio directory: give it this site's name and menu.
    for path in out.glob('*.html'):
        if path.name not in FORWARD and path.name not in national and not (path.name.startswith('google') and len(path.name) == 27):
            path.write_text(rebrand(path.read_text(encoding='utf-8')), encoding='utf-8')

    (out / '404.html').write_text(not_found(), encoding='utf-8')
    (out / 'CNAME').write_text(SITE.split('//')[1] + '\n', encoding='utf-8')

    # Google Search Console ownership file (google<token>.html): published, never listed as a page.
    real = sorted(p.name for p in out.glob('*.html') if p.name not in FORWARD and p.name != '404.html'
                  and not (p.name.startswith('google') and len(p.name) == 27))
    urls = [(f'{SITE}/' + ('' if n == 'index.html' else n), out / n) for n in real]
    # Stand-alone pages that live in their own folder (an event page) are listed too.
    urls += [(f'{SITE}/{p.parent.name}/', p) for p in sorted(out.glob('*/index.html')) if p.parent.name in EXTRA_FOLDERS]
    # And their other pages, like the game's contest page and its rules.
    urls += [(f'{SITE}/{p.parent.name}/{p.name}', p) for p in sorted(out.glob('*/*.html')) if p.parent.name in EXTRA_FOLDERS and p.name != 'index.html']
    (out / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(sitemap_entry(u, p) for u, p in urls) + '</urlset>\n', encoding='utf-8')
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
