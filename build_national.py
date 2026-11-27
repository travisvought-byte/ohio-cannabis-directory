"""Build the national portal: home, help by need, about, one comparison page per law
question, and one page per state and DC.

Ohio is the template. Every state page has the same two parts: the shared questions
about the law (data/state-permissions.json) and the seven directory pathways measured
by the state completion standard (data/state-scorecard.json). A state with no directory
pack yet shows its pathways as "Not started", never as absent help.

Nothing here adds a claim. Every answer, source and review date is read from the
canonical data; a missing answer reads "Not yet reviewed".

Output goes to national/ (generated; do not hand-edit). Pages use relative links, so the
folder can be served from any address. Set NATIONAL_ORIGIN (for example
https://the-reefer.com) once that domain serves these pages; until then the pages carry
no canonical address and ask search engines not to index them.

Run: python build_national.py
"""
import html
import json
import os
import re
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse

from directory_brand import DEFAULT_SITE_ORIGIN, EMAIL, OHIO_HOME
from permissions_page import KIND_LABEL, LEVEL_TEXT, chip
from validate_permissions import evidence_level

import city_guides  # visitor guides for Denver, Chicago, New York City, Los Angeles, Detroit, Boston, Seattle, Phoenix, Miami, San Francisco, Portland, New Orleans, Washington, DC, Columbus, Cleveland, Cincinnati, Dayton, Toledo and Akron, plus the visiting.html hub (November 27, 2026)

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / 'national'
SITE_NAME = 'The Reefer'
TAGLINE = 'Cannabis information and resources for every state'
ORIGIN = os.environ.get('NATIONAL_ORIGIN', '').rstrip('/')
REPO = 'https://github.com/travisvought-byte/ohio-cannabis-directory'
GIVING_TUESDAY = 'https://www.zeffy.com/en-US/donation-form/giving-tuesday-no-veteran-left-isolated'  # VHG's Giving Tuesday 2026 campaign on Zeffy; footer link until Travis says to take it down
LEVELS = {'starter': 'Starter', 'partial': 'Partial', 'broad': 'Broad'}
PACK_LABEL = {'live': 'Full state guide', 'pilot': 'Pilot state guide'}

CSS = '''
:root{color-scheme:light dark;--ink:#17231e;--soft:#4a554f;--line:#d9ddd6;--link:#1d5c7a;--bg:#f7f6f1;--card:#fff;--green:#1d4a37;--green2:#2f6d50;--gold:#e9b949;--mint:#e6f0e9;--note:#fff4dc}
*{box-sizing:border-box}@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--link);text-underline-offset:3px}.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.site{background:var(--green);color:#fff}header.site .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:0 22px;min-height:62px}
.brand{display:inline-flex;align-items:center;gap:10px;color:#fff;text-decoration:none;font-weight:800;font-size:1.22rem;min-height:48px}.brand img{width:40px;height:40px;border-radius:8px;flex:none}
header.site nav{margin-left:auto;display:flex;flex-wrap:wrap;gap:0 20px}header.site nav a{color:#fff;text-decoration:none;min-height:44px;display:inline-flex;align-items:center;font-weight:600;opacity:.9}
header.site nav a:hover,header.site nav a:focus-visible{opacity:1;text-decoration:underline}
main{max-width:1080px;margin:0 auto;padding:6px 20px 24px}
h1{font-size:clamp(26px,4vw,38px);line-height:1.15;margin:.6em 0 .3em}h2{margin:1.6em 0 .4em;font-size:1.45rem;line-height:1.25}h3{margin:1.2em 0 .4em;font-size:1.1rem}
p{max-width:70ch}.muted{color:var(--soft);font-size:.95rem}.crumbs{font-size:.9rem;margin:14px 0 0}.lede{font-size:1.08rem}
.answer{border-left:5px solid var(--green);background:var(--bg);padding:10px 16px;margin:6px 0 14px;max-width:70ch;box-shadow:0 0 0 1px rgba(0,0,0,.08)}.answer p{margin:.2em 0}.answer strong{font-size:1.08rem}
.hero{position:relative;overflow:hidden;background:linear-gradient(155deg,var(--green) 0%,var(--green2) 100%);color:#fff}
.hero .wrap{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);align-items:center;gap:24px;padding-top:34px;padding-bottom:46px}
.hero h1{font-size:clamp(32px,5.2vw,52px);line-height:1.06;margin:.25em 0 .35em;max-width:15ch}.hero p{color:#e2eee6;font-size:1.08rem;margin:.4em 0}
.ahoy{background:var(--gold);color:#221c08}.ahoy p{max-width:none;margin:0;padding:10px 0;font-size:.98rem;line-height:1.45}.ahoy a{color:#221c08;font-weight:800;white-space:nowrap}.ahoy .flag{font-size:1.15rem}.hero .worldlink{margin:14px 0 0;font-weight:700}.hero .worldlink a{color:var(--gold)}.hero .gamecard{display:flex;align-items:center;gap:14px;margin:18px 0 0;padding:14px 16px;background:rgba(0,0,0,.24);border:2px solid var(--gold);border-radius:16px;max-width:600px}.hero .gamecard .gc-flag{font-size:2rem;line-height:1}.hero .gamecard p{margin:0}.hero .gamecard .gc-title{font-weight:800;color:#fff;font-size:1.08rem}.hero .gamecard .gc-sub{color:#e2eee6;font-size:.95rem;margin-top:2px}.hero .gamecard .gc-go{margin-left:auto;flex:none;background:var(--gold);color:#221c08;font-weight:800;text-decoration:none;border-radius:999px;padding:10px 18px;min-height:44px;display:inline-flex;align-items:center;white-space:nowrap}.hero .gamecard .gc-go:hover,.hero .gamecard .gc-go:focus-visible{background:#f3cb63}header.site nav a.play{color:var(--gold);opacity:1;font-weight:800}.hero .eyebrow{color:var(--gold);font-size:.82rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase}
.hero .art .shipbox{position:relative;max-width:520px;margin:0 auto}.hero .art .ship{display:block;width:100%;height:auto;border-radius:22px;box-shadow:0 18px 38px rgba(0,0,0,.45)}
.ship .vessel{transform-origin:330px 540px;animation:bob 7s ease-in-out infinite}.ship .flag{filter:drop-shadow(0 0 7px rgba(150,225,235,.55)) drop-shadow(0 0 1px rgba(220,245,250,.9));transform-origin:330px 140px;animation:fly 3.2s ease-in-out infinite}.ship .swell{animation:swell 6s ease-in-out infinite}
.ship .sailor{transform-box:fill-box;transform-origin:50% 100%;animation:cough 9s ease-in-out infinite}.ship .ember{fill:#ff7a1a;animation:ember 9s linear infinite}
.ship .puff{opacity:0;transform-box:fill-box;transform-origin:center;animation:puff 3.3s ease-out infinite}.ship .hack{opacity:0;transform-box:fill-box;transform-origin:0 50%;animation:hack 9s ease-out infinite}
.ship .cough{font:700 13px system-ui,sans-serif;fill:#f6ecc4;opacity:0;animation:word 9s ease-out infinite}
@keyframes cough{0%,66%,92%,100%{transform:rotate(0)}70%{transform:rotate(16deg) translateY(1px)}74%{transform:rotate(5deg)}78%{transform:rotate(18deg) translateY(1px)}82%{transform:rotate(6deg)}86%{transform:rotate(15deg)}}
@keyframes ember{0%,40%,60%,100%{fill:#ff7a1a;r:2.2px}50%{fill:#ffd36b;r:3.4px}}
@keyframes puff{0%{opacity:0;transform:translate(0,0) scale(.5)}15%{opacity:.75}100%{opacity:0;transform:translate(14px,-46px) scale(2.6)}}
@keyframes hack{0%,67%{opacity:0;transform:scale(.3)}72%{opacity:.9;transform:scale(1)}80%{opacity:.8;transform:scale(1.25) translateX(4px)}92%,100%{opacity:0;transform:scale(1.7) translate(10px,-8px)}}
@keyframes word{0%,68%{opacity:0;transform:translateY(4px)}73%,86%{opacity:1;transform:translateY(0)}94%,100%{opacity:0;transform:translateY(-6px)}}
.yarn{position:relative;z-index:1;margin:-17% 3.5% 0;padding:10px 15px 13px;background:#fffaf0;color:#17231e;border-radius:14px;filter:drop-shadow(0 8px 16px rgba(0,0,0,.5))}.yarn::before{content:"";position:absolute;left:42.6%;bottom:calc(100% - 1px);width:5.4%;aspect-ratio:1/1.9;background:#fffaf0;clip-path:polygon(30% 0,100% 100%,0 100%)}.yarnhead{display:flex;align-items:center;justify-content:space-between;gap:10px}.yarn h2{margin:0;font-size:.78rem;line-height:1.3;letter-spacing:.09em;text-transform:uppercase;color:var(--green2)}.yarnhead a{color:#1d5c7a;flex:none;font-size:.85rem;min-height:28px;display:inline-flex;align-items:center}.yarn #joke-text{max-width:none;margin:.1em 0 0;color:#17231e;font-size:1.12rem;font-weight:600;line-height:1.35}
.jokes{list-style:none;padding:0}.jokes li{padding:12px 0;border-bottom:1px solid var(--line)}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-.7deg)}50%{transform:translateY(5px) rotate(.8deg)}}
@keyframes fly{0%,100%{transform:skewY(-1.6deg) scaleX(1)}50%{transform:skewY(2deg) scaleX(.975)}}
@keyframes swell{0%,100%{transform:translateX(0)}50%{transform:translateX(-36px)}}
@media (prefers-reduced-motion:reduce){.ship .vessel,.ship .flag,.ship .swell,.ship .sailor,.ship .ember,.ship .puff,.ship .hack,.ship .cough{animation:none}.ship .puff{opacity:.5}}
.pick{background:var(--card);color:var(--ink);border-radius:14px;padding:14px 16px 16px;margin-top:22px;max-width:520px;box-shadow:0 12px 30px rgba(0,0,0,.2)}
.pick label{display:block;font-weight:800;margin-bottom:6px}.pick .row{display:flex;gap:8px}.pick select{flex:1;min-width:0;font-size:1.05rem}
.pick button{font:inherit;font-weight:800;min-height:48px;padding:0 22px;border:0;border-radius:8px;background:var(--gold);color:#221c08;cursor:pointer}
.pick button:hover,.pick button:focus-visible{background:#f3cb63}.hero .pick p.muted{margin:8px 0 0;color:var(--soft);font-size:.9rem}
section.block{margin:38px 0}section.block>h2{margin-top:0}
.tasks{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:14px 0 10px}
.task{display:flex;flex-direction:column;gap:6px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 14px;text-decoration:none;color:var(--ink);transition:transform .12s,box-shadow .12s,border-color .12s}
.task:hover,.task:focus-visible{transform:translateY(-2px);box-shadow:0 8px 22px rgba(23,35,30,.1);border-color:var(--green2)}
.task .ic{width:46px;height:46px;border-radius:12px;background:var(--mint);color:var(--green);display:grid;place-items:center}.task .ic svg{width:26px;height:26px}
.task strong{font-size:1.02rem;line-height:1.25}.task .d{font-size:.88rem;color:var(--soft);line-height:1.35}
.also{font-size:.95rem}.also a{white-space:nowrap}
.tasks.intents{grid-template-columns:repeat(4,minmax(0,1fr))}.intent{position:relative}.intent .go{color:var(--ink);text-decoration:none}
.intent .go::after{content:"";position:absolute;inset:0;border-radius:14px}.intent .go:focus-visible{outline:none}.intent:focus-within{outline:3px solid var(--link);outline-offset:2px}
.intent .more{position:relative;z-index:1;display:flex;flex-wrap:wrap;gap:0 12px;margin-top:auto;font-size:.86rem}.intent .more a{min-height:32px;display:inline-flex;align-items:center}
.for-you{font-size:1.08rem}
.mapbox{display:grid;grid-template-columns:minmax(0,640px) minmax(0,1fr);gap:28px;align-items:start}
.usmap{display:grid;grid-template-columns:repeat(11,minmax(0,1fr));gap:4px;margin:10px 0;max-width:640px}
.tile{aspect-ratio:1;display:grid;place-items:center;border-radius:6px;font-weight:800;font-size:clamp(10px,1.7vw,15px);text-decoration:none;color:#fff;background:#9aa3a0}
.tile:hover,.tile:focus-visible{outline:3px solid var(--ink);outline-offset:1px}
.tile.allowed,.tile.positive,.tile.broad,.sw.allowed,.sw.positive,.sw.broad{background:#2f7d4f}.tile.medical-only,.sw.medical-only{background:#387b9c}
.tile.limited,.tile.varies-locally,.tile.partial,.tile.starter,.sw.limited,.sw.varies-locally,.sw.partial,.sw.starter{background:#e3b23c;color:#2a2108}
.tile.not-permitted,.tile.negative,.sw.not-permitted,.sw.negative{background:#b4513a}.tile.not-reviewed,.tile.not-started,.sw.not-reviewed,.sw.not-started{background:#d4d8d5;color:#3b4541}
.legend{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:6px 18px;margin:8px 0;font-size:.93rem}.legend .sw{display:inline-block;width:15px;height:15px;border-radius:4px;vertical-align:-2px;margin-right:7px}
details.az{margin:10px 0}details.az summary{cursor:pointer;font-weight:700;color:var(--link);min-height:44px;display:flex;align-items:center}
.az ul{columns:4 150px;list-style:none;padding:0;margin:6px 0}.az li{break-inside:avoid}.az a{display:inline-flex;min-height:34px;align-items:center}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.pill{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:6px 15px;border-radius:999px;background:var(--card);border:1px solid var(--line);text-decoration:none;color:var(--ink);font-weight:650}
.pill small{color:var(--soft);font-weight:500}.pill:hover,.pill:focus-visible{border-color:var(--green2);background:var(--mint)}
.guides{display:grid;gap:10px}.guide{display:block;background:var(--card);border:1px solid var(--line);border-left:5px solid var(--green2);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--ink)}
.guide strong{color:var(--link);text-decoration:underline;text-underline-offset:3px}.guide span{display:block;font-size:.9rem;color:var(--soft)}
.family{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,250px),1fr));gap:12px;margin:12px 0}
.site-card{display:block;background:var(--card);border:1px solid var(--line);border-top:5px solid var(--gold);border-radius:12px;padding:14px 16px;text-decoration:none;color:var(--ink)}
.site-card strong{display:block;font-size:1.05rem;color:var(--link)}.site-card .u{font-size:.85rem;color:var(--soft)}.site-card p{margin:.35em 0 0;font-size:.93rem}
.site-card:hover,.site-card:focus-visible,.guide:hover,.guide:focus-visible{box-shadow:0 6px 18px rgba(23,35,30,.1)}
.glance{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:4px 16px;margin:14px 0}.glance ul{list-style:none;margin:0;padding:0}
.glance li{border-top:1px solid var(--line)}.glance li:first-child{border-top:0}
.glance a{display:grid;grid-template-columns:minmax(0,210px) 1fr;gap:2px 14px;padding:10px 0;text-decoration:none;color:var(--ink);align-items:baseline}.glance .q{font-weight:650;color:var(--link)}
.onpage{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:.95rem;margin:8px 0}.onpage a{min-height:40px;display:inline-flex;align-items:center}
.medcard{background:var(--card);border:1px solid var(--line);border-left:6px solid #3b7fa0;border-radius:14px;padding:6px 18px 12px;margin:18px 0}.medcard h2{margin-top:.6em}.steps{padding-left:1.3em}.steps li{margin:.3em 0}.facts{display:grid;grid-template-columns:minmax(0,170px) 1fr;gap:6px 16px;margin:12px 0}.facts dt{font-weight:700}.facts dd{margin:0}.mednote{background:var(--note);border-radius:8px;padding:8px 12px}.medlinks{display:flex;flex-wrap:wrap;gap:8px}@media(max-width:560px){.facts{grid-template-columns:1fr}.facts dd{margin-bottom:6px}}.featured{background:var(--card);border:3px solid #4a8a3c;border-radius:16px;padding:12px 20px 14px;margin:20px 0;box-shadow:0 4px 14px rgba(0,0,0,.08)}.feat-label{display:inline-flex;align-items:center;gap:6px;margin:0 0 8px;padding:3px 12px;border-radius:999px;background:#4a8a3c;color:#fff;font-weight:700;font-size:.9rem}.feat-label svg{width:18px;height:18px}.feat-top{display:flex;flex-wrap:wrap;gap:16px;align-items:center}.feat-top>div{flex:1 1 260px;min-width:0}.feat-top h2{margin:.1em 0}.feat-logo{flex:none;display:block;background:#fff;border:1px solid var(--line);border-radius:12px;padding:8px}.feat-logo img{display:block;width:140px;height:auto}.feat-kind{margin:0;font-weight:700;color:var(--soft)}.feat-go{list-style:none;padding:0;margin:12px 0 6px;display:flex;flex-wrap:wrap;gap:10px}.feat-go a{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:8px 16px;border:2px solid #4a8a3c;border-radius:10px;font-weight:700;text-decoration:none;color:var(--ink);background:var(--card)}.feat-go a svg{width:20px;height:20px}.feat-go a.primary{background:#2f6b28;border-color:#2f6b28;color:#fff}.feat-go a:hover,.feat-go a:focus-visible{outline:3px solid #4a8a3c;outline-offset:2px}.feat-note{margin:.4em 0 0}@media(max-width:560px){.feat-go a{width:100%}.feat-go li{flex:1 1 100%}}.og{background:var(--card);border:2px solid var(--line);border-radius:16px;padding:10px 20px 12px;margin:20px 0}.og h2{display:flex;align-items:center;gap:8px;margin:.3em 0}.og h2 svg{width:24px;height:24px}.og-list{list-style:none;padding:0;margin:10px 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}.og-list li{border:1px solid var(--line);border-radius:12px;padding:10px 14px;background:var(--bg,#fff)}.og-list a{display:flex;flex-direction:column;min-height:44px;text-decoration:none;color:var(--ink)}.og-list a strong{font-size:1.1rem;text-decoration:underline;text-underline-offset:3px}.og-list p{margin:.3em 0 0;font-size:.95rem}.og-best{display:inline-block;margin-top:6px;padding:2px 10px;border-radius:999px;background:#2f6b28;color:#fff;font-weight:700;font-size:.85rem}.reuse{background:var(--mint);border-radius:10px;padding:10px 14px}.next{background:var(--mint);border-radius:14px;padding:14px 18px;margin:26px 0}.next h2{margin:0 0 .3em;font-size:1.2rem}.next ul{margin:.3em 0;padding-left:1.2em}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:8px 0;min-width:0;scroll-margin-top:12px}.card h3,.card h4{margin:0 0 6px;font-size:1rem;line-height:1.35}.card p{margin:.25rem 0}
.chip{display:inline-block;border:1px solid;border-radius:999px;padding:0 10px;font-size:.82rem;font-weight:700;line-height:1.7;white-space:nowrap}
.chip.allowed,.chip.positive,.chip.broad{background:#e7f3eb;border-color:#2e7d4f;color:#1d5a37}.chip.medical-only{background:#e5f1f7;border-color:#3b7fa0;color:#1d4f68}
.chip.limited,.chip.varies-locally,.chip.partial,.chip.starter{background:#fff4dc;border-color:#b8860b;color:#664a00}
.chip.not-permitted,.chip.negative{background:#fbeaea;border-color:#a90000;color:#7a0000}.chip.not-reviewed,.chip.not-started{background:#f0f0f0;border-color:#888;color:#444}
.level{display:inline-block;font-size:.78rem;font-weight:700;border-radius:4px;padding:0 6px;background:#eef3fb;color:#24426e}.level.compilation{background:#fff4dc;color:#664a00}
.short{font-weight:650}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,290px),1fr));gap:8px;list-style:none;padding:0;margin:12px 0}
.grid li{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 12px;min-width:0}.grid li[hidden]{display:none}.grid .state{font-weight:700;font-size:1.05rem;display:inline-flex;min-height:36px;align-items:center}
.grid .chips{display:flex;flex-wrap:wrap;gap:4px 6px;font-size:.85rem;align-items:center}.grid .meta{font-size:.82rem;color:var(--soft);margin:4px 0 0}
select{font:inherit;min-height:48px;padding:6px 9px;border:1px solid #888;border-radius:8px;background:var(--card);color:var(--ink)}
table{border-collapse:collapse;width:100%;background:var(--card)}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}.scroll{overflow-x:auto}
.sources{font-size:.9rem;padding-left:1.6em}.sources li{margin:.3em 0;overflow-wrap:anywhere}.cites a{font-size:.82rem;margin-left:2px}
.needs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,230px),1fr));gap:10px;margin:12px 0}
.need{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--ink)}
.need strong{display:block;color:var(--link);text-decoration:underline;text-underline-offset:3px}.need span{display:block;font-size:.9rem;color:var(--soft);margin-top:2px}
.need:hover,.need:focus-visible{border-color:var(--link)}
.rows{list-style:none;padding:0;margin:12px 0}.rows li{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:6px 0;display:grid;grid-template-columns:minmax(120px,190px) 1fr;gap:4px 14px;align-items:baseline}
.rows li[hidden]{display:none}.rows .state{font-weight:700}.rows .meta{grid-column:2;font-size:.82rem;color:var(--soft);margin:0}.tally{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin:8px 0}
footer.site{background:#13261d;color:#c9d7cf;margin-top:44px;font-size:.92rem}footer.site .wrap{padding:26px 20px 30px}footer.site a{color:#fff}
footer.site h2{font-size:1rem;color:var(--gold);margin:0 0 .3em;text-transform:uppercase;letter-spacing:.07em}
footer.site .cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:18px}footer.site ul{list-style:none;padding:0;margin:0}footer.site li a{display:inline-flex;min-height:36px;align-items:center}
footer.site p{max-width:none;margin:18px 0 0;color:#a9bcb1}
.glance-head{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:6px 16px;padding:12px 0 10px;border-bottom:1px solid var(--line)}
.glance-head h2{margin:0;font-size:1.2rem}.meter{display:flex;align-items:center;gap:10px;font-size:.9rem;color:var(--soft)}
.meter .bar{width:150px;height:10px;border-radius:999px;background:var(--line);overflow:hidden}.meter .fill{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--green2),#58a878)}
.glance .q{display:flex;align-items:center;gap:10px}.glance .qi{flex:none;width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:var(--mint);color:var(--green)}.glance .qi svg{width:20px;height:20px}
.glance li.t-allowed .qi,.glance li.t-positive .qi{background:#e7f3eb;color:#1d5a37}.glance li.t-medical-only .qi{background:#e5f1f7;color:#1d4f68}
.glance li.t-limited .qi,.glance li.t-varies-locally .qi{background:#fff4dc;color:#664a00}.glance li.t-not-permitted .qi,.glance li.t-negative .qi{background:#fbeaea;color:#7a0000}
.glance li.t-not-reviewed .qi{background:#f0f0f0;color:#555}.glance a:hover .q,.glance a:focus-visible .q{text-decoration:underline}
.tile{position:relative}
@media (prefers-reduced-motion:no-preference){.usmap .tile{animation:tilein .45s ease-out both;animation-delay:calc(var(--i,0)*16ms);transition:transform .12s}.usmap .tile:hover,.usmap .tile:focus-visible{transform:scale(1.1);z-index:4}
.meter .fill{animation:grow .9s ease-out both}.glance li{animation:rise .35s ease-out both;animation-delay:calc(var(--i,0)*40ms)}}
@keyframes tilein{from{opacity:0;transform:scale(.55)}to{opacity:1;transform:none}}@keyframes grow{from{width:0}}@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@media (hover:hover){.tile::after{content:attr(data-tip);position:absolute;bottom:calc(100% + 7px);left:50%;transform:translateX(-50%);z-index:5;background:#13261d;color:#fff;font:600 13px/1.3 system-ui,sans-serif;padding:6px 9px;border-radius:7px;white-space:nowrap;box-shadow:0 6px 16px rgba(0,0,0,.25);opacity:0;pointer-events:none;transition:opacity .12s}
.tile.tl::after{left:0;transform:none}.tile.tr::after{left:auto;right:0;transform:none}.tile:hover::after,.tile:focus-visible::after{opacity:1}}
@media (prefers-color-scheme:dark){:root{--ink:#e6ece8;--soft:#a8b6af;--line:#33433b;--link:#8fcbe8;--bg:#111a15;--card:#1a251f;--mint:#1e3328;--note:#3a3119}
.task .ic,.glance .qi{color:#a8dfbd}.task:hover,.task:focus-visible{box-shadow:0 8px 22px rgba(0,0,0,.4)}
.chip.allowed,.chip.positive,.chip.broad{background:rgba(46,125,79,.25);color:#a3e2bb}.chip.medical-only{background:rgba(59,127,160,.25);color:#a9d8ef}
.chip.limited,.chip.varies-locally,.chip.partial,.chip.starter{background:rgba(184,134,11,.22);color:#f1d48a}.chip.not-permitted,.chip.negative{background:rgba(169,0,0,.25);color:#f3b0a6;border-color:#d0645a}
.chip.not-reviewed,.chip.not-started{background:rgba(136,136,136,.2);color:#cfd4d1}.level{background:#22324a;color:#bcd0f0}.level.compilation{background:#3a3119;color:#f1d48a}
.glance li.t-allowed .qi,.glance li.t-positive .qi{background:rgba(46,125,79,.28);color:#a3e2bb}.glance li.t-medical-only .qi{background:rgba(59,127,160,.28);color:#a9d8ef}
.glance li.t-limited .qi,.glance li.t-varies-locally .qi{background:rgba(184,134,11,.25);color:#f1d48a}.glance li.t-not-permitted .qi,.glance li.t-negative .qi{background:rgba(169,0,0,.28);color:#f3b0a6}
.glance li.t-not-reviewed .qi{background:rgba(136,136,136,.22);color:#cfd4d1}.tile.not-reviewed,.tile.not-started{background:#3a4640;color:#d7ddd9}.sw.not-reviewed,.sw.not-started{background:#3a4640}
select{border-color:#5d6b64}}
@media(max-width:900px){.tasks{grid-template-columns:repeat(3,minmax(0,1fr))}.tasks.intents{grid-template-columns:repeat(2,minmax(0,1fr))}.mapbox{grid-template-columns:1fr;gap:6px}}
@media(max-width:720px){.hero .wrap{grid-template-columns:1fr;padding-top:24px;padding-bottom:34px}.hero .art{order:-1}.hero .art .shipbox{max-width:420px;margin:0}}
@media(max-width:560px){.hero .gamecard{flex-wrap:wrap}.hero .gamecard .gc-go{margin-left:0;width:100%;justify-content:center}header.site nav{margin-left:0;gap:0 16px}header.site .wrap{padding-bottom:4px}.tasks{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.task{padding:12px}.tasks.intents{grid-template-columns:1fr}
.usmap{gap:3px}.tile{border-radius:4px}.glance a{grid-template-columns:1fr}.needs{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.need{padding:10px 11px}.rows li{grid-template-columns:1fr}.rows .meta{grid-column:1}}
/* Sponsored spots: set apart from listings and answers by a dashed gold frame and their own label. */
.ad-slot{margin:34px 0;padding:10px 16px 14px;max-width:720px;background:#fbf6e6;border:2px dashed #b89a45;border-radius:12px}.ad-slot[hidden]{display:none}
.ad-label{margin:0 0 6px;font-size:.75rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:#6b5517}
.ad-slot a{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;text-decoration:none;color:var(--ink);min-height:44px}.ad-slot img{max-width:120px;max-height:90px;width:auto;height:auto;border-radius:8px;flex:none}
.ad-slot .ad-text{flex:1 1 220px;min-width:0}.ad-slot strong{display:block;color:var(--link);text-decoration:underline;text-underline-offset:3px}.ad-slot .ad-text span{display:block;font-size:.93rem}
@media (prefers-color-scheme:dark){.ad-slot{background:#25210f;border-color:#8c7638}.ad-label{color:#e8d08a}}
@media print{header.site nav,footer.site,select,label,.pick,.ad-slot{display:none}}
'''


