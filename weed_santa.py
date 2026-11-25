"""Weed Santa: national/weed-santa.html on the-reefer.com.

Owner direction, November 25, 2026: free help for Ohio adults who cannot afford cannabis, served by vetted Ohio adults
who give a legal amount at no cost under Ohio Revised Code 3796.221(A)(4). Ohio first. The page promotes the help, never
a product. Canonical data: data/weed-santa.json; every legal claim carries a named source and the date it was checked.

Both forms open an email to the site's own address from the visitor's email app (mailto). Nothing a visitor types is
sent to this site or to any third party, so requests are never stored or shown here. Built through
build_national.pages(), so it shares the national page shell (navigation, footer and visit counter).
"""
import json
from pathlib import Path

from location_validation import OHIO_COUNTIES

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data/weed-santa.json'
NAME = 'weed-santa.html'

# Line icons, decorative only (aria-hidden): every icon sits next to text that says the same thing.
PATHS = {
    'mail': 'M3 6h18v12H3zM3 7l9 6 9-6',
    'people': 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 20a6 6 0 0 1 12 0M17 11a2.5 2.5 0 1 0 0-5M16 14a5 5 0 0 1 5 6',
    'home': 'M3 11l9-7 9 7M5 10v10h14V10M10 20v-6h4v6',
    'gift': 'M3 9h18v4H3zM5 13v8h14v-8M12 9v12M12 9c-2-4-6-4-6-1s6 1 6 1zM12 9c2-4 6-4 6-1s-6 1-6 1z',
    'id': 'M3 5h18v14H3zM8 11a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM5 16a3 3 0 0 1 6 0M14 9h4M14 13h4',
    'scale': 'M12 3v18M6 21h12M4 7h16M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z',
    'pin': 'M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12zM12 11.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
    'sprout': 'M12 21v-9M12 12C12 7 8 5 4 5c0 4 3 7 8 7zM12 12c0-4 3-6 8-6 0 4-3 6-8 6',
    'nosmoke': 'M3 3l18 18M3 14h11v3H3zM17 14h1v3h-1M20 14h1v3h-1M17 10c0-2 2-2 2-4',
    'card': 'M3 6h18v12H3zM3 10h18M7 15h4',
    'star': 'M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z',
    'tag': 'M3 12V3h9l9 9-9 9zM7.5 7.5h.01',
    'check': 'M4 12l5 5L20 6',
    'x': 'M6 6l12 12M18 6L6 18',
}

CSS = ('.sr{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}.mi{display:grid;place-items:center;width:40px;height:40px;border-radius:10px;background:var(--mint);color:var(--green);margin-bottom:6px;flex:none}.mi svg{width:24px;height:24px}'
       '.ws-hero{background:var(--card);border:1px solid var(--line);border-left:6px solid #b3261e;border-radius:14px;padding:18px 20px;margin:12px 0}'
       '.ws-hero p{margin:.4em 0}.ws-cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}'
       '.ws-cta a{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;border-radius:999px;font-weight:700;text-decoration:none;border:2px solid var(--green)}'
       '.ws-cta a.primary{background:var(--green);color:#fff}.ws-cta a.secondary{background:transparent;color:var(--green)}'
       '.flow{list-style:none;padding:0;margin:14px 0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;counter-reset:s}'
       '.flow li{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;counter-increment:s}'
       '.flow li strong{display:block}.flow li strong::before{content:counter(s) ". "}.flow li p{margin:4px 0 0;font-size:.95rem}'
       '.tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}'
       '.tile{display:flex;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}.tile h3{margin:0 0 .2em;font-size:1.05rem}.tile p{margin:0}'
       '.never{list-style:none;padding:0;margin:10px 0}.never li{display:flex;gap:10px;align-items:flex-start;margin:8px 0}'
       '.never .x{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:#7a1010;color:#fff;flex:none}.never .x svg{width:16px;height:16px}'
       '.ws-form{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:12px 0;scroll-margin-top:16px}'
       '.ws-form label,.ws-form legend{font-weight:700;display:block;margin:0 0 4px}.ws-form .hint{font-weight:400;color:var(--soft);font-size:.92rem;display:block}'
       '.ws-form .field{margin:0 0 16px}.ws-form input[type=text],.ws-form select,.ws-form textarea{width:100%;max-width:32rem;padding:8px 10px;border:1px solid #6b7780;border-radius:8px;font:inherit;background:#fff;color:#111}'
       '.ws-form textarea{min-height:5em}.ws-form fieldset{border:0;padding:0;margin:0 0 16px}'
       '.ws-form .opt{display:flex;align-items:center;gap:10px;min-height:44px;font-weight:400}.ws-form .opt input{width:22px;height:22px;min-height:0;flex:none}'
       '.ws-form button{min-height:48px;padding:0 22px;border-radius:999px;border:2px solid var(--green);background:var(--green);color:#fff;font:inherit;font-weight:700;cursor:pointer}'
       '.ws-form :focus-visible{outline:3px solid #b3261e;outline-offset:2px}.req{color:#7a1010}'
       '.ws-done{margin-top:14px;padding:14px;border-radius:10px;background:var(--mint)}.ws-done textarea{width:100%;min-height:10em;font:inherit}'
       '.code{counter-reset:c;list-style:none;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}'
       '.code li{counter-increment:c;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}.code li strong::before{content:counter(c) ". "}'
       '@media (max-width:760px){.flow,.tiles,.code{grid-template-columns:1fr}}'
       '@media (prefers-color-scheme:dark){.mi{color:#a8dfbd}.ws-done{color:var(--ink)}.ws-cta a.secondary{color:#a8dfbd;border-color:#a8dfbd}}')

