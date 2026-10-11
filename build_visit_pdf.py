from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
OUT=Path('assets/dispensary-visit-companion.pdf')
c=canvas.Canvas(str(OUT),pagesize=(612,792));c.setTitle('Dispensary visit handoff and experience journal')
def header(title,sub,page):
 c.setFillColor(HexColor('#a90000'));c.rect(36,730,540,5,fill=1,stroke=0);c.setFillColor(HexColor('#252525'));c.setFont('Helvetica-Bold',22);c.drawString(36,695,title);c.setFont('Helvetica',10);c.drawString(36,673,sub);c.setFont('Helvetica',8);c.drawString(36,26,'Ohio Cannabis Directory | Personal worksheet | October 2026');c.drawRightString(576,26,str(page))
def field(label,y,lines=1):
 c.setFont('Helvetica-Bold',11);c.drawString(36,y,label);c.setStrokeColor(HexColor('#bbbbbb'))
 for i in range(lines):c.line(36,y-23-i*23,576,y-23-i*23)
def text(lines,y):
 c.setFont('Helvetica',10)
 for line in lines:c.drawString(36,y,line);y-=15
header('My dispensary visit plan','Complete before you go. Share only what you choose with dispensary staff.',1)
field('What am I trying to accomplish? What do I want to ask?',638,2)
field('Experience: first time / occasional / returning / experienced with a new form',553)
field('Product: gummies / flower / concentrate / tincture or oil / topical / unsure',497)
field('Budget including taxes, fees and any device:',441)
field('Preferences, ingredients to avoid, and questions for my clinician:',385)
field('Label: THC per piece or mL ______  CBD ______  Package quantity ______',329)
field('My planned amount per use ______  Uses per week ______  Target weeks ______',273)
text(['Supply estimate: package quantity / amount per use / uses per week = weeks.',
      'Use matching units (pieces, mL or grams). Actual use, waste and shelf life may differ.',
      'Label math: mg per piece or mL x amount = labeled mg per use.',
      'For weight percent: percent x grams x 10 = labeled mg; absorption differs.',
      'These calculations do not recommend an amount or predict effects.'],223)
text(['Ask staff: THC/CBD? How to measure? Onset and duration? Testing and allergens?',
      'Final price? Required device? Secure storage and expiration? Confirm ID/payment.',
      'Start with a small trial purchase when your response is unknown.'],129)
text(['Do not drive impaired. Avoid alcohol. Lock products away from children and pets.',
      'Discuss medicines and health concerns with a clinician or pharmacist.'],72)
c.showPage()
header('My experience journal','Keep for your own reference. Responses vary; a journal does not establish a safe dose.',2)
field('Date / time _________  Product / brand / batch ______________________',638)
field('Form / route _________  THC _________  CBD _________  Label unit _________',582)
field('Amount used _________  Labeled content _________  Intended goal _________',526)
field('When did effects begin? When were they strongest? When did they fade?',470,2)
field('What did I notice? Helpful effects, unwanted effects, or no change:',385,3)
field('Context: food, sleep, other substances, and relevant medicines:',277,2)
field('Questions for staff or a clinician before a future purchase:',192,2)
text(['Keep notes private. Do not use this worksheet to justify driving or early redosing.',
      'Inspired by New York Office of Cannabis Management consumer education.',
      'General education: cannabis.ny.gov and canada.ca/cannabis.',
      'For shopping education and Ohio resources, return to the directory buyer guide.'],105)
c.save()
