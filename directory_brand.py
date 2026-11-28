"""Shared VHG identity and public update-request links."""
import base64
import os
import re
import html
from pathlib import Path
from urllib.parse import urlencode, quote

EMAIL = 'VeteranHomeGuardians@gmail.com'

# Public address of the site that serves these pages. The default keeps current output unchanged;
# set SITE_ORIGIN to publish the same pages on another domain (for example https://ohioweed.org).
DEFAULT_SITE_ORIGIN = 'https://weed.vethomeguard.org'
SITE_ORIGIN = os.environ.get('SITE_ORIGIN', DEFAULT_SITE_ORIGIN).rstrip('/')

from urllib.parse import urlparse
SITE_HOST = urlparse(SITE_ORIGIN).netloc
DEFAULT_SITE_HOST = urlparse(DEFAULT_SITE_ORIGIN).netloc

def site_origin(text):
    """Replace the default public domain in built output with SITE_ORIGIN, including bare printed URLs."""
    return text.replace(DEFAULT_SITE_ORIGIN, SITE_ORIGIN).replace(DEFAULT_SITE_HOST, SITE_HOST)
BRAND_CSS = '''
  .vhg-brand{display:flex;align-items:center;gap:1rem;margin:0 0 .5rem;text-decoration:none;color:inherit}
  .vhg-brand img{width:48px;height:auto;flex:none}
  .vhg-brand strong{display:block;font-size:1rem;line-height:1.3}
  .vhg-brand span span{display:block;font-size:.82rem;color:var(--ink-soft);margin-top:.2rem}
  :where(a){color:#215b76;text-underline-offset:3px}:where(a:visited){color:#215b76}
  .knowledge-links{display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;margin:0 0 1.5rem;font-size:.95rem}
  [hidden]{display:none!important}.site-footer{max-width:1120px;margin:24px auto;padding:20px;border-top:1px solid #ccc}.site-footer nav{display:flex;flex-wrap:wrap;gap:4px 18px}.site-footer a,.knowledge-links a{display:inline-flex;align-items:center;min-height:44px}p{max-width:70ch}button,input,select,summary{min-height:44px}button,input,select,textarea{font-size:16px}body{font-size:16px}.vhg-brand img{width:48px;height:48px}.knowledge-links{gap:0 18px}.site-footer p{font-size:14px;color:#555}@media(max-width:650px){.knowledge-links{font-size:14px;gap:0 12px}.site-footer a{font-size:14px}body a{min-height:44px;display:inline-flex;align-items:center}button,a.btn{min-height:44px}}@media print{.site-footer,.knowledge-links,.vhg-brand,.nav-groups{display:none!important}}
  .update-contact{overflow-wrap:anywhere}
  .knowledge-links{gap:8px!important;margin:0 0 1.25rem}
  .knowledge-links a{min-height:36px;padding:0 14px;border:1px solid #cfd6d9;border-radius:999px;background:#fff;color:#20313a;text-decoration:none;font-size:14px;line-height:1.2;white-space:nowrap}
  .knowledge-links a:hover,.knowledge-links a:focus-visible{border-color:#215b76;color:#215b76}
  .site-nav{position:relative;align-items:center}
  .site-nav .nav-more{position:static}
  .site-nav .nav-more>summary{list-style:none;display:inline-flex;align-items:center;min-height:36px;padding:0 14px;border:1px solid #215b76;border-radius:999px;background:#215b76;color:#fff;font-size:14px;font-weight:600;cursor:pointer;white-space:nowrap}
  .site-nav .nav-more>summary::-webkit-details-marker{display:none}
  .site-nav .nav-more>summary::after{content:"";width:7px;height:7px;margin-left:8px;border:solid currentColor;border-width:0 2px 2px 0;transform:translateY(-2px) rotate(45deg)}
  .site-nav .nav-more[open]>summary::after{transform:translateY(2px) rotate(-135deg)}
  .nav-groups{position:absolute;left:0;right:0;top:calc(100% + 6px);z-index:20;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:4px 20px;padding:16px 18px;background:#fff;border:1px solid #cfd6d9;border-radius:10px;box-shadow:0 10px 30px rgba(20,40,50,.16)}
  .nav-group p{margin:0 0 4px;font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#555}
  .site-nav .nav-group a{display:flex;border:0;border-radius:0;padding:0;background:none;min-height:40px;white-space:normal;color:#215b76;font-size:15px;text-decoration:underline;text-underline-offset:3px}
  @media(max-width:900px){.nav-groups{grid-template-columns:repeat(2,minmax(0,1fr))}}
  @media(max-width:650px){.knowledge-links{margin:0 0 1rem}.knowledge-links>a{min-height:40px;font-size:14px}.nav-groups{grid-template-columns:1fr;max-height:70vh;overflow:auto}.site-nav .nav-group a{min-height:44px}}
'''

