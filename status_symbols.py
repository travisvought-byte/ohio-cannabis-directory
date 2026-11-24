"""One symbol per answer status, shared by every page that shows a status (November 24, 2026).

A state's answer never rests on color alone (WCAG 1.4.1; owner direction, November 24, 2026): a check for
allowed, a plus for medical only, a half circle for limited or partial, an X for not permitted, a dashed ring
for not yet reviewed. The national map tiles and key (build_national.py), the answer chips on the-reefer.com
and on compare.html (permissions_page.py), and the bars of the national comparison chart all draw the same
symbol, so a visitor learns it once.

Line drawings from Lucide (ISC license, https://lucide.dev), drawn in the element's text color with a CSS
mask, so they follow dark mode and show in Windows high contrast. They are decoration on top of the status
words, which stay as text: screen readers hear the words, not the symbol.
"""
from urllib.parse import quote

STATUS_SYMBOLS = {
    ('allowed', 'positive', 'broad'): '<path d="M20 6 9 17l-5-5"/>',
    ('medical-only',): '<path d="M5 12h14"/><path d="M12 5v14"/>',
    ('limited', 'varies-locally', 'partial', 'starter'): '<circle cx="12" cy="12" r="10"/><path d="M12 18a6 6 0 0 0 0-12v12z"/>',
    ('not-permitted', 'negative'): '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    ('not-reviewed', 'not-started'): ('<path d="M10.1 2.182a10 10 0 0 1 3.8 0"/><path d="M13.9 21.818a10 10 0 0 1-3.8 0"/>'
                                      '<path d="M17.609 3.721a10 10 0 0 1 2.69 2.7"/><path d="M2.182 13.9a10 10 0 0 1 0-3.8"/>'
                                      '<path d="M20.279 17.609a10 10 0 0 1-2.7 2.69"/><path d="M21.818 10.1a10 10 0 0 1 0 3.8"/>'
                                      '<path d="M3.721 6.391a10 10 0 0 1 2.7-2.69"/><path d="M6.391 20.279a10 10 0 0 1-2.69-2.7"/>'),
}
TONES = [tone for tones in STATUS_SYMBOLS for tone in tones]


def symbol_url(inner):
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='3' "
           "stroke-linecap='round' stroke-linejoin='round'>" + inner.replace('"', "'") + '</svg>')
    return 'url("data:image/svg+xml,' + quote(svg, safe=" /:='.,-") + '")'


def symbol_rules(*kinds):
    """`--sym` for each tone on `.<kind>.<tone>::before`, for every kind of element named."""
    return ''.join(','.join(f'.{kind}.{t}::before' for t in tones for kind in kinds) + '{--sym:' + symbol_url(inner) + '}'
                   for tones, inner in STATUS_SYMBOLS.items())


def chip_css(with_symbols=True):
    """A small symbol before the words of every answer chip (.chip.<tone>). Pass with_symbols=False where the page
    already sets --sym for .chip through symbol_rules(), so each drawing is written once."""
    drawn = ','.join(f'.chip.{t}::before' for t in TONES)
    return (drawn + '{content:"";display:inline-block;width:.95em;height:.95em;margin:0 .3em 0 -.1em;vertical-align:-.13em;'
            'background:currentColor;-webkit-mask:var(--sym) center/contain no-repeat;mask:var(--sym) center/contain no-repeat}'
            + (symbol_rules('chip') if with_symbols else '')
            + '@media (forced-colors:active){' + drawn + '{background:CanvasText;forced-color-adjust:none}}')
