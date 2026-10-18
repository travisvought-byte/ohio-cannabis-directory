const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const server=await require('./server.cjs')(),browser=await chromium.launch({headless:true});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/gc.zgo.at/**',r=>r.abort());
  await page.goto(server.base+'expungement.html');
  assert.equal(await page.locator('.checklist > li').count(),6);
  assert.equal(await page.locator('.step-help[open]').count(),0);
  for (const id of ['online-search','eligibility-help','application-help','filing-help','hearing-help','follow-up-help']) {
   await page.locator('a[href="#'+id+'"]').first().click();
   assert(await page.locator('#'+id).evaluate(el=>el.open),id+' opens from main step');
   assert(await page.locator('#'+id+' a[href^="https://"]').first().isVisible());
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),id+' mobile width');
   await page.locator('#'+id+' > summary').click();
  }
  await page.goto(server.base+'expungement.html#filing-help');
  assert(await page.locator('#filing-help').evaluate(el=>el.open),'direct help URL opens panel');
  await page.locator('a[href="#online-search"]').first().click();
  await page.selectOption('#court-county','Morrow');
  assert.equal(await page.locator('#court-search-results article:visible').count(),2);
  assert((await page.locator('#court-count').textContent()).includes('Morrow'));
  await page.selectOption('#court-county','');
  assert.equal(await page.locator('#court-search-results article:visible').count(),9);
  await page.setViewportSize({width:1280,height:900});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.emulateMedia({media:'print'});
  assert.equal(await page.locator('.step-help:visible').count(),0);
  assert.equal(await page.locator('.checklist input:visible').count(),6);
  assert(await page.locator('.print-url').isVisible());
  assert.deepEqual(errors,[]);
  const plain=await browser.newContext({javaScriptEnabled:false}),fallback=await plain.newPage();
  await fallback.goto(server.base+'expungement.html');
  await fallback.locator('#online-search > summary').click();
  assert.equal(await fallback.locator('#court-search-results article:visible').count(),9);
  await fallback.locator('#filing-help > summary').click();
  assert(await fallback.locator('#filing-help a[href*="affidavits-of-indigency"]').isVisible());
  await plain.close();
  console.log('PASS: six-step help, direct links, county filtering, mobile/desktop width, checklist printing and no-JavaScript resources.');
 } finally {await browser.close();await server.close();}
})().catch(e=>{console.error(e);process.exit(1)});