def brand_header():
    # Primary navigation (UX pass, Nov 10, 2026): four everyday routes stay visible
    # on a phone; every other page is one tap away in "All pages", grouped by need.
    # Works without JavaScript (details/summary).
    groups = [
        ('Businesses', [('relationships.html', 'Who works with whom'), ('assessment.html', 'Business self-check'),
                        ('directory.html#upcoming-card', 'Events'), (update_url(), 'Get listed or fix a listing')]),
        ('Buying and the law', [('buyer-guide.html', 'Shop smart'), ('knowledge.html#hemp', 'Hemp, CBD and THC'),
                                ('ancestry.html', 'Strains'), ('seeds.html', 'Seeds &amp; growing')]),
        ('Rights and policy', [('expungement.html', 'Record clearing'), ('advocacy.html', 'Advocacy'),
                               ('compare.html', 'Compare states')]),
        ('Other states', [('state.html?state=PA', 'Pennsylvania portal'), ('locations.html?state=NY', 'New York dispensaries')]),
        ('Veteran Home Guardians', [('https://guide.vethomeguard.org/', 'Veteran Resident Guide'),
                                    ('https://www.findbingo.org/ohio/', 'Ohio Bingo Finder')]),
    ]
    menu = ''.join('<div class="nav-group"><p>' + title + '</p>' + ''.join(f'<a href="{href}">{label}</a>' for href, label in links) + '</div>'
                   for title, links in groups)
    return ('<a class="vhg-brand" href="index.html"><img src="assets/vhg-logo.png" alt="" width="48" height="48">'
            '<span><strong>Ohio Cannabis Directory</strong></span></a>'
            '<nav class="knowledge-links site-nav" aria-label="Primary">'
            '<a href="directory.html">Business directory</a><a href="pennsylvania-directory.html">Pennsylvania directory</a>'
            '<a href="locations.html">Find a dispensary</a><a href="knowledge.html">Learn</a>'
            '<details class="nav-more"><summary>All pages</summary><div class="nav-groups">' + menu + '</div></details></nav>'
            '<script>(()=>{const close=()=>document.querySelectorAll(".nav-more[open]").forEach(d=>d.open=false);'
            'document.addEventListener("click",e=>{if(!e.target.closest(".nav-more")||e.target.closest(".nav-groups a"))close()});'
            'document.addEventListener("keydown",e=>{if(e.key==="Escape")close()});})();</script>')

# The family of free guides. Owner direction, November 28, 2026: guides link to each other by how visitors
# identify, and every page names the others. One list, shared by the Ohio pages, the-reefer.com's pages
# (build_national.py) and the pages published as built (scripts/build_pages_site.py), in the family's shared
# order: (key, name, address, who it is for). Abuse of Office covers Ohio, so its line says so.
GUIDES = [
    ('vets', 'Veteran Resource Guide', 'https://guide.vethomeguard.org/', 'veterans and their families'),
    ('mob', 'Mobility Talk', 'https://mobilitytalk.org/', 'disability and mobility help'),
    ('ymt', 'Yoga Mom Talk', 'https://www.yogamomtalk.com/', 'moms, parents and families'),
    ('nina', "Nina's Map", 'https://ninas-map.com/', 'Native and Indigenous people'),
    ('aoo', 'Abuse of Office', 'https://abuseofoffice.org/', 'rights with police, jails and courts in Ohio'),
    ('reefer', 'The Reefer', 'https://the-reefer.com/', 'cannabis laws and help in every state'),
    ('earth', 'Earth Rules', 'https://earthrules.org/', 'everyday adult know-how'),
    ('bingo', 'Find Bingo', 'https://www.findbingo.org/', 'bingo games and senior centers near you'),
]


def more_guides(leave_out='reefer'):
    """The footer line naming every other guide in the family. This repository is The Reefer, so it is left out."""
    items = ' · '.join(f'<a href="{url}">{name}</a> ({who})' for key, name, url, who in GUIDES if key != leave_out)
    return f'<!--related--><p class="related">More free guides: {items}</p><!--/related-->'


