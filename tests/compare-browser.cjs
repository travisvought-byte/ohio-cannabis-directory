const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const server=await require('./server.cjs')(),browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
  await page.route('**/gc.zgo.at/**',r=>r.abort());await page.goto(server.base+'compare.html');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no horizontal scroll on a phone');
  assert.equal(await page.locator('#topic-license-limits .state').count(),3);
  assert(await page.locator('#topic-growing-space .state.missing').count()>=1,'unreviewed states are labeled');
  assert.match(await page.locator('.assessment .tag').first().textContent(),/analysis, not fact/);
  for(const href of await page.locator('.cites a').evaluateAll(as=>as.map(a=>a.getAttribute('href'))))assert.equal(await page.locator(href).count(),1,href+' resolves to a listed source');
  const key='oversupply-price-collapse',letter=page.locator('#letter-'+key);
  assert.match(await letter.inputValue(),/Keep the requests you agree with/);
  await page.locator('#form-'+key+' input[value="publish-data"]').check();
  await page.locator('#town-'+key).fill('PRIVATE_TOWN_123');await page.locator('#name-'+key).fill('Private Tester');
  let draft=await letter.inputValue();assert.match(draft,/PRIVATE_TOWN_123, Ohio/);assert.match(draft,/publish, each year/);assert.doesNotMatch(draft,/House Bill 4121/);assert.match(draft,/Private Tester$/);
  await letter.fill(draft+'\nManual edit.');await page.locator('#town-'+key).fill('Columbus');
  assert.match(await letter.inputValue(),/Manual edit\./,'manual edits survive later field changes');
  assert.match(await page.locator('#status-'+key).textContent(),/edits are kept/);
  await page.locator('#rebuild-'+key).click();assert.doesNotMatch(await letter.inputValue(),/Manual edit/);assert.match(await letter.inputValue(),/Columbus, Ohio/);
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('denied'))},configurable:true}));
  await page.locator('#copy-'+key).click();assert.match(await page.locator('#status-'+key).textContent(),/copied/);
  assert(!requests.some(url=>url.includes('PRIVATE_TOWN_123')||url.includes('Private')),'letter details never leave the page');
  assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);
  await page.setViewportSize({width:1280,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.deepEqual(errors,[]);
  const plain=await browser.newContext({javaScriptEnabled:false}),fallback=await plain.newPage();await fallback.goto(server.base+'compare.html');
  assert.match(await fallback.locator('#letter-'+key).inputValue(),/Keep the requests you agree with/);await plain.close();
  console.log('PASS: state comparison mobile width, labeled assessment, resolvable citations, letter choices, preserved edits, start over, clipboard fallback, privacy and no-JS letter.');
 }finally{await browser.close();await server.close();}
})().catch(e=>{console.error(e);process.exit(1)});
