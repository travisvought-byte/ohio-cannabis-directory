"""Render the public record in data/on-the-record.json (owner direction, November 24, 2026).

Two built pages share this: lawmakers.html carries the committee testimony next to the scorecard,
and on-the-record.html carries the lobbying reports, the OHCANN profile and members, the Form 990
filings and the record of sources that could not be checked. Each page stays inside the 200 KB
initial-HTML budget.

lawmakers.html is published at ohioweed.org and on-the-record.html at the-reefer.com, so links
between the two are absolute."""
import html
import json
from collections import Counter
from datetime import date
from pathlib import Path

from directory_brand import OHIO_HOME

ROOT = Path(__file__).resolve().parent
RECORD = ROOT / 'data/on-the-record.json'
NATIONAL_HOME = 'https://the-reefer.com'
DETAIL_URL = NATIONAL_HOME + '/on-the-record.html'
LOBBY_URL = NATIONAL_HOME + '/lobbyists.html'
LAWMAKERS_URL = OHIO_HOME + '/lawmakers.html'
DATA_URL = 'https://github.com/travisvought-byte/ohio-cannabis-directory/blob/main/data/on-the-record.json'
POSITIONS = ['Sponsor', 'Proponent', 'Opponent', 'Interested Party']

CSS = ('.otr h3{margin-top:28px}.otr .table-wrap{overflow-x:auto;max-width:100%;border:1px solid #ccc;border-radius:8px;background:white}'
       '.otr table{border-collapse:collapse;width:100%;font-size:.9rem;min-width:640px}.otr th,.otr td{border-bottom:1px solid #e2e2e2;padding:8px 10px;text-align:left;vertical-align:top}'
       '.otr th{background:#f0f0ee;font-weight:650}.otr .counts{font-weight:600}.otr blockquote{margin:6px 0 0;padding-left:10px;border-left:3px solid #ccc}'
       '.otr .bill{background:white;border:1px solid #ccc;border-radius:10px;padding:18px;margin:18px 0}.otr .jump{display:flex;flex-wrap:wrap;gap:6px 16px}'
       '.otr .org990{margin:10px 0}.otr dl{display:grid;grid-template-columns:minmax(0,14rem) minmax(0,1fr);gap:4px 12px;margin:8px 0}.otr dt{font-weight:600}.otr dd{margin:0}'
       '@media(max-width:650px){.otr dl{grid-template-columns:1fr}.otr table{min-width:0}.otr thead{display:none}'
       '.otr tr{display:block;border-bottom:1px solid #ccc;padding:6px 0}.otr td{display:block;border:0;padding:3px 12px}'
       '.otr td[data-label]::before{content:attr(data-label);display:block;font-size:.78rem;font-weight:650;color:#555;text-transform:uppercase;letter-spacing:.03em}}')


def load():
    return json.loads(RECORD.read_text(encoding='utf-8'))


def esc(value):
    return html.escape(str(value), quote=True)


def a(label, url):
    return f'<a href="{esc(url)}">{esc(label)}</a>' if url else esc(label)


def day(iso):
    if len(iso) == 7:
        y, m = iso.split('-')
        return date(int(y), int(m), 1).strftime('%B %Y')
    d = date.fromisoformat(iso)
    return d.strftime('%B ') + str(d.day) + d.strftime(', %Y')


def money(value):
    return 'not reported' if value is None else f'${value:,}'


def yes_no(value):
    return 'not answered' if value is None else ('Yes' if value else 'No')


def name_case(text):
    """Names and titles on IRS returns are often filed in capitals; show them in ordinary case."""
    if not text:
        return ''
    if text.isupper():
        keep = {'OHCANN', 'OGA', 'ACLU', 'US', 'CEO', 'CFO', 'COO', 'PAC', 'III', 'II', 'IV', 'MD', 'LLC'}
        return ' '.join(w if w in keep else w.capitalize() for w in text.split())
    return text


def bill_numbers(data):
    return {b['id']: b['number'] for b in data['bills']}


# ---------------------------------------------------------------- lawmakers.html: testimony

