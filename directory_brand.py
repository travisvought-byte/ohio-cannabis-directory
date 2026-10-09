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
  .update-contact{overflow-wrap:anywhere}
'''

def brand_header():
    logo = base64.b64encode((Path(__file__).parent / 'assets/vhg-logo.png').read_bytes()).decode()
    return ('<a class="vhg-brand" href="https://vethomeguard.org/">'
            f'<img src="data:image/png;base64,{logo}" alt="" width="80" height="80">'
            '<span><strong>Veteran Home Guardians</strong><span>A voice for all veterans</span></span></a>')

def update_url(kind='listing'):
    subjects = {'listing': 'Ohio Cannabis Directory: listing update',
                'relationship': 'Ohio Cannabis Directory: relationship update'}
    body = ('Organization or listing link:\r\n\r\n'
            'Addition or correction:\r\n\r\n'
            'Website or source:\r\n\r\n')
    return 'mailto:' + EMAIL + '?' + urlencode({'subject': subjects[kind], 'body': body}, quote_via=quote)

def brand_page(page):
    return (page.replace('__VHG_BRAND__', brand_header())
            .replace('__VHG_CSS__', BRAND_CSS)
            .replace('__UPDATE_URL__', update_url())
            .replace('__RELATIONSHIP_UPDATE_URL__', update_url('relationship'))
            .replace('__VHG_EMAIL__', EMAIL))
