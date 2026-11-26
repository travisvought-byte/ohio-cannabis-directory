// Check the live Silver Cup pages: the contest page, the rules, the home banner, the privacy section, the game's
// Cup box and the address file, at phone and laptop width, in light and dark, with no page errors.
const {chromium} = require('playwright');
const fs = require('fs');
const OUT = 'tools/pillage-ad/live-cup';
fs.mkdirSync(OUT, {recursive: true});
const log = [], bad = [];
const say = (...a) => { const s = a.join(' '); log.push(s); console.log(s); };
const check = (ok, what) => { say(ok ? 'OK  ' : 'BAD ', what); if (!ok) bad.push(what); };
const SITE = 'https://the-reefer.com';
const bust = () => '?check=' + Date.now();
async function ctxFor(browser, opts) {
  const ctx = await browser.newContext(opts);
  await ctx.route('**/*', r => /goatcounter|gc\.zgo\.at/i.test(r.request().url()) ? r.abort() : r.continue());
  return ctx;
}
async function open(ctx, path, name, errs) {
  const p = await ctx.newPage();
  p.on('pageerror', e => { errs.push(name + ': ' + e.message); say('PAGE ERROR', name, e.message); });
  p.on('console', m => { if (m.type() === 'error' && !/goatcounter|gc\.zgo|ERR_FAILED/i.test(m.text())) say('console error', name, m.text()); });
  p.on('response', r => { if (r.status() >= 400 && !/goatcounter|gc\.zgo/.test(r.url())) { say('HTTP', r.status(), name, r.url()); errs.push(name + ': HTTP ' + r.status() + ' ' + r.url()); } });
  await p.goto(SITE + path + (path.includes('?') ? '&c=' + Date.now() : bust()), {waitUntil: 'networkidle'});
  return p;
}
const fits = p => p.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
(async () => {
  let live = false;
  for (let i = 0; i < 40 && !live; i++) {
    try {
      const c = await (await fetch(SITE + '/pillage/contest.html' + bust())).text();
      const g = await (await fetch(SITE + '/pillage/' + bust())).text();
      const h = await (await fetch(SITE + '/' + bust())).text();
      live = /Silver Cup/.test(c) && /cup-api\.js/.test(g) && /cup-banner/.test(h);
    } catch (e) { say('fetch failed', e.message); }
    if (!live) await new Promise(r => setTimeout(r, 15000));
  }
  check(live, 'the contest page, the game with cup-api.js and the home banner are live');
  const api = await (await fetch(SITE + '/pillage/cup-api.js' + bust())).text();
  check(/PILLAGE_CUP_API\s*=\s*''/.test(api), 'cup-api.js is served and empty until the server runs: ' + api.trim().split('\n').pop());
  const rules = await (await fetch(SITE + '/pillage/contest-rules.html' + bust())).text();
  const sitemap = await (await fetch(SITE + '/sitemap.xml' + bust())).text();
  check(/pillage\/contest\.html/.test(sitemap) && /pillage\/contest-rules\.html/.test(sitemap), 'the sitemap lists the contest page and the rules');
  for (const words of ['No purchase necessary', '21', 'void where prohibited', 'earlier', 'within 30 days', 'release Facebook'])
    check(rules.toLowerCase().includes(words.toLowerCase()), 'rules say: ' + words);
  try {
    const ow = await (await fetch('https://ohioweed.org/directory.html' + bust())).text();
    say('ohioweed.org/directory.html has the Cup line:', /national-event-cup/.test(ow));
  } catch (e) { say('ohioweed.org fetch failed', e.message); }

  const browser = await chromium.launch({headless: true});
  const errs = [];
  for (const [label, opts] of [['phone', {viewport: {width: 390, height: 844}, deviceScaleFactor: 2}],
                               ['laptop-dark', {viewport: {width: 1280, height: 900}, colorScheme: 'dark'}]]) {
    const ctx = await ctxFor(browser, opts);
    // contest page
    let p = await open(ctx, '/pillage/contest.html', 'contest ' + label, errs);
    const cd = await p.textContent('#cd');
    check(/^Opens in \d/.test(cd), label + ' countdown runs: ' + cd);
    check((await p.textContent('#board-status')).includes('once the Cup’s server is running'), label + ' board says the server is not running yet');
    check(await p.locator('a[href="/partners.html#ask"]').count() >= 2, label + ' the business link is on the page');
    check(await fits(p), label + ' contest page fits the screen');
    await p.screenshot({path: `${OUT}/contest-${label}.png`, fullPage: true});
    const ask = p.locator('a[href="/partners.html#ask"]').first();
    await ask.click(); await p.waitForLoadState('networkidle');
    check(/\/partners(\.html)?#ask$/.test(p.url()) && await p.locator('#ask').count() === 1, label + ' business link lands on Partners, Ask: ' + p.url());
    await p.close();
    // rules
    p = await open(ctx, '/pillage/contest-rules.html', 'rules ' + label, errs);
    check(await fits(p), label + ' rules fit the screen');
    await p.screenshot({path: `${OUT}/rules-${label}.png`, fullPage: true});
    await p.close();
    // home banner
    p = await open(ctx, '/', 'home ' + label, errs);
    check(await p.isVisible('#cup-banner'), label + ' home banner shows');
    check(await fits(p), label + ' home fits the screen');
    await p.screenshot({path: `${OUT}/home-${label}.png`});
    await p.click('#cup-banner a'); await p.waitForLoadState('networkidle');
    check(/\/pillage\/contest\.html/.test(p.url()), label + ' home banner opens the contest page: ' + p.url());
    await p.close();
    // privacy
    p = await open(ctx, '/privacy.html', 'privacy ' + label, errs);
    check((await p.textContent('main')).includes('The game and its Silver Cup'), label + ' privacy has the Silver Cup section');
    await p.close();
    // game title screen
    p = await open(ctx, '/pillage/', 'game ' + label, errs);
    await p.waitForTimeout(1500);
    check(await p.isVisible('#title-cup'), label + ' the game title screen shows the Cup box');
    say(label, 'Cup box:', (await p.textContent('#title-cup')).replace(/\s+/g, ' ').trim());
    check(await p.evaluate(() => window.PILLAGE_CUP_API === ''), label + ' the game read cup-api.js');
    await p.screenshot({path: `${OUT}/game-title-${label}.png`});
    await p.close();
    await ctx.close();
  }
  await browser.close();
  check(errs.length === 0, 'no page errors or failed loads: ' + JSON.stringify(errs));
  say(bad.length ? 'FAILED: ' + bad.join(' | ') : 'ALL OK');
  fs.writeFileSync(`${OUT}/log.txt`, log.join('\n') + '\n');
})().catch(e => { console.error(e); fs.writeFileSync(`${OUT}/log.txt`, log.join('\n') + '\nCRASH ' + e.stack + '\n'); process.exit(0); });
