"""Build the source-linked Ohio advocacy guide and private letter composer."""
from pathlib import Path
from directory_brand import brand_page

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'advocacy.html'

def main():
    page = (ROOT / 'templates/advocacy.html').read_text(encoding='utf-8')
    built = brand_page(page)
    import re
    description = re.search(r'<meta name="description" content="([^"]+)"', page).group(1)
    built = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="' + description + '">', built)
    OUT.write_text(built, encoding='utf-8')
    print('Built advocacy.html: decision-makers, reform priorities and constituent letter')

if __name__ == '__main__':
    main()
