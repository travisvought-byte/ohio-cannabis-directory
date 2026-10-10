"""Build source-reviewed consumer routes without changing the organization dataset."""
import html
from pathlib import Path
from directory_brand import brand_page
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'resources.html'
REVIEWED = '2026-10-09'
DCC = 'https://com.ohio.gov/divisions-and-programs/cannabis-control'
RESOURCES = [
 ('dispensaries','Find a dispensary',[
  ('Ohio Division of Cannabis Control',DCC,'Ohio’s official starting point for licensed dispensary locations. Choose “Dispensary Map” or “Dispensaries” on the state page. Check the license type, hours and current menu before traveling.'),
  ('Medical patient dispensary lookup',DCC+'/patients-caregivers/find-dispensary','State guidance and location lookup for patients and caregivers. Confirm that the location serves medical patients.')]),
 ('seeds','Find seeds and growing supplies',[
  ('Dutch Wilson Genetics','https://dutchwilsonseeds.com/','Ohio-based seed company with regular and feminized seed catalogs. Published contact: (740) 272-2349; dutchwilsonseeds@yahoo.com. Catalog reviewed; current stock and delivery eligibility must be confirmed with the seller.'),
  ('Humboldt Seed Company U.S. catalog','https://californiahempseeds.com/shop/','Seed catalog identifying Humboldt Seed Company, including feminized options. National supplier; an Ohio storefront or Ohio delivery guarantee has not been verified.'),
  ('Find cultivation suppliers in the directory','index.html?q=cultivation','Search existing organizations for cultivation services and equipment. Use your city or county as an additional search term; service areas are descriptive, not measured distances.')]),
 ('records','Get help clearing a record',[
  ('Ohio Legal Help: record sealing','https://www.ohiolegalhelp.org/topic/seal-criminal-record','Statewide explanation of sealing, expungement and legal-aid options. Start here to identify the right assistance for your county.'),
  ('Eligibility interview and action plan','https://www.ohiolegalhelp.org/letters-forms/criminal-sealing-eligibility','A guided record-sealing interview that produces next steps. Have your court names, case numbers and charge details ready. This general tool is separate from the marijuana-specific statute below.'),
  ('Opportunity Port','https://opportunityport.org/faqs/','Currently serves Franklin County residents seeking help with Ohio records. Legal assistance is free; filing fees may apply. Services outside Franklin County are paused.'),
  ('Marijuana-specific expungement: ORC 2953.321','https://codes.ohio.gov/ohio-revised-code/section-2953.321','Effective March 20, 2026. Covers specified marijuana/hashish possession cases from before that date, including certain dismissed cases. Apply to the sentencing court with case information and evidence of the covered offense. Relief requires a court process; it is not automatic. The statute sets a $50 application fee unless indigent.')]),
 ('medical','Start as a medical patient or caregiver',[
  ('Ohio patient and caregiver steps',DCC+'/patients-caregivers/obtain-medical-marijuana','Official steps for obtaining a recommendation, registering and purchasing medical cannabis. Bring an active registry card, active recommendation and government-issued ID when purchasing.'),
  ('Patient registry help',DCC,'For registry questions, the state publishes 1-833-464-6627 and MMCPRegistry@com.ohio.gov. Choose patient and caregiver resources on the DCC page.')]),
 ('rules','Understand the Ohio rules',[
  ('Home growing: ORC 3796.04','https://codes.ohio.gov/ohio-revised-code/section-3796.04','Adults 21+ may grow up to six plants per person, with no more than twelve at one residence. Grow at your primary residence in a secured enclosed area, inaccessible to people under 21 and not visible from public space. Rental prohibitions and other residence restrictions apply. The section prohibits selling homegrown marijuana, hydrocarbon extraction and public consumption.'),
  ('Ohio cannabis law: current chapter','https://codes.ohio.gov/ohio-revised-code/chapter-3796','Read the current law for possession, transport, purchase, patient and other requirements. Home-growing permission does not answer every possession or transport question.'),
  ('State cannabis guidance',DCC,'The official hub links the Ohio Cannabis FAQ, current rules and patient guidance. Use current state sources when an older online summary conflicts.')]),
 ('community','Find community and business connections',[
  ('Midwest CannaWomen','https://midwestcannawomen.crd.co/','Ohio-focused community resource for cannabis patients, caregivers and industry connections.'),
  ('Search Ohio organizations','index.html','Search the full business and nonprofit directory by need, organization, city or service area.'),
  ('Browse documented relationships','relationships.html','Explore the existing source-documented relationships between organizations.')])]

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