def testimony_table(rows):
    body = []
    for t in rows:
        who = 'Individual testifying for themselves' if t['individual'] else esc(t['witness'])
        org = '—' if t['individual'] else esc(t['organization'])
        words = f'<blockquote>“{esc(t["quote"])}”</blockquote>' if t['quote'] else f'<span class="review">{esc(t["note"])}</span>'
        doc = a('Official testimony', t['document_url']) if t['document_url'] else 'Not posted'
        body.append(f'<tr id="{esc(t["id"])}"><td data-label="Hearing">{esc(day(t["hearing_date"]))}<br><span class="review">{esc(t["chamber"])} {esc(t["committee"])}, {esc(t["hearing"])}</span></td>'
                    f'<td data-label="Witness">{who}</td><td data-label="Testifying for">{org}</td><td data-label="Position">{esc(t["position"])}</td><td data-label="In their own words">{words}</td><td data-label="Record">{doc}</td></tr>')
    return ('<div class="table-wrap"><table><thead><tr><th scope="col">Hearing</th><th scope="col">Witness</th><th scope="col">Testifying for</th>'
            '<th scope="col">Position</th><th scope="col">In their own words</th><th scope="col">Record</th></tr></thead><tbody>'
            + ''.join(body) + '</tbody></table></div>')


def testimony_bill(bill, rows, lob):
    counts = Counter(t['position'] for t in rows)
    count_line = ' · '.join(f'{p}: {counts[p]}' for p in POSITIONS if counts[p])
    return (f'<section class="bill" id="record-{bill["id"]}"><h3>{esc(bill["number"])} — {esc(bill["title"])}</h3>'
            f'<p>{esc(bill["why"])}</p><p class="review">{esc(bill["status"])} '
            f'{a("Bill page", bill["official_page"])} · {a("Committee testimony", bill["committee_page"])} · {a("Status history", bill["status_page"])}</p>'
            f'<details open><summary>Committee testimony: {len(rows)} entries</summary><p class="counts">{esc(count_line)}</p>{testimony_table(rows)}</details>'
            f'<p>{len(lob["employers"])} employers reported lobbying on {esc(bill["number"])}. '
            f'{a("See who lobbied, their registered agents and the reporting periods", LOBBY_URL + "#lobby-" + bill["id"])}.</p></section>')


def lawmakers_section(heading, intro):
    data = load()
    jump = ' '.join(f'<a href="#record-{esc(b["id"])}">{esc(b["number"])} testimony</a>' for b in data['bills'])
    rules = ''.join(f'<li>{esc(r)}</li>' for r in data['rules'])
    bills = ''.join(testimony_bill(b, [t for t in data['testimony'] if t['bill'] == b['id']],
                                   next(l for l in data['lobbying'] if l['bill'] == b['id'])) for b in data['bills'])
    nums = bill_numbers(data)
    positions = ''.join(f'<li><strong>{esc(nums[k])}:</strong> {esc(v)}</li>' for k, v in data['ohcann']['positions'].items())
    return (f'<section class="otr" id="on-the-record"><h2>{esc(heading)}</h2><p>{esc(intro)}</p>'
            f'<nav class="jump" aria-label="On the record">{jump} {a("Who lobbied", LOBBY_URL + "#lobbying")} '
            f'{a("OHCANN profile", DETAIL_URL + "#ohcann")} {a("Form 990 filings", DETAIL_URL + "#form-990")}</nav>'
            f'<details><summary>How this section is built</summary><ul>{rules}</ul><p>{esc(data["testimony_source"])}</p></details>'
            f'<p class="review">Records checked {esc(day(data["as_of"]))}. {a("Download every entry as data", DATA_URL)}.</p>'
            f'{bills}'
            f'<section class="bill" id="ohcann-summary"><h3>Ohio Cannabis Coalition (OHCANN): what the records show</h3><ul>{positions}</ul>'
            f'<p>{a("Full OHCANN profile: former names, members, registered lobbyists, statements and tax filings", DETAIL_URL + "#ohcann")}.</p></section>'
            f'<p class="review">Campaign contributions to each lawmaker are not shown yet: the Ohio Secretary of State’s campaign finance site blocked retrieval on {esc(day(data["as_of"]))}. '
            f'{a("What could not be checked", DETAIL_URL + "#not-checked")}.</p>'
            f'<p><strong>Your turn.</strong> <a href="advocacy.html#write">Write to your own representative and senator</a> in your own words, '
            f'or <a href="#member-search">find them in the roster above</a>.</p></section>')


