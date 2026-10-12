"""Build the source-linked Ohio advocacy guide and private letter composer."""
from pathlib import Path
from directory_brand import brand_page

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'advocacy.html'

def main():
    page = (ROOT / 'templates/advocacy.html').read_text(encoding='utf-8')
    OUT.write_text(brand_page(page), encoding='utf-8')
    print('Built advocacy.html: decision-makers, reform priorities and constituent letter')

if __name__ == '__main__':
    main()
