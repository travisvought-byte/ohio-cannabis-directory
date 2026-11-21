// Browser checks for the store and dispensary maps (November 21, 2026): the map follows the filters, the list beside it
// works by mouse and keyboard, "near me" lists the closest places, phones fit in light and dark, reduced motion stops
// the animation, and without JavaScript the map stays hidden while the cards and tables remain.
// Outside requests (the OpenStreetMap pictures, the visit counter) are blocked, so only this site's own files load.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),TYPES={'.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.svg':'image/svg+xml','.html':'text/html'};
 const server=http.createServer((req,res)=>{const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(root,'.'+name);
  if(!file.startsWith(root+path.sep)){res.statusCode=404;return res.end()}
  try{res.setHeader('Content-Type',TYPES[path.extname(file)]||'text/plain');res.end(fs.readFileSync(file))}catch{res.statusCode=404;res.end()}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base='http://127.0.0.1:'+server.address().port+'/';
 const browser=await chromium.launch({headless:true});
 const open=async(ctx,pg,ready)=>{const p=await ctx.newPage(),errs=[];p.on('pageerror',e=>errs.push(e.message));
  await p.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());await p.goto(base+pg);
  await p.waitForFunction(sel=>document.querySelectorAll(sel).length>0,ready||'.pm-list .pm-hit');await p.waitForTimeout(700);p.errs=errs;return p;};
 const settle=p=>p.waitForTimeout(500);
 const fits=p=>p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
 try{
  // Ohio dispensaries: the map shows with the cards, the list beside it holds the closest, the filters move the map
  const ctx=await browser.newContext({viewport:{width:1280,height:900}});
  let p=await open(ctx,'locations.html?state=OH');
  assert(await p.isVisible('#loc-map .pm-map'),'map shows');assert.equal(await p.locator('#cards article').count(),230,'every card stays');
  assert(await p.locator('#loc-map .marker-cluster').count()>0,'pins close together are grouped');
  const hits=await p.locator('#loc-map .pm-hit').count();assert(hits>0&&hits<=40,'up to 40 closest listed beside the map');
  assert.match(await p.textContent('#loc-map .pm-count'),/4 more have no map point and are only in the list below\./,'locations with no map point are counted, not dropped');
  assert.equal(await p.textContent('#loc-map .pm-head'),'Closest to the middle of the map');
  await p.selectOption('#city','Columbus');await settle(p);
  const subs=await p.locator('#loc-map .pm-sub').allTextContents();assert(subs.length>0&&subs.every(s=>s.includes('Columbus')),'the map follows the city filter');
  assert.match(await p.textContent('#loc-map .pm-count'),/^2[0-9] locations in view\./,'the Columbus dispensaries are all in view');
  // the list opens the pin's details, by mouse and by keyboard; Details jumps to the card
  const first=p.locator('#loc-map .pm-name').first(),name=(await first.textContent()).replace(' — show on the map','');
  await first.click();await p.waitForSelector('.leaflet-popup-content');assert((await p.textContent('.leaflet-popup-content')).includes(name),'the list opens the pin');
  await p.waitForFunction(n=>[...document.querySelectorAll('#loc-map .pm-name[aria-pressed=true]')].map(b=>b.textContent).join()===n+' — show on the map',name,{timeout:5000});
  assert(await p.locator('.leaflet-popup-content a',{hasText:'Directions'}).count()===1,'directions from the pin');
  await p.keyboard.press('Escape');const second=p.locator('#loc-map .pm-name').nth(1);await p.keyboard.press('Shift');await second.focus();
  assert.equal(await p.evaluate(()=>getComputedStyle(document.activeElement).outlineStyle),'solid','focused list button shows a ring');
  const name2=(await second.textContent()).replace(' — show on the map','');await p.keyboard.press('Enter');await p.waitForFunction(n=>(document.querySelector('.leaflet-popup-content')||{}).textContent?.includes(n),name2);
  const sizes=await p.$$eval('#loc-map .pm-name, #loc-map .pm-acts a',bs=>bs.map(b=>b.getBoundingClientRect().height));assert(sizes.every(h=>h>=44),'list buttons and links are easy to tap');
  const details=p.locator('#loc-map .pm-hit').first().locator('a',{hasText:'Details'});const target=(await details.getAttribute('href')).slice(1);
  await details.click();assert.equal(new URL(p.url()).hash,'#'+target,'Details jumps to the card');assert(await p.locator('#'+target).isVisible());
  // another state: the map moves there
  await p.selectOption('#state','PA');await settle(p);
  assert.match(await p.textContent('#loc-map .pm-count'),/37 more have no map point/);assert((await p.locator('#loc-map .pm-sub').allTextContents()).every(s=>/, PA|[A-Z]/.test(s)));
  assert(!(await p.textContent('#loc-map .pm-list')).includes('Columbus'),'only Pennsylvania on the map');
  assert.deepEqual(p.errs,[],'no script errors');assert.equal(await p.evaluate(()=>localStorage.length+sessionStorage.length),0,'nothing stored');
  await ctx.close();

  // near me: the map centers on the visitor and lists the closest first; Reset clears it
  const here=await browser.newContext({viewport:{width:1280,height:900},geolocation:{latitude:39.9612,longitude:-82.9988},permissions:['geolocation']});
  p=await open(here,'locations.html?state=OH');await p.click('#near');await p.waitForFunction(()=>document.querySelector('#loc-map .pm-head').textContent==='Closest to you');
  const near=await p.locator('#loc-map .pm-sub').first().textContent();assert.match(near,/ mi from you$/,'distances from the visitor');assert(parseFloat(near.split(' · ').pop())<5,'the closest is in Columbus');
  assert(!new URL(p.url()).search.includes('39.96'),'the location never goes in the address');
  await p.click('#reset');await settle(p);assert.equal(await p.textContent('#loc-map .pm-head'),'Closest to the middle of the map');
  // on the Ontario store page, the map's own button
  p=await open(here,'national/world-canada-stores.html');assert(await p.isVisible('.placemap .pm-locate'),'near-me button shows where location works');
  await here.close();

  // Ontario: 1,916 stores from the table, the table's search narrows the map
  const wide=await browser.newContext({viewport:{width:1280,height:900}});
  p=await open(wide,'national/world-canada-stores.html');
  assert.match(await p.textContent('.placemap .pm-count'),/of 1,916 stores in view/,'every Ontario store with a map point');
  await p.fill('#wtb-ontario-q','Ottawa');await p.waitForFunction(()=>[...document.querySelectorAll('.placemap .pm-sub')].every(s=>s.textContent.toLowerCase().includes('ottawa')));
  const shown=await p.$$eval('#wtb-ontario tbody tr',rs=>rs.filter(r=>!r.hidden).length);
  const listed=await p.textContent('.placemap .pm-count');assert(listed.includes(String(shown))||/closest of/.test(listed),'map and table agree: '+listed+' / '+shown);
  const see=p.locator('.placemap .pm-hit').first().locator('a',{hasText:'See it in the table'});const row=(await see.getAttribute('href')).slice(1);await see.click();
  assert(await p.locator('#'+row).isVisible(),'the list leads to the table row');
  assert.deepEqual(p.errs,[]);
  // Amsterdam coffeeshops
  p=await open(wide,'national/world-netherlands.html');assert.match(await p.textContent('.placemap .pm-count'),/of 138 coffeeshops in view/);
  await p.fill('#cs-filter','Haarlemmerstraat');await p.waitForFunction(()=>[...document.querySelectorAll('.placemap .pm-sub')].every(s=>s.textContent.toLowerCase().includes('haarlemmerstraat')));
  assert.deepEqual(p.errs,[]);await wide.close();

  // phones, light and dark: everything fits a 320 px screen; dark pages darken the street pictures
  for(const scheme of ['light','dark']){const ph=await browser.newContext({viewport:{width:320,height:700},colorScheme:scheme});
   for(const pg of ['locations.html?state=NY','national/world-canada-stores.html','national/world-netherlands.html']){p=await open(ph,pg);assert(await fits(p),pg+' fits a 320 px screen ('+scheme+')');assert(await p.isVisible('.pm-map'));}
   const filter=await p.evaluate(()=>getComputedStyle(document.querySelector('.leaflet-tile-pane')).filter);assert.equal(filter!=='none',scheme==='dark','street pictures darkened only in dark mode');
   await ph.close();}

  // reduced motion
  const rm=await browser.newContext({reducedMotion:'reduce'});p=await open(rm,'locations.html?state=OH');assert(!(await p.getAttribute('#loc-map .pm-map','class')).includes('leaflet-fade-anim'),'no map animation');await rm.close();

  // without JavaScript: no empty map; the Ontario and Amsterdam tables keep their own map links
  const nojs=await browser.newContext({javaScriptEnabled:false});p=await nojs.newPage();await p.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());
  await p.goto(base+'locations.html');assert(await p.isHidden('#loc-map'));
  await p.goto(base+'national/world-canada-stores.html');assert(await p.isHidden('.placemap'));assert(await p.locator('#wtb-ontario a',{hasText:'Map'}).first().isVisible());await nojs.close();
  console.log('PASS place maps: Ohio, Pennsylvania and New York dispensaries, Ontario stores and Amsterdam coffeeshops on clustered maps that follow the filters, list beside the map by mouse and keyboard, near me, 320 px phones in light and dark, reduced motion and no-JavaScript paths.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
