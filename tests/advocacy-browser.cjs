const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const server=await require('./server.cjs')(),browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
  await page.route('**/gc.zgo.at/**',r=>r.abort());await page.goto(server.base+'advocacy.html');
  assert(await page.locator('#compose-fields').isVisible());assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.locator('#recipient').fill('Representative Example');await page.locator('#town').fill('Marengo');
  await page.locator('#sender').fill('Private test name');await page.locator('#reason').fill('PRIVATE_REASON_123 <b>keep as text</b>');
  await page.locator('input[value="outofstate"]').uncheck();await page.locator('#build').click();
  const draft=await page.locator('#letter').inputValue();assert(draft.includes('Marengo'));assert(draft.includes('PRIVATE_REASON_123'));assert(!draft.includes('another state'));
  await page.locator('#letter').fill(draft+'\nManual edit.');await page.locator('#town').fill('Columbus');
  assert((await page.locator('#letter').inputValue()).includes('Manual edit.'));
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('denied'))},configurable:true}));
  await page.locator('#copy').click();assert.match(await page.locator('#status').textContent(),/selected/);
  assert.equal(await page.locator('#letter').evaluate(el=>el.selectionEnd-el.selectionStart),(await page.locator('#letter').inputValue()).length);
  const event=page.waitForEvent('download');await page.locator('#download').click();const download=await event;
  assert.equal(download.suggestedFilename(),'ohio-cannabis-constituent-letter.txt');assert.equal(fs.readFileSync(await download.path(),'utf8'),await page.locator('#letter').inputValue());
  await page.emulateMedia({media:'print'});assert(await page.locator('#print-letter').isVisible());assert(!(await page.locator('#letter').isVisible()));assert.match(await page.locator('#print-letter').textContent(),/Manual edit/);assert.equal(await page.locator('#print-letter b').count(),0);
  await page.emulateMedia({media:'screen'});
  for(const el of await page.locator('input[name="priority"]').all())await el.uncheck();await page.locator('#build').click();assert.match(await page.locator('#status').textContent(),/at least one/);assert.match(await page.locator('#letter').inputValue(),/Manual edit/);
  assert.equal(await page.evaluate(()=>localStorage.length),0);assert.equal(await page.evaluate(()=>sessionStorage.length),1);assert(!requests.some(url=>url.includes('PRIVATE_REASON_123')||url.includes('Marengo')));
  await page.screenshot({path:'/tmp/advocacy-mobile.png',fullPage:true});
  await page.reload();assert((await page.locator('#letter').inputValue()).includes('PRIVATE_REASON_123'));assert((await page.locator('#letter').inputValue()).includes('Manual edit.'));
  for(const key of ['homegrow','patients','beverages','independent','ownership','equity','reinvestment'])await page.locator('input[value="'+key+'"]').check();
  await page.locator('#build').click();const expanded=await page.locator('#letter').inputValue();assert.match(expanded,/home-grow/);assert.match(expanded,/medical patient/);assert.match(expanded,/THC beverages/);assert.match(expanded,/independent Ohio/);assert.match(expanded,/ownership/);assert.match(expanded,/36%/);assert.match(expanded,/disproportionately harmed/);assert.match(expanded,/community outcomes/);
  await page.locator('#sent-date').fill('2026-10-16');assert.match(await page.locator('#followup-date').textContent(),/October 30, 2026/);
  const backupEvent=page.waitForEvent('download');await page.locator('#download-notes').click();const backup=await backupEvent,backupPath=await backup.path();assert.equal(JSON.parse(fs.readFileSync(backupPath,'utf8')).version,2);
  await page.locator('#letter').fill('Changed after backup');await page.locator('#restore-work').setInputFiles(backupPath);await page.waitForFunction(()=>document.getElementById('status').textContent.includes('Backup restored'));assert.equal(await page.locator('#letter').inputValue(),expanded);
  const beforeInvalid=await page.locator('#letter').inputValue();await page.locator('#restore-work').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({version:2,fields:{recipient:'changed'},priorities:['homegrow']}))});await page.waitForFunction(()=>document.getElementById('status').textContent.includes('could not be restored'));assert.equal(await page.locator('#letter').inputValue(),beforeInvalid);
  const readableEvent=page.waitForEvent('download');await page.locator('#download-readable').click();const readable=await readableEvent;assert.match(fs.readFileSync(await readable.path(),'utf8'),/OHIO CANNABIS ADVOCACY NOTES/);
  assert.equal(await page.locator('#letter-actions a').getAttribute('target'),'_blank');
  await page.locator('[data-priorities]').click();assert.equal(await page.locator('input[name="priority"]:checked').count(),2);assert(await page.locator('input[value="equity"]').isChecked());
  page.once('dialog',dialog=>dialog.accept());await page.locator('#clear-work').click();assert.equal(await page.locator('#letter').inputValue(),'');assert.equal(await page.evaluate(()=>sessionStorage.length),0);

  await page.setViewportSize({width:1280,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:'/tmp/advocacy-desktop.png',fullPage:true});assert.deepEqual(errors,[]);
  const plain=await browser.newContext({javaScriptEnabled:false}),fallback=await plain.newPage();await fallback.goto(server.base+'advocacy.html');assert(await fallback.locator('#letter').isVisible());assert(await fallback.locator('noscript').isVisible());await plain.close();
  console.log('PASS: advocacy mobile width, personalized draft, preserved edits, empty selection, clipboard fallback, text download, print, session restore, new policy choices, backup import validation, readable notes, clearing saved work, privacy and no-JS fallback.');
 }finally{await browser.close();await server.close();}
})().catch(e=>{console.error(e);process.exit(1)});
