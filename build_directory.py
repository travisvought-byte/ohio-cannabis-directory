#!/usr/bin/env python3
"""Build a self-contained, searchable HTML page from the Ohio Cannabis
Ecosystem Directory master workbook.

No external network dependencies at runtime: data, styles and script are
all inlined so the page works on bad conference wifi or fully offline.
"""
import json
import html
import datetime
import pandas as pd

SRC = "/mnt/user-data/uploads/Ohio_Cannabis_Ecosystem_Directory_v67_Master.xlsx"
OUT = "/mnt/user-data/outputs/ohio-cannabis-directory.html"

OUT_OF_SCOPE = "Out of scope — flagged for removal or separate list"

COLS = {
    "Category": "cat",
    "Organization / Business Name": "org",
    "Type": "type",
    "Contact Person": "person",
    "Email": "email",
    "Phone": "phone",
    "Website": "web",
    "Source(s)": "src",
    "Service Area": "area",
    "Notes": "notes",
    "Seed Source": "seed",
    "Verification Tier": "tier",
    "Capabilities / Keywords": "keys",
}


def clean(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def main():
    df = pd.read_excel(SRC, sheet_name="Directory", header=3).dropna(how="all")

    records = []
    for _, row in df.iterrows():
        rec = {short: clean(row.get(col)) for col, short in COLS.items()}
        rec["scope"] = 0 if rec["cat"] == OUT_OF_SCOPE else 1
        # precomputed lowercase haystack keeps filtering fast on phones
        rec["_s"] = " ".join([
            rec["org"], rec["cat"], rec["keys"], rec["area"],
            rec["person"], rec["notes"], rec["type"],
        ]).lower()
        records.append(rec)

    records.sort(key=lambda r: r["org"].lower())

    cats = sorted({r["cat"] for r in records if r["scope"]})
    types = sorted({r["type"] for r in records if r["scope"]})
    n_pub = sum(r["scope"] for r in records)
    n_scope = len(records) - n_pub
    today = datetime.date.today()
    built = today.strftime("%B %-d, %Y")
    built_iso = today.isoformat()

    payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"))

    cat_opts = "\n".join(
        f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in cats
    )
    type_opts = "\n".join(
        f'<option value="{html.escape(t)}">{html.escape(t)}</option>' for t in types
    )

    # A complete text index keeps the directory useful to search engines,
    # archival tools, and visitors browsing without JavaScript.
    noscript = [
        '<div class="wrap" style="padding:1.5rem 1.1rem">',
        "<h2>Full directory index</h2>",
        (
            f"<p>All {n_pub} publishable organizations, listed for browsers "
            "and crawlers without JavaScript. Use the search above for "
            "capability, contact and provenance detail.</p>"
        ),
    ]
    for cat in cats:
        cat_records = [r for r in records if r["scope"] and r["cat"] == cat]
        noscript.append(f"<h3>{html.escape(cat)} ({len(cat_records)})</h3>")
        noscript.append("<ul>")
        for rec in cat_records:
            org = html.escape(rec["org"])
            if rec["web"]:
                web = html.escape(rec["web"], quote=True)
                name = f'<a href="{web}" rel="nofollow noopener">{org}</a>'
            else:
                name = org
            detail = " — ".join(
                x for x in [html.escape(rec["area"]), html.escape(rec["keys"])] if x
            )
            noscript.append(f"<li>{name}{' — ' + detail if detail else ''}</li>")
        noscript.append("</ul>")
    noscript.append("</div>")
    noscript_index = "\n".join(noscript)

    page = TEMPLATE.replace("__PAYLOAD__", payload)
    page = page.replace("__CAT_OPTS__", cat_opts)
    page = page.replace("__TYPE_OPTS__", type_opts)
    page = page.replace("__N_PUB__", str(n_pub))
    page = page.replace("__N_SCOPE__", str(n_scope))
    page = page.replace("__BUILT__", built)
    page = page.replace("__BUILT_ISO__", built_iso)
    page = page.replace("__NOSCRIPT_INDEX__", noscript_index)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"wrote {OUT}")
    print(f"  {n_pub} publishable, {n_scope} out of scope, {len(cats)} categories")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ohio Cannabis Ecosystem Directory</title>