# A symbol on each map tile, key swatch, answer chip and comparison bar, so a state's answer does not rest on
# color alone (WCAG 1.4.1; owner direction, November 24, 2026). The symbols live in status_symbols.py, shared
# with compare.html. Screen readers already hear the answer in each tile's label and each chip's words.
from status_symbols import STATUS_SYMBOLS, chip_css, symbol_rules, symbol_url as _symbol_url  # noqa: E402


def status_symbol_css():
    rules = ['.usmap .tile{align-content:center;gap:1px}'
             '.usmap .tile::before,.legend .sw::before,.spread .seg::before{content:"";display:block;background:currentColor;'
             '-webkit-mask:var(--sym) center/contain no-repeat;mask:var(--sym) center/contain no-repeat}'
             '.usmap .tile::before{width:.8em;height:.8em}'
             '.sw{color:#fff}.legend .sw{display:inline-grid;place-items:center}.legend .sw::before{width:11px;height:11px}'
             '.sw.limited,.sw.varies-locally,.sw.partial,.sw.starter{box-shadow:inset 0 0 0 1.5px #8a6a12}'
             '.sw.not-reviewed,.sw.not-started{box-shadow:inset 0 0 0 1.5px #6b7470}'
             '.spread .seg::before{flex:none;width:13px;height:13px}',
             symbol_rules('tile', 'sw', 'seg', 'chip'), chip_css(with_symbols=False)]
    rules.append('@media (prefers-color-scheme:dark){.sw.not-reviewed,.sw.not-started{color:#d7ddd9}}')
    rules.append('@media (forced-colors:active){.usmap .tile::before{background:LinkText;forced-color-adjust:none}'
                 '.legend .sw::before,.spread .seg::before{background:CanvasText;forced-color-adjust:none}}')
    return '\n' + ''.join(rules) + '\n'


CSS += status_symbol_css()

ASSETS = '../assets/the-reefer/'  # national/ pages; the published copy sits at the root (see scripts/build_pages_site.py)
LOGO_ALT = 'The-Reefer.com logo: a pirate skull in a red bandana and eye patch over crossed bones and a cannabis leaf'

ICON_PATHS = {
    'scale': 'M12 3v18M6 21h12M4 7h16M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z',
    'bag': 'M5 8h14l-1 12H6zM9 8V6a3 3 0 0 1 6 0v2',
    'sprout': 'M12 21v-9M12 12C12 8 9 6 5 6c0 4 3 6 7 6zM12 12c0-4 3-7 7-7 0 4-3 7-7 7z',
    'plane': 'M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z',
    'record': 'M7 3h7l5 5v13H7zM14 3v5h5M10 14.5l2 2 4-4',
    'star': 'M12 3l2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3l-5.5 2.9 1-6.2L3 9.6l6.2-.9z',
    'heart': 'M12 20s-7-4.4-9-9a4.5 4.5 0 0 1 9-3 4.5 4.5 0 0 1 9 3c-2 4.6-9 9-9 9zM12 10v5M9.5 12.5h5',
    'person': 'M4 21c0-3.3 3.6-5.5 8-5.5s8 2.2 8 5.5M12 12.5a4.25 4.25 0 1 0 0-8.5 4.25 4.25 0 0 0 0 8.5z',
    'megaphone': 'M3 10v4h3l7 4V6l-7 4zM16.5 9.5a3.5 3.5 0 0 1 0 5M19 7a7 7 0 0 1 0 10',
    'briefcase': 'M3 8h18v12H3zM9 8V5h6v3M3 13h18',
    'card': 'M3 6h18v12H3zM3 10h18M7 15h4M15 13.5v3M13.5 15h3',
    'box': 'M4 8l8-4 8 4v8l-8 4-8-4zM4 8l8 4 8-4M12 12v8',
    'swap': 'M4 9h14l-3-3M20 15H6l3 3',
    'cloud': 'M7 18a4 4 0 0 1-.6-7.96A5.5 5.5 0 0 1 17 9.1 4.5 4.5 0 0 1 17 18z',
    'car': 'M3 16v-4l2.2-5h13.6l2.2 5v4zM3 12h18M6 16v3M18 16v3M7 14h.01M17 14h.01',
    # Help page (November 24, 2026): a capitol for federal law, a gavel for legal help, a phone for help lines.
    'capitol': 'M3 21h18M4 18h16M5.5 18v-6M10 18v-6M14 18v-6M18.5 18v-6M3.5 12h17M6.5 12a5.5 5.5 0 0 1 11 0M12 6.5V3',
    'gavel': 'M12 6l2.5-2.5 6 6L18 12zM15 9 4 20M13 21h8',
    'phone': 'M5 4h3.5L10 8.5 8 10a11 11 0 0 0 6 6l1.5-2 4.5 1.5V19a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z',
    # Visuals pass (November 25, 2026): steps of a medical card, the coverage questions, privacy, partners and about.
    'doctor': 'M6 3v6a4 4 0 0 0 8 0V3M10 13v2.5a5 5 0 0 0 10 0V14M20 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z',
    'form': 'M6 3h9l4 4v14H6zM15 3v4h4M9 11h7M9 14.5h7M9 18h4',
    'shield': 'M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6zM9 12l2 2 4-4',
    'pill': 'M10.5 20.5a5 5 0 0 1-7-7l6-6a5 5 0 0 1 7 7zM8.5 8.5l7 7',
    'receipt': 'M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h3',
    'chart': 'M4 20V10M10 20V4M16 20v-7M2 20h20',
    'server': 'M4 4h16v6H4zM4 14h16v6H4zM8 7h.01M8 17h.01',
    'pin': 'M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11zM12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
    'lock': 'M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4M12 15v2',
    'tag': 'M3 12V4h8l10 10-8 8zM7.5 7.5h.01',
    'link': 'M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1',
    'people': 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM2.5 20c0-3.5 2.9-6 6.5-6s6.5 2.5 6.5 6M16 4.3a3.5 3.5 0 0 1 0 6.4M18 14.4c2.1.8 3.5 2.8 3.5 5.6',
    'mail': 'M3 6h18v12H3zM3 6l9 7 9-7',
    'check': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM8 12l3 3 5-6',
    'book': 'M4 19V5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2 2 2 0 0 0 2 2h13M8 7.5h7M8 11h5',
    'calendar': 'M4 5h16v16H4zM4 10h16M8 3v4M16 3v4',
    'globe': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3c2.5 2.5 3.8 5.5 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.5-3.8-9S9.5 5.5 12 3z',
    'warning': 'M12 3 2 20h20zM12 9v5M12 17h.01',
    'leaf': 'M5 19C5 11 10 5 20 4c-1 10-7 15-15 15zM5 19l7-7',
}
QUESTION_ICON = {'adult-use': 'scale', 'medical': 'heart', 'buying': 'bag', 'possession': 'box', 'sharing': 'swap', 'home-grow': 'sprout',
                 'public-use': 'cloud', 'driving': 'car', 'employment': 'briefcase', 'record-relief': 'record'}


def icon(name):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="{ICON_PATHS[name]}"/></svg>')


# A tile map: every state the same size, placed roughly where it sits on a US map (row, column).
TILES = {
    'AK': (0, 0), 'ME': (0, 10), 'WI': (1, 5), 'VT': (1, 9), 'NH': (1, 10),
    'WA': (2, 0), 'ID': (2, 1), 'MT': (2, 2), 'ND': (2, 3), 'MN': (2, 4), 'IL': (2, 5), 'MI': (2, 6), 'NY': (2, 8), 'MA': (2, 9),
    'OR': (3, 0), 'NV': (3, 1), 'WY': (3, 2), 'SD': (3, 3), 'IA': (3, 4), 'IN': (3, 5), 'OH': (3, 6), 'PA': (3, 7), 'NJ': (3, 8), 'CT': (3, 9), 'RI': (3, 10),
    'CA': (4, 0), 'UT': (4, 1), 'CO': (4, 2), 'NE': (4, 3), 'MO': (4, 4), 'KY': (4, 5), 'WV': (4, 6), 'VA': (4, 7), 'MD': (4, 8), 'DE': (4, 9),
    'AZ': (5, 1), 'NM': (5, 2), 'KS': (5, 3), 'AR': (5, 4), 'TN': (5, 5), 'NC': (5, 6), 'SC': (5, 7), 'DC': (5, 8),
    'OK': (6, 3), 'LA': (6, 4), 'MS': (6, 5), 'AL': (6, 6), 'GA': (6, 7),
    'HI': (7, 0), 'TX': (7, 3), 'FL': (7, 8),
}


def tone_of(question, status):
    own = (question or {}).get('statuses', {}).get(status)
    return own['tone'] if own else status


# Owner direction, November 26, 2026: "could you just give us a better map?" The square tile grid became a real map of
# the country, the same state outlines Nina's Map uses (data/us-map.json). Each state is a link with its answer in its
# name; small northeastern states also get a labeled box at the side so they are easy to tap. Color is never the only
# signal: each answer has its own fill pattern, the legend shows the same patterns, and the A-Z list repeats everything.
US_MAP = json.loads((ROOT / 'data/us-map.json').read_text(encoding='utf-8'))
SIDE_BOXES = ['VT', 'NH', 'MA', 'RI', 'CT', 'NJ', 'DE', 'MD', 'DC']
LABEL_AT = {'MI': (690, 197), 'FL': (790, 520), 'LA': (566, 470), 'KY': (700, 322), 'ID': (196, 175), 'CA': (76, 290)}
FILLS = {  # tone: (fill color, pattern drawn over it, label color)
    'allowed': ('#2f7d4f', '', '#fff'), 'positive': ('#2f7d4f', '', '#fff'), 'broad': ('#2f7d4f', '', '#fff'),
    'medical-only': ('#387b9c', '<path d="M0 8L8 0" stroke="#fff" stroke-opacity=".45" stroke-width="2"/>', '#fff'),
    'limited': ('#e3b23c', '<circle cx="4" cy="4" r="1.3" fill="#5c4708"/>', '#2a2108'),
    'varies-locally': ('#e3b23c', '<circle cx="4" cy="4" r="1.3" fill="#5c4708"/>', '#2a2108'),
    'partial': ('#e3b23c', '<circle cx="4" cy="4" r="1.3" fill="#5c4708"/>', '#2a2108'),
    'starter': ('#e3b23c', '<circle cx="4" cy="4" r="1.3" fill="#5c4708"/>', '#2a2108'),
    'not-permitted': ('#b4513a', '<path d="M0 0L8 8M8 0L0 8" stroke="#fff" stroke-opacity=".35" stroke-width="1.4"/>', '#fff'),
    'negative': ('#b4513a', '<path d="M0 0L8 8M8 0L0 8" stroke="#fff" stroke-opacity=".35" stroke-width="1.4"/>', '#fff'),
    'not-reviewed': ('#d4d8d5', '', '#2c3531'), 'not-started': ('#d4d8d5', '', '#2c3531')}


def _fill(tone):
    color, pattern, _ = FILLS.get(tone, FILLS['not-reviewed'])
    return f'url(#pt-{tone})' if pattern else color


def map_defs(tones):
    out = []
    for t in sorted(set(tones)):
        color, pattern, _ = FILLS.get(t, FILLS['not-reviewed'])
        if pattern:
            out.append(f'<pattern id="pt-{t}" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="{color}"/>{pattern}</pattern>')
    return '<defs>' + ''.join(out) + '</defs>'


def tile_map(perm, question, answers, caption):
    """Each state colored by its answer to one question; a state with no reviewed answer is grey, never 'prohibited'."""
    names = perm['jurisdictions']
    tally, tones, shapes, labels, boxes = {}, [], [], [], []
    for i, st in enumerate(US_MAP['states']):
        code = st['code']
        a = answers.get(code, {}).get(question['id'])
        status = a['status'] if a else 'not-reviewed'
        tally[status] = tally.get(status, 0) + 1
        tone = tone_of(question, status)
        tones.append(tone)
        short = (a or {}).get('short', '').strip()
        label = status_label(perm, question, status) + (f': {short}' if short and short.rstrip('.').lower() not in ('yes', 'no') else '')
        href = f'{slug(names[code])}.html'
        shapes.append(f'<a href="{href}" class="st {esc(tone)}" data-track="map-state" aria-label="{esc(names[code])}: {esc(label)}">'
                      f'<title>{esc(names[code])}: {esc(status_label(perm, question, status))}</title><path d="{st["d"]}" fill="{_fill(tone)}"/></a>')
        ink = FILLS.get(tone, FILLS['not-reviewed'])[2]
        if code in SIDE_BOXES:
            y = 92 + SIDE_BOXES.index(code) * 40
            boxes.append(f'<a href="{href}" class="st box {esc(tone)}" data-track="map-state" aria-label="{esc(names[code])}: {esc(label)}">'
                         f'<title>{esc(names[code])}: {esc(status_label(perm, question, status))}</title>'
                         f'<rect x="992" y="{y}" width="58" height="32" rx="6" fill="{_fill(tone)}"/>'
                         f'<text x="1021" y="{y + 21}" fill="{ink}" aria-hidden="true">{code}</text></a>')
        else:
            x, y = LABEL_AT.get(code, (st['cx'], st['cy']))
            labels.append(f'<text x="{x}" y="{y + 5}" fill="{ink}">{code}</text>')
    order = [st for st in list(question.get('statuses', {})) + list(perm['statuses']) if st in tally]
    legend = ''.join(f'<li><svg class="swv" width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" focusable="false">'
                     f'<rect width="22" height="22" rx="4" fill="{_fill(tone_of(question, st))}"/></svg>'
                     f'{esc(status_label(perm, question, st))} ({tally[st]})</li>' for st in order)
    svg = (f'<figure class="usvg"><svg viewBox="0 0 1060 {US_MAP["height"]}" role="group" aria-label="{esc(caption)}">'
           + map_defs(tones) + '<g class="shapes">' + ''.join(shapes) + '</g>'
           '<g class="labels" aria-hidden="true">' + ''.join(labels) + '</g>'
           '<g class="boxes">' + ''.join(boxes) + '</g></svg>'
           '<figcaption class="muted">Small states are also in the boxes on the right. Every state is in the A–Z list too.</figcaption></figure>')
    return svg, f'<ul class="legend" aria-label="Map key">{legend}</ul>'


USVG_CSS = (
    '.usvg{margin:10px 0;max-width:820px}.usvg svg{display:block;width:100%;height:auto}'
    '.usvg .st path,.usvg .st rect{stroke:#fff;stroke-width:1;transition:filter .12s}'
    '.usvg .st:hover path,.usvg .st:hover rect{filter:brightness(1.15)}'
    '.usvg .st:focus{outline:none}.usvg .st:focus-visible path,.usvg .st:focus-visible rect{stroke:#111;stroke-width:3.5}'
    '.usvg text{font:700 13px system-ui,sans-serif;text-anchor:middle;pointer-events:none}'
    '.usvg .labels text{paint-order:stroke;stroke:rgba(0,0,0,.25);stroke-width:.6px}'
    '.legend .swv{vertical-align:middle;margin-right:6px;flex:none}'
    '.legend li{display:inline-flex;align-items:center;margin:0 14px 6px 0}'
    '@media (forced-colors:active){.usvg .st path,.usvg .st rect{stroke:CanvasText}.usvg .st:focus-visible path{stroke:Highlight}}'
)
CSS += USVG_CSS


