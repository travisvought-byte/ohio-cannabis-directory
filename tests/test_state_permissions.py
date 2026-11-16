import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validate_permissions import validate, evidence_level  # noqa: E402
import permissions_page  # noqa: E402

DATA = json.loads((ROOT / 'data/state-permissions.json').read_text(encoding='utf-8'))


def broken(change):
    data = copy.deepcopy(DATA)
    change(data)
    return data


class StatePermissionsTest(unittest.TestCase):
    def test_repository_data_is_valid(self):
        validate(copy.deepcopy(DATA))

    def test_every_jurisdiction_answers_the_top_questions(self):
        answered = {(a['state'], a['question']) for a in DATA['answers']}
        self.assertEqual(len(DATA['jurisdictions']), 51)
        for code in DATA['jurisdictions']:
            for q in ('adult-use', 'medical'):
                self.assertIn((code, q), answered)

    def test_rejects_stored_not_reviewed_answers(self):
        def change(d): d['answers'][0]['status'] = 'not-reviewed'
        with self.assertRaises(AssertionError):
            validate(broken(change))

    def test_rejects_unknown_status_and_sources(self):
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['answers'][0].update(status='legal')))
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['answers'][0].update(source_ids=['no-such-source'])))
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['answers'][0].update(source_ids=[])))

    def test_rejects_missing_top_level_answer(self):
        def change(d):
            d['answers'] = [a for a in d['answers'] if not (a['state'] == 'WY' and a['question'] == 'medical')]
        with self.assertRaises(AssertionError):
            validate(broken(change))

    def test_rejects_uncited_sources_and_compilation_official_links(self):
        def extra(d):
            d['sources'].append(dict(d['sources'][0], id='unused-source'))
        with self.assertRaises(AssertionError):
            validate(broken(extra))
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['official_links'].update(ID={'source_id': 'natl-disa-map'})))

    def test_medical_not_permitted_needs_an_official_source(self):
        def change(d):
            for a in d['answers']:
                if (a['state'], a['question']) == ('ID', 'medical'):
                    a['source_ids'] = ['natl-disa-map']
        with self.assertRaises(AssertionError):
            validate(broken(change))
        sources = {s['id']: s for s in DATA['sources']}
        for a in DATA['answers']:
            if a['question'] == 'medical' and a['status'] == 'not-permitted':
                self.assertNotEqual(evidence_level(a, sources), 'compilation', a['state'])

    def test_official_links_cover_the_states_reviewed_for_issue_147(self):
        reviewed = ['ID', 'IN', 'IA', 'KS', 'LA', 'MT', 'NE', 'NC', 'ND', 'SC', 'WA', 'WI', 'WY']
        self.assertEqual([c for c in reviewed if c not in DATA['official_links']], [])

    def test_national_audience(self):
        audiences = {i['id']: i.get('audience', 'consumer') for i in DATA['national']}
        self.assertIn('business', audiences.values())
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['national'][0].update(audience='investors')))
        html = permissions_page.render_national(DATA)
        self.assertLess(html.index('data-audience="consumer"'), html.index('id="national-business"'))
        self.assertLess(html.index('id="national-business"'), html.index('data-audience="business"'))

    def test_evidence_levels(self):
        sources = {s['id']: s for s in DATA['sources']}
        levels = {(a['state'], a['question']): evidence_level(a, sources) for a in DATA['answers']}
        self.assertEqual(levels[('OH', 'adult-use')], 'official')
        # The rule itself, independent of which answers happen to rest on which sources today.
        official = next(s['id'] for s in DATA['sources'] if s['kind'] == 'statute')
        compiled = next(s['id'] for s in DATA['sources'] if s['kind'] == 'compilation')
        self.assertEqual(evidence_level({'source_ids': [official]}, sources), 'official')
        self.assertEqual(evidence_level({'source_ids': [compiled]}, sources), 'compilation')
        self.assertEqual(evidence_level({'source_ids': [official, compiled]}, sources), 'mixed')

    def test_every_adult_use_answer_cites_a_state_source(self):
        # Issue #146: no adult-use answer rests on national compilations alone.
        sources = {s['id']: s for s in DATA['sources']}
        for a in DATA['answers']:
            if a['question'] == 'adult-use':
                self.assertNotEqual(evidence_level(a, sources), 'compilation', a['state'])
                self.assertTrue(any(sources[sid]['scope'] == 'state' for sid in a['source_ids']), a['state'])

    def test_adult_use_states_answer_the_detail_questions(self):
        # Issue #148: every adult-use state answers each detail question from official sources.
        detail = ['buying', 'possession', 'sharing', 'home-grow', 'public-use', 'driving']
        sources = {s['id']: s for s in DATA['sources']}
        answers = {(a['state'], a['question']): a for a in DATA['answers']}
        adult = [s for (s, q), a in answers.items() if q == 'adult-use' and a['status'] == 'allowed']
        self.assertGreaterEqual(len(adult), 25)
        for s in adult:
            for q in detail:
                self.assertIn((s, q), answers)
                self.assertEqual(evidence_level(answers[(s, q)], sources), 'official', (s, q))

    def test_work_and_record_questions_word_their_own_statuses(self):
        # Issue #150: "Allowed" and "Not permitted" would read as a verdict on the visitor here.
        questions = {q['id']: q for q in DATA['questions']}
        for qid in ('employment', 'record-relief'):
            self.assertFalse(set(questions[qid]['statuses']) & set(DATA['statuses']), qid)
            self.assertTrue(questions[qid]['note'].strip(), qid)

        def use(status):
            def change(d):
                for a in d['answers']:
                    if (a['state'], a['question']) == ('NY', 'employment'):
                        a['status'] = status
            return change
        validate(broken(use('partly-protected')))
        for bad in ('allowed', 'not-permitted', 'automatic', 'not-reviewed'):
            with self.assertRaisesRegex(AssertionError, 'status must be one of', msg=bad):
                validate(broken(use(bad)))
        # A question on the shared statuses cannot borrow another question's wording.
        self.assertNotIn('statuses', questions[DATA['answers'][0]['question']])
        with self.assertRaises(AssertionError):
            validate(broken(lambda d: d['answers'][0].update(status='protected')))

    def test_question_status_definitions_are_checked(self):
        def q(d, qid):
            return next(x for x in d['questions'] if x['id'] == qid)
        cases = {
            'a shared status cannot be reworded': lambda d: q(d, 'employment')['statuses'].update(
                {'allowed': {'label': 'Allowed', 'tone': 'positive'}}),
            'tone must be one of': lambda d: q(d, 'employment')['statuses']['protected'].update(tone='good'),
            'text is required': lambda d: q(d, 'record-relief')['statuses']['automatic'].update(label=' '),
            'two statuses share a label': lambda d: q(d, 'record-relief')['statuses']['by-application'].update(label='Automatic'),
            'needs at least two': lambda d: q(d, 'record-relief').update(statuses={}),
            'note: text is required': lambda d: q(d, 'record-relief').update(note=''),
            'top-level questions use the shared statuses': lambda d: q(d, 'adult-use').update(
                statuses={'yes': {'label': 'Yes', 'tone': 'positive'}, 'no': {'label': 'No', 'tone': 'negative'}}),
        }
        for message, change in cases.items():
            with self.assertRaisesRegex(AssertionError, message):
                validate(broken(change))

    def test_labels_that_say_the_law_lacks_something_need_an_official_source(self):
        # "Not protected" and "No process" cannot rest on a national list alone.
        compiled = next(s['id'] for s in DATA['sources'] if s['kind'] == 'compilation')

        def rest_on_compilation(state, keep):
            def change(d):
                for a in d['answers']:
                    if (a['state'], a['question']) == (state, 'employment'):
                        moved, a['source_ids'], a['reviewed_on'] = a['source_ids'], [compiled], d['as_of']
                    if (a['state'], a['question']) == (state, 'adult-use'):
                        keeper = a
                if keep:  # keep the statute cited somewhere, so nothing else about the data changes
                    keeper['source_ids'] = keeper['source_ids'] + moved
                    keeper['reviewed_on'] = d['as_of']
            return change
        with self.assertRaisesRegex(AssertionError, 'OH/employment: this answer needs an official source'):
            validate(broken(rest_on_compilation('OH', keep=True)))
        validate(broken(rest_on_compilation('NY', keep=True)))  # "Protected" carries no such claim

    def test_answers_rest_on_official_sources_or_compilations_only(self):
        # The evidence label names those two kinds; an advocacy page or news report cannot carry an answer.
        other = next(s['id'] for s in DATA['sources'] if s['kind'] == 'organization')
        with self.assertRaisesRegex(AssertionError, 'must be one of'):
            validate(broken(lambda d: d['answers'][0]['source_ids'].append(other)))
        kinds = {s['id']: s['kind'] for s in DATA['sources']}
        self.assertEqual({kinds[sid] for a in DATA['answers'] for sid in a['source_ids']} - {'statute', 'regulator', 'government', 'compilation'}, set())

    def test_ohio_pennsylvania_and_new_york_answer_work_and_record_questions(self):
        # Issue #150: migrated from the reviewed rule summaries, each from official sources.
        sources = {s['id']: s for s in DATA['sources']}
        answers = {(a['state'], a['question']): a for a in DATA['answers']}
        for state in ('OH', 'PA', 'NY'):
            for qid in ('employment', 'record-relief'):
                self.assertIn((state, qid), answers)
                self.assertEqual(evidence_level(answers[(state, qid)], sources), 'official', (state, qid))

    def test_work_answers_from_a_national_list_alone_say_so(self):
        # Issue #159: a label taken from a national list names whose list it is and that the state's law is unchecked.
        sources = {s['id']: s for s in DATA['sources']}
        listed = [a for a in DATA['answers'] if a['question'] in ('employment', 'record-relief')
                  and evidence_level(a, sources) == 'compilation']
        for a in listed:
            for sid in a['source_ids']:
                self.assertIn(sources[sid]['publisher'], a['detail'], (a['state'], a['question']))
            self.assertIn('Not yet checked against', a['detail'], (a['state'], a['question']))
            self.assertIn(sources[a['source_ids'][0]]['publisher'], a['citation'], (a['state'], a['question']))

    def test_page_shows_each_question_s_own_labels(self):
        questions = {q['id']: q for q in DATA['questions']}
        answers = {(a['state'], a['question']): a for a in DATA['answers']}
        html = permissions_page.render_permissions(DATA)  # the default state is rendered into the page
        rows = html.split('<article class="perm-row" ')
        for qid in ('employment', 'record-relief'):
            row = next(r for r in rows if r.startswith(f'data-question="{qid}"'))
            own = questions[qid]['statuses'][answers[(permissions_page.HOME, qid)]['status']]
            self.assertIn(f'<span class="chip {own["tone"]}">{own["label"]}</span>', row)
            self.assertNotIn(DATA['statuses']['allowed'], row)
            self.assertNotIn(DATA['statuses']['not-permitted'], row)
            self.assertIn('class="perm-note muted"', row)
        # Unanswered states keep the shared "Not yet reviewed" label; nothing is filled in for them.
        unanswered = next((c for c in DATA['jurisdictions'] if (c, 'employment') not in answers), None)
        if unanswered:
            cell = permissions_page.cell(DATA, unanswered, None, questions['employment'])
            self.assertIn('<span class="chip not-reviewed">Not yet reviewed</span>', cell)
        # The browser gets the labels with the questions, so both renderers word them the same way.
        info = permissions_page.payload(DATA)
        self.assertEqual({q['id']: q.get('statuses') for q in info['questions']},
                         {q['id']: q.get('statuses') for q in DATA['questions']})

    def test_page_payload_cites_listed_sources(self):
        info = permissions_page.payload(DATA)
        count = len(DATA['sources'])
        for answers in info['answers'].values():
            for a in answers.values():
                self.assertTrue(all(1 <= n <= count for n in a['cites']))
        html = permissions_page.render_permissions(DATA)
        self.assertIn('Not yet reviewed', html)
        self.assertEqual(html.count('<option value='), 51 + 52)

    def test_page_lists_the_sources_its_own_text_cites(self):
        # Issue #158: the page carries the sources for the national items and the default state;
        # the switcher adds the rest from the public data, so the page does not grow with every source.
        import re
        static = permissions_page.render_national(DATA) + permissions_page.render_permissions(DATA)
        cited = {int(n) for n in re.findall(r'href="#psource-(\d+)"', static)}
        listed = [int(n) for n in re.findall(r'<li value="(\d+)" id="psource-\1">', permissions_page.render_sources(DATA))]
        self.assertTrue(cited)
        self.assertEqual(set(listed), cited)             # every [sN] in the page resolves, and nothing else is carried
        self.assertEqual(listed, sorted(listed))
        self.assertLess(len(listed), len(DATA['sources']))
        # The browser can add any other source under the same number.
        info = permissions_page.payload(DATA)
        self.assertEqual([s['url'] for s in info['sources']], [s['url'] for s in DATA['sources']])
        self.assertEqual({s['kind'] for s in info['sources']} - set(info['kinds']), set())
        for answers in info['answers'].values():
            for a in answers.values():
                self.assertTrue(all(1 <= n <= len(info['sources']) for n in a['cites']))

    def test_page_does_not_grow_with_another_state_s_sources(self):
        def change(d):
            d['sources'].append(dict(d['sources'][0], id='tx-extra-source', url='https://example.gov/tx', retrieved_on=d['as_of']))
            answer = next(a for a in d['answers'] if a['state'] == 'TX' and a['question'] == 'adult-use')
            answer['source_ids'].append('tx-extra-source')
            answer['reviewed_on'] = d['as_of']
        more = validate(broken(change))
        self.assertNotEqual(permissions_page.HOME, 'TX')
        for render in (permissions_page.render_national, permissions_page.render_permissions,
                       permissions_page.render_glance, permissions_page.render_sources):
            self.assertEqual(render(more), render(DATA), render.__name__)
        self.assertEqual(len(permissions_page.payload(more)['sources']), len(DATA['sources']) + 1)


if __name__ == '__main__':
    unittest.main()