# "More help made for you": each line names how a visitor may describe themselves and sends them to the guide
# made for them (same owner direction). (guide key, how the visitor identifies, what the guide offers, drawn from
# each guide's own description). made_for_you() fills in the name and address.
MADE_FOR_YOU = [
    ('vets', 'A veteran or military family',
     'Free help for veterans and families in every state: claims, VA health care, housing and long-term care.'),
    ('mob', 'Living with a disability, or caring for someone who is',
     'Free disability help in every state: benefits, equipment repair, rides, in-home help and your rights.'),
    ('nina', 'Native American, Alaska Native or Indigenous',
     'A free map for First Peoples: Nations, Indian health clinics, community centers and help.'),
    ('aoo', 'Arrested, jailed or dealing with a court in Ohio',
     'Your rights when arrested or jailed in Ohio, and how to hold officials to account.'),
    ('ymt', 'A mom, parent or caregiver of kids',
     'Free help for moms and families in every state: food, rent, child care and disability help.'),
    ('reefer', 'A medical cannabis patient, or clearing a cannabis record, in any state',
     'Plain cannabis answers for every state: the law, medical cards, record clearing and help.'),
    ('earth', 'Figuring out adult life',
     'A plain guide to what everyone is expected to know: taxes, credit, moving, checkups and more.'),
    ('bingo', 'An older adult looking for bingo or a senior center',
     'Bingo games and senior centers near you.'),
]
# Deep pages that fit a line better than the guide's home page. Every one exists in that guide's repository.
MADE_FOR_YOU_PAGES = {'aoo': ('https://abuseofoffice.org/rights.html', 'Abuse of Office (Ohio)')}
MADE_FOR_YOU_OHIO_PAGES = {'bingo': ('https://www.findbingo.org/ohio/', 'Find Bingo (Ohio)')}


def made_for_you(leave_out=('reefer',), ohio=False):
    """The "More help made for you" lines: (key, who, guide name, address, what it offers). Ohio pages send older
    adults to Find Bingo's Ohio list."""
    guides = {key: (name, url) for key, name, url, _ in GUIDES}
    pages = {**MADE_FOR_YOU_PAGES, **(MADE_FOR_YOU_OHIO_PAGES if ohio else {})}
    out = []
    for key, who, what in MADE_FOR_YOU:
        if key in leave_out:
            continue
        name, url = guides[key]
        url, name = pages.get(key, (url, name))
        out.append((key, who, name, url, what))
    return out


def brand_footer():
    return ('<footer class="site-footer"><nav aria-label="More resources">'
            '<a href="pennsylvania-directory.html">Pennsylvania directory</a><a href="state.html?state=PA">Pennsylvania portal</a>'
            '<a href="relationships.html">Who works with whom</a><a href="ancestry.html">Strains</a><a href="seeds.html">Seeds &amp; growing supplies</a>'
            '<a href="resources.html#community">Events</a><a href="resources.html">Resources by need</a>'
            '<a href="'+update_url()+'">Suggest a correction</a>'
            '<a href="https://github.com/travisvought-byte/ohio-cannabis-directory#readme">Methods &amp; sources</a>'
            '<a href="ohio-cannabis-directory.csv" download>CSV download</a>'
            '<a href="https://guide.vethomeguard.org/">Veteran Resident Guide</a>'
            '<a href="https://www.findbingo.org/ohio/">Ohio Bingo Finder</a>'
            '</nav><p>Created and maintained by <a href="work-with-travis.html">Travis Vought</a> · Shared in support of Veteran Home Guardians · <a href="https://www.zeffy.com/en-US/donation-form/giving-tuesday-no-veteran-left-isolated">Give to VHG on Giving Tuesday</a> · '
            '<a href="https://github.com/travisvought-byte/ohio-cannabis-directory/blob/main/PROJECT_STEWARDSHIP.md">Project roles</a></p>'
            + more_guides() + '</footer>')

def update_url(kind='listing'):
    subjects = {'listing': 'Ohio Cannabis Directory: listing update',
                'relationship': 'Ohio Cannabis Directory: relationship update'}
    body = ('Organization or listing link:\r\n\r\n'
            'Addition or correction:\r\n\r\n'
            'Website or source:\r\n\r\n')
    return 'mailto:' + EMAIL + '?' + urlencode({'subject': subjects[kind], 'body': body}, quote_via=quote)

# The Ohio pages in this repo are published at ohioweed.org. Both sites build from here,
# so each page names one canonical address wherever it is served from. Pennsylvania and
# the shared state page stay on SITE_ORIGIN. The Ohio business directory (directory.html,
# which index.html forwards to) is the OhioWeed home, so it names ohioweed.org too.
OHIO_HOME = 'https://ohioweed.org'
OHIO_PAGES = frozenset({
    'advocacy.html', 'ancestry.html', 'assessment.html', 'buyer-guide.html', 'compare.html', 'directory.html',
    'expungement.html', 'intake.html', 'knowledge.html', 'lawmakers.html', 'locations.html',
    'november-campaign.html', 'relationships.html', 'resources.html', 'seeds.html',
    'work-with-travis.html',
})


