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
        self.assertEqual(len(self.result['national']), 64)
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

    def test_no_published_page_names_the_retired_address(self):
        for path in self.out.rglob('*.html'):
            self.assertNotIn('weed.vethomeguard.org', path.read_text(encoding='utf-8'), path.name)

    def test_local_links_on_national_pages_resolve(self):
        import re
        for name in self.result['national']:
            for href in re.findall(r'href="([^"#:?]+\.html)', self.read(name)):
                self.assertTrue((self.out / href).exists(), f'{name} links to missing {href}')

    def test_committed_files_are_untouched(self):
        self.assertIn('noindex', (ROOT / 'national/index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
