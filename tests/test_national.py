"""The national section is generated from canonical data and adds no claim of its own."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_national  # noqa: E402

PERM = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))
SCORE = json.loads((ROOT / 'data/state-scorecard.json').read_text(encoding='utf-8'))
PAGES = build_national.pages()


class NationalPagesTest(unittest.TestCase):
    def test_committed_pages_match_the_build(self):
        committed = {p.name for p in (ROOT / 'national').glob('*.html')}
        self.assertEqual(committed, set(PAGES), 'national/ requires rebuild (python build_national.py)')
        for name, text in PAGES.items():
            self.assertEqual((ROOT / 'national' / name).read_text(encoding='utf-8'), text,
                             f'national/{name} requires rebuild (python build_national.py)')

    def test_one_page_per_jurisdiction_linked_from_home(self):
        self.assertEqual(len(PAGES), len(PERM['jurisdictions']) + 6 + len(PERM['questions']))  # home, help, about, medical cards, coverage, partners
        for name in PERM['jurisdictions'].values():
            page = build_national.slug(name) + '.html'
            self.assertIn(page, PAGES)
            self.assertIn(f'href="{page}"', PAGES['index.html'])

    def test_every_answer_is_shown_with_its_review_date_and_no_more(self):
        by_state = build_national.answers_by_state(PERM)
        for code, name in PERM['jurisdictions'].items():
            text = PAGES[build_national.slug(name) + '.html']
            shown = len(re.findall(r'data-question="', text))
            self.assertEqual(shown, len(PERM['questions']))
            self.assertEqual(text.count('No reviewed source yet'), len(PERM['questions']) - len(by_state[code]))
            for answer in by_state[code].values():
                self.assertIn(build_national.esc(answer['short']), text)
                self.assertIn('checked ' + build_national.long_date(answer['reviewed_on']), text)

    def test_portal_pages_cover_every_question_and_need(self):
        home = PAGES['index.html']
        for q in PERM['questions']:
            name = build_national.law_page_name(q['id'])
            self.assertIn(f'href="{name}"', home)
            page = PAGES[name]
            self.assertEqual(len(re.findall(r'<li data-state="', page)), len(PERM['jurisdictions']))
            answered = sum(a['question'] == q['id'] for a in PERM['answers'])
            self.assertEqual(page.count('data-status="not-reviewed"'), len(PERM['jurisdictions']) - answered)
        for item in PERM['national']:
            self.assertIn(f'data-national="{item["id"]}"', PAGES['help.html'])
            self.assertIn(f'href="help.html#{build_national.slug(item["need"])}"', home)
            self.assertIn(f'id="{build_national.slug(item["need"])}"', PAGES['help.html'])
        self.assertIn('href="about.html"', home)

    def test_cited_sources_are_listed_on_the_page(self):
        for name, text in PAGES.items():
            cited = {int(n) for n in re.findall(r'href="#source-(\d+)"', text)}
            listed = {int(n) for n in re.findall(r'id="source-(\d+)"', text)}
            self.assertEqual(cited, listed, name)

    def test_pathway_levels_come_only_from_the_scorecard(self):
        for code, name in PERM['jurisdictions'].items():
            text = PAGES[build_national.slug(name) + '.html']
            self.assertEqual(len(re.findall(r'data-pathway="', text)), 7)
            card = SCORE['states'].get(code)
            if card:
                self.assertNotIn('Not started', text)
                for row in card['pathways'].values():
                    self.assertIn(f'chip {row["level"]}', text)
            else:
                self.assertEqual(text.count('<span class="chip not-started">'), 7)

    def test_local_links_resolve(self):
        for name, text in PAGES.items():
            for href in re.findall(r'href="([^"#:]+\.html)[^"]*"', text):
                target = PAGES if '/' not in href else None
                if target is not None:
                    self.assertIn(href, PAGES, f'{name} links to missing {href}')
                else:
                    self.assertTrue((ROOT / 'national' / href.split('?')[0]).resolve().exists(), f'{name}: {href}')

    def test_no_canonical_until_the_domain_is_set(self):
        if not build_national.ORIGIN:
            for text in PAGES.values():
                self.assertNotIn('rel="canonical"', text)
                self.assertIn('noindex', text)

    def test_build_writes_to_a_chosen_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            build_national.main(temp)
            self.assertEqual({p.name for p in Path(temp).glob('*.html')}, set(PAGES))


if __name__ == '__main__':
    unittest.main()
