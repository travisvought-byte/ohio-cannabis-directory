"""Visuals stay accessible and add no claim (owner direction, November 24, 2026: visuals and symbols wherever
they help, ADA compliant, the symbols themselves accessible).

- Every inline drawing is either hidden from screen readers (decoration beside words) or a named image.
- Every chart has its numbers as text on the page: the national comparison carries its own table; the
  waiting-period bars sit under the table they redraw and keep that table's wording.
- Every step diagram repeats steps written on the page; it is never the only place a step appears.
"""
import html
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted(ROOT.glob('*.html')) + sorted((ROOT / 'national').glob('*.html'))


def text(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


class InlineDrawings(unittest.TestCase):
    def test_every_svg_is_decoration_or_a_named_image(self):
        for path in PAGES:
            page = path.read_text(encoding='utf-8')
            for tag in re.findall(r'<svg\b[^>]*>', page):
                decorative = 'aria-hidden="true"' in tag
                named = 'role="img"' in tag and re.search(r'aria-label(ledby)?="[^"]+"', tag)
                self.assertTrue(decorative or named, f'{path.name}: {tag[:120]}')
                if decorative:
                    self.assertIn('focusable="false"', tag, f'{path.name}: hidden drawing must not take focus')

    def test_every_role_img_has_a_name(self):
        for path in PAGES:
            for tag in re.findall(r'<[a-z]+\b[^>]*role="img"[^>]*>', path.read_text(encoding='utf-8')):
                self.assertRegex(tag, r'aria-label(ledby)?="[^"]+"', f'{path.name}: {tag[:120]}')


class Charts(unittest.TestCase):
    def test_national_comparison_has_its_numbers_as_text(self):
        page = (ROOT / 'national/index.html').read_text(encoding='utf-8')
        figure = re.search(r'<figure class="spread".*?</figure>', page, re.S).group(0)
        bars = re.findall(r'<span class="bar" role="img" aria-label="([^"]+)">(.*?)</span></li>', figure)
        cells = re.findall(r'<tr><th scope="row">[^<]+</th><td>([^<]+)</td></tr>', figure)
        self.assertTrue(bars)
        self.assertEqual(len(bars), len(cells), 'one table row per bar')
        for (label, segments), cell in zip(bars, cells):
            counts = [int(n) for n in re.findall(r'style="flex:(\d+) 1 0"', segments)]
            self.assertEqual(sum(counts), 51, 'each bar is every state and DC')
            self.assertEqual(html.unescape(label).rsplit(', of ', 1)[0].split(', '), html.unescape(cell).split(' · '))
            self.assertEqual(counts, [int(x.rsplit(' ', 1)[1]) for x in html.unescape(cell).split(' · ')], 'bar and table agree')
        self.assertIn('as of', text(figure))

    def test_waiting_bars_redraw_the_table_above_them(self):
        page = (ROOT / 'expungement.html').read_text(encoding='utf-8')
        start = page.index('<section id="timing">')
        table = page[start:page.index('</table>', start)]
        figure = re.search(r'<figure class="vchart">.*?</figure>', page[start:], re.S).group(0)
        self.assertLess(page.index('</table>', start), page.index('<figure class="vchart">', start), 'the table comes first')
        cells = [text(v) for v in re.findall(r'<td>(.*?)</td>', table)]
        bars = [text(v).split(': ', 1)[1] for v in re.findall(r'<dd><span>(.*?)</span>', figure)]
        self.assertEqual(cells, bars, 'the bars use the table’s own wording, in its order')
        widths = [float(w) for w in re.findall(r'--w:([\d.]+)', figure)]
        self.assertTrue(widths and all(0 < w <= 1 for w in widths) and max(widths) == 1)
        self.assertIn('supremecourt.ohio.gov', figure, 'the chart names the table’s source')
        self.assertIn('Checked', text(figure))


class StepDiagrams(unittest.TestCase):
    def test_every_step_card_repeats_a_step_written_on_the_page(self):
        found = 0
        for path in PAGES:
            page = path.read_text(encoding='utf-8')
            for diagram in re.findall(r'<ol class="vflow".*?</ol>', page, re.S):
                rest = page.replace(diagram, '')
                titles = [text(t) for t in re.findall(r'<span class="vflow-t">(.*?)</span>', diagram)]
                self.assertTrue(titles)
                for title in titles:
                    found += 1
                    self.assertIn(title, text(rest), f'{path.name}: "{title}" appears only in the diagram')
                for href in re.findall(r'href="#([^"]+)"', diagram):
                    self.assertIn(f'id="{href}"', page, f'{path.name}: #{href}')
                self.assertNotIn('<svg', re.sub(r'<svg class="vi"[^>]*aria-hidden="true" focusable="false">', '', diagram))
        self.assertGreaterEqual(found, 9, 'the record-clearing and advocacy steps')

    def test_pages_with_visuals_keep_unique_ids(self):
        for name in ['expungement.html', 'advocacy.html', 'knowledge.html', 'resources.html', 'directory.html',
                     'compare.html', 'national/index.html', 'national/help.html']:
            ids = re.findall(r'\sid="([^"]+)"', (ROOT / name).read_text(encoding='utf-8'))
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            self.assertEqual(dupes, [], name)


if __name__ == '__main__':
    unittest.main()
