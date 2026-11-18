"""Every page a visitor reads carries the suicide and homelessness help block.

Owner direction, November 17, 2026: this help goes on every page of every site.
The block comes from directory_brand.help_now(); these checks keep it from
dropping off a page, appearing twice, or losing one of its phone links.
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from directory_brand import help_now  # noqa: E402


def built_pages():
    """Committed pages a visitor can open: not templates, not the search-engine ownership file."""
    listed = subprocess.run(['git', 'ls-files', '*.html'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    return sorted(name for name in listed
                  if not name.startswith('templates/')
                  and not (name.startswith('google') and len(name) == 27))


class HelpNowTest(unittest.TestCase):
    def test_block_names_each_line_once_with_a_working_link(self):
        block = help_now()
        for link in ('href="tel:988"', 'href="sms:988"', 'href="tel:211"',
                     'href="https://www.hud.gov/findshelter"', 'href="tel:+18774243838"'):
            self.assertEqual(block.count(link), 1, link)
        for words in ('Thinking about suicide', 'press 1', 'No safe place to sleep tonight',
                      'press 6 for homeless services', '1-877-424-3838'):
            self.assertIn(words, block)
        self.assertTrue(block.startswith('<aside class="help-now" aria-label="Need help now?"'))

    def test_every_built_page_carries_the_block_once(self):
        block = help_now()
        pages = built_pages()
        self.assertGreater(len(pages), 80)
        for name in pages:
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertEqual(text.count(block), 1, f'{name} should carry the help block exactly once')
            self.assertEqual(text.count('class="help-now"'), 1, name)

    def test_the_block_sits_just_above_the_footer(self):
        block = help_now()
        for name in built_pages():
            text = (ROOT / name).read_text(encoding='utf-8')
            after = text[text.index(block) + len(block):]
            self.assertTrue(after.startswith('<footer'), f'{name}: the help block should sit directly above the footer')


if __name__ == '__main__':
    unittest.main()