# Visuals on every US page (owner direction, November 25, 2026: "add some reasonable visuals everywhere, at least for
# the US side"). Each one redraws facts the page already states in words, beside those words; none adds a claim.
# - locator(): where the state sits on the same tile map as the home page, its tile carrying its adult-use symbol.
#   The figure is a named image, and its caption says the same in words.
# - the medical card steps (medical_section) are drawn as a numbered stepper; the steps stay an ordered list of
#   the state's own wording, and each step's icon is decoration chosen from words in that step.
# - At a glance is a grid of icon tiles, each tile edged in its answer's tone and carrying its status symbol.
# - law_timeline(): the dates a state's answers give as "in effect", in order, each linking to its answer.
# - question_bar(): on a comparison page, the 51 answers as one bar, its counts also shown as text in the tally.
VISUAL_CSS = '''
.statehead{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,220px);gap:4px 26px;align-items:start}
.locator{margin:10px 0 6px}.lmap{display:grid;grid-template-columns:repeat(11,minmax(0,1fr));gap:2px;max-width:220px}
.lmap span{aspect-ratio:1;border-radius:2px;background:#a9b1ad}
.lmap .here{position:relative;z-index:1;display:grid;place-items:center;border-radius:3px;transform:scale(1.6);box-shadow:0 0 0 1px #13261d;color:#fff}
.lmap .here::before{content:"";width:72%;height:72%;background:currentColor;-webkit-mask:var(--sym) center/contain no-repeat;mask:var(--sym) center/contain no-repeat}
.lmap .here.allowed,.lmap .here.positive{background:#2f7d4f}.lmap .here.medical-only{background:#387b9c}
.lmap .here.limited,.lmap .here.varies-locally,.lmap .here.partial{background:#e3b23c;color:#2a2108}
.lmap .here.not-permitted,.lmap .here.negative{background:#b4513a}.lmap .here.not-reviewed{background:#d4d8d5;color:#3b4541}
.locator figcaption{margin-top:14px;font-size:.88rem;color:var(--soft);line-height:1.5}.locator figcaption strong{color:var(--ink)}
.vsteps{list-style:none;padding:0;margin:12px 0;counter-reset:vst}
.vsteps li{position:relative;display:grid;grid-template-columns:46px minmax(0,1fr);gap:12px;align-items:start;margin:0;padding:0 0 16px;counter-increment:vst}
.vsteps li:not(:last-child)::after{content:"";position:absolute;left:22px;top:48px;bottom:2px;width:2px;background:#6b8796}
.vsteps .sti{position:relative;display:grid;place-items:center;width:46px;height:46px;border-radius:50%;background:#e5f1f7;color:#1d4f68;border:1.5px solid #3b7fa0}
.vsteps .sti svg{width:24px;height:24px}.vsteps .sti::after{content:counter(vst);position:absolute;top:-7px;right:-9px;min-width:22px;height:22px;padding:0 5px;border-radius:11px;background:#1d4f68;color:#fff;font:700 13px/22px system-ui,sans-serif;text-align:center}
.vsteps .stt{padding-top:10px}
.glance{padding:4px 16px 14px}.glance ul{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,230px),1fr));gap:10px;padding:12px 0 0}
.glance li,.glance li:first-child{border:1px solid var(--line);border-top:4px solid #888;border-radius:12px;background:var(--card)}
.glance li.t-allowed,.glance li.t-positive{border-top-color:#2f7d4f}.glance li.t-medical-only{border-top-color:#387b9c}
.glance li.t-limited,.glance li.t-varies-locally,.glance li.t-partial{border-top-color:#b8860b}.glance li.t-not-permitted,.glance li.t-negative{border-top-color:#b4513a}
.glance a,.glance li a{display:flex;flex-direction:column;align-items:flex-start;gap:8px;height:100%;padding:12px 14px}
.glance .qi{width:42px;height:42px;border-radius:12px}.glance .qi svg{width:24px;height:24px}
.glance li.t-partial .qi{background:#fff4dc;color:#664a00}
.tline{margin:14px 0 18px;padding:12px 16px;background:var(--card);border:1px solid var(--line);border-radius:12px;max-width:760px}
.tline figcaption strong{display:block;font-size:1.05rem}.tline figcaption span{display:block;font-size:.88rem;color:var(--soft)}
.tline ol{list-style:none;margin:12px 0 0;padding:0 0 0 6px}.tline li{position:relative;padding:0 0 14px 26px;border-left:2px solid #6b8796}
.tline li:last-child{border-left-color:transparent;padding-bottom:2px}.tline li::before{content:"";position:absolute;left:-8px;top:3px;width:14px;height:14px;border-radius:50%;background:var(--green2);box-shadow:0 0 0 3px var(--card)}
.tline time{display:block;font-weight:750}.tline .tq{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;margin:3px 0}.tline .tq a{display:inline-flex;align-items:center;gap:6px;min-height:32px}
.tline .tq svg{width:18px;height:18px;flex:none;color:var(--green2)}
.spread.solo{margin:14px 0 4px;max-width:640px}.spread.solo .bar{display:flex;gap:2px;min-height:30px;margin-top:8px}
.ih2{display:flex;align-items:center;gap:10px}.ih2 .hi{flex:none;width:38px;height:38px;border-radius:10px;display:grid;place-items:center;background:var(--mint);color:var(--green)}.ih2 .hi svg{width:22px;height:22px}
.stats{list-style:none;padding:0;margin:14px 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr));gap:10px}
.stats li{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);border-left:5px solid var(--green2);border-radius:12px;padding:12px 14px}
.stats .si{flex:none;width:42px;height:42px;border-radius:12px;display:grid;place-items:center;background:var(--mint);color:var(--green)}.stats .si svg{width:24px;height:24px}
.stats strong{display:block;font-size:1.5rem;line-height:1.1}.stats span.l{display:block;font-size:.88rem;color:var(--soft);line-height:1.3}
.need .ni{display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:var(--mint);color:var(--green);margin-bottom:6px}.need .ni svg{width:24px;height:24px}
.scene{display:block;width:100%;max-width:520px;height:auto;margin:6px 0 14px}
@media (prefers-color-scheme:dark){.lmap span{background:#3d4a43}.lmap .here{box-shadow:0 0 0 1px #e6ece8}.vsteps .sti{background:rgba(59,127,160,.28);color:#a9d8ef}.vsteps .sti::after{background:#a9d8ef;color:#10202a}
.glance li.t-partial .qi{background:rgba(184,134,11,.25);color:#f1d48a}.tline .tq svg{color:#a8dfbd}.ih2 .hi,.stats .si,.need .ni{color:#a8dfbd}}
@media(max-width:700px){.statehead{grid-template-columns:1fr}.locator{display:flex;align-items:center;gap:22px}.lmap{width:150px;flex:none}.locator figcaption{margin-top:0}}
@media print{.lmap .here,.vsteps .sti,.vsteps .sti::after,.tline li::before{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
@media (forced-colors:active){.lmap span{forced-color-adjust:none;background:Canvas;border:1px solid GrayText}.lmap .here{background:Highlight;color:HighlightText}
.lmap .here::before{background:HighlightText}.vsteps .sti{border-color:CanvasText}.vsteps .sti::after{forced-color-adjust:none;background:CanvasText;color:Canvas}
.vsteps li:not(:last-child)::after,.tline li::before{forced-color-adjust:none;background:CanvasText}.tline li{border-left-color:CanvasText}.glance li{border-color:CanvasText}}
''' + symbol_rules('here')
CSS += VISUAL_CSS


def locator(perm, code, answers, place):
    """Where the state sits among the 50 states and DC, on the home page's tile map. One tile is drawn in its
    adult-use answer's color and symbol; the caption gives the same answer in words."""
    q = next(x for x in perm['questions'] if x['id'] == 'adult-use')
    a = answers.get(code, {}).get('adult-use')
    status = a['status'] if a else 'not-reviewed'
    tone, label = tone_of(q, status), status_label(perm, q, status)
    cells = ''.join(f'<span class="here {esc(tone)}" style="grid-row:{r + 1};grid-column:{c + 1}"></span>' if k == code
                    else f'<span style="grid-row:{r + 1};grid-column:{c + 1}"></span>'
                    for k, (r, c) in sorted(TILES.items(), key=lambda kv: kv[1]))
    return (f'<figure class="locator"><div class="lmap" role="img" aria-label="Map: {esc(place)} among the 50 states and DC, '
            f'marked {esc(label.lower())} for adult use">{cells}</div>'
            f'<figcaption><strong>{esc(place[0].upper() + place[1:])}</strong> on the US map. Adult use: {chip(perm, status, q)}</figcaption></figure>')


# A step's icon, from the words of the step itself, in this order of preference. Decoration only: the step's
# own words are the content, and a step that matches none of these gets the number alone.
STEP_ICONS = [('doctor', r'physician|doctor|provider|practitioner|pharmacist|clinician|certif|recommendation'),
              ('bag', r'dispensar|\bbuy\b|purchase|treatment center|pharmac'),
              ('form', r'apply|applic|register|registry|portal|account|online|\bform\b|submit'),
              ('card', r'\bcard\b|\bid\b|\bfee|\bpay')]


def step_icon(text):
    for name, words in STEP_ICONS:
        if re.search(words, text, re.I):
            return icon(name)
    return ''


def step_list(items):
    """The state's steps as a numbered stepper: still an ordered list of the state's words, read in order; the
    drawn number and icon are hidden from screen readers, which number the list themselves."""
    return ('<ol class="steps vsteps" role="list">' + ''.join(
        f'<li><span class="sti" aria-hidden="true">{step_icon(x)}</span><span class="stt">{esc(x)}</span></li>' for x in items) + '</ol>')


def law_timeline(perm, state_answers, place):
    """The dates on which a state's answers say a rule took effect, oldest first. Only dates already in the
    answers (effective_on); each entry links to the answer that gives it."""
    by_date = {}
    for q in perm['questions']:
        a = state_answers.get(q['id'])
        if a and a.get('effective_on'):
            by_date.setdefault(a['effective_on'], []).append((q, a))
    if not by_date:
        return ''
    rows = []
    for day in sorted(by_date):
        items = ''.join(f'<span class="tq"><a href="#q-{esc(q["id"])}">{icon(QUESTION_ICON[q["id"]]) if q["id"] in QUESTION_ICON else ""}'
                        f'{esc(LAW_BLURB.get(q["id"], q["question"]))}</a> <span class="muted">{esc(a["citation"])}</span></span>' for q, a in by_date[day])
        rows.append(f'<li><time datetime="{esc(day)}">{long_date(day)}</time>{items}</li>')
    what = 'date' if len(by_date) == 1 else 'dates'
    return (f'<figure class="tline" aria-labelledby="tline-h"><figcaption id="tline-h"><strong>Key {what} in {esc(place)}</strong>'
            '<span>The date each cited law or rule below took effect, as its answer gives it. Select one for the full answer and source.</span></figcaption>'
            f'<ol>{"".join(rows)}</ol></figure>')


def question_bar(perm, question, answers):
    """One comparison question's 51 answers as a single bar, in the home page chart's colors and symbols. The
    counts are in the bar's name and in the tally under the map; the map's key explains each symbol."""
    names = perm['jurisdictions']
    tally = {}
    for code in names:
        a = answers.get(code, {}).get(question['id'])
        st = a['status'] if a else 'not-reviewed'
        tally[st] = tally.get(st, 0) + 1
    order = [st for st in list(question.get('statuses', {})) + list(perm['statuses']) if st in tally]
    order.sort(key=lambda st: SPREAD_ORDER.index(tone_of(question, st)))
    said = [f'{status_label(perm, question, st)} {tally[st]}' for st in order]
    segs = ''.join(f'<span class="seg {esc(tone_of(question, st))}{"" if tally[st] >= 8 else " bare"}" style="flex:{tally[st]} 1 0">'
                   + (f'<span>{tally[st]}</span>' if tally[st] >= 4 else '') + '</span>' for st in order)
    return ('<figure class="spread solo"><figcaption><strong>All the answers in one bar</strong>'
            f'<span class="muted">Each part is one answer, sized by how many of the {len(names)} jurisdictions give it; the number is the count. '
            'The key under the map explains each symbol, and the list below gives every count in words.</span></figcaption>'
            f'<span class="bar" role="img" aria-label="{esc(", ".join(said))}, of {len(names)}">{segs}</span></figure>')


def icon_heading(level, hid, text, name):
    """A section heading with a decorative icon in front; the heading reads exactly as its words."""
    return f'<h{level} id="{esc(hid)}" class="ih2"><span class="hi">{icon(name)}</span>{text}</h{level}>'


def stat_tiles(items, label):
    """Numbers the page already states, as tiles: (icon, number, words). A list, so each reads as one line."""
    return (f'<ul class="stats" aria-label="{esc(label)}">' + ''.join(
        f'<li><span class="si" aria-hidden="true">{icon(name)}</span><span><strong>{esc(n)}</strong> <span class="l">{esc(words)}</span></span></li>'
        for name, n, words in items) + '</ul>')


# The other sites in the same family. Every page links to them.
FAMILY = [
    (OHIO_HOME + '/', 'OhioWeed.org', 'ohioweed.org', 'The complete Ohio guide: business directory, dispensary finder, record clearing and advocacy.'),
    ('https://mobilitytalk.org/', 'Mobility Talk', 'mobilitytalk.org', 'Mobility resources and advocacy for people across the country.'),
    ('https://findbingo.org/', 'Find Bingo', 'findbingo.org', 'Find bingo games and halls near you.'),
    ('https://vethomeguard.org/', 'Veteran Home Guardians', 'vethomeguard.org', 'The veteran nonprofit this work is shared in support of.'),
    ('https://travisvought.com/', 'All sites by Travis Vought', 'travisvought.com', 'Every directory, guide and project in one place.'),
]

def esc(value):
    return html.escape(str(value), quote=True)


def long_date(value):
    d = date.fromisoformat(value)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def load():
    read = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))
    return read('data/state-permissions.json'), read('data/state-scorecard.json'), read('data/directory.json')


def load_landing():
    """Who each fixed page is written for (data/landing-pages.json): titles, openings and the home page's
    "I'm here to…" chooser. State and country openings are composed from each page's own answers instead."""
    return json.loads((ROOT / 'data/landing-pages.json').read_text(encoding='utf-8'))


def for_you(text):
    """The opening written to the person most likely to land on a page. Framing only: facts stay in the cited answers."""
    return f'<p class="lede for-you">{text}</p>'


def more_links(pairs):
    """Next stops for a page's visitor, as pills. Every link goes to a page that already exists."""
    if not pairs:
        return ''
    return '<nav class="pills" aria-label="Also useful">' + ''.join(f'<a class="pill" href="{esc(href)}">{esc(label)}</a>' for label, href in pairs) + '</nav>'


def load_medical():
    """Patient guides for the medical-only states (data/medical-programs.json), keyed by state code."""
    data = json.loads((ROOT / 'data/medical-programs.json').read_text(encoding='utf-8'))
    return data, {p['state']: p for p in data['states']}


# States with their own full guide keep their own store finder; the pipeline list is not shown there.
OWN_STORE_FINDER = {'OH', 'PA', 'NY'}


def load_dispensaries():
    """Regulator-published store lists, keyed by state code.

    data/medical-dispensaries.json holds hand-copied lists for medical-only states;
    data/state-retail-locations.json is written by the source pipeline (pipeline/) from each
    regulator's own list. Where both cover a state, the pipeline copy is used.
    """
    data = json.loads((ROOT / 'data/medical-dispensaries.json').read_text(encoding='utf-8'))
    by_state = {s['state']: s for s in data['states']}
    mined = ROOT / 'data/state-retail-locations.json'
    if mined.exists():
        for s in json.loads(mined.read_text(encoding='utf-8'))['states']:
            if s['state'] not in OWN_STORE_FINDER and s['locations']:
                by_state[s['state']] = {**s, 'source': s['sources'][0]}
    return data, by_state


def dispensary_section(entry, cites, name):
    """The regulator's list as printed: name, address, phone, each row filterable by a typed city or name."""
    src = entry['source']
    srcs = entry.get('sources') or [src]
    dated = f', list dated {long_date(entry["list_date"])}' if entry.get('list_date') else ''
    several_kinds = len({loc.get('kind') for loc in entry['locations']}) > 1
    rows = []
    for loc in entry['locations']:
        extra = [loc[k] for k in ('phone',) if loc.get(k)]
        if loc.get('county'):
            extra.append(f'{loc["county"]} County')
        if loc.get('opened'):
            extra.append(f'open since {loc["opened"]}')
        if several_kinds and loc.get('kind'):
            extra.append(loc['kind'])
        if loc.get('licenses'):
            extra.append(('Licenses ' if len(loc['licenses']) > 1 else 'License ') + ', '.join(loc['licenses']))
        site = f' · <a href="{esc(loc["website"])}" target="_blank" rel="noopener">Website</a>' if loc.get('website') else ''
        licensee = f' <span class="muted">({esc(loc["licensee"])})</span>' if loc.get('licensee') and loc['licensee'] != loc['name'] else ''
        rows.append(f'<li><strong>{esc(loc["name"])}</strong>{licensee}<br>{esc(loc["address"])}<br><span class="muted">{esc(" · ".join(extra))}</span>{site}</li>')
    return (f'<section class="medcard" id="dispensaries" aria-labelledby="dispensaries-h"><h2 id="dispensaries-h">Where to buy in {esc(name)}: the {esc(entry["label"])}</h2>'
            f'<p class="muted">Copied from the regulator’s own {"lists" if len(srcs) > 1 else "list"}{dated}, retrieved {long_date(src["retrieved_on"])} {cites.mark([s["id"] for s in srcs])}. Call ahead: hours and openings change.</p>'
            '<label for="disp-filter">Filter by city or name</label> <input id="disp-filter" type="search" autocomplete="off" style="font:inherit;min-height:44px;padding:6px 10px;border:1px solid #888;border-radius:8px;max-width:100%">'
            f'<ul class="grid" id="disp-list">{"".join(rows)}</ul>'
            '<script>(function(){var f=document.getElementById("disp-filter"),r=document.querySelectorAll("#disp-list li");f.addEventListener("input",function(){var q=f.value.trim().toLowerCase();'
            'for(var i=0;i<r.length;i++)r[i].hidden=q&&r[i].textContent.toLowerCase().indexOf(q)<0})})();</script></section>')


def load_jokes():
    """Jokes the owner has approved, as {ISO date: text} (data/jokes.json). Unapproved jokes are never published."""
    data = json.loads((ROOT / 'data/jokes.json').read_text(encoding='utf-8'))
    return {j['date']: j['text'] for j in data['jokes'] if j.get('approved')}


# Shows the joke for the visitor's own date in the sailor's speech bubble, and on jokes.html the ones that have already
# run. A day with no joke of its own keeps the one before it. Once the batch has run out the list starts over, one a
# day, so the sailors are never left with nothing to say; only approved jokes are ever in the page.
JOKE_SCRIPT = ('<script>(function(){var d=new Date(),t=d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2);'
               'var j=JSON.parse(document.getElementById("jokes-data").textContent),k=Object.keys(j).sort(),p=null,i;'
               'function n(s){var a=s.split("-");return Math.round(Date.UTC(+a[0],a[1]-1,+a[2])/864e5)}'
               'if(k.length&&t>k[k.length-1]){p=k[(n(t)-n(k[k.length-1])-1)%k.length]}else{for(i=0;i<k.length;i++)if(k[i]<=t)p=k[i]}'
               'var box=document.getElementById("joke");if(box&&p){document.getElementById("joke-text").textContent=j[p];box.hidden=false}'
               'var rows=document.querySelectorAll("#joke-list li"),shown=0;for(i=0;i<rows.length;i++)if(rows[i].getAttribute("data-date")<=t){rows[i].hidden=false;shown++}'
               'var none=document.getElementById("joke-none");if(none&&rows.length&&!shown)none.hidden=false})();</script>')


def jokes_data(jokes):
    return '<script type="application/json" id="jokes-data">' + json.dumps(jokes, ensure_ascii=False).replace('</', '<\\/') + '</script>'


def jokes_page(jokes):
    """The running list: every approved joke up to today, newest first. Future jokes stay hidden until their day."""
    rows = ''.join(f'<li data-date="{d}" hidden><span class="muted">{long_date(d)}</span><br>{esc(jokes[d])}</li>' for d in sorted(jokes, reverse=True))
    body = ['<p class="crumbs"><a href="index.html">Home</a> › Joke of the day</p>', '<h1>Joke of the day</h1>',
            '<p class="lede">One cannabis joke a day. Today’s is on the <a href="index.html">home page</a>; the ones that already ran are below, newest first.</p>',
            f'<ul class="jokes" id="joke-list">{rows}</ul>',
            '<p class="muted" id="joke-none"' + ('' if not jokes else ' hidden') + '>No jokes have run yet. Check back tomorrow.</p>',
            jokes_data(jokes), JOKE_SCRIPT]
    return shell('Joke of the day', 'A cannabis joke every day, with the running list of the ones that already ran.', ''.join(body), 'jokes.html', 'the joke of the day page',
                 ld=[breadcrumbs([('Home', '')], 'jokes.html', 'Joke of the day')])


# Sponsored spots (owner's direction, November 19, 2026: the site carries advertising from direct sponsors, kept apart from
# the listings and the law). data/national-sponsors.json is empty by default, and an empty file puts nothing on any page.
# A spot is never placed inside the answers, a listing or the map; it never changes what is listed, how it ranks or what
# a state page says. At most one spot on the home page and one on each state page: the first active entry in file order.
SPONSORS_FILE = ROOT / 'data/national-sponsors.json'
SPONSOR_SLOTS = {'home': 'the home page', 'state': 'state pages'}
SPONSOR_FIELDS = {'id', 'slot', 'sponsor', 'text', 'url', 'image', 'image_alt', 'start', 'end', 'states'}
SPONSOR_TEXT_MAX = 200


def load_sponsors(codes, path=None):
    """Read and check the sponsored spots. A mistake stops the build rather than publishing a broken or misleading spot."""
    data = json.loads(Path(path or SPONSORS_FILE).read_text(encoding='utf-8'))
    rows = data.get('sponsors')
    if not isinstance(rows, list):
        raise SystemExit('data/national-sponsors.json: "sponsors" must be a list (empty when there are none)')
    seen = set()
    for i, s in enumerate(rows):
        where = f'data/national-sponsors.json sponsor {i + 1}'
        if not isinstance(s, dict):
            raise SystemExit(f'{where}: must be an object')
        unknown = set(s) - SPONSOR_FIELDS
        if unknown:
            raise SystemExit(f'{where}: unknown field(s) {sorted(unknown)}')
        for key in ('id', 'slot', 'sponsor', 'text', 'url'):
            if not isinstance(s.get(key), str) or not s[key].strip():
                raise SystemExit(f'{where}: "{key}" is required')
        if s['id'] in seen:
            raise SystemExit(f'{where}: id "{s["id"]}" is used twice')
        seen.add(s['id'])
        if s['slot'] not in SPONSOR_SLOTS:
            raise SystemExit(f'{where}: "slot" must be one of {sorted(SPONSOR_SLOTS)}')
        if len(s['text']) > SPONSOR_TEXT_MAX:
            raise SystemExit(f'{where}: "text" is longer than {SPONSOR_TEXT_MAX} characters')
        if not re.fullmatch(r'https://[^\s"<>]+', s['url']):
            raise SystemExit(f'{where}: "url" must be a full https:// address')
        if 'image' in s:
            # Served from this site, so showing a spot never sends a visitor's browser to the sponsor's server.
            if not re.fullmatch(r'assets/sponsors/[A-Za-z0-9._-]+\.(png|jpg|jpeg|webp|svg)', s['image'] or '') or not (ROOT / s['image']).is_file():
                raise SystemExit(f'{where}: "image" must be a file in assets/sponsors/ (png, jpg, webp or svg)')
            if not isinstance(s.get('image_alt'), str) or not s['image_alt'].strip():
                raise SystemExit(f'{where}: an image needs "image_alt" text')
        elif 'image_alt' in s:
            raise SystemExit(f'{where}: "image_alt" without an image')
        for key in ('start', 'end'):
            if key in s:
                try:
                    date.fromisoformat(s[key])
                except (TypeError, ValueError):
                    raise SystemExit(f'{where}: "{key}" must be a date like 2026-12-31')
        if 'start' in s and 'end' in s and s['start'] > s['end']:
            raise SystemExit(f'{where}: "start" is after "end"')
        if 'states' in s:
            if s['slot'] != 'state':
                raise SystemExit(f'{where}: "states" applies only to the state slot')
            if not isinstance(s['states'], list) or not s['states'] or set(s['states']) - set(codes):
                raise SystemExit(f'{where}: "states" must be a list of state codes such as ["OH", "PA"]')
    return rows


def active_sponsor(sponsors, slot, code=None, today=None):
    """The one spot to show in a slot today, or None. A spot without states runs on every state page."""
    today = (today or date.today()).isoformat()
    for s in sponsors:
        if s['slot'] != slot or s.get('start', today) > today or s.get('end', today) < today:
            continue
        if slot == 'state' and s.get('states') and code not in s['states']:
            continue
        return s
    return None


# The site is rebuilt only when it changes, so a page could outlive a spot's end date: the visitor's own date hides it.
SPONSOR_SCRIPT = ('<script>(function(){var d=new Date(),t=d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2);'
                  'var a=document.querySelectorAll(".ad-slot[data-end]");for(var i=0;i<a.length;i++)if(a[i].getAttribute("data-end")<t)a[i].hidden=true})();</script>')


def sponsor_slot(s):
    """A labeled sponsored spot, or nothing at all when no spot is active."""
    if not s:
        return ''
    image = f'<img src="../{esc(s["image"])}" alt="{esc(s["image_alt"])}" loading="lazy">' if s.get('image') else ''
    end = f' data-end="{esc(s["end"])}"' if s.get('end') else ''
    return (f'<aside class="ad-slot" aria-label="Sponsored" data-sponsor="{esc(s["id"])}"{end}><p class="ad-label">Sponsored</p>'
            f'<a href="{esc(s["url"])}" target="_blank" rel="sponsored noopener" data-track="sponsor:{esc(s["id"])}">{image}'
            f'<span class="ad-text"><strong>{esc(s["sponsor"])}</strong><span>{esc(s["text"])}</span></span></a></aside>'
            + (SPONSOR_SCRIPT if end else ''))


FEATURED_FILE = ROOT / 'data/state-featured.json'


def load_featured(codes, path=None):
    """Groups featured on state pages, only ones that accepted. A mistake stops the build."""
    rows = json.loads(Path(path or FEATURED_FILE).read_text(encoding='utf-8')).get('featured', [])
    out = {}
    for i, f in enumerate(rows):
        where = f'data/state-featured.json entry {i + 1}'
        for key in ('id', 'state', 'name', 'kind', 'text', 'site', 'accepted_on'):
            if not f.get(key):
                raise SystemExit(f'{where}: missing {key}')
        if f['state'] not in codes:
            raise SystemExit(f'{where}: unknown state {f["state"]}')
        urls = [f['site']] + [l['url'] for l in f.get('links', [])] + ([f['donate']] if f.get('donate') else [])
        if any(not u.startswith('https://') for u in urls):
            raise SystemExit(f'{where}: links must be https')
        out.setdefault(f['state'], []).append(f)
    return out


