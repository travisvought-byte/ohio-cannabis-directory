// The Silver Cup's pages: the contest page (countdown and boards) and the official rules.
const fs = require('fs'), path = require('path'), assert = require('assert');
const {JSDOM} = require('jsdom');
const DIR = path.join(__dirname, '..', 'pillage');
const START = Date.UTC(2026, 11, 1, 8), END = Date.UTC(2026, 11, 5, 8);

function page(file, {api, now, board} = {}) {
  let html = fs.readFileSync(path.join(DIR, file), 'utf8');
  html = html.replace('<script src="/assets/analytics.js" defer></script>', '')
    .replace(/<script src="cup-api\.js\?v=\d+"><\/script>/, '<script>window.PILLAGE_CUP_API = ' + JSON.stringify(api || '') + ';</script>');
  const calls = [];
  const dom = new JSDOM(html, {url: 'https://the-reefer.com/pillage/' + file, runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(w) {
      if (now) w.Date.now = () => now;
      w.fetch = (u) => { calls.push(String(u)); return Promise.resolve({json: () => Promise.resolve(board)}); };
    }});
  return {dom, w: dom.window, $: id => dom.window.document.getElementById(id), calls};
}
const tick = () => new Promise(r => setTimeout(r, 20));

(async () => {
  // Without the server running: the page explains, and nothing is fetched.
  let P = page('contest.html', {now: START - 2 * 864e5 - 3 * 36e5});
  assert.match(P.$('cd').textContent, /^Opens in 2 days, 3 hours, 0 minutes$/, P.$('cd').textContent);
  assert.match(P.$('board-status').textContent, /once the Cup’s server is running/);
  assert.equal(P.calls.length, 0);
  assert.equal(P.w.document.querySelectorAll('a[href="/partners.html#ask"]').length >= 2, true, 'the add-your-business link');
  assert(P.w.document.querySelector('.prizes'), 'the prize list was written in');
  P.w.close();

  // Before the start, with the server: the practice board, with no prize badges.
  const board = {ok: true, practice: true, checking: 2,
    captains: [{name: '<img src=x onerror=alert(1)>', crew: 'Calico Crew', xp: 1234, level: 5}, {name: 'Ned Low', crew: '', xp: 900, level: 4}],
    crews: [{name: 'Calico Crew', xp: 1234, members: 1, top: ['<img src=x onerror=alert(1)>']}],
    tallies: {sold: [{name: 'Ned Low', n: 40}], days: [{name: 'Ned Low', n: 12}]}};
  P = page('contest.html', {api: 'https://cup.example/', now: START - 600e3, board});
  await tick();
  assert.deepEqual(P.calls, ['https://cup.example/api/board?kind=practice']);
  assert.equal(P.$('cap-h').textContent, 'Practice captains');
  const first = P.$('board-captains').children[0];
  assert.equal(first.querySelector('.who').textContent, '<img src=x onerror=alert(1)>', 'names are shown as text');
  assert.equal(P.w.document.querySelectorAll('#board-captains img').length, 0, 'and never as markup');
  assert.equal(P.w.document.querySelectorAll('#board-captains .win').length, 0, 'practice wins no silver');
  assert.match(first.textContent, /1,234 renown, level 5/);
  assert.match(P.$('board-crews').textContent, /Calico Crew 1,234 renown · 1 captain/);
  assert.match(P.$('board-tallies').textContent, /Top Smugglers.*Ned Low: 40 bales sold/);
  assert.match(P.$('board-status').textContent, /2 runs waiting to be checked/);
  P.w.close();

  // During the Cup: the prize board, and the top three carry their prizes.
  board.practice = false;
  board.captains.push({name: 'Anne Bonny', crew: 'Calico Crew', xp: 800, level: 4}, {name: 'Mary Read', crew: '', xp: 700, level: 3});
  P = page('contest.html', {api: 'https://cup.example', now: START + 36e5, board});
  await tick();
  assert.deepEqual(P.calls, ['https://cup.example/api/board']);
  assert.match(P.$('cd').textContent, /^On now\. Closes in 3 days, 23 hours/);
  assert.deepEqual([...P.w.document.querySelectorAll('#board-captains .win')].map(e => e.textContent), ['10 silver halves', '5 silver halves', '1 silver half']);
  P.w.close();
  P = page('contest.html', {now: END + 1000});
  assert.match(P.$('cd').textContent, /over/);
  P.w.close();

  // The rules: everything the contest promises is written down, with the silver's value.
  P = page('contest-rules.html');
  const t = P.w.document.body.textContent.replace(/\s+/g, ' ');
  for (const need of ['No purchase necessary', 'contest of skill', '21 or older', 'United States', 'Void where prohibited', 'Ties go to the earlier verified run',
    'about half are 90% silver and half are 40% silver', 'sponsor’s choice', 'within 7 days', 'Prizes ship within 30 days', 'One prize per person', 'Help is allowed',
    'may disqualify', '12:00:00 AM Pacific on Tuesday, December 1, 2026', '11:59:59 PM Pacific on Friday, December 4, 2026', 'veteranhomeguardians@gmail.com',
    'isn’t run, sponsored or endorsed by MJBizCon', 'approximate', 'move with the price of silver', 'Add your business to your state’s directory'])
    assert(t.includes(need), 'the rules say: ' + need);
  const rows = [...P.w.document.querySelectorAll('.vals tbody tr')].map(r => r.textContent.replace(/\s+/g, ' ').trim());
  assert.equal(rows.length, 4, 'a value for each place, and the total');
  assert.match(t, /spot price of \$[\d.]+ a troy ounce \(\w+, bid price at .+2026\)/, 'the spot price says where and when it was read');
  // The contest page and the rules agree on the price.
  const spot = s => (s.match(/spot price of (\$[\d.]+) a troy ounce/) || [])[1];
  const c = fs.readFileSync(path.join(DIR, 'contest.html'), 'utf8');
  assert.equal(spot(c), spot(t), 'one spot price on both pages');
  P.w.close();
  console.log('pillage contest pages ok');
})().catch(e => { console.error(e); process.exit(1); });
