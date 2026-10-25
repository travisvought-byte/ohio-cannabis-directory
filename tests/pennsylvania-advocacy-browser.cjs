const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const server=await require('./server.cjs')(),browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});
  await page.route('**/gc.zgo.at/**',r=>r.abort());
  await page.goto(server.base+'advocacy.html');
  await page.locator('a[href="pennsylvania-advocacy.html"]').click();
  assert.equal(new URL(page.url()).pathname,'/pennsylvania-advocacy.html');
  assert(await page.locator('nav[aria-label="Primary"]').isVisible());
  assert(await page.getByRole('heading',{name:'HB 20: bipartisan private-market proposal'}).isVisible());
  assert(await page.getByRole('heading',{name:'HB 1200: Pennsylvania Cannabis Stores model'}).isVisible());
  const senate=page.locator('article').filter({has:page.getByRole('heading',{name:'SB 120: Senate Cannabis Control Board proposal'})});
  assert(await senate.isVisible());
  assert.match(await senate.innerText(),/dropped from the calendar October 19, 2026/);
  assert(!await page.locator('section[aria-labelledby="sources"]').innerText().then(t=>t.includes('\\n')));
  for(const width of [390,1280]){
   await page.setViewportSize({width,height:844});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'horizontal overflow at '+width);
  }
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'/tmp/pa-advocacy-mobile.png',fullPage:true});
  await page.emulateMedia({media:'print'});
  assert(await page.locator('#status').isVisible());
  assert(await page.locator('#action').isVisible());
  assert(await page.locator('#sources').isVisible());
  assert(!await page.locator('nav[aria-label="Primary"]').isVisible());
  const context=await browser.newContext({javaScriptEnabled:false});
  const plain=await context.newPage();await plain.goto(server.base+'pennsylvania-advocacy.html');
  assert(await plain.locator('#action').isVisible());
  assert(await plain.locator('section[aria-labelledby="sources"] a[href$="/2025/hb20"]').isVisible());
  await context.close();
  console.log('PASS PA advocacy: discoverable entry, separate proposals, mobile/desktop width, print sources/actions, no-JavaScript access.');
 }finally{await browser.close();await server.close();}
})().catch(e=>{console.error(e);process.exit(1)});