def featured_section(groups, name):
    """The state's featured group, first on the page: their logo, what they do and big links to them.
    Featured with their agreement; not a paid placement and not an endorsement."""
    if not groups:
        return ''
    out = [f'<section class="featured" id="groups" aria-labelledby="groups-h"><p class="feat-label">'
           f'<span aria-hidden="true">{icon("star")}</span>Featured {esc(name)} resource</p>']
    for i, g in enumerate(groups):
        hid = 'groups-h' if i == 0 else f'groups-h{i}'
        logo = (f'<a class="feat-logo" href="{esc(g["site"])}" target="_blank" rel="noopener">'
                f'<img src="../{esc(g["logo"])}" alt="{esc(g.get("logo_alt") or g["name"] + " logo")}" width="309" height="320"></a>'
                if g.get('logo') else '')
        out.append(f'<div class="feat-top">{logo}<div><h2 id="{hid}">Start here: {esc(g["name"])}</h2>'
                   f'<p class="feat-kind">{esc(g["kind"])}</p><p>{esc(g["text"])}</p></div></div>')
        buttons = [(f'Go to {g["name"]}', g['site'], 'link', True)]
        buttons += [(l['label'], l['url'], l.get('icon', 'link'), False) for l in g.get('links', [])]
        if g.get('donate'):
            buttons.append(('Donate to support their work', g['donate'], 'heart', False))
        out.append('<ul class="feat-go">' + ''.join(
            f'<li><a{" class=\"primary\"" if main else ""} href="{esc(u)}" target="_blank" rel="noopener">'
            f'<span aria-hidden="true">{icon(ic)}</span>{esc(label)}</a></li>' for label, u, ic, main in buttons) + '</ul>')
    out.append(f'<p class="muted feat-note">Featured with their agreement, not paid. Our own {esc(name)} guide continues below.</p>')
    return ''.join(out) + '</section>'


# Visitor guides for a city in a state, linked near the top of that state's page (November 27, 2026).
# Each state maps to a list of (page, heading, text), one per guide; California has two.
CITY_GUIDES = {'NV': [('las-vegas.html', 'Visiting Las Vegas?',
                       'Where visitors can and can’t use cannabis: hotels, casinos, cars, Red Rock, Lake Mead and Hoover Dam, plus lounges, driving and flying home.')]}
CITY_GUIDES.update(city_guides.state_boxes())  # CO: Denver, IL: Chicago, NY: New York City, CA: Los Angeles and San Francisco, MI: Detroit, MA: Boston, WA: Seattle, AZ: Phoenix, FL: Miami, OR: Portland, LA: New Orleans, DC: Washington, DC, OH: Columbus, Cleveland, Cincinnati, Dayton, Toledo and Akron
CITY_CSS = ('.cityguide{display:flex;gap:12px;align-items:center;background:var(--card);border:2px solid var(--gold);border-radius:14px;padding:12px 16px;margin:16px 0;max-width:820px}'
            '.cityguide .ci{flex:none;display:grid;place-items:center;width:42px;height:42px;border-radius:10px;background:var(--mint);color:var(--green)}.cityguide .ci svg{width:24px;height:24px}'
            '.cityguide p{margin:0}.cityguide a{font-weight:800;display:inline-flex;min-height:44px;align-items:center}'
            '@media (prefers-color-scheme:dark){.cityguide .ci{color:#a8dfbd}}')


def city_guide(code):
    """The visitor-guide box for a state: one link per city guide, all in one box, then the list of every city guide."""
    if code not in CITY_GUIDES:
        return ''
    guides = CITY_GUIDES[code]
    label = guides[0][1] if len(guides) == 1 else 'Visitor guides: ' + ', '.join(head.removeprefix('Visiting ').rstrip('?') for _, head, _ in guides)
    links = '<br>'.join(f'<a href="{page}">{esc(head)} The rules for visitors</a><br>{esc(text)}' for page, head, text in guides)
    return (f'<aside class="cityguide" aria-label="{esc(label)}"><span class="ci" aria-hidden="true">{icon("pin")}</span>'
            f'<p>{links}<br><a href="{city_guides.HUB}">More city guides: the rules for visitors, city by city</a></p></aside>')


NEIGHBORS_FILE = ROOT / 'data/state-neighbors.json'


def load_neighbors(codes, path=None):
    """{state: (heading, [neighboring states])} from data/state-neighbors.json. Every state and DC must be listed,
    and a border listed for one state must be listed for the other; a mistake stops the build."""
    data = json.loads(Path(path or NEIGHBORS_FILE).read_text(encoding='utf-8'))
    out = {c: ('Nearby states', list(ns)) for c, ns in data['borders'].items()}
    out.update({c: (v['label'], list(v['states'])) for c, v in data['no_land_border'].items()})
    missing, unknown = sorted(set(codes) - set(out)), sorted(set(out) - set(codes))
    if missing or unknown:
        raise SystemExit(f'data/state-neighbors.json: missing {missing}, unknown {unknown}')
    for c, ns in data['borders'].items():
        for n in ns:
            if n not in codes or c not in data['borders'].get(n, []):
                raise SystemExit(f'data/state-neighbors.json: {c} lists {n}, but {n} does not list {c}')
    return out


def nearby_section(perm, code, answers, neighbors):
    """Plain links to the neighboring states' pages, each with its adult-use answer as published there."""
    if not neighbors or code not in neighbors:
        return ''
    label, codes = neighbors[code]
    names = perm['jurisdictions']
    q = next(x for x in perm['questions'] if x['id'] == 'adult-use')
    rows = []
    for c in sorted(codes, key=lambda c: names[c]):
        a = answers.get(c, {}).get('adult-use')
        right = f'{chip(perm, a["status"], q)} <span class="short">{esc(a["short"])}</span>' if a else chip(perm, 'not-reviewed')
        rows.append(f'<li><a class="state" href="{slug(names[c])}.html">{esc(names[c])}</a><span>{right}</span></li>')
    place = 'The District of Columbia' if code == 'DC' else names[code]
    lead = 'The law can change at the state line.' if label == 'Nearby states' else f'{place} shares no land border with another state.'
    return (f'<section aria-labelledby="nearby"><h2 id="nearby">{esc(label)}</h2>'
            f'<p>{esc(lead)} Each of these pages answers the same {len(perm["questions"])} questions, with sources. '
            'Shown here: whether adults 21 and older can use cannabis without a medical card.</p>'
            '<ul class="rows nearby">' + ''.join(rows) + '</ul></section>')


# The national pages a state page sends visitors on to, picked by what the state allows. Each one covers every state.
TOPIC_LINKS = {
    'possession': ('law-possession.html', 'Possession limits in every state', 'how much an adult can have'),
    'employment': ('law-employment.html', 'Worker protections in every state', 'whether off-the-job use can cost you a job'),
    'record-relief': ('law-record-relief.html', 'Clearing a cannabis record in every state', 'sealing and expungement'),
    'medical-cards': ('medical.html', 'Medical card guides, state by state', 'who qualifies, the steps and the cost'),
    'medical': ('law-medical.html', 'Medical programs in every state', 'which states have one and how broad it is'),
    'travel': ('help.html#travel', 'Flying with cannabis', 'what TSA says'),
}
TOPICS_BY_STATUS = {'allowed': ('possession', 'employment', 'record-relief'),
                    'medical-only': ('medical-cards', 'employment', 'record-relief')}
TOPICS_OTHERWISE = ('medical', 'record-relief', 'possession')


def topic_links(adult_status):
    picks = TOPICS_BY_STATUS.get(adult_status, TOPICS_OTHERWISE) + ('travel',)
    return ''.join(f'<li><a href="{TOPIC_LINKS[k][0]}">{esc(TOPIC_LINKS[k][1])}</a>: {esc(TOPIC_LINKS[k][2])}</li>' for k in picks)


def load_coverage():
    """Who pays for medical cannabis (data/medical-coverage.json)."""
    return json.loads((ROOT / 'data/medical-coverage.json').read_text(encoding='utf-8'))


MEDICAL_ROWS = [('who', 'Who can get one'), ('fee', 'Cost'), ('fee_help', 'Help with the cost'), ('card_length', 'How long it lasts'), ('caregivers', 'Caregivers'),
                ('visitors', 'Visiting patients'), ('buy', 'Where patients buy')]


def medical_section(prog, cites, name, medical_only=True):
    """How patients get a card, each fact marked with its regulator source."""
    out = [f'<section class="medcard" id="medical-card" aria-labelledby="medical-card-h"><h2 id="medical-card-h">How patients get a medical card in {esc(name)}</h2>',
           f'<p class="muted">From {esc(prog["agency"])}. ' + ('Adults without a card cannot buy here.' if medical_only else 'Adults 21 and older can also buy without a card; see the answers below.') + '</p>']
    if prog.get('note'):
        out.append(f'<p class="mednote">{esc(prog["note"]["text"])} {cites.mark([prog["note"]["source"]])}</p>')
    if prog.get('steps'):
        out.append('<h3>Steps</h3>' + step_list(prog['steps']['items'])
                   + f'<p class="muted">Steps as the state describes them {cites.mark([prog["steps"]["source"]])}</p>')
    rows = [(label, prog[key]) for key, label in MEDICAL_ROWS if prog.get(key)]
    if rows:
        out.append('<dl class="facts">' + ''.join(f'<dt>{esc(label)}</dt><dd>{esc(f["text"])} {cites.mark([f["source"]])}</dd>' for label, f in rows) + '</dl>')
    missing = [label for key, label in MEDICAL_ROWS if not prog.get(key) and key != 'fee_help']
    if missing:
        out.append(f'<p class="muted">Not stated on the state pages we checked: {esc(", ".join(m.lower() for m in missing))}. Check with the state.</p>')
    out.append('<p><a href="coverage.html">Does Medicaid, Medicare or insurance pay for it?</a></p>')
    out.append('<p class="medlinks">' + ''.join(f'<a class="pill" href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["label"])}</a>' for l in prog['links']) + '</p>')
    out.append('</section>')
    return ''.join(out)


# Owner direction, November 26, 2026: point people to the best existing resources instead of pretending to be
# the best at everything. Links only, no affiliation or payment. Completeness was checked against the regulator's
# own store list where this site has one (data/outside-guides.json says how).
GUIDES_FILE = ROOT / 'data/outside-guides.json'
GUIDE_ORDER = ('leafly', 'weedmaps', 'mpp', 'norml_laws', 'norml_lawyers')


def load_guides(path=None):
    data = json.loads((path or GUIDES_FILE).read_text(encoding='utf-8'))
    for code, st in data['states'].items():
        for key, url in st['links'].items():
            if key not in data['guides'] or not url.startswith('https://'):
                raise ValueError(f'outside guide {key} for {code} must be a known guide with an https address')
    return data


def reuse_offer(place='this'):
    """The free and open source offer (owner direction, November 26, 2026), with a way to reach Travis."""
    return (f'<p class="reuse"><strong>Free and open source.</strong> Run a {esc(place)} guide or group of your own? Copy anything on The Reefer '
            f'that helps you, and Travis will help you set it up for free: <a href="mailto:{EMAIL}">email {EMAIL}</a> or '
            f'<a href="{REPO}">get the code on GitHub</a>.</p>')


def guides_section(data, code, name):
    st = (data or {}).get('states', {}).get(code)
    if not st or not st['links']:
        return ''
    counts, full = st['counts'], data['complete_at']
    reg = counts.get('regulator')

    def note(key):
        n = counts.get(key)
        if not (reg and n):
            return '', 0
        share = n / reg
        if share >= full:
            return f'Lists about as many stores as the state’s own list ({n:,} vs {reg:,}).', share
        return f'Lists fewer stores than the state’s own list ({n:,} vs {reg:,}), so check the state’s list too.', share

    stores = sorted((k for k in ('leafly', 'weedmaps') if k in st['links']), key=lambda k: -note(k)[1])
    items = []
    for key in stores + [k for k in GUIDE_ORDER if k not in ('leafly', 'weedmaps') and k in st['links']]:
        g = data['guides'][key]
        text, share = note(key)
        best = ' <span class="og-best">Most complete store finder we checked</span>' if key == (stores[0] if stores else None) and share >= full else ''
        items.append(f'<li><a href="{esc(st["links"][key])}" target="_blank" rel="noopener"><strong>{esc(g["name"])}</strong>'
                     f'<span>{esc(g["what"])}</span></a>{best}' + (f'<p class="muted">{esc(text)}</p>' if text else '') + '</li>')
    when = long_date(data['checked_on'])
    return (f'<section class="og" id="other-guides" aria-labelledby="og-h"><h2 id="og-h">{icon("link")} Other good guides for {esc(name)}</h2>'
            '<p>Other sites already do some of this well, so use them too. We don’t run them and they don’t pay us.</p>'
            f'<ul class="og-list">{"".join(items)}</ul>'
            f'<p class="muted">Links and store counts checked {when}. Counts are rough: a site may include delivery services, and a state list can lag.</p>'
            + reuse_offer(name) + '</section>')


def correction_url(place):
    body = 'Page or state:\r\n\r\nAddition or correction:\r\n\r\nWebsite or source:\r\n\r\n'
    return 'mailto:' + EMAIL + '?' + urlencode({'subject': f'{SITE_NAME}: correction for {place}', 'body': body}, quote_via=quote)


def page_url(name):
    return ORIGIN + '/' + ('' if name == 'index.html' else name)


def json_ld(nodes):
    """Structured data for search engines. Only text already shown on the page; absolute URLs need ORIGIN."""
    if not ORIGIN or not nodes:
        return ''
    data = {'@context': 'https://schema.org', '@graph': nodes}
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return f'<script type="application/ld+json">{text}</script>'


def breadcrumbs(trail, name, title):
    """BreadcrumbList matching the visible crumbs: trail is [(label, page)], the current page comes last."""
    items = [{'@type': 'ListItem', 'position': i, 'name': label, 'item': ORIGIN + '/' + page}
             for i, (label, page) in enumerate(trail, 1)]
    items.append({'@type': 'ListItem', 'position': len(items) + 1, 'name': title, 'item': page_url(name)})
    return {'@type': 'BreadcrumbList', '@id': page_url(name) + '#breadcrumb', 'itemListElement': items}


def website_node():
    return {'@type': 'WebSite', '@id': ORIGIN + '/#website', 'url': ORIGIN + '/', 'name': SITE_NAME,
            'alternateName': 'The-Reefer.com', 'description': TAGLINE, 'inLanguage': 'en-US',
            'license': 'https://creativecommons.org/licenses/by/4.0/',
            'creator': {'@type': 'Person', 'name': 'Travis Vought', 'url': 'https://travisvought.com/'}}


def shell(title, description, body, name, place, hero='', ld=None, css=''):
    head = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark">',
            f'<title>{esc(title)} | {esc(SITE_NAME)}</title>',
            f'<meta name="description" content="{esc(description)}">',
            '<meta name="theme-color" content="#1d4a37">',
            f'<link rel="icon" type="image/png" href="{ASSETS}favicon-64.png"><link rel="apple-touch-icon" href="{ASSETS}apple-touch-icon.png">',
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(SITE_NAME)}">',
            f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}">']
    if ORIGIN:
        href = page_url(name)
        head.append(f'<link rel="canonical" href="{esc(href)}"><meta property="og:url" content="{esc(href)}">'
                    f'<meta property="og:image" content="{ORIGIN}/assets/the-reefer/logo-share.jpg"><meta property="og:image:width" content="1200">'
                    f'<meta property="og:image:height" content="800"><meta property="og:image:alt" content="{esc(LOGO_ALT)}"><meta name="twitter:card" content="summary_large_image">')
    else:
        head.append('<meta name="robots" content="noindex,follow">')
    if ld and ORIGIN:
        head.append(json_ld(ld))
    head.append(f'<style>{CSS}{css}</style></head><body>')
    top = (f'<header class="site"><div class="wrap"><a class="brand" href="index.html" aria-label="{esc(SITE_NAME)} home"><img src="{ASSETS}mark-96.png" alt="" width="40" height="40"><span>{esc(SITE_NAME)}</span></a>'
           '<nav aria-label="Primary"><a href="index.html#map">Your state</a><a href="medical.html">Medical cards</a><a href="index.html#compare">Compare laws</a>'
           '<a href="world.html">World</a><a href="learn.html">101</a><a href="help.html">Get help</a><a href="about.html">About</a>'
           # Owner's request, November 26, 2026 (round 4): make the pirate game easy to find from every page.
           '<a class="play" href="../pillage/"><span aria-hidden="true">🏴‍☠️</span> Play our game</a></nav></div></header>')
    family = ''.join(f'<li><a href="{esc(url)}">{esc(label)}</a></li>' for url, label, _, _ in FAMILY)
    foot = ('<footer class="site"><div class="wrap"><div class="cols">'
            '<nav aria-label="This site"><h2>This site</h2><ul><li><a href="index.html#map">Pick your state</a></li>'
            '<li><a href="index.html#compare">Compare the law</a></li><li><a href="medical.html">Medical cards</a></li><li><a href="coverage.html">Medicaid and insurance</a></li><li><a href="help.html">Get help</a></li><li><a href="weed-santa.html">Weed Santa</a></li><li><a href="world.html">Around the world</a></li><li><a href="learn.html">Cannabis 101</a></li><li><a href="hash-myths.html">Hash myths, busted</a></li><li><a href="heritage.html">Where weed comes from</a></li><li><a href="travel-warnings.html">Travel warnings</a></li><li><a href="jokes.html">Joke of the day</a></li><li><a href="../pillage/">Pillage the Reefer (a game)</a></li><li><a href="partners.html">Partners</a></li><li><a href="about.html">About and methods</a></li><li><a href="privacy.html">Privacy</a></li></ul></nav>'
            f'<nav aria-label="Our other sites"><h2>Our other sites</h2><ul>{family}</ul></nav>'
            '<nav aria-label="Corrections and data"><h2>Fix or reuse</h2><ul>'
            f'<li><a href="{esc(correction_url(place))}">Suggest a correction</a></li>'
            f'<li><a href="{REPO}#readme">Methods &amp; sources</a></li>'
            f'<li><a href="{REPO}/blob/main/architecture/STATE_COMPLETION_STANDARD.md">State completion standard</a></li>'
            '<li><a href="about.html#reuse">Copy anything here, free</a></li></ul></nav></div>'
            f'<p class="foot-reuse"><strong>Free and open source.</strong> Anyone may copy what’s on this site for their own site or group, and Travis will help you set it up: <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>'
            '<p>Summaries of the cited sources, each with the date it was checked. Not legal advice. A missing answer means not yet reviewed, '
            'never that something is prohibited. Free to use under CC BY 4.0. Created and maintained by Travis Vought, shared in support of Veteran Home Guardians. '
            f'Giving Tuesday is December 1: <a href="{GIVING_TUESDAY}">give to Veteran Home Guardians</a>.</p></div></footer>')
    from a11y import finish  # a skip link and less motion when the visitor's device asks
    return finish(''.join(head) + top + hero + '<main>' + body + '</main>' + foot + '<script src="../assets/analytics.js" defer></script></body></html>\n')

class Cites:
    """Per-page source numbering, in order of first use."""

    def __init__(self, sources):
        self.sources, self.order = sources, []

    def mark(self, ids):
        out = []
        for sid in ids:
            if sid not in self.order:
                self.order.append(sid)
            n = self.order.index(sid) + 1
            out.append(f'<a href="#source-{n}" aria-label="Source {n}">[{n}]</a>')
        return '<span class="cites">' + ''.join(out) + '</span>'

    def render(self):
        if not self.order:
            return ''
        out = ['<h2 id="sources">Sources</h2><ol class="sources">']
        for n, sid in enumerate(self.order, 1):
            s = self.sources[sid]
            out.append(f'<li id="source-{n}"><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a> · {esc(s["publisher"])} · '
                       f'{esc(KIND_LABEL[s["kind"]])} · retrieved {long_date(s["retrieved_on"])}</li>')
        out.append('</ol>')
        return ''.join(out)


def answers_by_state(perm):
    out = {}
    for a in perm['answers']:
        out.setdefault(a['state'], {})[a['question']] = a
    return out


def pack_link(code, pack, pathway_id):
    """Where a built pathway lives today. Ohio is published at ohioweed.org; pilots use the shared state page."""
    if code == 'OH':
        url = next((p.get('public_url') for p in pack['pathways'] if p['pathway_id'] == pathway_id), None)
        return (OHIO_HOME + (urlparse(url).path.replace('/index.html', '/') or '/') + ('#' + urlparse(url).fragment if urlparse(url).fragment else '')
                if url and url.startswith(DEFAULT_SITE_ORIGIN) else OHIO_HOME + '/')
    return f'../state.html?state={code}&pathway={pathway_id}'


def law_section(perm, code, state_answers, cites, sources):
    name = perm['jurisdictions'][code]
    out = [f'<h2 id="law">The law in {esc(name)}</h2>',
           f'<p>The same {len(perm["questions"])} questions are asked of every state. Each answer names its source and the date it was checked.</p>',
           law_timeline(perm, state_answers, 'the District of Columbia' if code == 'DC' else name)]
    for group in perm['groups']:
        out.append(f'<h3>{esc(group["label"])}</h3>')
        for q in (q for q in perm['questions'] if q['group'] == group['id']):
            a = state_answers.get(q['id'])
            note = f'<p class="muted">{esc(q["note"])}</p>' if q.get('note') else ''
            if not a:
                out.append(f'<article class="card" id="q-{esc(q["id"])}" data-question="{esc(q["id"])}"><h4>{esc(q["question"])}</h4>{note}'
                           f'<p>{chip(perm, "not-reviewed")} <span class="muted">No reviewed source yet. This does not mean it is prohibited.</span></p></article>')
                continue
            level = evidence_level(a, sources)
            effective = f' · in effect {long_date(a["effective_on"])}' if a.get('effective_on') else ''
            out.append(f'<article class="card" id="q-{esc(q["id"])}" data-question="{esc(q["id"])}"><h4>{esc(q["question"])}</h4>{note}'
                       f'<p>{chip(perm, a["status"], q)} <span class="short">{esc(a["short"])}</span></p><p>{esc(a["detail"])}</p>'
                       f'<p class="muted">{esc(a["citation"])}{effective} · checked {long_date(a["reviewed_on"])} {cites.mark(a["source_ids"])} '
                       f'<span class="level {esc(level)}">{esc(LEVEL_TEXT[level])}</span></p></article>')
    return ''.join(out)


