"""Build lobbyists.html: the employers and registered agents who reported lobbying on SB 56, HB 160
and HB 611, and the agents' federal contributions (in progress). Canonical data: data/on-the-record.json."""
from pathlib import Path

from directory_brand import brand_page
from site_visuals import with_css
from on_the_record import CSS, lobbyists_body, load, day

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'lobbyists.html'


def main():
    page = (ROOT / 'templates/lobbyists.html').read_text(encoding='utf-8')
    page = (page.replace('__OTR_CSS__', CSS).replace('__BODY__', lobbyists_body())
            .replace('__CHECKED__', day(load()['as_of'])))
    OUT.write_text(brand_page(with_css(page), OUT.name), encoding='utf-8')
    print('Built lobbyists.html: lobbying reports per bill and registered lobbyists’ federal contributions')


if __name__ == '__main__':
    main()
