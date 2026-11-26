// Check the live game's real-geography charts: the new files load, the ship starts at the real Tortuga,
// autopilot sails from Tortuga across into the Florida Straits and docks at Havana, and a passage reaches Nassau.
const {chromium} = require('playwright');
const fs = require('fs');
const OUT = 'tools/pillage-ad/live-check';
fs.mkdirSync(OUT, {recursive: true});
const log = [], bad = [];
const say = (...a) => { const s = a.join(' '); log.push(s); console.log(s); };
const check = (ok, what) => { say(ok ? 'OK  ' : 'BAD ', what); if (!ok) bad.push(what); };
(async () => {
  const browser = await chromium.launch({headless: true});
  const ctx = await browser.newContext({viewport: {width: 540, height: 760}, deviceScaleFactor: 2});
  await ctx.route('**/*', r => /goatcounter|analytics/i.test(r.request().url()) ? r.abort() : r.continue());
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => { errs.push(e.message); say('PAGE ERROR', e.message); });
  page.on('response', r => { if (/pillage\/[a-z]+\.js/.test(r.url())) say('loads', r.status(), r.url()); });
  await page.goto('https://the-reefer.com/pillage/?check=' + Date.now(), {waitUntil: 'networkidle'});
  await page.waitForSelector('#btn-new');
  await page.click('#btn-new');
  await page.waitForSelector('#cap-ok');
  await page.click('#cap-ok');
  await page.waitForTimeout(800);
  await page.evaluate(() => document.querySelectorAll('dialog[open]').forEach(d => d.close()));
  await page.waitForTimeout(600);
  const info = await page.evaluate(() => {
    const D = window.PILLAGE_DATA, E = window.PILLAGE_ENGINE, S = window.__pillage.state, t = D.PORTS.tortuga;
    return {k: window.PILLAGE_COASTS && window.PILLAGE_COASTS.k, scale: D.SCALE, emerald: D.STASHES.emerald.name, hideout: D.HIDEOUT.name,
      map: S.map, at: E.toLonLat(D.MAPS[S.map], S.x, S.y), tortugaTown: E.toLonLat(D.MAPS.windward, t.town[0], t.town[1]),
      credit: /Natural Earth/.test(document.body.textContent), seas: Object.keys(D.MAPS).map(m => m + ' ' + D.MAPS[m].lands.length + ' lands')};
  });
  say('INFO', JSON.stringify(info));
  check(info.k === 140 && info.scale === 140, 'coasts.js is live with the shared 140-per-degree scale');
  check(info.emerald === 'Serrana Bank' && info.hideout === 'Île-à-Vache', 'dig site and hideout carry their real names');
  check(info.credit, 'the page credits Natural Earth');
  check(info.map === 'windward' && Math.abs(info.at[0] + 72.8) < 0.5 && Math.abs(info.at[1] - 20.05) < 0.5, 'a new voyage starts off the real Tortuga');
  await page.screenshot({path: OUT + '/start-tortuga.png'});
  await page.evaluate(() => window.__pillage.openChart());
  await page.waitForTimeout(400);
  await page.locator('#dlg-chart').screenshot({path: OUT + '/chart.png'});
  await page.evaluate(() => document.querySelectorAll('dialog[open]').forEach(d => d.close()));
  await page.waitForTimeout(400);
  // Autopilot from Tortuga to Havana: out through the Windward Passage side into the Florida Straits.
  const trip = await page.evaluate(() => {
    const P = window.__pillage, D = window.PILLAGE_DATA, E = window.PILLAGE_ENGINE, S = () => P.state, r = Math.random;
    Math.random = () => 0.99;
    const shut = () => document.querySelectorAll('dialog[open]').forEach(d => { if (d.id !== 'dlg-port') d.close(); });
    P.dock('tortuga'); document.querySelectorAll('dialog[open]').forEach(d => d.close());
    const h = D.PORTS.havana.dock, planned = P.planRoute({type: 'port', id: 'havana', map: 'straits', x: h[0], y: h[1], label: 'Havana'});
    let cross = null, steps = 0;
    for (; steps < 20000 && !S().docked; steps++) {
      const m0 = S().map, x0 = S().x, y0 = S().y;
      P.step(0.05); shut();
      if (S().map !== m0 && !cross) cross = {from: m0, to: S().map, before: E.toLonLat(D.MAPS[m0], x0, y0), after: E.toLonLat(D.MAPS[S().map], S().x, S().y)};
    }
    Math.random = r;
    return {planned, cross, steps, docked: S().docked, map: S().map};
  });
  say('TRIP', JSON.stringify(trip));
  check(trip.planned && trip.cross && trip.cross.from === 'windward' && trip.cross.to === 'straits', 'autopilot crosses from the Windward Passage into the Florida Straits');
  check(trip.cross && Math.abs(trip.cross.before[0] - trip.cross.after[0]) < 0.75 && Math.abs(trip.cross.before[1] - trip.cross.after[1]) < 0.75, 'the crossing keeps the real position');
  check(trip.docked === 'havana', 'and docks at Havana');
  await page.waitForTimeout(500);
  await page.screenshot({path: OUT + '/havana-port.png'});
  await page.evaluate(() => document.querySelectorAll('dialog[open]').forEach(d => d.close()));
  await page.waitForTimeout(1200);
  await page.screenshot({path: OUT + '/off-havana.png'});
  // A quick passage from Havana to Nassau.
  const pass = await page.evaluate(() => {
    const P = window.__pillage, r = Math.random;
    Math.random = () => 0.99;
    P.dock('havana'); document.querySelectorAll('dialog[open]').forEach(d => d.close());
    const v = P.voyage('havana', 'nassau'), ok = P.passage('nassau');
    for (let i = 0; i < 40 && document.getElementById('dlg-encounter').open; i++) {
      const b = document.querySelector('#enc-body .choice:not([disabled])') || document.querySelector('#enc-body .primary'); if (b) b.click(); else break; }
    Math.random = r;
    return {v, ok, docked: P.state.docked, map: P.state.map};
  });
  say('PASSAGE', JSON.stringify(pass));
  check(pass.ok && pass.docked === 'nassau' && pass.map === 'straits', 'a passage from Havana docks at Nassau');
  await page.waitForTimeout(500);
  await page.screenshot({path: OUT + '/nassau-port.png'});
  check(!errs.length, 'no page errors');
  say(bad.length ? 'RESULT BROKEN: ' + bad.join('; ') : 'RESULT OK');
  fs.writeFileSync(OUT + '/log.txt', log.join('\n') + '\n');
  await browser.close();
})().catch(e => { say('FAILED', e.stack); fs.writeFileSync(OUT + '/log.txt', log.join('\n') + '\n'); process.exit(0); });