def pathway_section(code, name, pathways, card, pack):
    out = [f'<h2 id="directory">Directory and local help in {esc(name)}</h2>']
    if card:
        out.append(f'<p>{esc(name)} has a {esc(PACK_LABEL[card["publication_status"]].lower())}. Levels are earned from the data under the '
                   f'<a href="{REPO}/blob/main/architecture/STATE_COMPLETION_STANDARD.md">state completion standard</a>; none of the levels means exhaustive coverage.</p>')
    else:
        out.append(f'<p>The {esc(name)} directory has not been started. Ohio is the template: these are the seven parts every state guide is built toward. '
                   '“Not started” means no records have been reviewed yet, not that help does not exist. '
                   '<a href="help.html">National resources that cover every state</a> are available now.</p>')
    for p in pathways:
        row = (card or {}).get('pathways', {}).get(p['id'])
        if row:
            nxt = f'<p class="muted">Next level needs: {esc(row["next"])}</p>' if row.get('next') else ''
            out.append(f'<article class="card" data-pathway="{esc(p["id"])}"><h3><a href="{esc(pack_link(code, pack, p["id"]))}">{esc(p["label"])}</a></h3>'
                       f'<p><span class="chip {esc(row["level"])}">{esc(LEVELS[row["level"]])}</span> {esc(p["task"])}</p>{nxt}</article>')
        else:
            out.append(f'<article class="card" data-pathway="{esc(p["id"])}"><h3>{esc(p["label"])}</h3>'
                       f'<p><span class="chip not-started">Not started</span> {esc(p["task"])}</p></article>')
    return ''.join(out)


def glance(perm, state_answers, name):
    """Every question in one short list, each linking to its full answer below. No new wording: the short answer as published."""
    rows = []
    for i, q in enumerate(perm['questions']):
        a = state_answers.get(q['id'])
        right = (f'{chip(perm, a["status"], q)} {esc(a["short"])}' if a else chip(perm, 'not-reviewed'))
        tone = tone_of(q, a['status']) if a else 'not-reviewed'
        ic = f'<span class="qi">{icon(QUESTION_ICON[q["id"]])}</span>' if q['id'] in QUESTION_ICON else ''
        rows.append(f'<li class="t-{esc(tone)}" style="--i:{i}"><a href="#q-{esc(q["id"])}"><span class="q">{ic}{esc(LAW_BLURB.get(q["id"], q["question"]))}</span><span>{right}</span></a></li>')
    total, done = len(perm['questions']), sum(1 for q in perm['questions'] if q['id'] in state_answers)
    meter = (f'<p class="meter"><span class="bar" role="img" aria-label="{done} of {total} questions answered"><span class="fill" style="width:{round(100 * done / total)}%"></span></span>'
             f'<span>{done} of {total} answered from named sources</span></p>')
    return (f'<section class="glance" id="glance" aria-label="{esc(name)} at a glance"><div class="glance-head"><h2>At a glance</h2>{meter}</div><ul>'
            + ''.join(rows) + '</ul></section>')


def state_page(perm, score, directory, code, answers, sources, medical=None, dispensaries=None, sponsors=(), featured=None, guides=None, neighbors=None):
    name = perm['jurisdictions'][code]
    groups = (featured or {}).get(code, [])
    state_answers = answers.get(code, {})
    cites = Cites(sources)
    card = score['states'].get(code)
    pack = next((s for s in directory['states'] if s['code'] == code), None)
    place = 'the District of Columbia' if code == 'DC' else name
    prog = (medical or {}).get(code)
    shops = (dispensaries or {}).get(code)
    body = [f'<p class="crumbs"><a href="index.html#map">All states</a> › {esc(name)}</p>',
            f'<h1>Is weed legal in {esc(place)}?</h1>', short_answer(place, state_answers, cites),
            '<div class="statehead"><div>', for_you(state_intro(code, place, state_answers, prog, shops))]
    lede = [f'{label}: {chip(perm, a["status"], q)} {esc(a["short"])}' for label, q, a in
            (('Adult use', q, state_answers.get(q['id'])) if q['id'] == 'adult-use' else ('Medical use', q, state_answers.get(q['id']))
             for q in perm['questions'] if q['id'] in ('adult-use', 'medical')) if a]
    if lede:
        body.append('<p class="lede">' + '<br>'.join(lede) + '</p>')
    link = perm['official_links'].get(code)
    if link:
        s = sources[link['source_id']]
        body.append(f'<p>Official state site: <a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a> '
                    f'<span class="muted">({esc(s["publisher"])}, checked {long_date(s["retrieved_on"])})</span></p>')
    else:
        body.append('<p>Official state site: <span class="muted">not yet reviewed</span></p>')
    body.append('</div>' + locator(perm, code, answers, place) + '</div>')
    body.append(featured_section(groups, name))
    body.append(city_guide(code))
    if code == 'OH':
        body.append(f'<p><strong>Ohio’s full guide lives at <a href="{OHIO_HOME}/">OhioWeed.org</a></strong>: business directory, dispensary finder, record clearing, advocacy and more.</p>')
    body.append(guides_section(guides, code, name))
    # What the visitor most likely came for comes first: where adults can buy the store list, elsewhere the medical card.
    adult_status = state_answers.get('adult-use', {}).get('status')
    card_html = medical_section(prog, cites, name, adult_status == 'medical-only') if prog else ''
    card_link = '<a href="#medical-card">Get a medical card</a>' if prog else ''
    shop_link = ''
    stores_first = adult_status == 'allowed'
    if shops:
        shop_link = '<a href="#dispensaries">Where to buy</a>'
    first, second = ((shop_link, card_link) if stores_first else (card_link, shop_link))
    body.append('<nav class="onpage" aria-label="On this page">' + first + second
                + ('<a href="#groups">Local groups</a>' if groups else '') + ('<a href="#other-guides">Other guides</a>' if (guides or {}).get('states', {}).get(code, {}).get('links') else '') + '<a href="#glance">At a glance</a><a href="#law">The law in detail</a>' + (f'<a href="#nearby">{esc(neighbors[code][0])}</a>' if (neighbors or {}).get(code) else '')
                + '<a href="#directory">Local help</a><a href="#sources">Sources</a></nav>')
    if stores_first and shops:
        body.append(dispensary_section(shops, cites, name))
    body.append(card_html)
    if shops and not stores_first:
        body.append(dispensary_section(shops, cites, name))
    body.append(glance(perm, state_answers, name))
    body.append(law_section(perm, code, state_answers, cites, sources))
    body.append(nearby_section(perm, code, answers, neighbors))
    body.append(pathway_section(code, name, directory['pathways'], card, pack))
    # After the main content, outside the answers and the directory cards.
    body.append(sponsor_slot(active_sponsor(sponsors, 'state', code)))
    guide = (f'<li><a href="{guide_link(code, name)}">The full {esc(name)} guide</a>: directory and local help</li>' if card else '')
    body.append(f'<aside class="next" aria-label="Where to go next"><h2>Where to go next</h2><ul>{guide}'
                + topic_links(adult_status) +
                '<li><a href="help.html">National help</a>: travel, veterans, legal aid, health and safety</li>'
                '<li><a href="index.html#compare">Compare a rule across every state</a></li>'
                '<li><a href="index.html#map">Pick another state</a></li></ul></aside>')
    body.append(cites.render())
    answered = len(state_answers)
    short = {k: state_answers[k]['short'].rstrip('.') for k in ('adult-use', 'medical') if k in state_answers}
    description = state_description(place, state_answers, answered, len(perm['questions']), bool(shops))
    year = (state_answers.get('adult-use') or {}).get('reviewed_on', perm.get('as_of', ''))[:4]
    page, title = slug(name) + '.html', state_title(name, place, adult_status, prog, shops, year)
    ld = [breadcrumbs([('All states', '')], page, name)]
    faq = faq_node(perm, state_answers, page)
    if faq:
        ld.append(faq)
    return shell(title, description, ''.join(body), page, name, ld=ld, css=CITY_CSS if code in CITY_GUIDES else '')


def state_title(name, place, adult_status, prog, shops, year=''):
    """The tab and search title: the question people ask, the year its answer was checked, then what this page leads with."""
    ask = f'Is weed legal in {place}?' + (f' ({year})' if year else '')
    if adult_status == 'allowed' and shops:
        return f'{ask} Where to buy and the rules'
    if adult_status == 'medical-only' and prog:
        return f'{ask} How to get a medical card'
    return f'{ask} {name} cannabis laws'


def answer_link(state_answers, qid):
    """A state's own short answer, word for word, linked to its full answer and source further down the page."""
    a = state_answers.get(qid)
    return f'<a href="#q-{esc(qid)}">{esc(a["short"].rstrip("."))}</a>' if a else ''


def state_intro(code, place, state_answers, prog, shops):
    """The opening for a state page, written to someone in that state or headed there.

    Built only from what the page itself shows: the state's own cited short answers (linked to their
    full answer and source), the regulator's store list and the medical card guide. A state with
    different answers gets different words; nothing here is a claim the page does not already cite."""
    link = lambda qid: answer_link(state_answers, qid)
    adult = state_answers.get('adult-use')
    status = adult['status'] if adult else None
    record = link('record-relief')
    record_line = f'Old cannabis record holding you back? In {esc(place)}: {record}.' if record else ''
    if status == 'allowed':
        facts = [f'{label}: {link(q)}' for label, q in (('Buy', 'buying'), ('Carry', 'possession'), ('Grow at home', 'home-grow')) if link(q)]
        first = (f'If you are 21 or older in {esc(place)}, here is the short version. ' + ' · '.join(facts) + '.' if facts
                 else f'Adults 21 and older can use cannabis in {esc(place)}: {link("adult-use")}.')
        if shops:
            second = f'Start with the <a href="#dispensaries">list of {esc(shops["label"])}</a> just below to find one near you; every rule after it links to its source.'
        elif code == 'OH':
            second = f'Ohio’s dispensary finder, business directory and record-clearing guide are on <a href="{OHIO_HOME}/">OhioWeed.org</a>.'
        else:
            second = record_line
        return f'{first} {second}'.strip()
    if status == 'medical-only':
        first = f'In {esc(place)}, only registered patients can buy and use cannabis, so for most people the first step is a medical card.'
        if prog:
            # Name only the facts the state's guide actually gives, in the order a patient needs them.
            parts = [label for key, label in (('who', 'who qualifies'), ('steps', 'the steps'), ('fee', 'what it costs'),
                                              ('fee_help', 'help with the cost'), ('buy', 'where patients buy')) if prog.get(key)]
            listed = (', '.join(parts[:-1]) + ' and ' + parts[-1]) if len(parts) > 1 else (parts[0] if parts else 'the card rules')
            where = f', followed by the <a href="#dispensaries">list of {esc(shops["label"])}</a>' if shops else ''
            second = (f'{listed[0].upper() + listed[1:]}, as the state regulator ({esc(prog["agency"])}) gives them, '
                      f'{"are" if len(parts) > 1 else "is"} <a href="#medical-card">just below</a>{where}.')
        else:
            second = f'Medical program: {link("medical")}.' if link('medical') else ''
        return ' '.join(x for x in (first, second, record_line) if x)
    medical = link('medical')
    if status == 'not-permitted':
        first = f'Adult use is not legal in {esc(place)}' + (f'. Medical: {medical}.' if medical else '.')
    elif status:
        first = f'Adult use in {esc(place)}: {link("adult-use")}.' + (f' Medical: {medical}.' if medical else '')
    else:
        first = f'Here is what is known so far about cannabis law in {esc(place)}, each answer with its source.'
    if record:
        second = f'If an old cannabis charge is what brought you here, the route in {esc(place)} is: {record}.'
    elif prog:
        second = 'Patients: the medical card steps are <a href="#medical-card">just below</a>.'
    else:
        second = ''
    return f'{first} {second}'.strip()


def state_lead(place, state_answers):
    """The plain yes / medical only / no answer to "Is weed legal in ...?", built only from the
    state's own cited short answers for adult and medical use. None when adult use is not reviewed."""
    adult = state_answers.get('adult-use')
    if not adult:
        return None
    med = state_answers.get('medical')
    a_short, status = adult['short'].rstrip('.'), adult['status']
    m_short, m_status = (med['short'].rstrip('.'), med['status']) if med else (None, None)
    if status == 'allowed':
        if a_short == 'Yes, 21 and older':
            return f'Yes. Weed is legal in {place} for adults 21 and older' + (', and for medical patients.' if m_status == 'allowed' else '.')
        return f'Yes. Adult use in {place}: {a_short}.'
    if status == 'medical-only':
        detail = m_short and not m_short.lower().startswith('yes')
        return f'Only with a medical card. Recreational weed is not legal in {place}' + (f'; medical: {m_short}.' if detail else ', but medical cannabis is.')
    if status == 'not-permitted' and m_status == 'not-permitted':
        return f'No. Weed is not legal in {place}, and there is no medical marijuana law.'
    if status == 'not-permitted':
        return f'No. Weed is not legal in {place}. Medical use: {m_short or "a narrow program only"}.'
    return f'Adult use in {place}: {a_short}.' + (f' Medical: {m_short}.' if m_short else '')


def short_answer(place, state_answers, cites):
    """The answer box under the heading: the plain answer, then the law it rests on and the date it was checked."""
    lead = state_lead(place, state_answers)
    if not lead:
        return ''
    a = state_answers['adult-use']
    return (f'<div class="answer" role="note" aria-label="Short answer"><p><strong>Short answer:</strong> {esc(lead)}</p>'
            f'<p class="muted">Checked {long_date(a["reviewed_on"])} against {esc(a["citation"])} {cites.mark(a["source_ids"])}</p></div>')


def state_description(place, state_answers, answered, total, has_stores=False):
    """The search-result snippet for a state page: the answer first, in plain words,
    then the details people look for next. Built only from the short answers shown on the page."""
    def short(q):
        a = state_answers.get(q)
        return (a['short'].rstrip('.'), a['status']) if a else (None, None)
    adult, adult_status = short('adult-use')
    med, med_status = short('medical')
    med_detail = med and not med.lower().startswith('yes')
    if adult_status == 'allowed':
        lead = state_lead(place, state_answers)
        extra = []
        for q, label in (('possession', 'Limit'), ('home-grow', 'Home grow')):
            text, status = short(q)
            if text and status in ('allowed', 'limited'):
                extra.append(f'{label}: {text[0].lower() + text[1:]}.')
        rest = ' '.join(extra) or 'Where to buy, limits and driving rules, with official sources.'
        if has_stores:
            rest = (rest + ' Plus the regulator’s own store list.').strip()
    elif adult_status == 'medical-only':
        lead = f'Only with a medical card. Recreational weed is not legal in {place}' + (f'; medical: {med}.' if med_detail else ', but medical cannabis is.')
        rest = 'How to get a medical card, who qualifies and the rules, with official sources.' + (' Plus where patients buy.' if has_stores else '')
    elif adult_status == 'not-permitted' and med_status == 'not-permitted':
        lead = f'No. Weed is not legal in {place}, and there is no medical marijuana law.'
        rest = 'Driving, work and record-clearing rules, with official sources.'
    elif adult_status == 'not-permitted':
        lead = f'No. Weed is not legal in {place}. Medical use: {med or "a narrow program only"}.'
        rest = 'Driving, work and record-clearing rules, with official sources.'
    else:
        lead = f'Is weed legal in {place}? Adult use: {adult or "not yet reviewed"}. Medical: {med or "not yet reviewed"}.'
        rest = f'{answered} of {total} questions answered from official sources.'
    return f'{lead} {rest}'


def faq_node(perm, state_answers, page):
    """The answered law questions as FAQPage data: the question, short answer, detail and citation shown on the page."""
    entries = []
    for q in perm['questions']:
        a = state_answers.get(q['id'])
        if not a:
            continue
        effective = f', in effect {long_date(a["effective_on"])}' if a.get('effective_on') else ''
        text = (f'{a["short"].rstrip(".")}. {a["detail"]} '
                f'Source: {a["citation"]}{effective}, checked {long_date(a["reviewed_on"])}.')
        entries.append({'@type': 'Question', 'name': q['question'], 'acceptedAnswer': {'@type': 'Answer', 'text': text}})
    if not entries:
        return None
    return {'@type': 'FAQPage', '@id': page_url(page) + '#law', 'url': page_url(page),
            'isPartOf': {'@id': ORIGIN + '/#website'}, 'mainEntity': entries}


NEED_BLURB = {
    'Federal law': 'Where federal scheduling stands',
    'State laws': 'A national guide to each state’s laws and penalties',
    'Travel': 'What the TSA says about flying',
    'Patients traveling': 'Using a medical card away from home',
    'Veterans': 'VA care and state cannabis programs',
    'Legal help': 'Find free civil legal aid',
    'Record clearing': 'National guides to sealing and expungement',
    'Contact lawmakers': 'Find your state legislators by address',
    'Health and safety': 'Poison Help and the national helpline',
    'Business': 'The national industry association',
}
LAW_BLURB = {
    'adult-use': 'Is adult use legal?',
    'medical': 'Is there a medical program?',
    'buying': 'Where adults can buy',
    'possession': 'How much an adult can have',
    'sharing': 'Sharing and gifting',
    'home-grow': 'Growing at home',
    'public-use': 'Using it in public',
    'driving': 'Driving rules',
    'employment': 'Work and off-the-job use',
    'record-relief': 'Clearing a past record',
}


SPREAD_CSS = '''
/* The comparison chart on the home page (spread_chart): one bar per question, one segment per answer, 51 jurisdictions each. */
.spread{margin:22px 0 6px;max-width:860px}.spread figcaption strong{display:block;font-size:1.1rem}.spread figcaption span{display:block}
.spread ol{list-style:none;margin:12px 0;padding:0;display:grid;gap:9px}.spread ol>li{display:grid;grid-template-columns:minmax(0,14.5em) minmax(0,1fr);gap:3px 14px;align-items:center}
.spread .sq{font-weight:650;line-height:1.3}.spread .bar{display:flex;gap:2px;min-height:30px}
.spread .seg{display:flex;align-items:center;justify-content:center;gap:4px;min-width:3px;overflow:hidden;border-radius:4px;color:#fff;font-weight:800;font-size:.88rem;line-height:1}
.spread .seg.allowed,.spread .seg.positive{background:#2f7d4f}.spread .seg.medical-only{background:#387b9c}
.spread .seg.limited,.spread .seg.varies-locally,.spread .seg.partial{background:#e3b23c;color:#2a2108}.spread .seg.not-permitted,.spread .seg.negative{background:#b4513a}
.spread .seg.not-reviewed{background:#d4d8d5;color:#3b4541}.spread .seg.bare::before{display:none}
/* The light segments get a darker edge, so every bar stands out 3:1 from the page (WCAG 1.4.11). */
.spread .seg.limited,.spread .seg.varies-locally,.spread .seg.partial{box-shadow:inset 0 0 0 1.5px #8a6a12}.spread .seg.not-reviewed{box-shadow:inset 0 0 0 1.5px #6b7470}
.spread details{margin:6px 0}.spread summary{cursor:pointer;font-weight:700;color:var(--link);min-height:44px;display:flex;align-items:center}.spread td,.spread th{font-size:.92rem}
@media (prefers-color-scheme:dark){.spread .seg.not-reviewed{background:#3a4640;color:#d7ddd9;box-shadow:inset 0 0 0 1.5px #8a9690}}
@media (forced-colors:active){.spread .seg{forced-color-adjust:none;background:Canvas;color:CanvasText;border:1px solid CanvasText}}
@media(max-width:560px){.spread ol>li{grid-template-columns:1fr}}
@media print{.spread .seg{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
'''


SPREAD_ORDER = ['allowed', 'positive', 'medical-only', 'limited', 'varies-locally', 'partial', 'not-permitted', 'negative', 'not-reviewed']


def spread_chart(perm, answers):
    """How the 50 states and DC answer each question: one bar per question, one segment per answer, sized by
    how many jurisdictions give it. Owner direction, November 24, 2026: visuals that carry information. Nothing
    new is said: the counts are the same answers each law page maps and lists, and the table under the chart
    gives every number as text. Unreviewed states are counted as "Not yet reviewed", never as a "no"."""
    names = perm['jurisdictions']
    total = len(names)
    rows, table, keyed = [], [], {}
    for q in perm['questions']:
        tally = {}
        for code in names:
            a = answers.get(code, {}).get(q['id'])
            st = a['status'] if a else 'not-reviewed'
            tally[st] = tally.get(st, 0) + 1
        order = [st for st in list(q.get('statuses', {})) + list(perm['statuses']) if st in tally]
        # Like answers sit together: yes, then medical only, then limited, then no, then not yet reviewed.
        order.sort(key=lambda st: SPREAD_ORDER.index(tone_of(q, st)))
        said = [f'{status_label(perm, q, st)} {tally[st]}' for st in order]
        segs = []
        for st in order:
            tone, n = tone_of(q, st), tally[st]
            keyed.setdefault(tone, [])
            if status_label(perm, q, st) not in keyed[tone]:
                keyed[tone].append(status_label(perm, q, st))
            # Room for a symbol and the count only where the segment is wide enough to hold them.
            inside = f'<span>{n}</span>' if n >= 4 else ''
            segs.append(f'<span class="seg {esc(tone)}{"" if n >= 8 else " bare"}" style="flex:{n} 1 0">{inside}</span>')
        label = esc(LAW_BLURB.get(q['id'], q['question']))
        rows.append(f'<li><a class="sq" href="{law_page_name(q["id"])}">{label}</a>'
                    f'<span class="bar" role="img" aria-label="{esc(", ".join(said))}, of {total}">{"".join(segs)}</span></li>')
        table.append(f'<tr><th scope="row">{label}</th><td>{esc(" · ".join(said))}</td></tr>')
    families = [('allowed', 'positive'), ('medical-only',), ('limited', 'varies-locally', 'partial'), ('not-permitted', 'negative'), ('not-reviewed',)]
    key = []
    for fam in families:
        labels = [lab for tone in fam for lab in keyed.get(tone, [])]
        if labels:
            key.append(f'<li><span class="sw {fam[0]}"></span>{esc(" / ".join(labels))}</li>')
    assert all(any(t in fam for fam in families) for t in keyed), 'a status tone has no place in the chart key'
    return ('<figure class="spread" id="spread"><figcaption><strong>How the 50 states and DC answer each question</strong>'
            f'<span class="muted">Each bar is all {total} jurisdictions, split by their answer; the number is how many give it. '
            f'Select a question for the map and the list. From the answers on each state’s page, each with its own source, as of {long_date(perm["as_of"])}.</span></figcaption>'
            '<ol>' + ''.join(rows) + '</ol>'
            '<ul class="legend" aria-label="Chart key">' + ''.join(key) + '</ul>'
            '<details><summary>Chart data as a table</summary><div class="scroll"><table><caption class="muted">Number of jurisdictions giving each answer, '
            f'as of {long_date(perm["as_of"])}</caption><thead><tr><th scope="col">Question</th><th scope="col">Answers</th></tr></thead><tbody>'
            + ''.join(table) + '</tbody></table></div></details></figure>')


def law_page_name(question_id):
    return f'law-{question_id}.html'


def needs_in_order(perm):
    seen = []
    for item in perm['national']:
        if item['need'] not in seen:
            seen.append(item['need'])
    return seen


def status_label(perm, question, status):
    own = question.get('statuses', {}).get(status)
    return own['label'] if own else perm['statuses'][status]


# One icon per need on the help page, from the same set as the home page cards. A need without one shows none.
# ICON_HEAD_CSS styles an icon in front of a heading (.ih .hi) or inside a pill (.pi); Cannabis 101 uses it too.
NEED_ICON = {'Federal law': 'capitol', 'State laws': 'scale', 'Travel': 'plane', 'Patients traveling': 'card', 'Veterans': 'star',
             'Legal help': 'gavel', 'Record clearing': 'record', 'Contact lawmakers': 'megaphone', 'Health and safety': 'phone',
             'Business': 'briefcase'}
ICON_HEAD_CSS = ('.pill .pi{display:grid;color:var(--green2)}.pill .pi svg{width:20px;height:20px}'
            '.ih{display:flex;align-items:center;gap:10px}.ih .hi{flex:none;width:38px;height:38px;border-radius:10px;display:grid;place-items:center;'
            'background:var(--mint);color:var(--green)}.ih .hi svg{width:22px;height:22px}'
            '@media (prefers-color-scheme:dark){.pill .pi,.ih .hi{color:#a8dfbd}}')


