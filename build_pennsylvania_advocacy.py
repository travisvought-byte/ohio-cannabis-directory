"""Build the source-linked Pennsylvania policy pilot with shared site navigation."""
from pathlib import Path
import re
from directory_brand import brand_page
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'pennsylvania-advocacy.html'
def main():
    page = (ROOT / 'templates/pennsylvania-advocacy.html').read_text(encoding='utf-8')
    built = brand_page(page)
    description = re.search(r'<meta name="description" content="([^"]+)"', page).group(1)
    built = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="' + description + '">', built)
    OUT.write_text(built, encoding='utf-8')
    print('Built pennsylvania-advocacy.html')
if __name__ == '__main__':
    main()