# ---------------------------------------------------------------- on-the-record.html: detail

def periods(values):
    return ', '.join(values)


def lobbying_table(entry):
    body = ''.join(f'<tr><td data-label="Employer">{esc(e["employer"])}</td><td data-label="Reporting periods">{esc(periods(e["periods"]))}</td>'
                   f'<td data-label="Agents">{esc(", ".join(e["agents"])) if e["agents"] else "Employer report; no agent named"}</td></tr>'
                   for e in entry['employers'])
    return ('<div class="table-wrap"><table><thead><tr><th scope="col">Employer (as registered)</th><th scope="col">Reporting periods</th>'
            '<th scope="col">Registered agents who reported the bill</th></tr></thead><tbody>' + body + '</tbody></table></div>')


def lobbying_section(data):
    parts = []
    for b in data['bills']:
        lob = next(l for l in data['lobbying'] if l['bill'] == b['id'])
        parts.append(f'<section class="bill" id="lobby-{esc(b["id"])}"><h3>{esc(b["number"])} — {esc(b["title"])}</h3>'
                     f'<p>{len(lob["employers"])} employers. Searched {esc(lob["periods_searched"])}. {a("Run this search on JLEC", lob["search_url"])}. '
                     f'{a("Committee testimony on this bill", LAWMAKERS_URL + "#record-" + b["id"])}.</p>'
                     f'<details><summary>Employers, agents and reporting periods</summary>{lobbying_table(lob)}</details></section>')
    return (f'<section id="lobbying"><h2>Who lobbied</h2><p>{esc(data["lobbying_source"])} An activity report shows that an employer, '
            f'through its registered agents, lobbied on a bill in a four-month period. It does not show a position or an amount spent on that bill.</p>'
            + ''.join(parts) + '</section>')


def filing_rows(org):
    out = []
    for f in org['filings']:
        name = esc(f['name_on_return']) + (f' (doing business as {esc(f["doing_business_as"])})' if f['doing_business_as'] else '')
        lines = [('Form', f'{esc(f["form"])}, filed {esc(day(f["filed"]))}' if f['filed'] else esc(f['form'])),
                 ('Name on return', name),
                 ('Total revenue', money(f['total_revenue'])),
                 ('Total expenses', money(f['total_expenses'])),
                 ('Program service revenue', money(f['program_service_revenue'])),
                 ('Membership dues (Part VIII, line 1b)', money(f['membership_dues_part_viii_1b']))]
        if f['form'] != '990-PF':
            lines.append(('Political campaign activity (Part IV, line 3)', yes_no(f['part_iv_line3_political_campaign_activity'])))
        if f['part_iv_line4_lobbying_501c3'] is not None:
            lines.append(('Lobbying, 501(c)(3) (Part IV, line 4)', yes_no(f['part_iv_line4_lobbying_501c3'])))
        if f['part_iv_line5_dues_notice_or_proxy_tax'] is not None:
            lines.append(('Dues notice or proxy tax, 501(c)(4)–(6) (Part IV, line 5)', yes_no(f['part_iv_line5_dues_notice_or_proxy_tax'])))
        c = f['schedule_c']
        if c:
            if c['dues_and_assessments'] is not None:
                lines.append(('Dues and assessments (Schedule C, Part III-B, line 1)', money(c['dues_and_assessments'])))
            if c['nondeductible_lobbying_and_political_total'] is not None:
                lines.append(('Nondeductible lobbying and political expenditures (Schedule C, Part III-B)', money(c['nondeductible_lobbying_and_political_total'])))
            if c['substantially_all_dues_nondeductible']:
                lines.append(('Schedule C, Part III-A', 'States that substantially all dues are nondeductible by members, so no amount is reported'))
            if c['political_expenditures'] is not None:
                lines.append(('Political expenditures (Schedule C, Part I)', money(c['political_expenditures'])))
        if f['lobbying_501c3']:
            lines.append((f['lobbying_501c3']['line'], money(f['lobbying_501c3']['amount'])))
        for p in f['section_527_organizations'] or []:
            lines.append(('Section 527 political organization named (Schedule C)', f'{esc(name_case(p["name"]))}: contributions received and delivered {money(p["contributions_received_and_delivered"])}; paid from own funds {money(p["paid_from_internal_funds"])}'))
        if f['form'] == '990' and not c and not f['lobbying_501c3']:
            lines.append(('Schedule C', 'Not attached to the return'))
        paid = ''.join(f'<li>{esc(name_case(p["name"]))}, {esc(name_case(p["title"]) or "title not given")}: {money(p["reportable_compensation"])}'
                       + (f' (plus {money(p["compensation_from_related_orgs"])} from related organizations)' if p['compensation_from_related_orgs'] else '')
                       + (f' (plus {money(p["other_compensation"])} other)' if p['other_compensation'] else '') + '</li>' for p in f['paid_people'])
        people = (f'<ul>{paid}</ul>' if paid else '<p>No one listed with reportable compensation.</p>') + \
                 f'<p class="review">{f["unpaid_people_listed"]} other officers, directors or trustees listed with no reportable compensation.</p>'
        dl = ''.join(f'<dt>{esc(k)}</dt><dd>{v}</dd>' for k, v in lines)
        out.append(f'<h4>Fiscal year ending {esc(day(f["fiscal_year_end"]))}</h4><dl>{dl}</dl>'
                   f'<p><strong>Officers, directors and key employees with compensation (Part VII)</strong></p>{people}')
    return ''.join(out)


