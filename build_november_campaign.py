"""Rebuild the campaign's authored template with current shared site navigation."""
from directory_data import ROOT
from directory_brand import brand_page
from site_visuals import section_heading, with_css

OUT = ROOT / 'november-campaign.html'
# A decorative icon in front of each way a store can help (visuals pass, November 25, 2026); the headings read as before.
OPTION_ICONS = {'Round up': 'calculator', 'Top up': 'tag', 'Store-funded donation': 'store'}


def main():
    page = (ROOT / 'templates/november-campaign.html').read_text()
    for title, name in OPTION_ICONS.items():
        assert page.count(f'<h3>{title}</h3>') == 1, f'the campaign option "{title}" changed; update OPTION_ICONS'
        page = page.replace(f'<h3>{title}</h3>', section_heading(3, title, name))
    OUT.write_text(brand_page(with_css(page), OUT.name))


if __name__ == '__main__':
    main()
