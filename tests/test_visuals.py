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
                # The US map is a named group of links, one per state (keyboard and screen reader reachable).
                named = named or ('role="group"' in tag and re.search(r'aria-label="[^"]+"', tag))
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


# Visuals pass (owner direction, November 25, 2026: "add some reasonable visuals everywhere, at least for the US side").
NATIONAL = ROOT / 'national'
US_PAGES = [p for p in sorted(NATIONAL.glob('*.html')) if not p.name.startswith('world') and p.name != 'jokes.html']
VISUAL = re.compile(r'<svg\b|class="(usmap|lmap|vsteps|tline|spread[^"]*|stats|vstats|vflow|vchart)"')


class EveryUsPage(unittest.TestCase):
    def test_every_us_page_has_a_visual(self):
        for path in US_PAGES:
            self.assertRegex(path.read_text(encoding='utf-8'), VISUAL, path.name)
        for name in ('advocacy', 'expungement', 'resources', 'knowledge', 'directory', 'buyer-guide', 'assessment', 'lawmakers', 'seeds',
                     'on-the-record', 'lobbyists', 'relationships', 'pennsylvania-advocacy', 'pennsylvania-directory', 'november-campaign', 'ancestry'):
            self.assertRegex((ROOT / f'{name}.html').read_text(encoding='utf-8'), VISUAL, name)


class StatePageVisuals(unittest.TestCase):
    import json as _json
    PERM = _json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))
    MED = {p['state']: p for p in _json.loads((ROOT / 'data/medical-programs.json').read_text(encoding='utf-8'))['states']}

    def page(self, code):
        name = re.sub(r'[^a-z0-9]+', '-', self.PERM['jurisdictions'][code].lower()).strip('-')
        return (NATIONAL / f'{name}.html').read_text(encoding='utf-8')

    def test_locator_marks_one_state_and_says_it_in_words(self):
        for code in self.PERM['jurisdictions']:
            page = self.page(code)
            fig = re.search(r'<figure class="locator">(.*?)</figure>', page, re.S)
            self.assertTrue(fig, code)
            self.assertEqual(fig.group(1).count('class="here '), 1, code)
            self.assertRegex(fig.group(1), r'<div class="lmap" role="img" aria-label="Map: [^"]+ for adult use">')
            self.assertIn('Adult use: <span class="chip', fig.group(1), 'the caption gives the answer in words')

    def test_medical_steps_are_the_states_own_words_in_order(self):
        for code, prog in self.MED.items():
            if not prog.get('steps'):
                continue
            steps = re.search(r'<ol class="steps vsteps" role="list">(.*?)</ol>', self.page(code), re.S).group(1)
            self.assertEqual([text(x) for x in re.findall(r'<span class="stt">(.*?)</span>', steps)], prog['steps']['items'], code)
            self.assertNotIn('<svg', re.sub(r'<svg viewBox="0 0 24 24"[^>]*aria-hidden="true" focusable="false">', '', steps.replace('<span class="sti" aria-hidden="true">', '')))

    def test_timeline_dates_come_from_the_answers(self):
        for code in self.PERM['jurisdictions']:
            page = self.page(code)
            dates = sorted({a['effective_on'] for a in self.PERM['answers'] if a['state'] == code and a['effective_on']})
            fig = re.search(r'<figure class="tline".*?</figure>', page, re.S)
            if not dates:
                self.assertIsNone(fig, code)
                continue
            self.assertEqual(re.findall(r'<time datetime="([^"]+)">', fig.group(0)), dates, code)
            for href in re.findall(r'href="#([^"]+)"', fig.group(0)):
                self.assertIn(f'id="{href}"', page, code)


if __name__ == '__main__':
    unittest.main()