def nonprofit_section(data):
    blocks = []
    for org in data['nonprofit_filings']:
        blocks.append(f'<details class="org990" id="f990-{esc(org["ein"])}"><summary>{esc(org["label"])} · EIN {esc(org["ein"])}</summary>'
                      f'<p class="review">Appears in the testimony as: {esc("; ".join(org["appears_as"]))}. {a("All filings on ProPublica Nonprofit Explorer", org["propublica_url"])}.</p>'
                      f'{filing_rows(org)}</details>')
    missing = ''.join(f'<li>{esc(m["organization"])}{" (EIN " + esc(m["ein"]) + ")" if m["ein"] else ""}: {esc(m["finding"])}</li>' for m in data['no_990_found'])
    return (f'<section id="form-990"><h2>Form 990 filings of the trade and advocacy groups that testified</h2>'
            f'<p>{esc(data["nonprofit_filings_source"])} Companies, governments and hospitals are not included. Amounts, names and titles are as the return '
            f'reports them (some titles are cut short on the return itself); the return is the record.</p>'
            + ''.join(blocks) + f'<details><summary>Groups with no return found</summary><ul>{missing}</ul></details></section>')


def ohcann_section(data):
    o = data['ohcann']
    nums = bill_numbers(data)
    names = ''.join(f'<li>{esc(f["name"])}' + (f': “{esc(f["says"])}”' if f['says'] else '') + f' {a("Source", f["source"])}</li>' for f in o['former_names'])
    w = o['what_it_is']
    staff = ', '.join(f'{esc(n)} ({esc(t)})' for n, t in o['leadership']['staff'])
    board = ', '.join(f'{esc(n)} ({esc(t)}; {esc(c)})' for n, t, c in o['leadership']['board'])
    reg = o['lobbying_registration']
    agents = ', '.join(f'{esc(x["name"])} (' + ', '.join(k for k in ('legislative', 'executive', 'retirement') if x[k]) + ')' for x in reg['current_agents'])
    bills = ''.join(f'<tr><td data-label="Bill">{esc(b["bill"])}</td><td data-label="Reporting periods">{esc(periods(b["periods"]))}</td><td data-label="Agents">{esc(", ".join(b["agents"])) or "Employer report"}</td></tr>' for b in reg['bills_reported'])
    positions = ''.join(f'<li><strong>{esc(nums[k])}:</strong> {esc(v)} {a("Testimony on this bill", LAWMAKERS_URL + "#record-" + k)}</li>' for k, v in o['positions'].items())
    statements = ''.join(f'<li>{esc(day(s["date"]))} · {a(s["title"], s["source"])}' + (f'<blockquote>“{esc(s["quote"])}”</blockquote>' if s['quote'] else '') + '</li>' for s in o['statements'])
    own = ''.join(f'<li>{esc(nums[t["bill"]])}: {esc(t["position"])}, {esc(day(t["hearing_date"]))}. {a("Testimony entry", LAWMAKERS_URL + "#" + t["id"])}</li>'
                  for t in data['testimony'] if t['organization'] and 'OHCANN' in t['organization'])
    return (f'<section id="ohcann"><h2>Profile: Ohio Cannabis Coalition (OHCANN)</h2>'
            f'<p>Built from the same kinds of record as the rest of this page: its own website and statements, its lobbying registration, the committee records and its tax returns. '
            f'Its directory listing keeps record ID {esc(o["directory_record_id"])}.</p>'
            f'<dl><dt>What it says it is</dt><dd>“{esc(w["says"])}” {a("Source", w["source"])}</dd>'
            f'<dt>Tax status</dt><dd>{esc(w["tax_status"])}, EIN {esc(o["ein"])}. <a href="#f990-{esc(o["ein"])}">Its Form 990 filings</a></dd>'
            f'<dt>Mission on its 2024 return, as filed</dt><dd>“{esc(w["mission_on_2024_return"])}”</dd>'
            f'<dt>Membership benefit it lists</dt><dd>“{esc(w["membership_benefits_says"])}” {a("Source", w["membership_benefits_source"])}</dd>'
            f'<dt>Staff on its website</dt><dd>{staff} {a("Source", o["leadership"]["source"])}</dd>'
            f'<dt>Board on its website</dt><dd>{board}</dd></dl>'
            f'<h3>Former and alternate names</h3><ul>{names}</ul>'
            f'<h3>Recorded positions</h3><ul>{positions}</ul><p class="review">Committee testimony filed by OHCANN on these bills:</p><ul>{own}</ul>'
            f'<h3>Its own public statements</h3><ul>{statements}</ul><p class="review">From {a("OHCANN’s news and press page", o["statements_source"])}.</p>'
            f'<h3>Registered lobbyists</h3><p>Current agent on the {a("JLEC employer registration", reg["agents_source"])}: {agents}. {esc(reg["note"])}</p>'
            f'<details><summary>Every bill OHCANN reported lobbying on, January 2023 to now ({len(reg["bills_reported"])} bills)</summary>'
            f'<div class="table-wrap"><table><thead><tr><th scope="col">Bill (as reported)</th><th scope="col">Reporting periods</th><th scope="col">Agents</th></tr></thead><tbody>{bills}</tbody></table></div>'
            f'<p class="review">{a("Run this search on JLEC", reg["bills_reported_source"])}.</p></details>'
            f'<p>{esc(o["federal_lobbying"])}</p><p><a href="#members">Member companies: the membership tracker</a> · {a("Registered lobbyists’ federal contributions", LOBBY_URL + "#lobbyists")}</p></section>')


