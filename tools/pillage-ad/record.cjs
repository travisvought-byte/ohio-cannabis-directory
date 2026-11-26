// Records real gameplay of Pillage the Reefer for the promo video.
// Frame-by-frame with a fake clock, so every frame is crisp and the timing is exact.
// Output: tools/pillage-ad/out/<scene>.mp4 (1080x1080, 30 fps) plus a few still PNGs for checking.
// Runs in CI (see .github/workflows/pillage-ad-record.yml). Analytics are blocked so nothing is counted.
const {chromium} = require('playwright');
const http = require('node:http'), fs = require('node:fs'), path = require('node:path'), {execFileSync} = require('node:child_process');

const ROOT = path.resolve(__dirname, '..', '..');
const OUT = path.join(__dirname, 'out');
const FRAMES = path.join(OUT, 'frames');
const FPS = 30, SIZE = 540, DPR = 2;
const log = (...a) => console.log('[rec]', ...a);

const STYLE = `<style id="ad-rec">
html,body{margin:0!important;overflow:hidden!important;background:#0b4250!important}
.stage{position:fixed!important;left:0!important;top:0!important;width:${SIZE}px!important;height:${SIZE}px!important;border:0!important;border-radius:0!important;box-shadow:none!important;margin:0!important;z-index:50!important}
header.site,.skip{display:none!important}
#sea:focus-visible{outline:none!important}
*{scrollbar-width:none!important}
::-webkit-scrollbar{display:none!important}
</style>`;
// A seeded Math.random so a run is repeatable, with a queue to force a roll on camera.
const RAND = `<script>(function(){var s=20261126;function r(){s|=0;s=s+0x6D2B79F5|0;var t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;}
window.__force=[];Math.random=function(){return window.__force.length?window.__force.shift():r();};})();</script>`;

const TYPES = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.ico': 'image/x-icon', '.txt': 'text/plain', '.woff2': 'font/woff2'};
function serve() {
  return new Promise(res => {
    const server = http.createServer((req, resp) => {
      let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      if (p.endsWith('/')) p += 'index.html';
      const file = path.resolve(ROOT, '.' + p);
      if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { resp.statusCode = 404; return resp.end(); }
      let body = fs.readFileSync(file);
      if (p === '/pillage/index.html') body = Buffer.from(body.toString('utf8').replace('<head>', '<head>' + RAND).replace('</head>', STYLE + '</head>'));
      resp.setHeader('Content-Type', TYPES[path.extname(file)] || 'application/octet-stream');
      resp.end(body);
    });
    server.listen(0, '127.0.0.1', () => res({base: 'http://127.0.0.1:' + server.address().port, close: () => server.close()}));
  });
}

// A voyage in progress: level 5, the Florida Straits, west of Nassau, every sea charted.
function voyage() {
  return {v: 1, map: 'straits', x: 640, y: 300, angle: 0, gold: 1650, cargo: {tangerine: 3, purple: 2}, basis: {},
    up: {hold: 2, hull: 2, cannons: 2, crew: 1, sails: 1, lavender: 0, secret: 0}, hull: 65, xp: 760, pts: 0,
    skill: {fight: 1, sail: 1, charm: 1}, dist: 12000, hints: {}, found: {}, quests: {},
    visited: {tortuga: 1, portroyal: 1, petitgoave: 1, nassau: 1, havana: 1}, known: {tortuga: 1, portroyal: 1, petitgoave: 1, nassau: 1, havana: 1, staugustine: 1},
    collected: {}, pillaged: 3, sunk: 1, tmap: null, dug: 0,
    flags: {r5: 1, r6: 1, gentleNote: 1, p_steer: 1, seen_straits: 1, seen_windward: 1}, docked: null, fog: '__FOG__', grit: 0, buff: null, seen: {},
    shot: 30, mk: {}, look: {captain: 'Captain Reefer', ship: 'the Lucky Leaf', sail: 'seafoam', flag: 'leaf'}, relics: {}, gentle: false, earned: 900, bricks: 0, atBase: false,
    rep: {britain: 12, spain: 0, france: 8, dutch: 5, brethren: 0}, marque: '', jobs: [], jobsTaken: {}, jobsDone: 2, bounties: 0, news: [], lastDay: 14,
    salute: {}, seed: 424242, food: 30, decoys: 0, fireship: 0, record: {}};
}

