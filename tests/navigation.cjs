const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const links=[['Pennsylvania directory','pennsylvania-directory.html'],['Pennsylvania portal','state.html?state=PA'],['Record clearing','expungement.html'],['Advocacy','advocacy.html'],['Compare states','compare.html'],['Find a dispensary','locations.html'],['Shop smart','buyer-guide.html'],['Strains','ancestry.html'],['Learn','knowledge.html'],['Business directory','directory.html'],['Business self-check','assessment.html']];
for(const name of fs.readdirSync('.').filter(n=>n.endsWith('.html'))){const d=new JSDOM(fs.readFileSync(name,'utf8')).window.document;
if(name==='work-with-travis.html'){
  const nav=d.querySelector('nav[aria-label="Site navigation"]');
  assert(nav,'independent commercial page navigation');
  assert(nav.querySelector('a[href="index.html"]'),'return to public directory');
  assert(d.querySelector('a[data-track="commercial-contact-top"][href="https://www.linkedin.com/in/travisvought/"]'),'verified professional inquiry path');
  assert(d.querySelector('a[data-track="commercial-contact-bottom"]'),'second inquiry opportunity');
  assert(d.querySelector('meta[name="description"]'),'commercial meta description');
  assert(!d.querySelector('a[href*="/donate"]'),'commercial page must not collect VHG donations');
  assert(fs.statSync(name).size<200000,'commercial page HTML budget');
  continue;
}
const nav=d.querySelector('nav[aria-label="Primary"]');assert(nav,name+' primary navigation');for(const [label,href] of links)assert([...nav.querySelectorAll('a')].some(a=>a.textContent===label&&a.getAttribute('href')===href),name+': '+label);assert(nav.textContent.includes('Veteran Resident Guide'));assert.equal(nav.querySelectorAll('a')[1].textContent,'Pennsylvania directory');assert(d.querySelector('.site-footer a[href="state.html?state=PA"]'));assert(d.querySelector('.site-footer'),name+' footer');assert(d.title.endsWith(' | Ohio Cannabis Directory'));assert(fs.statSync(name).size<200000,name+' initial HTML budget');for(const key of ['og:title','og:description','og:image'])assert(d.querySelector('meta[property="'+key+'"]'),name+' '+key);assert(d.querySelector('meta[name="description"]'));}
const home=fs.readFileSync('index.html','utf8');assert(home.includes("location.replace('directory.html'+location.search+location.hash)"));assert(home.includes('<h1>Ohio Cannabis Industry Directory</h1>'));assert.equal(new JSDOM(home).window.document.querySelectorAll('nav[aria-label="Primary"] a[href="directory.html"]').length,1);assert(!home.includes('id="home-search"'));console.log('PASS: industry directory first, consistent navigation and preserved URL parameters.');
