"""Create the printable dispensary shopping worksheet."""
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'assets/dispensary-shopping-guide.pdf'
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='SmallText',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=5))
styles['Title'].textColor=colors.HexColor('#a90000');styles['Title'].fontSize=25;styles['Title'].leading=29
styles['Heading2'].textColor=colors.HexColor('#a90000');styles['Heading2'].spaceBefore=13
story=[]
def p(t,style='Body'):story.append(Paragraph(t,styles[style]))
def h(t):p(t,'Heading2')
def line(t):p(t+' ______________________________________________________');story.append(Spacer(1,6))
def table(rows,widths):
 t=Table([[Paragraph(str(c),styles['SmallText']) for c in r] for r in rows],colWidths=widths,hAlign='LEFT')
 t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#bbbbbb')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.append(t)
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#555555'));c.drawString(42,25,'Veteran Home Guardians | Ohio Cannabis Ecosystem Directory | October 11, 2026');c.drawRightString(570,25,str(d.page))
p('Your dispensary shopping plan','Title');p('A first-time and new-product buyer guide. Fill this out before your visit, then use it to explain what you need.','Body')
h('1. What are you trying to accomplish?');line('My goal or question');p('Examples: understand product choices, avoid smoke, find a measurable product, or discuss a health concern with a clinician. Desired effects are not guaranteed.','SmallText')
p('Experience: [ ] First time  [ ] Occasional  [ ] Returning after a break<br/>[ ] Experienced with cannabis, but new to this product form')
line('What worked or felt uncomfortable before?');line('Ingredients / flavors / methods I want to avoid');line('Budget including taxes, fees and any device ($)')
h('2. What do you want to buy?');p('[ ] Flower / pre-rolls   [ ] Gummies / other edibles   [ ] Concentrates<br/>[ ] Cartridge / disposable   [ ] Tincture / oral oil   [ ] Topical   [ ] Not sure')
line('Preferred form / product');line('I want my purchase to cover about how many weeks?')
h('3. Before you leave home');p('[ ] Check that the store is licensed, open and serves your purchase type.<br/>[ ] Confirm payment methods, fees and total-price information.<br/>[ ] Adult-use: bring current government photo ID showing age 21+.<br/>[ ] Medical: bring active registry card and linked ID; recommendation must be active.<br/>[ ] Arrange travel so you will not drive while impaired.<br/>[ ] Have secure storage away from children and pets.')
p('Tell the staff: "I am a __________ buyer. I want __________. My budget is $____ total. I want a small, measurable trial amount and help understanding the label."','Body')
story.append(PageBreak())
p('Know the product before buying','Title')
table([['Product','Check the label and ask','Plan the quantity in'],['Flower / pre-rolls','Grams in package; batch THC/CBD; infused or plain; device and supplies needed. A strain name does not guarantee chemistry or effects.','Grams or whole pre-rolls. Puff size and device use vary.'],['Gummies / edibles','THC/CBD per piece, per serving and per package; allergens; whether dividing a piece is reliable. One gummy can contain several servings.','Pieces or reliably measured fractions. Calculate mg THC in that amount separately.'],['Concentrates / cartridges','Extract type, grams, THC/CBD, ingredients and compatible device. High potency can make small amounts difficult to measure.','Grams using your own measured use. Do not infer grams per puff.'],['Tincture / oral oil','THC/CBD in mg per mL; bottle mL; marked dropper; intended route. Swallowing and under-tongue use may differ.','mL measured with the supplied marked device; drops may be inconsistent.'],['Topicals','Ingredients, application directions, skin precautions and whether it is a transdermal product.','Applications using manufacturer directions; do not compare to oral THC doses.']],[108,295,125])
h('New-buyer starting reference');p('Health Canada advises new or occasional edible users to start with 2.5 mg THC or less and allow up to four hours for full effects before taking more. This is general lower-risk guidance, not a personal prescription. Consider a small trial purchase before planning a long supply.')
p('Inhaled effects can start within seconds to minutes and take up to 30 minutes to fully develop. Edible effects may begin after 30 minutes to two hours and take up to four hours to fully develop. Onset, peak, duration and impairment are different; response varies. Do not use a supply calculation to decide when you can drive.')
p('Ask a clinician or pharmacist about medication interactions or health concerns. Avoid combining with alcohol. Keep the product in its labeled container, locked away from children and pets. Higher-potency extracts can be difficult for beginners to measure.')
h('Ask the staff to write this down');line('Product / batch');line('THC and CBD per planned amount');line('How to measure / use it and how long to wait');line('Storage instructions / expiration date')
story.append(PageBreak())
p('How long will this purchase last?','Title');p('This page estimates supply duration, not the length of the high or the right dose. Use your own established amount, or leave it blank until you know your response. Use the same unit throughout each calculation.')
table([['Product / unit','Package quantity','Amount per use','Uses per week','Estimated weeks'],['Gummies / pieces','________','________','________','________'],['Flower / grams','________','________','________','________'],['Concentrate / grams','________','________','________','________'],['Oral oil / mL','________','________','________','________'],['Other: ______','________','________','________','________']],[120,102,102,102,102])
h('The arithmetic');p('<b>Uses per package</b> = package quantity / amount per use<br/><b>Weeks per package</b> = uses per package / uses per week<br/><b>Quantity needed</b> = amount per use x uses per week x target weeks<br/><b>Whole packages needed</b> = quantity needed / package quantity, rounded up')
p('<b>Gummy example:</b> 10 pieces / 0.25 piece = 40 uses. At 2 uses per week, this is 20 weeks. If each piece contains 10 mg THC, one-quarter piece contains a nominal 2.5 mg THC only if the product can be divided reliably. The arithmetic is an example, not a recommended schedule.')
p('<b>Flower example:</b> 3.5 g / an established 0.1 g per use = 35 uses. At 5 uses per week, this is 7 weeks. Grams do not establish absorbed THC or equivalent edible effects.')
p('<b>Oil example:</b> 30 mL / an established 0.25 mL per use = 120 uses. At 4 uses per week, this is 30 weeks. Multiply mL used by the labeled mg THC per mL to learn THC in that amount. Check whether the shelf life covers the estimated supply period.')
line('Final price with taxes / fees ($)');line('My trial amount / purchase decision');line('Notes after trying it: amount, timing and response')
h('Sources and more help');p('Sources checked October 11, 2026. Health guidance is general; the Ohio sources cover store entry and purchase documents.','SmallText')
for name,url in [('Health Canada: lower your risks','https://www.canada.ca/en/health-canada/services/drugs-medication/cannabis/resources/lower-your-risks.html'),('Ohio adult-use dispensing rule','https://codes.ohio.gov/ohio-administrative-code/rule-1301:18-8-08'),('Ohio: activating your medical marijuana card','https://com.ohio.gov/divisions-and-programs/cannabis-control/patients-caregivers/patient-and-caregiver-registry/activating-your-medical-marijuana-card')]:p('<link href="'+url+'">'+name+'</link>','SmallText')
p('<link href="https://travisvought-byte.github.io/ohio-cannabis-directory/buyer-guide.html">Online shopping worksheet and calculator</link><br/><link href="https://travisvought-byte.github.io/ohio-cannabis-directory/knowledge.html">Product definitions, processing and label guide</link>','SmallText')
SimpleDocTemplate(str(OUT),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=36,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
