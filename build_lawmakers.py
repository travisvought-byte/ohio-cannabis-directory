"""Build a lightweight searchable roster with a complete non-JS fallback."""
import html
import json
from pathlib import Path
from directory_brand import brand_page

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'lawmakers.html'

def main():
    data = json.loads((ROOT / 'data/legislators.json').read_text())
    entries = []
    for member in data['members']:
        name = html.escape(member['name'])
        label = f'{member["chamber"]} District {member["district"]} — {name}'
        if member['vacant']:
            entries.append(f'<li>{label} · vacant as of {data["checked_on"]}</li>')
        else:
            phone = (f'<a href="tel:+1{member["phone"].translate(str.maketrans("", "", "() -"))}">{member["phone"]}</a> · '
                     if member['phone'] else '')
            entries.append(f'<li>{label} · {member["party"]} · '
                           f'<a href="{html.escape(member["contact_url"], quote=True)}">Official contact</a> · ' +
                           phone +
                           f'<a href="advocacy.html?member={member["id"]}#write">Write a letter</a></li>')
    page = (ROOT / 'templates/lawmakers.html').read_text().replace('__ROSTER__', ''.join(entries)).replace('__CHECKED__', data['checked_on'])
    OUT.write_text(brand_page(page))
    print('Built lawmakers.html:', len(entries), 'districts with complete fallback')

if __name__ == '__main__':
    main()
