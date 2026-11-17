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


if __name__ == '__main__':
    unittest.main()