def member_row(m, data, nums):
    testimony = {t['id']: t for t in data['testimony']}
    tst = []
    for i in m['testimony_ids']:
        t = testimony[i]
        tst.append(f'Testified as {esc(t["position"].lower())} on {esc(nums[t["bill"]])}, {esc(day(t["hearing_date"]))} ({esc(t["chamber"])} {esc(t["committee"])}). '
                   + a('Testimony entry', LAWMAKERS_URL + '#' + i))
    lob = '; '.join(f'{nums[k]} (as {v})' for k, v in m['lobbying_reported_on'].items())
    regs = ''.join(f'<p>{a(r["employer"], r["source"])}: ' + (esc(', '.join(x['name'] for x in r['current_agents'])) or 'no current agent') + '</p>' for r in m['jlec_registrations'])
    directory = (f'{a("Listed", OHIO_HOME + "/directory.html")} as {esc(m["directory_record_name"])} ({esc(m["directory_record_id"])})'
                 if m['directory_record_id'] else 'Not listed')
    status = (f'Left OHCANN on {esc(day(m["left_on"]))}. {a("Source", m["left_source"])}' if m['left_on']
              else f'Listed as OHCANN member (as of {esc(day(m["status_as_of"]))})')
    return (f'<tr><td data-label="Member">{a(m["name"], m["website"])}</td><td data-label="Status">{status}</td><td data-label="In the directory">{directory}</td>'
            f'<td data-label="JLEC registration (current agents)">{regs or "None found"}</td>'
            f'<td data-label="Testimony on SB 56, HB 160, HB 611">{"<br>".join(tst) or "None"}</td>'
            f'<td data-label="Lobbying reported on these bills">{esc(lob) or "None reported"}</td></tr>')