let page, scene = null, n = 0, tick = 0;
const scenes = [];
async function startScene(name) { scene = name; n = 0; fs.mkdirSync(path.join(FRAMES, name), {recursive: true}); scenes.push(name); log('scene', name); }
// Advance one frame of game time and photograph it. each(i) runs before the frame.
async function shoot(count, each) {
  for (let i = 0; i < count; i++) {
    if (each) await each(i);
    await page.clock.runFor([33, 33, 34][tick++ % 3]);
    await page.screenshot({path: path.join(FRAMES, scene, 'f' + String(n++).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 93});
  }
}
async function still(name) { try { await page.screenshot({path: path.join(OUT, name + '.png')}); } catch (e) { log('still failed', name, e.message); } }
async function idle(ms) { await page.clock.runFor(ms); }
const until = async (fn, maxFrames, extra) => { let k = 0; while (k < maxFrames) { if (await page.evaluate(fn).catch(() => false)) break; await shoot(1); k++; } return k < maxFrames; };
const open = id => `!!document.getElementById('${id}') && document.getElementById('${id}').open`;
// Ease a scrollable dialog so `sel` sits near the top, over `frames` frames.
async function glide(dlgSel, sel, frames, offset) {
  const plan = await page.evaluate(([d, s, off]) => {
    const dlg = document.querySelector(d), t = document.querySelector(s);
    if (!dlg || !t) return null;
    const from = dlg.scrollTop, to = Math.max(0, Math.min(dlg.scrollHeight - dlg.clientHeight, from + t.getBoundingClientRect().top - dlg.getBoundingClientRect().top - off));
    return [from, to];
  }, [dlgSel, sel, offset || 60]);
  if (!plan) { log('glide: missing', sel); return shoot(frames); }
  await shoot(frames, i => page.evaluate(([d, a, b, k]) => { const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2; document.querySelector(d).scrollTop = a + (b - a) * e; },
    [dlgSel, plan[0], plan[1], Math.min(1, (i + 1) / frames)]));
}

async function newPage(browser, base) {
  const ctx = await browser.newContext({viewport: {width: SIZE, height: SIZE}, deviceScaleFactor: DPR, reducedMotion: 'no-preference', timezoneId: 'America/New_York'});
  await ctx.route('**/*', r => {
    const u = r.request().url();
    if (!u.startsWith(base) || /analytics|goatcounter/i.test(u)) return r.abort();
    return r.continue();
  });
  const p = await ctx.newPage();
  p.on('pageerror', e => log('PAGE ERROR', e.message));
  p.on('console', m => { if (m.type() === 'error') log('console', m.text()); });
  await p.clock.install({time: new Date('2026-11-26T12:00:00-05:00')});
  return {ctx, p};
}

async function titleScene(browser, base) {
  const {ctx, p} = await newPage(browser, base);
  page = p;
  await page.goto(base + '/pillage/');
  await page.waitForSelector('#btn-new');
  await idle(400);
  await startScene('title');
  await shoot(75);
  await still('title');
  await page.click('#btn-new');
  await shoot(20);
  // Name the captain on camera, then pick the green leaf flag and sea-green sails.
  const name = 'Captain Reefer';
  await page.fill('#cap-name', '');
  for (let i = 0; i < name.length; i++) { await page.fill('#cap-name', name.slice(0, i + 1)); await shoot(2); }
  await shoot(8);
  for (const v of [['cap-flag', 'leaf'], ['cap-sail', 'seafoam']]) {
    const sel = `input[name="${v[0]}"][value="${v[1]}"]`;
    if (await page.$(sel)) { await page.check(sel, {force: true}).catch(e => log('check', e.message)); await shoot(12); }
  }
  await still('captain');
  await shoot(15);
  await ctx.close();
}

async function voyageScene(browser, base) {
  const {ctx, p} = await newPage(browser, base);
  page = p;
  await page.goto(base + '/pillage/');
  await page.waitForSelector('#btn-new');
  await page.evaluate(s => {
    const full = btoa(String.fromCharCode(255).repeat(140));
    s.fog = {straits: full, windward: full};
    localStorage.setItem('pillageTheReefer.v1', JSON.stringify(s));
  }, voyage());
  await page.reload();
  await page.waitForSelector('#btn-continue:not([hidden])');
  await idle(300);
  await page.click('#btn-continue');
  await idle(200);
  // Stage the Straits: a Spanish ship of the line sailing west on the lane above, a merchantman ahead,
  // a pirate brigantine on the horizon, and nobody close enough to pick a fight yet.
  await page.evaluate(() => {
    const P = window.__pillage, E = window.PILLAGE_ENGINE, D = window.PILLAGE_DATA, list = P.npcs().straits;
    document.getElementById('toast').classList.remove('show');
    const m = E.prepareMap('straits'), free = (x, y) => E.nearestFreePoint(m, x, y);
    const put = (nn, at, to, extra) => { const a = free(at[0], at[1]); Object.assign(nn, {x: a[0], y: a[1], route: [a, free(to[0], to[1])], leg: 0, path: null, pi: 0, gone: false, chase: false, cool: 999, angle: Math.atan2(to[1] - at[1], to[0] - at[0])}, extra || {}); };
    let navy = list.find(x => x.kind === 'navy'), merch = list.find(x => x.kind === 'merchant'), pir = list.filter(x => x.kind === 'pirate');
    if (navy) put(navy, [1180, 215], [380, 225], {nation: 'spain', tier: 5});
    if (merch) put(merch, [900, 385], [1200, 400], {nation: 'britain', looted: false});
    pir.forEach((x, i) => i === 0 ? put(x, [1320, 560], [1000, 560], {tier: 2}) : put(x, [300, 950], [200, 1000]));
    list.filter(x => x.kind === 'customs').forEach((x, i) => put(x, [200 + i * 60, 600], [220 + i * 60, 900]));
    window.__ad = {navy: navy, pirate: pir[0]};
  });
  await idle(1200);
  await page.evaluate(() => document.getElementById('toast').classList.remove('show'));
  await startScene('sail');
  await shoot(12);
  await page.evaluate(() => { const P = window.__pillage, p = window.PILLAGE_DATA.PORTS.nassau; P.planRoute({type: 'port', id: 'nassau', map: 'straits', x: p.dock[0], y: p.dock[1], label: 'Nassau'}); });
  const docked = await until(open('dlg-port'), 330);
  log('docked at Nassau:', docked);
  if (!docked) {
    await page.evaluate(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.__pillage.dock('nassau'); });
    await shoot(10);
  }
  await page.evaluate(() => { if (!document.getElementById('dlg-port').open) { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.__pillage.openPort('nassau', 'market'); } });
  await still('sail-end');

  // The market: buy five bales of Nassau Nectar.
  await startScene('market');
  await shoot(30);
  await glide('#dlg-port', '.goods', 24, 50);
  await shoot(20);
  const buy = page.locator('#dlg-port button[aria-label^="Buy 5 bales of Nassau Nectar"]');
  if (await buy.count()) { await buy.first().hover().catch(() => {}); await shoot(10); await buy.first().click(); }
  else log('no Nassau Nectar buy button');
  await shoot(45);
  await still('market');

  // The tavern: the real history of Nassau, then hire a fire ship.
  await startScene('tavern');
  await page.click('#tab-tavern');
  await shoot(30);
  await glide('#dlg-port', '#port-panel .history', 30, 80);
  await shoot(75);
  await still('tavern-history');
  const hire = page.locator('#dlg-port button[data-key="fireship"]');
  if (await hire.count()) {
    await glide('#dlg-port', '#port-panel .repair', 24, 40);
    await shoot(20);
    await hire.first().hover().catch(() => {});
    await shoot(10);
    await hire.first().click();
    await shoot(50);
  } else { log('no fire ship button'); await page.evaluate(() => { window.__pillage.state.fireship = 1; }); }
  await still('tavern-fireship');

  // Cast off with the fire ship astern.
  await startScene('castoff');
  const sail = page.locator('#dlg-port button', {hasText: 'Set sail'});
  if (await sail.count()) await sail.last().click(); else await page.evaluate(() => document.getElementById('dlg-port').close());
  await page.evaluate(() => { const P = window.__pillage, E = window.PILLAGE_ENGINE, m = E.prepareMap('straits'), f = E.nearestFreePoint(m, 1060, 255); P.planRoute({type: 'point', map: 'straits', x: f[0], y: f[1], label: 'west'}); });
  await shoot(90);
  await still('castoff');

  // Black sails: a pirate brigantine comes for us, and the fire ship goes in.
  await page.evaluate(() => {
    const P = window.__pillage, E = window.PILLAGE_ENGINE, m = E.prepareMap('straits'), s = P.state, list = P.npcs().straits;
    document.querySelectorAll('dialog[open]').forEach(d => d.close());
    const a = E.nearestFreePoint(m, 760, 660);
    s.x = a[0]; s.y = a[1]; s.angle = 0; s.docked = null;
    const pir = window.__ad.pirate || list.find(x => x.kind === 'pirate');
    const b = E.nearestFreePoint(m, 1010, 640);
    Object.assign(pir, {x: b[0], y: b[1], route: [b, E.nearestFreePoint(m, 1200, 700)], leg: 0, path: null, pi: 0, gone: false, chase: false, cool: 999, tier: 2, angle: Math.PI});
    list.forEach(x => { if (x !== pir && Math.hypot(x.x - a[0], x.y - a[1]) < 600) { x.cool = 999; const c = E.nearestFreePoint(m, 200, 1000); x.x = c[0]; x.y = c[1]; x.route = [c, c]; x.path = null; } });
  });
  await idle(1600);
  await startScene('fight');
  await page.evaluate(() => {
    const P = window.__pillage, E = window.PILLAGE_ENGINE, m = E.prepareMap('straits'), f = E.nearestFreePoint(m, 1250, 650);
    P.planRoute({type: 'point', map: 'straits', x: f[0], y: f[1], label: 'east'});
    window.__ad.pirate.cool = 0;
  });
  const met = await until(open('dlg-encounter'), 240);
  log('pirate met:', met);
  if (!met) { await page.evaluate(() => window.__pillage.encounter(window.__ad.pirate)); }
  await shoot(60);
  await still('fight');
  const fire = page.locator('#enc-body button', {hasText: 'fire ship'});
  if (await fire.count()) {
    await fire.first().scrollIntoViewIfNeeded().catch(() => {});
    await fire.first().hover().catch(() => {});
    await shoot(18);
    await page.evaluate(() => { window.__force = [0.97]; });
    await fire.first().click();
  } else {
    log('no fire ship option; firing cannonballs');
    await page.evaluate(() => { window.__force = [0.97]; });
    await page.locator('#enc-body button').first().click();
  }
  await shoot(100);
  await still('fight-won');
  const cont = page.locator('#dlg-encounter button', {hasText: 'Continue'});
  if (await cont.count()) { await cont.first().click(); await shoot(45); }

  // The sea chart.
  await startScene('chart');
  await page.evaluate(() => { document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.__pillage.openChart(); });
  await shoot(60);
  await still('chart');
  await ctx.close();
}

(async () => {
  fs.rmSync(OUT, {recursive: true, force: true});
  fs.mkdirSync(FRAMES, {recursive: true});
  const server = await serve();
  const browser = await chromium.launch({headless: true});
  try { await titleScene(browser, server.base); } catch (e) { log('title scene failed:', e.stack); }
  try { await voyageScene(browser, server.base); } catch (e) { log('voyage scene failed:', e.stack); await still('error'); }
  await browser.close();
  server.close();
  for (const s of scenes) {
    const dir = path.join(FRAMES, s);
    if (!fs.readdirSync(dir).length) continue;
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(dir, 'f%05d.jpg'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', path.join(OUT, s + '.mp4')]);
    log('encoded', s, fs.readdirSync(dir).length, 'frames');
  }
  fs.rmSync(FRAMES, {recursive: true, force: true});
})();
