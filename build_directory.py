#!/usr/bin/env python3
"""Build the searchable directory from canonical repository JSON.

The generated HTML includes a crawlable fallback and loads a local static
JSON payload for interactive search; no external directory API is required.
"""
import json
import html
import datetime
import calendar
from pathlib import Path
import pandas as pd
from directory_data import RELEASE, RELEASE_DATE, script_json, load_records, load_event_routes, load_directory
from directory_brand import brand_page
from public_data import externalize

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "ohio-cannabis-directory.csv"
OUT = ROOT / "directory.html"

OUT_OF_SCOPE = "Out of scope — flagged for removal or separate list"

COLS = {
    "Record ID": "id",
    "Last Reviewed": "reviewed",
    "Category": "cat",
    "Organization / Business Name": "org",
    "Type": "type",
    "Contact Person": "person",
    "Email": "email",
    "Phone": "phone",
    "Website": "web",
    "Source(s)": "src",
    "Service Area": "area",
    "Service Area (as published)": "area_original",
    "Notes": "notes",
    "Seed Source": "seed",
    "Verification Tier": "tier",
    "Capabilities / Keywords": "keys",
}

UPCOMING_EVENTS = load_event_routes()


def clean(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def main():
    data = load_directory()
    details = {s['organization_id']: s['attributes'].get('provider_details') for s in data['services'] if s.get('origin') == 'organization-profile'}
    df = pd.DataFrame(load_records(include_withdrawn=False)).dropna(how="all")

    records = []
    for _, row in df.iterrows():
        rec = {short: clean(row.get(col)) for col, short in COLS.items()}
        rec["scope"] = 0 if rec["cat"] == OUT_OF_SCOPE else 1
        rec["provider"] = details.get(rec["id"])
        # precomputed lowercase haystack keeps filtering fast on phones
        rec["_s"] = " ".join([
            rec["org"], rec["cat"], rec["keys"], rec["area"],
            rec["person"], rec["notes"], rec["type"], rec["area_original"],
            *((rec["provider"] or {}).get(field, "") for field in ("serves", "coverage_note", "contact_note")),
        ]).lower()
        records.append(rec)

    records.sort(key=lambda r: r["org"].removeprefix("! ").casefold())

    cats = sorted({r["cat"] for r in records if r["scope"]})
    types = sorted({r["type"] for r in records if r["scope"]})
    n_pub = sum(r["scope"] for r in records)
    n_scope = len(records) - n_pub
    today = RELEASE_DATE
    built = today.strftime("%B %-d, %Y")
    built_iso = today.isoformat()

    month_index = today.month - 1 + 3
    limit_year = today.year + month_index // 12
    limit_month = month_index % 12 + 1
    limit_day = min(today.day, calendar.monthrange(limit_year, limit_month)[1])
    event_limit = datetime.date(limit_year, limit_month, limit_day)
    visible_events = [
        event for event in UPCOMING_EVENTS
        if today <= datetime.date.fromisoformat(event["date"]) <= event_limit
    ]
    home_events = ['<h2>Upcoming events <span>· next 3 months</span></h2><ol class="event-line" aria-label="Upcoming Ohio cannabis events">']
    if visible_events:
        for event in sorted(visible_events, key=lambda e: (not e.get("featured", False), e["date"])):
            event_date = datetime.date.fromisoformat(event["date"])
            date_label = event_date.strftime("%a, %b %-d, %Y")
            home_events.append(
                '<li class="home-event">'
                + ('<span class="event-featured">Featured event</span>' if event.get('featured') else '') +
                f'<h3>{html.escape(event["name"])}</h3>'
                f'<p><time datetime="{event["date"]}">{html.escape(date_label)}</time></p>'
                f'<p class="event-place">{html.escape(event["place"])}</p>'
                f'<p><a href="{html.escape(event["url"], quote=True)}" target="_blank" rel="noopener">Event details</a></p>'
                + (f'<p><a href="{html.escape(event["registration_url"], quote=True)}" target="_blank" rel="noopener">Register / RSVP</a> · Checked {html.escape(event["reviewed_on"])}</p>' if event.get("registration_url") else "") +
                '</li>'
            )
    else:
        home_events.append('<li class="home-empty">No confirmed event dates in this window.</li>')
    home_events.append('</ol>')
    home_event_markup = "\n".join(home_events)

    payload = script_json(records)

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
                web = html.escape(rec["web"].split("|")[0].strip(), quote=True)
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

    page = brand_page(TEMPLATE).replace("__PAYLOAD__", payload)
    page = page.replace("__UPCOMING_EVENTS__", script_json(UPCOMING_EVENTS))
    page = page.replace("__HOME_EVENT_MARKUP__", home_event_markup)
    page = page.replace("__CAT_OPTS__", cat_opts)
    help_routes = [('Banking & Financial Services', 'Banking'), ('Accounting & Tax', 'Accounting & tax'), ('Legal & Licensing', 'Legal & licensing'), ('Testing Labs', 'Testing labs'), ('Packaging & Labeling', 'Packaging & labels'), ('Staffing & HR', 'Staffing & HR'), ('Insurance', 'Insurance'), ('Security & Cash Logistics', 'Security & cash logistics')]
    from urllib.parse import urlencode, quote
    help_actions = ['banking', 'accounting', 'legal', 'testing', 'packaging', 'staffing', 'insurance', 'security']
    page = page.replace('__HELP_ROUTES__', ''.join(f'<a class="btn help-route" href="directory.html?{html.escape(urlencode({"category": category}), quote=True)}" data-help="{html.escape(category, quote=True)}" data-track="business-help:{action}">{html.escape(label)}</a>' for (category, label), action in zip(help_routes, help_actions)))
    event_subject = quote('Ohio cannabis event submission')
    event_body = quote('Event name:\nDate and time:\nVenue, city and county:\nOrganizer and public contact:\nOfficial event or registration link:\nAudience and age requirements:\nCost, if any:\n')
    page = page.replace('__EVENT_SUBMISSION__', f'mailto:veteranhomeguardians@gmail.com?subject={event_subject}&amp;body={event_body}')
    page = page.replace("__TYPE_OPTS__", type_opts)
    page = page.replace("__AREA_OPTS__", "".join('<option>'+html.escape(a)+'</option>' for a in ["Ohio statewide","Ohio regional","Nationwide incl. Ohio","Multistate, Ohio unconfirmed","Outside Ohio"]))
    page = page.replace("__N_PUB__", str(n_pub))
    page = page.replace("__N_SCOPE__", str(n_scope))
    page = page.replace("__EXPORT_COLUMNS__", script_json([[COLS[c], c] for c in df.columns]))
    page = page.replace("__VERSION__", RELEASE["version"])
    page = page.replace("__BUILT__", built)
    page = page.replace("__BUILT_ISO__", built_iso)
    page = page.replace("__NOSCRIPT_INDEX__", noscript_index)

    page=externalize(page,payload,records,"data/public-organizations.json")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"wrote {OUT}")
    print(f"  {n_pub} publishable, {n_scope} out of scope, {len(cats)} categories")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Business directory</title>
