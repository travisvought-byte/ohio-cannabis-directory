"""Build the source-linked Ohio record relief walkthrough."""
from pathlib import Path
from directory_brand import brand_page
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'expungement.html'
def main():
    page = (ROOT / 'templates/expungement.html').read_text(encoding='utf-8')
    OUT.write_text(brand_page(page), encoding='utf-8')
    print('Built expungement.html')
if __name__ == '__main__':
    main()
