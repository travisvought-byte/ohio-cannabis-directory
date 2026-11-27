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
        world = json.loads((ROOT / 'data/world-permissions.json').read_text(encoding='utf-8'))
        # home, help, about, privacy, medical cards, coverage, partners, jokes, hash myths, Weed Santa, Las Vegas, Denver, Chicago, New York City; plus the world hub, travel warnings, heritage, Cannabis 101 and one page per country
        where = json.loads((ROOT / 'data/world-where-to-buy.json').read_text(encoding='utf-8'))
        store_pages = sum(1 for c in where['countries'].values() if c.get('page'))
        store_pages += len(json.loads((ROOT / 'data/world-starter.json').read_text(encoding='utf-8'))['countries'])  # starter pages
        self.assertEqual(len(PAGES), len(PERM["jurisdictions"]) + 14 + len(PERM["questions"]) + 4 + len(world['countries']) + store_pages)
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

    def test_state_pages_link_their_neighbors(self):
        data = json.loads((ROOT / 'data/state-neighbors.json').read_text(encoding='utf-8'))
        lists = dict(data['borders'])
        lists.update({c: v['states'] for c, v in data['no_land_border'].items()})
        self.assertEqual(set(lists), set(PERM['jurisdictions']))
        names = PERM['jurisdictions']
        for code, name in names.items():
            text = PAGES[build_national.slug(name) + '.html']
            start = text.index('<section aria-labelledby="nearby">')
            section = text[start:text.index('</section>', start)]
            self.assertIn('<h2 id="nearby">', section)
            self.assertIn('href="#nearby"', text, f'{name}: the on-page menu reaches the nearby states')
            want = [build_national.slug(names[c]) + '.html' for c in sorted(lists[code], key=lambda c: names[c])]
            self.assertEqual(re.findall(r'<a class="state" href="([^"]+)">', section), want, name)
            self.assertNotIn(code, lists[code])

    def test_neighbors_match_the_map(self):
        """A border is listed exactly when the two outlines in data/us-map.json (Census Bureau shapes) share a point."""
        import itertools
        borders = json.loads((ROOT / 'data/state-neighbors.json').read_text(encoding='utf-8'))['borders']
        shapes = json.loads((ROOT / 'data/us-map.json').read_text(encoding='utf-8'))['states']
        points = {}
        for s in shapes:
            nums = re.findall(r'-?\d+(?:\.\d+)?', s['d'])
            points[s['code']] = set(zip(nums[0::2], nums[1::2]))
        for a, b in itertools.combinations(sorted(borders), 2):
            self.assertEqual(bool(points[a] & points[b]), b in borders[a], f'{a} and {b}')
            self.assertEqual(b in borders[a], a in borders[b], f'{a} and {b} list each other')

    def test_state_pages_send_visitors_to_topic_pages_that_link_back(self):
        topics = {build_national.law_page_name(q['id']) for q in PERM['questions']} | {'medical.html'}
        for code, name in PERM['jurisdictions'].items():
            page = build_national.slug(name) + '.html'
            text = PAGES[page]
            start = text.index('<aside class="next"')
            aside = text[start:text.index('</aside>', start)]
            linked = [h for h in re.findall(r'href="([^"#]+)"', aside) if h in topics]
            self.assertGreaterEqual(len(linked), 3, name)
            for topic in linked:
                self.assertIn(f'href="{page}', PAGES[topic], f'{topic} links back to {name}')

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

    def test_words_in_the_home_picture_are_never_mirrored(self):
        """The sailor facing left is the other sailor's drawing mirrored, but his "*cough*" must read left to right.
        So a word never sits inside a mirrored group, and never carries a transform of its own: the stylesheet
        animates the word's transform, and that animation replaces the attribute (the cause of the backwards word the
        owner reported on November 17, 2026). tests/picture-browser.cjs checks the same thing as a browser draws it."""
        import xml.etree.ElementTree as ET
        home = PAGES['index.html']
        start = home.index('<svg class="ship"')
        picture = ET.fromstring(home[start:home.index('</svg>', start) + len('</svg>')])
        parent = {child: node for node in picture.iter() for child in node}
        words = [node for node in picture.iter() if node.tag.endswith('}text')]
        self.assertEqual([word.text for word in words], ['*cough*', '*cough*'], 'one cough for each sailor')
        mirrored = 0
        for word in words:
            self.assertNotIn('transform', word.attrib, 'the animation would replace a transform set on the word itself')
            node, figure = word, parent[word]
            while node in parent:
                node = parent[node]
                for factors in re.findall(r'scale\(([^)]*)\)', node.get('transform', '')):
                    self.assertTrue(all(float(f) > 0 for f in re.split(r'[\s,]+', factors.strip())),
                                    f'a word sits inside a flipped group: scale({factors})')
            # The word belongs to one sailor: it shares a group with his figure, and only the figure may be mirrored.
            figures = [g for g in figure if g is not word]
            self.assertEqual(len(figures), 1)
            self.assertEqual(len([g for g in figures[0].iter() if g.get('class') == 'sailor']), 1)
            mirrored += figures[0].get('transform') == 'scale(-1 1)'
        self.assertEqual(mirrored, 1, 'the two sailors face each other: exactly one figure is mirrored')


if __name__ == '__main__':
    unittest.main()
