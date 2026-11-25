"""Build the source-linked Pennsylvania policy pilot with shared site navigation."""
from pathlib import Path
import re
from directory_brand import brand_page
from site_visuals import step_flow, with_css
# The page's four sections as linked icon cards under its opening (visuals pass, November 25, 2026).
PARTS = [('status', 'Proposals to follow', 'form'), ('map', 'Who can move the issue', 'people'),
         ('questions', 'Useful questions to raise', 'checklist'), ('action', 'Take one practical step', 'send')]
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'pennsylvania-advocacy.html'
def main():
    page = (ROOT / 'templates/pennsylvania-advocacy.html').read_text(encoding='utf-8')
    for hid, title, _ in PARTS:
        assert f'<h2 id="{hid}">{title}</h2>' in page, 'the Pennsylvania sections changed; update PARTS'
    lead = page.index('</p>', page.index('<p class="lead">')) + 4
    page = with_css(page[:lead] + step_flow([(t, i, '#' + h) for h, t, i in PARTS], 'This page in four steps', accent='#a90000') + page[lead:])
    built = brand_page(page, OUT.name)
    description = re.search(r'<meta name="description" content="([^"]+)"', page).group(1)
    built = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="' + description + '">', built)
    OUT.write_text(built, encoding='utf-8')
    print('Built pennsylvania-advocacy.html')
if __name__ == '__main__':
    main()