def members_section(data):
    ms = data['ohcann_membership']
    nums = bill_numbers(data)
    head = ('<div class="table-wrap"><table><thead><tr><th scope="col">Member (as shown)</th><th scope="col">Status</th><th scope="col">In the directory</th>'
            '<th scope="col">JLEC registration (current agents)</th><th scope="col">Testimony on SB 56, HB 160, HB 611</th><th scope="col">Lobbying reported on these bills</th></tr></thead><tbody>')
    left = [m for m in data['ohcann_members'] if m['left_on']]
    listed = [m for m in data['ohcann_members'] if not m['left_on']]
    testified = [m for m in listed if m['testimony_ids']]
    def summary(m):
        counts = Counter((next(t['position'] for t in data['testimony'] if t['id'] == i).lower(), nums[i.split('-')[0]]) for i in m['testimony_ids'])
        return ', '.join(f'{esc(p)} on {esc(b)}' + (f' ({n} witnesses)' if n > 1 else '') for (p, b), n in counts.items())
    against = '; '.join(f'{esc(m["name"])}: {summary(m)}' for m in testified)
    snaps = ', '.join(a(day(x['date']), x['url']) for x in ms['wayback_snapshots'])
    left_block = (head + ''.join(member_row(m, data, nums) for m in left) + '</tbody></table></div>') if left else '<p>None recorded. No dated source has been found that says a member company left.</p>'
    return (f'<section id="members"><h2>OHCANN member companies: tracker</h2>'
            f'<p>From {a("OHCANN’s members page", ms["source"])}, retrieved {esc(day(ms["retrieved_on"]))}. Internet Archive snapshots: {snaps}. {esc(ms["wayback_note"])}</p>'
            f'<p>{esc(ms["status_rule"])} {esc(data["ohcann_members_note"])} {esc(ms["directory_note"])}</p>'
            f'<h3>Left OHCANN</h3>{left_block}'
            f'<h3>Listed members ({len(listed)})</h3>'
            + (f'<p>Members whose own testimony is in the committee record on these bills: {against}.</p>' if testified else '')
            + f'<details open><summary>All {len(listed)} listed members</summary>{head}{"".join(member_row(m, data, nums) for m in listed)}</tbody></table></div></details></section>')


