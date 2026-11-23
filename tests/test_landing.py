"""Every landing page speaks to the person most likely to land there (owner direction, November 23, 2026).

Checks: each national page has its own title, search description, H1 and share tags; state, country and
law pages open with a line written to their visitor, whose links land on the page's own answers; the
home page's "I'm here to..." chooser routes only to pages that exist; and the Ohio and Pennsylvania pages
named in data/landing-pages.json carry their own title, description and opening.
"""
import html
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build_national  # noqa: E402

PAGES = build_national.pages()
LANDING = json.loads((ROOT / 'data/landing-pages.json').read_text(encoding='utf-8'))
PERM = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))
WORLD = json.loads((ROOT / 'data/world-permissions.json').read_text(encoding='utf-8'))
STARTER = json.loads((ROOT / 'data/world-starter.json').read_text(encoding='utf-8'))


def head(text, pattern):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1)) if m else None


def opening(text):
    m = re.search(r'<p class="lede for-you">(.*?)</p>', text, re.S)
    return m.group(1) if m else None


class LandingPages(unittest.TestCase):
    def test_each_page_has_its_own_title_description_h1_and_share_tags(self):
        seen = {'title': {}, 'description': {}, 'h1': {}}
        for name, text in PAGES.items():
            title = head(text, r'<title>(.*?)</title>')
            desc = head(text, r'<meta name="description" content="([^"]*)">')
            h1 = head(text, r'<h1[^>]*>(.*?)</h1>')
            self.assertTrue(title and desc and h1, name)
            self.assertEqual(head(text, r'<meta property="og:description" content="([^"]*)">'), desc, name)
            self.assertTrue(head(text, r'<meta property="og:title" content="([^"]*)">'), name)
            for key, value in (('title', title), ('description', desc), ('h1', h1)):
                self.assertNotIn(value, seen[key], f'{name} repeats the {key} of {seen[key].get(value)}')
                seen[key][value] = name

    def test_state_country_and_law_pages_open_to_their_visitor(self):
        names = [build_national.slug(n) + '.html' for n in PERM['jurisdictions'].values()]
        names += [c['page'] for c in WORLD['countries'].values()] + [c['page'] for c in STARTER['countries'].values()]
        names += [build_national.law_page_name(q['id']) for q in PERM['questions']]
        names += list(LANDING['national_pages'])
        for name in names:
            text = PAGES[name]
            intro = opening(text)
            self.assertTrue(intro, f'{name} has no opening for its visitor')
            self.assertLess(text.index('<h1'), text.index('class="lede for-you"'), name)
            for anchor in re.findall(r'href="#([^"]+)"', intro):
                self.assertIn(f'id="{anchor}"', text, f'{name}: the opening links to #{anchor}, which is not on the page')

    def test_state_openings_quote_the_states_own_answers(self):
        by_state = build_national.answers_by_state(PERM)
        openings = set()
        for code, name in PERM['jurisdictions'].items():
            intro = opening(PAGES[build_national.slug(name) + '.html'])
            for qid, short in re.findall(r'<a href="#q-([a-z-]+)">([^<]+)</a>', intro):
                self.assertEqual(html.unescape(short), by_state[code][qid]['short'].rstrip('.'), f'{name}: {qid}')
            openings.add(re.sub(re.escape(build_national.esc(name)), '', intro))
        # Not one sentence with the state name swapped in: the words follow each state's own answers.
        self.assertGreater(len(openings), len(PERM['jurisdictions']) * 0.8)

    def test_home_chooser_routes_only_to_existing_pages(self):
        home = PAGES['index.html']
        self.assertIn(html.escape(LANDING['home_chooser']['heading'], quote=False), home)
        for it in LANDING['home_chooser']['intents']:
            self.assertIn(f'id="for-{it["id"]}"', home)
            for href in [it['href']] + [h for _, h in it.get('more', [])]:
                self.assertIn(f'href="{html.escape(href, quote=True)}"', home)
                if href.startswith('https://'):
                    continue
                page, _, anchor = href.partition('#')
                if not page:
                    self.assertIn(f'id="{anchor}"', home, href)
                    continue
                if page.startswith('../'):
                    self.assertTrue((ROOT / page[3:]).exists(), href)
                    continue
                self.assertIn(page, PAGES, href)
                if anchor:
                    self.assertIn(f'id="{anchor}"', PAGES[page], href)

    def test_ohio_and_pennsylvania_pages_carry_their_own_lines(self):
        for name, entry in LANDING['ohio_pages'].items():
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertNotIn('__LANDING_INTRO__', text, name)
            if entry.get('title'):
                self.assertIn('<title>' + html.escape(entry['title'], quote=False) + ' | ', text, name)
            if entry.get('description'):
                self.assertIn('<meta name="description" content="' + html.escape(entry['description'], quote=True) + '">', text, name)
            if entry.get('intro'):
                self.assertIn(html.escape(entry['intro'], quote=False), text, name)
            desc = head(text, r'<meta name="description" content="([^"]*)">')
            self.assertEqual(head(text, r'<meta property="og:description" content="([^"]*)">'), desc, name)


if __name__ == '__main__':
    unittest.main()
