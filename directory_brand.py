"""Shared VHG identity and public update-request links."""
import base64
from pathlib import Path
from urllib.parse import urlencode, quote

EMAIL = 'VeteranHomeGuardians@gmail.com'
BRAND_CSS = '''
  .vhg-brand{display:flex;align-items:center;gap:1rem;margin:0 0 1.3rem;text-decoration:none;color:inherit}
  .vhg-brand img{width:80px;height:auto;flex:none}
  .vhg-brand strong{display:block;font-size:1rem;line-height:1.3}
  .vhg-brand span span{display:block;font-size:.82rem;color:var(--ink-soft);margin-top:.2rem}
  .knowledge-links{display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;margin:0 0 1.5rem;font-size:.95rem}
  .update-contact{overflow-wrap:anywhere}
'''

def brand_header():
    logo = base64.b64encode((Path(__file__).parent / 'assets/vhg-logo.png').read_bytes()).decode()
    return ('<a class="vhg-brand" href="https://vethomeguard.org/">'
            '<img src="assets/vhg-logo.png" alt="" width="80" height="80">'
            '<span><strong>Veteran Home Guardians</strong><span>A voice for all veterans</span></span></a>'
            '<nav class="knowledge-links" aria-label="Cannabis learning"><a href="buyer-guide.html">Dispensary shopping guide</a><a href="assessment.html">Business self-assessment</a><a href="knowledge.html">Cannabis knowledge</a><a href="ancestry.html">Strain library</a><a href="https://travisvought-byte.github.io/vhg-veteran-resident-guide/">Veteran Resident Guide</a></nav>')

def update_url(kind='listing'):
    subjects = {'listing': 'Ohio Cannabis Directory: listing update',
                'relationship': 'Ohio Cannabis Directory: relationship update'}
    body = ('Organization or listing link:\r\n\r\n'
            'Addition or correction:\r\n\r\n'
            'Website or source:\r\n\r\n')
    return 'mailto:' + EMAIL + '?' + urlencode({'subject': subjects[kind], 'body': body}, quote_via=quote)

def brand_page(page):
    page = page.replace('</head>', '<script src="assets/analytics.js"></script></head>')
    return (page.replace('__VHG_BRAND__', brand_header())
            .replace('__VHG_CSS__', BRAND_CSS)
            .replace('__UPDATE_URL__', update_url())
            .replace('__RELATIONSHIP_UPDATE_URL__', update_url('relationship'))
            .replace('__VHG_EMAIL__', EMAIL))