<meta name="description" content="A searchable, source-verified directory of Ohio cannabis and cannabis-adjacent organizations: operators, service providers and nonprofits.">
<link rel="canonical" href="https://travisvought-byte.github.io/ohio-cannabis-directory/directory.html">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Business directory">
<meta property="og:title" content="Business directory">
<meta property="og:description" content="Find resources for yourself or your business in Ohio cannabis. __N_PUB__ organizations, each traced to a named source. Free and open under CC BY 4.0.">
<meta property="og:url" content="https://travisvought-byte.github.io/ohio-cannabis-directory/">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Business directory">
<meta name="twitter:description" content="Find resources for yourself or your business in Ohio cannabis. __N_PUB__ organizations, each traced to a named source. Free and open under CC BY 4.0.">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "Business directory",
  "description": "A source-verified directory of __N_PUB__ organizations operating in or serving Ohio's cannabis market. Each record is traced to a named source and released under CC BY 4.0.",
  "url": "https://travisvought-byte.github.io/ohio-cannabis-directory/",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "isAccessibleForFree": true,
  "keywords": ["Ohio", "cannabis", "business directory", "market map", "open data", "data provenance"],
  "version": "__VERSION__",
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
__VHG_CSS__
  :root{
    --paper:#F6F7F8;
    --paper-deep:#EFF1F2;
    --ink:#212325;
    --ink-soft:#3F4443;
    --rule:#BFC6CB;
    --field:#BA0C2F;
    --field-deep:#70071C;
    --flag:#70071C;
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

  /* ---- home screen highlights ------------------------------------- */
  .home-highlights{display:grid;grid-template-columns:1fr;gap:.55rem;margin:0 0 1.15rem}
  .highlight-card{padding:.75rem .85rem;background:var(--paper-deep);border-left:3px solid var(--field)}
  .highlight-card h2{font-family:var(--sans);font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-soft);margin:0 0 .25rem}
  .highlight-card h3{font-family:var(--serif);font-size:1.12rem;font-weight:400;line-height:1.25;margin:0 0 .12rem}
  .highlight-card p{font-size:.85rem;color:var(--ink-soft);margin:.15rem 0}
  .highlight-card a{color:var(--field-deep);text-decoration:none;border-bottom:1px solid rgba(186,12,47,.4)}
  .highlight-card a:hover{border-bottom-color:var(--field-deep)}
  .home-empty{font-size:.87rem;color:var(--ink-soft);margin:.2rem 0 0}

  /* ---- the search is the hero -------------------------------------- */
  .searchbox{position:relative; margin-bottom:.85rem}
  #q{
    width:100%; font-family:var(--serif); font-size:1.35rem;
    padding:.55rem 2.2rem .5rem 0; color:var(--ink);
    background:transparent; border:0; border-bottom:3px solid var(--field);
    border-radius:0; appearance:none;
  }
  #q::placeholder{color:#868E92}
  #q:focus{outline:0; border-bottom-color:var(--field-deep)}
  #q:focus-visible{outline:0}
  .searchbox:focus-within{box-shadow:0 3px 0 -1px rgba(186,12,47,.22)}
  #clear{
    position:absolute; right:0; top:50%; transform:translateY(-50%);
    background:none; border:0; font-size:1.35rem; line-height:1;
    color:var(--ink-soft); cursor:pointer; padding:.2rem .35rem; display:none;
  }
  #clear:hover{color:var(--ink)}
  #q::-webkit-search-cancel-button{-webkit-appearance:none}

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
  .lane[aria-pressed="true"]{background:var(--field); border-color:var(--field); color:#FFFFFF}
  .lane .n{color:#868E92; margin-left:.3rem}
  .lane[aria-pressed="true"] .n{color:#EFF1F2}

  /* ---- records ------------------------------------------------------ */
  main{padding-top:.35rem}
  article{overflow-wrap:anywhere;padding:1.05rem 0; border-bottom:1px solid var(--rule)}
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
  .contact a{color:var(--field-deep); text-decoration:none; border-bottom:1px solid rgba(186,12,47,.35)}
  .contact a:hover{border-bottom-color:var(--field-deep)}
  .contact span{color:#868E92}
  .business-help{margin:1rem 0}.business-help h2{font-size:1rem;margin:0 0 .5rem}.help-links{display:flex;flex-wrap:wrap;gap:.45rem}.help-route{min-height:44px;display:inline-flex;align-items:center}.help-route[aria-current="true"]{background:var(--field);color:white;border-color:var(--field)}
  .provider-details{margin:.55rem 0;padding:.6rem .75rem;background:var(--paper-deep);font-size:.84rem}.provider-details p{margin:.15rem 0}.provider-details a{color:var(--field-deep)}
  #browse-extras>summary{display:none}
  .search-active #browse-extras>summary{display:inline-flex;align-items:center}
  #search-tools{margin-bottom:.7rem}
  #browse-extras>summary::before,#search-tools>summary::before{content:'+ ';margin-right:.35rem}
  #browse-extras[open]>summary::before,#search-tools[open]>summary::before{content:'− '}
  #results{scroll-margin-top:1rem}
  @media(max-width:40rem){.masthead{padding-left:1.1rem;padding-right:1.1rem}.search-active .controls{gap:.35rem}.search-active .controls select{flex:1 1 45%;min-width:0}.search-active .tally{margin:.2rem 0}}

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
  .prov .label{color:#646A6E}

  .empty{padding:3rem 0; text-align:left; color:var(--ink-soft); font-family:var(--serif)}
  .empty p{margin:0 0 .5rem}

  .highlight-card{min-width:0}
  .upcoming-events{margin:.9rem 0 1.2rem;padding:.8rem 1rem;background:#fff;border:1px solid var(--rule);border-top:4px solid var(--field)}
  .upcoming-events h2{margin:0;font-size:1.1rem;color:var(--field-deep)}
  .upcoming-events h2 span{font-size:.78rem;font-weight:400;color:var(--ink-soft)}
  .event-line{max-width:100%;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,18rem),1fr));gap:.8rem;list-style:none;margin:.7rem 0 0;padding:0}
  .home-event{min-width:0;border-left:3px solid var(--rule);padding:.25rem 0 .1rem .8rem}
  .home-event h3{font-family:var(--serif);font-size:1.08rem;line-height:1.25;margin:.15rem 0 .3rem;font-weight:600}
  .home-event p{font-size:.82rem;margin:.2rem 0;color:var(--ink-soft)}
  .event-featured{display:block;color:var(--field-deep);font-size:.66rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase}
  .home-event time{font-weight:700}.home-event a{display:inline-block;padding:.4rem 0;min-height:44px}
  @media print{.event-line{display:block;overflow:visible}.home-event{break-inside:avoid}}
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
    .home-highlights{grid-template-columns:1fr;gap:.75rem}
    .highlight-card{padding:.85rem 1rem}
  }
  @media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
  @media print{
    .searchbox,.controls,.lanes,.actions,details{display:none}
    body{background:#fff; font-size:11pt}
    article{page-break-inside:avoid}
  }
.november-campaign{background:#fff8e7;color:#20313a;border-left:4px solid #bb8e36;padding:10px 14px;margin:14px 0 18px;font-size:15px;line-height:1.5}.november-campaign a{color:#215b76;font-weight:700;text-underline-offset:3px}.search-active .november-campaign{display:none}@media print{.november-campaign{display:none}}
</style>
</head>
<body>

<header>
  <div class="wrap masthead">
    __VHG_BRAND__
    <h1>Ohio cannabis industry directory</h1>
    <p class="directory-intro">Browse __N_PUB__ organizations and their published contacts. Search by business, person, specialty, city, or county.</p>
    <div class="searchbox">
      <input id="q" type="search" autocomplete="off" spellcheck="false"
             placeholder="Search businesses, people, cities&hellip;"
             aria-label="Search the directory">
      <button id="clear" type="button" aria-label="Clear search">&times;</button>
    </div>
    <aside class="november-campaign" aria-label="November retail fundraiser"><strong>Retailers:</strong> run a November roundup for veterans — <strong>Marine Corps birthday (Nov. 10)</strong> and Veterans Day (Nov. 11). <a href="november-campaign.html">Campaign details →</a></aside>



    <details id="browse-extras" open><summary>Upcoming events and business help</summary>
    <section class="upcoming-events" id="upcoming-card" aria-label="Upcoming Ohio cannabis events">__HOME_EVENT_MARKUP__</section>
    <p class="event-submit"><a href="__EVENT_SUBMISSION__">Submit an Ohio cannabis event</a> · Include an official event link and organizer contact.</p>

    <section class="business-help" aria-labelledby="business-help-title"><h2 id="business-help-title">Find business help</h2><nav class="help-links" aria-label="Business help">__HELP_ROUTES__</nav></section>
    </details>

    <div class="controls">
      <select id="cat" aria-label="Filter by category">
        <option value="">All categories</option>
        __CAT_OPTS__
      </select>
      <select id="type" aria-label="Filter by organization type">
        <option value="">All types</option>
        __TYPE_OPTS__
      </select>
      <select id="area" aria-label="Filter by service area"><option value="">All service areas</option>__AREA_OPTS__</select>
      <p class="tally" id="tally" role="status" aria-live="polite"></p>
      <button class="btn" id="reset-search" type="button" hidden>Reset filters</button>
    </div>

    <details id="search-tools"><summary>Search tools and all categories</summary><div class="lanes" id="lanes"></div>

    <div class="actions">
      <button class="btn" id="share">Copy search link</button><span id="share-status" role="status" aria-live="polite"></span>
      <a class="btn" href="relationships.html">Who works with whom?</a>
      <button class="btn" id="dl">Download these results as CSV</button>
      <button class="btn" id="scope" aria-pressed="false">Show __N_SCOPE__ out-of-scope records</button>
      <a class="btn" href="__UPDATE_URL__">Email a listing update</a>
    </div>
    </details>
  </div>
</header>

<p class="wrap" id="single-record" hidden><button class="btn" id="all-records">Back to all organizations</button></p>
<main class="wrap" id="results"></main>
<details class="wrap"><summary>Browse the full text index without JavaScript</summary>__NOSCRIPT_INDEX__</details>

<footer class="wrap">
  <p>Listings are not paid placements. Any sponsorship or business relationship with a listed organization is disclosed on its record.</p><p>A Veteran Home Guardians resource, compiled and maintained by Travis Vought. Built __BUILT__ from release v__VERSION__. Every record carries the source used to verify it; open the provenance note on any entry to see it.</p>
  <p class="update-contact">Additions and corrections: <a href="__UPDATE_URL__">__VHG_EMAIL__</a>.</p>
  <p><a href="intake.html">Capture organizations offline</a> · <a href="relationships.html">Browse 60 documented relationships</a> · <a href="b2b-relationships.csv">Download relationship data</a></p>
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

const UPCOMING_EVENTS = __UPCOMING_EVENTS__;
function renderHomeHighlights(){
  const today = new Date();
  today.setHours(0,0,0,0);
  const limit = new Date(today);
  limit.setMonth(limit.getMonth() + 3);
  const upcoming = UPCOMING_EVENTS.filter(event => {
    const [year, month, day] = event.date.split("-").map(Number);
    const date = new Date(year, month - 1, day);
    return date >= today && date <= limit;
  }).sort((a,b) => Number(Boolean(b.featured))-Number(Boolean(a.featured)) || a.date.localeCompare(b.date));
  const panel = $('upcoming-card');if(!panel)return;
  if (!upcoming.length){
    panel.innerHTML = '<h2>Upcoming events · next 3 months</h2><p class="home-empty">No confirmed event dates in this window.</p>';
    return;
  }
  const dateLabel = event => {
    const [year, month, day] = event.date.split("-").map(Number);
    return new Intl.DateTimeFormat(undefined, {weekday:"short", month:"short", day:"numeric", year:"numeric"}).format(new Date(year, month - 1, day));
  };
  panel.innerHTML = '<h2>Upcoming events <span>· next 3 months</span></h2><ol class="event-line" aria-label="Upcoming Ohio cannabis events">' + upcoming.map(event =>
    `<li class="home-event">${event.featured?'<span class="event-featured">Featured event</span>':''}<h3>${esc(event.name)}</h3><p><time datetime="${esc(event.date)}">${esc(dateLabel(event))}</time></p><p class="event-place">${esc(event.place)}</p><p><a href="${esc(event.url)}" target="_blank" rel="noopener">Event details</a></p>${event.registration_url?`<p><a href="${esc(event.registration_url)}" target="_blank" rel="noopener">Register / RSVP</a> · Checked ${esc(event.reviewed_on)}</p>`:''}</li>`
  ).join('') + '</ol>';
}
renderHomeHighlights();
setInterval(renderHomeHighlights, 60000);
document.addEventListener('visibilitychange', () => {if (!document.hidden) renderHomeHighlights();});

$('area').addEventListener('change',()=>{clearRecord();render()});
const splitField = value => String(value || '')
  .split('|').map(part => part.trim()).filter(Boolean);

const safeURL = value => {try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)?u.href:''}catch{return ''}};
const splitPhones = value => String(value || '').split(/[|;]/).map(s=>s.trim()).filter(Boolean);
const telHref = value => {
  const ext = value.match(/\b(?:ext\.?|extension|x)\s*(\d+)\b/i);
  // Prefer a published numeric equivalent when a vanity number includes one.
  const numeric = value.match(/(?<!\d)(?:\+?1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]*\d{3}[ .-]*\d{4}(?!\d)/);
  let number = numeric ? numeric[0].replace(/[^\d+]/g,'') : '';
  if (!number){
    const vanity = value.match(/(?:\+?1[ .-]?)?\d{3}[ .-][A-Za-z0-9][A-Za-z0-9-]{6,}/);
    if(vanity){const keypad={ABC:'2',DEF:'3',GHI:'4',JKL:'5',MNO:'6',PQRS:'7',TUV:'8',WXYZ:'9'};
      number=vanity[0].toUpperCase().replace(/[A-Z]/g,c=>Object.entries(keypad).find(([letters])=>letters.includes(c))[1]).replace(/[^\d+]/g,'');}
  }
  if(!/^\+?\d{10,15}$/.test(number))return '';
  return 'tel:' + number + (ext ? ';ext=' + ext[1] : '');
};
window.telHref=telHref;
let recordID = '';
function searchURL(){const u=new URL(location.href);u.search='';u.hash='';if(qEl.value.trim())u.searchParams.set('q',qEl.value.trim());if(catEl.value)u.searchParams.set('category',catEl.value);if(typeEl.value)u.searchParams.set('type',typeEl.value);if($('area').value)u.searchParams.set('area',$('area').value);if(showScope)u.searchParams.set('scope','all');if(recordID)u.searchParams.set('org',recordID);return u}
function loadSearch(){const p=new URLSearchParams(location.search);if(!p.has('org')&&location.hash.startsWith('#org-'))p.set('org',location.hash.slice(1));qEl.value=p.get('q')||'';$('area').value=[...$('area').options].some(o=>o.value===p.get('area'))?p.get('area'):'';catEl.value=[...catEl.options].some(o=>o.value===p.get('category'))?p.get('category'):'';typeEl.value=[...typeEl.options].some(o=>o.value===p.get('type'))?p.get('type'):'';recordID=DATA.some(r=>r.id===p.get('org'))?p.get('org'):'';showScope=p.get('scope')==='all'||!!DATA.find(r=>r.id===recordID&&!r.scope);}
function clearRecord(){recordID=''}

function filtered(){
  const terms = qEl.value.toLowerCase().split(/\s+/).filter(Boolean);
  const cat = catEl.value, type = typeEl.value;
  return DATA.filter(r => {
    if (recordID && r.id !== recordID) return false;
    if (!showScope && !r.scope) return false;
    if (cat && r.cat !== cat) return false;
    if (type && r.type !== type) return false;
    if ($('area').value && ($('area').value==='Ohio regional'?!r.area.startsWith('Ohio regional:'):r.area!==$('area').value)) return false;
    return terms.every(t => r._s.includes(t));
  });
}

function record(r){
  const bits = [];
  splitField(r.email).forEach(email =>
    bits.push(`<a href="mailto:${esc(email)}">${esc(email)}</a>`));
  splitPhones(r.phone).forEach(phone => {const href=telHref(phone);bits.push(href?`<a href="${esc(href)}">${esc(phone)}</a>`:`<span>${esc(phone)}</span>`)});
  splitField(r.web).filter(safeURL).forEach((web, i, all) =>
    bits.push(`<a href="${esc(web)}" target="_blank" rel="noopener">${r.person.includes('parent-company ownership contact') ? 'Parent-company contact' : all.length > 1 ? `Website ${i + 1}` : 'Website'}</a>`));
  if (!bits.length) bits.push(`<span>Public contact pending</span><a data-track="contact-correction" href="mailto:veteranhomeguardians@gmail.com?subject=${encodeURIComponent('Public contact for '+r.org)}&amp;body=${encodeURIComponent('Organization: '+r.org+'\nRecord ID: '+r.id+'\nOfficial website or public contact:\nEvidence link:\n')}">Submit a public contact</a>`);

  const sources = r.src.split('|').map(s => s.trim()).filter(Boolean)
    .map(s => safeURL(s)
      ? `<a href="${esc(s)}" target="_blank" rel="noopener">${esc(s)}</a>`
      : esc(s)).join('<br>');

  const displayOrg = r.org;
  return `<article id="${esc(r.id)}">
    <h2>${esc(displayOrg)}</h2>
    <p class="line"><span class="cat">${esc(r.cat)}</span>${r.area ? ' &nbsp;/&nbsp; ' + esc(r.area) : ''}</p>
    ${r.person ? `<p class="line">${esc(r.person)}</p>` : ''}
    ${r.keys ? `<p class="keys">${esc(r.keys)}</p>` : ''}
    ${r.provider ? `<div class="provider-details"><p><strong>Who it serves:</strong> ${esc(r.provider.serves)}</p><p><strong>Service area:</strong> ${esc(r.provider.coverage_note)}</p><p>${esc(r.provider.contact_note)}</p><p><a href="${esc(r.provider.source_url)}" target="_blank" rel="noopener">Contact provider</a> · Details checked ${esc(r.provider.reviewed_on)}</p></div>` : ''}
    ${r.tier !== 'Source-verified' ? `<p class="flagged">${esc(r.tier)}</p>` : ''}
    <p class="contact">${bits.join('')}</p>
    <p class="line"><a href="?org=${encodeURIComponent(r.id)}">Link to this organization</a> · <a href="relationships.html?q=${encodeURIComponent(displayOrg)}">Relationships</a>${r.reviewed?' · Checked '+new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}).format(new Date(r.reviewed+'T00:00:00Z')):''}</p>
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

let wasActive = false;
function render(){
  shown = filtered();
  const active=Boolean(qEl.value.trim()||catEl.value||typeEl.value||$('area').value||recordID||showScope);
  document.body.classList.toggle('search-active',active);
  if(active!==wasActive){$('browse-extras').open=!active;wasActive=active;}
  $('reset-search').hidden=!active;
  history.replaceState(null,'',searchURL());
  $('single-record').hidden=!recordID;
  $('scope').setAttribute('aria-pressed',String(showScope));
  $('scope').textContent=showScope?'Hide out-of-scope records':'Show __N_SCOPE__ out-of-scope records';
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
  clearRecord();catEl.value = (catEl.value === b.dataset.cat) ? '' : b.dataset.cat;
  syncLanes(); render();
});

function syncLanes(){
  document.querySelectorAll('[data-help]').forEach(a=>a.setAttribute('aria-current',String(a.dataset.help===catEl.value)));
  lanes.querySelectorAll('.lane').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.cat === catEl.value)));
}
document.querySelector('.help-links').addEventListener('click',e=>{const a=e.target.closest('[data-help]');if(!a || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey)return;e.preventDefault();qEl.value='';typeEl.value='';$('area').value='';showScope=false;clearRecord();catEl.value=a.dataset.help;syncLanes();render();$('results').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});

qEl.addEventListener('input',()=>{clearRecord();render()});
catEl.addEventListener('change', () => {clearRecord();syncLanes();render();});
typeEl.addEventListener('change',()=>{clearRecord();render()});
$('clear').addEventListener('click', () => { qEl.value = '';clearRecord();qEl.focus();render(); });

$('scope').addEventListener('click', e => {
  clearRecord();showScope = !showScope;
  e.target.setAttribute('aria-pressed', String(showScope));
  e.target.textContent = showScope
    ? 'Hide out-of-scope records'
    : 'Show __N_SCOPE__ out-of-scope records';
  render();
});

$('dl').addEventListener('click', () => {
  const cols = __EXPORT_COLUMNS__;
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

$('share').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(searchURL().href);$('share-status').textContent='Link copied.'}catch{$('share-status').textContent='Copy the page address to share this search.'}});
$('all-records').addEventListener('click',()=>{clearRecord();qEl.value='';catEl.value='';typeEl.value='';$('area').value='';showScope=false;syncLanes();render()});
$('reset-search').addEventListener('click',()=>{$('all-records').click();qEl.focus();});
window.addEventListener('popstate',()=>{loadSearch();syncLanes();render()});
loadSearch();syncLanes();render();
</script>
<script
  data-goatcounter="https://travisvought.goatcounter.com/count"
  async
  src="//gc.zgo.at/count.js">
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
