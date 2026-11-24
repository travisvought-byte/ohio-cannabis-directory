"""Build the source-linked Ohio record relief walkthrough."""
import html
import json
import re
from pathlib import Path
from directory_brand import brand_page
from site_visuals import duration_bars, step_flow, with_css
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'expungement.html'
def court_searches():
    data = json.loads((ROOT / 'data/record-clearing-courts.json').read_text())
    counties = sorted({c['county'] for c in data['courts']})
    esc = html.escape
    result = '<p>Choose the county where the case happened. Municipal and Common Pleas courts often have separate searches. If unsure, check both.</p>'
    result += '<div id="court-filter" hidden><label for="court-county">County of your case</label><select id="court-county"><option value="">Show all listed counties</option>'
    result += ''.join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in counties)
    result += '</select><p id="court-count" role="status"></p></div><div class="help-grid" id="court-search-results">'
    for court in data['courts']:
        links = ' · '.join(f'<a href="{esc(url, quote=True)}">{esc(label)}</a>' for label,url in court['links'])
        result += f'<article data-county="{esc(court["county"])}"><h3>{esc(court["name"])}</h3><p><strong><a href="{esc(court["search_url"],quote=True)}">Open case search →</a></strong></p><p>{esc(court["instructions"])}</p><p>{links}</p><p class="source">{esc(court["note"])}</p><p class="source">Checked {data["reviewed_on"]} · <a href="{esc(court["source_url"],quote=True)}">Official source</a></p></article>'
    result += '</div><p><strong>Another county or court?</strong> <a href="https://www.supremecourt.ohio.gov/courts/judicial-system/ohio-trial-courts/">Choose your county in Ohio’s official court directory</a>, then open the court’s records search. The direct links above cover selected courts in five counties, not all Ohio courts.</p>'
    result += '<p>Search your current and former names. Check that a result is yours. Save the case number, final charge/subsection, outcome and dates. Download the disposition or judgment if available. Only request documents from the clerk when they are missing or a certified copy is required.</p>'
    result += '<details><summary>Do not remember which courts have your cases?</summary><p><a href="https://www.ohioattorneygeneral.gov/Individuals-and-Families/Consumers/Requesting-Your-Own-Criminal-Records">Request your own Ohio BCI criminal history</a>. This requires identification, consent, fingerprints and a $22 state fee, plus any WebCheck provider fee. It is not an instant public name search and does not replace the court documents.</p></details>'
    return result

# One icon per main step, in order (owner direction, November 24, 2026: visuals wherever they help).
STEP_ICONS = ['search', 'fork', 'form', 'tray', 'gavel', 'order']
STEP = re.compile(r'<li data-step="(\d)"><label><input type="checkbox"><strong>\1\. (.+?)\.</strong>')


def step_overview(page):
    """The six main steps as numbered icon cards above the checklist. Titles are read from the checklist itself,
    so the picture can never say something the steps do not; each card links to its step."""
    steps = STEP.findall(page)
    assert [n for n, _ in steps] == [str(i) for i in range(1, len(STEP_ICONS) + 1)], 'the checklist steps changed; update STEP_ICONS'
    page = STEP.sub(lambda m: m.group(0).replace('<li data-step="', f'<li id="step-{m.group(1)}" data-step="', 1), page)
    cards = step_flow([(html.unescape(title), name, f'#step-{n}') for (n, title), name in zip(steps, STEP_ICONS)],
                      'The six steps at a glance')
    head = '<section id="steps"><h2>What you need to do</h2>'
    assert head in page
    return page.replace(head, head + cards, 1)


def waiting_chart(page):
    """The general-route waiting periods, drawn from the table just above the chart, with that table's source."""
    start = page.index('<section id="timing">')
    end = page.index('</table></div>', start) + len('</table></div>')
    table = page[start:end]
    series = re.findall(r'<th scope="col">([^<]+)</th>', table)[1:]
    rows = [(html.unescape(label), [html.unescape(v) for v in values.split('</td><td>')])
            for label, values in re.findall(r'<tr><th scope="row">([^<]+)</th><td>(.+?)</td></tr>', table)]
    assert series == ['Sealing', 'Expungement'] and len(rows) == 4 and all(len(v) == 2 for _, v in rows), 'the waiting-period table changed'
    source = re.search(r'<p class="source">(<a href="https://www\.supremecourt\.ohio\.gov/[^"]+">[^<]+</a>)</p>', page[end:])
    checked = re.search(r'<p class="eyebrow">OHIO • (Checked [^<]+)</p>', page).group(1)
    note = (f'The waiting periods in the table above, on one scale: the longer the bar, the longer the wait. Source: '
            f'{source.group(1)}. {checked}.')
    chart = duration_bars(rows, series, 'The same waiting periods as bars', note)
    # After the table's own caution and source line, so they stay next to the table.
    after = end + source.end()
    return page[:after] + chart + page[after:]


def main():
    page = (ROOT / 'templates/expungement.html').read_text(encoding='utf-8')
    page = with_css(waiting_chart(step_overview(page.replace('__COURT_SEARCHES__', court_searches()))))
    OUT.write_text(brand_page(page, OUT.name), encoding='utf-8')
    print('Built expungement.html')
if __name__ == '__main__':
    main()
