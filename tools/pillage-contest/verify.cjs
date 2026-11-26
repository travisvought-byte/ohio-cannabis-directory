'use strict';
/* Silver Cup replay checker.
   Plays a contest run again from its seed and its recorded moves, in a pretend browser, part by part (one part for each
   time the page was opened), and reports the score the replay itself reaches. The phone's own report of its score is
   never used. A move that couldn't have been made (a hidden or disabled button, a key while a window was open, a place
   the game never offered) fails the run. So does a replay that doesn't land on the same voyage the phone saved.
   Usage: node verify.cjs run.json      or      require('./verify.cjs').verify(submission) */
const fs = require('fs'), path = require('path');
const {JSDOM} = require('jsdom');

const ROOT = path.join(__dirname, '..', '..', 'pillage');
const FILES = ['coasts.js', 'data.js', 'engine.js', 'events.js', 'qr.js', 'game.js'];
const read = f => fs.readFileSync(path.join(ROOT, f), 'utf8');
const MAX_STEPS = 60 * 60 * 60 * 120;  // 120 hours of play: far past anything a four-day contest allows
const MAX_EVENTS = 400000;

function boot(store, files) {
  files = files || {};
  const src = f => files[f] !== undefined ? files[f] : read(f);
  const dom = new JSDOM(src('index.html'), {runScripts: 'outside-only', url: 'https://the-reefer.com/pillage/'});
  const w = dom.window, errors = [], saves = [], env = {k: 0};
  w.addEventListener('error', e => errors.push(String(e.error || e.message)));
  const noop = () => {};
  const c2d = new Proxy({}, {get(t, k) { if (k in t) return t[k]; if (k === 'measureText') return () => ({width: 10}); if (/Gradient|Pattern/.test(k)) return () => ({addColorStop: noop}); if (k === 'getImageData' || k === 'createImageData') return () => ({data: new Uint8ClampedArray(4)}); return noop; }, set(t, k, v) { t[k] = v; return true; }});
  w.HTMLCanvasElement.prototype.getContext = () => c2d;
  w.HTMLCanvasElement.prototype.toDataURL = () => '';
  w.Path2D = class { moveTo() {} lineTo() {} closePath() {} quadraticCurveTo() {} bezierCurveTo() {} arc() {} rect() {} ellipse() {} };
  w.Element.prototype.getBoundingClientRect = () => ({left: 0, top: 0, width: 390, height: 520, right: 390, bottom: 520, x: 0, y: 0});
  w.Element.prototype.scrollIntoView = noop;
  w.requestAnimationFrame = () => 0;   // the checker turns the clock itself
  w.fetch = () => Promise.resolve({ok: false});
  w.matchMedia = () => ({matches: false, addEventListener: noop, removeEventListener: noop});
  Object.defineProperty(w.document, 'hidden', {get: () => false});
  // Dialogs: opening is plain. Closing sends no event by itself, because in a real browser the close event comes a moment
  // later. The recording says exactly when it came, and the checker sends it then.
  const stack = [];
  w.HTMLDialogElement.prototype.showModal = function () { if (this.hasAttribute('open')) return; this.setAttribute('open', ''); stack.push(this); };
  w.HTMLDialogElement.prototype.show = w.HTMLDialogElement.prototype.showModal;
  w.HTMLDialogElement.prototype.close = function () {
    if (!this.hasAttribute('open')) return;
    this.removeAttribute('open');
    const i = stack.lastIndexOf(this); if (i >= 0) stack.splice(i, 1);
    this.__pending = (this.__pending || 0) + 1;
  };
  for (const k in store) w.localStorage.setItem(k, store[k]);
  // A save is known by the step it came in and how many recorded moves had been made by then (counted by the checker,
  // since the replay's own recorder also notes the moves it is handed).
  w.PILLAGE_REPLAY = {onSave: (n, e, h, body) => saves.push({n, e: env.k, h, body})};
  for (const f of FILES) w.eval(src(f));
  return Object.assign(env, {w, P: w.__pillage, errors, saves, stack, dom});
}

class Refused extends Error {}