# Opens the visitor's own email app with the form's answers; shows the same text to copy when no email app opens.
SCRIPT = ('<script>(function(){function txt(f){var out=[],seen={};var els=f.elements;'
          'for(var i=0;i<els.length;i++){var e=els[i];if(!e.name||e.type==="submit"||e.type==="button")continue;'
          'var lab=e.getAttribute("data-label")||e.name;'
          'if((e.type==="checkbox"||e.type==="radio")&&!e.checked)continue;var v=(e.type==="checkbox"&&!e.value)?"yes":e.value.trim();if(!v)continue;'
          'if(seen[lab]){seen[lab].push(v)}else{seen[lab]=[v];out.push(lab)}}'
          'return out.map(function(k){return k+": "+seen[k].join(", ")}).join("\\n")}'
          'var fs=document.querySelectorAll("form.ws-form");for(var j=0;j<fs.length;j++)(function(f){'
          'f.addEventListener("submit",function(ev){ev.preventDefault();if(!f.reportValidity())return;'
          'var body=txt(f),to=f.getAttribute("data-to"),sub=f.getAttribute("data-subject");'
          'var done=f.querySelector(".ws-done"),ta=done.querySelector("textarea");ta.value=body;done.hidden=false;'
          'done.querySelector("[data-focus]").focus();'
          'window.location.href="mailto:"+to+"?subject="+encodeURIComponent(sub)+"&body="+encodeURIComponent(body)});'
          'var cp=f.querySelector(".ws-copy");cp.addEventListener("click",function(){var ta=f.querySelector(".ws-done textarea");'
          'ta.select();var ok=false;try{ok=document.execCommand("copy")}catch(e){}'
          'if(navigator.clipboard){navigator.clipboard.writeText(ta.value).then(function(){cp.textContent="Copied"},function(){})}else if(ok){cp.textContent="Copied"}})'
          '})(fs[j])})();</script>')


def load():
    return json.loads(DATA.read_text(encoding='utf-8'))


def svg(name):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="{PATHS[name]}"/></svg>')


