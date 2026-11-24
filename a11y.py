"""Accessibility finishing for every built page (November 24, 2026).

directory_brand.brand_page() (the Ohio pages) and build_national.shell() (the-reefer.com) call finish()
last, so every page gets, where it does not already have them:

- a "Skip to main content" link as the first thing in <body> (WCAG 2.4.1). It lands on the page's own
  heading, past the site menu, where the heading sits above <main> (the directory's search hero, the
  national home) or the menu sits inside <main> (the other Ohio pages); otherwise on <main>;
- styles for that link (hidden until a keyboard user reaches it), and less motion for visitors whose
  device asks for it (smooth scrolling and animation turned off).
"""
import re

MARK = '/* a11y-base */'
CSS = (MARK +
       '.a11y-skip{position:absolute;left:8px;top:-200px;z-index:10000;background:#fff;color:#14303f;'
       'padding:10px 14px;border:2px solid #14303f;border-radius:6px;font:700 17px/1.3 system-ui,sans-serif;'
       'text-decoration:underline}.a11y-skip:focus{top:8px;outline:3px solid #a07014;outline-offset:2px}'
       '@media print{.a11y-skip{display:none!important}}'
       '@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto!important}'
       '*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;'
       'transition-duration:.01ms!important;scroll-behavior:auto!important}}')

_SKIP_HINT = re.compile(r'skip|jump to|main content', re.I)


def _has_skip_link(body):
    for m in list(re.finditer(r'<a\b([^>]*)>(.*?)</a>', body, re.S))[:4]:
        attrs, text = m.group(1), re.sub(r'<[^>]+>', ' ', m.group(2))
        if re.search(r'href="#', attrs) and (_SKIP_HINT.search(text) or re.search(r'class="[^"]*skip', attrs)):
            return True
    return False


def _with_id(page, tag_match, fallback):
    """The element's id, adding `fallback` when it has none."""
    found = re.search(r'\bid="([^"]+)"', tag_match.group(1))
    if found:
        return page, found.group(1)
    start = tag_match.start() + len(tag_match.group(0).split()[0].rstrip('>'))
    return page[:start] + f' id="{fallback}"' + page[start:], fallback


def finish(page):
    if '</head>' not in page or not re.search(r'<body\b', page):
        return page
    body = re.search(r'<body\b[^>]*>', page)
    main = re.compile(r'<main\b([^>]*)>').search(page, body.end())
    if main is None:
        return page
    if MARK not in page:
        head_end = page.index('</head>')
        last = page.rfind('</style>', 0, head_end)
        page = (page[:last] + CSS + page[last:]) if last >= 0 else page.replace('</head>', '<style>' + CSS + '</style></head>', 1)
    body = re.search(r'<body\b[^>]*>', page)
    if _has_skip_link(page[body.end():]):
        return page
    main = re.compile(r'<main\b([^>]*)>').search(page, body.end())
    # The Ohio pages put the site menu first inside <main>: land on the heading after it.
    menu = re.compile(r'<nav\b[^>]*aria-label="Primary"[^>]*>').search(page, main.end())
    target = None
    # A page whose title sits above <main> (a hero under the site menu): land on the title, so the
    # search box beside it is not skipped.
    first_nav_end = page.find('</nav>', body.end())
    heading = re.compile(r'<h1\b([^>]*)>').search(page, body.end())
    if heading and heading.start() < main.start() and (first_nav_end < 0 or heading.start() > first_nav_end):
        page, target = _with_id(page, heading, 'page-title')
    elif menu and page.find('</main>', main.end()) > menu.start():
        menu_end = page.find('</nav>', menu.end())
        heading = re.compile(r'<h1\b([^>]*)>').search(page, menu_end)
        if heading and heading.start() < page.find('</main>', main.end()):
            page, target = _with_id(page, heading, 'page-title')
    if target is None:
        main = re.compile(r'<main\b([^>]*)>').search(page, body.end())
        page, target = _with_id(page, main, 'main-content')
    body = re.search(r'<body\b[^>]*>', page)
    return page[:body.end()] + f'<a class="a11y-skip" href="#{target}">Skip to main content</a>' + page[body.end():]
