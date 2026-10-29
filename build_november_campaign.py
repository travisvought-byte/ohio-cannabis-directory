"""Rebuild the campaign's authored template with current shared site navigation."""
from directory_data import ROOT
from directory_brand import brand_page

OUT = ROOT / 'november-campaign.html'


def main():
    OUT.write_text(brand_page((ROOT / 'templates/november-campaign.html').read_text()))


if __name__ == '__main__':
    main()
