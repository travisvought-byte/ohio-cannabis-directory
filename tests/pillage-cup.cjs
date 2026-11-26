'use strict';
/* The Silver Cup's replay check: a contest run played in a pretend browser (uneven frame times, dialogs that close a
   moment late, the page closed and opened again mid-run) replays to exactly the same voyage, and a faked run is caught. */
const assert = require('assert'), fs = require('fs'), path = require('path');
const {JSDOM} = require('jsdom');
const {verify} = require('../tools/pillage-contest/verify.cjs');
const ROOT = path.join(__dirname, '..', 'pillage'), read = f => fs.readFileSync(path.join(ROOT, f), 'utf8');
const FILES = ['coasts.js', 'data.js', 'engine.js', 'events.js', 'qr.js', 'game.js'];

// A little dice of the test's own, so the "player" is the same every run.
function dice(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = Math.imul(a ^ (a >>> 15), a | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

function browser(store, opts) {
  const dom = new JSDOM(read('index.html'), {runScripts: 'outside-only', url: 'https://the-reefer.com/pillage/'}), w = dom.window, errors = [];
  w.addEventListener('error', e => errors.push(e.error || e.message));
  const noop = () => {}, c2d = new Proxy({}, {get(t, k) { if (k in t) return t[k]; if (k === 'measureText') return () => ({width: 10}); if (/Gradient|Pattern/.test(k)) return () => ({addColorStop: noop}); if (k === 'getImageData' || k === 'createImageData') return (a, b, c, d) => ({data: new Uint8ClampedArray(4 * (c || a || 1) * (d || b || 1))}); return noop; }, set(t, k, v) { t[k] = v; return true; }});
  w.HTMLCanvasElement.prototype.getContext = () => c2d;
  w.Path2D = class { moveTo() {} lineTo() {} closePath() {} quadraticCurveTo() {} bezierCurveTo() {} arc() {} rect() {} ellipse() {} };
  w.Element.prototype.getBoundingClientRect = () => ({left: 0, top: 0, width: 390, height: 520, right: 390, bottom: 520, x: 0, y: 0});
  w.Element.prototype.scrollIntoView = noop;
  w.fetch = () => Promise.resolve({ok: false});
  Object.defineProperty(w.document, 'hidden', {get: () => false});
  let raf = null;
  w.requestAnimationFrame = cb => { raf = cb; return 1; };
  // Like a real browser: the close event arrives a moment after the dialog shuts.
  w.HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  w.HTMLDialogElement.prototype.close = function () { if (!this.hasAttribute('open')) return; this.removeAttribute('open'); setTimeout(() => this.dispatchEvent(new w.Event('close')), 0); };
  for (const k in (store || {})) w.localStorage.setItem(k, store[k]);
  for (const f of FILES) { w.eval(read(f)); if (f === 'data.js' && opts && opts.api) w.PILLAGE_DATA.CONTEST.api = opts.api; }
  let ts = 1000;
  const B = {w, dom, errors, P: w.__pillage, $: id => w.document.getElementById(id),
    frame(ms) { ts += ms; const cb = raf; raf = null; if (cb) cb(ts); },
    store() { const o = {}; for (let i = 0; i < w.localStorage.length; i++) { const k = w.localStorage.key(i); o[k] = w.localStorage.getItem(k); } return o; }};
  return B;
}
const later = () => new Promise(r => setTimeout(r, 2));
const open = B => [...B.w.document.querySelectorAll('dialog[open]')].pop() || null;
const usable = b => !b.disabled && !b.closest('[hidden]');

// One frame of a made-up player: deal with whatever window is open, otherwise steer, tap the sea or press keys.
async function playFrame(B, r, opts) {
  const d = open(B), P = B.P, $ = B.$;
  if (d) {
    if (r() < 0.55) { /* players read */ }
    else if (d.id === 'dlg-captain') {
      const inp = $('cap-name');
      if (inp.value.length < 6 && r() < 0.8) { inp.value += 'Anne'.charAt(inp.value.length % 4); inp.dispatchEvent(new B.w.Event('input', {bubbles: true})); }
      else $('cap-ok').click();
    } else if (d.id === 'dlg-note') $('note-ok').click();
    else if (d.id === 'dlg-encounter') {
      const bs = [...$('enc-body').querySelectorAll('button')].filter(usable);
      if (bs.length) bs[Math.floor(r() * bs.length)].click();
    } else if (d.id === 'dlg-port') {
      const x = r();
      const bs = [...d.querySelectorAll('button')].filter(b => usable(b) && b.id !== 'set-sail');
      if (x < 0.1 || !bs.length) $('set-sail').click();
      else if (x < 0.13) { const ev = new B.w.Event('cancel', {cancelable: true}); d.dispatchEvent(ev); if (!ev.defaultPrevented) d.close(); }
      else bs[Math.floor(r() * bs.length)].click();
    } else {
      const bs = [...d.querySelectorAll('button')].filter(usable);
      if (r() < 0.3 || !bs.length) { const ev = new B.w.Event('cancel', {cancelable: true}); d.dispatchEvent(ev); if (!ev.defaultPrevented) d.close(); }
      else bs[Math.floor(r() * bs.length)].click();
    }
  } else if (P.state && !P.state.docked) {
    const cv = $('sea'), x = r();
    if (x < 0.02) {
      cv.focus();
      const ev = new B.w.MouseEvent('pointerdown', {bubbles: true, clientX: Math.floor(r() * 390), clientY: Math.floor(r() * 520)});
      cv.dispatchEvent(ev);
    } else if (x < 0.05) {
      cv.focus();
      const k = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'a'][Math.floor(r() * 6)];
      cv.dispatchEvent(new B.w.KeyboardEvent(r() < 0.6 ? 'keydown' : 'keyup', {key: k, bubbles: true, cancelable: true}));
    } else if (x < 0.055) {
      cv.focus();
      cv.dispatchEvent(new B.w.KeyboardEvent('keydown', {key: 'Enter', bubbles: true, cancelable: true}));
    } else if (x < 0.057 && opts.chart) {
      cv.focus();
      cv.dispatchEvent(new B.w.KeyboardEvent('keydown', {key: 'm', bubbles: true, cancelable: true}));
    } else if (x < 0.06 && !$('action').hidden) $('action').click();
  }
  B.frame([16, 17, 16, 33, 8, 50, 16, 120][Math.floor(r() * 8)]);
  if (r() < 0.3) await later();
}

(async () => {
  const r = dice(+(process.env.CUP_DICE || 7));
  // Part one: a new contest run.
  let A = browser({});
  A.P.cup.start({id: 'test-run', seed: 424242, practice: true});
  assert(A.P.state.cup === 'practice' && A.P.state.seed === 424242, 'the run starts from the server’s seed');
  for (let i = 0; i < 2500; i++) await playFrame(A, r, {chart: true});
  await later();
  const pid = A.P.state;
  assert(A.P.cup.rec.ev.length > 50, 'moves were recorded (' + A.P.cup.rec.ev.length + ')');
  A.P.cup.save();
  // The page closes and opens again: the run carries on from its contest save.
  const st1 = A.store();
  assert(st1['pillageTheReefer.cup'] && !st1['pillageTheReefer.v1'], 'a contest run saves apart from your own voyage');
  A.dom.window.close();
  let B = browser(st1);
  const recd = B.P.cup.load();
  assert(recd && recd.segs.length === 1, 'the contest save holds part one');
  B.P.cup.resume(recd);
  for (let i = 0; i < 2500; i++) await playFrame(B, r, {chart: true});
  await later();
  // A third part, closed without a last save: whatever came after the last save is lost on the phone and in the replay alike.
  const st2 = B.store();
  B.dom.window.close();
  let C = browser(st2);
  C.P.cup.resume(C.P.cup.load());
  for (let i = 0; i < 1500; i++) await playFrame(C, r, {chart: true});
  await later();
  const sub = C.P.cup.sub(), xp = C.P.state.xp;
  assert.equal(sub.segs.length, 3, 'three parts');
  if (process.env.CUP_DUMP) fs.writeFileSync(process.env.CUP_DUMP, JSON.stringify(sub));
  const res = verify(JSON.parse(JSON.stringify(sub)));
  assert(res.ok, 'the honest run replays to the same voyage: ' + res.reason);
  assert.equal(res.xp, Math.round(xp), 'and the replay’s score is the phone’s score');
  console.log('cup: honest run of', res.steps, 'steps,', sub.segs.reduce((n, s) => n + s.ev.length, 0), 'moves, xp', res.xp, 'level', res.level, 'day', res.day);

  // A claimed score is never used: only the replay counts.
  const fake = JSON.parse(JSON.stringify(sub)); fake.claim.xp = 999999;
  assert.equal(verify(fake).xp, res.xp, 'a faked claim changes nothing');
  // A different seed doesn't replay to the same voyage.
  const seed2 = JSON.parse(JSON.stringify(sub)); seed2.run.seed = 424243;
  assert(!verify(seed2).ok, 'a run with a swapped seed is refused');
  // Gold slipped into the save between parts doesn't survive the replay.
  const forged = JSON.parse(JSON.stringify(sub)); forged.segs[2].h = 'x' + forged.segs[2].h;
  assert(!verify(forged).ok, 'a run whose end doesn’t match is refused');
  // A move the game would never have taken: docking while a window is open.
  const sneaky = JSON.parse(JSON.stringify(sub)); const ev0 = sneaky.segs[0].ev;
  const dlgAt = ev0.findIndex(x => x[1] === 'c');
  ev0.splice(dlgAt, 0, [ev0[dlgAt][0], 'act']);
  assert(!verify(sneaky).ok, 'a key press while a window is open is refused');
  // A tap on a button that isn't on screen.
  const ghost = JSON.parse(JSON.stringify(sub)); ghost.segs[1].ev.splice(3, 0, [ghost.segs[1].ev[3][0], 'c', '#opt-new-yes']);
  const gr = verify(ghost);
  assert(!gr.ok && /not there to tap|could not be made|ends somewhere else/.test(gr.reason), 'a tap on a hidden button is refused: ' + gr.reason);
  // A teleport: sailing to a port in another sea as if it were next door.
  const tp = JSON.parse(JSON.stringify(sub)); const sv = tp.segs[2];
  sv.ev.push([sv.n, 'go', {type: 'port', id: 'havana', map: 'windward', x: 100, y: 100, label: 'Havana'}]);
  assert(!verify(tp).ok, 'a made-up destination is refused');
  // Time can't be made up either: a part that says it has more moves than steps.
  const late = JSON.parse(JSON.stringify(sub)); late.segs[0].ev.push([late.segs[0].n + 5, 'kx']);
  assert(!verify(late).ok, 'moves after the part ended are refused');
  assert(!verify({run: {id: 'x', seed: 1}, segs: []}).ok && !verify(null).ok, 'nonsense is refused');

  // A run entered from the title screen after a voyage of one's own on the same page, with the Cup's window opened
  // mid-run, settings changed, a save at an odd moment, the page reloaded, and the run ended from Settings.
  {
    const r2 = dice(+(process.env.CUP_DICE || 7) + 100), sent = [];
    let runs = 0;
    const server = (w) => (url, o) => {
      const u = String(url), res = d => Promise.resolve({ok: true, json: () => Promise.resolve(d)});
      if (u === 'https://cup.test/api/start') {
        const b = JSON.parse(o.body); runs++;
        assert(b.adult === true && b.rules === true && b.ver === 'cup1' && b.email === 'anne@example.com', 'the entry carries what the server needs');
        return res({ok: true, run: {id: 'run' + runs, key: 'key' + runs, seed: 9000 + runs, practice: true, ver: b.ver, handle: b.handle, crew: b.crew}});
      }
      if (u === 'https://cup.test/api/submit') { sent.push({key: o.headers['x-run-key'], type: o.headers['content-type'], body: o.body}); return res({ok: true, status: 'pending'}); }
      if (u.startsWith('https://cup.test/api/run?')) return res({ok: true, last: {status: 'pending'}, best: null});
      return Promise.resolve({ok: false, json: () => Promise.resolve({})});
    };
    const D = browser({}, {api: 'https://cup.test'});
    D.w.fetch = server(D.w);
    D.$('btn-new').click();
    for (let i = 0; i < 900; i++) await playFrame(D, r2, {chart: true});
    await later();
    D.P.showTitle();
    assert(!D.$('title-cup').hidden && !D.$('btn-cup-go').hidden, 'the title screen offers the Cup');
    D.$('btn-cup-go').click();
    assert(D.$('dlg-cup').hasAttribute('open'), 'the entry form opens');
    D.$('cupf-name').value = 'Anne Bonny'; D.$('cupf-email').value = 'anne@example.com'; D.$('cupf-crew').value = 'Calico Crew';
    D.$('cupf-go').click();
    await later(); await later();
    assert(/21 or older/.test(D.$('cupf-err').textContent) && runs === 0, 'no entry without the two boxes ticked');
    D.$('cupf-adult').checked = true; D.$('cupf-rules').checked = true;
    D.$('cupf-go').click();
    for (let i = 0; i < 5; i++) await later();
    assert(D.P.cup.run && D.P.cup.run.run.id === 'run1' && D.P.state.seed === 9001, 'the run starts once the form has closed');
    assert(!D.$('btn-cup').hidden && D.$('cap-mode').hidden, 'a Cup run shows its button and offers no gentle seas');
    for (let i = 0; i < 1200; i++) await playFrame(D, r2, {chart: true});
    while (open(D)) { await playFrame(D, r2, {chart: true}); }
    D.$('btn-cup').click();
    assert(D.$('dlg-cupstat').hasAttribute('open'), 'the Cup button shows the run');
    for (let i = 0; i < 30; i++) D.frame(16);
    D.$('cupstat-send').click();
    for (let i = 0; i < 5; i++) await later();
    assert.equal(sent.length, 1, 'a run can be sent by hand');
    assert.equal(sent[0].key, 'key1');
    D.$('cupstat-back').click();
    await later();
    D.P.cup.save();   // as when the page is put away: a save at a moment the replay never saves at
    for (let i = 0; i < 30; i++) await playFrame(D, r2, {chart: true});
    while (open(D)) { await playFrame(D, r2, {chart: true}); }
    D.$('btn-settings').click();
    assert(!D.$('opt-ghosts-row').hidden && /End this practice run/.test(D.$('opt-new').textContent), 'settings in a Cup run');
    D.$('opt-ghosts').click();
    D.$('dlg-settings').querySelector('[data-close]').click();
    await later();
    for (let i = 0; i < 900; i++) await playFrame(D, r2, {chart: true});
    await later();
    const st3 = D.store();
    D.dom.window.close();
    const F = browser(st3, {api: 'https://cup.test'});
    F.w.fetch = server(F.w);
    assert(!F.$('btn-cup-continue').hidden, 'the title screen offers to carry on the run');
    F.$('btn-cup-continue').click();
    for (let i = 0; i < 700; i++) await playFrame(F, r2, {chart: true});
    while (open(F)) { await playFrame(F, r2, {chart: true}); }
    const before = sent.length, xp2 = Math.round(F.P.state.xp);
    F.$('btn-settings').click(); F.$('opt-new').click(); F.$('opt-new-yes').click();
    for (let i = 0; i < 6; i++) { await later(); F.frame(16); }
    assert.equal(sent.length, before + 1, 'ending the run sends it one last time');
    const last = JSON.parse(sent[sent.length - 1].body);
    assert.equal(last.over, 'ended');
    assert(F.$('dlg-note').hasAttribute('open'), 'and says so');
    const res2 = verify(last);
    assert(res2.ok, 'the run replays though it began after a voyage of the player’s own: ' + res2.reason);
    assert.equal(res2.xp, xp2, 'to the same score');
    assert.equal(res2.parts, 2);
    F.$('note-ok').click();
    await later(); await later();
    assert(!F.$('title-screen').hidden && F.$('btn-cup-continue').hidden, 'back at the title screen, with no run to carry on');
    console.log('cup: entered after a voyage of one’s own, ended from Settings at', res2.steps, 'steps, xp', res2.xp);
  }
  console.log('pillage cup ok');
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
