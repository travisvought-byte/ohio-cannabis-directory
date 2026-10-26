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
  const requests=[];
  page.on('request',request=>requests.push(request.url()+' '+(request.postData()||'')));
  await page.evaluate(()=>{
   window.paEvents=[];
   window.goatcounter.count=e=>(window.paEvents||(window.paEvents=[])).push(e);
   Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.paCopied=text;}}});
  });
  assert(await page.locator('#pa-copy').isDisabled());
  await page.locator('#pa-place').fill('PRIVATE_TOWN_58');
  await page.locator('#pa-reason').fill('PRIVATE_REASON_58 <script>not executable</script>');
  await page.locator('#pa-build').click();
  assert.match(await page.locator('#pa-draft').inputValue(),/independent Pennsylvania businesses/);
  const edited=(await page.locator('#pa-draft').inputValue())+'\nMy own closing.\n';
  await page.locator('#pa-draft').fill(edited);
  await page.locator('#pa-topic').selectOption('patients');
  assert.equal(await page.locator('#pa-draft').inputValue(),edited,'topic changes preserve edits');
  assert.match(await page.locator('#pa-letter-status').innerText(),/preserved/);
  await page.locator('#pa-copy').click();
  assert.equal(await page.evaluate(()=>window.paCopied),edited,'copy exact edited draft');
  const downloadPromise=page.waitForEvent('download');
  await page.locator('#pa-download').click();
  const download=await downloadPromise;
  assert.equal(download.suggestedFilename(),'pennsylvania-cannabis-message.txt');
  assert.equal(require('node:fs').readFileSync(await download.path(),'utf8'),edited);
  await page.emulateMedia({media:'print'});
  await page.evaluate(()=>{window.print=()=>{window.paPrinted={text:document.getElementById('pa-letter-print').textContent,main:getComputedStyle(document.querySelector('main')).display,letter:getComputedStyle(document.getElementById('pa-letter-print')).display};};});
  await page.locator('#pa-print').click();
  assert.deepEqual(await page.evaluate(()=>window.paPrinted),{text:edited,main:'none',letter:'block'});
  assert(!await page.locator('body').evaluate(el=>el.classList.contains('pa-print-letter')));
  await page.emulateMedia({media:'screen'});
  await page.evaluate(()=>{navigator.clipboard.writeText=async()=>{throw Error('denied');};});
  await page.locator('#pa-copy').click();
  assert.match(await page.locator('#pa-letter-status').innerText(),/use your device/);
  assert.equal(await page.locator('#pa-draft').evaluate(el=>el.value.slice(el.selectionStart,el.selectionEnd)),edited);
  await page.locator('#pa-build').click();
  assert.match(await page.locator('#pa-draft').inputValue(),/medical patient access/);
  assert(!(await page.locator('#pa-draft').inputValue()).includes('My own closing.'));
  for(const [topic,phrase] of [['market','independent Pennsylvania'],['equity','record-clearing'],['local','tax revenue']]){
   await page.locator('#pa-topic').selectOption(topic);await page.locator('#pa-build').click();
   assert((await page.locator('#pa-draft').inputValue()).includes(phrase));
  }
  assert(!requests.join('\n').includes('PRIVATE_'),'personal text never sent over network');
  assert(!await page.evaluate(()=>JSON.stringify(window.paEvents).includes('PRIVATE_')),'analytics excludes text');
  assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0,'no stored draft');
  await page.locator('#pa-clear').click();
  for(const id of ['pa-place','pa-reason','pa-draft'])assert.equal(await page.locator('#'+id).inputValue(),'');
  assert.equal(await page.locator('#pa-letter-print').textContent(),'');
  assert(await page.locator('#pa-print').isDisabled());
  await page.reload();assert.equal(await page.locator('#pa-draft').inputValue(),'');
  const senate=page.locator('article').filter({has:page.getByRole('heading',{name:'SB 120: Senate Cannabis Control Board proposal'})});
  assert(await senate.isVisible());
  assert.match(await senate.innerText(),/dropped from the calendar October 19, 2026/);
  assert(!await page.locator('section[aria-labelledby="sources"]').innerText().then(t=>t.includes('\\n')));
  for(const width of [320,390,1280]){
   await page.setViewportSize({width,height:844});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'horizontal overflow at '+width);
  }
  await page.setViewportSize({width:390,height:844});
  await page.locator('#pa-letter-builder').screenshot({path:'/tmp/pa-letter-mobile.png'});
  await page.screenshot({path:'/tmp/pa-advocacy-mobile.png',fullPage:true});
  await page.emulateMedia({media:'print'});
  assert(await page.locator('#status').isVisible());
  assert(await page.locator('#action').isVisible());
  assert(await page.locator('#sources').isVisible());
  assert(!await page.locator('nav[aria-label="Primary"]').isVisible());
  const context=await browser.newContext({javaScriptEnabled:false});
  const plain=await context.newPage();await plain.goto(server.base+'pennsylvania-advocacy.html');
  assert(await plain.locator('#action').isVisible());
  assert(!await plain.locator('#pa-letter-builder').isVisible());
  assert(await plain.locator('noscript p').isVisible());
  assert(await plain.locator('section[aria-labelledby="sources"] a[href$="/2025/hb20"]').isVisible());
  await context.close();
  console.log('PASS PA advocacy: discoverability, proposals, explicit rebuild/edit preservation, exact copy/download/letter-print, copy fallback, privacy/clear, mobile, no-JavaScript.');
 }finally{await browser.close();await server.close();}
})().catch(e=>{console.error(e);process.exit(1)});
