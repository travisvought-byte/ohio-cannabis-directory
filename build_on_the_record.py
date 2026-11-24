"""Build on-the-record.html: who lobbied on SB 56, HB 160 and HB 611, the Ohio Cannabis Coalition's
profile and members, the Form 990 filings of the groups that testified, and the sources that could
not be checked. Canonical data: data/on-the-record.json. Committee testimony is on lawmakers.html."""
from pathlib import Path

from directory_brand import brand_page
from on_the_record import CSS, detail_body, load, day

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'on-the-record.html'


def main():
    page = (ROOT / 'templates/on-the-record.html').read_text(encoding='utf-8')
    page = (page.replace('__OTR_CSS__', CSS).replace('__BODY__', detail_body())
            .replace('__CHECKED__', day(load()['as_of'])))
    OUT.write_text(brand_page(page, OUT.name), encoding='utf-8')
    print('Built on-the-record.html: lobbying reports, OHCANN profile, Form 990 filings and recorded gaps')


if __name__ == '__main__':
    main()