def need_icon(need, cls):
    return f'<span class="{cls}">{icon(NEED_ICON[need])}</span>' if need in NEED_ICON else ''


def help_page(perm, sources):
    cites = Cites(sources)
    land = load_landing()['national_pages']['help.html']
    body = ['<p class="crumbs"><a href="index.html">Home</a> › Help by need</p>', '<h1>Help by need</h1>', for_you(esc(land['intro'])),
            '<p>Federal rules, national help lines and organizations that cover every state. Each links to the agency or organization that runs it. '
            'A listing is not an endorsement; advocacy groups are named as such. For state-specific help, <a href="index.html#map">pick your state</a>.</p>',
            '<p><strong>In Ohio and can\'t afford cannabis you need?</strong> <a href="weed-santa.html">Weed Santa</a> matches adults 21 and over with vetted gifters who give a legal amount for free.</p>',
            '<nav class="pills" aria-label="Jump to a need">' + ''.join(f'<a class="pill" href="#{slug(n)}">{need_icon(n, "pi")}{esc(n)}</a>' for n in needs_in_order(perm)) + '</nav>']
    for need in needs_in_order(perm):
        body.append(f'<h2 id="{slug(need)}" class="ih">{need_icon(need, "hi")}{esc(need)}</h2>')
        for i in (i for i in perm['national'] if i['need'] == need):
            body.append(f'<article class="card" data-national="{esc(i["id"])}"><h3><a href="{esc(i["url"])}" target="_blank" rel="noopener">{esc(i["title"])}</a></h3>'
                        f'<p>{esc(i["text"])}</p><p class="muted">Checked {long_date(i["reviewed_on"])} {cites.mark(i["source_ids"])}</p></article>')
    body.append(cites.render())
    return shell(land['title'], 'National cannabis help lines, federal rules and organizations that cover every state, grouped by what you need.',
                 ''.join(body), 'help.html', 'the help page', ld=[breadcrumbs([('Home', '')], 'help.html', 'Help by need')], css=ICON_HEAD_CSS)


def medical_page(perm, med_data, medical, answers, sources, dispensaries=None):
    """Medical cards state by state: medical-only states first, each with cost, visitors and a link to its full patient guide."""
    names = perm['jurisdictions']
    grid, legend = tile_map(perm, next(x for x in perm['questions'] if x['id'] == 'adult-use'), answers,
                            'Map: adult use and medical-only states. Select a state to open its guide.')
    only = {c for c in medical if answers.get(c, {}).get('adult-use', {}).get('status') == 'medical-only'}
    body = ['<p class="crumbs"><a href="index.html">Home</a> › Medical cards</p>',
            '<h1>Getting a medical cannabis card, state by state</h1>',
            for_you(esc(load_landing()['national_pages']['medical.html']['intro'])),
            f'<p>In {len(only)} states, medical cannabis is legal but adult use is not, so a state card is the only legal way to buy. '
            'Each state below links to its patient guide: who qualifies, the steps, the cost and whether visiting patients can buy. Every fact comes from the state regulator.</p>',
            f'<div class="mapbox"><div>{grid}{legend}</div><div><h2 style="margin-top:0">Medical-only states</h2><p class="muted">Blue on the map. '
            f'Patient facts checked {long_date(med_data["as_of"])}.</p></div></div>',
            '<div class="guides">']
    def guide(code):
        prog = medical[code]
        bits = [f'Cost: {prog["fee"]["text"]}' if prog.get('fee') else '', f'Visitors: {prog["visitors"]["text"]}' if prog.get('visitors') else '',
                prog['note']['text'] if prog.get('note') and not prog.get('steps') else '']
        if (dispensaries or {}).get(code):
            bits.append(f'Store list: the {dispensaries[code]["label"]}')
        if not any(bits):
            bits = [f'Where patients buy: {prog["buy"]["text"]}' if prog.get('buy') else f'Who: {prog["who"]["text"]}']
        return (f'<a class="guide" href="{slug(names[code])}.html#medical-card"><strong>{esc(names[code])}</strong>'
                + ''.join(f'<span>{esc(b)}</span>' for b in bits if b) + '</a>')
    body.append(''.join(guide(c) for c in sorted(only, key=lambda c: names[c])) + '</div>')
    limited = sorted(c for c in names if answers.get(c, {}).get('medical', {}).get('status') == 'limited')
    if limited:
        body.append('<h2>States with narrow programs</h2><p>These states allow only low-THC oil or CBD for certain conditions. Open a state to read its answer and source.</p><ul class="pills" style="list-style:none;padding:0">'
                    + ''.join(f'<li><a class="pill" href="{slug(names[c])}.html#q-medical">{esc(names[c])} <small>{esc(answers[c]["medical"]["short"])}</small></a></li>' for c in limited) + '</ul>')
    body.append('<h2>Paying for it</h2><p>Medicaid, Medicare and insurance generally do not pay for medical cannabis, but some states cut the card fee. '
                '<a href="coverage.html">See who pays and where the card costs less</a>.</p>')
    body.append('<h2>States where adults can buy</h2><p>Every adult-use state also has a medical program, often with lower taxes or higher limits for patients. '
                'Patient guides so far:</p><div class="guides">' + ''.join(guide(c) for c in sorted(set(medical) - only, key=lambda c: names[c]))
                + '</div><p><a href="law-medical.html">See every state’s medical program on one page</a>.</p>')
    body.append('<p class="muted">Summaries of state regulator pages, each linked on the state’s page. Not medical or legal advice. A blank fact means the state page we checked did not say.</p>')
    title = 'How to get a medical cannabis card in each state'
    return shell(title, 'How patients get a medical cannabis card in each medical-only state: who qualifies, steps, cost and visiting-patient rules, from state regulators.',
                 ''.join(body), 'medical.html', 'the medical cards page', ld=[breadcrumbs([('Home', '')], 'medical.html', 'Medical cards')])


def law_page(perm, question, answers, sources, dispensaries=None):
    names = perm['jurisdictions']
    land = load_landing()['law_pages'].get(question['id'], {})
    total = len(names)
    rows, tally = [], {}
    for code in sorted(names, key=lambda c: names[c]):
        a = answers.get(code, {}).get(question['id'])
        page = slug(names[code]) + '.html'
        if not a:
            tally['not-reviewed'] = tally.get('not-reviewed', 0) + 1
            rows.append(f'<li data-state="{esc(code)}" data-status="not-reviewed"><a class="state" href="{page}">{esc(names[code])}</a>'
                        f'<span>{chip(perm, "not-reviewed")} <span class="muted">No reviewed source yet. This does not mean it is prohibited.</span></span></li>')
            continue
        tally[a['status']] = tally.get(a['status'], 0) + 1
        level = evidence_level(a, sources)
        rows.append(f'<li data-state="{esc(code)}" data-status="{esc(a["status"])}"><a class="state" href="{page}">{esc(names[code])}</a>'
                    f'<span>{chip(perm, a["status"], question)} <span class="short">{esc(a["short"])}</span></span>'
                    f'<p class="meta">Checked {long_date(a["reviewed_on"])} · {esc(LEVEL_TEXT[level])} · <a href="{page}#law">details and source</a></p></li>')
    order = [st for st in list(question.get('statuses', {})) + list(perm['statuses']) if st in tally]
    options = ''.join(f'<option value="{esc(st)}">{esc(status_label(perm, question, st))} ({tally[st]})</option>' for st in order)
    chips = ' '.join(f'<span>{chip(perm, st, question)} {tally[st]}</span>' for st in order)
    note = f'<p class="muted">{esc(question["note"])}</p>' if question.get('note') else ''
    answered = total - tally.get('not-reviewed', 0)
    map_grid = ''.join(tile_map(perm, question, answers, f'Map: {question["question"]} Select a state to open its guide.'))
    stores = ''
    if question['id'] == 'buying' and dispensaries:
        # The buyer's next step: the state pages that carry the regulator's own store list.
        stores = ('<h2 id="store-lists">States with the regulator’s store list</h2><nav class="pills" aria-label="State store lists">'
                  + ''.join(f'<a class="pill" href="{slug(names[c])}.html#dispensaries">{esc(names[c])}</a>' for c in sorted(dispensaries, key=lambda c: names[c]))
                  + '</nav>')
    body = ['<p class="crumbs"><a href="index.html">Home</a> › <a href="index.html#compare">Compare the law</a></p>',
            f'<h1>{esc(question["question"])}</h1>',
            for_you(esc(land['intro'])) if land.get('intro') else '', stores, more_links(land.get('more')),
            f'<p>Every state and DC, side by side. {answered} of {total} are answered from a named source; open a state for the full answer, its citation and its source.</p>{note}',
            question_bar(perm, question, answers), map_grid, '<p class="muted">Tap a state for its full answer and source, or use the list below.</p>',
            f'<h2 id="list">Every state in a list</h2><div class="tally">{chips}</div>',
            f'<label for="status-filter">Show</label> <select id="status-filter"><option value="">All {total}</option>{options}</select>',
            '<ul class="rows" id="rows">' + ''.join(rows) + '</ul>',
            '<script>(function(){var f=document.getElementById("status-filter");f.addEventListener("change",function(){'
            'document.querySelectorAll("#rows li").forEach(function(li){li.hidden=!!f.value&&li.getAttribute("data-status")!==f.value})})})();</script>']
    description = f'{question["question"]} All 50 states and DC compared, each answer traced to a named source and the date it was checked.'
    if land.get('intro') and len(land['intro']) <= 240:
        description = land['intro'] + ' All 50 states and DC, each answer sourced and dated.'
    page = law_page_name(question['id'])
    ld = [breadcrumbs([('Home', ''), ('Compare the law', '#compare')], page, question['question'])]
    return shell(land.get('title') or question['question'], description, ''.join(body), page, 'the state comparison', ld=ld, css=SPREAD_CSS)


def progress_section(perm, score, directory, answers):
    pathways = directory['pathways']
    total = len(perm['questions'])
    full = sum(len(answers.get(c, {})) == total for c in perm['jurisdictions'])
    out = [icon_heading(2, 'progress', 'Build progress', 'chart'),
           f'<p>Ohio is the template. Every state is built toward the same seven-part guide and measured by the same standard. '
           f'{full} of {len(perm["jurisdictions"])} jurisdictions have all {total} law questions answered; '
           f'{len(score["states"])} have a state guide. Scorecard as of {long_date(score["as_of"])}.</p>',
           '<div class="scroll"><table><thead><tr><th scope="col">State guide</th>']
    out += [f'<th scope="col">{esc(p["label"])}</th>' for p in pathways]
    out.append('</tr></thead><tbody>')
    for code, card in score['states'].items():
        out.append(f'<tr><th scope="row"><a href="{slug(card["name"])}.html">{esc(card["name"])}</a> <span class="muted">({esc(card["publication_status"])})</span></th>')
        out += [f'<td><span class="chip {esc(card["pathways"][p["id"]]["level"])}">{esc(LEVELS[card["pathways"][p["id"]]["level"]])}</span></td>' for p in pathways]
        out.append('</tr>')
    out.append('</tbody></table></div><p class="muted">Every other state shows “Not started” for these seven parts until its records are reviewed.</p>')
    return ''.join(out)


# Other open projects that collect related cannabis data, linked from the About page so people can find the data
# without anyone collecting it twice (owner direction, November 24, 2026). Name, URL, one sentence.
RELATED_PROJECTS = [
    ('Cannlytics cannabis license data', 'https://huggingface.co/datasets/cannlytics/cannabis_licenses',
     'open licensee data for about 21 states under CC BY 4.0; Ohio isn’t included yet.'),
    ('PDAPS Retail Marijuana Laws', 'https://pdaps.org/datasets/retail-marijuana-laws',
     'coded state retail cannabis laws from Temple University’s Center for Public Health Law Research, CC BY 4.0, current through March 2024.'),
    ('Collateral Consequences Resource Center', 'https://ccresourcecenter.org/marijuana-decriminalization-drives-expungement-reform/',
     'a national comparison of marijuana record clearing by state.'),
    ('Massachusetts Cannabis Control Commission open data', 'https://masscannabiscontrol.com/open-data/data-catalog/',
     'the state’s licensee data as downloadable files.'),
]
DATA_CREDIT = 'Ohio Cannabis Ecosystem Directory, compiled by Travis Vought.'  # the required attribution in LICENSE


def open_data_section():
    mail = 'mailto:' + EMAIL + '?' + urlencode({'subject': f'{SITE_NAME}: linking open datasets'}, quote_via=quote)
    return ('<h2 id="open-data" class="ih"><span class="hi">' + icon('swap') + '</span>Open data, and projects like this one</h2>'
            '<p>The directory’s listings are open data under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license">CC BY 4.0</a>. '
            'Anyone may copy and reuse them, with credit, so nobody has to collect the same listings twice. '
            f'The credit to use is “{esc(DATA_CREDIT)}” '
            f'The files are in <a href="{REPO}">the directory’s repository on GitHub</a>.</p>'
            '<h3 id="related">Related open projects</h3><ul>'
            + ''.join(f'<li><a href="{esc(url)}" target="_blank" rel="noopener">{esc(name)}</a> (new tab): {esc(line)}</li>'
                      for name, url, line in RELATED_PROJECTS) +
            f'</ul><p>Maintain a similar dataset? Write to us at <a href="{esc(mail)}">{esc(EMAIL)}</a> and we’ll link to each other.</p>')


def about_page(perm, score, directory, answers):
    total_answers = len(perm['answers'])
    body = ['<p class="crumbs"><a href="index.html">Home</a> › About</p>', f'<h1>About {esc(SITE_NAME)}</h1>',
            f'<p>{esc(SITE_NAME)} is a free cannabis information and resource portal for all 50 states and DC. It grew out of the Ohio Cannabis Directory at '
            f'<a href="{OHIO_HOME}/">OhioWeed.org</a>, which is the template every state is built toward.</p>',
            icon_heading(2, 'method', 'How the information is checked', 'check'),
            f'<p>Every answer names its source and the date it was checked. The site holds {total_answers} reviewed answers from {len(perm["sources"])} sources, as of {long_date(perm["as_of"])}. Each answer carries one of three labels:</p><ul>'
            + ''.join(f'<li><span class="level {esc(k)}">{esc(v)}</span></li>' for k, v in LEVEL_TEXT.items()) +
            '</ul><p>A missing answer reads “Not yet reviewed”. It never means something is prohibited. Summaries are not legal advice; the linked source is the authority.</p>',
            stat_tiles([('check', total_answers, 'reviewed answers'), ('book', len(perm['sources']), 'named sources'),
                        ('pin', len(perm['jurisdictions']), 'states and DC, the same questions for each'),
                        ('form', len(perm['questions']), 'law questions asked of every state')], f'The site in numbers, as of {long_date(perm["as_of"])}'),
            icon_heading(2, 'rules', 'Ground rules', 'scale') + '<ul><li>No paid placement, paid ranking or paid verification.</li>'
            '<li>The site carries advertising from direct sponsors. Sponsored spots are labeled “Sponsored”, sit apart from listings and answers, and never change what’s listed, how it ranks, or what a state page says. <a href="partners.html#sponsor">How sponsoring works</a>.</li>'
            '<li>State laws are presented side by side and factually. The site does not rank states or say which approach is better.</li>'
            '<li>Nonpartisan: every party and lawmaker is treated the same way.</li></ul>',
            progress_section(perm, score, directory, answers),
            open_data_section(),
            icon_heading(2, 'reuse', 'Free and open source: copy anything', 'link') +
            '<p>Everything on The Reefer is free and open source. If you run a guide, a group or a business site and something here would help '
            'your visitors, copy it: the pages, the data and the code that builds them. You don’t need to ask, and you don’t need to send traffic back. '
            'We link other good guides on every state page for the same reason: the more people find good information, the better.</p>'
            + reuse_offer('state or local') +
            icon_heading(2, 'corrections', 'Corrections and reuse', 'mail') +
            f'<p>Found something wrong or out of date? <a href="{esc(correction_url("the site"))}">Send a correction</a> with a link to the source. '
            f'Everything here is free to use under CC BY 4.0, and the data and build scripts are public on <a href="{REPO}">GitHub</a>.</p>'
            '<p>How visits are counted and what the site keeps: <a href="privacy.html">Privacy</a>.</p>'
            '<p>Created and maintained by Travis Vought, shared in support of Veteran Home Guardians.</p>']
    return shell(f'About {SITE_NAME}', f'How {SITE_NAME} checks its information, what its labels mean, how far each state guide has been built, and how to send a correction.',
                 ''.join(body), 'about.html', 'the site', ld=[breadcrumbs([('Home', '')], 'about.html', 'About')], css=ICON_HEAD_CSS)


PRIVACY_UPDATED = '2026-11-26'
PRIVACY_STATEMENT = 'https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement'


def privacy_page():
    """What the site counts and keeps, in plain words. Keep it true to assets/analytics.js and to the pages' own scripts:
    the national pages set no cookies and use no browser storage, and nothing typed into a filter or the letter builder leaves the page."""
    contact = 'mailto:' + EMAIL + '?' + urlencode({'subject': f'{SITE_NAME}: privacy question'}, quote_via=quote)
    body = ['<p class="crumbs"><a href="index.html">Home</a> › Privacy</p>', '<h1>Privacy</h1>',
            f'<p class="muted">Last updated {long_date(PRIVACY_UPDATED)}.</p>',
            f'<p class="lede">{esc(SITE_NAME)} does not ask who you are, apart from the optional prize contest in its game. It counts visits without cookies, keeps nothing you type, '
            'shares nothing about you with sponsors and sells no personal information.</p>',
            '<ul class="stats" aria-label="In short">' + ''.join(f'<li><span class="si" aria-hidden="true">{icon(n)}</span><span class="l">{t}</span></li>' for n, t in (
                ('chart', 'Visits counted without cookies'), ('lock', 'Nothing you type is kept'), ('tag', 'Nothing about you shared with sponsors'),
                ('receipt', 'No personal information sold'))) + '</ul>',
            icon_heading(2, 'counting', 'Counting visits', 'chart') + ''
            '<p>Visits are counted with <a href="https://www.goatcounter.com/">GoatCounter</a>. It sets no cookies and stores no personal information. '
            'For each page view it records the page, the site you came from, your browser and screen size, and an approximate country worked out from '
            'your IP address. It does not store the IP address.</p>'
            '<p>The counter also tallies which links and buttons are used, such as a state on the map, the name of another website a link leads to, '
            'or that a filter was used. It never records what you type. The results are seen as totals, not as a record of any one visitor.</p>',
            icon_heading(2, 'hosting', 'Hosting', 'server') + ''
            '<p>The site is hosted on GitHub Pages. Like any web host, GitHub receives your IP address when your browser asks for a page, and GitHub may '
            f'keep server logs, including IP addresses, for security. See the <a href="{PRIVACY_STATEMENT}">GitHub General Privacy Statement</a>.</p>',
            icon_heading(2, 'map', 'Maps', 'pin') + ''
            '<p>Some pages show stores on a map, such as Ontario’s cannabis stores and Amsterdam’s coffeeshops. The map’s code is served from this site, '
            'but the street pictures come from <a href="https://www.openstreetmap.org/">OpenStreetMap</a> (tile.openstreetmap.org). To show them, your browser '
            'asks OpenStreetMap for the pictures of the area you look at, so OpenStreetMap sees your IP address and which area you view, under the '
            '<a href="https://osmfoundation.org/wiki/Privacy_Policy">OpenStreetMap Foundation privacy policy</a>. Pages without a map do not contact it.</p>'
            '<p>The “near me” button asks your browser for your location only when you press it, and your browser asks you first. If you allow it, '
            'the page uses it to center the map and list the closest stores. Your location is never stored or sent to this site. The map then shows '
            'your area, so OpenStreetMap is asked for the pictures of that area, as for any area you look at.</p>',
            icon_heading(2, 'typing', 'What you type or choose', 'lock') + ''
            '<p>The state picker, the filters, the maps and the letter builder work inside your browser. What you type there is not sent to this site '
            'and is not saved: it is gone when you close the page. The pages do not use cookies or your browser’s storage.</p>'
            '<p>If you email a correction or a question, we receive your message and your email address and use them only to answer you and fix the page.</p>',
            icon_heading(2, 'sponsors', 'Sponsors', 'tag') + ''
            '<p>Sponsored spots are labeled “Sponsored” and link to the sponsor’s own site. Their pictures are served from this site, so seeing a spot '
            'does not contact the sponsor. Once you follow a sponsor’s link, that site’s privacy rules apply. This site does not share visitor '
            'information with sponsors. See <a href="partners.html#sponsor">how sponsoring works</a>.</p>',
            icon_heading(2, 'game', 'The game and its Silver Cup', 'star') + ''
            '<p>Pillage the Reefer saves your voyage in your browser, on your device. Nothing about a regular voyage is sent to this site. '
            'If you enter the Silver Cup, the game’s prize contest, it sends your captain name, your crew or business name and your email to the '
            'Cup’s server, which runs on Cloudflare, along with the recorded moves of your Cup runs, so each run can be replayed and checked and the '
            'winners reached. Captain names, crews and scores are shown on the public contest boards. Emails are never shown or shared, are used only '
            'to contact you about the Cup, and are wiped 60 days after it closes, by February 3, 2027. To limit how many runs one network starts, the '
            'server keeps a scrambled form of your IP address that changes every day, and drops it the next day.</p>'
            '<p>While you sail a Cup run with live captains on, as they are unless you turn them off in the game’s Settings, the server passes your '
            'ship’s position, captain name and crew to the other Cup players sailing, and keeps none of it. Like any web host, Cloudflare sees your IP '
            'address when the game talks to the Cup’s server. See the <a href="../pillage/contest-rules.html#privacy">contest rules</a>.</p>',
            icon_heading(2, 'other-sites', 'Links to other sites', 'link') + ''
            '<p>Answers link to state agencies, laws and organizations, and to our other sites. Each has its own privacy rules once you are there.</p>',
            icon_heading(2, 'audience', 'Who this site is for', 'people') + ''
            '<p>This site is for adults 21 and older. It is not directed to children, and we do not knowingly collect information from children. '
            'We do not sell personal information.</p>',
            icon_heading(2, 'contact', 'Questions', 'mail') + ''
            f'<p><a href="{esc(contact)}">Email a privacy question</a>. If this page changes, the date at the top changes with it.</p>']
    return shell('Privacy', f'How {SITE_NAME} counts visits without cookies, what it keeps (nothing you type), how sponsors are handled and who the site is for.',
                 ''.join(body), 'privacy.html', 'the privacy page', ld=[breadcrumbs([('Home', '')], 'privacy.html', 'Privacy')])


# What a visitor came for, each with one place to go. Help-page needs are linked by their section.
# A decorative icon in front of each coverage question (data/medical-coverage.json); a new question shows none.
COVERAGE_ICON = {'medicaid': 'people', 'medicare': 'person', 'insurance': 'shield', 'va': 'star', 'fda-drugs': 'pill', 'taxes': 'receipt'}


