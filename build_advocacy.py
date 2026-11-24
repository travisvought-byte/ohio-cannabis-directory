"""Build the source-linked Ohio advocacy guide and private letter composer."""
import html
import re
from pathlib import Path
from directory_brand import brand_page
from site_visuals import step_flow, with_css

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'advocacy.html'

STEP_ICONS = ['pin', 'checklist', 'send']


def step_overview(page):
    """The composer's three steps as numbered icon cards under its opening line (owner direction, November 24,
    2026: visuals wherever they help). Titles are read from the composer's own step headings."""
    steps = re.findall(r'<h3>(\d)\. ([^<]+)</h3>', page)
    assert [n for n, _ in steps] == ['1', '2', '3'], 'the composer steps changed; update STEP_ICONS'
    lead = re.search(r'<section id="write" class="composer"><h2>Take action in three steps</h2><p class="muted">[^<]+</p>', page)
    cards = step_flow([(html.unescape(title), name, None) for (_, title), name in zip(steps, STEP_ICONS)],
                      'The three steps at a glance', accent='#a90000')
    return with_css(page[:lead.end()] + cards + page[lead.end():])


def main():
    page = step_overview((ROOT / 'templates/advocacy.html').read_text(encoding='utf-8'))
    built = brand_page(page, OUT.name)
    description = re.search(r'<meta name="description" content="([^"]+)"', page).group(1)
    built = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="' + description + '">', built)
    OUT.write_text(built, encoding='utf-8')
    print('Built advocacy.html: decision-makers, reform priorities and constituent letter')

if __name__ == '__main__':
    main()
