"""Joke of the day (data/jokes.json): one joke per date, and only owner-approved jokes are published."""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build_national  # noqa: E402

DATA = json.loads((ROOT / 'data/jokes.json').read_text(encoding='utf-8'))


class Jokes(unittest.TestCase):
    def test_one_joke_per_date_with_text_and_a_decision(self):
        dates = [j['date'] for j in DATA['jokes']]
        self.assertEqual(len(dates), len(set(dates)))
        for j in DATA['jokes']:
            self.assertRegex(j['date'], r'^\d{4}-\d{2}-\d{2}$')
            self.assertTrue(j['text'].strip())
            self.assertIsInstance(j['approved'], bool)
            self.assertFalse(set(j) - {'date', 'text', 'approved'})

    def test_unapproved_jokes_are_never_published(self):
        pages = build_national.pages()
        for j in DATA['jokes']:
            if not j['approved']:
                for name in ('index.html', 'jokes.html'):
                    self.assertNotIn(build_national.esc(j['text']), pages[name])
                    self.assertNotIn(j['text'], pages[name])

    def test_approved_jokes_reach_the_home_page_and_the_list(self):
        fake = {'2026-11-18': 'Test joke one.', '2026-11-19': 'Test joke two.'}
        with mock.patch.object(build_national, 'load_jokes', return_value=fake):
            pages = build_national.pages()
        self.assertIn('id="joke" hidden', pages['index.html'])
        self.assertIn('Test joke one.', pages['index.html'])
        self.assertEqual(pages['jokes.html'].count('<li data-date='), 2)
        self.assertIn('hidden><span', pages['jokes.html'])  # future jokes stay hidden until their day

    def test_the_joke_is_told_in_the_picture(self):
        """Owner's direction: the joke is in the home page picture, told by one sailor to the other, and prominent.
        It is a speech bubble laid over the foot of the picture, straight after the drawing, ahead of everything else."""
        fake = {'2026-11-18': 'Test joke one.', '2026-11-19': 'Test joke two.'}
        with mock.patch.object(build_national, 'load_jokes', return_value=fake):
            home = build_national.pages()['index.html']
        self.assertEqual(home.count('id="joke"'), 1)
        self.assertEqual(home.count('id="joke-text"'), 1)
        self.assertIn('</svg><div class="yarn" id="joke" hidden><div class="yarnhead"><h2>Joke of the day</h2>'
                      '<a href="jokes.html">Earlier jokes</a></div><p id="joke-text"></p></div></div></div></div></section>', home)
        self.assertIn('<div class="art"><div class="shipbox"><svg class="ship"', home)
        self.assertNotIn('class="block joke"', home, 'the joke no longer sits in a box of its own down the page')
        self.assertLess(home.index('id="joke"'), home.index('id="tasks"'), 'the joke is met before the list of tasks')
        self.assertLess(home.index('<h1>'), home.index('id="joke"'), 'the page heading still comes first for screen readers')
        self.assertLess(home.index('id="joke"'), home.index('id="jokes-data"'), 'the bubble exists before the script fills it')
        # The bubble is not hidden from screen readers; only the two sailors in the drawing are decoration.
        bubble = home[home.index('<div class="yarn"'):home.index('</section>', home.index('<div class="yarn"'))]
        self.assertNotIn('aria-hidden', bubble)

    def test_no_bubble_without_an_approved_joke(self):
        with mock.patch.object(build_national, 'load_jokes', return_value={}):
            home = build_national.pages()['index.html']
        for part in ('id="joke"', 'class="yarn"', 'jokes-data'):
            self.assertNotIn(part, home)
        self.assertIn('<div class="art"><div class="shipbox"><svg class="ship"', home)

    def test_the_script_sends_and_stores_nothing(self):
        for banned in ('fetch(', 'XMLHttpRequest', 'sendBeacon', 'document.cookie', 'localStorage', 'sessionStorage', 'innerHTML', 'http'):
            self.assertNotIn(banned, build_national.JOKE_SCRIPT, banned)

    def test_a_batch_runs_one_day_after_another(self):
        """The sailors always have something to say: no day inside a batch is without a joke."""
        import datetime
        days = [datetime.date.fromisoformat(j['date']) for j in DATA['jokes']]
        for before, after in zip(days, days[1:]):
            self.assertEqual(after - before, datetime.timedelta(days=1), f'{after} does not follow {before}')


if __name__ == '__main__':
    unittest.main()