def coverage_page(perm, medical, sources):
    """Who pays for medical cannabis, question by question, then the states that lower the card fee."""
    data, names, cites = load_coverage(), perm['jurisdictions'], Cites(sources)
    body = ['<p class="crumbs"><a href="index.html">Home</a> › <a href="medical.html">Medical cards</a> › Medicaid and insurance</p>',
            '<h1>Does Medicaid, Medicare or insurance pay for medical cannabis?</h1>',
            for_you(esc(load_landing()['national_pages']['coverage.html']['intro'])),
            '<p class="short">Short answer: patients pay for dispensary cannabis themselves. What can change is the cost of the card, '
            'and a few cannabis medicines are ordinary prescriptions. Each answer below comes from the agency’s own page.</p>',
            '<nav class="pills" aria-label="On this page">' + ''.join(f'<a class="pill" href="#{esc(i["id"])}">{esc(i["question"])}</a>' for i in data['items'])
            + '<a class="pill" href="#fee-help">Card fee help by state</a></nav>']
    for item in data['items']:
        ic = f'<span class="hi">{icon(COVERAGE_ICON[item["id"]])}</span>' if item['id'] in COVERAGE_ICON else ''
        body.append(f'<article class="card" id="{esc(item["id"])}"><h2 class="ih2" style="margin:.2em 0">{ic}{esc(item["question"])}</h2><p class="short">{esc(item["short"])}</p><ul>')
        for point in item['points']:
            body.append(f'<li>{esc(point["text"])}' + (f' {cites.mark([point["source"]])}' if point['source'] else '') + '</li>')
        body.append('</ul></article>')
    helped = sorted((c for c in medical if medical[c].get('fee_help')), key=lambda c: names[c])
    body.append(icon_heading(2, 'fee-help', 'Card fee help by state', 'card') + '<p>States that lower or waive the patient card fee for people on Medicaid or with low income, and for veterans, '
                'among the state programs reviewed so far.</p><ul class="rows">')
    for code in helped:
        f = medical[code]['fee_help']
        body.append(f'<li><a class="state" href="{slug(names[code])}.html#medical-card">{esc(names[code])}</a><span>{esc(f["text"])} {cites.mark([f["source"]])}</span></li>')
    body.append('</ul><p class="muted">A state missing from this list has not been reviewed for fee help yet, or its regulator page did not state any. '
                f'Checked {long_date(data["as_of"])}. Not medical, legal or tax advice.</p>')
    body.append('<aside class="next"><h2>Where to go next</h2><ul><li><a href="medical.html">How to get a medical card in your state</a></li>'
                '<li><a href="help.html#veterans">Veterans: VA care and state programs</a></li><li><a href="index.html#map">Pick your state</a></li></ul></aside>')
    body.append(cites.render())
    title = 'Does Medicaid, Medicare or insurance cover medical cannabis?'
    faq = {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': i['question'],
           'acceptedAnswer': {'@type': 'Answer', 'text': i['short'] + ' ' + ' '.join(p['text'] for p in i['points'] if p['source'])}} for i in data['items']]}
    return shell(title, 'Whether Medicaid, Medicare, private insurance or the VA pay for medical cannabis, which cannabis medicines are prescriptions, and which states cut the card fee.',
                 ''.join(body), 'coverage.html', 'the Medicaid and insurance page',
                 ld=[breadcrumbs([('Home', ''), ('Medical cards', 'medical.html')], 'coverage.html', 'Medicaid and insurance'), faq])


def partners_page(perm, sources):
    """How an organization can be listed or link here. Ground rules first; no organization is called a partner until it agrees."""
    body_mail = 'Organization:\r\nWebsite:\r\nState(s) served:\r\nWho you help (patients, veterans, legal aid, business):\r\nContact person:\r\n'
    mail = 'mailto:' + EMAIL + '?' + urlencode({'subject': f'{SITE_NAME}: partner or listing request', 'body': body_mail}, quote_via=quote)
    sponsor_body = ('Organization:\r\nWebsite:\r\nLicense and state (if you hold one):\r\nStates you want to reach:\r\n'
                    'What you would like the spot to say:\r\nContact person:\r\n')
    sponsor_mail = 'mailto:' + EMAIL + '?' + urlencode({'subject': f'{SITE_NAME}: sponsoring or advertising', 'body': sponsor_body}, quote_via=quote)
    link_html = f'<a href="{ORIGIN or DEFAULT_SITE_ORIGIN}/">Cannabis laws, medical cards and help for every state (The Reefer)</a>'
    orgs = []
    for i in perm['national']:
        s = sources[i['source_ids'][0]]
        if s['kind'] == 'organization' and s['publisher'] not in [o[0] for o in orgs]:
            orgs.append((s['publisher'], i['url'], i['need']))
    body = ['<p class="crumbs"><a href="index.html">Home</a> › Partners</p>', '<h1>Work with The Reefer</h1>',
            '<p class="lede">The Reefer is a free, source-linked guide to cannabis law, medical cards and help in every state. '
            'Patient groups, veteran organizations, legal aid offices, clinics, libraries and state associations can be listed here and can link here, at no cost.</p>',
            '<div class="needs">'
            f'<div class="need"><span class="ni" aria-hidden="true">{icon("form")}</span><strong>Get listed</strong><span>Tell us who you help and where. We add organizations to the state pages they serve, with a link to your own site.</span></div>'
            f'<div class="need"><span class="ni" aria-hidden="true">{icon("link")}</span><strong>Link to us</strong><span>Point your members to their state page, the medical card guides or the Medicaid and insurance page.</span></div>'
            f'<div class="need"><span class="ni" aria-hidden="true">{icon("check")}</span><strong>Correct us</strong><span>If a rule, fee or address on a page you know is out of date, send the source and we fix it.</span></div></div>',
            icon_heading(2, 'rules', 'Ground rules', 'scale') + '<ul>'
            '<li>No paid placement, paid ranking or paid verification. Listing is free and cannot be bought.</li>'
            '<li>Sponsored spots are labeled “Sponsored”, sit apart from listings and answers, and never change what’s listed, how it ranks, or what a state page says.</li>'
            '<li>A listing is not an endorsement, in either direction. Advocacy groups are named as advocacy groups.</li>'
            '<li>Every published fact names its source and the date it was checked. Listings link to the organization’s own site.</li>'
            '<li>The site is nonpartisan and treats every party and lawmaker the same way.</li>'
            '<li>Everything here is free to reuse under CC BY 4.0.</li></ul>',
            icon_heading(2, 'ask', 'Ask to be listed or to partner', 'mail') + f'<p><a class="pill" href="{esc(mail)}">Email a request</a></p>'
            '<p class="muted">Include your website, the states you serve and who you help. Requests are reviewed by a person.</p>',
            icon_heading(2, 'sponsor', 'Sponsor or advertise', 'tag') +
            '<p>The Reefer is free to use. Sponsors help pay for it. A sponsor gets a labeled spot on the home page or on the state pages it chooses: '
            'a short message and a link to its own site. Sponsoring is separate from being listed, which stays free.</p>'
            '<h3>Who can sponsor</h3><ul>'
            '<li>Cannabis businesses licensed in the states where they operate: dispensaries, growers, processors, testing labs and the companies that serve them</li>'
            '<li>Patient, veteran and advocacy groups</li>'
            '<li>Legal, compliance, banking, insurance and accounting services</li>'
            '<li>Events, publications and other organizations whose work fits the people who use this site</li></ul>'
            '<h3>Rules for sponsored spots</h3><ul>'
            '<li>Every spot is labeled “Sponsored” and sits apart from listings, the law answers and the map.</li>'
            '<li>Sponsoring never changes what is listed, how anything ranks, or what a law answer or state page says. It does not buy a listing, a review or a verification.</li>'
            '<li>Every spot is reviewed by a person before it runs, and can be declined or taken down.</li>'
            '<li>Only businesses licensed where they operate.</li>'
            '<li>No health or medical claims.</li>'
            '<li>Nothing that appeals to anyone under 21.</li>'
            '<li>The spot links to the sponsor’s own site. Visitor information is not shared with sponsors; see <a href="privacy.html">Privacy</a>.</li></ul>'
            f'<h3>Get in touch</h3><p><a class="pill" href="{esc(sponsor_mail)}">Email about sponsoring</a></p>'
            '<p class="muted">Include your website, your license and its state if you hold one, and the states you want to reach. Requests are answered by a person.</p>',
            icon_heading(2, 'link', 'Link to The Reefer', 'link') + '<p>Copy this link into your resources page, or link straight to any state page (for example, <code>the-reefer.com/florida.html</code>).</p>'
            f'<pre style="white-space:pre-wrap;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;overflow-wrap:anywhere">{esc(link_html)}</pre>'
            '<ul><li><a href="medical.html">Medical card guides, state by state</a></li><li><a href="coverage.html">Medicaid, Medicare and insurance</a></li>'
            '<li><a href="help.html#veterans">Veterans</a></li><li><a href="law-record-relief.html">Clearing a past record, state by state</a></li></ul>',
            icon_heading(2, 'already', 'Organizations this site already points visitors to', 'people') +
            '<p>These national organizations are linked from the <a href="help.html">help page</a> because they run a resource visitors need. They are not partners of this site and have not endorsed it.</p><ul>'
            + ''.join(f'<li><a href="{esc(url)}" target="_blank" rel="noopener">{esc(name)}</a> <span class="muted">({esc(need.lower())})</span></li>' for name, url, need in orgs) + '</ul>']
    return shell('Partner with The Reefer', 'How patient groups, veteran organizations, legal aid offices and state associations can be listed on The Reefer or link to it, free with no paid placement, and how to sponsor a labeled spot.',
                 ''.join(body), 'partners.html', 'the partners page', ld=[breadcrumbs([('Home', '')], 'partners.html', 'Partners')])


# Quick questions that sit under the "I'm here to…" chooser on the home page.
QUICK = [('Is it legal where I am?', 'law-adult-use.html'), ('Can I grow my own?', 'law-home-grow.html')]


def chooser(data):
    """The home page's "I'm here to…" chooser (data/landing-pages.json, home_chooser): one card per reason people
    come, each going to a page that already exists, with a few next stops under it."""
    cards = []
    for it in data['intents']:
        more = ''.join(f'<a href="{esc(href)}" data-track="intent-more:{esc(it["id"])}">{esc(label)}</a>' for label, href in it.get('more', []))
        cards.append(f'<div class="task intent" id="for-{esc(it["id"])}"><span class="ic">{icon(it["icon"])}</span>'
                     f'<a class="go" href="{esc(it["href"])}" data-track="intent:{esc(it["id"])}"><strong>{esc(it["label"])}</strong></a>'
                     f'<span class="d">{esc(it["text"])}</span>' + (f'<span class="more">{more}</span>' if more else '') + '</div>')
    return f'<h2>{esc(data["heading"])}</h2><div class="tasks intents">' + ''.join(cards) + '</div>'


def guide_link(code, name):
    return (OHIO_HOME + '/') if code == 'OH' else slug(name) + '.html'


