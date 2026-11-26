// Check the live game: Mildew's name in the Nassau tavern, and her nickname answer.
const {chromium} = require('playwright');
const fs = require('fs');
const OUT = 'tools/pillage-ad/live-check';
fs.mkdirSync(OUT, {recursive: true});
const log = [];
const say = (...a) => { const s = a.join(' '); log.push(s); console.log(s); };
(async () => {
  const browser = await chromium.launch({headless: true});
  const ctx = await browser.newContext({viewport: {width: 540, height: 760}, deviceScaleFactor: 2});
  await ctx.route('**/*', r => /goatcounter|analytics/i.test(r.request().url()) ? r.abort() : r.continue());
  const page = await ctx.newPage();
  page.on('pageerror', e => say('PAGE ERROR', e.message));
  page.on('request', r => { if (/pillage\/data\.js/.test(r.url())) say('loads', r.url()); });
  await page.goto('https://the-reefer.com/pillage/?check=' + Date.now(), {waitUntil: 'networkidle'});
  await page.waitForSelector('#btn-new');
  await page.click('#btn-new');
  await page.waitForSelector('#cap-ok');
  await page.click('#cap-ok');
  await page.waitForTimeout(800);
  // Close the start-up dialogs and let the game cast off before docking at Nassau (a first visit opens the tavern).
  await page.evaluate(() => document.querySelectorAll('dialog[open]').forEach(d => d.close()));
  await page.waitForTimeout(600);
  await page.evaluate(() => window.__pillage.dock('nassau'));
  await page.waitForTimeout(800);
  await page.evaluate(() => { if (!document.getElementById('dlg-port').open) window.__pillage.openPort('nassau', 'tavern'); else window.__pillage.showTab('tavern'); });
  await page.waitForTimeout(400);
  say('DOCKED', JSON.stringify(await page.evaluate(() => window.__pillage.state.docked)));
  say('PORT', JSON.stringify(await page.textContent('#port-title')));
  await page.waitForSelector('#port-panel .npc h3');
  const name = await page.textContent('#port-panel .npc h3');
  const role = await page.textContent('#port-panel .npc .role');
  say('NAME', JSON.stringify(name));
  say('ROLE', JSON.stringify(role));
  await page.locator('#dlg-port').screenshot({path: OUT + '/tavern.png'});
  const ask = page.locator('#port-panel button', {hasText: 'Why do they call you Mildew?'});
  if (await ask.count()) {
    await ask.first().click();
    await page.waitForTimeout(300);
    say('ANSWER', JSON.stringify(await page.textContent('#npc-says')));
    await page.locator('#dlg-port').screenshot({path: OUT + '/tavern-nickname.png'});
  } else say('NO NICKNAME QUESTION');
  say(name.includes('Mildew') && !name.includes('[object') ? 'RESULT OK' : 'RESULT BROKEN');
  fs.writeFileSync(OUT + '/log.txt', log.join('\n') + '\n');
  await browser.close();
})().catch(e => { say('FAILED', e.stack); fs.writeFileSync(OUT + '/log.txt', log.join('\n') + '\n'); process.exit(0); });