def canonical_url(name):
    """The single public address for a built page."""
    origin = OHIO_HOME if name in OHIO_PAGES else SITE_ORIGIN
    return origin + '/' + ('' if name == 'index.html' else name)

LANDING_FILE = Path(__file__).resolve().parent / 'data/landing-pages.json'
LANDING_INTRO = '__LANDING_INTRO__'


def landing(name):
    """Who a built page is written for (data/landing-pages.json, ohio_pages): its tab title, search
    description and opening lines. Owner direction, November 23, 2026: every landing page speaks to the
    person most likely to land there."""
    import json
    return json.loads(LANDING_FILE.read_text(encoding='utf-8'))['ohio_pages'].get(name or '', {})


def apply_landing(page, name):
    """Put the page's own title, description and opening in place. A page that asks for an opening
    (__LANDING_INTRO__) and has none in the data stops the build rather than publishing a blank line."""
    entry = landing(name)
    if LANDING_INTRO in page:
        if not entry.get('intro'):
            raise SystemExit(f'{name}: the page has an opening slot but data/landing-pages.json gives it no "intro"')
        page = page.replace(LANDING_INTRO, html.escape(entry['intro'], quote=False))
    if entry.get('title'):
        page = re.sub(r'<title>.*?</title>', lambda m: '<title>' + html.escape(entry['title'], quote=False) + '</title>', page, count=1, flags=re.S)
    if entry.get('description'):
        tag = '<meta name="description" content="' + html.escape(entry['description'], quote=True) + '">'
        if re.search(r'<meta name="description" content="[^"]*">', page):
            page = re.sub(r'<meta name="description" content="[^"]*">', lambda m: tag, page, count=1)
        else:
            page = page.replace('</head>', tag + '</head>', 1)
    return page


def brand_page(page, name=None):
    page = site_origin(page)
    page = apply_landing(page, name)
    page = re.sub(r'<script\b[^>]*data-goatcounter=[^>]*>\s*</script>', '', page, flags=re.S)
    if '__VHG_BRAND__' not in page:
        page=page.replace('<main>', '<main>__VHG_BRAND__',1)
    page=re.sub(r'<title>(.*?)</title>',lambda m:'<title>'+re.sub(r' \|.*$','',m.group(1)).replace('Ohio Cannabis Ecosystem Directory','Ohio Cannabis Directory')+' | Ohio Cannabis Directory</title>',page,count=1)
    page=page.replace('</body>',brand_footer()+'</body>')
    title=re.search(r'<title>(.*?)</title>',page).group(1)
    description='Find Ohio cannabis businesses, dispensaries and plain-language guides, each traced to a source.'
    if 'name="description"' not in page:page=page.replace('</head>','<meta name="description" content="'+description+'"></head>')
    # The share card says what this page says in search, not a line shared by every page.
    own = re.search(r'<meta name="description" content="([^"]*)">', page)
    description = own.group(1) if own else description
    page=re.sub(r'<meta\s+property="og:[^"]+"[^>]*>','',page)
    meta='<meta property="og:type" content="website"><meta property="og:site_name" content="Ohio Cannabis Directory"><meta property="og:title" content="'+html.escape(title,quote=True)+'"><meta property="og:description" content="'+description+'"><meta property="og:image" content="'+SITE_ORIGIN+'/assets/vhg-logo.png"><meta property="og:image:alt" content="Veteran Home Guardians logo">'
    page=page.replace('</head>',meta+'</head>')

    if name:
        href = canonical_url(name)
        page = re.sub(r'<link rel="canonical"[^>]*>', '', page)
        page = page.replace('</head>', '<link rel="canonical" href="' + href + '">'
                            '<meta property="og:url" content="' + href + '"></head>')

    page = page.replace('</head>', '<script src="assets/analytics.js"></script></head>')
    out = page.replace('__VHG_BRAND__', brand_header())
    out = (out
           .replace('__VHG_CSS__', BRAND_CSS)
           .replace('__UPDATE_URL__', update_url())
           .replace('__RELATIONSHIP_UPDATE_URL__', update_url('relationship'))
           .replace('__VHG_EMAIL__', EMAIL))
    # Last: a skip link past the site menu, and less motion when the visitor's device asks (a11y.py).
    from a11y import finish
    return finish(out)
