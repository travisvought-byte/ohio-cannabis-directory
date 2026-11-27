"""Visiting Las Vegas: cannabis rules for visitors, national/las-vegas.html on the-reefer.com.

Written for the people in town for MJBizCon (December 1 to 4, 2026) and every other Las Vegas visitor: whether a tourist
can buy, how much, where it can and can't be used (hotels, casinos, cars, federal land), consumption lounges, driving
and flying home. Canonical data: data/las-vegas.json. Every point carries a named official source and the date it was
checked; no business appears except as the Cannabis Compliance Board's own licensee list names it. Built through
build_national.pages(), so it shares the national page shell (navigation, footer and visit counter).
"""
import json
from datetime import date
from pathlib import Path

from city_guides import CSS, MARK, PATHS, render, svg  # noqa: F401  (shared with the other city guides)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/las-vegas.json'
NAME = 'las-vegas.html'
STATE = 'NV'


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def show_box(nat, directory, contest, today=None):
    """During MJBizCon week: the free planner and the Silver Cup. Left out of builds after the show; a small script
    removes it from a page built earlier once the show's last day has passed."""
    event = next((e for e in directory.get('events', []) if e['id'] == nat.MJBIZCON_EVENT_ID), None)
    if not event:
        return ''
    start, end = date.fromisoformat(event['starts_on']), date.fromisoformat(event['ends_on'])
    if (today or date.today()) > end:
        return ''
    esc = nat.esc
    when = f'{start.strftime("%B")} {start.day} to {end.day}' if start.month == end.month else f'{start:%B} {start.day} to {end:%B} {end.day}'
    return (f'<aside class="lv-show" id="mjbizcon-week" data-ends="{end.isoformat()}" aria-labelledby="show-h">'
            f'<h2 id="show-h">{svg("calendar")}During MJBizCon week</h2>'
            f'<p>In town for <strong>{esc(event["name"])}</strong>, <time datetime="{start.isoformat()}">{esc(when)}</time>? '
            'Our free Attendee Planner lists every exhibitor with booth numbers, every session with times and rooms, and after-hours events. '
            f'And the <strong>Silver Cup</strong> runs the same days: the three best captains in our free pirate game win silver half dollars.</p>'
            '<p class="go">'
            f'<a class="cta" href="{esc(contest)}" data-track="las-vegas:silver-cup">See the Silver Cup</a>'
            f'<a href="{esc(nat.MJBIZCON_PLANNER)}/copy" target="_blank" rel="noopener" data-track="las-vegas:planner-copy">Get the free planner</a>'
            f'<a href="{esc(event["next_step_url"])}" target="_blank" rel="noopener" data-track="las-vegas:event">MJBizCon’s own site</a></p>'
            '</aside>'
            '<script>(function(){var b=document.getElementById("mjbizcon-week");if(!b)return;var d=new Date(),'
            't=d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2);'
            'if(t>b.getAttribute("data-ends"))b.remove()})();</script>')


def plain(point):
    return point['text']


# The page's own settings for city_guides.render(); the facts themselves live in data/las-vegas.json.
PAGE = {
    'name': NAME, 'state_name': 'Nevada', 'state_page': 'nevada.html', 'crumb': 'Visiting Las Vegas',
    'h1': 'Visiting Las Vegas? The cannabis rules for visitors',
    'title': 'Visiting Las Vegas: cannabis rules for visitors (2026)',
    'description': ('Can tourists buy weed in Las Vegas? Yes, at 21 with ID. Limits, where you can and can’t use it (hotels, casinos, cars, '
                    'Red Rock, Lake Mead, Hoover Dam), lounges, driving and flying home, from official sources.'),
    'adult': 'For adults 21 and older. Plain summaries of Nevada and federal sources, each linked below. Not legal advice.',
    'prefix': 'lv', 'place': 'the Las Vegas visitor page',
    'more': [('nevada.html', 'The full Nevada guide', ': the state’s law, store list and local help'),
             ('law-public-use.html', 'Public use in every state', ': where you can and can’t use it back home'),
             ('law-driving.html', 'Driving and cannabis in every state', ''),
             ('travel-warnings.html', 'Travel warnings', ': the countries and states where any amount can land you in trouble'),
             ('help.html#travel', 'Flying with cannabis', ': what TSA says')],
    'business_note': 'A business named here is named only because the state’s own list names it.',
}


def mix_table(nat, d):
    """The Cannabis Compliance Board's own chart: flower and other products together, inside the limits section."""
    esc = nat.esc

    def after(s, mark):
        if s['id'] != 'limits':
            return ''
        m = d['mix']
        top = max(r['mg'] for r in m['rows'])
        return (f'<div class="scroll"><table class="lv-mix"><caption>{esc(m["caption"])}{mark(m["source_ids"])}</caption>'
                '<thead><tr><th scope="col">Flower you have</th><th scope="col">THC allowed in other products</th><th scope="col"><span class="lv-sr">Share of the 7,087 mg limit</span></th></tr></thead><tbody>'
                + ''.join(f'<tr><th scope="row">{esc(r["flower"])} <span class="muted">({esc(r["grams"])} g)</span></th>'
                          f'<td class="n">{r["mg"]:,} mg</td><td style="width:40%"><span class="bar" style="width:{round(100 * r["mg"] / top)}%" aria-hidden="true"></span></td></tr>'
                          for r in m['rows'])
                + f'</tbody></table></div><p class="muted">{esc(m["note"])}</p>')
    return after


def page(nat, landing, directory, today=None):
    d = load()
    return render(nat, d, landing['intro'], PAGE, top=show_box(nat, directory, d['event']['contest'], today),
                  after_section=mix_table(nat, d))
