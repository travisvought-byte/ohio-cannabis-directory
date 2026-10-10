"""Build source-reviewed consumer routes without changing the organization dataset."""
import html
from pathlib import Path
from directory_brand import brand_page
from directory_data import load_resource_routes
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'resources.html'
REVIEWED = '2026-10-09'
DCC = 'https://com.ohio.gov/divisions-and-programs/cannabis-control'
RESOURCES = load_resource_routes()

def main():
 sections = []
 for key,title,items in RESOURCES:
  cards = ''.join(f'<article><h3><a href="{html.escape(url,quote=True)}">{html.escape(name)}</a></h3><p>{html.escape(desc)}</p><p class="review">Source reviewed {REVIEWED} · <a href="{html.escape(url,quote=True)}">Open source / take next step</a></p></article>' for name,url,desc in items)
  sections.append(f'<section id="{key}"><h2>{title}</h2>{cards}<p><a href="#start">Back to choices</a></p></section>')
 nav = ''.join(f'<a class="choice" href="#{key}">{html.escape(title)}</a>' for key,title,_ in RESOURCES)
 page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ohio Cannabis Consumer Resources | Veteran Home Guardians</title><meta name="description" content="Source-reviewed Ohio cannabis routes for dispensaries, seeds, record clearing, medical patients, rules and community."><style>
 :root{--ink-soft:#555;--field-deep:#9d0927}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#faf9f6;color:#25282b;font:16px/1.6 system-ui,sans-serif}.wrap{max-width:960px;margin:auto;padding:28px 20px}a{color:var(--field-deep);overflow-wrap:anywhere}a:focus-visible{outline:3px solid #9d0927;outline-offset:4px}h1{font-size:clamp(1.8rem,5vw,2.5rem);line-height:1.2}h2{line-height:1.3}h3{font-size:1.05rem;margin:0}p{max-width:78ch}.choices{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}.choice{padding:16px;border:1px solid #ccc;background:white;font-weight:650;text-decoration:none}.choice:hover{border-color:#9d0927}section{scroll-margin-top:20px;margin-top:42px;border-top:3px solid #ba0c2f;padding-top:12px}article{padding:18px 0;border-bottom:1px solid #ddd}article p{margin:8px 0}.review,footer{font-size:.83rem;color:#555}footer{margin-top:35px;border-top:1px solid #ccc;padding-top:20px}__VHG_CSS__ @media print{.choices{display:none}section,article{break-inside:avoid}body{background:white}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
 </style></head><body><main class="wrap" id="start">__VHG_BRAND__<p><a href="index.html">← Full organization directory</a></p><h1>What do you need?</h1><p>Practical starting points for people using Ohio’s cannabis resources. Pick a need, see who serves it, and follow the source to take the next step.</p><nav class="choices" aria-label="Choose a resource">__NAV__</nav><p class="review">Reviewed October 9, 2026. These are referral routes, not a complete local provider list. Seed catalogs are not endorsements or guarantees of lawful delivery. Confirm current eligibility, availability and requirements with the provider.</p>__SECTIONS__<footer><p>A Veteran Home Guardians resource, maintained by Travis Vought. Add a missing resource or report a correction: <a href="__UPDATE_URL__">__VHG_EMAIL__</a>.</p><p>Consumer routes are listed separately from the directory’s organization counts. Legal summaries point to the source and do not determine your individual eligibility.</p><p><a href="index.html">Organization directory</a> · <a href="relationships.html">Business relationships</a></p></footer></main></body></html>'''
 OUT.write_text(brand_page(page.replace('__NAV__',nav).replace('__SECTIONS__',''.join(sections))),encoding='utf-8')
 print(f'Built {OUT.name}: {len(RESOURCES)} consumer routes')
if __name__ == '__main__': main()
