// Check the live MJBizCon week board: tallies counted, carried in the score link and QR code, breakout boards
// with titles on another player's phone, an old (version 1) code still accepted, and no page errors.
const {chromium} = require('playwright');
const fs = require('fs');
const OUT = 'tools/pillage-ad/live-board';
fs.mkdirSync(OUT, {recursive: true});
const log = [], bad = [];
const say = (...a) => { const s = a.join(' '); log.push(s); console.log(s); };
const check = (ok, what) => { say(ok ? 'OK  ' : 'BAD ', what); if (!ok) bad.push(what); };
const URL0 = 'https://the-reefer.com/pillage/';
const seal1 = x => { let h = 0x811c9dc5; x = 'pillage:' + x; for (let i = 0; i < x.length; i++) { h ^= x.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return ('0000' + h.toString(36)).slice(-4); };
const b64 = x => Buffer.from(x, 'utf8').toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
async function ctxFor(browser, opts) {
  const ctx = await browser.newContext(opts);
  await ctx.route('**/*', r => /goatcounter|analytics/i.test(r.request().url()) ? r.abort() : r.continue());
  return ctx;
}
function watch(page, name, errs) {
  page.on('pageerror', e => { errs.push(name + ': ' + e.message); say('PAGE ERROR', name, e.message); });
  page.on('response', r => { if (/pillage\/[a-z]+\.(js|css)/.test(r.url())) say(name, 'loads', r.status(), r.url().replace(/^https:\/\/the-reefer\.com/, '')); });
}
(async () => {
  let live = false;
  for (let i = 0; i < 40 && !live; i++) {
    try {
      const h = await (await fetch(URL0 + '?c=' + Date.now())).text();
      const d = await (await fetch(URL0 + 'data.js?v=13&c=' + Date.now())).text();
      live = /game\.js\?v=12/.test(h) && /Smuggler Supreme/.test(d) && /share-stats/.test(h);
    } catch (e) { say('fetch failed', e.message); }
    if (!live) await new Promise(r => setTimeout(r, 15000));
  }
  check(live, 'the new page, data.js and game.js are live');
  const browser = await chromium.launch({headless: true});
  const errs = [];
  // Anne plays on her phone
  const A = await ctxFor(browser, {viewport: {width: 390, height: 844}, deviceScaleFactor: 2});
  const pa = await A.newPage(); watch(pa, 'anne', errs);
  await pa.goto(URL0 + '?check=' + Date.now(), {waitUntil: 'networkidle'});
  await pa.click('#btn-new');
  await pa.waitForSelector('#cap-ok');
  await pa.fill('#cap-name', 'Anne Bonny'); await pa.fill('#cap-ship', 'the Revenge');
  await pa.click('#cap-ok');
  await pa.waitForTimeout(800);
  await pa.evaluate(() => document.querySelectorAll('dialog[open]').forEach(d => d.close()));
  await pa.waitForTimeout(400);
  const a = await pa.evaluate(() => {
    const P = window.__pillage, D = window.PILLAGE_DATA, sg = Object.keys(D.SMOKE).find(g => P.sellAt('havana', g) > 0);
    P.state.cargo[sg] = 6;
    const sold = !!P.sellBales('havana', sg, 3), smoked = P.smoke(sg);
    P.state.pillaged = 4; P.state.sunk = 2; P.gainXp(500);
    const best = P.myBest();
    return {sold, smoked, counts: [P.state.sold, P.state.smoked], st: best.st, link: P.scoreLink(best), stats: D.BOARD.stats.map(S => S.board)};
  });
  say('ANNE', JSON.stringify(a));
  check(a.sold && a.smoked && a.counts[0] === 3 && a.counts[1] === 1, 'selling 3 bales and smoking 1 is counted');
  check(a.st.sold === 3 && a.st.smoked === 1 && a.st.pillaged === 4 && a.st.sunk === 2 && a.st.days >= 1, 'her best voyage carries the tallies');
  check(/^https:\/\/the-reefer\.com\/pillage\/\?vs=[A-Za-z0-9_-]+$/.test(a.link), 'the score link is clean: ' + a.link.length + ' characters');
  await pa.evaluate(() => window.__pillage.openShare(window.__pillage.myBest()));
  await pa.waitForTimeout(300);
  const share = await pa.evaluate(() => ({stats: document.getElementById('share-stats').textContent, hidden: document.getElementById('share-stats').hidden,
    qr: !!document.querySelector('#share-qr svg'), link: document.getElementById('share-link').value}));
  say('SHARE', JSON.stringify(share));
  check(!share.hidden && /3 bales sold/.test(share.stats) && /1 bale smoked/.test(share.stats) && /4 merchants plundered/.test(share.stats) && /2 pirate ships sunk/.test(share.stats), 'the score card lists her tallies');
  check(share.qr && share.link === a.link, 'with a QR code and the same link');
  await pa.locator('#dlg-share').screenshot({path: OUT + '/1-anne-score-card-phone.png'});
  await pa.evaluate(() => document.getElementById('dlg-share').close());
  // her captain's log on a laptop
  const AL = await ctxFor(browser, {viewport: {width: 1280, height: 900}});
  await AL.addInitScript(([k, v]) => { if (!localStorage.getItem(k)) Object.entries(v).forEach(([a, b]) => localStorage.setItem(a, b)); },
    ['pillageTheReefer.legacy', await pa.evaluate(() => { window.__pillage.state && window.dispatchEvent(new Event('pagehide')); const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); o[k] = localStorage.getItem(k); } return o; })]);
  const pl = await AL.newPage(); watch(pl, 'anne-laptop', errs);
  await pl.goto(URL0 + '?check=' + Date.now(), {waitUntil: 'networkidle'});
  if (await pl.locator('#btn-continue').isVisible()) await pl.click('#btn-continue');
  await pl.waitForTimeout(800);
  await pl.evaluate(() => document.querySelectorAll('dialog[open]').forEach(d => d.close()));
  await pl.click('#btn-log');
  await pl.waitForTimeout(400);
  const lg = await pl.evaluate(() => {
    const b = document.querySelector('#log-body .board');
    return b ? {cards: b.querySelectorAll('.board-cat').length, h: [...b.querySelectorAll('h3,h4')].map(x => x.tagName + ' ' + x.textContent), text: b.textContent} : null;
  });
  say('LOG', JSON.stringify(lg && {cards: lg.cards, h: lg.h}));
  check(lg && lg.cards === 7 && /Smuggler Supreme: Anne Bonny \(you\), 3 bales sold/.test(lg.text) && /Nobody yet\. Dig up buried treasure\./.test(lg.text), 'her captain’s log shows all seven breakout boards');
  if (lg) await pl.locator('#log-body .board').screenshot({path: OUT + '/2-anne-log-laptop.png'});
  // Ben scans her code on his phone, in dark mode
  const Bc = await ctxFor(browser, {viewport: {width: 390, height: 844}, deviceScaleFactor: 2, colorScheme: 'dark'});
  const pb = await Bc.newPage(); watch(pb, 'ben', errs);
  await pb.goto(a.link, {waitUntil: 'networkidle'});
  await pb.waitForTimeout(500);
  const b1 = await pb.evaluate(() => {
    const tb = document.getElementById('title-board'), top = tb.querySelector('.board-list li');
    return {hidden: tb.hidden, search: location.search, h4: [...tb.querySelectorAll('h4')].map(h => h.textContent), top: top && top.textContent,
      sr: !!(top && top.querySelector('.crowns .sr-only')), text: tb.textContent};
  });
  say('BEN', JSON.stringify({h4: b1.h4, top: b1.top, search: b1.search}));
  check(!b1.hidden && b1.search === '' && /Anne Bonny of the Revenge is on your MJBizCon week board/.test(b1.text), 'Anne lands on Ben’s board and the address bar is tidied');
  check(b1.h4.length === 8 && /Overall/.test(b1.h4[0]) && b1.h4.some(h => /Top Smugglers/.test(h)) && b1.h4.some(h => /Most Smoked/.test(h)) && b1.h4.some(h => /Merchant Wreckers/.test(h)), 'an overall board and seven breakout boards, each with a heading');
  check(/Admiral of the Week/.test(b1.top) && /Smuggler Supreme/.test(b1.top) && b1.sr, 'Anne’s line wears her titles, with a spoken label');
  check(/Captain Cloud: Anne Bonny, 1 bale smoked/.test(b1.text) && /Scourge of the Merchant Fleet: Anne Bonny, 4 merchants plundered/.test(b1.text), 'she leads the boards she has tallies on');
  await pb.locator('#title-board').screenshot({path: OUT + '/3-ben-board-phone-dark.png'});
  // an old score code, made before the breakout boards
  const body = ['1', 'old111', 'Old Salt', 'the Barnacle', 300, 4, 900, 0, Math.floor((Date.now() - 600e3) / 60000).toString(36)].join('~');
  await pb.goto(URL0 + '?vs=' + b64(body + '~' + seal1(body)), {waitUntil: 'networkidle'});
  await pb.waitForTimeout(500);
  const b2 = await pb.evaluate(() => ({rivals: window.__pillage.legacy ? window.__pillage.legacy.rivals.length : -1, text: document.getElementById('title-board').textContent}));
  say('OLD CODE', b2.rivals, /Saltiest Dog: Old Salt/.test(b2.text));
  check(/Old Salt of the Barnacle is on your/.test(b2.text) && /Saltiest Dog: Old Salt, 4 days at sea/.test(b2.text) && !/Smuggler Supreme: Old Salt/.test(b2.text), 'an old score link still works, on the boards it can count');
  await pb.locator('#title-board').screenshot({path: OUT + '/4-ben-board-old-code.png'});
  // keyboard: the share button on Anne's title screen is reachable
  await pa.evaluate(() => window.__pillage.showTitle());
  await pa.waitForTimeout(300);
  let reached = false;
  for (let i = 0; i < 80 && !reached; i++) { await pa.keyboard.press('Tab'); reached = await pa.evaluate(() => document.activeElement && document.activeElement.classList.contains('board-share')); }
  check(reached, 'the Show or send my score button is reachable by keyboard');
  await pa.locator('#title-board').screenshot({path: OUT + '/5-anne-title-board-phone.png'});
  check(errs.length === 0, 'no page errors (' + errs.length + ')');
  await browser.close();
  say(bad.length ? 'FAILED: ' + bad.join(' | ') : 'ALL OK');
  fs.writeFileSync(OUT + '/log.txt', log.join('\n') + '\n');
})().catch(e => { say('CRASH', e.stack); fs.writeFileSync(OUT + '/log.txt', log.join('\n') + '\n'); });
