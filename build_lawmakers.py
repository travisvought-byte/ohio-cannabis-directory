"""Build a lightweight searchable roster with a complete non-JS fallback, and the committee
testimony from data/on-the-record.json rendered as plain HTML (on_the_record.py) so it reads
without JavaScript and on every site that mirrors this page."""
import html
import json
from pathlib import Path
from directory_brand import brand_page, landing
from on_the_record import CSS, lawmakers_section

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'lawmakers.html'


def on_the_record():
    text = landing('lawmakers.html')['sections']['on-the-record']
    return lawmakers_section(text['heading'], text['intro'])


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
    page = page.replace('__ON_THE_RECORD__', on_the_record()).replace('__OTR_CSS__', CSS)
    OUT.write_text(brand_page(page, OUT.name))
    print('Built lawmakers.html:', len(entries), 'districts with complete fallback and the on-the-record section')


if __name__ == '__main__':
    main()
