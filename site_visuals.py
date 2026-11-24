"""Icons, step diagrams and simple bar charts for the Ohio pages (owner direction, November 24, 2026: visuals
wherever they help, ADA compliant, with the symbols themselves accessible).

Rules every visual here follows:
- It adds no claim. A step diagram repeats steps already written on the page; a chart redraws numbers that the
  page already gives as text, and names the same source and date.
- Words stay HTML text, never text inside a drawing, so they wrap, enlarge, translate and read aloud.
- Icons are original line drawings on a 24px grid (1.8 stroke, round ends), drawn in the text color
  (currentColor), so they follow Windows high contrast. They sit beside words that say the same thing, so they
  are hidden from screen readers (aria-hidden, not focusable).
- Bars never rely on color: each carries its words and value, and the second series is striped as well.
"""
import html
import re

ICONS = {
    # Record clearing, the six steps
    'search': 'M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13zM15.2 15.2 20 20',
    'fork': 'M12 21v-8M12 13 6 7M12 13l6-6M6 11V7h4M18 11V7h-4',
    'form': 'M6 3h9l4 4v14H6zM15 3v4h4M9 11h7M9 14.5h7M9 18h4',
    'tray': 'M3 14h5l1.5 3h5l1.5-3h5v6H3zM3 14l2.5-5M21 14l-2.5-5M12 3v8M8.5 7.5 12 11l3.5-3.5',
    'gavel': 'M12 6l2.5-2.5 6 6L18 12zM15 9 4 20M13 21h8',
    'order': 'M6 3h8l4 4v14H6zM14 3v4h4M9 14l2 2 4-4',
    # Advocacy, the three steps
    'pin': 'M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11zM12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
    'checklist': 'M3.5 6.5 5 8l2.5-3M3.5 12.5 5 14l2.5-3M3.5 18.5 5 20l2.5-3M11 6.5h9.5M11 12.5h9.5M11 18.5h9.5',
    'send': 'M21 3 3 10.5l7 3 3 7.5zM21 3 10 13.5',
    # Knowledge hub sections
    'book': 'M4 19V5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2 2 2 0 0 0 2 2h13M8 7.5h7M8 11h5',
    'package': 'M4 8l8-4 8 4v8l-8 4-8-4zM4 8l8 4 8-4M12 12v8M8 6l8 4',
    'flask': 'M9 3h6M10 3v6l-5.5 9.5A1.7 1.7 0 0 0 6 21h12a1.7 1.7 0 0 0 1.5-2.5L14 9V3M7.5 15h9',
    'tag': 'M3 12V4h8l10 10-8 8zM7.5 7.5h.01',
    'clock': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3.5 2',
    'leaf': 'M5 19C5 11 10 5 20 4c-1 10-7 15-15 15zM5 19l7-7',
    # Consumer routes (resources.html)
    'store': 'M3 9l1.5-5h15L21 9zM3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M5 12v9h14v-9M10 21v-5h4v5',
    'sprout': 'M12 20v-8M12 12C12 8 9 6 5 6c0 4 3 6 7 6zM12 12c0-4 3-7 7-7 0 4-3 7-7 7zM7 20h10',
    'medcard': 'M3 6h18v12H3zM8 9.5v5M5.5 12h5M13.5 10h5M13.5 14h3.5',
    'scale': 'M12 3v18M7 21h10M4 7h16M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z',
    'people': 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM2.5 20c0-3.5 2.9-6 6.5-6s6.5 2.5 6.5 6M16 4.3a3.5 3.5 0 0 1 0 6.4M18 14.4c2.1.8 3.5 2.8 3.5 5.6',
    'megaphone': 'M3 10v4h3l7 4V6l-7 4zM16.5 9.5a3.5 3.5 0 0 1 0 5M19 7a7 7 0 0 1 0 10',
    'briefcase': 'M3 8h18v12H3zM9 8V5h6v3M3 13h18',
    # Business help routes (directory.html)
    'bank': 'M3 21h18M4.5 18h15M6 18v-7M10 18v-7M14 18v-7M18 18v-7M3.5 11h17M12 3 3.5 8v3h17V8z',
    'calculator': 'M6 3h12v18H6zM9 6.5h6v3H9zM9 13h.01M12 13h.01M15 13h.01M9 16.5h.01M12 16.5h.01M15 16.5h.01',
    'shield': 'M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6zM9 12l2 2 4-4',
    'lock': 'M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4M12 15v2',
}

# One icon per knowledge section (data/knowledge.json), shared by OhioWeed's knowledge hub and the-reefer.com's
# Cannabis 101. A new section without one still builds, with no icon.
KNOWLEDGE_ICONS = {'definitions': 'book', 'forms': 'package', 'processing': 'flask', 'labels': 'tag', 'safer-use': 'clock', 'hemp': 'leaf'}