<meta name="description" content="A searchable, source-verified directory of Ohio cannabis and cannabis-adjacent organizations: operators, service providers and nonprofits.">
<link rel="canonical" href="https://travisvought-byte.github.io/ohio-cannabis-directory/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ohio Cannabis Ecosystem Directory">
<meta property="og:title" content="Ohio Cannabis Ecosystem Directory">
<meta property="og:description" content="Who serves what in Ohio cannabis. __N_PUB__ organizations, each traced to a named source. Free and open under CC BY 4.0.">
<meta property="og:url" content="https://travisvought-byte.github.io/ohio-cannabis-directory/">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Ohio Cannabis Ecosystem Directory">
<meta name="twitter:description" content="Who serves what in Ohio cannabis. __N_PUB__ organizations, each traced to a named source. Free and open under CC BY 4.0.">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "Ohio Cannabis Ecosystem Directory",
  "description": "A source-verified directory of __N_PUB__ organizations operating in or serving Ohio's cannabis market. Each record is traced to a named source and released under CC BY 4.0.",
  "url": "https://travisvought-byte.github.io/ohio-cannabis-directory/",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "isAccessibleForFree": true,
  "keywords": ["Ohio", "cannabis", "business directory", "market map", "open data", "data provenance"],
  "version": "4.0",
  "dateModified": "__BUILT_ISO__",
  "creator": {"@type": "Person", "name": "Travis Vought"},
  "spatialCoverage": {"@type": "Place", "name": "Ohio, United States"},
  "distribution": [
    {
      "@type": "DataDownload",
      "encodingFormat": "text/csv",
      "name": "Directory records (CSV)",
      "contentUrl": "https://raw.githubusercontent.com/travisvought-byte/ohio-cannabis-directory/main/ohio-cannabis-directory.csv"
    },
    {
      "@type": "DataDownload",
      "encodingFormat": "text/csv",
      "name": "Business-to-business relationships (CSV)",
      "contentUrl": "https://raw.githubusercontent.com/travisvought-byte/ohio-cannabis-directory/main/b2b-relationships.csv"
    }
  ],
  "codeRepository": "https://github.com/travisvought-byte/ohio-cannabis-directory"
}
</script>
<style>
  :root{
    --paper:#EDEFE8;
    --paper-deep:#E3E6DC;
    --ink:#16231B;
    --ink-soft:#4A5A50;
    --rule:#C2CAB9;
    --field:#5F7434;
    --field-deep:#43521F;
    --flag:#8A4B2A;
    --serif: Georgia, "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
    --sans: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }
  *{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%}
  body{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:var(--sans); font-size:16px; line-height:1.5;
  }
  .wrap{max-width:52rem; margin:0 auto; padding:0 1.1rem}

  /* ---- masthead ---------------------------------------------------- */
  header{border-bottom:1px solid var(--rule); background:var(--paper)}
  .masthead{padding:1.6rem 0 0}
  h1{
    font-family:var(--serif); font-weight:400; font-size:1.75rem;
    line-height:1.15; margin:0 0 .35rem; letter-spacing:-.005em;
  }
  .standfirst{
    margin:0 0 1.25rem; color:var(--ink-soft); font-size:.92rem;
    max-width:44ch;
  }

  /* ---- the search is the hero -------------------------------------- */
  .searchbox{position:relative; margin-bottom:.85rem}
  #q{
    width:100%; font-family:var(--serif); font-size:1.35rem;
    padding:.55rem 2.2rem .5rem 0; color:var(--ink);
    background:transparent; border:0; border-bottom:3px solid var(--field);
    border-radius:0; appearance:none;
  }
  #q::placeholder{color:#93A08C}
  #q:focus{outline:0; border-bottom-color:var(--field-deep)}
  #q:focus-visible{outline:0}
  .searchbox:focus-within{box-shadow:0 3px 0 -1px rgba(95,116,52,.22)}
  #clear{
    position:absolute; right:0; top:50%; transform:translateY(-50%);
    background:none; border:0; font-size:1.35rem; line-height:1;
    color:var(--ink-soft); cursor:pointer; padding:.2rem .35rem; display:none;
  }
  #clear:hover{color:var(--ink)}

  .controls{display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; padding-bottom:.9rem}
  select{
    font-family:var(--sans); font-size:.88rem; color:var(--ink);
    background:var(--paper-deep); border:1px solid var(--rule);
    padding:.42rem 1.9rem .42rem .6rem; border-radius:2px;
    appearance:none; cursor:pointer; max-width:100%;
    background-image:url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='7'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%234A5A50' stroke-width='1.4' fill='none'/%3E%3C/svg%3E");
    background-repeat:no-repeat; background-position:right .6rem center;
  }
  select:focus-visible, button:focus-visible, a:focus-visible, summary:focus-visible{
    outline:2px solid var(--field-deep); outline-offset:2px;
  }
  .tally{
    font-family:var(--serif); font-size:.9rem; color:var(--ink-soft);
    margin-left:auto; white-space:nowrap;
  }
  .tally b{color:var(--ink); font-weight:400}

  /* ---- category shortcuts ------------------------------------------ */
  .lanes{display:flex; flex-wrap:wrap; gap:.3rem; padding-bottom:1rem}
  .lane{
    font-size:.79rem; font-family:var(--sans); color:var(--ink-soft);
    background:none; border:1px solid var(--rule); border-radius:2px;
    padding:.25rem .5rem; cursor:pointer;
  }
  .lane:hover{border-color:var(--field); color:var(--ink)}
  .lane[aria-pressed="true"]{background:var(--field); border-color:var(--field); color:#F3F5EE}
  .lane .n{color:#8B9884; margin-left:.3rem}
  .lane[aria-pressed="true"] .n{color:#D3DCC4}

  /* ---- records ------------------------------------------------------ */
  main{padding-top:.35rem}
  article{padding:1.05rem 0; border-bottom:1px solid var(--rule)}
  article h2{
    font-family:var(--sans); font-size:1.03rem; font-weight:600;
    margin:0 0 .18rem; line-height:1.3;
  }
  .line{font-size:.86rem; color:var(--ink-soft); margin:0 0 .1rem}
  .cat{color:var(--field-deep)}
  .keys{font-size:.86rem; color:var(--ink-soft); margin:.3rem 0 .05rem}
  .flagged{
    display:inline-block; font-size:.74rem; color:var(--flag);
    border-left:2px solid var(--flag); padding-left:.4rem; margin-top:.35rem;
  }
  .contact{display:flex; flex-wrap:wrap; gap:.15rem .9rem; margin-top:.5rem; font-size:.88rem}
  .contact a{color:var(--field-deep); text-decoration:none; border-bottom:1px solid rgba(95,116,52,.35)}
  .contact a:hover{border-bottom-color:var(--field-deep)}
  .contact span{color:#8B9884}

  details{margin-top:.55rem}
  summary{
    font-size:.8rem; color:var(--ink-soft); cursor:pointer;
    list-style:none; display:inline-block; border-bottom:1px dotted var(--rule);
  }
  summary::-webkit-details-marker{display:none}
  summary:hover{color:var(--ink)}
  .prov{
    font-size:.83rem; color:var(--ink-soft); margin:.5rem 0 0;
    padding-left:.75rem; border-left:2px solid var(--rule);
  }
  .prov p{margin:0 0 .4rem}
  .prov a{color:var(--field-deep); word-break:break-all}
  .prov .label{color:#8B9884}

  .empty{padding:3rem 0; text-align:left; color:var(--ink-soft); font-family:var(--serif)}
  .empty p{margin:0 0 .5rem}

  /* ---- footer ------------------------------------------------------- */
  footer{
    border-top:1px solid var(--rule); margin-top:2rem; padding:1.5rem 0 3rem;
    font-size:.82rem; color:var(--ink-soft);
  }
  footer p{margin:0 0 .6rem; max-width:60ch}
  footer a{color:var(--field-deep)}
  .actions{display:flex; flex-wrap:wrap; gap:.5rem; margin-bottom:1.1rem}
  .masthead .actions{margin:.1rem 0 1.15rem}
  .btn{
    font-family:var(--sans); font-size:.85rem; color:var(--ink);
    background:var(--paper-deep); border:1px solid var(--rule);
    padding:.45rem .75rem; border-radius:2px; cursor:pointer;
    text-decoration:none; display:inline-block;
  }
  .btn:hover{border-color:var(--field)}

  @media (min-width:40rem){
    .masthead{padding-top:2.4rem}
    h1{font-size:2.2rem}
    #q{font-size:1.6rem}
    article{padding:1.25rem 0}
  }
  @media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
  @media print{
    .searchbox,.controls,.lanes,.actions,details{display:none}
    body{background:#fff; font-size:11pt}
    article{page-break-inside:avoid}
  }
</style>
</head>
<body>

<header>
  <div class="wrap masthead">
    <h1>Ohio Cannabis Ecosystem Directory</h1>
    <p class="standfirst">Who serves what in Ohio cannabis. __N_PUB__ organizations, each traced to a named source.</p>

    <div class="searchbox">
      <input id="q" type="search" autocomplete="off" spellcheck="false"
             placeholder="Search packaging, mold, payments, staffing&hellip;"
             aria-label="Search the directory">
      <button id="clear" type="button" aria-label="Clear search">&times;</button>
    </div>

    <div class="controls">
      <select id="cat" aria-label="Filter by category">
        <option value="">All categories</option>
        __CAT_OPTS__
      </select>
      <select id="type" aria-label="Filter by organization type">
        <option value="">Businesses and nonprofits</option>
        __TYPE_OPTS__
      </select>
      <p class="tally" id="tally" role="status" aria-live="polite"></p>
    </div>

    <div class="lanes" id="lanes"></div>

    <div class="actions">
      <button class="btn" id="dl">Download these results as CSV</button>
      <button class="btn" id="scope" aria-pressed="false">Show __N_SCOPE__ out-of-scope records</button>
      <a class="btn" href="https://github.com/travisvought-byte/ohio-cannabis-directory/issues/new/choose" target="_blank" rel="noopener">Add or correct a listing</a>
    </div>
  </div>
</header>

<main class="wrap" id="results"></main>
<noscript>
__NOSCRIPT_INDEX__
</noscript>

<footer class="wrap">
  <p>Compiled and maintained by Travis Vought. Built __BUILT__ from master v67. Every record carries the source used to verify it; open the provenance note on any entry to see it.</p>
  <p>Out-of-scope records are kept rather than deleted so that renamed, acquired and superseded organizations stay findable. They are hidden by default.</p>
  <p>Released under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a>. Copy it, build on it, keep the attribution. Corrections and additions are welcome and get verified before they go in.</p>
</footer>

<script>
const DATA = __PAYLOAD__;

const $ = id => document.getElementById(id);
const qEl = $('q'), catEl = $('cat'), typeEl = $('type');
const results = $('results'), tally = $('tally'), lanes = $('lanes');
let showScope = false, shown = [];

const esc = s => String(s).replace(/[&<>"]/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

const splitField = value => String(value || '')
  .split('|').map(part => part.trim()).filter(Boolean);

const telHref = value => {
  const ext = value.match(/\b(?:ext\.?|extension|x)\s*(\d+)\b/i);
  const base = ext ? value.slice(0, ext.index) : value;
  const number = (base.match(/[\d+]/g) || []).join('');
  return 'tel:' + number + (ext ? ';ext=' + ext[1] : '');
};

function filtered(){
  const terms = qEl.value.toLowerCase().split(/\s+/).filter(Boolean);
  const cat = catEl.value, type = typeEl.value;
  return DATA.filter(r => {
    if (!showScope && !r.scope) return false;
    if (cat && r.cat !== cat) return false;
    if (type && r.type !== type) return false;
    return terms.every(t => r._s.includes(t));
  });
}

function record(r){
  const bits = [];
  splitField(r.email).forEach(email =>
    bits.push(`<a href="mailto:${esc(email)}">${esc(email)}</a>`));
  splitField(r.phone).forEach(phone =>
    bits.push(`<a href="${esc(telHref(phone))}">${esc(phone)}</a>`));
  if (r.web)   bits.push(`<a href="${esc(r.web)}" target="_blank" rel="noopener">Website</a>`);
  if (!bits.length) bits.push('<span>No contact detail on file</span>');

  const sources = r.src.split('|').map(s => s.trim()).filter(Boolean)
    .map(s => s.startsWith('http')
      ? `<a href="${esc(s)}" target="_blank" rel="noopener">${esc(s)}</a>`
      : esc(s)).join('<br>');

  return `<article>
    <h2>${esc(r.org)}</h2>
    <p class="line"><span class="cat">${esc(r.cat)}</span>${r.area ? ' &nbsp;/&nbsp; ' + esc(r.area) : ''}</p>
    ${r.person ? `<p class="line">${esc(r.person)}</p>` : ''}
    ${r.keys ? `<p class="keys">${esc(r.keys)}</p>` : ''}
    ${r.tier !== 'Source-verified' ? `<p class="flagged">${esc(r.tier)}</p>` : ''}
    <p class="contact">${bits.join('')}</p>
    <details>
      <summary>Provenance and notes</summary>
      <div class="prov">
        ${r.notes ? `<p>${esc(r.notes)}</p>` : ''}
        ${sources ? `<p><span class="label">Verified against</span><br>${sources}</p>` : ''}
        ${r.seed ? `<p><span class="label">First recorded via</span> ${esc(r.seed)}</p>` : ''}
      </div>
    </details>
  </article>`;
}

function render(){
  shown = filtered();
  tally.innerHTML = `<b>${shown.length}</b> of ${DATA.filter(r => showScope || r.scope).length}`;
  $('clear').style.display = qEl.value ? 'block' : 'none';

  if (!shown.length){
    results.innerHTML = `<div class="empty">
      <p>Nothing matches that yet.</p>
      <p>Try a broader word, or clear the category filter. If a real Ohio provider is missing, that is a gap worth reporting.</p>
    </div>`;
    return;
  }
  results.innerHTML = shown.map(record).join('');
}

// category shortcuts, sized by how many records sit in each lane
const counts = {};
DATA.filter(r => r.scope).forEach(r => counts[r.cat] = (counts[r.cat] || 0) + 1);
lanes.innerHTML = Object.keys(counts).sort((a,b) => counts[b] - counts[a])
  .map(c => `<button class="lane" type="button" aria-pressed="false" data-cat="${esc(c)}">${esc(c)}<span class="n">${counts[c]}</span></button>`)
  .join('');

lanes.addEventListener('click', e => {
  const b = e.target.closest('.lane');
  if (!b) return;
  catEl.value = (catEl.value === b.dataset.cat) ? '' : b.dataset.cat;
  syncLanes(); render();
});

function syncLanes(){
  lanes.querySelectorAll('.lane').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.cat === catEl.value)));
}

qEl.addEventListener('input', render);
catEl.addEventListener('change', () => { syncLanes(); render(); });
typeEl.addEventListener('change', render);
$('clear').addEventListener('click', () => { qEl.value = ''; qEl.focus(); render(); });

$('scope').addEventListener('click', e => {
  showScope = !showScope;
  e.target.setAttribute('aria-pressed', String(showScope));
  e.target.textContent = showScope
    ? 'Hide out-of-scope records'
    : 'Show __N_SCOPE__ out-of-scope records';
  render();
});

$('dl').addEventListener('click', () => {
  const cols = [['org','Organization'],['cat','Category'],['type','Type'],
    ['person','Contact Person'],['email','Email'],['phone','Phone'],['web','Website'],
    ['area','Service Area'],['keys','Capabilities / Keywords'],['tier','Verification Tier'],
    ['notes','Notes'],['src','Source(s)'],['seed','Seed Source']];
  const q = v => '"' + String(v).replace(/"/g,'""') + '"';
  const csv = [cols.map(c => q(c[1])).join(',')]
    .concat(shown.map(r => cols.map(c => q(r[c[0]])).join(','))).join('\r\n');
  const url = URL.createObjectURL(new Blob(['\ufeff' + csv], {type:'text/csv;charset=utf-8'}));
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ohio-cannabis-directory.csv';
  a.click();
  URL.revokeObjectURL(url);
});

render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
