"""The published site: national pages at the root of the-reefer.com, Ohio pages forwarded."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

import build_pages_site  # noqa: E402


class PagesSiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.result = build_pages_site.build(Path(cls.temp.name) / 'site')
        cls.out = cls.result['out']

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def read(self, name):
        return (self.out / name).read_text(encoding='utf-8')

    def test_home_is_the_national_page_on_the_new_domain(self):
        home = self.read('index.html')
        self.assertIn('<link rel="canonical" href="https://the-reefer.com/">', home)
        self.assertNotIn('noindex', home)
        self.assertIn('href="ohio.html"', home)
        self.assertEqual(self.read('CNAME').strip(), 'the-reefer.com')

    def test_every_state_page_is_at_the_root_and_in_the_sitemap(self):
        sitemap = self.read('sitemap.xml')
        self.assertEqual(len(self.result['national']), 74)  # 69 state-section pages plus the 5 world pages
        for name in self.result['national']:
            self.assertTrue((self.out / name).exists(), name)
            if name != 'index.html':
                self.assertIn(f'https://the-reefer.com/{name}', sitemap)
            self.assertNotIn('href="../', self.read(name))

    def test_ohio_pages_forward_to_ohioweed(self):
        for name in build_pages_site.FORWARD:
            text = self.read(name)
            self.assertIn(f'url=https://ohioweed.org/{name}', text)
            self.assertNotIn(f'https://the-reefer.com/{name}<', self.read('sitemap.xml'))

    def test_other_pages_are_published_as_built(self):
        for name in ('state.html', 'pennsylvania-directory.html'):
            text = self.read(name)
            self.assertNotIn('http-equiv="refresh"', text)
            self.assertIn(f'https://the-reefer.com/{name}', text)

    def test_other_pages_carry_this_sites_name_and_menu(self):
        import re
        for name in ('state.html', 'pennsylvania-directory.html', 'pennsylvania-advocacy.html'):
            text = self.read(name)
            self.assertIn('| The Reefer</title>', text)
            self.assertIn('aria-label="The Reefer home"', text)
            self.assertNotIn('class="vhg-brand"', text)
            self.assertNotIn('knowledge-links site-nav', text)
            block = text[text.index('<div class="reefer-top"'):text.index('</nav></div>')] + text[text.rindex('<footer class="site-footer"'):]
            self.assertIn('<a href="privacy.html">Privacy</a>', block, f'{name} footer links to the privacy page')
            for href in re.findall(r'href="([^"#:?]+\.html)', block):
                self.assertTrue((self.out / href).exists(), f'{name} menu links to missing {href}')

    def test_no_published_page_names_the_retired_address(self):
        for path in self.out.rglob('*.html'):
            self.assertNotIn('weed.vethomeguard.org', path.read_text(encoding='utf-8'), path.name)

    def test_local_links_on_national_pages_resolve(self):
        import re
        for name in self.result['national']:
            for href in re.findall(r'href="([^"#:?]+\.html)', self.read(name)):
                self.assertTrue((self.out / href).exists(), f'{name} links to missing {href}')

    def test_structured_data_matches_the_page(self):
        import json
        import re
        perm = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))
        answered = {}
        for a in perm['answers']:
            answered.setdefault(a['state'], set()).add(a['question'])
        questions = {q['id']: q['question'] for q in perm['questions']}
        for name in self.result['national']:
            text = self.read(name)
            blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
            self.assertEqual(len(blocks), 1, name)
            graph = json.loads(blocks[0])['@graph']
            types = [n['@type'] for n in graph]
            if name == 'index.html':
                self.assertEqual(types, ['WebSite'])
                self.assertEqual(graph[0]['url'], 'https://the-reefer.com/')
                continue
            crumbs = graph[0]
            self.assertEqual(crumbs['@type'], 'BreadcrumbList', name)
            self.assertEqual(crumbs['itemListElement'][-1]['item'], f'https://the-reefer.com/{name}')
        for code, state in perm['jurisdictions'].items():
            name = re.sub(r'[^a-z0-9]+', '-', state.lower()).strip('-') + '.html'
            graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', self.read(name), re.S).group(1))['@graph']
            faq = [n for n in graph if n['@type'] == 'FAQPage']
            asked = {q['name'] for q in faq[0]['mainEntity']} if faq else set()
            # Only questions with a reviewed answer are marked up, each one visible on the page.
            self.assertEqual(asked, {questions[q] for q in answered.get(code, set())}, name)

    def test_committed_files_are_untouched(self):
        self.assertIn('noindex', (ROOT / 'national/index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