def icon(name, cls='vi', size=24):
    """A decorative line icon; the words beside it carry the meaning."""
    return (f'<svg class="{cls}" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            f'<path d="{ICONS[name]}"/></svg>')


# --v-accent and --v-tint follow each page's own color; the defaults are the Ohio red the guides use.
CSS = '''
.vflow{list-style:none;margin:16px 0 24px;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,138px),1fr));gap:10px}
.vflow li{min-width:0;break-inside:avoid}
.vflow-box{display:flex;flex-direction:column;align-items:center;gap:7px;height:100%;padding:14px 10px 12px;background:#fff;border:1px solid #c9c9c9;border-top:4px solid var(--v-accent,#8c0924);border-radius:10px;text-align:center;color:#25282b;text-decoration:none;line-height:1.3}
a.vflow-box .vflow-t{color:var(--v-accent,#8c0924);text-decoration:underline;text-underline-offset:3px}a.vflow-box:hover{border-color:var(--v-accent,#8c0924)}
.vflow-ic{position:relative;display:grid;place-items:center;width:54px;height:54px;border-radius:50%;background:var(--v-tint,#f7e9ec);color:var(--v-accent,#8c0924)}.vflow-ic svg{width:28px;height:28px}
.vflow-n{position:absolute;top:-6px;right:-9px;min-width:25px;height:25px;padding:0 6px;border:1px solid transparent;border-radius:13px;background:var(--v-accent,#8c0924);color:#fff;font:700 14px/23px system-ui,sans-serif}
.vflow-t{font-weight:650;font-size:.95rem;overflow-wrap:anywhere}
.vchart{margin:18px 0 22px;padding:16px 18px;background:#fff;border:1px solid #ccc}.vchart figcaption{margin:0 0 10px}.vchart figcaption strong{display:block}.vchart figcaption span{display:block;font-size:.87rem;color:#555}
.vbars{margin:0}.vbars>div{padding:8px 0;border-top:1px solid #e3e3e3}.vbars>div:first-child{border-top:0}.vbars dt{font-weight:650;margin:0 0 4px}
.vbars dd{margin:3px 0;display:grid;grid-template-columns:minmax(0,13.5em) minmax(0,1fr);gap:2px 12px;align-items:center;font-size:.93rem}
.vtrack{display:block;height:16px;border-radius:3px;background:#f1ecec}.vb{display:block;height:100%;min-width:4px;width:calc(var(--w)*100%);border-radius:3px;background:var(--v-accent,#8c0924)}
.vb.alt{background:repeating-linear-gradient(135deg,var(--v-accent,#8c0924) 0 4px,#ecc9d0 4px 8px);box-shadow:inset 0 0 0 1.5px var(--v-accent,#8c0924)}
.vic{display:inline-flex;align-items:center;gap:8px}.vic svg{flex:none;width:22px;height:22px;color:var(--v-accent,#8c0924)}
.sec-h{display:flex;align-items:center;gap:12px}.sec-ic{flex:none;display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:var(--v-tint,#f7e9ec);color:var(--v-accent,#8c0924)}.sec-ic svg{width:24px;height:24px}
@media(max-width:600px){.vbars dd{grid-template-columns:1fr}}
@media print{.vchart,.vflow-box{break-inside:avoid}.vb,.vflow-n,.vflow-ic,.sec-ic{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
@media (forced-colors:active){.vflow-box{border-color:CanvasText}.vb{forced-color-adjust:none;background:CanvasText}
.vb.alt{background:repeating-linear-gradient(135deg,CanvasText 0 4px,Canvas 4px 8px);box-shadow:inset 0 0 0 1.5px CanvasText}.vtrack{border:1px solid CanvasText}}
'''

_CSS_MARK = '/* site-visuals */'


def with_css(page):
    """Add the visual styles to a page's own stylesheet, once."""
    if _CSS_MARK in page:
        return page
    last = page.index('</style>')
    return page[:last] + _CSS_MARK + CSS + page[last:]


def step_flow(steps, label, accent=None):
    """The steps already written on a page, drawn as numbered icon cards in order. steps: (title, icon, href or
    None). An <ol>, so the order is read out; the visible number is hidden from screen readers because the list
    already numbers each step."""
    style = f' style="--v-accent:{accent}"' if accent else ''
    items = []
    for n, (title, name, href) in enumerate(steps, 1):
        inner = (f'<span class="vflow-ic">{icon(name)}<span class="vflow-n" aria-hidden="true">{n}</span></span>'
                 f'<span class="vflow-t">{html.escape(title, quote=False)}</span>')
        box = (f'<a class="vflow-box" href="{html.escape(href, quote=True)}">{inner}</a>' if href
               else f'<span class="vflow-box">{inner}</span>')
        items.append(f'<li>{box}</li>')
    return f'<ol class="vflow" aria-label="{html.escape(label, quote=True)}"{style}>' + ''.join(items) + '</ol>'


def years(text):
    """'6 months' -> 0.5, '1 year' -> 1, '11 years, unless …' -> 11. Anything else stops the build: a chart must
    never guess at a number the page does not state."""
    m = re.match(r'\s*(\d+(?:\.\d+)?)\s+(month|months|year|years)\b', text)
    if not m:
        raise SystemExit(f'cannot chart the waiting period {text!r}')
    value = float(m.group(1))
    return value / 12 if m.group(2).startswith('month') else value


def duration_bars(rows, series, title, note):
    """A bar chart of waiting periods already given in a table on the page. rows: (row label, [text per series]).
    Each bar keeps its words and the table's own wording ('1 year, unless excluded'); the second series is
    striped. Bars share one scale, the longest period."""
    longest = max(years(v) for _, values in rows for v in values)
    groups = []
    for label, values in rows:
        dds = ''.join(
            f'<dd><span>{html.escape(kind)}: {html.escape(v)}</span><span class="vtrack"><span class="vb{" alt" if i else ""}" '
            f'style="--w:{years(v) / longest:.4f}"></span></span></dd>'
            for i, (kind, v) in enumerate(zip(series, values)))
        groups.append(f'<div><dt>{html.escape(label)}</dt>{dds}</div>')
    return (f'<figure class="vchart"><figcaption><strong>{html.escape(title)}</strong><span>{note}</span></figcaption>'
            f'<dl class="vbars">' + ''.join(groups) + '</dl></figure>')


def section_heading(level, inner, name, attrs=''):
    """A heading with its section icon in front. The icon is hidden from screen readers, so the heading reads
    exactly as before."""
    return f'<h{level}{attrs} class="sec-h"><span class="sec-ic">{icon(name)}</span><span>{inner}</span></h{level}>'