// One recorded move, made again exactly as the browser made it, or refused if it couldn't have been made.
function play(env, x) {
  const {w, P, stack} = env, doc = w.document, kind = x[1];
  const topDlg = () => stack.filter(d => d.hasAttribute('open')).pop() || null;
  const usable = el => {
    if (!el || !el.isConnected || el.closest('[hidden]') || el.closest('[inert]')) return false;
    if (el.disabled || el.closest('fieldset:disabled') || el.closest('[aria-disabled=true]')) return false;
    const dlg = el.closest('dialog'), top = topDlg();
    if (dlg && !dlg.hasAttribute('open')) return false;
    if (top && !top.contains(el)) return false;   // a modal window blocks everything behind it
    return true;
  };
  if (['kd', 'ku', 'kx', 'act', 'chart', 'log', 'go', 'pick'].includes(kind)) {
    const mv = x.slice(1);
    if (!P.cup.canInput(mv)) throw new Refused('a move that could not be made: ' + kind);
    P.cup.input(mv);
    return;
  }
  if (kind === 'c' || kind === 'ch' || kind === 'in' || kind === 'kt') {
    const el = P.cup.elOf(x[2]);
    if (!usable(el)) throw new Refused('a tap on something that was not there to tap: ' + x[2]);
    if (kind === 'c') {
      if (el.matches('input, select, textarea, label, canvas, a[href]')) throw new Refused('a tap the browser would not send');
      el.dispatchEvent(new w.MouseEvent('click', {bubbles: true, cancelable: true, view: w}));
    } else if (kind === 'ch') {
      if (el.matches('input[type=checkbox], input[type=radio]')) {
        const v = !!x[3];
        if (el.type === 'radio' && !v) throw new Refused('a radio button cannot be switched off');
        el.checked = v;
      } else if (el.matches('select')) {
        if (![...el.options].some(o => o.value === String(x[3]) && !o.disabled)) throw new Refused('a choice that was not on the list');
        el.value = String(x[3]);
      } else if (el.matches('input, textarea')) {
        if (el.readOnly) throw new Refused('typing into a box that takes none');
        el.value = String(x[3]);
      } else throw new Refused('a change to something that does not change');
      el.dispatchEvent(new w.Event('change', {bubbles: true}));
    } else if (kind === 'in') {
      if (!el.matches('input[type=text], textarea') || el.readOnly) throw new Refused('typing into a box that takes none');
      const v = String(x[3]);
      if (el.maxLength > 0 && v.length > el.maxLength) throw new Refused('more letters than the box holds');
      el.value = v;
      el.dispatchEvent(new w.Event('input', {bubbles: true}));
    } else {
      if (!el.closest('#port-tabs') || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(x[3])) throw new Refused('a key the game does not take there');
      el.focus();
      el.dispatchEvent(new w.KeyboardEvent('keydown', {key: x[3], bubbles: true, cancelable: true}));
    }
    return;
  }
  if (kind === 'x' || kind === 'z') {
    const dlg = doc.getElementById(String(x[2]));
    if (!dlg || dlg.tagName !== 'DIALOG') throw new Refused('a window that does not exist');
    if (kind === 'x') {
      if (!dlg.hasAttribute('open') || topDlg() !== dlg) throw new Refused('Escape on a window that was not on top');
      const ev = new w.Event('cancel', {cancelable: true});
      dlg.dispatchEvent(ev);
      if (!ev.defaultPrevented) dlg.close();
    } else {
      if (dlg.__pending > 0) dlg.__pending--;
      else if (dlg.hasAttribute('open') && topDlg() === dlg) dlg.close(), dlg.__pending--;   // closed by a second Escape, which some browsers allow
      else throw new Refused('a window closing that was never closed');
      dlg.dispatchEvent(new w.Event('close'));
    }
    return;
  }
  throw new Refused('a move of an unknown kind');
}

function checkSeg(seg, i) {
  if (!seg || !Array.isArray(seg.ev) || !Number.isInteger(seg.n) || seg.n < 0 || typeof seg.h !== 'string') throw new Refused('part ' + (i + 1) + ' is damaged');
  let last = 0;
  for (const x of seg.ev) {
    if (!Array.isArray(x) || !Number.isInteger(x[0]) || x[0] < last || x[0] > seg.n || typeof x[1] !== 'string') throw new Refused('part ' + (i + 1) + ' has moves out of order');
    last = x[0];
  }
}

