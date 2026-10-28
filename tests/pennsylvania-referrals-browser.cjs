const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const server=await require('./server.cjs')(),browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));await page.route('**/gc.zgo.at/**',r=>r.abort());
  await page.goto(server.base+'pennsylvania-advocacy.html');
  await page.locator('a[href="state.html?state=PA"]').click();
  await page.waitForFunction(()=>document.querySelector('#state-title').textContent==='Pennsylvania cannabis resources');
  assert.match(await page.locator('#state-select option:checked').innerText(),/pilot/);
  assert.match(await page.locator('#state-coverage').innerText(),/Pilot coverage/);
  assert.equal(await page.locator('#pathways a').count(),7);
  assert.equal(await page.locator('#pathways a').filter({hasText:'Not yet researched'}).count(),4);
  await page.selectOption('#path-select','medical');assert.equal(await page.locator('#state-results article').count(),2);
  assert.equal(await page.locator('#state-route').getAttribute('href'),'https://www.pa.gov/services/health/register-for-the-medical-marijuana-program');
  await page.locator('#svc-pa-mmap summary').click();assert.match(await page.locator('#svc-pa-mmap').innerText(),/PACE\/PACENET/);assert.match(await page.locator('#svc-pa-mmap details').innerText(),/Veteran status alone/);
  await page.selectOption('#path-select','records');assert.equal(await page.locator('#state-results article').count(),2);
  const local=page.locator('#svc-pa-npls-record-help');assert.match(await local.innerText(),/Monroe, PA; Pike, PA/);
  const route=await local.getByRole('link',{name:'Link to this route',exact:true}).getAttribute('href');
  await page.goto(route);await page.waitForSelector('#svc-pa-npls-record-help');assert.equal(await page.locator('#state-results article').count(),1);
  await page.selectOption('#path-select','dispensaries');assert.equal(await page.locator('#state-results article').count(),1);
  assert.equal(await page.locator('#svc-pa-dispensary-list .btn').getAttribute('href'),'https://www.pa.gov/agencies/health/programs/medical-marijuana/dispensaries');
  for(const need of ['seeds','rules','business','community']){
   await page.selectOption('#path-select',need);assert.equal(await page.locator('#state-results article').count(),0);
   assert.match(await page.locator('#state-coverage').innerText(),/Not yet researched/);assert(!await page.locator('#state-route').isVisible());
  }
  await page.selectOption('#path-select','medical');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:'/tmp/pa-referrals-mobile.png',fullPage:true});
  await page.emulateMedia({media:'print'});
  assert(await page.locator('#svc-pa-registration .print-route').isVisible());
  assert.match(await page.locator('#svc-pa-registration .print-route').innerText(),/pa.gov\/services\/health\/register/);
  await page.emulateMedia({media:'screen'});
  await page.selectOption('#state-select','OH');assert.equal(await page.locator('[id^="svc-pa-"]').count(),0);
  // Roster dispensaries appear in the finder; the legal-aid office does not.
  await page.goto(server.base+'locations.html?state=PA');await page.waitForFunction(()=>document.querySelectorAll('#cards article').length===200);
  assert.equal(await page.locator('#state option[value="PA"]').count(),1);
  assert.equal(await page.locator('#cards article',{hasText:'North Penn Legal Services'}).count(),0);
  await page.getByRole('searchbox',{name:'Search',exact:true}).fill('Stroudsburg');
  assert.equal(await page.locator('#cards article').count(),2);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const plain=await browser.newContext({javaScriptEnabled:false}),fallback=await plain.newPage();
  await fallback.goto(server.base+'state.html?state=PA');
  assert(await fallback.getByRole('heading',{name:'Pennsylvania pilot referral routes'}).isVisible());
  assert(await fallback.getByRole('link',{name:'Monroe and Pike County legal-help intake',exact:true}).isVisible());
  await plain.close();assert.deepEqual(errors,[]);
  console.log('PASS PA referrals: pilot/gap labels, five routes, county scope, citations, deep links, no-JS access, Ohio/store isolation and mobile width.');
 }finally{await browser.close();await server.close();}
})().catch(e=>{console.error(e);process.exit(1)});
