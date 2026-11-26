/* Pillage the Reefer: the game screen, controls, ports, people and saving. */
(function () {
  'use strict';
  var D = window.PILLAGE_DATA, E = window.PILLAGE_ENGINE;
  if (!D || !E || !document.getElementById('sea')) return;
  var GOODS = D.GOODS, MAPS = D.MAPS, PORTS = D.PORTS, STASHES = D.STASHES, PEOPLE = D.PEOPLE, QUESTS = D.QUESTS, UP = D.UPGRADES;
  var SAVE_KEY = 'pillageTheReefer.v1', PREF_KEY = 'pillageTheReefer.prefs';
  var FOG = 40, REVEAL = 190, ORDER = Object.keys(GOODS), NPORTS = Object.keys(PORTS).length;
  var EV = window.PILLAGE_EVENTS || {sea: [], port: []};
  var clamp = E.clamp, SMOKE = D.SMOKE || {};
  var STRAINS = ORDER.filter(function (g) { return !GOODS[g].kind; });
  function $(id) { return document.getElementById(id); }

  /* ---------- small helpers ---------- */
  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) { if (attrs[k] !== null && attrs[k] !== undefined && attrs[k] !== false) n.setAttribute(k, attrs[k]); }
    if (text !== undefined && text !== null) n.textContent = text;
    return n;
  }
  function fmt(n) { return Math.round(n).toLocaleString('en-US'); }
  function plural(n, one, many) { return n === 1 ? one : (many || one + 's'); }
  function baleWord(n) { return fmt(n) + ' ' + plural(n, 'bale'); }
  function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function andList(a) { return a.length < 2 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1]; }
  function turnToward(a, b, max) {
    var d = ((b - a + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    return a + clamp(d, -max, max);
  }
  function compass(dx, dy) {
    var a = Math.atan2(-dy, dx) * 180 / Math.PI;
    var dirs = ['east', 'north-east', 'north', 'north-west', 'west', 'south-west', 'south', 'south-east'];
    return dirs[Math.round(((a + 360) % 360) / 45) % 8];
  }
  function track(a) { try { if (window.directoryTrack) window.directoryTrack('pillage-' + a); } catch (e) { /* counting is optional */ } }

  /* ---------- preferences (kept apart from the voyage) ---------- */
  var prefs = {sound: false, motion: null, fast: false};
  try { var sp = JSON.parse(localStorage.getItem(PREF_KEY)); if (sp) { for (var pk in prefs) if (pk in sp) prefs[pk] = sp[pk]; } } catch (e) { /* private mode */ }
  var osReduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function calm() { return prefs.motion === null ? !!(osReduce && osReduce.matches) : !!prefs.motion; }
  function savePrefs() { try { localStorage.setItem(PREF_KEY, JSON.stringify(prefs)); } catch (e) { /* ignore */ } }

  /* ---------- sound (off unless the player turns it on) ---------- */
  var actx = null;
  function tone(f, at, dur, type, vol, to) {
    var o = actx.createOscillator(), g = actx.createGain();
    o.type = type || 'sine';
    o.frequency.setValueAtTime(f, at);
    if (to) o.frequency.exponentialRampToValueAtTime(to, at + dur);
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(vol || 0.1, at + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(g); g.connect(actx.destination);
    o.start(at); o.stop(at + dur + 0.03);
  }
  function sfx(name) {
    if (!prefs.sound) return;
    try {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      if (actx.state === 'suspended') actx.resume();
      var n = actx.currentTime;
      if (name === 'coin') { tone(1046, n, 0.08, 'square', 0.04); tone(1568, n + 0.07, 0.14, 'square', 0.04); }
      else if (name === 'pickup') { tone(523, n, 0.1, 'triangle', 0.09); tone(784, n + 0.09, 0.16, 'triangle', 0.09); }
      else if (name === 'boom') { tone(150, n, 0.45, 'sawtooth', 0.08, 45); }
      else if (name === 'fanfare') { [523, 659, 784, 1046].forEach(function (f, i) { tone(f, n + i * 0.13, 0.24, 'triangle', 0.09); }); }
      else if (name === 'splash') { tone(320, n, 0.3, 'sine', 0.07, 90); }
      else if (name === 'bad') { tone(300, n, 0.2, 'square', 0.05, 140); }
    } catch (e) { /* no audio here */ }
  }

  /* ---------- the voyage ---------- */
  var state = null, started = false, fogs = {}, npcs = {}, floaters = {}, jokes = [];
  var ship = {vx: 0, vy: 0}, auto = null, grace = 0, t = 0, wake = [], action = null, actionKey = '', justLeft = null;
  var keys = {}, timers = {reveal: 0, save: 4, where: 0, wake: 0}, lastWhereKey = '', toastTimer = 0;
  var levelUp = 0, evClock = 70, evRecent = [], lastPortEv = -999;

  function newState() {
    var p = PORTS.tortuga;
    return {v: 1, map: 'windward', x: p.dock[0], y: p.dock[1], angle: -Math.PI / 2, gold: 250, cargo: {}, basis: {},
      up: {hold: 0, hull: 0, cannons: 0, crew: 0, sails: 0, lavender: 0}, hull: UP.hull.levels[0], xp: 0, pts: 0,
      skill: {fight: 0, sail: 0, charm: 0}, dist: 0, hints: {}, found: {}, quests: {}, visited: {},
      known: {tortuga: 1, portroyal: 1, petitgoave: 1}, collected: {}, pillaged: 0, sunk: 0, tmap: null, dug: 0,
      flags: {}, docked: null, fog: {}, grit: 0, buff: null, seen: {}};
  }
  function curMap() { return MAPS[state.map]; }
  // Your ship and skills, plus whatever boost you've smoked.
  function stats() {
    var b = boost();
    if (!b) return E.stats(state);
    var k = state.skill, st = E.stats({up: state.up, skill: {fight: k.fight + (b.fight || 0), sail: k.sail + (b.sail || 0), charm: k.charm + (b.charm || 0)}});
    if (b.speed) st.speed *= 1 + b.speed;
    return st;
  }
  function hullMax() { return UP.hull.levels[state.up.hull]; }
  function level() { return E.levelOf(state.xp); }
  function title(lv) { return D.LEVELS[(lv || level()) - 1].title; }
  function tier() { return D.SEA_TIER[state.map] || 1; }
  function cargoCount() { var n = 0; for (var g in state.cargo) n += state.cargo[g]; return n; }
  function capacity() { return UP.hold.levels[state.up.hold]; }
  function space() { return Math.max(0, capacity() - cargoCount()); }
  function addCargo(g, n) {
    n = Math.max(0, Math.min(n, space()));
    if (n > 0) {
      state.cargo[g] = (state.cargo[g] || 0) + n;
      if (!state.collected[g]) { state.collected[g] = 1; gainXp(10); }
    }
    return n;
  }
  function takeCargo(g, n) {
    var have = state.cargo[g] || 0;
    n = Math.max(0, Math.min(n, have));
    if (n > 0 && state.basis[g]) { state.basis[g] = Math.round(state.basis[g] * (have - n) / have); if (!state.basis[g]) delete state.basis[g]; }
    state.cargo[g] = have - n;
    if (!state.cargo[g]) delete state.cargo[g];
    return n;
  }
  // Selling earns renown for the profit over what you paid (found and looted bales cost nothing).
  function sellGoods(g, n, price) {
    var have = state.cargo[g] || 0, cost = have ? (state.basis[g] || 0) * Math.min(n, have) / have : 0;
    n = takeCargo(g, n);
    if (n <= 0) return null;
    state.gold += n * price;
    return {n: n, gold: n * price, xp: Math.floor(Math.max(0, n * price - cost) / 20)};
  }
  function cargoValue() { var v = 0; for (var g in state.cargo) v += state.cargo[g] * GOODS[g].base; return v; }
  function day() { return E.dayOf(state.dist); }
  function pieces() { return ['s1', 's2', 's3'].filter(function (k) { return state.found[k]; }).length; }
  function speed() { return stats().speed; }
  function rank() { return state.found.emerald ? 'Legend of the Reefer' : title(); }
  function gainXp(n) {
    n = Math.round(n);
    if (!(n > 0) || !state) return '';
    var before = level();
    state.xp += n;
    var after = level();
    if (after > before) {
      state.pts += after - before;
      levelUp = after;
      sfx('fanfare');
      track('level-' + after);
    }
    return ' ⭐ +' + n + ' renown.';
  }
  function hurt(n, floor) {
    var low = Math.min(state.hull, floor || 1), k = Math.min(n, Math.max(0, state.hull - low));
    state.hull -= k;
    return k;
  }
  function heal(n) { var k = Math.max(0, Math.min(n, hullMax() - state.hull)); state.hull += k; return k; }

  /* ---------- odds: the number on the button is exactly the number that's rolled ---------- */
  // A miss earns a second wind: +10% on the next check for each miss in a row, up to +30%. Some boosts add luck too.
  function boost() { var b = state && state.buff; return b && SMOKE[b.g] && state.dist < b.until ? SMOKE[b.g] : null; }
  function edge() { var b = boost(); return Math.min(0.3, 0.1 * (state.grit || 0)) + ((b && b.luck) || 0); }
  function chanceOf(p) { return Math.round(clamp(p + edge(), 0.05, 0.95) * 100); }
  function pct(p) { return chanceOf(p) + '% chance'; }
  function roll(p) {
    var ok = Math.random() * 100 < chanceOf(p);
    state.grit = ok ? 0 : Math.min(3, (state.grit || 0) + 1);
    return ok;
  }
  function edgeHint() {
    var b = boost(), parts = [];
    if (state.grit) parts.push('+' + Math.min(30, 10 * state.grit) + '% second wind after ' + ['a miss', 'two misses', 'three misses'][Math.min(3, state.grit) - 1]);
    if (b && b.luck) parts.push('+' + Math.round(b.luck * 100) + '% from your ' + b.name);
    return parts.length ? '🍀 Already counted in these odds: ' + andList(parts) + '.' : '';
  }

  /* ---------- smoking a bale: a short, strain-specific boost ---------- */
  var mendAcc = 0;
  function verb(g) { return (SMOKE[g] && SMOKE[g].verb) || 'smoke'; }
  function boostDays(S) { return S.days || 2; }
  function boostLeft() { return state.buff ? Math.max(1, Math.ceil((state.buff.until - state.dist) / 900)) : 0; }
  function smoke(g) {
    var S = SMOKE[g], had = boost();
    if (!S || !(state.cargo[g] > 0)) return false;
    takeCargo(g, 1);
    state.buff = {g: g, until: Math.round(state.dist) + 900 * boostDays(S)};
    mendAcc = 0;
    sfx('pickup');
    track('smoke');
    say('🔥 You ' + (verb(g) === 'eat' ? 'pass round a crate of ' : 'light up a bale of ') + GOODS[g].name + '. ' + S.flavor + ' Boost: ' + S.name + ', about ' + boostDays(S) + ' days of sailing. ' + S.does +
      (had && had !== S ? ' It replaces ' + had.name + '.' : ''));
    save();
    return true;
  }
  // Called as the ship covers distance: wears the boost off and lets Honey Hands patch the hull.
  function boostTick(moved) {
    var b = state.buff;
    if (!b) return '';
    var S = SMOKE[b.g];
    if (S && S.mend && state.hull < hullMax()) {
      mendAcc += Math.min(moved, Math.max(0, b.until - (state.dist - moved)));
      if (mendAcc >= 100) { heal(Math.floor(mendAcc / 100)); mendAcc %= 100; }
    }
    if (!S || state.dist >= b.until) { state.buff = null; mendAcc = 0; return S ? '🔥 Your ' + S.name + ' boost has worn off.' : ''; }
    return '';
  }
  function nearPort(x, y, r, mid) {
    mid = mid || state.map;
    for (var pid in PORTS) { var p = PORTS[pid]; if (p.map === mid && Math.hypot(p.dock[0] - x, p.dock[1] - y) < r) return pid; }
    return null;
  }

  /* ---------- fog of war: the parchment you haven't sailed yet ---------- */
  function fogFor(mid) {
    if (!fogs[mid]) {
      var m = MAPS[mid], c = Math.ceil(m.w / FOG), r = Math.ceil(m.h / FOG);
      fogs[mid] = {cols: c, rows: r, a: new Uint8Array(c * r), canvas: null, dirty: true};
    }
    return fogs[mid];
  }
  function reveal(mid, x, y, rad) {
    var f = fogFor(mid), changed = false;
    var c0 = Math.max(0, Math.floor((x - rad) / FOG)), c1 = Math.min(f.cols - 1, Math.floor((x + rad) / FOG));
    var r0 = Math.max(0, Math.floor((y - rad) / FOG)), r1 = Math.min(f.rows - 1, Math.floor((y + rad) / FOG));
    for (var r = r0; r <= r1; r++) {
      for (var c = c0; c <= c1; c++) {
        var i = r * f.cols + c;
        if (!f.a[i] && Math.hypot((c + 0.5) * FOG - x, (r + 0.5) * FOG - y) < rad) { f.a[i] = 1; changed = true; }
      }
    }
    if (changed) f.dirty = true;
  }
  function explored(mid, x, y) {
    var f = fogFor(mid);
    return !!f.a[clamp(Math.floor(y / FOG), 0, f.rows - 1) * f.cols + clamp(Math.floor(x / FOG), 0, f.cols - 1)];
  }
  function encodeFog(f) {
    var s = '';
    for (var i = 0; i < f.a.length; i += 8) {
      var b = 0;
      for (var k = 0; k < 8; k++) if (f.a[i + k]) b |= 1 << k;
      s += String.fromCharCode(b);
    }
    return btoa(s);
  }
  function decodeFog(mid, s) {
    var f = fogFor(mid);
    try {
      var bin = atob(s);
      for (var i = 0; i < bin.length; i++) {
        var b = bin.charCodeAt(i);
        for (var k = 0; k < 8; k++) { var idx = i * 8 + k; if (idx < f.a.length) f.a[idx] = (b >> k) & 1; }
      }
      f.dirty = true;
    } catch (e) { /* a damaged save just means a fresh chart */ }
  }
  function fogCanvas(mid) {
    var f = fogFor(mid);
    if (!f.canvas) { f.canvas = document.createElement('canvas'); f.canvas.width = f.cols; f.canvas.height = f.rows; f.dirty = true; }
    if (f.dirty) {
      var g = f.canvas.getContext('2d'), img = g.createImageData(f.cols, f.rows);
      for (var i = 0; i < f.a.length; i++) {
        img.data[i * 4] = 236; img.data[i * 4 + 1] = 223; img.data[i * 4 + 2] = 186; img.data[i * 4 + 3] = f.a[i] ? 0 : 250;
      }
      g.putImageData(img, 0, 0);
      f.dirty = false;
    }
    return f.canvas;
  }
  function portKnown(pid) {
    var p = PORTS[pid];
    return !!(state.known[pid] || state.visited[pid] || explored(p.map, p.dock[0], p.dock[1]));
  }

  /* ---------- saving (this browser only) ---------- */
  function save() {
    if (!state || !started) return;
    try {
      state.fog = {};
      for (var mid in fogs) state.fog[mid] = encodeFog(fogs[mid]);
      state.saved = Date.now();
      localStorage.setItem(SAVE_KEY, JSON.stringify(state));
    } catch (e) { /* storage full or blocked: play on */ }
  }
  function loadSaved() {
    try {
      var s = JSON.parse(localStorage.getItem(SAVE_KEY));
      return s && s.v === 1 && MAPS[s.map] ? s : null;
    } catch (e) { return null; }
  }
  function fromSave(s) {
    var b = newState();
    for (var k in b) {
      if (s[k] === undefined || s[k] === null) continue;
      if (typeof b[k] === 'object' && b[k] !== null) {
        if (typeof s[k] === 'object') b[k] = k === 'up' || k === 'skill' ? Object.assign(b[k], s[k]) : s[k];
      } else if (typeof b[k] === typeof s[k]) b[k] = s[k];
    }
    if (s.docked && PORTS[s.docked]) b.docked = s.docked; else b.docked = null;
    for (var g in b.cargo) if (!GOODS[g] || !(b.cargo[g] > 0)) delete b.cargo[g];
    for (var u in b.up) if (!UP[u] || !(b.up[u] >= 0) || b.up[u] >= UP[u].levels.length) b.up[u] = 0;
    for (var sk in b.skill) b.skill[sk] = clamp(Math.floor(b.skill[sk]) || 0, 0, D.SKILL_MAX);
    if (s.xp === undefined) {
      // A voyage saved before captains had levels: credit what it already did.
      var xp = Object.keys(b.visited).length * 25 + b.pillaged * 30 + Object.keys(b.collected).length * 10;
      ['s1', 's2', 's3'].forEach(function (k) { if (b.found[k]) xp += 100; });
      if (b.found.emerald) xp += 400;
      Object.keys(b.quests).forEach(function (q) { if (b.quests[q] === 'done' && QUESTS[q]) xp += QUESTS[q].gold / 4; });
      b.xp = Math.round(xp);
      b.pts = E.levelOf(b.xp) - 1;
      b.hull = UP.hull.levels[b.up.hull];
    }
    b.xp = Math.max(0, Math.round(b.xp) || 0);
    b.pts = Math.max(0, Math.floor(b.pts) || 0);
    b.hull = clamp(Math.round(b.hull) || 1, 1, UP.hull.levels[b.up.hull]);
    if (b.tmap && !(MAPS[b.tmap.map] && b.tmap.at)) b.tmap = null;
    if (b.buff && !(SMOKE[b.buff.g] && b.buff.until > 0)) b.buff = null;
    b.grit = clamp(Math.floor(b.grit) || 0, 0, 3);
    if (typeof b.seen !== 'object' || Array.isArray(b.seen)) b.seen = {};
    for (var sp in b.seen) if (!PORTS[sp] || !b.seen[sp] || typeof b.seen[sp].s !== 'object') delete b.seen[sp];
    return b;
  }

  /* ---------- seas, ships and floating cargo ---------- */
  function enterMap(mid) {
    var m = E.prepareMap(mid);
    if (!m.draw) {
      m.draw = m.polys.map(function (p) {
        var path = new Path2D(), inner = new Path2D(), c = p.c;
        p.pts.forEach(function (q, i) {
          if (i) path.lineTo(q[0], q[1]); else path.moveTo(q[0], q[1]);
          var x = c[0] + (q[0] - c[0]) * 0.55, y = c[1] + (q[1] - c[1]) * 0.55;
          if (i) inner.lineTo(x, y); else inner.moveTo(x, y);
        });
        path.closePath(); inner.closePath();
        var size = Math.min(p.bb.x1 - p.bb.x0, p.bb.y1 - p.bb.y0);
        return {path: path, inner: size > 36 ? inner : null, land: p.land};
      });
    }
    if (!npcs[mid]) {
      npcs[mid] = m.patrols.map(function (p) {
        var s = E.nearestFreePoint(m, p.route[0][0], p.route[0][1]);
        return {kind: p.kind, tier: D.SEA_TIER[mid] || 1, route: p.route, leg: 0, path: null, pi: 0, x: s[0], y: s[1], angle: 0, cool: 8, chase: false, looted: false,
          name: pick(p.kind === 'customs' ? D.CUSTOMS_NAMES : D.MERCHANT_NAMES)};
      });
      for (var k = 0; k < (D.PIRATE_COUNT[mid] || 0); k++) npcs[mid].push(makePirate(m));
    }
    if (!floaters[mid]) {
      floaters[mid] = {list: [], timer: 12, bottle: 25};
      for (var i = 0; i < 3; i++) { var b = spawnFloater(m, false); if (b) floaters[mid].list.push(b); }
    }
    return m;
  }
  function freeSpot(m, farFromShip) {
    for (var tries = 0; tries < 80; tries++) {
      var x = 80 + Math.random() * (m.w - 160), y = 80 + Math.random() * (m.h - 160);
      if (m.nav.blocked[E.cellIdx(m, x, y)] || nearPort(x, y, 280, m.id)) continue;
      if (farFromShip && state && state.map === m.id && Math.hypot(x - state.x, y - state.y) < 480) continue;
      return [x, y];
    }
    return E.nearestFreePoint(m, m.w / 2, m.h / 2);
  }
  function pirateShip(m, n) {
    var s = freeSpot(m, true);
    n.x = s[0]; n.y = s[1]; n.route = [s, freeSpot(m), freeSpot(m)]; n.leg = 0; n.path = null; n.pi = 0;
    n.gone = false; n.chase = false; n.angle = Math.random() * 6;
    if (n.kind === 'pirate') { n.captain = pick(D.PIRATE_CAPTAINS); n.name = pick(D.PIRATE_SHIPS); }
    return n;
  }
  function makePirate(m) { return pirateShip(m, {kind: 'pirate', tier: D.SEA_TIER[m.id] || 1, cool: 10}); }
  function maybeBoss(m, list) {
    if (m.id !== D.BOSS.map || state.flags.boss || level() < D.BOSS.level || list.some(function (n) { return n.kind === 'boss'; })) return;
    list.push(pirateShip(m, {kind: 'boss', tier: 4, cool: 5, captain: D.BOSS.captain, name: D.BOSS.ship}));
  }
  var DANGER = ['Easy pickings', 'A fair fight', 'Looks risky', 'Too strong for us'];
  function dangerOf(n) { return E.danger(stats(), state.hull, E.foe(n.kind, n.tier)); }
  function spawnFloater(m, bottle) {
    for (var tries = 0; tries < 40; tries++) {
      var x = 40 + Math.random() * (m.w - 80), y = 40 + Math.random() * (m.h - 80);
      if (m.nav.blocked[E.cellIdx(m, x, y)]) continue;
      if (state && Math.hypot(x - state.x, y - state.y) < 180) continue;
      var g = bottle ? 'bottle' : Math.random() < 0.16 ? 'mermaid' : pick(D.COMMON);
      return {x: x, y: y, g: g, n: g === 'mermaid' || bottle ? 1 : 1 + Math.floor(Math.random() * 3), ph: Math.random() * 6};
    }
    return null;
  }

  /* ---------- messages ---------- */
  var pending = null;
  function announce(msg) {
    var dlg = openDialogEl(), live = dlg ? dlg.querySelector('.dlg-live') : $('live');
    if (!live) live = $('live');
    if (pending && pending.live === live) { pending.msg += ' ' + msg; return; }
    pending = {live: live, msg: msg};
    live.textContent = '';
    setTimeout(function () { var p = pending; pending = null; if (p) p.live.textContent = p.msg; }, 60);
  }
  function say(msg) {
    var dlg = openDialogEl(), live = dlg && dlg.querySelector('.dlg-live');
    if (live) { live.hidden = false; live.textContent = msg; return; }
    var tEl = $('toast');
    tEl.textContent = msg;
    tEl.classList.add('show');
    toastTimer = Math.max(4, msg.length / 18);
    announce(msg);
  }
  var parrotLast = {};
  function parrot(key, msg, once, every) {
    if (once && state.flags['p_' + key]) return;
    if (!once && parrotLast[key] !== undefined && t - parrotLast[key] < (every || 40)) return;
    parrotLast[key] = t;
    if (once) state.flags['p_' + key] = 1;
    say('🦜 ' + D.PARROT + ': “' + msg + '”');
  }

  /* ---------- dialogs ---------- */
  function openDialogEl() { return document.querySelector('dialog[open]'); }
  function openDialog(dlg, focusEl) {
    var live = dlg.querySelector('.dlg-live');
    if (live) { live.textContent = ''; }
    if (!dlg.open) { if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', ''); }
    keys = {};
    if (focusEl) setTimeout(function () { focusEl.focus(); }, 0);
  }
  function closeDialog(dlg) {
    if (typeof dlg === 'string') dlg = $(dlg);
    if (dlg.open) { if (typeof dlg.close === 'function') dlg.close(); else { dlg.removeAttribute('open'); dlg.dispatchEvent(new Event('close')); } }
  }
  function focusSea() {
    if (!started || openDialogEl()) return;
    try { $('sea').focus({preventScroll: true}); } catch (e) { $('sea').focus(); }
  }
  function paused() { return !started || !!openDialogEl() || document.hidden; }

  var noteDone = null;
  function note(title, text, extra, onClose) {
    $('note-title').textContent = title;
    var b = $('note-body');
    b.textContent = '';
    String(text).split('\n\n').forEach(function (p) { b.appendChild(el('p', null, p)); });
    if (extra) b.appendChild(extra);
    noteDone = onClose || null;
    openDialog($('dlg-note'), $('note-ok'));
  }

  /* ---------- sailing ---------- */
  function exitPointFrom(e, at) {
    var r = e.rect;
    if (r[2] > r[3]) return [clamp(at[0], r[0] + 40, r[0] + r[2] - 40), r[1] + r[3] / 2];
    return [r[0] + r[2] / 2, clamp(at[1], r[1] + 20, r[1] + r[3] - 20)];
  }
  function exitPoint(e) { return exitPointFrom(e, [state.x, state.y]); }
  function nextSea(from, to) {
    var prev = {}, q = [from];
    prev[from] = null;
    while (q.length) {
      var c = q.shift();
      if (c === to) break;
      MAPS[c].exits.forEach(function (e) { if (!(e.to in prev)) { prev[e.to] = c; q.push(e.to); } });
    }
    if (!(to in prev) || to === from) return null;
    var hop = to;
    while (prev[hop] !== from) hop = prev[hop];
    return hop;
  }
  function planRoute(goal) {
    var m = curMap(), target, exit = null;
    if (goal.map === state.map) target = [goal.x, goal.y];
    else {
      var next = nextSea(state.map, goal.map);
      exit = m.exits.filter(function (e) { return e.to === next; })[0];
      if (!exit) return false;
      target = exitPoint(exit);
    }
    var path = E.findPath(m, state.x, state.y, target[0], target[1]);
    if (!path) { say('Your navigator can’t find a sea route from here. Try sailing a little way first.'); return false; }
    if (state.docked) leavePort(true);
    auto = {goal: goal, path: path, i: 0, exit: exit, target: target, stuck: 0, chk: 0, lx: state.x, ly: state.y};
    return true;
  }
  function setCourse(goal) {
    if (planRoute(goal)) {
      if (goal.type !== 'point') say('🧭 Setting course for ' + goal.label + '.');
      focusSea();
    }
  }
  function arrive() {
    var a = auto;
    auto = null;
    ship.vx *= 0.3; ship.vy *= 0.3;
    if (!a) return;
    if (a.exit) { transition(a.exit, a.goal); return; }
    var g = a.goal;
    if (g.type === 'port') dock(g.id);
    else if (g.type === 'stash' || g.type === 'tmap') tryDig(g.id);
  }
  function transition(exit, goal) {
    goal = goal || (auto && auto.goal);
    auto = null;
    var m = enterMap(exit.to), a = exit.arrive;
    var x = a[0] === 'x' ? clamp(state.x, 80, m.w - 80) : a[0];
    var f = E.nearestFreePoint(m, x, a[1]);
    state.map = exit.to; state.x = f[0]; state.y = f[1];
    state.flags['seen_' + exit.to] = 1;
    ship.vx *= 0.5; ship.vy *= 0.5; wake = [];
    grace = 1.5;
    reveal(state.map, state.x, state.y, REVEAL);
    snapCamera();
    say('⛵ You sail into ' + m.name + '. ' + m.blurb);
    if (goal && goal.type !== 'point') planRoute(goal);
    updateWhere(true);
    save();
  }
  function dock(pid, lead) {
    var p = PORTS[pid], first = !state.visited[pid];
    auto = null; ship.vx = ship.vy = 0;
    state.docked = pid; state.visited[pid] = 1; state.known[pid] = 1;
    notePrices(pid);
    var f = E.nearestFreePoint(curMap(), p.dock[0], p.dock[1]);
    state.x = f[0]; state.y = f[1];
    reveal(state.map, p.dock[0], p.dock[1], 170);
    sfx('splash');
    var msg = (lead ? lead + ' ' : '') + (first ? '⚓ Your first visit to ' + p.name + '!' + gainXp(25) : '');
    if (state.gold < 30 && !cargoCount() && state.flags.relief !== day()) {
      state.flags.relief = day();
      state.gold += 100;
      msg += ' The harbourmaster takes pity on your empty purse and lends you 100 doubloons. “Pay me back when you’re famous.”';
    }
    checkGoals();
    save();
    updateWhere(true);
    var ev = !first && t - lastPortEv > 90 && Math.random() < 0.25 ? pickEvent(EV.port) : null;
    function open() { openPort(pid, first ? 'tavern' : 'market'); if (msg) say(msg.trim()); }
    if (ev) { lastPortEv = t; runEvent(ev, open); } else open();
  }
  function leavePort(silent, quick) {
    if (!state.docked) return;
    var pid = state.docked;
    state.docked = null;
    justLeft = pid;
    grace = 1.2;
    closeDialog('dlg-port');
    if (!silent) say('⛵ You cast off from ' + PORTS[pid].name + '.');
    updateWhere(true);
    if (!quick && !state.flags.p_steer) setTimeout(function () { parrot('steer', 'Arrow keys or tap the sea to steer! Chart & sail picks a port for you! Squawk!', true); }, 1200);
    save();
    focusSea();
  }

  function step(dt) {
    t += dt;
    if (toastTimer > 0) { toastTimer -= dt; if (toastTimer <= 0) $('toast').classList.remove('show'); }
    if (paused() || state.docked) return;
    if (levelUp) { showLevelUp(); return; }
    var m = curMap();
    if (grace > 0) grace -= dt;

    var ix = 0, iy = 0, tx = 0, ty = 0, sp = speed();
    if (keys.ArrowLeft || keys.a) ix -= 1;
    if (keys.ArrowRight || keys.d) ix += 1;
    if (keys.ArrowUp || keys.w) iy -= 1;
    if (keys.ArrowDown || keys.s) iy += 1;
    if (ix || iy) {
      auto = null;
      var L = Math.hypot(ix, iy);
      tx = ix / L * sp; ty = iy / L * sp;
    } else if (auto) {
      var tg = auto.path[auto.i], dx = tg[0] - state.x, dy = tg[1] - state.y, d = Math.hypot(dx, dy), last = auto.i === auto.path.length - 1;
      if (d < (last ? 8 : 16)) {
        auto.i++;
        if (auto.i >= auto.path.length) { arrive(); return; }
      } else {
        var s2 = sp * (prefs.fast ? 2.2 : 1);
        if (last && d < 60) s2 *= Math.max(0.35, d / 60);
        tx = dx / d * s2; ty = dy / d * s2;
      }
    }
    var k = Math.min(1, dt * 3.2);
    ship.vx += (tx - ship.vx) * k; ship.vy += (ty - ship.vy) * k;
    var ox = state.x, oy = state.y, nx = state.x + ship.vx * dt, ny = state.y + ship.vy * dt;
    if (!E.shipBlocked(m, nx, state.y)) state.x = nx; else ship.vx *= -0.2;
    if (!E.shipBlocked(m, state.x, ny)) state.y = ny; else ship.vy *= -0.2;
    var moved = Math.hypot(state.x - ox, state.y - oy), vs = Math.hypot(ship.vx, ship.vy);
    state.dist += moved;
    var worn = boostTick(moved);
    if (worn) say(worn);
    if (vs > 6) state.angle = turnToward(state.angle, Math.atan2(ship.vy, ship.vx), dt * 5);

    // A stuck autopilot looks for another way, then gives up.
    if (auto) {
      auto.chk += dt;
      if (auto.chk > 1.2) {
        if (Math.hypot(state.x - auto.lx, state.y - auto.ly) < 4) {
          auto.stuck++;
          var np = auto.stuck < 3 ? E.findPath(m, state.x, state.y, auto.target[0], auto.target[1]) : null;
          if (np) { auto.path = np; auto.i = 0; } else { auto = null; say('Your crew can’t find a way through. Try steering a little first.'); }
        }
        if (auto) { auto.chk = 0; auto.lx = state.x; auto.ly = state.y; }
      }
    }

    timers.wake -= dt;
    if (!calm() && vs > 25 && timers.wake <= 0) {
      timers.wake = 0.07;
      wake.push({x: state.x - Math.cos(state.angle) * 12, y: state.y - Math.sin(state.angle) * 12, age: 0});
    }
    for (var w = wake.length - 1; w >= 0; w--) { wake[w].age += dt; if (wake[w].age > 1.6) wake.splice(w, 1); }

    timers.reveal -= dt;
    if (timers.reveal <= 0) { timers.reveal = 0.2; var bs = boost(); reveal(state.map, state.x, state.y, REVEAL * ((bs && bs.sight) || 1)); }

    if (grace <= 0) {
      for (var e = 0; e < m.exits.length; e++) {
        var r = m.exits[e].rect;
        if (state.x >= r[0] && state.x <= r[0] + r[2] && state.y >= r[1] && state.y <= r[1] + r[3]) { transition(m.exits[e]); return; }
      }
    }
    pickups(m, dt);
    if (paused()) return;
    updateNpcs(m, dt);
    if (paused()) return;
    evClock -= dt;
    if (evClock <= 0) {
      var busy = npcs[state.map].some(function (n) { return !n.gone && Math.hypot(n.x - state.x, n.y - state.y) < 280; });
      if (vs > 10 && grace <= 0 && !busy && !nearPort(state.x, state.y, 220)) {
        var ev = pickEvent(EV.sea);
        evClock = 75 + Math.random() * 40;
        if (ev) { runEvent(ev); return; }
      } else evClock = 5;
    }
    updateAction();
    timers.save -= dt;
    if (timers.save <= 0) { timers.save = 5; save(); }
    timers.where -= dt;
    if (timers.where <= 0) { timers.where = 1.2; updateWhere(); }
  }

  function pickups(m, dt) {
    var F = floaters[state.map];
    F.timer -= dt;
    if (F.timer <= 0) {
      var comb = boost() && boost().comb;
      F.timer = (16 + Math.random() * 18) * (comb ? 0.5 : 1);
      if (F.list.filter(function (b) { return b.g !== 'bottle'; }).length < (comb ? 6 : 4)) { var b = spawnFloater(m, false); if (b) F.list.push(b); }
    }
    F.bottle -= dt;
    if (F.bottle <= 0) {
      F.bottle = 70 + Math.random() * 50;
      if (!F.list.some(function (b) { return b.g === 'bottle'; })) { var bt = spawnFloater(m, true); if (bt) F.list.push(bt); }
    }
    for (var i = F.list.length - 1; i >= 0; i--) {
      var f = F.list[i];
      if (Math.hypot(f.x - state.x, f.y - state.y) > 22) continue;
      if (f.g === 'bottle') { F.list.splice(i, 1); sfx('pickup'); openBottle(); return; }
      if (space() <= 0) { parrot('full', 'Hold’s full! Hold’s full! Sell, sell! Squawk!', false, 25); continue; }
      var n = addCargo(f.g, f.n);
      F.list.splice(i, 1);
      sfx('pickup');
      say('📦 You fish ' + baleWord(n) + ' of ' + GOODS[f.g].name + ' out of the sea.');
      checkGoals();
    }
  }
  function openBottle() {
    var text;
    if (jokes.length && Math.random() < 0.75) text = 'You fish a bottle out of the waves. The note inside says:\n\n“' + pick(jokes) + '”';
    else text = 'You fish a bottle out of the waves. ' + pick(D.BOTTLE_TIPS);
    note('🍾 Message in a bottle', text);
  }

  function updateNpcs(m, dt) {
    var list = npcs[state.map], hasCargo = cargoCount() > 0, safe = !!nearPort(state.x, state.y, 170), weak = state.hull < hullMax() * 0.35;
    var bz = boost(), calmed = !!(bz && bz.calm);
    maybeBoss(m, list);
    for (var i = 0; i < list.length; i++) {
      var n = list[i], raider = n.kind === 'pirate';
      if (n.cool > 0) n.cool -= dt;
      if (n.looted && n.cool <= 0) { n.looted = false; n.name = pick(D.MERCHANT_NAMES); }
      if (n.gone) { if (n.cool <= 0) pirateShip(m, n); continue; }
      var d = Math.hypot(n.x - state.x, n.y - state.y), tx, ty, chase = false;
      var sp = n.kind === 'customs' ? 78 : n.kind === 'merchant' ? 48 : 64;
      if (n.kind === 'customs') {
        var nose = 210 * noseFactor();
        chase = n.cool <= 0 && hasCargo && d < nose && E.walkable(m, [n.x, n.y], [state.x, state.y]);
        if (chase && !n.chase) parrot('customs', 'Blue sails! Blue sails! Customs! Squawk!', false, 30);
      } else if (raider) {
        // Pirates leave you be near a port's guns, and don't bother with a ship that's already battered.
        chase = n.cool <= 0 && !safe && !weak && !calmed && d < 240 && E.walkable(m, [n.x, n.y], [state.x, state.y]);
        if (chase && !n.chase) parrot('pirate', 'Black sails! Pirates! ' + DANGER[dangerOf(n)] + '! Squawk!', false, 30);
      } else if (n.kind === 'boss' && d < 320) {
        // Gristle never chases: you pick the moment by sailing into him.
        parrot('boss', 'Red trim! That’s Gristle! ' + DANGER[dangerOf(n)] + '! Sail into him when you’re ready. Squawk!', false, 90);
      }
      if (!chase && n.chase) n.path = null;
      n.chase = chase;
      if (chase) { tx = state.x; ty = state.y; sp = n.kind === 'customs' ? 84 : 80 + 6 * n.tier; }
      else {
        if (!n.path) {
          var to = n.route[(n.leg + 1) % n.route.length];
          n.path = E.findPath(m, n.x, n.y, to[0], to[1]) || [[n.x, n.y]];
          n.pi = 0;
        }
        var p = n.path[n.pi];
        if (Math.hypot(p[0] - n.x, p[1] - n.y) < 12) {
          n.pi++;
          if (n.pi >= n.path.length) { n.leg = (n.leg + 1) % n.route.length; n.path = null; }
          continue;
        }
        tx = p[0]; ty = p[1];
      }
      var dx = tx - n.x, dy = ty - n.y, L = Math.hypot(dx, dy) || 1, vx = dx / L * sp, vy = dy / L * sp;
      var nx = n.x + vx * dt, ny = n.y + vy * dt;
      if (!E.shipBlocked(m, nx, n.y)) n.x = nx;
      if (!E.shipBlocked(m, n.x, ny)) n.y = ny;
      n.angle = turnToward(n.angle, Math.atan2(vy, vx), dt * 4);
      if (n.kind === 'merchant' && !n.looted && d < 200 && !state.flags.p_merchant) parrot('merchant', 'Fat merchantman! Sail into her to board! Pillage! Squawk!', true);
      if (d < 26 && grace <= 0 && n.cool <= 0 && !(n.kind === 'merchant' && n.looted) && !(raider && (safe || weak || calmed))) { encounter(n); return; }
    }
  }

  /* ---------- the context button: dock or dig ---------- */
  function updateAction() {
    var a = null, mid = state.map;
    if (justLeft && (PORTS[justLeft].map !== mid || Math.hypot(PORTS[justLeft].dock[0] - state.x, PORTS[justLeft].dock[1] - state.y) > 75)) justLeft = null;
    for (var pid in PORTS) {
      var p = PORTS[pid];
      if (pid !== justLeft && p.map === mid && Math.hypot(p.dock[0] - state.x, p.dock[1] - state.y) < 55) { a = {kind: 'dock', id: pid, label: '⚓ Dock at ' + p.name}; break; }
    }
    if (!a) {
      for (var sid in STASHES) {
        var s = STASHES[sid];
        if (s.map !== mid || state.found[sid]) continue;
        var d = Math.hypot(s.at[0] - state.x, s.at[1] - state.y);
        if (d > 70) continue;
        if (s.needs && pieces() < s.needs) { parrot('haze', 'Something’s buried under that haze, Cap’n, but we need the whole map! Squawk!', false, 60); continue; }
        if (state.hints[sid] || s.needs) a = {kind: 'dig', id: sid, label: '⛏️ Dig for treasure'};
        else if (d < 48) { a = {kind: 'dig', id: sid, label: '⛏️ Dig for treasure'}; parrot('shiny', 'Something shiny on that beach! Squawk!', false, 30); }
      }
    }
    var tm = state.tmap;
    if (!a && tm && tm.map === mid && Math.hypot(tm.at[0] - state.x, tm.at[1] - state.y) < 70) a = {kind: 'dig', id: 'tmap', label: '⛏️ Dig for treasure'};
    action = a;
    var key = a ? a.kind + a.id : '';
    if (key !== actionKey) {
      actionKey = key;
      var b = $('action');
      if (a) { b.textContent = a.label; b.hidden = false; announce(a.label.replace(/^\S+\s/, '') + ': press Enter, or use the button.'); }
      else b.hidden = true;
    }
  }
  function doAction() {
    if (!action) return;
    if (action.kind === 'dock') dock(action.id);
    else if (action.kind === 'dig') tryDig(action.id);
  }

  function seenSea(mid) {
    return mid === state.map || !!state.flags['seen_' + mid] || Object.keys(PORTS).some(function (p) { return PORTS[p].map === mid && state.visited[p]; });
  }
  // A treasure map points at a small island in a sea you know. One map at a time keeps it simple.
  function giveMap() {
    if (state.tmap) return null;
    var mid = Math.random() < 0.6 ? state.map : pick(Object.keys(MAPS).filter(seenSea)), m = enterMap(mid), spots = [];
    m.lands.forEach(function (L) {
      if (!L.blob || L.haze || Math.max(L.blob[2], L.blob[3]) > 32) return;
      var at = [L.blob[0], L.blob[1]];
      if (nearPort(at[0], at[1], 150, mid)) return;
      if (Object.keys(STASHES).some(function (k) { var s = STASHES[k]; return s.map === mid && Math.hypot(s.at[0] - at[0], s.at[1] - at[1]) < 60; })) return;
      var f = E.nearestFreePoint(m, at[0], at[1]);
      if (Math.hypot(f[0] - at[0], f[1] - at[1]) > 55) return;
      spots.push({name: L.name, at: at});
    });
    if (!spots.length) return null;
    var sp = pick(spots);
    state.tmap = {map: mid, at: sp.at, name: sp.name, tier: D.SEA_TIER[mid] || 1};
    reveal(mid, sp.at[0], sp.at[1], 120);
    return '🗺️ It shows treasure buried on ' + sp.name + (mid === state.map ? '' : ', over in ' + MAPS[mid].name) + '. It’s marked on your chart.';
  }
  function digMap() {
    var tm = state.tmap;
    if (!tm) return;
    state.tmap = null;
    state.dug++;
    var gold = Math.round((70 + Math.random() * 60) * tm.tier), got = '';
    state.gold += gold;
    if (Math.random() < 0.45) {
      var g = Math.random() < 0.5 ? 'kraken' : 'mermaid', k = addCargo(g, g === 'kraken' ? 1 : 2);
      if (k) got = ' and ' + baleWord(k) + ' of ' + GOODS[g].name;
    }
    sfx('fanfare');
    track('treasure-map');
    var text = pick(['You dig until your spade goes clunk.', 'Three paces from a rock shaped like a nose: clunk!', 'You dig up two coconuts, a boot and, at last, a chest.']) +
      ' Inside: ' + fmt(gold) + ' doubloons' + got + '.' + gainXp(25 + 25 * tm.tier);
    checkGoals();
    save();
    note('💰 Treasure on ' + tm.name + '!', text);
  }
  function tryDig(sid) {
    if (sid === 'tmap') { digMap(); return; }
    var s = STASHES[sid];
    if (state.found[sid]) return;
    if (s.needs && pieces() < s.needs) {
      note('🌫️ A strange haze', 'A thick, sweet-smelling haze hangs over this cay. You poke around, but without the whole map you could dig here for a year. ' + D.PARROT + ' sneezes.\n\nMap pieces found: ' + pieces() + ' of 3.');
      return;
    }
    state.found[sid] = 1;
    state.gold += s.gold;
    var lost = [];
    for (var g in s.loot) {
      var n = addCargo(g, s.loot[g]);
      if (n < s.loot[g]) lost.push(baleWord(s.loot[g] - n) + ' of ' + GOODS[g].name);
    }
    var text = s.text + gainXp(sid === 'emerald' ? 400 : s.piece ? 100 : 80);
    if (lost.length) text += '\n\nThere’s no room in your hold for ' + andList(lost) + ', so you leave it for the goats.';
    if (s.piece && pieces() === 3) {
      text += '\n\nThe three pieces fit together. In the middle, circled twice: Smoke Cay, out in the open sea north of the Spanish Main. It’s on your chart now.';
      reveal('main', STASHES.emerald.at[0], STASHES.emerald.at[1], 150);
    }
    sfx('fanfare');
    track(sid === 'emerald' ? 'emerald-bale' : 'map-piece');
    var extra = null, title = '🗺️ Map piece ' + pieces() + ' of 3';
    if (sid === 'emerald') {
      title = '💚 You found the Emerald Bale!';
      extra = el('p', {class: 'win'}, 'You are now a Legend of the Reefer. Day ' + day() + ', ' + fmt(state.gold) + ' doubloons, ' + state.pillaged + ' ' + plural(state.pillaged, 'ship') + ' pillaged, ' + Object.keys(state.collected).length + ' of ' + ORDER.length + ' strains collected, level ' + level() + '. The sea is still yours: keep sailing as long as you like.');
    }
    checkGoals();
    save();
    note(title, text, extra);
  }

  /* ---------- run-ins at sea ---------- */
  // Takes about frac of the hold, a bale at a time from the biggest stacks, so a mixed hold isn't wiped out.
  function confiscate(frac) {
    var want = cargoCount() ? Math.max(1, Math.round(cargoCount() * frac)) : 0, total = 0;
    while (total < want) {
      var big = null;
      for (var g in state.cargo) if (state.cargo[g] > 0 && (!big || state.cargo[g] > state.cargo[big])) big = g;
      if (!big) break;
      total += takeCargo(big, 1);
    }
    return total;
  }
  function encounter(n) {
    ship.vx *= 0.2; ship.vy *= 0.2;
    keys = {};
    sfx('boom');
    if (n.kind === 'customs') customs(n);
    else if (n.kind === 'merchant') merchant(n);
    else if (n.kind === 'boss') gristle(n);
    else fight(n);
  }
  function gristle(n) {
    showEncounter('💀 ' + D.BOSS.captain, D.BOSS.intro, [
      {label: '⚔️ Fight him! (' + DANGER[dangerOf(n)].toLowerCase() + ')', next: function () { fight(n); }},
      {label: '⛵ Not today', fn: function () { return 'You come about before ' + n.name + ' can run out her guns. ' + D.BOSS.captain + ' jeers at you across the water. He’ll be here when you’re ready.'; }}
    ], function () { n.cool = 20; grace = 3; });
  }
  // How far away Customs can smell your cargo, as a share of the usual distance.
  function noseFactor() { var b = boost(); return (state.up.lavender ? 0.55 : 1) * (state.flags.vicar ? 0.7 : 1) * ((b && b.nose) || 1); }
  // The bale you'd burn to cover an escape: the cheapest one aboard.
  function burnPick() {
    var held = Object.keys(state.cargo).filter(function (g) { return state.cargo[g] > 0; });
    held.sort(function (a, b) { return GOODS[a].base - GOODS[b].base; });
    return held[0] || null;
  }
  var BURN_P = 0.5;
  function customs(n, after, lead) {
    // A cutter that has had its word with you leaves you alone for a good while.
    var done = function () { n.cool = 60; grace = 3; if (after) after(); };
    if (!cargoCount()) {
      showEncounter('🔵 Crown Customs', n.name + ' of the Crown Customs pulls alongside, sniffs the air and peers into your empty hold. “Nothing aboard but a parrot? Carry on, Captain.”', [{label: 'Carry on'}], done);
      return;
    }
    var st = stats(), vicar = state.flags.vicar ? 1 : 0, bg = burnPick();
    var bribe = Math.max(15, Math.round(cargoValue() * 0.18 * (1 - 0.1 * st.charm)));
    // Each way out leans on a different part of your ship and captain, so how you build your ship shows here.
    var runP = Math.min(0.95, 0.5 + 0.1 * st.sails + 0.07 * st.sail + 0.1 * vicar);
    var shotP = Math.min(0.95, 0.2 + 0.13 * st.cannons + 0.07 * st.fight);
    var talkP = Math.min(0.95, 0.35 + 0.1 * st.charm + 0.3 * vicar);
    var hint = 'Your odds come from your ship and skills: sails and Sailing for running, cannons and Fighting for a warning shot, Charm for talking. ' + edgeHint();
    showEncounter('🔵 Crown Customs!', lead || n.name + ' of the Crown Customs blocks your way. “Inspection! What is that smell? Is that… citrus?”', [
      {label: '🪙 Pay a “paperwork fee” of ' + fmt(bribe) + ' doubloons', disabled: state.gold < bribe, fn: function () {
        state.gold -= bribe; sfx('coin');
        return pick([n.name + ' pockets the fee, stamps a form in triplicate and wishes you a pleasant voyage.',
          'The fee vanishes into a very large hat. “Everything appears to be in order,” says ' + n.name + ', not looking at anything.']);
      }},
      {label: '⛵ Run for it (' + pct(runP) + ')', fn: function () {
        if (roll(runP)) return 'You crowd on every scrap of sail and leave the cutter wallowing in your wake. Somewhere behind you, a whistle is blown very angrily.' + gainXp(10);
        var lost = confiscate(1 / 3); sfx('bad');
        return 'They catch you before you clear the reef. ' + n.name + ' confiscates ' + baleWord(lost) + ' “for evidence.” You hear coughing from their ship for the rest of the afternoon.';
      }},
      {label: '💣 Fire a warning shot (' + pct(shotP) + ')', fn: function () {
        if (roll(shotP)) return 'BOOM. The cannonball lands a polite distance from their bow. After a short meeting, the cutter decides it left the kettle on and sails home.' + gainXp(10);
        var lost = confiscate(1 / 3), fine = Math.min(state.gold, Math.round(state.gold * 0.1));
        state.gold -= fine; sfx('bad');
        return 'BOOM. You hit their flagpole. ' + n.name + ' is furious, seizes ' + baleWord(lost) + ' and fines you ' + fmt(fine) + ' doubloons for damage to Crown property.';
      }},
      {label: '🗣️ Ask about their day (' + pct(talkP) + ')', fn: function () {
        if (roll(talkP)) return pick(['“Rough day?” you ask. ' + n.name + ' talks for forty minutes about a stapler. Everyone forgets about the inspection.',
          'You compliment their hat. They blush, wave you through and ask where you got your parrot.',
          'You explain it’s all for a botanist in Cartagena. Technically true. They let you go with a warning and a pamphlet.']) + gainXp(10);
        var lost = confiscate(0.25); sfx('bad');
        return n.name + ' is not interested in your thoughts on the weather and confiscates ' + baleWord(lost) + '.';
      }},
      {label: '🔥 Burn a bale of ' + GOODS[bg].name + ' (' + pct(BURN_P) + ')', next: function () {
        takeCargo(bg, 1);
        if (roll(BURN_P)) {
          showEncounter('🔵 Crown Customs', 'You set a bale of ' + GOODS[bg].name + ' smouldering and fan the smoke at the cutter. ' + cap(n.name) + ' breathes in, giggles at a seagull and wanders off to find a snack. Nobody remembers why they stopped you.' + gainXp(10), [], done);
          return;
        }
        sfx('bad');
        customs(n, after, 'You set a bale of ' + GOODS[bg].name + ' smouldering, but the wind shifts and blows the smoke straight back over your own deck. Your crew has the giggles. ' + n.name + ' does not. “Now then. About that inspection.”');
      }}
    ], done, hint);
  }
  function merchant(n) {
    var dz = dangerOf(n);
    showEncounter('🟤 A fat merchantman!', cap(n.name) + ' wallows alongside, low in the water. Her crew looks nervous. Her cargo smells wonderful.', [
      {label: '⚔️ Attack her! (' + DANGER[dz].toLowerCase() + ')', next: function () { fight(n); }},
      {label: '👋 Wave politely', fn: function () {
        if (Math.random() < 0.25 && space() > 0) { var g = pick(D.COMMON); addCargo(g, 1); return 'The merchants wave back. Touched, they toss you a bale of ' + GOODS[g].name + ' out of pure pity.'; }
        return 'The merchants wave back. Everyone feels good about it. Nothing else happens.';
      }},
      {label: '⛵ Leave her be', fn: function () { return 'You let ' + n.name + ' waddle on. The sea is big enough for everyone.'; }}
    ], function () { if (!n.looted) n.cool = 12; grace = 3; });
  }

  /* ---------- battles: a few rounds of broadsides, boarding or running ---------- */
  function foeName(n) { return n.kind === 'merchant' ? cap(n.name) : n.captain; }
  function toll(n) { return clamp(Math.round(state.gold * 0.08), 25 * n.tier, 200 * n.tier); }
  function fight(n, after) {
    var B = {n: n, en: E.foe(n.kind, n.tier), round: 0, after: after}, intro;
    B.eh = B.en.hull;
    if (n.kind === 'boss') intro = D.BOSS.captain + ' runs out every gun on ' + n.name + ' and laughs like a broken accordion.';
    else if (n.kind === 'pirate') intro = pick(['Black sails off the bow! ' + n.captain + ' of ' + n.name + ' runs out the guns and grins with every one of their teeth.',
      cap(n.name) + ' swings alongside, flying the skull and crossed spatulas. ' + n.captain + ' shouts: “Your cargo or your dignity!”',
      'A pirate sloop cuts across your path. ' + n.captain + ' of ' + n.name + ' raises a cutlass and a very loud voice.']);
    else intro = 'You run out your guns. On ' + n.name + ', somebody drops a teapot.';
    if (n.kind !== 'merchant') track(n.kind === 'boss' ? 'meet-gristle' : 'pirate-battle');
    renderFight(B, intro);
  }
  function bar(icon, label, now, max, cls) {
    var row = el('div', {class: 'bar-row'}), lab = el('span', {class: 'bar-label'});
    lab.appendChild(el('span', {'aria-hidden': 'true'}, icon + ' '));
    lab.appendChild(document.createTextNode(label + ': ' + Math.max(0, now) + ' of ' + max));
    row.appendChild(lab);
    var track = el('span', {class: 'bar ' + cls, 'aria-hidden': 'true'}), fill = el('span');
    fill.style.width = clamp(now / max * 100, 0, 100).toFixed(0) + '%';
    track.appendChild(fill);
    row.appendChild(track);
    return row;
  }
  function hullBars(B) {
    var w = el('div', {class: 'bars'});
    w.appendChild(bar('🛡️', 'Your hull', state.hull, hullMax(), 'mine'));
    w.appendChild(bar('☠️', B.n.kind === 'merchant' ? 'Her hull' : 'Their hull', B.eh, B.en.hull, 'theirs'));
    return w;
  }
  function renderFight(B, text) {
    var body = $('enc-body'), st = stats(), en = B.en, n = B.n;
    $('enc-title').textContent = n.kind === 'merchant' ? '⚔️ Attacking ' + n.name : (n.kind === 'boss' ? '💀 ' : '🏴‍☠️ ') + n.captain + ', ' + n.name;
    body.textContent = '';
    body.appendChild(el('p', {id: 'enc-text'}, text));
    body.appendChild(hullBars(B));
    body.appendChild(el('p', {class: 'hint'}, '🦜 ' + D.PARROT + ' sizes them up: ' + DANGER[E.danger(st, state.hull, en, B.eh)].toLowerCase() + '. Every broadside that lands raises your boarding odds.'));
    var eh = edgeHint();
    if (eh) body.appendChild(el('p', {class: 'hint'}, eh));
    var list = el('div', {class: 'choices'}), bp = E.boardChance(st, en, B.eh), fp = E.fleeChance(st, en), bg = burnPick();
    var opts = [
      {label: '💣 Fire a broadside (' + Math.max(1, Math.round(st.fire * 0.85)) + ' to ' + Math.max(1, Math.round(st.fire * 1.15)) + ' damage)', act: 'fire'},
      {label: '⚔️ Board ' + (n.kind === 'merchant' ? 'her' : 'them') + ' (' + pct(bp) + ')', act: 'board'},
      {label: '⛵ Run for it (' + pct(fp) + ')', act: 'run'}
    ];
    if (n.kind === 'pirate' && bg) opts.push({label: '🔥 Burn a bale of ' + GOODS[bg].name + ' (' + pct(BURN_P) + ')', act: 'burn'});
    if (B.round === 0 && n.kind === 'pirate') opts.push({label: '🪙 Pay them to leave you alone (' + fmt(toll(n)) + ' doubloons)', act: 'pay', disabled: state.gold < toll(n)});
    if (B.round === 0 && n.kind === 'merchant') opts.push({label: '🏳️ Let her go after all', act: 'leave'});
    opts.forEach(function (o) {
      var b = el('button', {type: 'button', class: 'choice'}, o.label);
      if (o.disabled) b.disabled = true;
      b.addEventListener('click', function () { fightRound(B, o.act); });
      list.appendChild(b);
    });
    body.appendChild(list);
    openDialog($('dlg-encounter'), list.querySelector('button:not([disabled])'));
  }
  function fightRound(B, act) {
    var st = stats(), en = B.en, n = B.n, txt;
    B.round++;
    if (act === 'leave') { n.cool = 12; endFight(B, 'You think better of it and let ' + n.name + ' waddle on.'); return; }
    if (act === 'pay') {
      var cost = toll(n);
      state.gold -= cost; sfx('coin'); n.cool = 60;
      endFight(B, n.captain + ' counts the ' + fmt(cost) + ' doubloons, bites one, and waves you on your way. “Pleasure doing business.”');
      return;
    }
    if (act === 'burn') {
      var bg = burnPick();
      if (bg) {
        takeCargo(bg, 1);
        if (roll(BURN_P)) {
          n.cool = 60;
          endFight(B, 'You set a bale of ' + GOODS[bg].name + ' smouldering and let the breeze carry it over. On ' + n.name + ', the shouting turns to giggling. ' + n.captain + ' forgets what they were angry about and wanders off to look for snacks.' + gainXp(10));
          return;
        }
        txt = 'You set a bale of ' + GOODS[bg].name + ' smouldering, but the smoke drifts the wrong way.';
      } else txt = 'You have nothing left to burn.';
    } else if (act === 'run') {
      if (roll(E.fleeChance(st, en))) {
        n.cool = 45;
        endFight(B, pick(['You crowd on every scrap of sail and leave them wallowing in your wake.', 'You duck behind a reef they don’t dare cross. By the time they find a way round, you’re gone.',
          'A lucky gust fills your sails. Their curses fade behind you.']));
        return;
      }
      txt = 'You try to slip away, but ' + foeName(n) + ' cuts you off.';
    } else if (act === 'board') {
      if (roll(E.boardChance(st, en, B.eh))) { win(B, 'board'); return; }
      txt = 'Your boarders swing across and get swatted straight back into the sea.';
    } else {
      var dmg = E.hit(st.fire, Math.random());
      B.eh = Math.max(0, B.eh - dmg);
      sfx('boom');
      txt = 'BOOM! Your broadside hits for ' + dmg + '.';
      if (B.eh <= 0) { win(B, 'sink'); return; }
      if (n.kind === 'merchant' && B.eh <= en.hull * 0.35) { win(B, 'strike'); return; }
    }
    var back = E.hit(en.fire * (act === 'board' ? 1.25 : 1), Math.random());
    state.hull = Math.max(0, state.hull - back);
    txt += ' ' + (n.kind === 'merchant' ? 'Her crew fires back' : 'They fire back') + ' for ' + back + '.';
    if (state.hull <= 0) { lose(B, txt); return; }
    renderFight(B, txt);
  }
  function win(B, how) {
    var n = B.n, en = B.en, st = stats(), haul = {}, got = [], left = 0, gold, xp, count = 0, total = 0;
    if (n.kind === 'boss') { gold = D.BOSS.gold; haul = Object.assign({}, D.BOSS.loot); xp = 600; }
    else if (n.kind === 'merchant') {
      gold = Math.round((30 + Math.random() * 40) * en.tier);
      count = 3 + Math.floor(Math.random() * 4) + 2 * st.crew;
      if (Math.random() < 0.35) haul.kraken = Math.random() < 0.3 ? 2 : 1;
      xp = 12 + 10 * en.tier;
    } else {
      gold = Math.round((60 + Math.random() * 70) * en.tier);
      count = 2 + Math.floor(Math.random() * 3) + st.crew;
      if (Math.random() < 0.3) haul[Math.random() < 0.5 ? 'kraken' : 'mermaid'] = 1;
      xp = 30 + 30 * en.tier;
    }
    for (var h in haul) total += haul[h];
    while (total < count) { var g = pick(D.COMMON); haul[g] = (haul[g] || 0) + 1; total++; }
    state.gold += gold;
    Object.keys(haul).forEach(function (g) {
      var k = addCargo(g, haul[g]);
      if (k) got.push(baleWord(k) + ' of ' + GOODS[g].name);
      left += haul[g] - k;
    });
    var txt = how === 'board' ? 'With a mighty “Arrr!” your crew swings aboard. ' + (n.kind === 'merchant' ? 'The merchants surrender at once; they’re paid by the hour.' : foeName(n) + ' throws down their cutlass.')
      : how === 'strike' ? cap(n.name) + ' strikes her colours before you can fire again.'
      : 'Your broadside smashes ' + n.name + '’s mainmast. ' + foeName(n) + ' surrenders.';
    txt += ' You take ' + fmt(gold) + ' doubloons' + (got.length ? ' and ' + andList(got) : '') + '.' + (left ? ' Your hold can’t fit the other ' + baleWord(left) + '.' : '');
    if (n.kind === 'pirate' && !state.tmap && Math.random() < 0.35) { var map = giveMap(); if (map) txt += ' In the captain’s cabin you find a treasure map. ' + map; }
    if (n.kind === 'boss') txt += ' ' + D.BOSS.captain + ' is marooned on a sandbar with a hat and a coconut. Every tavern from here to Tortuga will be singing about you.';
    txt += gainXp(xp);
    if (n.kind === 'merchant') { n.looted = true; n.cool = 60; state.pillaged++; if (state.pillaged === 1) track('first-pillage'); }
    else {
      state.sunk++;
      if (n.kind === 'boss') { state.flags.boss = 1; npcs[state.map].splice(npcs[state.map].indexOf(n), 1); track('beat-gristle'); }
      else { n.gone = true; n.cool = 90; if (state.sunk === 1) track('first-pirate'); }
    }
    sfx('fanfare');
    endFight(B, txt);
  }
  function lose(B, txt) {
    var n = B.n;
    state.hull = Math.max(1, Math.ceil(hullMax() * 0.25));
    sfx('bad');
    if (n.kind === 'merchant') {
      n.cool = 30;
      txt += ' That’s enough for your poor ship. Her crew chases you off with mops and a strongly worded letter.';
    } else {
      var lost = confiscate(1 / 3), fine = Math.min(Math.round(state.gold * 0.1), 400);
      state.gold -= fine;
      n.cool = 90;
      txt += ' Your ship is beaten. ' + foeName(n) + ' takes ' + (lost ? baleWord(lost) : 'nothing from your empty hold') + (fine ? ' and ' + fmt(fine) + ' doubloons' : '') + ', then sails off laughing.';
    }
    txt += ' Your crew patches the worst holes. Your ship, your upgrades and your renown are all still yours: get to a port for repairs.';
    endFight(B, txt);
  }
  function endFight(B, txt) {
    var body = $('enc-body'), n = B.n, c = el('button', {type: 'button', class: 'primary', 'aria-describedby': 'enc-text'}, 'Continue');
    body.textContent = '';
    body.appendChild(el('p', {id: 'enc-text'}, txt));
    body.appendChild(hullBars(B));
    c.addEventListener('click', function () {
      closeDialog('dlg-encounter');
      grace = 3;
      if (n.kind === 'merchant' && !n.looted) n.cool = Math.max(n.cool, 12);
      checkGoals();
      save();
      if (B.after) B.after();
    });
    body.appendChild(c);
    c.focus();
  }
  // opts: the choices. With no choices it just shows the text and a Continue button.
  function showEncounter(title, text, opts, onDone, hint) {
    var dlg = $('dlg-encounter'), body = $('enc-body');
    $('enc-title').textContent = title;
    body.textContent = '';
    var p = el('p', {id: 'enc-text'}, text.replace(/\s+/g, ' ').trim()), list = el('div', {class: 'choices'});
    body.appendChild(p);
    hint = (hint || '').trim();
    if (hint && opts.length) body.appendChild(el('p', {class: 'hint'}, hint));
    body.appendChild(list);
    function finish() { closeDialog(dlg); if (onDone) onDone(); checkGoals(); save(); }
    if (!opts.length) {
      var go = el('button', {type: 'button', class: 'primary', 'aria-describedby': 'enc-text'}, 'Continue');
      go.addEventListener('click', finish);
      list.appendChild(go);
      openDialog(dlg, go);
      return;
    }
    opts.forEach(function (o) {
      var b = el('button', {type: 'button', class: 'choice'}, o.label);
      if (o.disabled) { b.disabled = true; b.setAttribute('aria-describedby', 'enc-text'); }
      b.addEventListener('click', function () {
        if (o.next) { o.next(); return; }
        var res = o.fn ? o.fn() : null;
        if (!res) { finish(); return; }
        p.textContent = res.replace(/\s+/g, ' ').trim();
        var hn = body.querySelector('.hint');
        if (hn) hn.remove();
        list.textContent = '';
        var c = el('button', {type: 'button', class: 'primary', 'aria-describedby': 'enc-text'}, 'Continue');
        c.addEventListener('click', finish);
        list.appendChild(c);
        c.focus();
      });
      list.appendChild(b);
    });
    openDialog(dlg, list.querySelector('button:not([disabled])'));
  }

  /* ---------- surprises at sea and in port (written in events.js) ---------- */
  function pickEvent(list) {
    var tr = tier(), ok = list.filter(function (e) {
      return evRecent.indexOf(e.id) < 0 && !(e.minTier && tr < e.minTier) && !(e.needsNoMap && state.tmap) &&
        !(e.needsDamage && state.hull >= hullMax()) && !(e.once && state.flags['ev_' + e.id]);
    });
    if (!ok.length) return null;
    var e = pick(ok);
    evRecent.push(e.id);
    if (evRecent.length > 5) evRecent.shift();
    if (e.once) state.flags['ev_' + e.id] = 1;
    return e;
  }
  function evApi() {
    function common(list) { var c = list.filter(function (g) { return !GOODS[g].rare; }); return c.length ? c : list; }
    function tally(o) { var out = []; for (var g in o) out.push(baleWord(o[g]) + ' of ' + GOODS[g].name); return andList(out); }
    return {
      tier: tier(), st: stats(), parrot: D.PARROT, odds: pct, check: roll, xp: gainXp, give: addCargo, cargo: cargoCount, space: space, giveMap: giveMap,
      // check() is a shown check: it rolls the same percentage odds() prints. chance() is for hidden surprises.
      chance: function (p) { return Math.random() < p; },
      rand: function (lo, hi) { return lo + Math.floor(Math.random() * (hi - lo + 1)); },
      goldNow: function () { return state.gold; },
      hasGold: function (n) { return state.gold >= n; },
      gold: function (n) { var was = state.gold; state.gold = Math.max(0, Math.round(state.gold + n)); if (n > 0) sfx('coin'); return state.gold - was; },
      money: function (n) { return fmt(n) + ' ' + plural(n, 'doubloon'); },
      bales: function (n, g) { return baleWord(n) + ' of ' + GOODS[g].name; },
      // Surprises can dent the hull but never sink you.
      hurtText: function (n) { var k = hurt(n, Math.ceil(hullMax() * 0.2)); if (k) sfx('bad'); return k ? '🛡️ −' + k + ' hull.' : ''; },
      heal: function (n) { var k = heal(n); return k ? '🛡️ +' + k + ' hull.' : ''; },
      giveRandom: function (n) {
        var got = {};
        for (var i = 0; i < n; i++) { var g = pick(D.COMMON); if (addCargo(g, 1)) got[g] = (got[g] || 0) + 1; }
        return tally(got);
      },
      loseRandom: function (n) {
        var lost = {};
        for (var i = 0; i < n; i++) {
          var held = Object.keys(state.cargo);
          if (!held.length) break;
          var g = pick(common(held));
          takeCargo(g, 1);
          lost[g] = (lost[g] || 0) + 1;
        }
        return tally(lost);
      },
      sellRandom: function (n, mult, lead) {
        var sold = 0, got = 0, xp = 0;
        for (var i = 0; i < n; i++) {
          var held = Object.keys(state.cargo);
          if (!held.length) break;
          var g = pick(common(held)), r = sellGoods(g, 1, Math.round(GOODS[g].base * mult));
          if (r) { sold++; got += r.gold; xp += r.xp; }
        }
        if (!sold) return 'You have nothing left to sell.';
        sfx('coin');
        return lead + ' You sell ' + baleWord(sold) + ' for ' + fmt(got) + ' doubloons.' + gainXp(xp + 5);
      },
      skillPoint: function () { state.pts++; levelUp = levelUp || -1; return '⭐ You gain a skill point. Spend it from your captain’s log.'; }
    };
  }
  function runEvent(e, after) {
    ship.vx *= 0.3; ship.vy *= 0.3;
    keys = {};
    var opts = e.opts(evApi()), odds = opts.some(function (o) { return /% chance/.test(o.label); });
    showEncounter(e.title, e.text, opts, function () { grace = 2; if (after) after(); }, odds ? edgeHint() : '');
  }

  /* ---------- ports ---------- */
  var portTab = 'market', talkNode = 'start';
  function portTabs(pid) {
    var p = PORTS[pid], tabs = [['market', '🛒 Market'], ['tavern', '🍺 Tavern']];
    if (p.yard) tabs.push(['yard', '🔨 Shipwright']);
    tabs.push(['routes', '🧭 Routes']);
    return tabs;
  }
  function openPort(pid, tab) {
    var p = PORTS[pid];
    $('port-title').textContent = '⚓ ' + p.name;
    $('port-blurb').textContent = p.blurb;
    talkNode = 'start';
    var tl = $('port-tabs');
    tl.textContent = '';
    portTabs(pid).forEach(function (tb) {
      var b = el('button', {type: 'button', role: 'tab', id: 'tab-' + tb[0], 'aria-controls': 'port-panel'}, tb[1]);
      b.dataset.tab = tb[0];
      b.addEventListener('click', function () { showTab(tb[0], true); });
      tl.appendChild(b);
    });
    showTab(tab || 'market', false);
    openDialog($('dlg-port'), $('tab-' + portTab));
  }
  function showTab(name, userClick) {
    portTab = name;
    Array.prototype.forEach.call($('port-tabs').children, function (b) {
      var on = b.dataset.tab === name;
      b.setAttribute('aria-selected', on ? 'true' : 'false');
      b.tabIndex = on ? 0 : -1;
    });
    $('port-panel').setAttribute('aria-labelledby', 'tab-' + name);
    renderPanel();
    if (userClick) $('tab-' + name).focus();
  }
  function renderPanel(keepKey) {
    var pid = state.docked, panel = $('port-panel');
    if (!pid) return;
    panel.textContent = '';
    $('port-status').textContent = portStatus();
    if (state.hull < hullMax()) panel.appendChild(repairRow());
    if (portTab === 'market') renderMarket(pid, panel);
    else if (portTab === 'tavern') renderTavern(pid, panel);
    else if (portTab === 'routes') renderRoutes(pid, panel);
    else renderYard(panel);
    if (keepKey) {
      var again = panel.querySelector('[data-key="' + keepKey + '"]');
      if (again && !again.disabled) again.focus();
      else { var h = panel.querySelector('h3'); if (h) { h.tabIndex = -1; h.focus(); } }
    }
  }
  function portStatus() {
    return '🪙 ' + fmt(state.gold) + ' doubloons · 📦 ' + cargoCount() + ' of ' + capacity() + ' bales · 🛡️ Hull ' + state.hull + ' of ' + hullMax() + ' · ⭐ Level ' + level();
  }
  function repairRow() {
    var need = hullMax() - state.hull, afford = Math.min(need, Math.floor(state.gold / 2)), box = el('div', {class: 'repair'});
    box.appendChild(el('p', null, '🛡️ Your hull is at ' + state.hull + ' of ' + hullMax() + '. Repairs cost 2 doubloons a point.'));
    var b = el('button', {type: 'button', class: 'secondary', 'data-key': 'repair'},
      afford >= need ? '🔧 Repair it all for ' + fmt(need * 2) + ' doubloons' : afford > 0 ? '🔧 Repair ' + afford + ' points for ' + fmt(afford * 2) + ' doubloons' : '🔧 You can’t afford repairs yet');
    b.disabled = afford <= 0;
    b.addEventListener('click', function () {
      var k = Math.min(hullMax() - state.hull, Math.floor(state.gold / 2));
      if (k <= 0) return;
      state.gold -= k * 2; state.hull += k;
      sfx('coin');
      say('🔧 The shipwrights fix ' + k + ' hull points for ' + fmt(k * 2) + ' doubloons.');
      save();
      renderPanel('repair');
    });
    box.appendChild(b);
    return box;
  }
  // What you pay and get right now: your Charm (boost included) and any selling boost.
  function buyAt(pid, g) { return E.buyPrice(pid, g, day(), stats().charm); }
  function sellAt(pid, g) { var b = boost(), p = E.sellPrice(pid, g, day(), stats().charm); return b && b.sell ? Math.round(p * (1 + b.sell)) : p; }
  // The ledger keeps the plain prices (no boosts) from the last time you stood in each market.
  function notePrices(pid) {
    var d = day(), ch = state.skill.charm, rec = {d: d, b: {}, s: {}};
    ORDER.forEach(function (g) { var b = E.buyPrice(pid, g, d, ch); if (b) rec.b[g] = b; rec.s[g] = E.sellPrice(pid, g, d, ch); });
    state.seen[pid] = rec;
  }
  function bestSeen(g, except) {
    var best = null;
    for (var pid in state.seen) {
      if (pid === except || !PORTS[pid]) continue;
      var r = state.seen[pid], v = r.s && r.s[g];
      if (v && (!best || v > best.price)) best = {pid: pid, price: v, d: r.d};
    }
    return best;
  }
  function trade(pid, g, n, buying) {
    var price = buying ? buyAt(pid, g) : sellAt(pid, g);
    if (buying) {
      n = Math.min(n, space(), Math.floor(state.gold / price));
      if (n <= 0) return;
      state.gold -= n * price;
      addCargo(g, n);
      state.basis[g] = (state.basis[g] || 0) + n * price;
      say('Bought ' + baleWord(n) + ' of ' + GOODS[g].name + ' for ' + fmt(n * price) + ' doubloons.');
    } else {
      var r = sellGoods(g, n, price);
      if (!r) return;
      say('Sold ' + baleWord(r.n) + ' of ' + GOODS[g].name + ' for ' + fmt(r.gold) + ' doubloons.' + gainXp(r.xp));
    }
    sfx('coin');
    checkGoals();
    save();
  }
  function renderMarket(pid, panel) {
    var p = PORTS[pid];
    notePrices(pid);
    var list = ORDER.filter(function (g) { return p.sells.indexOf(g) >= 0 || state.cargo[g]; });
    list.sort(function (a, b) { return (GOODS[b].home === pid) - (GOODS[a].home === pid); });
    var held = Object.keys(state.cargo), total = 0;
    held.forEach(function (g) { total += state.cargo[g] * sellAt(pid, g); });
    var intro = el('p', {class: 'hint'}, 'Prices change every day. Each port grows one strain cheaply and pays more for strains from elsewhere, most of all from another sea. Hash, rosin and biscuits fetch a premium where they’re wanted.');
    panel.appendChild(intro);
    if (held.length) {
      var all = el('button', {type: 'button', class: 'secondary sellall', 'data-key': 'sellall'}, '💰 Sell the whole hold for ' + fmt(total) + ' doubloons');
      all.addEventListener('click', function () {
        var n = 0, got = 0, xp = 0;
        Object.keys(state.cargo).forEach(function (g) { var r = sellGoods(g, state.cargo[g], sellAt(pid, g)); if (r) { n += r.n; got += r.gold; xp += r.xp; } });
        sfx('coin');
        say('Sold all ' + baleWord(n) + ' for ' + fmt(got) + ' doubloons.' + gainXp(xp));
        checkGoals(); save(); renderPanel('sellall');
      });
      panel.appendChild(all);
    }
    var ul = el('ul', {class: 'goods'});
    list.forEach(function (g) {
      var G = GOODS[g], bp = buyAt(pid, g), spr = sellAt(pid, g), have = state.cargo[g] || 0, S = SMOKE[g], best = bestSeen(g, pid);
      var li = el('li', {class: 'good'});
      var head = el('div', {class: 'g-head'});
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, G.icon));
      head.appendChild(el('h3', null, G.name));
      if (G.home === pid) head.appendChild(el('span', {class: 'tag'}, G.kind ? 'Made here' : 'Grown here'));
      if (E.wanted(pid, g)) head.appendChild(el('span', {class: 'tag'}, 'Wanted here'));
      li.appendChild(head);
      li.appendChild(el('p', {class: 'g-note'}, G.note));
      if (S) li.appendChild(el('p', {class: 'g-note'}, '🔥 ' + cap(verb(g)) + ' one for ' + S.name + '. ' + S.does));
      if (best && best.price > spr) li.appendChild(el('p', {class: 'g-note'}, '📒 Best price you know of: ' + best.price + ' in ' + PORTS[best.pid].name + ' on day ' + best.d + '.'));
      var pr = el('p', {class: 'g-prices'});
      pr.innerHTML = (bp ? 'Buy for <b>' + bp + '</b>' : 'Not sold here') + ' · Sells for <b>' + spr + '</b> · You have <b>' + have + '</b>';
      li.appendChild(pr);
      var btns = el('div', {class: 'g-btns'});
      function btn(label, aria, key, n, buying, disabled) {
        var b = el('button', {type: 'button', 'aria-label': aria, 'data-key': key}, label);
        b.disabled = !!disabled;
        b.addEventListener('click', function () { trade(pid, g, n, buying); renderPanel(key); });
        btns.appendChild(b);
      }
      if (bp) {
        var maxBuy = Math.min(space(), Math.floor(state.gold / bp));
        btn('Buy 1', 'Buy 1 bale of ' + G.name + ' for ' + bp + ' doubloons', 'b1' + g, 1, true, maxBuy < 1);
        btn('Buy 5', 'Buy 5 bales of ' + G.name + ' for ' + fmt(bp * 5) + ' doubloons', 'b5' + g, 5, true, maxBuy < 5);
        btn('Buy max (' + maxBuy + ')', 'Buy as many bales of ' + G.name + ' as you can: ' + maxBuy, 'bm' + g, maxBuy, true, maxBuy < 1);
      }
      btn('Sell 1', 'Sell 1 bale of ' + G.name + ' for ' + spr + ' doubloons', 's1' + g, 1, false, have < 1);
      btn('Sell all (' + have + ')', 'Sell all ' + have + ' bales of ' + G.name + ' for ' + fmt(spr * have) + ' doubloons', 'sa' + g, have, false, have < 1);
      if (S && have > 0) {
        var sb = el('button', {type: 'button', 'data-key': 'sm' + g, 'aria-label': cap(verb(g)) + ' a bale of ' + G.name + ' for ' + S.name + '. ' + S.does}, '🔥 ' + cap(verb(g)) + ' 1');
        sb.addEventListener('click', function () { smoke(g); renderPanel('sm' + g); });
        btns.appendChild(sb);
      }
      li.appendChild(btns);
      ul.appendChild(li);
    });
    panel.appendChild(ul);
  }

  /* ---------- routes: the trade ledger and quick passage ---------- */
  var voyCache = {}, lookupG = null;
  function legLength(mid, a, b) {
    var m = E.prepareMap(mid), s = E.nearestFreePoint(m, a[0], a[1]), f = E.nearestFreePoint(m, b[0], b[1]), path = E.findPath(m, s[0], s[1], f[0], f[1]);
    if (!path) return null;
    var L = 0, px = s[0], py = s[1];
    path.forEach(function (q) { L += Math.hypot(q[0] - px, q[1] - py); px = q[0]; py = q[1]; });
    return L;
  }
  // The sea route from one port to another: how far, how many days, which seas.
  function voyage(from, to) {
    var key = from + '>' + to;
    if (key in voyCache) return voyCache[key];
    var A = PORTS[from], B = PORTS[to], mid = A.map, at = A.dock, len = 0, seas = [mid], v = null;
    for (var hops = 0; mid !== B.map && hops < 6; hops++) {
      var next = nextSea(mid, B.map), ex = next && MAPS[mid].exits.filter(function (e) { return e.to === next; })[0];
      if (!ex) break;
      var pt = exitPointFrom(ex, at), L = legLength(mid, at, pt);
      if (L === null) break;
      len += L;
      var m2 = E.prepareMap(next), arr = ex.arrive;
      at = [arr[0] === 'x' ? clamp(pt[0], 80, m2.w - 80) : arr[0], arr[1]];
      mid = next; seas.push(mid);
    }
    if (mid === B.map) {
      var L2 = legLength(mid, at, B.dock);
      if (L2 !== null) { len += L2; v = {len: Math.round(len), days: Math.max(1, Math.round(len / 900)), seas: seas}; }
    }
    voyCache[key] = v;
    return v;
  }
  // Whole-number odds of meeting Customs or pirates on a passage. These are exactly the odds rolled.
  function passageRisk(v) {
    var b = boost(), f = clamp(v.days / 2, 0.6, 1.5), top = 1;
    v.seas.forEach(function (s) { top = Math.max(top, D.SEA_TIER[s] || 1); });
    var weak = state.hull < hullMax() * 0.35;
    var c = cargoCount() ? 0.15 * noseFactor() * f : 0;
    var p = (b && b.calm) || weak ? 0 : clamp(0.06 + 0.04 * top - 0.03 * state.up.sails, 0.03, 0.25) * f;
    return {customs: Math.round(c * 100), pirates: Math.round(p * 100), top: top};
  }
  function sailText(days) { return days + (days === 1 ? ' day’s' : ' days’') + ' sail'; }
  function riskText(v) {
    var rk = passageRisk(v);
    return 'On the way: ' + (cargoCount() ? 'Customs ' + rk.customs + '% chance, ' : '') + 'pirates ' + rk.pirates + '% chance.';
  }
  // One turn: the days pass, at most one run-in, then you land.
  function passage(to) {
    var from = state.docked, v = from && to !== from ? voyage(from, to) : null;
    if (!v) return false;
    var risk = passageRisk(v), r = Math.random() * 100;
    leavePort(true, true);
    auto = null; ship.vx = ship.vy = 0; wake = []; keys = {};
    // A passage takes whole days, so the day counter moves by exactly the days shown.
    state.dist += v.days * 900;
    var worn = boostTick(v.days * 900);
    v.seas.forEach(function (s) { state.flags['seen_' + s] = 1; });
    var P = PORTS[to], m = enterMap(P.map), f = E.nearestFreePoint(m, P.dock[0], P.dock[1]);
    state.map = P.map; state.x = f[0]; state.y = f[1];
    justLeft = null;
    snapCamera();
    needRender = true;
    track('passage');
    var lead = '⛵ ' + v.days + ' ' + plural(v.days, 'day') + ' at sea from ' + PORTS[from].name + '. It’s now day ' + day() + '.' + (worn ? ' ' + worn : '');
    var land = function () { dock(to, lead); };
    if (r < risk.customs) {
      sfx('boom');
      customs({kind: 'customs', name: pick(D.CUSTOMS_NAMES), cool: 0}, land);
    } else if (r < risk.customs + risk.pirates) {
      var sea = v.seas.filter(function (s) { return (D.SEA_TIER[s] || 1) === risk.top; }).pop(), n = makePirate(enterMap(sea));
      n.cool = 0;
      sfx('boom');
      fight(n, land);
    } else {
      var ev = Math.random() < 0.25 ? pickEvent(EV.sea) : null;
      if (ev) runEvent(ev, land); else land();
    }
    return true;
  }
  function portGoal(pid) { var p = PORTS[pid]; return {type: 'port', id: pid, map: p.map, x: p.dock[0], y: p.dock[1], label: p.name, icon: '⚓'}; }
  // The best runs you know of: buy where you've seen it cheap, sell where you've seen it dear, ranked by profit a day.
  function bestRuns(limit) {
    var seen = state.seen, ports = Object.keys(seen).filter(function (q) { return PORTS[q]; }), all = [], out = [], used = {};
    ports.forEach(function (a) {
      Object.keys(seen[a].b || {}).forEach(function (g) {
        var bp = seen[a].b[g];
        ports.forEach(function (z) {
          var sp = seen[z].s && seen[z].s[g];
          if (z === a || !(sp > bp)) return;
          var v = voyage(a, z);
          if (v && sp - bp >= Math.max(3, bp * 0.1)) all.push({g: g, from: a, to: z, bp: bp, sp: sp, gain: sp - bp, days: v.days, score: (sp - bp) / v.days});
        });
      });
    });
    all.sort(function (x, y) { return y.score - x.score; });
    all.forEach(function (r) { if (out.length < limit && !used[r.g]) { used[r.g] = 1; out.push(r); } });
    return out;
  }
  function renderLedger(box, here) {
    var seen = state.seen, ports = Object.keys(seen).filter(function (q) { return PORTS[q]; });
    box.appendChild(el('h3', null, '📒 Trade ledger'));
    if (!ports.length) { box.appendChild(el('p', {class: 'hint'}, 'Every market you visit goes in your ledger, so you can plan where to buy and where to sell.')); return; }
    box.appendChild(el('p', {class: 'hint'}, 'Prices from the markets you’ve visited, with the day you saw them. They drift a little every day.'));
    box.appendChild(el('h4', null, 'Best runs you know'));
    var runs = bestRuns(4);
    if (!runs.length) box.appendChild(el('p', null, 'No money-making runs yet. Visit a few more markets.'));
    else {
      var ul = el('ul', {class: 'goods'});
      runs.forEach(function (r, i) {
        var G = GOODS[r.g], li = el('li', {class: 'good'}), p1 = el('p', {class: 'run'}), d1 = seen[r.from].d, d2 = seen[r.to].d;
        p1.appendChild(el('span', {'aria-hidden': 'true'}, G.icon + ' '));
        p1.appendChild(el('b', null, G.name));
        p1.appendChild(document.createTextNode(': buy in ' + PORTS[r.from].name + ' for ' + r.bp + ', sell in ' + PORTS[r.to].name + ' for ' + r.sp + '.'));
        li.appendChild(p1);
        li.appendChild(el('p', {class: 'g-note'}, '+' + r.gain + ' a bale, about ' + sailText(r.days) + ' apart. Seen on day ' + Math.min(d1, d2) + (d1 !== d2 ? ' and day ' + Math.max(d1, d2) : '') + '.'));
        var btns = el('div', {class: 'g-btns'}), b;
        if (here === r.from) {
          b = el('button', {type: 'button', 'data-key': 'run' + i}, '🛒 Buy it in the market');
          b.addEventListener('click', function () { showTab('market', true); });
        } else if (here) {
          var v = voyage(here, r.from);
          b = el('button', {type: 'button', 'data-key': 'run' + i, 'aria-label': 'Quick passage to ' + PORTS[r.from].name + (v ? ', about ' + v.days + ' ' + plural(v.days, 'day') : '')}, '⛵ Quick passage to ' + PORTS[r.from].name);
          b.addEventListener('click', function () { passage(r.from); });
        } else {
          b = el('button', {type: 'button', 'data-key': 'run' + i}, '🧭 Set course for ' + PORTS[r.from].name);
          b.addEventListener('click', function () { closeDialog('dlg-chart'); setCourse(portGoal(r.from)); });
        }
        btns.appendChild(b);
        li.appendChild(btns);
        ul.appendChild(li);
      });
      box.appendChild(ul);
    }
    box.appendChild(el('h4', null, 'Look up a cargo'));
    var id = here ? 'lookup-port' : 'lookup-chart', row = el('p', {class: 'lookup'}), sel = el('select', {id: id}), out = el('ul', {class: 'checks'});
    row.appendChild(el('label', {for: id}, 'Cargo'));
    ORDER.forEach(function (g) { var o = el('option', {value: g}, GOODS[g].name); sel.appendChild(o); });
    var held = Object.keys(state.cargo);
    sel.value = lookupG && GOODS[lookupG] ? lookupG : held[0] || ORDER[0];
    row.appendChild(sel);
    box.appendChild(row);
    function show() {
      var g = sel.value;
      lookupG = g;
      out.textContent = '';
      ports.slice().sort(function (a, b) { return (seen[b].s[g] || 0) - (seen[a].s[g] || 0); }).forEach(function (q) {
        var r = seen[q], li = el('li');
        li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, '⚓'));
        li.appendChild(document.createTextNode(PORTS[q].name + (q === here ? ' (here)' : '') + ': ' + (r.b[g] ? 'sells it for ' + r.b[g] + ', ' : '') + 'pays ' + (r.s[g] || '?') + '. Day ' + r.d + '.'));
        out.appendChild(li);
      });
    }
    sel.addEventListener('change', show);
    show();
    box.appendChild(out);
  }
  function renderRoutes(pid, panel) {
    panel.appendChild(el('p', {class: 'hint'}, 'Pick a port you know and your crew sails straight there. The days pass, prices move, and you might meet Customs, pirates or a surprise on the way.'));
    panel.appendChild(el('h3', null, '🧭 Quick passage'));
    var list = Object.keys(PORTS).filter(function (q) { return q !== pid && portKnown(q); }).map(function (q) { return {pid: q, v: voyage(pid, q)}; })
      .filter(function (o) { return o.v; }).sort(function (a, b) { return a.v.len - b.v.len; });
    if (!list.length) panel.appendChild(el('p', null, 'No other ports on your chart yet. Ask around in the tavern.'));
    var ul = el('ul', {class: 'goods'}), held = Object.keys(state.cargo);
    list.forEach(function (o) {
      var P = PORTS[o.pid], li = el('li', {class: 'good'}), head = el('div', {class: 'g-head'}), seen = state.seen[o.pid];
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, '⚓'));
      head.appendChild(el('h3', null, P.name));
      head.appendChild(el('span', {class: 'tag'}, MAPS[P.map].short));
      li.appendChild(head);
      li.appendChild(el('p', {class: 'g-note'}, 'About ' + sailText(o.v.days) + '. ' + riskText(o.v)));
      if (!seen) li.appendChild(el('p', {class: 'g-note'}, '📒 You haven’t seen this market yet.'));
      else {
        var sells = Object.keys(seen.b).map(function (g) { return GOODS[g].name + ' ' + seen.b[g]; });
        if (sells.length) li.appendChild(el('p', {class: 'g-note'}, '📒 Sells ' + andList(sells) + ' (day ' + seen.d + ').'));
        var bestG = null;
        held.forEach(function (g) { if (seen.s[g] && (!bestG || seen.s[g] > seen.s[bestG])) bestG = g; });
        if (bestG) li.appendChild(el('p', {class: 'g-note'}, '📒 Pays best for your hold: ' + seen.s[bestG] + ' for ' + GOODS[bestG].name + '.'));
      }
      var btns = el('div', {class: 'g-btns'}), b = el('button', {type: 'button', 'data-key': 'go' + o.pid, 'aria-label': 'Quick passage to ' + P.name + ', about ' + o.v.days + ' ' + plural(o.v.days, 'day')}, '⛵ Sail to ' + P.name);
      b.addEventListener('click', function () { passage(o.pid); });
      btns.appendChild(b);
      li.appendChild(btns);
      ul.appendChild(li);
    });
    panel.appendChild(ul);
    renderLedger(panel, pid);
  }

  function cond(c) {
    if (!c) return true;
    var neg = c.charAt(0) === '!';
    if (neg) c = c.slice(1);
    var p = c.split(':'), k = p[0], v = p[1], r = true;
    if (k === 'hint') r = !!state.hints[v];
    else if (k === 'quest') r = !!state.quests[v];
    else if (k === 'can') r = canComplete(v);
    else if (k === 'done') r = state.quests[v] === 'done';
    else if (k === 'pieces') r = pieces() >= +v;
    else if (k === 'found') r = !!state.found[v];
    return neg ? !r : r;
  }
  function canComplete(id) { var q = QUESTS[id]; return state.quests[id] === 'active' && (state.cargo[q.good] || 0) >= q.n; }
  function effects(spec) {
    if (!spec) return;
    spec.split(',').forEach(function (e) {
      var p = e.split(':'), k = p[0], v = p[1];
      if (k === 'hint' && !state.hints[v]) { state.hints[v] = 1; say('🗺️ Marked on your chart: rumored treasure on ' + STASHES[v].name + '.'); }
      else if (k === 'know' && !state.known[v]) {
        state.known[v] = 1;
        reveal(PORTS[v].map, PORTS[v].dock[0], PORTS[v].dock[1], 120);
        say('🧭 ' + PORTS[v].name + ' (' + MAPS[PORTS[v].map].short + ') is now on your chart.');
      }
      else if (k === 'quest' && !state.quests[v]) { var q = QUESTS[v]; state.quests[v] = 'active'; say('📜 New request: bring ' + baleWord(q.n) + ' of ' + GOODS[q.good].name + ' to ' + PORTS[q.port].name + '.'); }
      else if (k === 'complete' && canComplete(v)) {
        var qq = QUESTS[v];
        takeCargo(qq.good, qq.n);
        state.gold += qq.gold;
        state.quests[v] = 'done';
        if (v === 'prudence') state.flags.vicar = 1;
        sfx('coin');
        say('🪙 Delivered! +' + fmt(qq.gold) + ' doubloons.' + gainXp(qq.gold / 4));
      }
    });
    checkGoals();
    save();
  }
  function renderTavern(pid, panel) {
    var who = PEOPLE[PORTS[pid].who], node = talkNode === 'bye' ? null : who[talkNode] || who.start;
    var card = el('div', {class: 'npc'});
    card.appendChild(el('span', {class: 'portrait', 'aria-hidden': 'true'}, who.icon));
    var id = el('div');
    id.appendChild(el('h3', null, who.name));
    id.appendChild(el('p', {class: 'role'}, who.role));
    card.appendChild(id);
    panel.appendChild(card);
    var says = el('p', {class: 'says', id: 'npc-says', tabindex: '-1'});
    var opts = el('div', {class: 'choices'});
    if (!node) {
      says.textContent = 'You tip your hat to ' + who.name + ' and head back to the docks.';
      var again = el('button', {type: 'button', class: 'choice'}, 'Talk again');
      again.addEventListener('click', function () { talkNode = 'start'; renderPanel(); $('npc-says').focus(); });
      opts.appendChild(again);
    } else {
      says.textContent = '“' + node.text + '”';
      if (node.do) effects(node.do);
      node.options.forEach(function (o) {
        if (!cond(o.if) || !cond(o.also)) return;
        var b = el('button', {type: 'button', class: 'choice'}, o.label);
        b.addEventListener('click', function () {
          if (o.do) effects(o.do);
          talkNode = o.end ? 'bye' : o.next;
          renderPanel();
          $('npc-says').focus();
        });
        opts.appendChild(b);
      });
    }
    panel.appendChild(says);
    panel.appendChild(opts);
    var mine = Object.keys(QUESTS).filter(function (q) { return QUESTS[q].by === PORTS[pid].who && state.quests[q] === 'active'; });
    mine.forEach(function (q) {
      var Q = QUESTS[q];
      panel.appendChild(el('p', {class: 'hint'}, '📜 Request: ' + baleWord(Q.n) + ' of ' + GOODS[Q.good].name + ' (you have ' + (state.cargo[Q.good] || 0) + '). Reward: ' + fmt(Q.gold) + ' doubloons.'));
    });
  }
  function renderYard(panel) {
    panel.appendChild(el('p', {class: 'hint'}, 'The shipwright can fit out your sloop, for a price.'));
    var ul = el('ul', {class: 'goods'});
    Object.keys(UP).forEach(function (k) {
      var U = UP[k], lvl = state.up[k], max = U.levels.length - 1;
      var li = el('li', {class: 'good'});
      var head = el('div', {class: 'g-head'});
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, U.icon));
      head.appendChild(el('h3', null, U.name));
      li.appendChild(head);
      var now = k === 'hold' ? 'Holds ' + U.levels[lvl] + ' bales now.' : k === 'hull' ? U.levels[lvl] + ' hull points now.' : k === 'lavender' ? (lvl ? 'Fitted.' : 'Not fitted yet.') : 'Level ' + lvl + ' of ' + max + '.';
      li.appendChild(el('p', {class: 'g-note'}, U.note + ' ' + now));
      var btns = el('div', {class: 'g-btns'});
      if (lvl < max) {
        var cost = U.cost[lvl], label = k === 'hold' ? 'Grow to ' + U.levels[lvl + 1] + ' bales' : k === 'hull' ? 'Strengthen to ' + U.levels[lvl + 1] + ' points' : k === 'lavender' ? 'Fit it' : 'Upgrade to level ' + (lvl + 1);
        var b = el('button', {type: 'button', 'data-key': 'up' + k, 'aria-label': label + ' for ' + fmt(cost) + ' doubloons'}, label + ' · ' + fmt(cost) + ' 🪙');
        b.disabled = state.gold < cost;
        b.addEventListener('click', function () {
          if (state.gold < cost) return;
          state.gold -= cost; state.up[k]++;
          if (k === 'hull') state.hull += U.levels[state.up.hull] - U.levels[state.up.hull - 1];
          sfx('fanfare');
          say('🔨 ' + U.name + ': done! ' + (k === 'hold' ? 'Your hold now takes ' + capacity() + ' bales.' : k === 'hull' ? 'Your ship now has ' + hullMax() + ' hull points.' : 'The shipwright wipes their hands and grins.'));
          checkGoals(); save(); renderPanel('up' + k);
        });
        btns.appendChild(b);
      } else btns.appendChild(el('span', {class: 'tag'}, 'Fully fitted'));
      li.appendChild(btns);
      ul.appendChild(li);
    });
    panel.appendChild(ul);
  }

  /* ---------- goals and the captain's log ---------- */
  function goalList() {
    var visited = Object.keys(state.visited).length, strains = STRAINS.filter(function (g) { return state.collected[g]; }).length, lv = level();
    return [
      {id: 'full', text: 'Fill your hold to the brim', done: !!state.flags.full},
      {id: 'k1', text: 'Have 1,000 doubloons in your purse', done: !!state.flags.k1},
      {id: 'pillage', text: 'Pillage a merchant ship', done: state.pillaged > 0},
      {id: 'pirate', text: 'Beat a pirate ship in battle', done: state.sunk > 0},
      {id: 'lv5', text: 'Reach level 5, ' + title(5), done: lv >= 5},
      {id: 'maps', text: 'Dig up 3 treasure maps', n: Math.min(3, state.dug) + ' of 3', done: state.dug >= 3},
      {id: 'ports', text: 'Drop anchor in all ' + NPORTS + ' ports', n: visited + ' of ' + NPORTS, done: visited >= NPORTS},
      {id: 'pieces', text: 'Find the 3 pieces of Captain Featherstone’s map', n: pieces() + ' of 3', done: pieces() >= 3},
      {id: 'emerald', text: 'Dig up the Emerald Bale', done: !!state.found.emerald},
      {id: 'strains', text: 'Collect all ' + STRAINS.length + ' strains', n: strains + ' of ' + STRAINS.length, done: strains >= STRAINS.length},
      {id: 'boss', text: 'Beat ' + D.BOSS.captain + ' of ' + D.BOSS.ship + ' (sails the Spanish Main from level ' + D.BOSS.level + ')', done: !!state.flags.boss},
      {id: 'lv10', text: 'Reach level 10, ' + title(10), done: lv >= 10}
    ];
  }
  function checkGoals() {
    if (!state) return;
    if (cargoCount() >= capacity()) state.flags.full = 1;
    if (state.gold >= 1000) state.flags.k1 = 1;
    goalList().forEach(function (g) {
      if (g.done && !state.flags['g_' + g.id]) {
        state.flags['g_' + g.id] = 1;
        sfx('fanfare');
        say('🏆 Goal complete: ' + g.text.replace(/ \(.*\)$/, '') + '!');
      }
    });
    if (state.docked && openDialogEl() === $('dlg-port')) $('port-status').textContent = portStatus();
  }

  /* ---------- levels and skills ---------- */
  function skillList(onSpend) {
    var ul = el('ul', {class: 'goods skills'});
    Object.keys(D.SKILLS).forEach(function (k) {
      var S = D.SKILLS[k], v = state.skill[k], li = el('li', {class: 'good'}), head = el('div', {class: 'g-head'});
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, S.icon));
      head.appendChild(el('h3', null, S.name));
      head.appendChild(el('span', {class: 'tag'}, v + ' of ' + D.SKILL_MAX));
      li.appendChild(head);
      li.appendChild(el('p', {class: 'g-note'}, S.note));
      if (state.pts > 0 && v < D.SKILL_MAX) {
        var b = el('button', {type: 'button', class: 'primary', 'data-key': 'sk' + k}, 'Train ' + S.name + ' to ' + (v + 1));
        b.addEventListener('click', function () {
          if (state.pts <= 0 || state.skill[k] >= D.SKILL_MAX) return;
          state.skill[k]++; state.pts--;
          sfx('pickup');
          save();
          onSpend('sk' + k);
        });
        var w = el('div', {class: 'g-btns'});
        w.appendChild(b);
        li.appendChild(w);
      }
      ul.appendChild(li);
    });
    return ul;
  }
  function refocus(box, key, fallback) {
    var again = box.querySelector('[data-key="' + key + '"]') || (key.indexOf('sk') === 0 ? box.querySelector('[data-key^="sk"]') : null);
    (again || fallback).focus();
  }
  function showLevelUp() {
    var lv = levelUp, wrap = el('div');
    levelUp = 0;
    if (!state.pts) return;
    function draw(key) {
      wrap.textContent = '';
      wrap.appendChild(el('p', {class: 'win'}, state.pts ? 'Skill points to spend: ' + state.pts + '.' : 'All spent. Fair winds, Captain.'));
      wrap.appendChild(skillList(function (k) { draw(k); refocus(wrap, k, $('note-ok')); }));
    }
    draw();
    note(lv > 0 ? '🎖️ Level ' + lv + ': ' + title(lv) + '!' : '⭐ A new skill point',
      (lv > 0 ? 'Word of your exploits is spreading through every tavern in the Caribbean. ' : '') + 'Pick a skill to train now, or later from your captain’s log.', wrap);
    var first = wrap.querySelector('[data-key^="sk"]');
    if (first) setTimeout(function () { first.focus(); }, 0);
  }

  function openLog() { renderLog(); openDialog($('dlg-log'), $('log-close')); }
  function renderLog(key) {
    var b = $('log-body'), lv = level(), next = D.LEVELS[lv], st = stats();
    b.textContent = '';
    b.appendChild(el('p', null, '🎖️ ' + rank() + ' · 📅 Day ' + day() + ' · 🪙 ' + fmt(state.gold) + ' doubloons · ⛵ ' + fmt(state.dist / 100) + ' leagues sailed · ⚔️ ' + state.pillaged + ' ' + plural(state.pillaged, 'merchant') + ' pillaged, ' + state.sunk + ' ' + plural(state.sunk, 'pirate') + ' beaten'));
    b.appendChild(el('h3', null, 'Your captain: level ' + lv + ', ' + title(lv)));
    b.appendChild(el('p', null, '⭐ Renown: ' + fmt(state.xp) + (next ? '. Level ' + (lv + 1) + ', ' + next.title + ', at ' + fmt(next.xp) + '.' : '. You’ve reached the top level!')));
    if (next) {
      var prev = D.LEVELS[lv - 1].xp, track = el('span', {class: 'bar xp', 'aria-hidden': 'true'}), fill = el('span');
      fill.style.width = clamp((state.xp - prev) / (next.xp - prev) * 100, 0, 100).toFixed(0) + '%';
      track.appendChild(fill);
      b.appendChild(track);
    }
    b.appendChild(el('p', {class: 'hint'}, 'Earn renown by trading at a profit, winning fights, finishing requests, finding treasure and seeing new ports.'));
    b.appendChild(el('p', null, '🛡️ Hull ' + state.hull + ' of ' + st.hullMax + ' · 💣 Broadside about ' + st.fire + ' damage · 👥 Boarders: level ' + st.crew + ' · ⛵ Sails: level ' + st.sails));
    var bz = boost();
    if (bz) b.appendChild(el('p', {class: 'win'}, '🔥 ' + bz.name + ': ' + bz.does + ' About ' + boostLeft() + ' ' + plural(boostLeft(), 'day') + ' left.'));
    if (state.pts) b.appendChild(el('p', {class: 'win'}, 'You have ' + state.pts + ' skill ' + plural(state.pts, 'point') + ' to spend.'));
    b.appendChild(skillList(function (k) { renderLog(k); }));
    b.appendChild(el('h3', null, 'Goals'));
    var ul = el('ul', {class: 'checks'});
    goalList().forEach(function (g) {
      var li = el('li', {class: g.done ? 'done' : ''});
      li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, g.done ? '✅' : '⬜'));
      li.appendChild(el('span', {class: 'sr-only'}, g.done ? 'Done: ' : 'Not yet: '));
      li.appendChild(document.createTextNode(g.text + (g.n ? ' (' + g.n + ')' : '')));
      ul.appendChild(li);
    });
    b.appendChild(ul);
    var reqs = Object.keys(QUESTS).filter(function (q) { return state.quests[q]; });
    if (reqs.length) {
      b.appendChild(el('h3', null, 'Requests'));
      var rq = el('ul', {class: 'checks'});
      reqs.forEach(function (q) {
        var Q = QUESTS[q], done = state.quests[q] === 'done', li = el('li', {class: done ? 'done' : ''});
        li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, done ? '✅' : '📜'));
        li.appendChild(el('span', {class: 'sr-only'}, done ? 'Delivered: ' : 'Open: '));
        li.appendChild(document.createTextNode(PEOPLE[Q.by].name + ' in ' + PORTS[Q.port].name + ' wants ' + baleWord(Q.n) + ' of ' + GOODS[Q.good].name +
          (done ? '.' : ' (you have ' + (state.cargo[Q.good] || 0) + '). Reward: ' + fmt(Q.gold) + ' doubloons.')));
        rq.appendChild(li);
      });
      b.appendChild(rq);
    }
    var rum = Object.keys(STASHES).filter(function (s) { return !state.found[s] && (state.hints[s] || (STASHES[s].needs && pieces() >= 3)); });
    if (rum.length || state.tmap) {
      b.appendChild(el('h3', null, 'Treasure rumors'));
      var ru = el('ul', {class: 'checks'});
      rum.forEach(function (s) {
        var li = el('li');
        li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, '✖️'));
        li.appendChild(document.createTextNode('Something is buried on ' + STASHES[s].name + ' (' + MAPS[STASHES[s].map].short + ').'));
        ru.appendChild(li);
      });
      if (state.tmap) {
        var tl = el('li');
        tl.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, '🗺️'));
        tl.appendChild(document.createTextNode('Your treasure map: something is buried on ' + state.tmap.name + ' (' + MAPS[state.tmap.map].short + ').'));
        ru.appendChild(tl);
      }
      b.appendChild(ru);
    }
    b.appendChild(el('h3', null, 'Cargo hold: ' + cargoCount() + ' of ' + capacity() + ' bales'));
    var held = Object.keys(state.cargo);
    if (!held.length) b.appendChild(el('p', null, 'Empty, apart from a parrot and a smell.'));
    else {
      b.appendChild(el('p', {class: 'hint'}, 'Smoke a bale for a boost that lasts about two days of sailing. One boost at a time: a new one replaces the old.'));
      var cu = el('ul', {class: 'checks'});
      held.forEach(function (g) {
        var li = el('li'), S = SMOKE[g];
        li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, GOODS[g].icon));
        li.appendChild(el('span', {class: 'grow'}, GOODS[g].name + ': ' + baleWord(state.cargo[g]) + (S ? '. ' + S.name + '. ' + S.does : '')));
        if (S) {
          var sb = el('button', {type: 'button', class: 'mini', 'data-key': 'sm' + g, 'aria-label': cap(verb(g)) + ' a bale of ' + GOODS[g].name + ' for ' + S.name}, '🔥 ' + cap(verb(g)) + ' 1');
          sb.addEventListener('click', function () { smoke(g); renderLog('sm' + g); });
          li.appendChild(sb);
        }
        cu.appendChild(li);
      });
      b.appendChild(cu);
    }
    var ns = STRAINS.filter(function (g) { return state.collected[g]; }).length;
    b.appendChild(el('h3', null, 'Strain ledger: ' + ns + ' of ' + STRAINS.length));
    var lu = el('ul', {class: 'checks ledger'});
    STRAINS.forEach(function (g) {
      var G = GOODS[g], has = state.collected[g], li = el('li', {class: has ? 'done' : ''});
      li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, has ? G.icon : '❔'));
      li.appendChild(el('span', {class: 'sr-only'}, has ? 'Collected: ' : 'Not yet: '));
      li.appendChild(document.createTextNode(G.name + ' · ' + (G.rare || 'Grown in ' + PORTS[G.home].name + '.')));
      lu.appendChild(li);
    });
    b.appendChild(lu);
    if (key) refocus(b, key, $('log-close'));
  }

  /* ---------- chart and autopilot ---------- */
  var chartMap = 'windward';
  function destinations(mid) {
    var out = [];
    Object.keys(PORTS).forEach(function (pid) {
      var p = PORTS[pid];
      if (p.map !== mid || !portKnown(pid)) return;
      out.push({type: 'port', id: pid, map: p.map, x: p.dock[0], y: p.dock[1], label: p.name, icon: '⚓', here: state.docked === pid});
    });
    Object.keys(STASHES).forEach(function (sid) {
      var s = STASHES[sid];
      if (s.map !== mid || state.found[sid]) return;
      if (!(state.hints[sid] || (s.needs && pieces() >= s.needs))) return;
      out.push({type: 'stash', id: sid, map: s.map, x: s.at[0], y: s.at[1], label: 'the treasure on ' + s.name, icon: '✖️'});
    });
    var tm = state.tmap;
    if (tm && tm.map === mid) out.push({type: 'tmap', id: 'tmap', map: mid, x: tm.at[0], y: tm.at[1], label: 'the treasure on ' + tm.name, icon: '✖️'});
    if (mid === state.map) {
      MAPS[mid].exits.forEach(function (e) {
        var pt = exitPoint(e);
        out.push({type: 'exit', id: e.to, map: e.to, x: pt[0], y: pt[1], label: MAPS[e.to].name, icon: '⛵', exit: e});
      });
    }
    return out;
  }
  function goExit(e) {
    var arrive = e.exit.arrive, m = MAPS[e.exit.to];
    return {type: 'point', map: e.exit.to, x: arrive[0] === 'x' ? clamp(state.x, 80, m.w - 80) : arrive[0], y: arrive[1], label: m.name};
  }
  function openChart() {
    chartMap = state.map;
    renderChart();
    openDialog($('dlg-chart'), $('chart-dests').querySelector('button:not([disabled])') || $('chart-close'));
  }
  function renderChart() {
    var seas = $('chart-seas');
    seas.textContent = '';
    Object.keys(MAPS).forEach(function (mid) {
      var seen = mid === state.map || state.flags['seen_' + mid] || Object.keys(PORTS).some(function (p) { return PORTS[p].map === mid && portKnown(p); });
      var b = el('button', {type: 'button', 'aria-pressed': mid === chartMap ? 'true' : 'false'}, MAPS[mid].short + (mid === state.map ? ' (you are here)' : ''));
      b.disabled = !seen;
      b.addEventListener('click', function () { chartMap = mid; renderChart(); b.focus(); });
      seas.appendChild(b);
    });
    var cvs = $('chart-canvas'), m = enterMap(chartMap), wrap = cvs.parentNode;
    var cw = Math.max(200, wrap.clientWidth || 600), ch = Math.round(cw * m.h / m.w), dpr = Math.min(2, window.devicePixelRatio || 1);
    cvs.width = Math.round(cw * dpr); cvs.height = Math.round(ch * dpr);
    cvs.style.height = ch + 'px';
    var sc = cw / m.w;
    drawWorld(cvs.getContext('2d'), m, {a: dpr * sc, e: 0, f: 0, dpr: dpr, cw: cw, ch: ch}, {chart: true});
    cvs.setAttribute('aria-label', 'Chart of ' + m.name + '. The places you can sail to are listed below it.');
    $('chart-title-sea').textContent = m.name;
    var dl = $('chart-dests');
    dl.textContent = '';
    var list = destinations(chartMap);
    if (!list.length) dl.appendChild(el('li', null, 'Nothing charted here yet. Sail this way to fill in the map.'));
    list.forEach(function (d) {
      var li = el('li'), where = d.type === 'exit' ? 'sea passage' : MAPS[d.map].short;
      var b = el('button', {type: 'button'}, '');
      b.appendChild(el('span', {'aria-hidden': 'true'}, d.icon + ' '));
      b.appendChild(document.createTextNode((d.type === 'exit' ? 'Sail on to ' : 'Sail to ') + d.label + (d.here ? ' (you are here)' : '')));
      b.appendChild(el('span', {'class': 'sr-only'}, ','));
      b.appendChild(el('small', null, ' ' + where));
      b.disabled = !!d.here;
      b.addEventListener('click', function () {
        closeDialog('dlg-chart');
        setCourse(d.type === 'exit' ? goExit(d) : d);
      });
      li.appendChild(b);
      dl.appendChild(li);
    });
    var lg = $('chart-ledger');
    lg.textContent = '';
    renderLedger(lg, null);
  }
  function chartClick(ev) {
    var cvs = $('chart-canvas'), r = cvs.getBoundingClientRect(), m = MAPS[chartMap];
    var x = (ev.clientX - r.left) / r.width * m.w, y = (ev.clientY - r.top) / r.height * m.h, best = null, bd = 70;
    destinations(chartMap).forEach(function (d) {
      if (d.here) return;
      var dd = Math.hypot(d.x - x, d.y - y);
      if (dd < bd) { bd = dd; best = d; }
    });
    if (best) { closeDialog('dlg-chart'); setCourse(best.type === 'exit' ? goExit(best) : best); }
  }

  /* ---------- where am I (for everyone, and read aloud for screen readers) ---------- */
  function updateWhere(quiet) {
    var m = curMap(), txt, key;
    if (state.docked) { txt = '⚓ Docked at ' + PORTS[state.docked].name + ', ' + m.name + '.'; key = 'dock' + state.docked; }
    else {
      var best = null, bd = Infinity;
      Object.keys(PORTS).forEach(function (pid) {
        var p = PORTS[pid];
        if (p.map !== state.map || !portKnown(pid)) return;
        var d = Math.hypot(p.dock[0] - state.x, p.dock[1] - state.y);
        if (d < bd) { bd = d; best = pid; }
      });
      txt = '📍 ' + m.name + '.';
      key = state.map;
      if (best) {
        var p = PORTS[best], lg = Math.max(1, Math.round(bd / 100)), dir = compass(p.dock[0] - state.x, p.dock[1] - state.y);
        txt += bd < 120 ? ' ' + p.name + ' is right here.' : ' Nearest port: ' + p.name + ', about ' + lg + ' ' + plural(lg, 'league') + ' to the ' + dir + '.';
        key += best + (bd < 120 ? 'here' : bd < 400 ? 'near' : 'far');
      }
      if (auto && auto.goal.type !== 'point') txt += ' Course set for ' + auto.goal.label + '.';
    }
    if ($('where').textContent !== txt) $('where').textContent = txt;
    if (key !== lastWhereKey) {
      if (lastWhereKey && !state.docked && !quiet) announce(txt.replace(/^\S+\s/, ''));
      lastWhereKey = key;
    }
  }

  /* ---------- drawing ---------- */
  var cv = $('sea'), ctx = cv.getContext('2d'), view = {w: 1, h: 1, dpr: 1, s: 1, cx: 0, cy: 0}, needRender = true;
  var LOOK = {
    player: {hull: '#7a4b26', deck: '#c29560', sail: '#fbf4e2', flag: '#141414', mark: '#2f8f4e'},
    customs: {hull: '#2b394d', deck: '#8494ab', sail: '#2f6fd6', flag: '#ffffff'},
    merchant: {hull: '#8a5a2b', deck: '#d2aa74', sail: '#efd59e', flag: '#c0392b'},
    looted: {hull: '#6d5a48', deck: '#a99780', sail: '#b2a993', flag: '#7f7f7f'},
    pirate: {hull: '#2b2420', deck: '#6a5d52', sail: '#1c1c1c', flag: '#f2f2f2', mark: '#f2f2f2'},
    boss: {hull: '#3a1010', deck: '#7a4a3a', sail: '#4d0b0b', flag: '#f2d34a', mark: '#f2d34a'}
  };
  function resize() {
    var r = cv.getBoundingClientRect();
    view.dpr = Math.min(2, window.devicePixelRatio || 1);
    view.w = Math.max(1, r.width); view.h = Math.max(1, r.height);
    cv.width = Math.round(view.w * view.dpr); cv.height = Math.round(view.h * view.dpr);
    view.s = clamp(Math.min(view.w, view.h) / 520, 0.55, 1.35);
    snapCamera();
    needRender = true;
  }
  function camTarget() {
    var m = curMap(), s = view.s, hw = view.w / 2 / s, hh = view.h / 2 / s;
    return [m.w <= hw * 2 ? m.w / 2 : clamp(state.x, hw, m.w - hw), m.h <= hh * 2 ? m.h / 2 : clamp(state.y, hh, m.h - hh)];
  }
  function snapCamera() { if (!state) return; var c = camTarget(); view.cx = c[0]; view.cy = c[1]; }

  function pill(c, text, x, y, opts) {
    opts = opts || {};
    c.font = (opts.font || '700 13px system-ui, -apple-system, "Segoe UI", sans-serif');
    var w = c.measureText(text).width + 14, h = opts.h || 22, x0 = x - w / 2, y0 = y - h / 2, r = 7;
    c.beginPath();
    c.moveTo(x0 + r, y0); c.lineTo(x0 + w - r, y0); c.quadraticCurveTo(x0 + w, y0, x0 + w, y0 + r);
    c.lineTo(x0 + w, y0 + h - r); c.quadraticCurveTo(x0 + w, y0 + h, x0 + w - r, y0 + h);
    c.lineTo(x0 + r, y0 + h); c.quadraticCurveTo(x0, y0 + h, x0, y0 + h - r);
    c.lineTo(x0, y0 + r); c.quadraticCurveTo(x0, y0, x0 + r, y0); c.closePath();
    c.fillStyle = opts.bg || 'rgba(255,250,236,.94)'; c.fill();
    c.lineWidth = 1; c.strokeStyle = opts.line || 'rgba(40,30,10,.45)'; c.stroke();
    c.fillStyle = opts.ink || '#1b2a24'; c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText(text, x, y + 1);
  }
  function drawShip(c, x, y, a, look, L) {
    c.save(); c.translate(x, y); c.rotate(a);
    c.fillStyle = 'rgba(0,30,40,.22)'; c.beginPath(); c.ellipse(1.5, 3, L * 0.95, L * 0.42, 0, 0, Math.PI * 2); c.fill();
    c.beginPath(); c.moveTo(L, 0); c.quadraticCurveTo(L * 0.35, -L * 0.5, -L * 0.8, -L * 0.36); c.lineTo(-L * 0.8, L * 0.36); c.quadraticCurveTo(L * 0.35, L * 0.5, L, 0); c.closePath();
    c.fillStyle = look.hull; c.fill(); c.lineWidth = 1.2; c.strokeStyle = 'rgba(0,0,0,.55)'; c.stroke();
    c.beginPath(); c.moveTo(L * 0.7, 0); c.quadraticCurveTo(L * 0.25, -L * 0.32, -L * 0.62, -L * 0.22); c.lineTo(-L * 0.62, L * 0.22); c.quadraticCurveTo(L * 0.25, L * 0.32, L * 0.7, 0); c.closePath();
    c.fillStyle = look.deck; c.fill();
    c.beginPath(); c.moveTo(-L * 0.02, -L * 0.85); c.quadraticCurveTo(L * 0.52, 0, -L * 0.02, L * 0.85); c.lineTo(-L * 0.18, L * 0.8); c.quadraticCurveTo(L * 0.28, 0, -L * 0.18, -L * 0.8); c.closePath();
    c.fillStyle = look.sail; c.fill(); c.lineWidth = 0.8; c.strokeStyle = 'rgba(0,0,0,.4)'; c.stroke();
    if (look.mark) { c.fillStyle = look.mark; c.beginPath(); c.ellipse(L * 0.13, 0, L * 0.09, L * 0.2, 0, 0, Math.PI * 2); c.fill(); }
    c.fillStyle = look.flag; c.fillRect(-L * 1.0, -L * 0.13, L * 0.3, L * 0.26);
    c.restore();
  }
  function drawTown(c, p) {
    var x = p.town[0], y = p.town[1], dx = p.dock[0] - x, dy = p.dock[1] - y, d = Math.hypot(dx, dy) || 1;
    c.strokeStyle = '#6b4a2b'; c.lineWidth = 3.5; c.lineCap = 'round';
    c.beginPath(); c.moveTo(x + dx / d * 8, y + dy / d * 8); c.lineTo(x + dx * 0.72, y + dy * 0.72); c.stroke();
    var houses = [[-10, -3, '#c0392b'], [0, -8, '#d35400'], [10, -2, '#2e86c1'], [-4, 5, '#8e44ad'], [7, 6, '#27ae60']];
    houses.forEach(function (h) {
      var hx = x + h[0], hy = y + h[1];
      c.fillStyle = '#f7ecd6'; c.fillRect(hx - 3.5, hy - 2, 7, 6);
      c.fillStyle = h[2]; c.beginPath(); c.moveTo(hx - 4.5, hy - 2); c.lineTo(hx, hy - 6); c.lineTo(hx + 4.5, hy - 2); c.closePath(); c.fill();
    });
  }
  function drawCrate(c, f, anim) {
    var bob = anim ? Math.sin(t * 2.2 + f.ph) * 1.6 : 0, x = f.x, y = f.y + bob;
    c.fillStyle = 'rgba(255,255,255,.35)'; c.beginPath(); c.ellipse(x, f.y + 6, 9, 3, 0, 0, Math.PI * 2); c.fill();
    if (f.g === 'bottle') {
      c.save(); c.translate(x, y); c.rotate(0.6);
      c.fillStyle = '#3f8f5a'; c.fillRect(-3, -6, 6, 10); c.fillRect(-1.5, -9, 3, 4);
      c.fillStyle = '#f3e9cf'; c.fillRect(-1.8, -4, 3.6, 5);
      c.restore();
      return;
    }
    c.fillStyle = f.g === 'mermaid' ? '#d77fa1' : '#a8763e';
    c.fillRect(x - 6, y - 6, 12, 12);
    c.strokeStyle = 'rgba(60,30,10,.7)'; c.lineWidth = 1.2; c.strokeRect(x - 6, y - 6, 12, 12);
    c.beginPath(); c.moveTo(x - 6, y - 6); c.lineTo(x + 6, y + 6); c.moveTo(x + 6, y - 6); c.lineTo(x - 6, y + 6); c.stroke();
    if (f.g === 'mermaid') { c.fillStyle = '#fff6b0'; c.beginPath(); c.arc(x + 7, y - 7, anim ? 1.5 + Math.sin(t * 5) : 2, 0, Math.PI * 2); c.fill(); }
  }
  function drawWaves(c, m, T, anim) {
    var x0 = -T.e / T.a, y0 = -T.f / T.a, x1 = x0 + T.cw * T.dpr / T.a, y1 = y0 + T.ch * T.dpr / T.a, stp = 70;
    c.strokeStyle = 'rgba(255,255,255,.3)'; c.lineWidth = 1.4; c.beginPath();
    for (var gx = Math.floor(Math.max(0, x0) / stp) * stp; gx < Math.min(m.w, x1); gx += stp) {
      for (var gy = Math.floor(Math.max(0, y0) / stp) * stp; gy < Math.min(m.h, y1); gy += stp) {
        var r = Math.sin(gx * 12.9898 + gy * 78.233) * 43758.5453; r -= Math.floor(r);
        var x = gx + r * stp, y = gy + ((r * 7) % 1) * stp, dx = anim ? Math.sin(t * 0.9 + r * 6) * 4 : 0;
        c.moveTo(x - 6 + dx, y); c.quadraticCurveTo(x + dx, y - 4, x + 6 + dx, y);
      }
    }
    c.stroke();
  }
  function stashMarks(mid) {
    var out = Object.keys(STASHES).filter(function (sid) {
      var s = STASHES[sid];
      return s.map === mid && !state.found[sid] && (state.hints[sid] || (s.needs && pieces() >= s.needs));
    }).map(function (sid) { return STASHES[sid].at; });
    if (state.tmap && state.tmap.map === mid) out.push(state.tmap.at);
    return out;
  }
  function drawWorld(c, m, T, opts) {
    var chart = !!opts.chart, anim = !calm() && !chart, mid = m.id;
    c.setTransform(T.dpr, 0, 0, T.dpr, 0, 0);
    c.fillStyle = '#0b4250'; c.fillRect(0, 0, T.cw, T.ch);
    c.setTransform(T.a, 0, 0, T.a, T.e, T.f);
    var g = c.createLinearGradient(0, 0, 0, m.h);
    g.addColorStop(0, '#2aa9bd'); g.addColorStop(1, '#1b86a0');
    c.fillStyle = g; c.fillRect(0, 0, m.w, m.h);
    if (!chart) drawWaves(c, m, T, anim);
    c.lineJoin = 'round';
    m.draw.forEach(function (d) { c.strokeStyle = 'rgba(150,236,228,.42)'; c.lineWidth = 28; c.stroke(d.path); });
    m.draw.forEach(function (d) { c.strokeStyle = 'rgba(200,248,238,.55)'; c.lineWidth = 12; c.stroke(d.path); });
    m.draw.forEach(function (d) {
      c.fillStyle = '#64a553'; c.fill(d.path);
      c.save(); c.clip(d.path);
      c.strokeStyle = '#ecd8a0'; c.lineWidth = 10; c.stroke(d.path);
      if (d.inner) { c.fillStyle = '#4f8c43'; c.fill(d.inner); }
      c.restore();
    });
    Object.keys(PORTS).forEach(function (pid) { if (PORTS[pid].map === mid) drawTown(c, PORTS[pid]); });
    m.lands.forEach(function (L) {
      if (!L.haze) return;
      for (var i = 0; i < 5; i++) {
        var hx = L.blob[0] + Math.cos(i * 1.3 + (anim ? t * 0.25 : 0)) * 22, hy = L.blob[1] + Math.sin(i * 1.7 + (anim ? t * 0.2 : 0)) * 14;
        var rg = c.createRadialGradient(hx, hy, 2, hx, hy, 46);
        rg.addColorStop(0, 'rgba(214,206,236,.55)'); rg.addColorStop(1, 'rgba(214,206,236,0)');
        c.fillStyle = rg; c.beginPath(); c.arc(hx, hy, 46, 0, Math.PI * 2); c.fill();
      }
    });
    if (!chart && mid === state.map) {
      floaters[mid].list.forEach(function (f) { drawCrate(c, f, anim); });
      wake.forEach(function (w) {
        c.fillStyle = 'rgba(255,255,255,' + (0.45 * (1 - w.age / 1.6)).toFixed(3) + ')';
        c.beginPath(); c.arc(w.x, w.y, 2 + w.age * 4, 0, Math.PI * 2); c.fill();
      });
      npcs[mid].forEach(function (n) {
        if (n.gone) return;
        var look = n.kind === 'merchant' ? (n.looted ? LOOK.looted : LOOK.merchant) : LOOK[n.kind];
        drawShip(c, n.x, n.y, n.angle, look, n.kind === 'merchant' ? 20 : n.kind === 'boss' ? 23 : n.kind === 'pirate' ? 17 : 15);
      });
      var bob = anim ? Math.sin(t * 1.6) * 0.06 : 0;
      drawShip(c, state.x, state.y, state.angle + bob, LOOK.player, 15);
    }
    c.imageSmoothingEnabled = true;
    var f = fogFor(mid);
    c.drawImage(fogCanvas(mid), 0, 0, f.cols, f.rows, 0, 0, f.cols * FOG, f.rows * FOG);
    if (chart && mid === state.map) {
      c.fillStyle = '#d0342c'; c.strokeStyle = '#fff'; c.lineWidth = 4;
      c.beginPath(); c.arc(state.x, state.y, 14, 0, Math.PI * 2); c.fill(); c.stroke();
    }
    stashMarks(mid).forEach(function (at) {
      var s = {at: at};
      c.setLineDash([6, 5]); c.strokeStyle = 'rgba(120,20,20,.85)'; c.lineWidth = chart ? 4 : 2;
      c.beginPath(); c.arc(s.at[0], s.at[1], chart ? 46 : 38, 0, Math.PI * 2); c.stroke(); c.setLineDash([]);
      c.strokeStyle = '#b3201b'; c.lineWidth = chart ? 7 : 4; c.lineCap = 'round';
      c.beginPath(); c.moveTo(s.at[0] - 9, s.at[1] - 9); c.lineTo(s.at[0] + 9, s.at[1] + 9); c.moveTo(s.at[0] + 9, s.at[1] - 9); c.lineTo(s.at[0] - 9, s.at[1] + 9); c.stroke();
    });
    if (!chart && auto && auto.goal.map === mid) {
      var last = auto.path[auto.path.length - 1], pr = anim ? 10 + Math.sin(t * 4) * 3 : 11;
      c.strokeStyle = 'rgba(255,255,255,.9)'; c.lineWidth = 2.5; c.beginPath(); c.arc(last[0], last[1], pr, 0, Math.PI * 2); c.stroke();
    }
    // Labels, drawn at screen size.
    c.setTransform(T.dpr, 0, 0, T.dpr, 0, 0);
    var k = T.a / T.dpr, ex = T.e / T.dpr, fy = T.f / T.dpr;
    function sx(x) { return ex + x * k; }
    function sy(y) { return fy + y * k; }
    c.textAlign = 'center'; c.textBaseline = 'middle';
    m.lands.forEach(function (L) {
      if (!L.label || !explored(mid, L.label[0], L.label[1])) return;
      c.font = 'italic 700 ' + (chart ? 11 : 13) + 'px Georgia, "Times New Roman", serif';
      c.fillStyle = 'rgba(22,52,28,.8)';
      c.fillText(L.name, sx(L.label[0]), sy(L.label[1]));
    });
    Object.keys(PORTS).forEach(function (pid) {
      var p = PORTS[pid];
      if (p.map !== mid || !portKnown(pid)) return;
      pill(c, '⚓ ' + p.name, sx(p.town[0]), sy(p.town[1]) - (chart ? 12 : 20), chart ? {font: '700 11px system-ui, sans-serif', h: 18} : null);
    });
    stashMarks(mid).forEach(function (at) {
      var s = {at: at};
      pill(c, 'Buried treasure?', sx(s.at[0]), sy(s.at[1]) + (chart ? 22 : 34), {font: '700 11px system-ui, sans-serif', h: 18, bg: 'rgba(255,240,220,.94)', ink: '#7a1712'});
    });
    if (!chart && mid === state.map) {
      npcs[mid].forEach(function (n) {
        if (n.gone || (n.kind !== 'pirate' && n.kind !== 'boss') || !explored(mid, n.x, n.y)) return;
        if (n.kind === 'pirate' && Math.hypot(n.x - state.x, n.y - state.y) > 380) return;
        pill(c, n.kind === 'boss' ? '💀 Gristle' : '☠️ Pirates', sx(n.x), sy(n.y) - 30, {font: '700 11px system-ui, sans-serif', h: 18, bg: 'rgba(24,18,16,.9)', ink: '#fff', line: 'rgba(255,255,255,.5)'});
      });
    }
    m.exits.forEach(function (e) {
      var r = e.rect, arrow = r[0] <= 0 && r[3] > r[2] ? '← ' : r[0] + r[2] >= m.w && r[3] > r[2] ? '→ ' : r[1] <= 0 ? '↑ ' : '↓ ';
      var x = clamp(sx(e.at[0]), 90, T.cw - 90), y = clamp(sy(e.at[1]), 16, T.ch - 16);
      if (!chart && (Math.abs(sx(e.at[0]) - x) > 260 || Math.abs(sy(e.at[1]) - y) > 260)) return;
      pill(c, arrow + MAPS[e.to].short, x, y, {font: '700 ' + (chart ? 11 : 12) + 'px system-ui, sans-serif', h: chart ? 18 : 22, bg: 'rgba(20,60,70,.9)', ink: '#fff', line: 'rgba(255,255,255,.6)'});
    });
  }

  var lastFrame = 0;
  function frame(ts) {
    var dt = Math.min(0.05, Math.max(0, (ts - lastFrame) / 1000));
    lastFrame = ts;
    if (state) {
      var was = paused();
      step(dt);
      if (!was || needRender) {
        var c2 = camTarget();
        if (calm() || was) { view.cx = c2[0]; view.cy = c2[1]; }
        else { var kk = Math.min(1, dt * 5); view.cx += (c2[0] - view.cx) * kk; view.cy += (c2[1] - view.cy) * kk; }
        var s = view.s;
        drawWorld(ctx, curMap(), {a: view.dpr * s, e: view.dpr * (view.w / 2 - view.cx * s), f: view.dpr * (view.h / 2 - view.cy * s), dpr: view.dpr, cw: view.w, ch: view.h}, {});
        needRender = false;
      }
      if (started) updateHud();
    }
    requestAnimationFrame(frame);
  }

  var hudCache = {};
  function setText(id, v) { if (hudCache[id] !== v) { hudCache[id] = v; $(id).textContent = v; } }
  function updateHud() {
    setText('h-gold', fmt(state.gold));
    setText('h-hold', cargoCount() + '/' + capacity());
    setText('h-hull', state.hull + '/' + hullMax());
    setText('h-lvl', String(level()));
    setText('h-day', String(day()));
    setText('h-rank', rank());
    setText('h-sea', MAPS[state.map].short);
    var bz = boost(), bt = bz ? bz.name + ', ' + boostLeft() + ' ' + plural(boostLeft(), 'day') : '';
    if (hudCache.buff !== bt) { hudCache.buff = bt; $('h-buff').textContent = bt; $('h-buff-li').hidden = !bt; }
    var low = state.hull < hullMax() * 0.35, pts = state.pts > 0;
    if (hudCache.low !== low) { hudCache.low = low; $('h-hull').parentNode.classList.toggle('low', low); }
    if (hudCache.pts !== pts) { hudCache.pts = pts; $('h-pts').hidden = !pts; $('log-pip').hidden = !pts; }
  }

  /* ---------- starting, continuing, starting over ---------- */
  function begin(fresh, saved) {
    fogs = {}; npcs = {}; floaters = {}; auto = null; wake = []; keys = {}; actionKey = ''; lastWhereKey = ''; justLeft = null;
    state = fresh ? newState() : fromSave(saved);
    if (!fresh && state.fog) for (var mid in state.fog) if (MAPS[mid]) decodeFog(mid, state.fog[mid]);
    var m = enterMap(state.map);
    if (E.shipBlocked(m, state.x, state.y)) { var f = E.nearestFreePoint(m, state.x, state.y); state.x = f[0]; state.y = f[1]; }
    reveal(state.map, state.x, state.y, REVEAL);
    Object.keys(state.known).forEach(function (pid) { if (PORTS[pid]) reveal(PORTS[pid].map, PORTS[pid].dock[0], PORTS[pid].dock[1], 110); });
    started = true;
    levelUp = 0; evClock = 70 + Math.random() * 30; evRecent = []; lastPortEv = -999; hudCache = {}; mendAcc = 0;
    $('title-screen').hidden = true;
    $('hud').hidden = false; $('tools').hidden = false;
    resize();
    updateHud();
    updateWhere();
    try { $('game').scrollIntoView({block: 'start', behavior: calm() ? 'auto' : 'smooth'}); } catch (er) { /* old browsers */ }
    if (fresh) {
      track('new-game');
      save();
      note('🏴‍☠️ Ahoy, Captain!', 'You’ve just spent your last coins on a leaky little sloop called the Lucky Leaf, plus one parrot of questionable loyalty: ' + D.PARROT + '.\n\n' +
        'The plan: buy cheap where it grows, sell dear where it doesn’t, pillage the odd fat merchantman and maybe, just maybe, dig up Captain Ines Featherstone’s legendary Emerald Bale.\n\n' +
        'Start at the Leaky Lantern tavern here in Tortuga. Mama Ruthie hears everything.', null, function () { dock('tortuga'); });
    } else if (state.docked) {
      openPort(state.docked, 'market');
    } else {
      say('Welcome back, Captain. Your voyage continues on day ' + day() + '.');
      focusSea();
    }
  }
  function showTitle() {
    var saved = loadSaved(), cont = $('btn-continue');
    if (saved) {
      var s = fromSave(saved);
      cont.hidden = false;
      $('continue-note').textContent = 'Level ' + E.levelOf(s.xp) + ' · Day ' + E.dayOf(s.dist) + ' · ' + fmt(s.gold) + ' doubloons · ' + MAPS[s.map].name;
      $('btn-new').textContent = 'New voyage';
    } else {
      cont.hidden = true;
      $('continue-note').textContent = '';
      $('btn-new').textContent = 'Set sail';
    }
    $('title-screen').hidden = false;
    $('hud').hidden = true; $('tools').hidden = true;
    if (!state) {
      state = newState();
      enterMap(state.map);
      reveal(state.map, state.x, state.y, 520);
      resize();
    }
  }

  /* ---------- wiring ---------- */
  function wire() {
    $('btn-new').addEventListener('click', function () {
      if (loadSaved()) { $('title-confirm').hidden = false; $('btn-confirm-new').focus(); return; }
      begin(true);
    });
    $('btn-confirm-new').addEventListener('click', function () { $('title-confirm').hidden = true; begin(true); });
    $('btn-keep').addEventListener('click', function () { $('title-confirm').hidden = true; $('btn-continue').focus(); });
    $('btn-continue').addEventListener('click', function () { var s = loadSaved(); if (s) begin(false, s); else begin(true); });

    $('action').addEventListener('click', function () { doAction(); });
    $('btn-chart').addEventListener('click', function () { if (started) openChart(); });
    $('btn-log').addEventListener('click', function () { if (started) openLog(); });
    $('btn-settings').addEventListener('click', function () {
      $('opt-sound').checked = !!prefs.sound;
      $('opt-motion').checked = calm();
      $('opt-fast').checked = !!prefs.fast;
      $('settings-confirm').hidden = true;
      openDialog($('dlg-settings'), $('opt-sound'));
    });
    $('opt-sound').addEventListener('change', function () { prefs.sound = this.checked; savePrefs(); sfx('coin'); });
    $('opt-motion').addEventListener('change', function () { prefs.motion = this.checked; savePrefs(); wake = []; });
    $('opt-fast').addEventListener('change', function () { prefs.fast = this.checked; savePrefs(); });
    $('opt-new').addEventListener('click', function () { $('settings-confirm').hidden = false; $('opt-new-yes').focus(); });
    $('opt-new-no').addEventListener('click', function () { $('settings-confirm').hidden = true; $('opt-new').focus(); });
    $('opt-new-yes').addEventListener('click', function () {
      closeDialog('dlg-settings');
      try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* ignore */ }
      begin(true);
    });

    Array.prototype.forEach.call(document.querySelectorAll('[data-close]'), function (b) {
      b.addEventListener('click', function () { closeDialog(b.closest('dialog')); });
    });
    $('note-ok').addEventListener('click', function () { closeDialog('dlg-note'); });
    $('set-sail').addEventListener('click', function () { leavePort(); });
    // The close event arrives a moment late. After a quick passage the next port is already open by then, so leave it be.
    $('dlg-port').addEventListener('close', function () { if (state && state.docked && !$('dlg-port').open) leavePort(); });
    $('dlg-note').addEventListener('close', function () { var f = noteDone; noteDone = null; if (f) f(); else focusSea(); });
    $('dlg-encounter').addEventListener('cancel', function (e) { e.preventDefault(); });
    ['dlg-chart', 'dlg-log', 'dlg-settings', 'dlg-encounter'].forEach(function (id) {
      $(id).addEventListener('close', function () { setTimeout(focusSea, 0); });
    });
    $('chart-canvas').addEventListener('click', chartClick);
    $('port-tabs').addEventListener('keydown', function (e) {
      if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].indexOf(e.key) < 0) return;
      var tabs = Array.prototype.slice.call(this.children), i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      e.preventDefault();
      var n = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      showTab(tabs[n].dataset.tab, true);
    });

    var STEER = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'a', 's', 'd'];
    window.addEventListener('keydown', function (e) {
      if (!started || openDialogEl() || e.ctrlKey || e.metaKey || e.altKey) return;
      if (document.activeElement !== cv) return;
      var k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
      if (STEER.indexOf(k) >= 0) { keys[k] = true; e.preventDefault(); return; }
      if (k === 'Enter' || k === ' ' || k === 'e') { e.preventDefault(); doAction(); }
      else if (k === 'm' || k === 'c') { e.preventDefault(); openChart(); }
      else if (k === 'l') { e.preventDefault(); openLog(); }
    });
    window.addEventListener('keyup', function (e) { var k = e.key.length === 1 ? e.key.toLowerCase() : e.key; keys[k] = false; });
    window.addEventListener('blur', function () { keys = {}; });
    cv.addEventListener('blur', function () { keys = {}; });
    cv.addEventListener('pointerdown', function (e) {
      if (!started || state.docked || openDialogEl()) return;
      try { cv.focus({preventScroll: true}); } catch (er) { cv.focus(); }
      var r = cv.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top;
      var wx = view.cx + (px - view.w / 2) / view.s, wy = view.cy + (py - view.h / 2) / view.s, near = 34 / view.s + 8, goal = null;
      destinations(state.map).forEach(function (d) {
        if (goal || d.here || d.type === 'exit' || (d.type === 'port' && d.id === justLeft)) return;
        var p = d.type === 'port' ? PORTS[d.id] : null;
        var dd = Math.min(Math.hypot(d.x - wx, d.y - wy), p ? Math.hypot(p.town[0] - wx, p.town[1] - wy) : Infinity);
        if (dd < near) goal = d;
      });
      planRoute(goal || {type: 'point', map: state.map, x: wx, y: wy, label: 'there'});
    });
    window.addEventListener('resize', function () { if (state) resize(); });
    document.addEventListener('visibilitychange', function () { if (document.hidden) save(); });
    window.addEventListener('pagehide', save);
    if (osReduce && osReduce.addEventListener) osReduce.addEventListener('change', function () { needRender = true; });
  }

  function loadJokes() {
    if (!window.fetch) return;
    fetch('../data/jokes.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
      if (!d || !d.jokes) return;
      var n = new Date(), today = n.getFullYear() + '-' + ('0' + (n.getMonth() + 1)).slice(-2) + '-' + ('0' + n.getDate()).slice(-2);
      jokes = d.jokes.filter(function (j) { return j.approved && j.date <= today && j.text; }).map(function (j) { return j.text; });
    }).catch(function () { /* bottles fall back to tips */ });
  }

  wire();
  showTitle();
  loadJokes();
  requestAnimationFrame(frame);
  window.__pillage = {get state() { return state; }, step: step, begin: begin, dock: dock, planRoute: planRoute, openChart: openChart, encounter: encounter, tryDig: tryDig,
    npcs: function () { return npcs; }, runEvent: runEvent, giveMap: giveMap, gainXp: gainXp, events: EV,
    smoke: smoke, stats: stats, passage: passage, voyage: voyage, passageRisk: passageRisk, bestRuns: bestRuns, odds: {chanceOf: chanceOf, pct: pct, roll: roll}};
})();