// sub: {run: {id, seed, practice}, segs: [{ev, n, p0, h}, ...]}. Every part but the last ends where the phone last saved
// before the page was opened again; the last ends where the run was sent.
function verify(sub, opts) {
  opts = opts || {};
  const out = {ok: false, reason: '', parts: 0, steps: 0, xp: 0, level: 0, day: 0, gold: 0, stats: {}, captain: '', ship: '', over: ''};
  let env = null;
  try {
    if (!sub || !sub.run || !Number.isInteger(sub.run.seed) || !Array.isArray(sub.segs) || !sub.segs.length) throw new Refused('not a contest run');
    let steps = 0, events = 0, snapshot = null;
    sub.segs.forEach((seg, i) => {
      checkSeg(seg, i);
      steps += seg.n; events += seg.ev.length;
      if (steps > MAX_STEPS || events > MAX_EVENTS) throw new Refused('longer than any real run');
    });
    for (let i = 0; i < sub.segs.length; i++) {
      const seg = sub.segs[i], last = i === sub.segs.length - 1;
      if (env) env.dom.window.close();
      env = boot({'pillageTheReefer.prefs': JSON.stringify({fast: !!seg.p0})}, opts.files);
      const {P} = env;
      if (i === 0) P.cup.start({id: sub.run.id, seed: sub.run.seed, practice: !!sub.run.practice});
      else P.cup.resume(snapshot);
      const ev = seg.ev;
      let k = 0;
      const next = () => { env.k = k + 1; play(env, ev[k++]); };
      while (k < ev.length && ev[k][0] === 0) next();
      for (let s = 1; s <= seg.n; s++) {
        P.cup.tick();
        while (k < ev.length && ev[k][0] === s) next();
      }
      if (P.cup.rec.n !== seg.n) throw new Refused('part ' + (i + 1) + ' lost count of time');
      if (last) {
        if (P.cup.hash() !== seg.h) throw new Refused('the replay of part ' + (i + 1) + ' ends somewhere else than the run that was sent');
      } else {
        P.cup.save();
        const hit = env.saves.filter(s => s.n === seg.n && s.e === ev.length && s.h === seg.h).pop();
        if (!hit) throw new Refused('the replay of part ' + (i + 1) + ' ends somewhere else than the phone saved');
        snapshot = JSON.parse(hit.body);
      }
      out.parts = i + 1;
      out.steps += seg.n;
    }
    const st = env.P.state, D = env.w.PILLAGE_DATA, E = env.w.PILLAGE_ENGINE;
    Object.assign(out, {ok: true, xp: Math.round(st.xp) || 0, level: E.levelOf(st.xp), day: E.dayOf(st.dist), gold: Math.round(st.gold) || 0,
      captain: st.look.captain || '', ship: st.look.ship || '', over: (env.P.cup.run && env.P.cup.run.over) || ''});
    (D.BOARD && D.BOARD.stats || []).forEach(S => { out.stats[S.k] = S.k === 'days' ? E.dayOf(st.dist) : Math.max(0, Math.floor(st[S.k]) || 0); });
    if (st.gentle) throw new Refused('gentle seas do not count');
    if (env.errors.length) out.notes = env.errors.slice(0, 3);
  } catch (e) {
    out.ok = false;
    out.reason = e instanceof Refused ? e.message : 'the checker broke: ' + (e && e.message);
    out.broke = !(e instanceof Refused);   // the checker's own fault, not the player's: held for a person to look at
    if (env && env.P && env.P.state) { out.xp = Math.round(env.P.state.xp) || 0; }
  } finally {
    if (env) try { env.dom.window.close(); } catch (e) { /* closed */ }
  }
  return out;
}

module.exports = {verify, boot, play, Refused};

if (require.main === module) {
  const sub = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  console.log(JSON.stringify(verify(sub), null, 1));
}
