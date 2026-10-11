"""Shared VHG identity and public update-request links."""
import base64
import re
import html
from pathlib import Path
from urllib.parse import urlencode, quote

EMAIL = 'VeteranHomeGuardians@gmail.com'
BRAND_CSS = '''
  .vhg-brand{display:flex;align-items:center;gap:1rem;margin:0 0 .5rem;text-decoration:none;color:inherit}
  .vhg-brand img{width:48px;height:auto;flex:none}
  .vhg-brand strong{display:block;font-size:1rem;line-height:1.3}
  .vhg-brand span span{display:block;font-size:.82rem;color:var(--ink-soft);margin-top:.2rem}
  .knowledge-links{display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;margin:0 0 1.5rem;font-size:.95rem}
  [hidden]{display:none!important}.site-footer{max-width:1120px;margin:24px auto;padding:20px;border-top:1px solid #ccc}.site-footer nav{display:flex;flex-wrap:wrap;gap:4px 18px}.site-footer a,.knowledge-links a{display:inline-flex;align-items:center;min-height:44px}p{max-width:70ch}button,input,select,summary{min-height:44px}button,input,select,textarea{font-size:16px}body{font-size:16px}.vhg-brand img{width:48px;height:48px}.knowledge-links{gap:0 18px}.site-footer p{font-size:14px;color:#555}@media(max-width:650px){.knowledge-links{font-size:14px;gap:0 12px}.site-footer a{font-size:14px}body a{min-height:44px;display:inline-flex;align-items:center}button,a.btn{min-height:44px}}@media print{.site-footer,.knowledge-links,.vhg-brand{display:none!important}}
  .update-contact{overflow-wrap:anywhere}
'''

def brand_header():
    return ('<a class="vhg-brand" href="index.html"><img src="assets/vhg-logo.png" alt="" width="48" height="48">'
            '<span><strong>Ohio Cannabis Directory</strong></span></a>'
            '<nav class="knowledge-links" aria-label="Primary">'
            '<a href="locations.html">Find a dispensary</a><a href="buyer-guide.html">Shop smart</a>'
            '<a href="knowledge.html">Learn</a><a href="directory.html">Business directory</a>'
            '<a href="assessment.html">Business self-check</a>'
            '<a href="https://travisvought-byte.github.io/vhg-veteran-resident-guide/">Veteran Resident Guide</a></nav>')

def brand_footer():
    return ('<footer class="site-footer"><nav aria-label="More resources">'
            '<a href="relationships.html">Who works with whom</a><a href="seeds.html">Seeds &amp; growing supplies</a>'
            '<a href="resources.html#community">Events</a><a href="resources.html">Resources by need</a>'
            '<a href="'+update_url()+'">Suggest a correction</a>'
            '<a href="https://github.com/travisvought-byte/ohio-cannabis-directory#readme">Methods &amp; sources</a>'
            '<a href="ohio-cannabis-directory.csv" download>CSV download</a>'
            '<a href="https://travisvought-byte.github.io/vhg-veteran-resident-guide/">Veteran Resident Guide</a>'
            '</nav><p>Created and maintained by Travis Vought · Shared in support of Veteran Home Guardians · '
            '<a href="https://github.com/travisvought-byte/ohio-cannabis-directory/blob/main/PROJECT_STEWARDSHIP.md">Project roles</a></p></footer>')

def update_url(kind='listing'):
    subjects = {'listing': 'Ohio Cannabis Directory: listing update',
                'relationship': 'Ohio Cannabis Directory: relationship update'}
    body = ('Organization or listing link:\r\n\r\n'
            'Addition or correction:\r\n\r\n'
            'Website or source:\r\n\r\n')
    return 'mailto:' + EMAIL + '?' + urlencode({'subject': subjects[kind], 'body': body}, quote_via=quote)

def brand_page(page):
    page = re.sub(r'<script\b[^>]*data-goatcounter=[^>]*>\s*</script>', '', page, flags=re.S)
    if '__VHG_BRAND__' not in page:
        page=page.replace('<main>', '<main>__VHG_BRAND__',1)
    page=re.sub(r'<title>(.*?)</title>',lambda m:'<title>'+re.sub(r' \|.*$','',m.group(1)).replace('Ohio Cannabis Ecosystem Directory','Ohio Cannabis Directory')+' | Ohio Cannabis Directory</title>',page,count=1)
    page=page.replace('</body>',brand_footer()+'</body>')
    title=re.search(r'<title>(.*?)</title>',page).group(1)
    description='Find Ohio cannabis businesses, dispensaries and plain-language guides, each traced to a source.'
    if 'name="description"' not in page:page=page.replace('</head>','<meta name="description" content="'+description+'"></head>')
    page=re.sub(r'<meta\s+property="og:[^"]+"[^>]*>','',page)
    meta='<meta property="og:type" content="website"><meta property="og:site_name" content="Ohio Cannabis Directory"><meta property="og:title" content="'+html.escape(title,quote=True)+'"><meta property="og:description" content="'+description+'"><meta property="og:image" content="https://travisvought-byte.github.io/ohio-cannabis-directory/assets/vhg-logo.png"><meta property="og:image:alt" content="Veteran Home Guardians logo">'
    page=page.replace('</head>',meta+'</head>')

    page = page.replace('</head>', '<script src="assets/analytics.js"></script></head>')
    return (page.replace('__VHG_BRAND__', brand_header())
            .replace('__VHG_CSS__', BRAND_CSS)
            .replace('__UPDATE_URL__', update_url())
            .replace('__RELATIONSHIP_UPDATE_URL__', update_url('relationship'))
            .replace('__VHG_EMAIL__', EMAIL))