def ship_art():
    """The home page picture: the site flag flying from a ship under the moon. The flag is the logo itself (scripts/build_reefer_flag.py)."""
    stars = ''.join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in (
        (42, 60, 1.4), (96, 210, 1), (150, 38, 1.2), (236, 92, 1), (285, 30, 1.5), (60, 300, 1), (200, 250, 1.2), (598, 300, 1.2),
        (640, 262, 1), (560, 340, 1), (318, 172, 1), (24, 150, 1.2), (250, 180, .9), (628, 380, 1.1), (180, 330, 1)))
    def sailor(x, flip, delay, bandana):
        """A deckhand with a joint: smoke drifts up, and every few seconds he doubles over coughing.

        The sailor facing left is the same drawing mirrored. His "*cough*" is a word, so it is drawn on its own,
        outside the mirrored group, and reads left to right. Do not flip it back with a transform on the <text>:
        the stylesheet animates that element's transform and the animation replaces the attribute, which is how the
        word came out backwards (owner's report, November 17, 2026). tests/picture-browser.cjs checks it in a browser."""
        d = f' style="animation-delay:{delay}s"'
        puffs = ''.join(f'<circle class="puff" cx="21" cy="-58" r="4" style="animation-delay:{delay + i * 1.1:.1f}s"/>' for i in range(3))
        burst = ''.join(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>' for cx, cy, r in ((24, -54, 5), (32, -58, 6), (30, -49, 4), (39, -53, 5)))
        mirror = ' transform="scale(-1 1)"' if flip else ''
        return (f'<g transform="translate({x} 471)"><g{mirror}><g class="sailor"{d}>'
                '<path d="M-5 0L-4-22M5 0L4-22" stroke="#22323b" stroke-width="6" stroke-linecap="round"/>'
                '<rect x="-9" y="-45" width="18" height="25" rx="5" fill="#ece6d2"/><path d="M-9-38H9M-9-31H9M-9-24H9" stroke="#33566b" stroke-width="2.4"/>'
                '<path d="M-8-41L-13-27" stroke="#d9a77a" stroke-width="4.5" stroke-linecap="round"/>'
                '<circle cx="0" cy="-53" r="8" fill="#d9a77a"/>'
                f'<path d="M-8.5-55Q0-66 8.5-55Q0-58-8.5-55Z" fill="{bandana}"/><path d="M-8-55l-7 5 6-1z" fill="{bandana}"/>'
                '<path d="M8-41L15-45L11-51" fill="none" stroke="#d9a77a" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M10-52L19-55" stroke="#f6f2e4" stroke-width="2.4" stroke-linecap="round"/><circle class="ember" cx="20" cy="-55.4" r="2.2"{d}/>'
                f'<g class="hack" fill="#dfe9ea"{d}>{burst}</g></g>'
                f'<g fill="#dfe9ea">{puffs}</g></g>'
                f'<text class="cough" x="{-34 if flip else 14}" y="-74"{d}>*cough*</text></g>')

    crew = '<g aria-hidden="true">' + sailor(285, False, 0, '#d0342c') + sailor(392, True, -4.6, '#2f7d4f') + '</g>'
    sail = 'fill="url(#sail)" stroke="#6f8791" stroke-width="1.6"'
    return (
        f'<svg class="ship" viewBox="0 0 660 620" role="img" aria-label="{esc(LOGO_ALT)}, flying as a flag from the mast of a ship at sea under a full moon" xmlns="http://www.w3.org/2000/svg">'
        '<defs><radialGradient id="sky" cx="22%" cy="24%" r="95%"><stop offset="0" stop-color="#1c4a5c"/><stop offset=".45" stop-color="#0c2531"/><stop offset="1" stop-color="#04090d"/></radialGradient>'
        '<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff6cf" stop-opacity=".55"/><stop offset="1" stop-color="#fff6cf" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="sail" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#46565e"/><stop offset="1" stop-color="#141b1f"/></linearGradient>'
        '<linearGradient id="hull" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a1d14"/><stop offset="1" stop-color="#0a0705"/></linearGradient>'
        '<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f3a47"/><stop offset="1" stop-color="#03141a"/></linearGradient>'
        '<clipPath id="frame"><rect width="660" height="620" rx="22"/></clipPath></defs>'
        '<g clip-path="url(#frame)"><rect width="660" height="620" fill="url(#sky)"/>'
        f'<g fill="#e9f3f5" opacity=".8">{stars}</g>'
        '<circle cx="138" cy="138" r="150" fill="url(#glow)"/><circle cx="138" cy="138" r="58" fill="#f6ecc4"/>'
        '<g fill="#d9cc9c" opacity=".55"><circle cx="120" cy="120" r="11"/><circle cx="158" cy="150" r="7"/><circle cx="128" cy="165" r="5"/></g>'
        '<path d="M0 520 Q60 508 120 520 T240 520 T360 520 T480 520 T600 520 T720 520 V620 H0Z" fill="#0b2f3a" opacity=".9"/>'
        '<g class="vessel">'
        # masts, yards and rigging
        '<g stroke="#120c08" stroke-linecap="round" fill="none"><path d="M330 500V40" stroke-width="9"/><path d="M196 500V236" stroke-width="7"/><path d="M462 500V262" stroke-width="7"/>'
        '<path d="M560 452 L636 404" stroke-width="7"/><path d="M248 262H412M236 372H424M140 300H252M132 398H260M410 318H514M402 410H522" stroke-width="5"/>'
        '<g stroke-width="1.3" opacity=".8"><path d="M330 60L96 470M330 60L196 236M330 60L462 262M330 110L636 404M462 262L636 404M196 236L96 470M330 250L560 452"/></g></g>'
        # sails, filled by the wind toward the bow
        f'<g {sail}><path d="M250 266H410Q434 318 420 368H240Q262 318 250 266Z"/><path d="M238 376H422Q448 432 432 482H228Q252 432 238 376Z"/>'
        '<path d="M142 304H250Q268 350 256 394H134Q152 350 142 304Z"/><path d="M134 402H258Q278 446 264 484H126Q146 446 134 402Z"/>'
        '<path d="M412 322H512Q530 366 518 406H404Q422 366 412 322Z"/><path d="M404 414H520Q540 452 528 486H396Q416 452 404 414Z"/>'
        '<path d="M470 300L628 408L474 446Q496 372 470 300Z"/></g>'
        '<g stroke="#000" stroke-width="1" opacity=".35" fill="none"><path d="M300 266Q318 318 296 368M360 266Q380 318 362 368M300 376Q322 432 296 482M362 376Q386 432 366 482"/></g>'
        + crew +
        # hull with stern castle, gun ports and lantern
        '<path d="M70 448H150V470H520L572 444L548 520Q470 560 330 560Q170 560 96 524Z" fill="url(#hull)" stroke="#000" stroke-width="2"/>'
        '<path d="M70 448H150V470H520L572 444" fill="none" stroke="#c9a24a" stroke-width="3" opacity=".7"/>'
        '<path d="M92 500Q330 532 556 492" fill="none" stroke="#c9a24a" stroke-width="2" opacity=".45"/>'
        '<g fill="#f2c14e"><rect x="88" y="476" width="12" height="12" rx="2"/><rect x="112" y="478" width="12" height="12" rx="2"/><circle cx="74" cy="436" r="5"/></g>'
        '<g fill="#000"><rect x="190" y="490" width="16" height="13" rx="2"/><rect x="250" y="494" width="16" height="13" rx="2"/><rect x="310" y="496" width="16" height="13" rx="2"/>'
        '<rect x="370" y="495" width="16" height="13" rx="2"/><rect x="430" y="491" width="16" height="13" rx="2"/><rect x="486" y="485" width="16" height="13" rx="2"/></g>'
        '<path d="M74 448V432" stroke="#120c08" stroke-width="3"/>'
        # the flag
        f'<g class="flag"><image href="{ASSETS}flag-900.webp" x="330" y="14" width="318" height="261" preserveAspectRatio="none"/></g>'
        '<circle cx="330" cy="38" r="7" fill="#c9a24a"/></g>'
        # water in front of the hull
        '<path class="swell" d="M-60 548 Q0 530 60 548 T180 548 T300 548 T420 548 T540 548 T660 548 T780 548 V620 H-60Z" fill="url(#sea)"/>'
        '<g fill="none" stroke="#9fd3d6" stroke-width="2" stroke-linecap="round" opacity=".5"><path d="M84 540q24-12 48 0M220 552q24-12 48 0M470 546q24-12 48 0M560 566q20-10 40 0M40 584q22-10 44 0M330 590q22-10 44 0"/></g>'
        '<path d="M110 540 Q138 548 132 600 L150 600 Q150 548 166 540Z" fill="#f6ecc4" opacity=".12"/>'
        '</g></svg>')


def joke_bubble(jokes):
    """The joke of the day as a speech bubble in the home page picture: the sailor in the red bandana tells it and his
    shipmate coughs. Owner's direction, November 17, 2026: the joke belongs in the picture, told by the two sailors, and
    should be prominent. It is HTML laid over the foot of the picture (the water), not part of the drawing, so the words
    wrap and are read aloud; the flag and the moon stay clear. Hidden until the script has a joke for today."""
    if not jokes:
        return ''
    return ('<div class="yarn" id="joke" hidden><div class="yarnhead"><h2>Joke of the day</h2>'
            '<a href="jokes.html">Earlier jokes</a></div><p id="joke-text"></p></div>')


# Owner's request, November 23, 2026: promote the free MJBizCon attendee planner (his own public
# Google Sheet) on the home page while the show is ahead. Dates come from the canonical event record;
# the bar is left out of builds after the show and a small script hides it for visitors once it ends.
MJBIZCON_EVENT_ID = 'event-nv-mjbizcon-2026'
MJBIZCON_PLANNER = 'https://docs.google.com/spreadsheets/d/1QlynoENgH6QjzzsPuFThA7PyKAZuv5XOkA_fnxdQaEg'


def show_bar(directory, today=None):
    event = next((e for e in directory.get('events', []) if e['id'] == MJBIZCON_EVENT_ID), None)
    if not event:
        return ''
    start, end = date.fromisoformat(event['starts_on']), date.fromisoformat(event['ends_on'])
    if (today or date.today()) > end:
        return ''
    when = f'{start.strftime("%b")} {start.day}–{end.day}, {end.year}' if start.month == end.month else f'{start:%b %d} – {end:%b %d, %Y}'
    return ('<style>.showbar{background:#10291f;color:#f4f1e8;border-bottom:3px solid var(--gold)}.showbar .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:6px 22px;padding-top:12px;padding-bottom:12px}.showbar p{max-width:none;margin:0;font-size:.98rem;line-height:1.45;flex:1 1 420px}.showbar .kicker{display:inline-block;margin-right:6px;font-size:.72rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--gold)}.showbar .go{display:flex;flex-wrap:wrap;gap:4px 18px}.showbar .go a{color:#fff;font-weight:800;min-height:44px;display:inline-flex;align-items:center;text-underline-offset:3px;white-space:nowrap}.showbar .go a.cta{background:var(--gold);color:#221c08;border-radius:8px;padding:0 16px;text-decoration:none}@media print{.showbar{display:none}}</style>'
            f'<aside class="showbar" id="mjbizcon-bar" data-ends="{end.isoformat()}" aria-label="MJBizCon 2026"><div class="wrap">'
            f'<p><span class="kicker">Heading to Vegas?</span> <strong>MJBizCon 2026</strong> · Las Vegas Convention Center · '
            f'<time datetime="{start.isoformat()}">{esc(when)}</time>. Plan your trip with the free <strong>Attendee Planner</strong>: '
            'every exhibitor with booth numbers, every speaker and session with times and rooms, state takeovers and after-hours '
            'events, and a printable meeting plan. Make your own copy and it works on your phone.</p>'
            '<p class="go">'
            f'<a class="cta" href="{esc(MJBIZCON_PLANNER)}/edit?usp=sharing" target="_blank" rel="noopener" data-track="mjbizcon:planner-open">Open the planner →</a>'
            f'<a href="{esc(MJBIZCON_PLANNER)}/copy" target="_blank" rel="noopener" data-track="mjbizcon:planner-copy">Make my own copy</a>'
            f'<a href="{esc(MJBIZCON_PLANNER)}/export?format=xlsx" data-track="mjbizcon:planner-download">Download (.xlsx)</a>'
            '</p></div></aside>'
            '<script>(function(){var b=document.getElementById("mjbizcon-bar");if(!b)return;var d=new Date(),'
            't=d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2);'
            'if(t>b.getAttribute("data-ends"))b.remove()})();</script>')


# Owner direction, November 26, 2026: the home page felt disjointed. It now opens on three clear ways in (your state,
# the game, the MJBizCon planner while the show is ahead), then a real education section, then the rest. The
# "set sail" announcement and the separate MJBizCon bar were folded into this.
EDU_FILE = ROOT / 'data/home-education.json'
NATIONAL_GUIDES = [('Leafly', 'https://www.leafly.com/strains', 'Strain library and reviews'),
                   ('Leafly Learn', 'https://www.leafly.com/learn', 'Beginner guides and how-tos'),
                   ('Weedmaps Learn', 'https://weedmaps.com/learn', 'Plain guides to products and terms'),
                   ('NORML', 'https://norml.org/laws/', 'Laws and penalties in every state'),
                   ('Marijuana Policy Project', 'https://www.mpp.org/states/', 'Where each state’s laws and bills stand')]


# The Silver Cup, the game's prize contest for MJBizCon week (owner direction, November 26, 2026). Times are UTC:
# it opens at 12:00 AM Pacific on December 1 and closes at the end of December 4, Pacific.
SILVER_CUP_END = datetime(2026, 12, 5, 8, tzinfo=timezone.utc)


def silver_cup_banner(now=None):
    """A one-line banner under the home page's title while the Silver Cup is ahead or on. After the close it is left out
    of the build, and a small script removes it from a page built earlier."""
    if (now or datetime.now(timezone.utc)) >= SILVER_CUP_END:
        return ''
    return ('<p class="cup-banner" id="cup-banner" data-ends="' + SILVER_CUP_END.strftime('%Y-%m-%dT%H:%M:%SZ') + '">'
            '<a href="../pillage/contest.html" data-track="home:silver-cup"><span aria-hidden="true">🏆</span> '
            'Win silver in our pirate game: the Silver Cup, December 1 to 4</a></p>'
            '<script>(function(){var b=document.getElementById("cup-banner");'
            'if(b&&Date.now()>=Date.parse(b.getAttribute("data-ends")))b.remove()})();</script>')


def mjbizcon_card(directory, today=None):
    """The third way in while MJBizCon 2026 is ahead; after the show it is left out and a small script hides it."""
    event = next((e for e in directory.get('events', []) if e['id'] == MJBIZCON_EVENT_ID), None)
    if not event:
        return ''
    start, end = date.fromisoformat(event['starts_on']), date.fromisoformat(event['ends_on'])
    if (today or date.today()) > end:
        return ''
    when = f'{start.strftime("%b")} {start.day}–{end.day}, {end.year}' if start.month == end.month else f'{start:%b %d} – {end:%b %d, %Y}'
    return ('<li class="path biz" id="mjbizcon-card" data-ends="' + end.isoformat() + '"><span class="pi" aria-hidden="true">' + icon('calendar') + '</span>'
            f'<h2>Going to MJBizCon?</h2><p>Las Vegas, <time datetime="{start.isoformat()}">{esc(when)}</time>. Our free planner has every exhibitor and booth, '
            'every session with times and rooms, and after-hours events. Make a copy and it works on your phone.</p>'
            f'<a class="go" href="{esc(MJBIZCON_PLANNER)}/copy" target="_blank" rel="noopener" data-track="mjbizcon:planner-copy">Get the free planner</a>'
            f'<a class="alt" href="{esc(MJBIZCON_PLANNER)}/edit?usp=sharing" target="_blank" rel="noopener" data-track="mjbizcon:planner-open">Just look at it</a>'
            ' <a class="alt" href="las-vegas.html" data-track="mjbizcon:las-vegas">Vegas cannabis rules for visitors</a></li>'
            '<script>(function(){var b=document.getElementById("mjbizcon-card");if(!b)return;var d=new Date(),'
            't=d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2);'
            'if(t>b.getAttribute("data-ends"))b.remove()})();</script>')


def education_section(perm, answers):
    """Learn the basics: words to know, myths busted, and the big picture, every line from a reviewed record."""
    edu = json.loads(EDU_FILE.read_text(encoding='utf-8'))
    k = json.loads((ROOT / 'data/knowledge.json').read_text(encoding='utf-8'))
    ksrc = {x['id']: x for x in k['sources']}
    kitems = {it['id']: it for sec in k['sections'] for it in sec['items']}
    nat = {r['id']: r for r in perm['national']}
    psrc = {x['id']: x for x in perm['sources']}

    def src_links(entry):
        out = []
        for kid in entry.get('knowledge', []):
            for sid in kitems[kid].get('sources', []):
                out.append((ksrc[sid]['title'], ksrc[sid]['url']))
        for nid in entry.get('national', []):
            for sid in nat[nid]['source_ids']:
                out.append((psrc[sid]['publisher'], psrc[sid]['url']))
        seen, links = set(), []
        for title, url in out:
            if url not in seen:
                seen.add(url)
                links.append(f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(title)}</a>')
        return '<p class="src">Source: ' + ' · '.join(links) + '</p>' if links else ''

    terms = ''.join(f'<div><dt>{esc(t["term"])}</dt><dd>{esc(t["text"])} <a href="learn.html#definitions-{esc(t["knowledge"])}" aria-label="More on {esc(t["term"])}">More</a></dd></div>'
                    if any(sec['id'] == 'definitions' and t['knowledge'] in {i['id'] for i in sec['items']} for sec in k['sections'])
                    else f'<div><dt>{esc(t["term"])}</dt><dd>{esc(t["text"])}</dd></div>' for t in edu['terms'])
    term_src = src_links({'knowledge': [t['knowledge'] for t in edu['terms']]})
    myths = ''.join(f'<li><p class="myth"><span class="tag no">Myth</span> {esc(m["myth"])}</p><p class="fact"><span class="tag yes">Fact</span> {esc(m["fact"])}</p>'
                    f'{src_links(m)}<p class="more"><a href="{esc(m["more"][1])}">{esc(m["more"][0])}</a></p></li>' for m in edu['myths'])

    def tally(qid):
        t = {}
        for c in perm['jurisdictions']:
            a = answers.get(c, {}).get(qid)
            if a:
                t[a['status']] = t.get(a['status'], 0) + 1
        return t
    au, med, rec = tally('adult-use'), tally('medical'), tally('record-relief')
    hemp = kitems['hemp-federal-dates']
    big = [('chart', f'{au.get("allowed", 0)}', 'of the 50 states and DC let adults 21 and older use cannabis.',
            f'{au.get("medical-only", 0)} more allow it for medical patients only, and {au.get("not-permitted", 0)} don’t allow it for adults.', 'law-adult-use.html', 'See the map'),
           ('card', f'{med.get("allowed", 0)}', 'have a full medical cannabis program.',
            f'{med.get("limited", 0)} more have a limited one, often low-THC or CBD only.', 'medical.html', 'How to get a card'),
           ('record', f'{rec.get("automatic", 0)}', 'clear some old cannabis records on their own.',
            f'{rec.get("by-application", 0)} more do it when you apply, often with free legal help.', 'law-record-relief.html', 'Clear a record')]
    tiles = ''.join(f'<li><span class="bi" aria-hidden="true">{icon(ic)}</span><p><strong class="num">{n}</strong> {esc(a)}</p><p>{esc(b)}</p><a href="{href}">{esc(go)}</a></li>'
                    for ic, n, a, b, href, go in big)
    hemp_note = ('<li class="wide"><span class="bi" aria-hidden="true">' + icon('warning') + '</span><p><strong>Gas station THC is changing.</strong> '
                 'Since November 12, 2026, products with cannabinoids the plant can’t make on its own, like THC-O, are no longer federal hemp. '
                 'From December 11, 2026, federal hemp counts total THC and caps it at 0.4 mg per container, unless Congress changes it again.</p>'
                 + src_links({'knowledge': ['hemp-federal-dates']}) + '</li>')
    more = ' · '.join(f'<a href="{esc(h)}">{esc(l)}</a>' for l, h in edu['more'])
    return ('<section class="block edu" id="learn" aria-labelledby="learn-h"><h2 id="learn-h">Learn the basics</h2>'
            '<p class="lede">Real answers, no hype. Every fact below links to the agency or lab it comes from.</p>'
            '<div class="edu-grid">'
            f'<div class="edu-col"><h3>{icon("book")} Words to know</h3><dl class="terms">{terms}</dl>{term_src}</div>'
            f'<div class="edu-col"><h3>{icon("warning")} Myths, busted</h3><ul class="myths">{myths}</ul></div></div>'
            f'<h3 class="bigh">{icon("globe")} The big picture</h3><ul class="big">{tiles}{hemp_note}</ul>'
            '<p class="muted">State counts come from the answer on each state’s page, each with its own source, as of '
            f'{long_date(perm["as_of"])}.</p><p class="edu-more">Keep learning: {more}</p></section>')


def home_page(perm, score, directory, answers, sources, sponsors=()):
    names = perm['jurisdictions']
    jokes = load_jokes()
    ordered = sorted(names, key=lambda c: names[c])
    jump = ''.join(f'<option value="{slug(names[c])}.html">{esc(names[c])}</option>' for c in ordered)
    hero = ('<section class="hero" aria-labelledby="hero-title"><div class="wrap"><div class="copy">'
            '<p class="eyebrow">Free · All 50 states and DC · Every answer sourced</p>'
            '<h1 id="hero-title">Cannabis answers for your state, in plain language.</h1>'
            '<p>What’s legal, where to buy, how to clear a record and where to get help, with a link to the law or agency behind every answer.</p>'
            + silver_cup_banner() + '</div>'
            f'<div class="art"><div class="shipbox">{ship_art()}{joke_bubble(jokes)}</div></div></div></section>')
    # Three ways in, big and side by side, right under the title.
    paths = ('<section class="paths-wrap" aria-label="Start here"><ul class="paths">'
             '<li class="path state"><span class="pi" aria-hidden="true">' + icon('pin') + '</span><h2>Your state</h2>'
             '<p>The law in plain words, where to buy, medical cards and local help.</p>'
             '<form class="pick" id="pick"><label for="state-jump">Pick your state</label><div class="row">'
             f'<select id="state-jump" name="state"><option value="">Choose a state</option>{jump}</select><button type="submit">Go</button></div></form>'
             '<a class="alt" href="#map">Or tap it on the map</a> <a class="alt" href="world.html">Outside the US?</a></li>'
             '<li class="path game"><span class="pi" aria-hidden="true">🏴‍☠️</span><h2>Pillage the Reefer</h2>'
             '<p>Our free pirate game. Run weed between Caribbean ports, dodge the law and fight pirates. Plays on your phone, no sign-up.</p>'
             '<a class="go" href="../pillage/" data-track="home:game">Play the game</a></li>'
             + mjbizcon_card(directory) + '</ul></section>')

    joke = (jokes_data(jokes) + JOKE_SCRIPT) if jokes else ''
    body = [paths, education_section(perm, answers)]
    pick = load_landing()['home_chooser']
    body.append('<section class="block" id="tasks">' + chooser(pick))
    hrefs = [it['href'] for it in pick['intents']] + [href for it in pick['intents'] for _, href in it.get('more', [])]
    linked = {href.split('#')[1] for href in hrefs if href.startswith('help.html#')}
    more = [f'<a href="{href}">{esc(label)}</a>' for label, href in QUICK]
    more += [f'<a href="help.html#{slug(n)}">{esc(n)}</a>' for n in needs_in_order(perm) if slug(n) not in linked]
    more.append(f'<a href="{city_guides.HUB}">Visitor guides, city by city</a>')
    more.append('<a href="las-vegas.html">Visiting Las Vegas</a>')
    more += [f'<a href="{page}">{esc(label)}</a>' for page, label in city_guides.home_links()]
    body.append('<p class="also">Also: ' + ' · '.join(more) + ' · <a href="help.html">All national help</a></p></section>')
    body.append(joke)

    adult = next(q for q in perm['questions'] if q['id'] == 'adult-use')
    grid, legend = tile_map(perm, adult, answers, 'Map: adult use by state. Select a state to open its guide.')
    guides = []
    for code, card in score['states'].items():
        what = ('Business directory, dispensary finder, record clearing and advocacy on OhioWeed.org' if code == 'OH'
                else f'{PACK_LABEL[card["publication_status"]]}: directory and local help, being built out')
        guides.append(f'<a class="guide" href="{guide_link(code, card["name"])}"><strong>{esc(card["name"])}</strong><span>{esc(what)}</span></a>')
    body.append('<section class="block" id="map"><h2>Pick your state on the map</h2>'
                '<p>Colors show where adults can use cannabis. Tap a state for its full guide.</p>'
                f'<div class="mapbox"><div>{grid}{legend}</div><div><h3>States with a full local guide</h3>'
                '<p class="muted">Directories of businesses, dispensaries and local help. More states are added over time.</p>'
                f'<div class="guides">{"".join(guides)}</div></div></div>'
                '<details class="az"><summary>List all states A–Z</summary><ul>'
                + ''.join(f'<li><a href="{slug(names[c])}.html">{esc(names[c])}</a></li>' for c in ordered) + '</ul></details></section>')

    # Good guides that already exist, linked plainly (owner direction, November 26, 2026).
    body.append('<section class="block og" id="other-guides" aria-labelledby="og-h"><h2 id="og-h">' + icon('link') + ' Other good guides</h2>'
                '<p>Plenty of people already do parts of this well. Each state page links the best store finders and law guides for that state. '
                'We don’t run these sites and they don’t pay us.</p><ul class="og-list">'
                + ''.join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener"><strong>{esc(n)}</strong><span>{esc(w)}</span></a></li>' for n, u, w in NATIONAL_GUIDES)
                + '</ul>' + reuse_offer('state or local') + '</section>')

    import build_world  # the world section lives in build_world; imported here to avoid a load-time cycle
    n_world = len(build_world.load()['countries'])
    body.append('<section class="block" id="world"><h2>Around the world</h2>'
                f'<p>The same plain answers for {n_world} countries, where weed comes from, and the places it can land you in prison.</p>'
                '<div class="pills"><a class="pill" href="world.html">All countries</a><a class="pill" href="travel-warnings.html">Travel warnings</a>'
                '<a class="pill" href="heritage.html">Where weed comes from</a></div></section>')
    body.append('<section class="block" id="compare"><h2>Compare one rule across every state</h2>'
                '<p>Pick a question to see every state side by side, on a map and in a list.</p><div class="pills">')
    for q in perm['questions']:
        answered = sum(q['id'] in answers.get(c, {}) for c in names)
        body.append(f'<a class="pill" href="{law_page_name(q["id"])}">{esc(LAW_BLURB.get(q["id"], q["question"]))} <small>{answered}/{len(names)}</small></a>')
    body.append('</div><p class="muted">The number shows how many states have a reviewed answer so far. A missing answer means not yet reviewed, never that something is prohibited.</p>'
                + spread_chart(perm, answers) + '</section>')

    # After the map and the comparisons, never inside them.
    body.append(sponsor_slot(active_sponsor(sponsors, 'home')))
    body.append('<section class="block" id="family"><h2>More from the same team</h2><div class="family">')
    for url, label, host, text in FAMILY:
        body.append(f'<a class="site-card" href="{esc(url)}" data-track="family:{esc(host)}"><strong>{esc(label)}</strong><span class="u">{esc(host)}</span><p>{esc(text)}</p></a>')
    body.append('</div><p class="muted">How this site checks its information, and its ground rules: <a href="about.html">About</a>. No paid placement or ranking.</p></section>')
    body.append('<script>(function(){var f=document.getElementById("pick"),j=document.getElementById("state-jump");'
                'function go(){if(!j.value)return;if(window.directoryTrack)window.directoryTrack("state-picker");location.href=j.value}f.addEventListener("submit",function(e){e.preventDefault();go()});j.addEventListener("change",go)})();</script>')
    description = 'Free, plain-language cannabis answers for all 50 states and DC: what is legal, where to buy, record clearing, myths busted and the basics explained, each answer traced to a named source.'
    return shell(TAGLINE, description, ''.join(body), 'index.html', 'the home page', hero, ld=[website_node()], css=SPREAD_CSS + HOME_CSS)


HOME_CSS = """
.hero .wrap{padding-bottom:30px}
.paths-wrap{background:linear-gradient(180deg,var(--green2) 0,var(--green2) 70px,var(--bg) 70px)}
.paths{list-style:none;margin:0 auto;padding:0 20px;max-width:1080px;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.path{position:relative;background:var(--card);color:var(--ink);border-radius:18px;padding:18px 20px 20px;box-shadow:0 10px 28px rgba(0,0,0,.16);border-top:6px solid var(--green2);display:flex;flex-direction:column;gap:6px}
.path.game{border-top-color:#b4513a}.path.biz{border-top-color:var(--gold)}
.path h2{margin:0;font-size:1.5rem}.path p{margin:0}.path .pi{font-size:2rem;line-height:1;width:44px;height:44px;display:grid;place-items:center}.path .pi svg{width:36px;height:36px}
.path .go{margin-top:auto;align-self:flex-start;display:inline-flex;align-items:center;min-height:52px;padding:0 24px;border-radius:12px;background:var(--green);color:#fff;font-weight:800;font-size:1.1rem;text-decoration:none}
.path.game .go{background:#8f3a26}.path.biz .go{background:var(--gold);color:#221c08}
.path .go:hover,.path .go:focus-visible{outline:3px solid var(--ink);outline-offset:2px}
.path .alt{font-weight:700;min-height:44px;display:inline-flex;align-items:center;margin-right:14px}
.path .pick{margin:6px 0 0;padding:0;box-shadow:none;max-width:none}.path .pick select{min-height:52px;font-size:1.1rem}
.cup-banner{margin:14px 0 0}.cup-banner a{display:inline-flex;align-items:center;gap:8px;min-height:48px;padding:8px 18px;border-radius:999px;background:var(--gold);color:#221c08;font-weight:800;text-decoration:none}
.cup-banner a:hover,.cup-banner a:focus-visible{outline:3px solid #fff;outline-offset:2px}
.edu .lede{font-size:1.15rem}
.edu-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
.edu-col{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:6px 20px 16px}
.edu h3{display:flex;align-items:center;gap:8px;font-size:1.3rem}.edu h3 svg{width:26px;height:26px}
.terms{margin:0}.terms div{padding:10px 0;border-bottom:1px solid var(--line)}.terms dt{font-weight:800;font-size:1.08rem}.terms dd{margin:2px 0 0}
.myths{list-style:none;margin:0;padding:0}.myths li{padding:12px 0;border-bottom:1px solid var(--line)}.myths p{margin:.2em 0}
.myth{font-weight:700;text-decoration:line-through;text-decoration-thickness:2px;text-decoration-color:#b4513a}.myth .tag{text-decoration:none}
.tag{display:inline-block;margin-right:6px;padding:1px 9px;border-radius:999px;font-size:.85rem;font-weight:800;color:#fff;text-decoration:none}.tag.no{background:#9a3b27}.tag.yes{background:#2f6b28}
.src{font-size:.92rem;color:var(--soft)}.src a{color:var(--link)}.more{font-weight:700}
.big{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.big li{background:var(--mint);border-radius:16px;padding:14px 18px}.big li.wide{grid-column:1/-1;background:var(--note)}
.big .bi svg{width:30px;height:30px}.big p{margin:.3em 0}.big .num{font-size:2.2rem;line-height:1;display:block}.big a{font-weight:800;min-height:44px;display:inline-flex;align-items:center}
.edu-more{font-weight:700}
.og-list{list-style:none;padding:0;margin:10px 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.og-list li{border:1px solid var(--line);border-radius:12px;padding:10px 14px;background:var(--card)}
.og-list a{display:flex;flex-direction:column;min-height:44px;text-decoration:none;color:var(--ink)}.og-list a strong{font-size:1.1rem;text-decoration:underline;text-underline-offset:3px}
.reuse{background:var(--mint);border-radius:10px;padding:10px 14px}
@media(prefers-color-scheme:dark){.path{background:#1c2622;color:#eef3ee}.edu-col,.og-list li{background:#1c2622}.big li{background:#22312a}.big li.wide{background:#3a3220}.reuse{background:#22312a}}
"""


def state_names(perm):
    return {slug(name) + '.html' for name in perm['jurisdictions'].values()}


def pages():
    """Every generated page as {file name: text}."""
    perm, score, directory = load()
    sources = {s['id']: s for s in perm['sources']}
    answers = answers_by_state(perm)
    med_data, medical = load_medical()
    sources.update({s['id']: s for s in med_data['sources']})
    sources.update({s['id']: s for s in load_coverage()['sources']})
    disp_data, dispensaries = load_dispensaries()
    sources.update({src['id']: src for s in dispensaries.values() for src in (s.get('sources') or [s['source']])})
    sponsors = load_sponsors(perm['jurisdictions'])
    featured = load_featured(perm['jurisdictions'])
    guides = load_guides()
    neighbors = load_neighbors(perm['jurisdictions'])
    out = {'index.html': home_page(perm, score, directory, answers, sources, sponsors),
           'medical.html': medical_page(perm, med_data, medical, answers, sources, dispensaries),
           'coverage.html': coverage_page(perm, medical, sources),
           'partners.html': partners_page(perm, sources),
           'jokes.html': jokes_page(load_jokes()),
           'help.html': help_page(perm, sources),
           'about.html': about_page(perm, score, directory, answers),
           'privacy.html': privacy_page()}
    import hash_myths  # Hash myths, busted (owner direction, November 24, 2026)
    out[hash_myths.NAME] = hash_myths.page(sys.modules[__name__], load_landing()['national_pages'][hash_myths.NAME])
    import weed_santa  # Weed Santa, free cannabis help in Ohio (owner direction, November 25, 2026)
    out[weed_santa.NAME] = weed_santa.page(sys.modules[__name__], load_landing()['national_pages'][weed_santa.NAME])
    import las_vegas  # Visiting Las Vegas: cannabis rules for visitors, for MJBizCon week and after (November 27, 2026)
    out[las_vegas.NAME] = las_vegas.page(sys.modules[__name__], load_landing()['national_pages'][las_vegas.NAME], directory)
    for name in city_guides.GUIDES:  # Denver, Chicago, New York City, Los Angeles, Detroit, Boston, Seattle, Phoenix, Miami, San Francisco, Portland, New Orleans, Washington, DC, Columbus, Cleveland, Cincinnati, Dayton, Toledo and Akron visitor guides (November 27, 2026)
        out[name] = city_guides.page(sys.modules[__name__], name, load_landing()['national_pages'][name])
    out[city_guides.HUB] = city_guides.hub(sys.modules[__name__], load_landing()['national_pages'][city_guides.HUB])  # every visitor guide on one page
    for q in perm['questions']:
        out[law_page_name(q['id'])] = law_page(perm, q, answers, sources, dispensaries)
    for code, name in perm['jurisdictions'].items():
        out[slug(name) + '.html'] = state_page(perm, score, directory, code, answers, sources, medical, dispensaries, sponsors, featured, guides, neighbors)
    import build_world  # imported here: build_world uses this module's page shell
    world = build_world.pages(perm, sources)
    clash = sorted(set(world) & set(out))
    if clash:
        raise SystemExit(f'world pages would overwrite: {clash}')
    out.update(world)
    return out


def main(out_dir=None):
    out_dir = Path(out_dir or OUT_DIR)
    built = pages()
    if out_dir.exists():
        for old in out_dir.glob('*.html'):
            if old.name not in built:
                old.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in built.items():
        (out_dir / name).write_text(text, encoding='utf-8')
    print(f'Built national/: {len(built)} pages (home, help, about, privacy, medical cards, coverage, partners, jokes, hash myths, Weed Santa, Las Vegas, Denver, Chicago, New York City, Los Angeles, Detroit, Boston, Seattle, Phoenix, Miami, San Francisco, Portland, New Orleans, Washington, DC, Columbus, Cleveland, Cincinnati, Dayton, Toledo, Akron, the visitor guides hub, law comparisons, 51 states, world section)')


if __name__ == '__main__':
    main()
