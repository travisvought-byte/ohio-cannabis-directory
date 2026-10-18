"""Build the source-linked Ohio record relief walkthrough."""
import html
import json
from pathlib import Path
from directory_brand import brand_page
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

def main():
    page = (ROOT / 'templates/expungement.html').read_text(encoding='utf-8')
    OUT.write_text(brand_page(page.replace('__COURT_SEARCHES__', court_searches())), encoding='utf-8')
    print('Built expungement.html')
if __name__ == '__main__':
    main()