def page(nat, landing):
    d = load()
    esc = nat.esc
    srcs = {s['id']: s for s in d['sources']}
    order = []
    email = nat.EMAIL

    def mark(ids):
        out = []
        for sid in ids:
            assert sid in srcs, f'weed-santa: unknown source {sid}'
            if sid not in order:
                order.append(sid)
            n = order.index(sid) + 1
            out.append(f'<a href="#wsource-{n}" aria-label="Source {n}">[{n}]</a>')
        return ' <span class="cites">' + ''.join(out) + '</span>' if out else ''

    def text_field(fid, label, hint='', required=False, auto=''):
        req = ' required aria-required="true"' if required else ''
        star = ' <span class="req">(required)</span>' if required else ''
        h = f'<span class="hint" id="{fid}-hint">{esc(hint)}</span>' if hint else ''
        desc = f' aria-describedby="{fid}-hint"' if hint else ''
        ac = f' autocomplete="{auto}"' if auto else ''
        return (f'<div class="field"><label for="{fid}">{esc(label)}{star}{h}</label>'
                f'<input type="text" id="{fid}" name="{fid}" data-label="{esc(label)}"{req}{desc}{ac}></div>')

    def county(fid):
        opts = ''.join(f'<option>{esc(c)}</option>' for c in sorted(OHIO_COUNTIES))
        return (f'<div class="field"><label for="{fid}">Ohio county <span class="req">(required)</span></label>'
                f'<select id="{fid}" name="{fid}" data-label="Ohio county" required aria-required="true"><option value="">Choose your county</option>{opts}</select></div>')

    def choices(name, legend, options, kind='radio', required=False, hint=''):
        star = ' <span class="req">(required)</span>' if required else ''
        h = f'<span class="hint">{esc(hint)}</span>' if hint else ''
        items = []
        for i, opt in enumerate(options):
            req = ' required' if required and kind == 'radio' and i == 0 else ''
            items.append(f'<label class="opt"><input type="{kind}" name="{name}" value="{esc(opt)}" data-label="{esc(legend)}"{req}> {esc(opt)}</label>')
        return f'<fieldset><legend>{esc(legend)}{star}{h}</legend>{"".join(items)}</fieldset>'

    def agree(fid, text):
        return (f'<div class="field"><label class="opt"><input type="checkbox" id="{fid}" name="{fid}" value="yes" data-label="{esc(text)}" required aria-required="true"> '
                f'{esc(text)} <span class="req">(required)</span></label></div>')

    def done(kind):
        return (f'<div class="ws-done" hidden role="status"><p><strong data-focus tabindex="-1">Your email app should open with your {kind} filled in. Press send there.</strong></p>'
                f'<p>No email app opened? Copy the text below and email it to <a href="mailto:{esc(email)}">{esc(email)}</a>.</p>'
                f'<label for="{kind}-copy-text" class="sr">Your {kind}</label><textarea id="{kind}-copy-text" readonly></textarea>'
                f'<p><button type="button" class="ws-copy">Copy the text</button></p></div>')

    body = ['<p class="crumbs"><a href="index.html">Home</a> › <a href="help.html">Get help</a> › Weed Santa</p>',
            '<h1>Weed Santa: free cannabis help for Ohio adults who can\'t afford it</h1>', nat.for_you(esc(landing['intro'])),
            f'<div class="ws-hero"><p><strong>{esc(d["who"])}</strong> Requests start in Ohio. '
            'Nothing is sold, nothing is shipped, and no donation is ever asked for or taken in return.</p>'
            '<div class="ws-cta"><a class="primary" href="#ask">Ask for help</a><a class="secondary" href="#give">Become a gifter</a>'
            '<a class="secondary" href="#cost">Cut the cost first</a></div></div>',
            '<h2 id="how">How it works, in four steps</h2><ol class="flow">']
    for s in d['steps']:
        body.append(f'<li><span class="mi">{svg(s["icon"])}</span><strong>{esc(s["title"])}</strong><p>{esc(s["text"])}</p></li>')
    body.append('</ol>')

    body.append('<h2 id="rules">Ohio\'s gifting rules, in plain words</h2>'
                '<p>Ohio lets one adult give cannabis to another only under all of these conditions. Weed Santa follows every one of them.</p><div class="tiles">')
    for r in d['rules']:
        body.append(f'<div class="tile"><span class="mi">{svg(r["icon"])}</span><div><h3>{esc(r["title"])}</h3>'
                    f'<p>{esc(r["text"])}{mark(r["source_ids"])}</p></div></div>')
    body.append('</div><p>Every state\'s gifting rule, side by side: <a href="law-sharing.html">can adults share or gift it?</a></p>')

    body.append('<h2 id="never">What Weed Santa never does</h2><ul class="never">'
                + ''.join(f'<li><span class="x">{svg("x")}</span><span>{esc(n)}</span></li>' for n in d['never']) + '</ul>')

    body.append('<h2 id="cost">Cut the cost first</h2><p>If cost is what\'s stopping you, these can help on their own or alongside a gift.</p><div class="tiles">')
    for c in d['cost_help']:
        body.append(f'<div class="tile"><span class="mi">{svg(c["icon"])}</span><div><h3>{esc(c["title"])}</h3>'
                    f'<p>{esc(c["text"])}{mark(c["source_ids"])}</p></div></div>')
    body.append('</div><p>More: <a href="ohio.html">Ohio\'s medical card, step by step</a> · <a href="coverage.html">Medicaid, insurance and the VA</a> · '
                '<a href="https://ohioweed.org/locations.html">find an Ohio dispensary</a></p>')

    body.append('<h2 id="ask">Ask for help</h2>'
                f'<p>{esc(d["privacy"])}</p>'
                f'<form class="ws-form" id="ask-form" action="mailto:{esc(email)}" method="post" enctype="text/plain" '
                f'data-to="{esc(email)}" data-subject="Weed Santa request (Ohio)" aria-labelledby="ask">'
                + text_field('ask-name', 'First name or nickname', required=True, auto='given-name')
                + text_field('ask-contact', 'Best way to reach you', 'An email address or a phone number that takes texts.', required=True)
                + county('ask-county')
                + choices('ask-why', 'Why you\'re asking', ['Medical use', 'I can\'t afford it', 'I can\'t get to a dispensary', 'I\'m a veteran'],
                          kind='checkbox', hint='Optional. Tick any that fit.')
                + choices('ask-kind', 'What would help most', ['Flower', 'Edibles', 'No preference'])
                + choices('ask-where', 'Where could you meet', ['My home', 'The gifter\'s home', 'Either'], required=True)
                + choices('ask-extra', 'Would any of this help too', ['Getting an Ohio medical card', 'Finding dispensary discounts'],
                          kind='checkbox', hint='Optional.')
                + '<div class="field"><label for="ask-note">Anything else Weed Santa should know <span class="hint" id="ask-note-hint">Optional. Please leave out diagnoses and medical records.</span></label>'
                  '<textarea id="ask-note" name="ask-note" data-label="Anything else" aria-describedby="ask-note-hint"></textarea></div>'
                + agree('ask-21', 'I am 21 or older and will show ID')
                + agree('ask-ok', 'I understand a gift is free, happens only at a private home or farm in Ohio, and that I never pay or give anything back')
                + '<button type="submit">Send my request</button>' + done('request') + '</form>')

    body.append('<h2 id="give">Become a gifter</h2>'
                f'<p>{esc(d["vetting"])} Gifters give from their own Ohio purchases or their own Ohio harvest; Weed Santa never collects or hands out cannabis.</p>'
                '<h3 id="code">The gifter\'s code</h3><ol class="code">'
                + ''.join(f'<li><strong>{esc(c["title"])}</strong><p>{esc(c["text"])}</p></li>' for c in d['code']) + '</ol>'
                f'<form class="ws-form" id="give-form" action="mailto:{esc(email)}" method="post" enctype="text/plain" '
                f'data-to="{esc(email)}" data-subject="Weed Santa gifter interest (Ohio)" aria-labelledby="give">'
                + text_field('give-name', 'Your name', required=True, auto='name')
                + text_field('give-contact', 'Best way to reach you', 'An email address or a phone number that takes texts.', required=True)
                + county('give-county')
                + choices('give-source', 'Where your gifts would come from', ['An Ohio dispensary', 'My own Ohio home grow', 'Both'], required=True)
                + choices('give-often', 'How often you could give', ['About once a month', 'A few times a year', 'Just this holiday season'], required=True)
                + choices('give-where', 'Where you could meet', ['At the requester\'s home', 'At my home', 'Either'], required=True)
                + text_field('give-vouch', 'Who can vouch for you', 'Optional. Someone Weed Santa already knows.')
                + agree('give-21', 'I am 21 or older and will show ID on a video call')
                + agree('give-code', 'I have read the gifter\'s code and will follow every point')
                + '<button type="submit">Send my interest</button>' + done('note') + '</form>')

    body.append(f'<h2 id="states">Outside Ohio</h2><p>{esc(d["other_states"])} '
                'Want it in your state? Say so through <a href="#give">the gifter form</a>, and name your state in the county box\'s note.</p>')
    body.append(f'<p class="muted">Checked {nat.long_date(d["as_of"])}. This page explains Ohio law in plain words; it is not legal advice.</p>')
    body.append('<h2 id="sources">Sources</h2><ol class="sources">' + ''.join(
        f'<li id="wsource-{n}"><a href="{esc(srcs[sid]["url"])}" target="_blank" rel="noopener">{esc(srcs[sid]["title"])}</a> · '
        f'{"primary" if srcs[sid]["kind"] == "primary" else "secondary"} source · checked {nat.long_date(srcs[sid]["checked"])}</li>'
        for n, sid in enumerate(order, 1)) + '</ol>')
    body.append(SCRIPT)
    return nat.shell('Weed Santa: free cannabis help for Ohio adults who can\'t afford it',
                     'Ask Weed Santa for help, or become a vetted gifter. Ohio adults 21+ give a legal amount for free, at private homes, under Ohio\'s gifting law. Nothing sold, nothing shipped.',
                     ''.join(body), NAME, 'the Weed Santa page',
                     ld=[nat.breadcrumbs([('Home', ''), ('Get help', 'help.html')], NAME, 'Weed Santa')], css=CSS)