def lobbyists_section(data):
    lc = data['lobbyist_contributions']
    rows, pending = [], {}
    for r in lc['agents']:
        if not r['checked_on']:
            pending.setdefault(r['tier'], []).append(r['name'])
            continue
        contrib = ''.join(f'<li>{esc(day(c["date"])) if c["date"] else "date not given"} · {esc(name_case(c["recipient"] or ""))}'
                          + (f' ({esc(c["party"])})' if c['party'] else ' (party not stated)') + f' · ${c["amount"]:,.2f} · ' + a('FEC', c['source']) + '</li>' for c in r['contributions'])
        bio = (f'<p>{esc(r["bio"]["text"])} {a("Source", r["bio"]["source"])}</p>' if r.get('bio') else '')
        summary = f'<p>{esc(r["party_summary"])}.</p>' if r.get('party_summary') else ''
        note = f'<p class="review">{esc(r["note"])}</p>' if r.get('note') else ''
        rows.append(f'<tr><td data-label="Registered agent">{esc(r["name"])}<br><span class="review">{esc(r["tier"])}</span></td>'
                    f'<td data-label="Registered for">{esc("; ".join(r["registered_for"]))}</td>'
                    f'<td data-label="Checked">{esc(day(r["checked_on"]))}</td>'
                    f'<td data-label="Federal contributions">{esc(r["status"].capitalize())}.{summary}' + (f'<ul>{contrib}</ul>' if contrib else '') + f'{note}</td>'
                    f'<td data-label="Own bio">{bio or "Not reviewed yet"}</td></tr>')
    checked = len(rows)
    waiting = ''.join(f'<p><strong>{esc(t)} ({len(n)}):</strong> {esc(", ".join(n))}</p>' for t, n in pending.items())
    return (f'<section id="lobbyists"><h2>Registered lobbyists: federal contributions</h2>'
            f'<p class="counts">In progress, as of {esc(day(lc["as_of"]))}: {checked} of {len(lc["agents"])} registered agents checked.</p>'
            f'<p>{esc(lc["method"])} {esc(lc["order"])} {esc(lc["bios_rule"])}</p>'
            f'<div class="table-wrap"><table><thead><tr><th scope="col">Registered agent</th><th scope="col">Registered for</th><th scope="col">Checked</th>'
            f'<th scope="col">Federal contributions</th><th scope="col">Own bio</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<details><summary>Not yet checked ({len(lc["agents"]) - checked})</summary>{waiting}</details></section>')


def attempts_section(data):
    items = ''.join(f'<li><strong>{esc(x["source"])}</strong> ({esc(day(x["attempted_on"]))}): {esc(x["result"])}' + (f' {a("Source", x["url"])}' if x['url'] else '') + '</li>'
                    for x in data['retrieval_attempts'])
    return (f'<section id="not-checked"><h2>What could not be checked</h2><p>Campaign contributions to each lawmaker, and registered lobbyists’ own contributions and backgrounds, '
            f'are not shown yet. The attempts are recorded here so the gap is visible.</p><ul>{items}</ul></section>')


def detail_body():
    data = load()
    rules = ''.join(f'<li>{esc(r)}</li>' for r in data['rules'])
    return (f'<nav class="jump" aria-label="On this page"><a href="#ohcann">OHCANN profile</a> <a href="#members">Member tracker</a> <a href="#form-990">Form 990 filings</a> '
            f'<a href="#not-checked">What could not be checked</a> {a("Who lobbied and their contributions", LOBBY_URL)} {a("Committee testimony and lawmakers", LAWMAKERS_URL + "#on-the-record")}</nav>'
            f'<details><summary>How this page is built</summary><ul>{rules}</ul></details>'
            f'<p class="review">Records checked {esc(day(data["as_of"]))}. {a("Download every entry as data", DATA_URL)}.</p>'
            f'{ohcann_section(data)}{members_section(data)}{nonprofit_section(data)}{attempts_section(data)}'
            f'<p><strong>Your turn.</strong> {a("Find your own representative and senator and write in your own words", OHIO_HOME + "/advocacy.html#write")}.</p>')


def lobbyists_body():
    data = load()
    rules = ''.join(f'<li>{esc(r)}</li>' for r in data['rules'])
    jump = ' '.join(f'<a href="#lobby-{esc(b["id"])}">{esc(b["number"])}</a>' for b in data['bills'])
    return (f'<nav class="jump" aria-label="On this page">{jump} <a href="#lobbyists">Lobbyists’ federal contributions</a> '
            f'{a("OHCANN profile and member tracker", DETAIL_URL + "#ohcann")} {a("Committee testimony and lawmakers", LAWMAKERS_URL + "#on-the-record")}</nav>'
            f'<details><summary>How this page is built</summary><ul>{rules}</ul></details>'
            f'<p class="review">Records checked {esc(day(data["as_of"]))}. {a("Download every entry as data", DATA_URL)}.</p>'
            f'{lobbying_section(data)}{lobbyists_section(data)}'
            f'<p><strong>Your turn.</strong> {a("Find your own representative and senator and write in your own words", OHIO_HOME + "/advocacy.html#write")}.</p>')
