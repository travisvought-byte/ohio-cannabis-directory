/* Pillage the Reefer: the game screen, controls, ports, people and saving. */
(function () {
  'use strict';
  var D = window.PILLAGE_DATA, E = window.PILLAGE_ENGINE;
  if (!D || !E || !document.getElementById('sea')) return;
  var GOODS = D.GOODS, MAPS = D.MAPS, PORTS = D.PORTS, STASHES = D.STASHES, PEOPLE = D.PEOPLE, QUESTS = D.QUESTS, UP = D.UPGRADES;
  var SAVE_KEY = 'pillageTheReefer.v1', PREF_KEY = 'pillageTheReefer.prefs', LEGACY_KEY = 'pillageTheReefer.legacy';
  var FOG = 40, REVEAL = 190, ORDER = Object.keys(GOODS), NPORTS = Object.keys(PORTS).length;
  var EV = window.PILLAGE_EVENTS || {sea: [], port: []};
  var clamp = E.clamp, SMOKE = D.SMOKE || {};
  var STRAINS = ORDER.filter(function (g) { return !GOODS[g].kind; });
  var HIDE = D.HIDEOUT, RELICS = D.RELICS || {}, SAILS = D.SAILS || {}, FLAGS = D.FLAGS || {};
  // Contraband: the rare bales no market sells. Customs take them on sight, unless they're in the smuggler's hold.
  var CONTRABAND = ORDER.filter(function (g) { return GOODS[g].rare; });
  var SHOT_MAX = 40, SHOT_PRICE = 3, NAME_MAX = 24;
  // Round five, part two: provisions, decoys, fire ships and the law.
  var FOOD_MAX = 40, FOOD_PRICE = 2, DECOY_MAX = 2, DECOY_COST = 250, FIRE_COST = 500, FIRE_P = 0.8, LAW_BIG = 50;
  // Round five, part three: the grow at the hideout, and breeding real strains.
  var GROW = D.GROW, GENES = D.GENES || {}, CROSSES = D.CROSSES || [];
  // The MJBizCon week board: scores swapped phone to phone by QR code or link. Nothing goes to a server.
  var BOARD = D.BOARD || null, QR = window.PILLAGE_QR || null;
  // The breakout boards' stats. Set here, before the saved board is read, because reading it cleans each score's stats.
  var STATS = BOARD && BOARD.stats ? BOARD.stats : [], STAT_KEYS = STATS.map(function (S) { return S.k; });
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
  // The die stops tumbling when motion is reduced.
  function calmClass() { document.documentElement.classList.toggle('calm', calm()); }

  /* ---------- the legacy: what outlives any one ship (your hideout, earned colours and flags, the hall of fame) ---------- */
  function loadLegacy() {
    var L = {base: null, fame: [], sails: {}, flags: {}, pid: '', rivals: []};
    try {
      var s = JSON.parse(localStorage.getItem(LEGACY_KEY));
      if (s && typeof s === 'object') {
        if (s.base && typeof s.base === 'object') {
          var b = {lvl: clamp(Math.floor(s.base.lvl) || 0, 0, HIDE.caps.length - 1), gold: Math.max(0, Math.round(s.base.gold) || 0), bales: {}};
          b.basis = {};
          for (var g in (s.base.bales || {})) if (GOODS[g] && s.base.bales[g] > 0) {
            b.bales[g] = Math.floor(s.base.bales[g]);
            var bs = s.base.basis && +s.base.basis[g];
            if (bs > 0) b.basis[g] = Math.round(bs);
          }
          var gr = s.base.grow, beds = [], seeds = {};
          if (gr && typeof gr === 'object') {
            for (var gi = 0; gi < GROW.beds; gi++) {
              var bd = Array.isArray(gr.beds) && gr.beds[gi];
              beds.push(bd && GENES[bd.s] ? {s: bd.s, voy: +bd.voy || 0, ready: Math.floor(+bd.ready) || 0, x: bd.x ? 1 : 0} : null);
            }
            for (var sd in (gr.seeds || {})) if (GENES[sd]) seeds[sd] = 1;
          }
          b.grow = {beds: beds, seeds: seeds};
          L.base = b;
        }
        if (Array.isArray(s.fame)) L.fame = s.fame.filter(function (f) { return f && typeof f.captain === 'string' && typeof f.ship === 'string'; }).slice(0, 8);
        for (var sk in (s.sails || {})) if (SAILS[sk]) L.sails[sk] = 1;
        for (var fk in (s.flags || {})) if (FLAGS[fk]) L.flags[fk] = 1;
        if (typeof s.pid === 'string' && /^[a-z0-9]{6}$/.test(s.pid)) L.pid = s.pid;
        if (Array.isArray(s.rivals)) L.rivals = s.rivals.map(cleanEntry).filter(Boolean).slice(0, BOARD ? BOARD.max : 30);
      }
    } catch (e) { /* private mode or a damaged record: start fresh */ }
    return L;
  }
  var legacy = loadLegacy();
  function saveLegacy() { try { localStorage.setItem(LEGACY_KEY, JSON.stringify(legacy)); } catch (e) { /* ignore */ } }
  function cleanName(v, fallback) {
    var s = String(v || '').replace(/[\u0000-\u001f\u007f<>]/g, '').replace(/\s+/g, ' ').trim().slice(0, NAME_MAX);
    return s || fallback;
  }

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
      up: {hold: 0, hull: 0, cannons: 0, crew: 0, sails: 0, lavender: 0, secret: 0}, hull: UP.hull.levels[0], xp: 0, pts: 0,
      skill: {fight: 0, sail: 0, charm: 0}, dist: 0, hints: {}, found: {}, quests: {}, visited: {},
      known: {tortuga: 1, portroyal: 1, petitgoave: 1}, collected: {}, pillaged: 0, sunk: 0, tmap: null, dug: 0,
      flags: {}, docked: null, fog: {}, grit: 0, buff: null, seen: {},
      shot: 12, mk: {}, look: {captain: '', ship: 'the Lucky Leaf', sail: 'canvas', flag: 'skull'}, relics: {}, gentle: false, earned: 0, bricks: 0, atBase: false,
      rep: {britain: 0, spain: 0, france: 0, dutch: 0, brethren: 0}, marque: '', jobs: [], jobsTaken: {}, jobsDone: 0, bounties: 0, news: [], lastDay: 0,
      salute: {}, seed: Math.floor(Math.random() * 1e9), food: 20, decoys: 0, fireship: 0, record: {}, sold: 0, smoked: 0};
  }
  function curMap() { return MAPS[state.map]; }
  // Your ship and skills, plus whatever boost you've smoked.
  function stats() {
    var b = boost(), st;
    if (!b) st = E.stats(state);
    else {
      var k = state.skill;
      st = E.stats({up: state.up, relics: state.relics, skill: {fight: k.fight + (b.fight || 0), sail: k.sail + (b.sail || 0), charm: k.charm + (b.charm || 0)}});
      if (b.speed) st.speed *= 1 + b.speed;
    }
    if (hungry()) st.speed *= 0.8;
    return st;
  }
  // From level 2 the crew eats. With nothing left, they sail slower and do everything worse.
  function hungry() { return !!state && level() >= 2 && (state.food || 0) <= 0; }
  function relic(key) { return E.relicSum(state, key); }
  function hullMax() { return UP.hull.levels[state.up.hull] + relic('hull'); }
  function captainName() { return state.look.captain || 'A nameless captain'; }
  function shipName() { return state.look.ship || 'the Lucky Leaf'; }
  function level() { return E.levelOf(state.xp); }
  function title(lv) { return D.LEVELS[(lv || level()) - 1].title; }
  function tier() { return D.SEA_TIER[state.map] || 1; }
  function cargoCount() { var n = 0; for (var g in state.cargo) n += state.cargo[g]; return n; }
  function secretCap() { return UP.secret ? UP.secret.levels[state.up.secret || 0] : 0; }
  function capacity() { return UP.hold.levels[state.up.hold] + secretCap(); }
  // Your most valuable bales ride in the smuggler's hold. The rest is the open hold: what Customs search and pirates take.
  function openCargo() {
    var hide = Math.max(0, secretCap() - parcels()), out = {};
    Object.keys(state.cargo).sort(function (a, b) { return GOODS[b].base - GOODS[a].base; }).forEach(function (g) {
      var n = state.cargo[g], h = Math.min(hide, n);
      hide -= h;
      if (n - h > 0) out[g] = n - h;
    });
    return out;
  }
  function openCount() { var o = openCargo(), n = 0; for (var g in o) n += o[g]; return n; }
  function hiddenCount() { return cargoCount() - openCount(); }
  function openValue() { var o = openCargo(), v = 0; for (var g in o) v += o[g] * GOODS[g].base; return v; }
  function contrabandIn(o) { return CONTRABAND.filter(function (g) { return o[g] > 0; }); }
  function space() { return Math.max(0, capacity() - cargoCount() - jobLoad()); }
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
    state.earned += n * price;
    state.sold = (state.sold || 0) + n;
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
  // Every check is a roll of a twenty-sided die. A 50% chance means you need 11 or more; each 5% is one face of the die.
  function edge() { var b = boost(); return Math.min(0.3, 0.1 * (state.grit || 0)) + ((b && b.luck) || 0) + relic('luck') - (hungry() ? 0.1 : 0); }
  function chanceOf(p) { return Math.round(clamp(p + edge(), 0.05, 0.95) * 20) * 5; }
  function pct(p) { var c = chanceOf(p); return '🎲 ' + E.need(c) + '+, ' + c + '%'; }
  var lastRoll = null;
  function roll(p) {
    var nd = E.need(chanceOf(p)), d = 1 + Math.floor(Math.random() * 20), ok = d >= nd;
    state.grit = ok ? 0 : Math.min(3, (state.grit || 0) + 1);
    lastRoll = {d: d, need: nd, ok: ok};
    return ok;
  }
  // The roll, in words, for the top of an outcome. A natural 20 earns a little renown on top.
  function rollText(r) {
    if (!r) return '';
    if (r.d === 20) return '🎲 A natural 20!' + gainXp(10) + ' ';
    return '🎲 You rolled ' + r.d + ' (needed ' + r.need + '+). ';
  }
  function dieBadge(r) {
    var d = el('span', {class: 'die ' + (r.ok ? 'hit' : 'miss'), 'aria-hidden': 'true'}, String(r.d));
    return d;
  }
  function edgeHint() {
    var b = boost(), parts = [], lk = relic('luck');
    if (state.grit) parts.push('+' + Math.min(30, 10 * state.grit) + '% second wind after ' + ['a miss', 'two misses', 'three misses'][Math.min(3, state.grit) - 1]);
    if (b && b.luck) parts.push('+' + Math.round(b.luck * 100) + '% from your ' + b.name);
    if (lk) parts.push('+' + Math.round(lk * 100) + '% from your ' + RELICS.doubloon.name);
    var out = parts.length ? '🍀 Already counted in these odds: ' + andList(parts) + '.' : '';
    if (hungry()) out += (out ? ' ' : '') + '🍞 Your crew is hungry: −10% on every roll until you buy provisions.';
    return out;
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
    state.smoked = (state.smoked || 0) + 1;
    state.buff = {g: g, until: Math.round(state.dist) + 900 * boostDays(S)};
    mendAcc = 0;
    sfx('pickup');
    track('smoke');
    var munch = '';
    if (level() >= 2) {
      var ate = Math.min(2, state.food);
      state.food -= ate;
      munch = ate ? ' The munchies hit: the crew eats ' + ate + ' ' + plural(ate, 'day') + ' of provisions.' + (state.food ? '' : ' That was the last of the food.') : ' The munchies hit, and there’s nothing left to eat.';
    }
    say('🔥 You ' + (verb(g) === 'eat' ? 'pass round a crate of ' : 'light up a bale of ') + GOODS[g].name + '. ' + S.flavor + ' Boost: ' + S.name + ', about ' + boostDays(S) + ' days of sailing. ' + S.does +
      (had && had !== S ? ' It replaces ' + had.name + '.' : '') + munch);
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
  // A port, or your hideout: anywhere a quick passage can take you.
  function place(id) { return id === 'hideout' ? {name: HIDE.name, map: HIDE.map, dock: HIDE.dock} : PORTS[id]; }
  function baseKnown() { return !!(legacy.base || state.flags.baseKnown); }
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
        if (typeof s[k] === 'object') b[k] = k === 'up' || k === 'skill' || k === 'look' || k === 'rep' ? Object.assign(b[k], s[k]) : s[k];
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
    if (typeof b.relics !== 'object' || Array.isArray(b.relics)) b.relics = {};
    for (var rl in b.relics) if (!RELICS[rl]) delete b.relics[rl];
    b.hull = clamp(Math.round(b.hull) || 1, 1, E.stats(b).hullMax);
    // A voyage saved before ships could sink keeps its gentle seas: nobody signed up for that.
    if (s.gentle === undefined) b.gentle = true;
    b.shot = s.shot === undefined ? 12 : clamp(Math.floor(b.shot) || 0, 0, SHOT_MAX);
    b.earned = Math.max(0, Math.round(b.earned) || 0);
    b.bricks = Math.max(0, Math.floor(b.bricks) || 0);
    // Bales sold and smoked are counted from November 26, 2026, for the breakout boards.
    b.sold = Math.max(0, Math.floor(b.sold) || 0);
    b.smoked = Math.max(0, Math.floor(b.smoked) || 0);
    if (typeof b.mk !== 'object' || Array.isArray(b.mk)) b.mk = {};
    for (var mp in b.mk) { var M = b.mk[mp]; if (!PORTS[mp] || !M || typeof M.st !== 'object' || typeof M.b !== 'object' || typeof M.s !== 'object') delete b.mk[mp]; }
    var L = b.look;
    L.captain = cleanName(L.captain, '');
    L.ship = cleanName(L.ship, 'the Lucky Leaf');
    if (!SAILS[L.sail] || (SAILS[L.sail].earn && !legacy.sails[L.sail])) L.sail = 'canvas';
    if (!FLAGS[L.flag] || (FLAGS[L.flag].earn && !legacy.flags[L.flag])) L.flag = 'skull';
    b.atBase = !!(b.atBase && legacy.base);
    if (b.atBase) b.docked = null;
    if (b.tmap && !(MAPS[b.tmap.map] && b.tmap.at)) b.tmap = null;
    // A voyage saved before the charts followed the real coastlines (November 26, 2026). Its positions point at the
    // old hand-drawn shapes, so the ship moves to the port it was nearest, the fog starts fresh (ports you know stay
    // marked) and a treasure map is redrawn on the new chart.
    if (!b.flags.geo) {
      b.flags.geo = 1;
      b.fog = {};
      var OLD = {tortuga: [1000, 302], portroyal: [545, 832], petitgoave: [985, 598], havana: [385, 746], nassau: [1132, 300], staugustine: [482, 75],
        cartagena: [500, 758], portobelo: [180, 724], willemstad: [1196, 502], veracruz: [322, 790], barbados: [1362, 800]};
      var at = b.docked ? PORTS[b.docked].dock : b.atBase ? HIDE.dock : null, bd = Infinity;
      if (!at) for (var op in OLD) if (PORTS[op].map === b.map && Math.hypot(OLD[op][0] - b.x, OLD[op][1] - b.y) < bd) { bd = Math.hypot(OLD[op][0] - b.x, OLD[op][1] - b.y); at = PORTS[op].dock; }
      if (!at) { b.map = 'windward'; at = PORTS.tortuga.dock; }
      b.x = at[0]; b.y = at[1];
      if (b.tmap) b.tmap.redraw = 1;
    }
    if (b.buff && !(SMOKE[b.buff.g] && b.buff.until > 0)) b.buff = null;
    b.grit = clamp(Math.floor(b.grit) || 0, 0, 3);
    if (typeof b.seen !== 'object' || Array.isArray(b.seen)) b.seen = {};
    for (var sp in b.seen) if (!PORTS[sp] || !b.seen[sp] || typeof b.seen[sp].s !== 'object') delete b.seen[sp];
    // Round five: standing with each nation, jobs, letters of marque and harbour news. Older voyages start neutral with everyone.
    for (var rk in b.rep) if (!D.NATIONS[rk]) delete b.rep[rk]; else b.rep[rk] = clamp(Math.round(b.rep[rk]) || 0, -100, 100);
    if (!D.NATIONS[b.marque] || !(D.WAR[b.marque] || []).length) b.marque = '';
    function okJob(j) {
      if (!j || typeof j !== 'object' || typeof j.id !== 'string' || !D.NATIONS[j.by] || !PORTS[j.from] || !(j.pay > 0) || !(j.due > 0) || !(j.n > 0 || j.kind === 'bounty')) return false;
      if (j.kind === 'deliver' || j.kind === 'smuggle') return !!PORTS[j.to] && typeof j.what === 'string';
      if (j.kind === 'supply') return !!GOODS[j.g];
      return j.kind === 'bounty' && !!MAPS[j.sea] && j.tier >= 1 && j.tier <= 5 && typeof j.captain === 'string' && typeof j.ship === 'string';
    }
    b.jobs = Array.isArray(b.jobs) ? b.jobs.filter(okJob).slice(0, 3) : [];
    if (typeof b.jobsTaken !== 'object' || Array.isArray(b.jobsTaken)) b.jobsTaken = {};
    b.news = Array.isArray(b.news) ? b.news.filter(function (x) {
      return x && typeof x.text === 'string' && x.until > 0 && (x.kind === 'spike' || x.kind === 'glut' ? PORTS[x.pid] && GOODS[x.g] && x.mult > 0 : (x.kind === 'crack' || x.kind === 'raid') && MAPS[x.sea]);
    }).slice(0, 3) : [];
    if (typeof b.salute !== 'object' || Array.isArray(b.salute)) b.salute = {};
    b.jobsDone = Math.max(0, Math.floor(b.jobsDone) || 0);
    b.bounties = Math.max(0, Math.floor(b.bounties) || 0);
    b.lastDay = Math.max(0, Math.floor(b.lastDay) || 0);
    b.food = s.food === undefined ? 20 : clamp(Math.floor(b.food) || 0, 0, FOOD_MAX);
    b.decoys = clamp(Math.floor(b.decoys) || 0, 0, DECOY_MAX);
    b.fireship = b.fireship ? 1 : 0;
    if (typeof b.record !== 'object' || Array.isArray(b.record)) b.record = {};
    for (var rc in b.record) { var R = b.record[rc]; if (!D.NATIONS[rc] || !R || !(R.n > 0) || !(R.d > 0)) delete b.record[rc]; }
    return b;
  }

  /* ---------- seas, ships and floating cargo ---------- */
  function enterMap(mid) {
    var m = E.prepareMap(mid);
    if (!m.draw) {
      m.draw = m.polys.map(function (p) {
        var path = new Path2D(), inner = new Path2D(), c = p.c, L = p.land;
        p.pts.forEach(function (q, i) {
          if (i) path.lineTo(q[0], q[1]); else path.moveTo(q[0], q[1]);
          if (L.coast) return;
          var x = c[0] + (q[0] - c[0]) * 0.55, y = c[1] + (q[1] - c[1]) * 0.55;
          if (i) inner.lineTo(x, y); else inner.moveTo(x, y);
        });
        path.closePath(); inner.closePath();
        // A real coastline brings its own darker inland, a set distance in from the shore.
        if (L.coast) {
          (L.inner || []).forEach(function (r) { r.forEach(function (q, i) { if (i) inner.lineTo(q[0], q[1]); else inner.moveTo(q[0], q[1]); }); inner.closePath(); });
          return {path: path, inner: L.inner ? inner : null, land: L};
        }
        var size = Math.min(p.bb.x1 - p.bb.x0, p.bb.y1 - p.bb.y0);
        return {path: path, inner: size > 36 ? inner : null, land: L};
      });
    }
    if (!npcs[mid]) {
      npcs[mid] = m.patrols.map(function (p) {
        var s = E.nearestFreePoint(m, p.route[0][0], p.route[0][1]);
        var nat = p.kind === 'customs' ? lawOf(mid) : pick(D.SEA_TRADE[mid] || ['britain']);
        return {kind: p.kind, nation: nat, tier: D.SEA_TIER[mid] || 1, route: p.route, leg: 0, path: null, pi: 0, x: s[0], y: s[1], angle: 0, cool: 8, chase: false, looted: false,
          name: pick(p.kind === 'customs' ? D.NATIONS[nat].officers : D.MERCHANT_NAMES)};
      });
      for (var k = 0; k < (D.PIRATE_COUNT[mid] || 0); k++) npcs[mid].push(makePirate(m));
      (D.SEA_NAVY[mid] || []).forEach(function (nat) { npcs[mid].push(makeNavy(m, nat)); });
    }
    if (state) ensureBounties(mid);
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
    if (n.kind === 'pirate' && !n.bounty) { n.captain = pick(D.PIRATE_CAPTAINS); n.name = pick(D.PIRATE_SHIPS); n.tier = pirateTier(m.id); }
    if (n.kind === 'navy') { n.captain = pick(D.NATIONS[n.nation].captains); n.name = pick(D.NATIONS[n.nation].ships); }
    return n;
  }
  // Rougher seas and a bigger reputation bring bigger pirates, and the dice decide the rest. New captains only meet sloops and brigantines.
  function pirateTier(mid) { return E.pirateTier(D.SEA_TIER[mid] || 1, level(), Math.random(), day() <= 3 || level() < 3); }
  function shipClass(n) {
    if (n.kind === 'navy') return D.NAVY_CLASS[clamp(n.tier || 3, 3, 5) - 3];
    return n.kind === 'boss' ? 'flagship' : n.kind === 'pirate' ? (D.SHIP_CLASS[(n.tier || 1) - 1] || 'sloop') : 'merchantman';
  }
  function makePirate(m) { return pirateShip(m, {kind: 'pirate', tier: 1, cool: 10}); }
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
    else if (g.type === 'base') enterBase();
    else if (g.type === 'stash' || g.type === 'tmap') tryDig(g.id);
  }
  function transition(exit, goal) {
    goal = goal || (auto && auto.goal);
    auto = null;
    // You come out on the next sea at the same real spot you sailed off this one.
    var a = E.crossing(state.map, exit, state.x, state.y), m = enterMap(exit.to);
    var f = E.nearestFreePoint(m, a[0], a[1]);
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
    var jobs = settleJobs(pid);
    if (jobs) msg += ' ' + jobs;
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
    var worn = boostTick(moved), news = dayTick();
    if (worn || news) say(((worn || '') + ' ' + (news || '')).trim());
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
    if (timers.reveal <= 0) { timers.reveal = 0.2; var bs = boost(); reveal(state.map, state.x, state.y, REVEAL * ((bs && bs.sight) || 1) * (state.relics.spyglass ? RELICS.spyglass.sight : 1)); }

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
    var list = npcs[state.map], hasCargo = openCount() > 0 || openParcels() > 0, safe = !!nearPort(state.x, state.y, 170), weak = state.hull < hullMax() * 0.35;
    var bz = boost(), calmed = !!(bz && bz.calm), honoured = standOf('brethren') === 4, crack = seaNews('crack', m.id);
    maybeBoss(m, list);
    for (var i = 0; i < list.length; i++) {
      // Small pirates leave alone a captain the Brethren honour, unless there's a price on their head.
      var n = list[i], raider = n.kind === 'pirate', scared = raider && ((state.relics.flag && n.tier <= RELICS.flag.scare) || (honoured && !n.bounty && n.tier <= 2));
      var navy = n.kind === 'navy', hostile = navy && standOf(n.nation) <= 1;
      if (n.cool > 0) n.cool -= dt;
      if (n.looted && n.cool <= 0) { n.looted = false; n.name = pick(D.MERCHANT_NAMES); n.nation = pick(D.SEA_TRADE[m.id] || ['britain']); }
      if (n.gone) { if (n.cool <= 0) pirateShip(m, n); continue; }
      var d = Math.hypot(n.x - state.x, n.y - state.y), tx, ty, chase = false;
      var sp = n.kind === 'customs' ? 78 : n.kind === 'merchant' ? 48 : navy ? 60 : 64;
      if (n.kind === 'customs') {
        // A nation that dislikes you has its customs sniffing harder, and a crackdown more so.
        var nose = 210 * noseFactor() * stand(n.nation || lawOf(m.id)).law * (crack ? 1.4 : 1);
        chase = n.cool <= 0 && hasCargo && d < nose && E.walkable(m, [n.x, n.y], [state.x, state.y]);
        if (chase && !n.chase) parrot('customs', 'Blue sails! Blue sails! Customs! Squawk!', false, 30);
      } else if (raider) {
        // Pirates leave you be near a port's guns, and don't bother with a ship that's already battered.
        // Small pirates that see Gristle's flag on your mast want nothing to do with you.
        chase = n.cool <= 0 && !safe && !weak && !calmed && !scared && d < 240 && E.walkable(m, [n.x, n.y], [state.x, state.y]);
        if (chase && !n.chase) parrot('pirate', 'Black sails! A pirate ' + shipClass(n) + '! ' + DANGER[dangerOf(n)] + '! Squawk!', false, 30);
      } else if (navy) {
        // Warships come for a captain their nation is wary of, port guns or no port guns.
        chase = n.cool <= 0 && hostile && d < 260 && E.walkable(m, [n.x, n.y], [state.x, state.y]);
        if (chase && !n.chase) parrot('navy', 'A ' + NAT[n.nation].adj + ' ' + shipClass(n) + '! ' + cap(NAT[n.nation].short) + ' wants a word! ' + DANGER[dangerOf(n)] + '! Squawk!', false, 30);
      } else if (n.kind === 'boss' && d < 320) {
        // Gristle never chases: you pick the moment by sailing into him.
        parrot('boss', 'Red trim! That’s Gristle! ' + DANGER[dangerOf(n)] + '! Sail into him when you’re ready. Squawk!', false, 90);
      }
      if (!chase && n.chase) n.path = null;
      n.chase = chase;
      if (chase) { tx = state.x; ty = state.y; sp = n.kind === 'customs' ? 84 : navy ? 82 : 80 + 6 * n.tier; }
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
      if (d < 26 && grace <= 0 && n.cool <= 0 && !(n.kind === 'merchant' && n.looted) && !(raider && (safe || weak || calmed || scared)) && !(navy && !hostile && level() < 2)) { encounter(n); return; }
    }
  }

  /* ---------- the context button: dock or dig ---------- */
  function updateAction() {
    var a = null, mid = state.map, jl = justLeft && place(justLeft);
    if (jl && (jl.map !== mid || Math.hypot(jl.dock[0] - state.x, jl.dock[1] - state.y) > 75)) justLeft = null;
    if (HIDE.map === mid && justLeft !== 'hideout' && baseKnown() && Math.hypot(HIDE.dock[0] - state.x, HIDE.dock[1] - state.y) < 55) {
      a = {kind: 'base', id: 'hideout', label: legacy.base ? '🏚️ Enter your hideout' : '🔒 Try the cave door'};
    }
    for (var pid in PORTS) {
      var p = PORTS[pid];
      if (!a && pid !== justLeft && p.map === mid && Math.hypot(p.dock[0] - state.x, p.dock[1] - state.y) < 55) { a = {kind: 'dock', id: pid, label: '⚓ Dock at ' + p.name}; break; }
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
    else if (action.kind === 'base') enterBase();
    else if (action.kind === 'dig') tryDig(action.id);
  }

  function seenSea(mid) {
    return mid === state.map || !!state.flags['seen_' + mid] || Object.keys(PORTS).some(function (p) { return PORTS[p].map === mid && state.visited[p]; });
  }
  // A treasure map points at a small island in a sea you know. One map at a time keeps it simple.
  function giveMap() {
    if (state.tmap) return null;
    var mid = Math.random() < 0.6 ? state.map : pick(Object.keys(MAPS).filter(seenSea)), spots = mapSpots(mid);
    if (!spots.length) return null;
    var sp = pick(spots);
    state.tmap = {map: mid, at: sp.at, name: sp.name, tier: D.SEA_TIER[mid] || 1};
    reveal(mid, sp.at[0], sp.at[1], 120);
    return '🗺️ It shows treasure buried on ' + sp.name + (mid === state.map ? '' : ', over in ' + MAPS[mid].name) + '. It’s marked on your chart.';
  }
  // A treasure map drawn before the charts followed the real coastlines: the same island if it's on the new chart,
  // otherwise another little island on the same sea.
  function redrawMap() {
    var tm = state.tmap, spots = mapSpots(tm.map), same = spots.filter(function (sp) { return sp.name === tm.name; });
    var sp = same[0] || (spots.length ? pick(spots) : null);
    state.tmap = sp ? {map: tm.map, at: sp.at, name: sp.name, tier: tm.tier || D.SEA_TIER[tm.map] || 1} : null;
    if (sp) reveal(tm.map, sp.at[0], sp.at[1], 120);
  }
  // The little islands of a sea where treasure can be buried: clear of ports and the big dig sites, and close enough to dig from a ship.
  function mapSpots(mid) {
    var m = enterMap(mid), spots = [];
    m.lands.forEach(function (L) {
      if (!L.blob || L.haze || Math.max(L.blob[2], L.blob[3]) > 32) return;
      var at = [L.blob[0], L.blob[1]];
      if (nearPort(at[0], at[1], 150, mid)) return;
      if (Object.keys(STASHES).some(function (k) { var s = STASHES[k]; return s.map === mid && Math.hypot(s.at[0] - at[0], s.at[1] - at[1]) < 60; })) return;
      var f = E.nearestFreePoint(m, at[0], at[1]);
      if (Math.hypot(f[0] - at[0], f[1] - at[1]) > 55) return;
      spots.push({name: L.name, at: at});
    });
    return spots;
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
      text += '\n\nThe three pieces fit together. In the middle, circled twice: Serrana Bank, a few lonely cays out in the open sea north of the Spanish Main. It’s on your chart now.';
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
  // Only the open hold: what rides in the smuggler's hold is never found.
  function confiscate(frac) {
    var o = openCargo(), n = 0;
    for (var g0 in o) n += o[g0];
    var want = n ? Math.max(1, Math.round(n * frac)) : 0, total = 0;
    while (total < want) {
      var big = null;
      for (var g in o) if (o[g] > 0 && (!big || o[g] > o[big])) big = g;
      if (!big) break;
      takeCargo(big, 1); o[big]--; total++;
    }
    return total;
  }
  // Customs take every contraband bale they can see.
  function seizeContraband() {
    var o = openCargo(), got = [], op = openParcels();
    contrabandIn(o).forEach(function (g) { takeCargo(g, o[g]); got.push(baleWord(o[g]) + ' of ' + GOODS[g].name); });
    var msg = got.length ? ' They also seize ' + andList(got) + ': contraband, no questions asked.' : '';
    // Sealed parcels in plain sight: they take the lot, and the smuggling job is over.
    if (op) {
      var lost = state.jobs.filter(function (j) { return j.kind === 'smuggle'; });
      state.jobs = state.jobs.filter(function (j) { return j.kind !== 'smuggle'; });
      msg += ' They find your sealed parcels too and cart them off. ' + (lost.length > 1 ? 'Those smuggling jobs are' : 'That smuggling job is') + ' lost.';
    }
    return msg;
  }
  /* The law. Caught with a small haul: a warning the first time, then a fine. Caught with a big one: jail. */
  var pendingJail = null;
  function bigHaul() { return openCount() + openParcels() >= LAW_BIG; }
  function decoysLeft() { return state.decoys ? ' You have ' + state.decoys + ' ' + plural(state.decoys, 'decoy') + ' left.' : ' That was your last decoy.'; }
  function offences(k) { var r = state.record[k]; return r && day() - r.d <= 30 ? r.n : 0; }
  function booked(k) { var before = offences(k); state.record[k] = {n: before + 1, d: day()}; return before; }
  function warnOrFine(k) {
    if (!booked(k)) return ' It’s your first offence with ' + NAT[k].short + ', so they let you off with a warning. Next time there’ll be a fine.';
    var fine = Math.min(state.gold, Math.max(25, Math.round(state.gold * 0.1)));
    state.gold -= fine;
    return fine ? ' They’ve caught you before, so there’s a fine as well: ' + fmt(fine) + ' doubloons.' : '';
  }
  // Jail: they take the whole open hold and half your gold, then lock you up for a few days. It happens when the encounter closes.
  function jailText(k, lead) {
    var N = NAT[k], seen = openCount() + openParcels(), big = seen >= LAW_BIG, sz = seizeContraband(), o = openCargo(), lostN = 0;
    for (var g in o) { takeCargo(g, o[g]); lostN += o[g]; }
    var fine = Math.floor(state.gold / 2), days = big ? 5 : 3;
    state.gold -= fine;
    booked(k);
    state.rep[k] = big ? Math.min(repOf(k), -80) : -40;
    if (state.marque === k) state.marque = '';
    pendingJail = {k: k, days: days};
    sfx('bad'); track('jail');
    return lead + ' ⛓️ ' + (big ? 'With ' + baleWord(seen) + ' in plain sight, this is no fine.' : cap(N.short) + ' counts you an enemy, so this is no fine.') + ' ' + cap(N.law) + ' impounds ' +
      (lostN ? 'your whole open hold, ' + baleWord(lostN) + ',' : 'everything they can find') + ' takes ' + fmt(fine) + ' doubloons in fines and court costs, and locks you up for ' + days + ' days.' + sz +
      (hiddenCount() ? ' They never find your smuggler’s hold.' : '') +
      (big ? ' ' + cap(N.short) + ' now counts you a public enemy, and its warships will be hunting you for weeks.' : ' Once you’re out, ' + N.short + ' will still be wary of you.');
  }
  // Arrested by a warship: a big haul or bad blood means jail, otherwise a stiff fine.
  function arrest(k, lead) {
    if (bigHaul() || standOf(k) === 0) return jailText(k, lead);
    var o = openCargo(), lostN = 0, fine = Math.floor(state.gold / 3);
    for (var g in o) { takeCargo(g, o[g]); lostN += o[g]; }
    state.gold -= fine; settle(k); booked(k);
    return lead + ' They impound ' + (lostN ? baleWord(lostN) : 'nothing from your empty hold') + (fine ? ' and fine you ' + fmt(fine) + ' doubloons' : '') + '. “Thank you for your cooperation.” Your slate with ' + NAT[k].short + ' is clean, at a price.' +
      (hiddenCount() ? ' They never find your smuggler’s hold.' : '');
  }
  // Serve the time, then walk out on the docks of the nearest port of theirs.
  function serveJail() {
    var J = pendingJail;
    pendingJail = null;
    if (!J) return;
    var ports = Object.keys(PORTS).filter(function (p) { return PORTS[p].nation === J.k; }), here = ports.filter(function (p) { return PORTS[p].map === state.map; });
    var pid = here[0] || ports[0];
    state.dist += J.days * 900;
    var worn = boostTick(J.days * 900), news = dayTick(true), lead = '⛓️ After ' + J.days + ' days on bread and water, the turnkey lets you go. It’s now day ' + day() + '.' + (worn ? ' ' + worn : '') + (news ? ' ' + news : '');
    if (!pid) { say(lead); save(); return; }
    var P = PORTS[pid], m = enterMap(P.map), f = E.nearestFreePoint(m, P.dock[0], P.dock[1]);
    auto = null; ship.vx = ship.vy = 0; wake = []; keys = {}; justLeft = null;
    state.map = P.map; state.x = f[0]; state.y = f[1];
    snapCamera(); needRender = true;
    dock(pid, lead);
  }
  function encounter(n) {
    ship.vx *= 0.2; ship.vy *= 0.2;
    keys = {};
    sfx('boom');
    if (n.kind === 'customs') customs(n);
    else if (n.kind === 'merchant') merchant(n);
    else if (n.kind === 'boss') gristle(n);
    else if (n.kind === 'navy' && standOf(n.nation) > 1) navyHail(n);
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
  function customs(n, after, lead, die) {
    // A cutter that has had its word with you leaves you alone for a good while.
    var done = function () { n.cool = 60; grace = 3; if (pendingJail) { serveJail(); return; } if (after) after(); };
    var k = n.nation || lawOf(state.map), N = NAT[k], law = N.law, LAW = cap(law), sk = standOf(k);
    n.nation = k;
    if (!openCount() && !openParcels()) {
      showEncounter('🔵 ' + LAW, hiddenCount() || parcels() ? n.name + ' of ' + law + ' pulls alongside, sniffs the air and searches your hold from bow to stern. They tap every plank except the right one. “Nothing aboard but a parrot? Carry on, Captain.”'
        : n.name + ' of ' + law + ' pulls alongside, sniffs the air and peers into your empty hold. “Nothing aboard but a parrot? Carry on, Captain.”', [{label: 'Carry on'}], done);
      return;
    }
    var st = stats(), vicar = state.flags.vicar ? 1 : 0, bg = burnPick(), op = openParcels(), hot = contrabandIn(openCargo()).length > 0 || op > 0, crack = seaNews('crack', state.map);
    // Contraband in plain sight doubles the fee, and a failed escape costs you all of it. A nation that dislikes you charges more.
    var bribe = Math.max(15, Math.round((openValue() + 40 * op) * 0.18 * (1 - 0.1 * st.charm) * (hot ? 2 : 1) * STAND[sk].bribe * (crack ? 1.5 : 1)));
    // Each way out leans on a different part of your ship and captain, so how you build your ship shows here.
    var runP = Math.min(0.95, 0.5 + 0.1 * st.sails + 0.07 * st.sail + 0.1 * vicar);
    var shotP = Math.min(0.95, 0.2 + 0.13 * st.cannons + 0.07 * st.fight);
    var talkP = Math.min(0.95, 0.35 + 0.1 * st.charm + 0.3 * vicar);
    var papersP = sk >= 4 ? 0.85 : 0.6;
    function seized() { var s = hot ? seizeContraband() : ''; return s ? s + shift(k, -5) : ''; }
    var hint = 'Your odds come from your ship and skills: sails and Sailing for running, cannons and Fighting for a warning shot, Charm for talking. ' + edgeHint() +
      (hot ? ' ⚠️ They can see contraband in your open hold: the fee is doubled, and if a check fails they take it all.' : '') +
      (STAND[sk].bribe !== 1 ? ' Your standing with ' + N.short + ' (' + STAND[sk].name + ') ' + (STAND[sk].bribe > 1 ? 'raises' : 'lowers') + ' the fee.' : '') +
      (crack ? ' 📰 There’s a crackdown on in these waters: the fee is half again as much.' : '') +
      (bigHaul() ? ' ⛓️ ' + cap(baleWord(openCount() + op)) + ' in plain sight: if a check fails, it’s jail, not a fine.' : '');
    var opts = [
      {label: '🪙 Pay a “paperwork fee” of ' + fmt(bribe) + ' doubloons', disabled: state.gold < bribe, fn: function () {
        state.gold -= bribe; sfx('coin');
        return pick([n.name + ' pockets the fee, stamps a form in triplicate and wishes you a pleasant voyage.',
          'The fee vanishes into a very large hat. “Everything appears to be in order,” says ' + n.name + ', not looking at anything.']) + shift(k, 1);
      }}
    ];
    if (sk >= 3 && !n.papers) opts.push({label: '📜 Show your papers: ' + N.short + ' counts you a friend (' + pct(papersP) + ')', next: function () {
      var ok = roll(papersP), r = lastRoll;
      n.papers = true;
      if (ok) {
        showEncounter('🔵 ' + LAW, rollText(r) + n.name + ' reads your papers, finds your name on the list of friends of ' + N.name + ', and salutes. “So sorry to trouble you, Captain.”' + gainXp(10), [], done, '', r);
        return;
      }
      customs(n, after, rollText(r) + n.name + ' reads your papers twice, hands them back and smiles. “Very nice. Now open the hold.”', r);
    }});
    opts.push(
      {label: '⛵ Run for it (' + pct(runP) + ')', fn: function () {
        if (roll(runP)) return 'You crowd on every scrap of sail and leave the cutter wallowing in your wake. Somewhere behind you, a whistle is blown very angrily.' + gainXp(10) + shift(k, -3);
        if (bigHaul()) return jailText(k, 'They catch you before you clear the reef.');
        var s = seized(), lost = confiscate(1 / 3); sfx('bad');
        return 'They catch you before you clear the reef. ' + n.name + ' confiscates ' + baleWord(lost) + ' “for evidence.”' + s + ' You hear coughing from their ship for the rest of the afternoon.' + warnOrFine(k) + shift(k, -2);
      }},
      {label: state.shot > 0 ? '💣 Fire a warning shot (' + pct(shotP) + ', costs 1 cannonball)' : '💣 Fire a warning shot (no cannonballs left)', disabled: state.shot < 1, fn: function () {
        state.shot--;
        if (roll(shotP)) return 'BOOM. The cannonball lands a polite distance from their bow. After a short meeting, the cutter decides it left the kettle on and sails home.' + gainXp(10) + shift(k, -8);
        if (bigHaul()) return jailText(k, 'BOOM. You hit their flagpole.');
        booked(k);
        var s = seized(), lost = confiscate(1 / 3), fine = Math.min(state.gold, Math.round(state.gold * 0.1));
        state.gold -= fine; sfx('bad');
        return 'BOOM. You hit their flagpole. ' + n.name + ' is furious, seizes ' + baleWord(lost) + ' and fines you ' + fmt(fine) + ' doubloons for damage to the property of ' + N.name + '.' + s + shift(k, -5);
      }},
      {label: '🗣️ Ask about their day (' + pct(talkP) + ')', fn: function () {
        if (roll(talkP)) return pick(['“Rough day?” you ask. ' + n.name + ' talks for forty minutes about a stapler. Everyone forgets about the inspection.',
          'You compliment their hat. They blush, wave you through and ask where you got your parrot.',
          'You explain it’s all for a botanist in Cartagena. Technically true. They let you go with a warning and a pamphlet.']) + gainXp(10);
        if (bigHaul()) return jailText(k, n.name + ' is not interested in your thoughts on the weather.');
        var s = seized(), lost = confiscate(0.25); sfx('bad');
        return n.name + ' is not interested in your thoughts on the weather and confiscates ' + baleWord(lost) + '.' + s + warnOrFine(k) + shift(k, -2);
      }}
    );
    if (state.decoys) opts.push({label: '🚩 Send a decoy to draw them off (always works; you lose her)', fn: function () {
      state.decoys--; track('decoy');
      return 'Your decoy sloop breaks away with every sail set, looking as guilty as a ship can look. ' + cap(n.name) + ' gives chase. Somewhere over the horizon they’ll board her and find nothing but a crew eating biscuits.' + shift(k, -3) + decoysLeft();
    }});
    if (bg) opts.push({label: '🔥 Burn a bale of ' + GOODS[bg].name + ' (' + pct(BURN_P) + ')', next: function () {
      takeCargo(bg, 1);
      var ok = roll(BURN_P), r = lastRoll;
      if (ok) {
        showEncounter('🔵 ' + LAW, rollText(r) + 'You set a bale of ' + GOODS[bg].name + ' smouldering and fan the smoke at the cutter. ' + cap(n.name) + ' breathes in, giggles at a seagull and wanders off to find a snack. Nobody remembers why they stopped you.' + gainXp(10), [], done, '', r);
        return;
      }
      sfx('bad');
      customs(n, after, rollText(r) + 'You set a bale of ' + GOODS[bg].name + ' smouldering, but the wind shifts and blows the smoke straight back over your own deck. Your crew has the giggles. ' + n.name + ' does not. “Now then. About that inspection.”', r);
    }});
    showEncounter('🔵 ' + LAW + '!', lead || n.name + ' of ' + law + ' blocks your way, flying the flag of ' + N.name + '. “Inspection! What is that smell? Is that… citrus?”', opts, done, hint, die);
  }
  function merchant(n) {
    var dz = dangerOf(n), k = n.nation || pick(D.SEA_TRADE[state.map] || ['britain']), N = NAT[k], legal = !!state.marque && atWar(state.marque, k);
    n.nation = k;
    showEncounter('🟤 A fat ' + N.adj + ' merchantman!', cap(n.name) + ' wallows alongside under the flag of ' + N.name + ', low in the water. Her crew looks nervous. Her cargo smells wonderful.', [
      {label: '⚔️ Attack her! (' + DANGER[dz].toLowerCase() + (legal ? '; fair game under your ' + NAT[state.marque].adj + ' letter of marque' : '; ' + N.short + ' won’t like it') + ')', next: function () { fight(n); }},
      {label: '👋 Wave politely', fn: function () {
        if (Math.random() < 0.25 && space() > 0) { var g = pick(D.COMMON); addCargo(g, 1); return 'The merchants wave back. Touched, they toss you a bale of ' + GOODS[g].name + ' out of pure pity.'; }
        return 'The merchants wave back. Everyone feels good about it. Nothing else happens.';
      }},
      {label: '⛵ Leave her be', fn: function () { return 'You let ' + n.name + ' waddle on. The sea is big enough for everyone.'; }}
    ], function () { if (!n.looted) n.cool = 12; grace = 3; });
  }

  /* ---------- battles: a few rounds of cannon fire, boarding or running ---------- */
  function foeName(n) { return n.kind === 'merchant' ? cap(n.name) : n.captain; }
  function toll(n) { return clamp(Math.round(state.gold * 0.08), 25 * n.tier, 200 * n.tier); }
  // Any bale makes ammunition at a pinch. Brick Weed is what it's for; otherwise the cheapest bale aboard goes in the cannon.
  function lobPick() { return state.cargo.brick > 0 ? 'brick' : burnPick(); }
  function lobFire(st, g) { return g === 'brick' && state.relics.goldbrick ? st.fire : Math.max(1, Math.round(st.fire * 0.6)); }
  function range(fire) { return Math.max(1, Math.round(fire * 0.85)) + ' to ' + Math.max(1, Math.round(fire * 1.15)); }
  // Every bale of weed that lands gets their crew a little higher: they aim worse and they're easier to board.
  function enemyFire(B) { return B.en.fire * (1 - 0.2 * (B.high || 0)); }
  function boardP(B, st) { return Math.min(0.95, E.boardChance(st, B.en, B.eh) + 0.1 * (B.high || 0)); }
  function fight(n, after) {
    var B = {n: n, en: E.foe(n.kind, n.tier), round: 0, after: after, high: 0}, intro, cls = shipClass(n);
    B.eh = B.en.hull;
    var bj = bountyOf(n);
    if (n.kind === 'boss') intro = D.BOSS.captain + ' runs out every gun on ' + n.name + ' and laughs like a broken accordion.';
    else if (n.kind === 'navy') intro = cap(n.name) + ', a ' + NAT[n.nation].adj + ' ' + cls + ', runs up her colours and opens every gun port. ' + n.captain + ' shouts across the water: “Heave to, in the name of ' + NAT[n.nation].name + '!”';
    else if (bj) intro = 'There’s the ship from the poster: ' + n.captain + ' of ' + n.name + ', a pirate ' + cls + ' wanted by ' + NAT[bj.by].short + '. Their crew runs out the guns.';
    else if (n.kind === 'pirate') intro = pick(['Black sails off the bow! ' + n.captain + ' of ' + n.name + ', a pirate ' + cls + ', runs out the guns and grins with every one of their teeth.',
      cap(n.name) + ', a pirate ' + cls + ', swings alongside, flying the skull and crossed spatulas. ' + n.captain + ' shouts: “Your cargo or your dignity!”',
      'A pirate ' + cls + ' cuts across your path. ' + n.captain + ' of ' + n.name + ' raises a cutlass and a very loud voice.']);
    else intro = 'You run out your guns. On ' + n.name + ', somebody drops a teapot.';
    if (n.kind !== 'merchant') track(n.kind === 'boss' ? 'meet-gristle' : n.kind === 'navy' ? 'navy-battle' : 'pirate-battle');
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
  function textBlock(body, text, die) {
    var row = el('div', {class: 'enc-row'});
    if (die) row.appendChild(dieBadge(die));
    row.appendChild(el('p', {id: 'enc-text'}, text.replace(/\s+/g, ' ').trim()));
    body.appendChild(row);
  }
  function renderFight(B, text, die) {
    var body = $('enc-body'), st = stats(), en = B.en, n = B.n, ef = enemyFire(B);
    $('enc-title').textContent = n.kind === 'merchant' ? '⚔️ Attacking ' + n.name : (n.kind === 'boss' ? '💀 ' : n.kind === 'navy' ? '⚓ ' : n.bounty ? '🎯 ' : '🏴‍☠️ ') + n.captain + ', ' + n.name +
      ' (' + (n.kind === 'navy' ? NAT[n.nation].adj + ' ' : '') + shipClass(n) + ')';
    body.textContent = '';
    textBlock(body, text, die);
    body.appendChild(hullBars(B));
    body.appendChild(el('p', {class: 'hint'}, '🦜 ' + D.PARROT + ' sizes them up: ' + DANGER[E.danger(st, state.hull, {fire: ef, hull: en.hull}, B.eh)].toLowerCase() + '. Every hit raises your boarding odds, and a 20 on the die doubles a shot.'));
    if (B.high) body.appendChild(el('p', {class: 'hint'}, '🌿 Their crew is ' + ['', 'a bit giggly', 'properly high', 'completely baked'][B.high] + ': their aim is ' + (20 * B.high) + '% worse and your boarding odds are ' + (10 * B.high) + '% better.'));
    // Fair warning before the shot that could end the voyage.
    if (n.kind !== 'merchant' && !state.gentle && Math.round(ef * 1.25 * 1.15) >= state.hull) {
      body.appendChild(el('p', {class: 'warn'}, '⚠️ Their next broadside could sink you, and a sunk ship ends this voyage. Running, paying or striking your colours keeps you afloat.'));
    }
    var eh = edgeHint();
    if (eh) body.appendChild(el('p', {class: 'hint'}, eh));
    var list = el('div', {class: 'choices'}), bp = boardP(B, st), fp = E.fleeChance(st, en), bg = burnPick(), lb = lobPick();
    var opts = [
      {label: state.shot > 0 ? '💣 Fire cannonballs (' + range(st.fire) + ' damage, ' + state.shot + ' left)' : '💣 Fire cannonballs (none left)', act: 'fire', disabled: state.shot < 1}
    ];
    if (lb) opts.push({label: GOODS[lb].icon + ' Lob a bale of ' + GOODS[lb].name + ' (' + range(lobFire(st, lb)) + ' damage, gets them high)', act: 'lob'});
    if (state.fireship && n.kind !== 'merchant') opts.push({label: '🔥 Send in your fire ship (' + pct(FIRE_P) + '; you lose her either way)', act: 'fireship'});
    if (state.decoys && n.kind !== 'merchant') opts.push({label: '🚩 Send a decoy to draw them off (always works; you lose her)', act: 'decoy'});
    opts.push({label: '⚔️ Board ' + (n.kind === 'merchant' ? 'her' : 'them') + ' (' + pct(bp) + ')', act: 'board'});
    opts.push({label: '⛵ Run for it (' + pct(fp) + ')', act: 'run'});
    if (n.kind === 'pirate' && bg) opts.push({label: '🔥 Burn a bale of ' + GOODS[bg].name + ' (' + pct(BURN_P) + ')', act: 'burn'});
    if (B.round === 0 && n.kind === 'pirate') opts.push({label: '🪙 Pay them to leave you alone (' + fmt(toll(n)) + ' doubloons)', act: 'pay', disabled: state.gold < toll(n)});
    if (B.round === 0 && n.kind === 'pirate' && !n.bounty && standOf('brethren') >= 3) opts.push({label: '🤝 Show the Brethren’s mark and parley (' + pct(parleyP(n)) + ')', act: 'parley'});
    if (n.kind === 'navy') opts.push({label: '🪙 Pay what you owe ' + NAT[n.nation].short + ' (' + fmt(fineOf(n.nation)) + ' doubloons, and your slate is clean)', act: 'fine', disabled: state.gold < fineOf(n.nation)});
    if (n.kind !== 'merchant') opts.push({label: '🏳️ Strike your colours (' + (n.kind !== 'navy' ? 'they take your open hold and half your gold' : bigHaul() || standOf(n.nation) === 0 ? 'jail: they take your open hold and half your gold' : 'they take your open hold and a third of your gold') + ')', act: 'strike'});
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
    var st = stats(), en = B.en, n = B.n, txt, die = null;
    B.round++;
    lastRoll = null;
    if (act === 'leave') { n.cool = 12; endFight(B, 'You think better of it and let ' + n.name + ' waddle on.'); return; }
    if (act === 'pay') {
      var cost = toll(n);
      state.gold -= cost; sfx('coin'); n.cool = 60;
      endFight(B, n.captain + ' counts the ' + fmt(cost) + ' doubloons, bites one, and waves you on your way. “Pleasure doing business.”' + (n.bounty ? '' : shift('brethren', 3)));
      return;
    }
    if (act === 'fine') {
      var owed = fineOf(n.nation);
      if (state.gold < owed) { renderFight(B, 'You turn out your pockets. It isn’t enough.'); return; }
      state.gold -= owed; settle(n.nation); sfx('coin'); n.cool = 120;
      endFight(B, n.captain + ' counts your ' + fmt(owed) + ' doubloons, writes you a receipt in triplicate and closes the gun ports. Your slate with ' + NAT[n.nation].short + ' is clean, or clean enough.');
      return;
    }
    if (act === 'strike') {
      if (n.kind === 'navy') { n.cool = 120; sfx('bad'); endFight(B, arrest(n.nation, 'You haul down your flag, and marines from ' + n.name + ' come aboard.')); return; }
      var o = openCargo(), lostN = 0, fine = Math.floor(state.gold / 2);
      for (var og in o) { takeCargo(og, o[og]); lostN += o[og]; }
      state.gold -= fine; n.cool = 90; sfx('bad');
      var after2 = n.kind === 'pirate' && !n.bounty ? shift('brethren', 2) : '';
      endFight(B, 'You haul down your flag. ' + foeName(n) + ' takes ' + (lostN ? baleWord(lostN) : 'nothing from your empty hold') + (fine ? ' and ' + fmt(fine) + ' doubloons, half your purse' : '') +
        (hiddenCount() ? ', but never finds your smuggler’s hold' : '') + '. “Pleasure doing business.” You live to sail another day.' + after2);
      return;
    }
    if (act === 'burn') {
      var bg = burnPick();
      if (bg) {
        takeCargo(bg, 1);
        if (roll(BURN_P)) {
          n.cool = 60;
          endFight(B, rollText(lastRoll) + 'You set a bale of ' + GOODS[bg].name + ' smouldering and let the breeze carry it over. On ' + n.name + ', the shouting turns to giggling. ' + n.captain + ' forgets what they were angry about and wanders off to look for snacks.' + gainXp(10), lastRoll);
          return;
        }
        die = lastRoll;
        txt = rollText(die) + 'You set a bale of ' + GOODS[bg].name + ' smouldering, but the smoke drifts the wrong way.';
      } else txt = 'You have nothing left to burn.';
    } else if (act === 'run') {
      if (roll(E.fleeChance(st, en))) {
        n.cool = 45;
        endFight(B, rollText(lastRoll) + pick(['You crowd on every scrap of sail and leave them wallowing in your wake.', 'You duck behind a reef they don’t dare cross. By the time they find a way round, you’re gone.',
          'A lucky gust fills your sails. Their curses fade behind you.']), lastRoll);
        return;
      }
      die = lastRoll;
      txt = rollText(die) + 'You try to slip away, but ' + foeName(n) + ' cuts you off.';
    } else if (act === 'parley') {
      if (roll(parleyP(n))) {
        n.cool = 60;
        endFight(B, rollText(lastRoll) + 'You show the Brethren’s mark, scratched on an old coin. ' + n.captain + ' squints at it, laughs and lowers the guns. “Any friend of Nassau. Fair winds.”' + gainXp(10), lastRoll);
        return;
      }
      die = lastRoll;
      txt = rollText(die) + n.captain + ' squints at your coin. “Never heard of you.”';
    } else if (act === 'decoy') {
      if (!state.decoys) { renderFight(B, 'You have no decoys left.'); return; }
      state.decoys--; n.cool = 90; sfx('boom'); track('decoy');
      endFight(B, 'Your decoy sloop cuts across ' + n.name + '’s bow, peppers the rigging with musket fire and runs for the horizon. ' + foeName(n) + ' takes the bait. By the time they catch her, empty and grinning, you’re long gone. Her crew will find their own way home.' + decoysLeft());
      return;
    } else if (act === 'fireship') {
      if (!state.fireship) { renderFight(B, 'You have no fire ship.'); return; }
      state.fireship = 0; track('fireship');
      if (roll(FIRE_P)) {
        if (n.kind !== 'boss') { win(B, 'fire', lastRoll); return; }
        var burnt = Math.ceil(en.hull * 0.6);
        B.eh = Math.max(0, B.eh - burnt); die = lastRoll; sfx('boom');
        txt = rollText(die) + 'Your fire ship grapples alongside ' + n.name + '. Her skeleton crew lights the fuses and rows clear, and flames race up the rigging for ' + burnt + ' damage. ' + foeName(n) + '’s crew beats the fire out, just.';
        if (B.eh <= 0) { win(B, 'fire', die); return; }
      } else {
        die = lastRoll;
        txt = rollText(die) + 'The wind backs at the last moment. Your fire ship drifts past ' + n.name + ' and burns out harmlessly. Her crew rows back, singed and sheepish.';
      }
    } else if (act === 'board') {
      if (roll(boardP(B, st))) { win(B, 'board', lastRoll); return; }
      die = lastRoll;
      txt = rollText(die) + 'Your boarders swing across and get swatted straight back into the sea.';
    } else {
      // Cannonballs or a bale of weed. The die decides how well it lands: a 20 doubles it.
      var lob = act === 'lob' ? lobPick() : null;
      if (act === 'lob' && !lob) { renderFight(B, 'You have nothing left to lob.'); return; }
      if (act === 'fire' && state.shot < 1) { renderFight(B, 'You’re out of cannonballs.'); return; }
      var d = 1 + Math.floor(Math.random() * 20), dmg = E.hit(lob ? lobFire(st, lob) : st.fire, Math.random()), crit = d === 20;
      if (crit) dmg *= 2;
      die = {d: d, need: 0, ok: true};
      B.eh = Math.max(0, B.eh - dmg);
      sfx('boom');
      if (lob) {
        takeCargo(lob, 1);
        if (lob === 'brick') state.bricks++;
        B.high = Math.min(3, (B.high || 0) + 1);
        txt = (crit ? '🎲 A natural 20: a direct hit on their galley! ' : '') + 'THWUMP! A bale of ' + GOODS[lob].name + ' bursts across their deck for ' + dmg + ' damage, and a sweet cloud rolls over their crew.';
      } else {
        state.shot--;
        txt = (crit ? '🎲 A natural 20: right through their gunport! ' : '') + 'BOOM! Your cannonballs hit for ' + dmg + '.';
      }
      if (!crit) die = null;
      if (B.eh <= 0) { win(B, 'sink', die); return; }
      if (n.kind === 'merchant' && B.eh <= en.hull * 0.35) { win(B, 'strike', die); return; }
    }
    var back = E.hit(enemyFire(B) * (act === 'board' ? 1.25 : 1), Math.random());
    state.hull = Math.max(0, state.hull - back);
    txt += ' ' + (n.kind === 'merchant' ? 'Her crew fires back' : 'They fire back') + ' for ' + back + '.';
    if (state.hull <= 0) {
      if (n.kind === 'merchant' || state.gentle) lose(B, txt, die); else sink(B, txt);
      return;
    }
    renderFight(B, txt, die);
  }
  function win(B, how, die) {
    var n = B.n, en = B.en, st = stats(), haul = {}, got = [], left = 0, gold, xp, count = 0, total = 0, note2 = '';
    if (n.kind === 'boss') { gold = D.BOSS.gold; haul = Object.assign({}, D.BOSS.loot); xp = 600; }
    else if (n.kind === 'merchant') {
      gold = Math.round((30 + Math.random() * 40) * en.tier);
      count = 3 + Math.floor(Math.random() * 4) + 2 * st.crew;
      if (Math.random() < 0.35) haul.kraken = Math.random() < 0.3 ? 2 : 1;
      xp = 12 + 10 * en.tier;
      if (state.marque && atWar(state.marque, n.nation || lawOf(state.map))) gold = Math.round(gold * 1.2);
    } else if (n.kind === 'navy') {
      gold = Math.round((80 + Math.random() * 60) * en.tier);
      count = 1 + Math.floor(Math.random() * 3) + st.crew;
      xp = 40 + 35 * en.tier;
    } else {
      gold = Math.round((60 + Math.random() * 70) * en.tier);
      count = 2 + Math.floor(Math.random() * 3) + st.crew;
      if (en.tier >= 4) haul.pearl = en.tier - 3;
      else if (Math.random() < 0.3) haul[Math.random() < 0.5 ? 'kraken' : 'mermaid'] = 1;
      xp = 30 + 30 * en.tier;
    }
    for (var h in haul) total += haul[h];
    while (total < count) { var g = pick(D.COMMON); haul[g] = (haul[g] || 0) + 1; total++; }
    // Sink her and half of it goes to the bottom. Board her and it's all yours, with a bonus on a natural 20.
    if ((how === 'sink' || how === 'fire') && n.kind !== 'boss') {
      gold = Math.round(gold / 2);
      for (var hk in haul) { haul[hk] = Math.floor(haul[hk] / 2); if (!haul[hk]) delete haul[hk]; }
      note2 = how === 'fire' ? ' Half her cargo burns with her.' : ' Half her cargo goes down with her.';
    } else if (how === 'board' && die && die.d === 20) {
      gold = Math.round(gold * 1.5);
      note2 = ' Your boarders find the captain’s secret purse as well.';
    }
    state.gold += gold;
    Object.keys(haul).forEach(function (g2) {
      var k = addCargo(g2, haul[g2]);
      if (k) got.push(baleWord(k) + ' of ' + GOODS[g2].name);
      left += haul[g2] - k;
    });
    var txt = how === 'board' ? 'With a mighty “Arrr!” your crew swings aboard. ' + (n.kind === 'merchant' ? 'The merchants surrender at once; they’re paid by the hour.' : foeName(n) + ' throws down their cutlass.')
      : how === 'strike' ? cap(n.name) + ' strikes her colours before you can fire again.'
      : how === 'fire' ? 'Your fire ship grapples alongside ' + n.name + '. Her skeleton crew lights the fuses and rows clear, and the whole lot goes up like a bonfire. ' + foeName(n) + ' and the crew jump for the boats.'
      : n.kind === 'boss' ? 'Your broadside smashes ' + n.name + '’s mainmast. ' + foeName(n) + ' surrenders.'
      : cap(n.name) + ' rolls over and sinks. ' + foeName(n) + ' and the crew row away in a very small boat.';
    txt = (die ? rollText(die) : '') + txt + note2;
    txt += ' You take ' + fmt(gold) + ' doubloons' + (got.length ? ' and ' + andList(got) : '') + '.' + (left ? ' Your hold can’t fit the other ' + baleWord(left) + '.' : '');
    if (n.kind === 'pirate' && !state.tmap && Math.random() < 0.35) { var map = giveMap(); if (map) txt += ' In the captain’s cabin you find a treasure map. ' + map; }
    if (n.kind === 'boss') txt += ' ' + D.BOSS.captain + ' is marooned on a sandbar with a hat and a coconut. Every tavern from here to Tortuga will be singing about you.';
    txt += gainXp(xp);
    var bj = bountyOf(n);
    if (n.kind === 'merchant') {
      var mk = n.nation || lawOf(state.map);
      if (state.marque && atWar(state.marque, mk)) txt += ' All legal: your ' + NAT[state.marque].adj + ' letter of marque says so.' + shift(mk, -4) + shift(state.marque, 6);
      else txt += ' ' + cap(NAT[mk].short) + ' will remember this.' + shift(mk, -12) + shift('brethren', 3);
      n.looted = true; n.cool = 60; state.pillaged++; if (state.pillaged === 1) track('first-pillage');
    } else if (n.kind === 'navy') {
      var nk = n.nation, more = Math.min(10, SHOT_MAX - state.shot);
      state.shot += more;
      if (more) txt += ' Her powder room yields ' + more + ' ' + plural(more, 'cannonball') + '.';
      txt += ' ' + cap(NAT[nk].short) + ' will not forgive this soon.' + shift(nk, -25);
      NAT_ORDER.forEach(function (e) { if (atWar(e, nk)) txt += shift(e, state.marque === e ? 10 : 6); });
      txt += shift('brethren', 6);
      state.flags.navywin = 1; n.gone = true; n.cool = 300; track('beat-navy');
    } else {
      state.sunk++;
      if (en.tier >= 4 && n.kind === 'pirate') state.flags.bigwin = 1;
      if (n.kind === 'boss') { state.flags.boss = 1; npcs[state.map].splice(npcs[state.map].indexOf(n), 1); track('beat-gristle'); }
      else if (bj) {
        bj.hit = true; removeNpc(n); track('bounty-hit');
        txt += ' That’s the ship from the ' + NAT[bj.by].adj + ' wanted poster: collect ' + fmt(bj.pay) + ' doubloons in ' + PORTS[bj.from].name + ' by day ' + bj.due + '.' + shift('brethren', -8);
      } else {
        n.gone = true; n.cool = 90; if (state.sunk === 1) track('first-pirate');
        txt += shift('brethren', -4) + shift(lawOf(state.map), 3);
      }
    }
    sfx('fanfare');
    endFight(B, txt, die);
  }
  // Gentle seas, or a merchant's mops: you limp away, poorer.
  function lose(B, txt, die) {
    var n = B.n;
    state.hull = Math.max(1, Math.ceil(hullMax() * 0.25));
    sfx('bad');
    if (n.kind === 'merchant') {
      n.cool = 30;
      txt += ' That’s enough for your poor ship. Her crew chases you off with mops and a strongly worded letter.';
    } else if (n.kind === 'navy') {
      n.cool = 120;
      txt += ' ' + arrest(n.nation, 'Your ship is beaten, and marines from ' + n.name + ' come aboard.');
    } else {
      // Taken over: they strip the open hold and nine doubloons in every ten.
      var o = openCargo(), lost = 0, fine = Math.floor(state.gold * 0.9);
      for (var og in o) { takeCargo(og, o[og]); lost += o[og]; }
      state.gold -= fine;
      n.cool = 90;
      txt += ' Your ship is beaten, and ' + foeName(n) + '’s crew swarms aboard. They take ' + (lost ? baleWord(lost) : 'nothing from your empty hold') + (fine ? ' and ' + fmt(fine) + ' doubloons, nine in every ten you had' : '') + (hiddenCount() ? ', but never find your smuggler’s hold' : '') + ', then sail off laughing.';
    }
    txt += ' Your crew patches the worst holes. Get to a port for repairs.';
    endFight(B, txt, die);
  }
  // Real danger: the ship goes down and the voyage ends. The hideout, your earned colours and the hall of fame stay.
  function sink(B, txt) {
    var n = B.n, body = $('enc-body'), lv = level();
    sfx('bad');
    addFame(state, 'sunk', 'sunk by ' + foeName(n) + ' of ' + n.name);
    started = false;
    try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* ignore */ }
    track('sunk');
    $('enc-title').textContent = '💀 ' + cap(shipName()) + ' goes down';
    body.textContent = '';
    body.appendChild(el('p', {id: 'enc-text'}, (txt + ' That was one broadside too many. ' + cap(shipName()) + ' rolls over and slips beneath the waves, cargo, gold and all. A fishing boat pulls your crew out of the water, along with one furious parrot.').replace(/\s+/g, ' ')));
    body.appendChild(el('p', {class: 'win'}, captainName() + ' sailed for ' + day() + ' ' + plural(day(), 'day') + ', reached level ' + lv + ' (' + title(lv) + ') and went down with ' + fmt(state.gold) + ' doubloons aboard. This voyage is over.'));
    var keep = [];
    if (legacy.base) keep.push('your hideout on ' + HIDE.name + ' still holds ' + fmt(legacy.base.gold) + ' doubloons and ' + baleWord(baseBales()));
    keep.push('your name is in the hall of fame');
    body.appendChild(el('p', null, 'What the sea can’t take: ' + andList(keep) + '. Any sail colours and flags you earned stay earned.'));
    var c = el('button', {type: 'button', class: 'primary', 'aria-describedby': 'enc-text'}, 'Back to the harbour');
    c.addEventListener('click', function () { closeDialog('dlg-encounter'); showTitle(); setTimeout(function () { $('btn-new').focus(); }, 0); });
    body.appendChild(c);
    openDialog($('dlg-encounter'), c);
  }
  function endFight(B, txt, die) {
    var body = $('enc-body'), n = B.n, c = el('button', {type: 'button', class: 'primary', 'aria-describedby': 'enc-text'}, 'Continue');
    body.textContent = '';
    textBlock(body, txt, die);
    body.appendChild(hullBars(B));
    c.addEventListener('click', function () {
      closeDialog('dlg-encounter');
      grace = 3;
      if (n.kind === 'merchant' && !n.looted) n.cool = Math.max(n.cool, 12);
      checkGoals();
      save();
      if (pendingJail) { serveJail(); return; }
      if (B.after) B.after();
    });
    body.appendChild(c);
    c.focus();
  }
  // opts: the choices. With no choices it just shows the text and a Continue button. die: a roll to show beside the text.
  function showEncounter(title, text, opts, onDone, hint, die) {
    var dlg = $('dlg-encounter'), body = $('enc-body');
    $('enc-title').textContent = title;
    body.textContent = '';
    textBlock(body, text, die);
    var p = $('enc-text'), list = el('div', {class: 'choices'});
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
        lastRoll = null;
        var res = o.fn ? o.fn() : null;
        if (!res) { finish(); return; }
        var r = lastRoll;
        p.textContent = (rollText(r) + res).replace(/\s+/g, ' ').trim();
        var old = body.querySelector('.die');
        if (old) old.remove();
        if (r) p.parentNode.insertBefore(dieBadge(r), p);
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
    var opts = e.opts(evApi()), odds = opts.some(function (o) { return /🎲/.test(o.label); });
    showEncounter(e.title, e.text, opts, function () { grace = 2; if (after) after(); }, odds ? edgeHint() : '');
  }

  /* ---------- the powers of 1718: flags, standing, warships, jobs and harbour news ---------- */
  var NAT = D.NATIONS, NAT_ORDER = D.NATION_ORDER, STAND = D.STAND;
  function natOf(pid) { return (PORTS[pid] && PORTS[pid].nation) || 'brethren'; }
  function lawOf(mid) { return D.SEA_LAW[mid] || 'britain'; }
  function repOf(k) { return (state.rep && state.rep[k]) || 0; }
  function standOf(k) { return E.standTier(repOf(k)); }
  function stand(k) { return STAND[standOf(k)]; }
  function atWar(a, b) { return (D.WAR[a] || []).indexOf(b) >= 0; }
  function enemiesOf(k) { return (D.WAR[k] || []).map(function (e) { return NAT[e].short; }); }
  // Moves your standing with a nation. Says something only when the tier changes.
  function shift(k, d) {
    if (!NAT[k] || !d || !state.rep) return '';
    var before = standOf(k);
    state.rep[k] = clamp(Math.round(repOf(k) + d), -100, 100);
    var after = standOf(k), msg = '';
    if (after !== before) msg = ' ' + STAND[after].icon + ' Your standing with ' + NAT[k].short + ' is now ' + STAND[after].name + '.';
    if (state.marque === k && after <= 1) { state.marque = ''; msg += ' ' + cap(NAT[k].short) + ' tears up your letter of marque.'; }
    return msg;
  }
  // Paying off a warship, or striking to her, settles what you owe that nation: Neutral, just.
  function settle(k) { if (state.rep && repOf(k) < -19) state.rep[k] = -19; }
  function fineOf(k) { return standOf(k) === 0 ? Math.max(150, Math.round(state.gold * 0.25)) : Math.max(50, Math.round(state.gold * 0.1)); }
  function parleyP(n) { return clamp(0.45 + (standOf('brethren') === 4 ? 0.25 : 0) + 0.05 * stats().charm - 0.05 * ((n.tier || 1) - 1), 0.1, 0.95); }
  function flagSwatch(k) { return el('span', {class: 'fl fl-' + k, 'aria-hidden': 'true'}); }
  function marqueLine() {
    if (!state.marque) return '';
    return '📜 You carry a ' + NAT[state.marque].adj + ' letter of marque: ' + andList(enemiesOf(state.marque)) + '’s merchant ships are fair game, and ' + NAT[state.marque].short + ' thanks you for every one.';
  }

  /* Warships: one or two per sea, flying the flag of whoever patrols it. Neutral or better and they leave you be. */
  function makeNavy(m, nat) { return pirateShip(m, {kind: 'navy', nation: nat, tier: (D.SEA_TIER[m.id] || 1) >= 3 ? 4 : 3, cool: 10}); }
  function navyHail(n) {
    var N = NAT[n.nation], dz = dangerOf(n), saluted = state.salute && state.salute[n.nation] === day();
    showEncounter('⚓ ' + cap(N.adj) + ' ' + shipClass(n), n.captain + ' of ' + n.name + ', a ' + N.adj + ' ' + shipClass(n) + ' of ' + N.navy + ', looks you over through a long brass telescope. Her gun ports stay shut. For now.', [
      {label: '🎩 Dip your flag in salute' + (saluted ? ' (already done today)' : ''), fn: function () {
        var msg = '';
        if (!saluted) { state.salute[n.nation] = day(); msg = shift(n.nation, 2); }
        return 'You dip your flag. ' + n.captain + ' raises a hat. Manners cost nothing at sea.' + msg;
      }},
      {label: '⚔️ Attack her (' + DANGER[dz].toLowerCase() + '; ' + N.short + ' will never forget it)', next: function () {
        state.rep[n.nation] = Math.min(repOf(n.nation) - 40, -60);
        fight(n);
      }},
      {label: '⛵ Sail on', fn: function () { return 'You keep a polite distance. ' + cap(n.name) + ' sails on, very slowly, so everyone can see how big she is.'; }}
    ], function () { n.cool = 40; grace = 3; });
  }

  /* Jobs: three a port every three days, from whoever runs the port. Cargo for a job rides in your hold but isn't yours to sell. */
  var JOB_MAX = 3;
  function jobLoad() { var n = 0; (state.jobs || []).forEach(function (j) { if (j.kind === 'deliver' || j.kind === 'smuggle') n += j.n; }); return n; }
  function parcels() { var n = 0; (state.jobs || []).forEach(function (j) { if (j.kind === 'smuggle') n += j.n; }); return n; }
  // Sealed parcels go in the smuggler's hold first. Whatever doesn't fit rides in the open.
  function openParcels() { return Math.max(0, parcels() - secretCap()); }
  function jobPeriod() { return Math.floor((day() - 1) / 3); }
  function makeJob(pid, kind, r, per, i) {
    var a = r(), b = r(), c = r(), d2 = r(), lv = level(), k = natOf(pid), id = pid + ':' + per + ':' + i;
    var payMod = 1 + 0.05 * stats().charm + stand(k).pay;
    if (kind === 'bounty' && lv < 3) kind = 'deliver';
    if (kind === 'deliver' || kind === 'smuggle') {
      var dests = Object.keys(PORTS).filter(function (q) {
        if (q === pid || (kind === 'smuggle' && ['spain', 'britain'].indexOf(PORTS[q].nation) < 0)) return false;
        var v0 = voyage(pid, q);
        return v0 && v0.days <= 5;
      });
      if (!dests.length) return null;
      var to = dests[Math.floor(a * dests.length)], v = voyage(pid, to), n = kind === 'deliver' ? 4 + Math.floor(b * 7) : 2 + Math.floor(b * 4);
      var seaMult = 1 + 0.15 * ((D.SEA_TIER[PORTS[to].map] || 1) - 1);
      var pay = kind === 'deliver' ? 40 + n * (6 + 7 * v.days) : 100 + n * (35 + 22 * v.days);
      return {id: id, kind: kind, by: k, from: pid, to: to, n: n, days: v.days, pay: Math.round(pay * seaMult * payMod / 5) * 5,
        due: day() + v.days + 2 + Math.ceil(v.days / 2), what: kind === 'deliver' ? D.JOB_CARGO[Math.floor(c * D.JOB_CARGO.length)] : 'sealed parcels'};
    }
    if (kind === 'supply') {
      var wants = D.COMMON.filter(function (g) { return PORTS[pid].sells.indexOf(g) < 0; }), g = wants[Math.floor(a * wants.length)], m = 4 + Math.floor(b * 5);
      if (!g) return null;
      return {id: id, kind: kind, by: k, from: pid, g: g, n: m, pay: Math.round(m * E.sellPrice(pid, g, day(), 0) * 1.4 * payMod / 5) * 5, due: day() + 10};
    }
    var sea = PORTS[pid].map, tr = clamp((D.SEA_TIER[sea] || 1) + 1 + (lv >= 6 ? 1 : 0), 2, 5);
    return {id: id, kind: 'bounty', by: k, from: pid, sea: sea, tier: tr, captain: D.PIRATE_CAPTAINS[Math.floor(c * D.PIRATE_CAPTAINS.length)],
      ship: D.PIRATE_SHIPS[Math.floor(d2 * D.PIRATE_SHIPS.length)], pay: Math.round((200 * tr + 40 * lv) * payMod / 5) * 5, due: day() + 12};
  }
  function jobOffers(pid) {
    var k = natOf(pid), st = standOf(k), per = jobPeriod(), r = E.rng(E.hashStr(state.seed + ':' + pid + ':' + per));
    var kinds = pid === 'nassau' ? ['smuggle', 'smuggle', 'supply'] : k === 'france' ? ['smuggle', 'deliver', 'supply'] : ['deliver', 'supply', 'bounty'];
    var out = [];
    // Every slot draws its dice whatever happens, so the board doesn't reshuffle while you look at it.
    kinds.forEach(function (kind, i) { var j = makeJob(pid, kind, r, per, i); if (j && !state.jobsTaken[j.id]) out.push(j); });
    if (st === 0) return [];
    return st === 1 ? out.slice(0, 1) : out;
  }
  function jobTitle(j) {
    if (j.kind === 'deliver') return 'Carry ' + j.n + ' ' + j.what + ' to ' + PORTS[j.to].name;
    if (j.kind === 'smuggle') return 'Smuggle ' + j.n + ' sealed parcels to ' + PORTS[j.to].name;
    if (j.kind === 'supply') return 'Bring ' + baleWord(j.n) + ' of ' + GOODS[j.g].name + ' to ' + PORTS[j.from].name;
    return 'Wanted: ' + j.captain + ' of ' + j.ship;
  }
  function jobText(j) {
    var by = ' Due by day ' + j.due + '. Pays ' + fmt(j.pay) + ' doubloons.';
    if (j.kind === 'deliver') return jobTitle(j) + ', about ' + sailText(j.days) + ' away. Takes ' + j.n + ' spaces in your hold.' + by;
    if (j.kind === 'smuggle') return jobTitle(j) + ', no questions asked. Takes ' + j.n + ' spaces. Your smuggler’s hold hides them first; any Customs officer who sees them takes them, and the job is lost.' + by;
    if (j.kind === 'supply') return jobTitle(j) + '. This port doesn’t grow it, so buy it elsewhere.' + by;
    return 'A pirate ' + (D.SHIP_CLASS[j.tier - 1] || 'ship') + ' wanted by ' + NAT[j.by].short + '. Last seen in ' + MAPS[j.sea].name + '. Beat that ship in battle, then collect in ' + PORTS[j.from].name + '.' + by;
  }
  function jobXp(j) { return j.kind === 'deliver' ? 15 + 5 * j.days : j.kind === 'smuggle' ? 25 + 8 * j.days : j.kind === 'supply' ? 20 : 40 + 20 * j.tier; }
  function takeJob(j) {
    if (state.jobs.length >= JOB_MAX || ((j.kind === 'deliver' || j.kind === 'smuggle') && space() < j.n)) return false;
    state.jobsTaken[j.id] = 1;
    state.jobs.push(j);
    if (j.to && !state.known[j.to]) { state.known[j.to] = 1; reveal(PORTS[j.to].map, PORTS[j.to].dock[0], PORTS[j.to].dock[1], 110); }
    if (j.kind === 'bounty' && npcs[j.sea]) ensureBounties(j.sea);
    track('job-' + j.kind);
    return true;
  }
  function dropJob(j) {
    state.jobs = state.jobs.filter(function (x) { return x !== j; });
    removeBounty(j);
    return shift(j.by, -5);
  }
  // Pays for every job that ends here. Supplies come out of your hold if you have them.
  function settleJobs(pid) {
    var msgs = [];
    state.jobs = state.jobs.filter(function (j) {
      var ok = (j.kind === 'deliver' || j.kind === 'smuggle') && j.to === pid;
      if (j.kind === 'supply' && j.from === pid && (state.cargo[j.g] || 0) >= j.n) { takeCargo(j.g, j.n); ok = true; }
      if (j.kind === 'bounty' && j.from === pid && j.hit) ok = true;
      if (!ok) return true;
      state.gold += j.pay; state.jobsDone++;
      if (j.kind === 'bounty') state.bounties++;
      var rep = j.kind === 'deliver' ? 4 : j.kind === 'supply' ? 3 : j.kind === 'smuggle' ? 2 : 10;
      msgs.push('📋 Job done: ' + jobTitle(j) + '. +' + fmt(j.pay) + ' doubloons.' + shift(j.by, rep) + (j.kind === 'smuggle' ? shift('brethren', 6) : '') + gainXp(jobXp(j)));
      return false;
    });
    if (msgs.length) { sfx('coin'); track('job-done'); }
    return msgs.join(' ');
  }
  function canDeliver(j, pid) { return j.kind === 'supply' && j.from === pid && (state.cargo[j.g] || 0) >= j.n; }
  // A wanted pirate sails the sea named on the poster until someone beats them. Not saved: the sea puts them back when you load.
  function ensureBounties(mid) {
    var list = npcs[mid];
    if (!list) return;
    (state.jobs || []).forEach(function (j) {
      if (j.kind !== 'bounty' || j.sea !== mid || j.hit || list.some(function (n) { return n.bounty === j.id; })) return;
      list.push(pirateShip(E.prepareMap(mid), {kind: 'pirate', bounty: j.id, tier: j.tier, captain: j.captain, name: j.ship, cool: 10}));
    });
  }
  function bountyOf(n) { for (var i = 0; n.bounty && i < state.jobs.length; i++) if (state.jobs[i].id === n.bounty) return state.jobs[i]; return null; }
  function removeNpc(n) { for (var mid in npcs) { var i = npcs[mid].indexOf(n); if (i >= 0) npcs[mid].splice(i, 1); } }
  function removeBounty(j) { if (j.kind !== 'bounty') return; for (var mid in npcs) npcs[mid] = npcs[mid].filter(function (n) { return n.bounty !== j.id; }); }

  /* Harbour news: a few days of good prices, gluts, crackdowns and pirate trouble. Opens up at level 2. */
  function newsOn(kind, pid, g) { for (var i = 0; i < (state.news || []).length; i++) { var x = state.news[i]; if (x.kind === kind && x.pid === pid && (!g || x.g === g)) return x; } return null; }
  function seaNews(kind, mid) { for (var i = 0; i < (state.news || []).length; i++) { var x = state.news[i]; if (x.kind === kind && x.sea === mid) return x; } return null; }
  function stockCap(pid, g) { var mx = E.stockMax(pid, g); return mx && newsOn('glut', pid, g) ? mx * 2 : mx; }
  function makeNews() {
    var d = day(), r = Math.random(), kind = r < 0.4 ? 'spike' : r < 0.65 ? 'glut' : r < 0.85 ? 'crack' : 'raid';
    var ports = Object.keys(PORTS).filter(portKnown), seas = Object.keys(MAPS).filter(seenSea), x = {kind: kind, until: d + 3 + Math.floor(Math.random() * 3)};
    if (kind === 'spike' || kind === 'glut') {
      x.pid = pick(ports);
      var P = PORTS[x.pid], opts = D.COMMON.filter(function (g) { return kind === 'spike' ? P.sells.indexOf(g) < 0 : P.sells.indexOf(g) >= 0; });
      if (!opts.length) return null;
      x.g = pick(opts);
      if (newsOn(kind, x.pid, x.g) || newsOn(kind === 'spike' ? 'glut' : 'spike', x.pid, x.g)) return null;
      x.mult = kind === 'spike' ? Math.round((1.8 + Math.random() * 0.6) * 100) / 100 : 0.55;
      if (kind === 'glut' && state.mk[x.pid]) state.mk[x.pid].st[x.g] = E.stockMax(x.pid, x.g) * 2;
    } else {
      x.sea = pick(seas);
      if (seaNews(kind, x.sea)) return null;
    }
    x.text = pick(D.NEWS[kind]).replace('{port}', x.pid ? PORTS[x.pid].name : '').replace('{good}', x.g ? GOODS[x.g].name : '')
      .replace('{sea}', x.sea ? MAPS[x.sea].name : '').replace('{law}', x.sea ? NAT[lawOf(x.sea)].law : '');
    if (kind === 'raid' && npcs[x.sea] && npcs[x.sea].filter(function (n) { return n.kind === 'pirate' && !n.bounty; }).length <= (D.PIRATE_COUNT[x.sea] || 0)) npcs[x.sea].push(makePirate(enterMap(x.sea)));
    return x;
  }
  function newsLine(x) { return x.text + ' (until day ' + x.until + ')'; }
  // Once a day: bad blood fades, late jobs fail, old news goes stale and new news comes in.
  function dayTick(fed) {
    var d = day();
    if (!state.lastDay) { state.lastDay = d; return ''; }
    if (d <= state.lastDay) return '';
    var passed = Math.min(30, d - state.lastDay), msgs = [];
    state.lastDay = d;
    if (level() >= 2 && !fed) {
      var had = state.food;
      state.food = Math.max(0, state.food - passed);
      if (had > 0 && !state.food) msgs.push('🍞 The provisions are gone. A hungry crew sails slower and does everything worse (−10% on every roll) until you buy more in a market.');
      else if (had > 5 && state.food <= 5) msgs.push('🍞 Provisions are running low: ' + state.food + ' ' + plural(state.food, 'day') + ' left. Any market sells more.');
    }
    NAT_ORDER.forEach(function (k) { if (state.rep[k] < 0) state.rep[k] = Math.min(0, state.rep[k] + passed); });
    state.jobs = state.jobs.filter(function (j) {
      if (j.due >= d) return true;
      removeBounty(j);
      msgs.push('📋 Too late: ' + jobTitle(j) + '. ' + (j.kind === 'deliver' || j.kind === 'smuggle' ? 'The cargo goes back with the next ship.' : 'The job is off.') + shift(j.by, -8));
      return false;
    });
    var per = jobPeriod();
    for (var id in state.jobsTaken) if (+id.split(':')[1] < per - 1) delete state.jobsTaken[id];
    state.news = state.news.filter(function (x) { return x.until >= d; });
    if (level() >= 2) for (var i = 0; i < passed && state.news.length < 3; i++) {
      if (Math.random() >= 0.4) continue;
      var x = makeNews();
      if (x) { state.news.push(x); msgs.push('📰 Harbour news: ' + x.text); }
    }
    return msgs.join(' ');
  }
  // What each level opens up, said once.
  function unlockText(lv) {
    var out = [];
    [2, 3, 4].forEach(function (L) {
      if (L > lv || state.flags['u' + L]) return;
      state.flags['u' + L] = 1;
      out.push('🔓 ' + D.UNLOCK[L]);
    });
    return out.join('\n\n');
  }

  /* The Jobs tab. */
  function renderJobs(pid, panel) {
    var k = natOf(pid), N = NAT[k], st = standOf(k);
    var head = el('p', {class: 'hint'});
    head.appendChild(flagSwatch(k));
    head.appendChild(document.createTextNode(' ' + (k === 'brethren' ? 'The Brethren of the Coast run things here.' : cap(N.adj) + ' port.') + ' Your standing: ' + STAND[st].icon + ' ' + STAND[st].name + '. ' +
      (st === 0 ? 'Nobody here will give you work until you mend fences: pay off a warship, or let time heal it.' : st === 1 ? 'They’ll only trust you with one job at a time.' : st >= 3 ? 'Friends get paid ' + Math.round(STAND[st].pay * 100) + '% more.' : 'Finish jobs to raise it: friends get paid more.')));
    panel.appendChild(head);
    if (state.jobs.length) {
      panel.appendChild(el('h3', null, '📋 Your jobs (' + state.jobs.length + ' of ' + JOB_MAX + ')'));
      var mine = el('ul', {class: 'goods'});
      state.jobs.forEach(function (j, i) {
        var li = el('li', {class: 'good'});
        li.appendChild(el('p', {class: 'run'}, (j.hit ? '✅ ' : '') + jobText(j) + (j.hit ? ' Done: collect in ' + PORTS[j.from].name + '.' : '')));
        var btns = el('div', {class: 'g-btns'});
        if (canDeliver(j, pid)) {
          var dv = el('button', {type: 'button', class: 'primary', 'data-key': 'dv' + i}, '📦 Deliver now');
          dv.addEventListener('click', function () { var m = settleJobs(pid); if (m) say(m); checkGoals(); save(); renderPanel('jobs'); });
          btns.appendChild(dv);
        }
        var ab = el('button', {type: 'button', 'data-key': 'ab' + i, 'aria-label': 'Give up the job: ' + jobTitle(j) + '. ' + NAT[j.by].short + ' will think less of you.'}, 'Give up');
        ab.addEventListener('click', function () { var m = dropJob(j); say('You give up the job: ' + jobTitle(j) + '.' + m); save(); renderPanel('jobs'); });
        btns.appendChild(ab);
        li.appendChild(btns);
        mine.appendChild(li);
      });
      panel.appendChild(mine);
    }
    panel.appendChild(el('h3', {'data-key': 'jobs', tabindex: '-1'}, '📌 The job board'));
    var offers = jobOffers(pid);
    if (!offers.length) panel.appendChild(el('p', null, st === 0 ? 'The board is empty for the likes of you.' : 'Nothing left on the board. New jobs go up every three days.'));
    else {
      var ul = el('ul', {class: 'goods'});
      offers.forEach(function (j, i) {
        var li = el('li', {class: 'good'}), full = state.jobs.length >= JOB_MAX, room = (j.kind !== 'deliver' && j.kind !== 'smuggle') || space() >= j.n;
        li.appendChild(el('p', {class: 'run'}, jobText(j)));
        var btns = el('div', {class: 'g-btns'}), b = el('button', {type: 'button', 'data-key': 'tk' + i},
          full ? 'You already have ' + JOB_MAX + ' jobs' : room ? '✍️ Take the job' : 'Needs ' + j.n + ' free spaces');
        b.disabled = full || !room;
        b.addEventListener('click', function () {
          if (!takeJob(j)) return;
          sfx('pickup');
          var m = settleJobs(pid);
          say('📋 New job: ' + jobTitle(j) + '. Due by day ' + j.due + '.' + (m ? ' ' + m : ''));
          checkGoals(); save(); renderPanel('jobs');
        });
        btns.appendChild(b);
        li.appendChild(btns);
        ul.appendChild(li);
      });
      panel.appendChild(ul);
    }
    panel.appendChild(el('p', {class: 'hint'}, 'Deliveries pay on arrival. Late jobs fail and cost you standing. Jobs are lost if your ship goes down.'));
    // Letters of marque: a nation at war pays you to raid its enemies' shipping.
    if (level() >= 3 && D.WAR[k] && D.WAR[k].length) {
      panel.appendChild(el('h3', null, '📜 Letter of marque'));
      if (state.marque === k) {
        panel.appendChild(el('p', null, marqueLine()));
        var tear = el('button', {type: 'button', class: 'secondary', 'data-key': 'mq'}, 'Hand the letter back');
        tear.addEventListener('click', function () { state.marque = ''; say('You hand back your ' + N.adj + ' letter of marque. The clerk looks relieved.'); save(); renderPanel('mq'); });
        panel.appendChild(tear);
      } else {
        panel.appendChild(el('p', null, 'A letter of marque makes you a privateer: a pirate with paperwork. With it, attacking ' + andList(enemiesOf(k)) + '’s merchant ships pays 20% more and ' + N.short + ' cheers instead of frowning. The bond is 200 doubloons. You can carry one nation’s letter at a time.'));
        var ok = st >= 3, mq = el('button', {type: 'button', class: 'primary', 'data-key': 'mq'},
          !ok ? 'Needs Friendly standing with ' + N.short : state.marque ? 'Swap your ' + NAT[state.marque].adj + ' letter for this one (200 doubloons)' : '📜 Take a letter of marque (200 doubloons)');
        mq.disabled = !ok || state.gold < 200;
        mq.addEventListener('click', function () {
          if (state.gold < 200) return;
          state.gold -= 200; state.marque = k; sfx('coin'); track('marque');
          say('📜 You sign for a ' + N.adj + ' letter of marque. ' + cap(andList(enemiesOf(k))) + '’s merchant ships are fair game now.');
          save(); renderPanel('mq');
        });
        panel.appendChild(mq);
      }
    }
  }
  // The powers, for the captain's log.
  function renderPowers(b) {
    b.appendChild(el('h3', null, 'The powers of 1718'));
    b.appendChild(el('p', {class: 'hint'}, D.WAR_NOTE));
    var ul = el('ul', {class: 'checks powers'});
    NAT_ORDER.forEach(function (k) {
      var N = NAT[k], s = STAND[standOf(k)], li = el('li');
      li.appendChild(flagSwatch(k));
      li.appendChild(el('span', {class: 'grow'}, cap(N.name) + ': ' + s.icon + ' ' + s.name + ' (' + repOf(k) + '). ' + N.flag + (state.marque === k ? ' You carry its letter of marque.' : '')));
      ul.appendChild(li);
    });
    b.appendChild(ul);
    b.appendChild(el('p', {class: 'hint'}, 'Standing sets your prices in a nation’s ports, how hard its Customs lean on you, what its jobs pay and whether its warships come for you. Pillaging its merchants and fighting its ships lowers it; jobs, fees and salutes raise it. Bad blood fades a little every day.'));
    if (state.jobs.length) {
      b.appendChild(el('h3', null, 'Jobs: ' + state.jobs.length + ' of ' + JOB_MAX));
      var jl = el('ul', {class: 'checks'});
      state.jobs.forEach(function (j) {
        var li = el('li');
        li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, j.hit ? '✅' : '📋'));
        li.appendChild(document.createTextNode(jobText(j) + (j.hit ? ' Done: collect in ' + PORTS[j.from].name + '.' : '')));
        jl.appendChild(li);
      });
      b.appendChild(jl);
    }
    if (state.news.length) {
      b.appendChild(el('h3', null, 'Harbour news'));
      var nl = el('ul', {class: 'checks'});
      state.news.forEach(function (x) { var li = el('li'); li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, '📰')); li.appendChild(document.createTextNode(newsLine(x))); nl.appendChild(li); });
      b.appendChild(nl);
    }
  }

  /* ---------- ports ---------- */
  var portTab = 'market', talkNode = 'start';
  function portTabs(pid) {
    var p = PORTS[pid], tabs = [['market', '🛒 Market'], ['tavern', '🍺 Tavern']];
    if (level() >= 2) tabs.push(['jobs', '📋 Jobs']);
    if (p.yard) tabs.push(['yard', '🔨 Shipwright']);
    tabs.push(['routes', '🧭 Routes']);
    return tabs;
  }
  function openPort(pid, tab) {
    var p = PORTS[pid];
    $('port-title').textContent = '⚓ ' + p.name;
    var bl = $('port-blurb'), k = natOf(pid), fl = el('span', {class: 'nat'});
    bl.textContent = p.blurb + ' ';
    fl.appendChild(flagSwatch(k));
    fl.appendChild(document.createTextNode(' ' + (k === 'brethren' ? 'A pirate port' : cap(NAT[k].adj) + ' port') + ' · your standing: ' + STAND[standOf(k)].name));
    bl.appendChild(fl);
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
    else if (portTab === 'jobs') renderJobs(pid, panel);
    else renderYard(panel);
    if (keepKey) {
      var again = panel.querySelector('[data-key="' + keepKey + '"]');
      if (again && !again.disabled) again.focus();
      else { var h = panel.querySelector('h3'); if (h) { h.tabIndex = -1; h.focus(); } }
    }
  }
  function portStatus() {
    return '🪙 ' + fmt(state.gold) + ' doubloons · 📦 ' + (cargoCount() + jobLoad()) + ' of ' + capacity() + ' in the hold · 🛡️ Hull ' + state.hull + ' of ' + hullMax() + ' · ⭐ Level ' + level();
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
  // Powder and shot: sold in every market, and kept apart from the hold.
  function buyShot(n) {
    n = Math.min(n, SHOT_MAX - state.shot, Math.floor(state.gold / SHOT_PRICE));
    if (n <= 0) return 0;
    state.gold -= n * SHOT_PRICE; state.shot += n;
    sfx('coin');
    say('💣 Bought ' + n + ' ' + plural(n, 'cannonball') + ' for ' + fmt(n * SHOT_PRICE) + ' doubloons. You have ' + state.shot + '.');
    save();
    return n;
  }
  // Provisions: from level 2 the crew eats a day's worth for every day at sea.
  function buyFood(n) {
    n = Math.min(n, FOOD_MAX - state.food, Math.floor(state.gold / FOOD_PRICE));
    if (n <= 0) return 0;
    state.gold -= n * FOOD_PRICE; state.food += n;
    sfx('coin');
    say('🍞 Bought ' + n + ' ' + plural(n, 'day') + ' of provisions for ' + fmt(n * FOOD_PRICE) + ' doubloons. You have ' + state.food + '.');
    save();
    return n;
  }
  function foodRow() {
    var room = FOOD_MAX - state.food, afford = Math.min(room, Math.floor(state.gold / FOOD_PRICE)), box = el('div', {class: 'repair'});
    box.appendChild(el('p', null, '🍞 Provisions: ' + state.food + ' of ' + FOOD_MAX + ' days. Ship’s biscuit, salt pork, plantains and a sack of the good snacks, ' + FOOD_PRICE + ' doubloons a day. The crew eats a day’s worth for every day at sea, and two more every time you smoke.' +
      (hungry() ? ' ⚠️ Your crew is hungry right now: slower sails and −10% on every roll.' : '')));
    var ten = Math.min(10, afford);
    [['food10', ten, ten ? 'Buy ' + ten + ' days · ' + fmt(ten * FOOD_PRICE) + ' 🪙' : 'Buy 10 days'], ['foodfill', afford, room ? 'Fill up (' + afford + ') · ' + fmt(afford * FOOD_PRICE) + ' 🪙' : 'Lockers are full']].forEach(function (o) {
      var b = el('button', {type: 'button', class: 'secondary', 'data-key': o[0], 'aria-label': o[1] ? 'Buy ' + o[1] + ' days of provisions for ' + fmt(o[1] * FOOD_PRICE) + ' doubloons' : null}, o[2]);
      b.disabled = o[1] <= 0;
      b.addEventListener('click', function () { if (buyFood(o[1])) renderPanel(o[0]); });
      box.appendChild(b);
    });
    return box;
  }
  function shotRow() {
    var room = SHOT_MAX - state.shot, afford = Math.min(room, Math.floor(state.gold / SHOT_PRICE)), box = el('div', {class: 'repair'});
    box.appendChild(el('p', null, '💣 Cannonballs: ' + state.shot + ' of ' + SHOT_MAX + '. Powder and shot cost ' + SHOT_PRICE + ' doubloons a ball. Out of shot, you can still lob bales of weed.'));
    var ten = Math.min(10, afford);
    [['shot10', ten, ten ? 'Buy ' + ten + ' · ' + fmt(ten * SHOT_PRICE) + ' 🪙' : 'Buy 10'], ['shotfill', afford, room ? 'Fill up (' + afford + ') · ' + fmt(afford * SHOT_PRICE) + ' 🪙' : 'Racks are full']].forEach(function (o) {
      var b = el('button', {type: 'button', class: 'secondary', 'data-key': o[0], 'aria-label': o[1] ? 'Buy ' + o[1] + ' cannonballs for ' + fmt(o[1] * SHOT_PRICE) + ' doubloons' : null}, o[2]);
      b.disabled = o[1] <= 0;
      b.addEventListener('click', function () { if (buyShot(o[1])) renderPanel(o[0]); });
      box.appendChild(b);
    });
    return box;
  }
  // Each market keeps a few bales of what it sells, restocks a third of its shelves a day, and remembers what you traded lately.
  function mkt(pid) {
    var d = day(), m = state.mk[pid];
    if (!m) m = state.mk[pid] = {d: d, st: {}, b: {}, s: {}};
    var dd = Math.max(0, d - (m.d || d));
    ORDER.forEach(function (g) {
      var mx = stockCap(pid, g);
      if (mx) m.st[g] = Math.min(mx, (typeof m.st[g] === 'number' ? m.st[g] : mx) + Math.ceil(mx / 3) * dd);
      if (dd) {
        if (m.b[g]) { m.b[g] *= Math.pow(0.5, dd); if (m.b[g] < 0.5) delete m.b[g]; }
        if (m.s[g]) { m.s[g] *= Math.pow(0.5, dd); if (m.s[g] < 0.5) delete m.s[g]; }
      }
    });
    m.d = d;
    return m;
  }
  function stockOf(pid, g) { return E.stockMax(pid, g) ? Math.max(0, Math.floor(mkt(pid).st[g])) : 0; }
  // What you pay and get right now: your Charm (boost included), any selling boost or relic, and what you've traded here lately.
  // extra: the price after that many more bales, so a whole lot can be priced bale by bale.
  // Your standing with the port's nation, and any harbour news about this cargo here.
  function priceMod(pid, g, buying) { var s = stand(natOf(pid)), x = newsOn(buying ? 'glut' : 'spike', pid, g); return (buying ? s.buy : s.sell) * (x ? x.mult : 1); }
  function buyFor(pid, g, extra) {
    var p = E.buyPrice(pid, g, day(), stats().charm);
    return p ? E.pushed(Math.max(1, Math.round(p * priceMod(pid, g, true))), (mkt(pid).b[g] || 0) + (extra || 0), true) : p;
  }
  function sellFor(pid, g, extra) {
    var b = boost(), up = ((b && b.sell) || 0) + relic('sell'), p = E.pushed(Math.max(1, Math.round(E.sellPrice(pid, g, day(), stats().charm) * priceMod(pid, g, false))), (mkt(pid).s[g] || 0) + (extra || 0), false);
    return up ? Math.round(p * (1 + up)) : p;
  }
  function buyAt(pid, g) { return buyFor(pid, g, 0); }
  function sellAt(pid, g) { return sellFor(pid, g, 0); }
  function costOf(pid, g, n) { var t = 0; for (var i = 0; i < n; i++) t += buyFor(pid, g, i); return t; }
  function payOf(pid, g, n) { var t = 0; for (var i = 0; i < n; i++) t += sellFor(pid, g, i); return t; }
  function maxBuy(pid, g) {
    var lim = Math.min(space(), stockOf(pid, g)), n = 0, t = 0;
    while (n < lim) { var c = buyFor(pid, g, n); if (!c || t + c > state.gold) break; t += c; n++; }
    return n;
  }
  // One bale at a time, so every bale moves the price of the next.
  function buyBales(pid, g, n) {
    var m = mkt(pid), got = 0, paid = 0;
    while (got < n && space() > 0 && m.st[g] >= 1) {
      var pr = buyAt(pid, g);
      if (!pr || state.gold < pr) break;
      state.gold -= pr; paid += pr; addCargo(g, 1); m.st[g]--; m.b[g] = (m.b[g] || 0) + 1; got++;
    }
    if (got) state.basis[g] = (state.basis[g] || 0) + paid;
    return {n: got, gold: paid};
  }
  function sellBales(pid, g, n) {
    var m = mkt(pid), r = {n: 0, gold: 0, xp: 0};
    while (r.n < n && state.cargo[g] > 0) {
      var one = sellGoods(g, 1, sellAt(pid, g));
      if (!one) break;
      m.s[g] = (m.s[g] || 0) + 1;
      r.n++; r.gold += one.gold; r.xp += one.xp;
    }
    return r.n ? r : null;
  }
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
    if (buying) {
      var b = buyBales(pid, g, n);
      if (!b.n) return;
      say('Bought ' + baleWord(b.n) + ' of ' + GOODS[g].name + ' for ' + fmt(b.gold) + ' doubloons.' + (stockOf(pid, g) ? '' : ' That’s all they had.'));
    } else {
      var r = sellBales(pid, g, n);
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
    held.forEach(function (g) { total += payOf(pid, g, state.cargo[g]); });
    var intro = el('p', {class: 'hint'}, 'Prices change every day. Each port grows one strain cheaply and pays more for strains from elsewhere, most of all from another sea. Markets only keep a few bales on the shelf, and every bale you buy nudges the price up (every bale you sell nudges it down) until the market settles over the next few days.');
    panel.appendChild(intro);
    var sk = standOf(natOf(pid));
    if (sk !== 2) panel.appendChild(el('p', {class: 'hint'}, STAND[sk].icon + ' ' + (natOf(pid) === 'brethren' ? 'The Brethren' : cap(NAT[natOf(pid)].short)) + ' ' + (sk > 2 ? 'likes you, so you buy a little cheaper and sell a little dearer here.' : 'doesn’t trust you, so you buy a little dearer and sell a little cheaper here.')));
    panel.appendChild(shotRow());
    if (level() >= 2) panel.appendChild(foodRow());
    if (held.length) {
      var all = el('button', {type: 'button', class: 'secondary sellall', 'data-key': 'sellall'}, '💰 Sell the whole hold for ' + fmt(total) + ' doubloons');
      all.addEventListener('click', function () {
        var n = 0, got = 0, xp = 0;
        Object.keys(state.cargo).forEach(function (g) { var r = sellBales(pid, g, state.cargo[g]); if (r) { n += r.n; got += r.gold; xp += r.xp; } });
        sfx('coin');
        say('Sold all ' + baleWord(n) + ' for ' + fmt(got) + ' doubloons.' + gainXp(xp));
        checkGoals(); save(); renderPanel('sellall');
      });
      panel.appendChild(all);
    }
    var ul = el('ul', {class: 'goods'});
    list.forEach(function (g) {
      var G = GOODS[g], bp = buyAt(pid, g), spr = sellAt(pid, g), have = state.cargo[g] || 0, S = SMOKE[g], best = bestSeen(g, pid), stock = stockOf(pid, g);
      var li = el('li', {class: 'good'});
      var head = el('div', {class: 'g-head'});
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, G.icon));
      head.appendChild(el('h3', null, G.name));
      if (G.home === pid) head.appendChild(el('span', {class: 'tag'}, G.kind ? 'Made here' : 'Grown here'));
      if (E.wanted(pid, g)) head.appendChild(el('span', {class: 'tag'}, 'Wanted here'));
      if (G.rare) head.appendChild(el('span', {class: 'tag hot'}, 'Contraband'));
      var nx = newsOn('spike', pid, g) || newsOn('glut', pid, g);
      if (nx) head.appendChild(el('span', {class: 'tag' + (nx.kind === 'spike' ? ' hot' : '')}, nx.kind === 'spike' ? '📰 In demand' : '📰 Glut'));
      if (bp) head.appendChild(el('span', {class: 'tag' + (stock ? '' : ' hot')}, stock ? stock + ' in stock' : 'Sold out'));
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
        var mb = maxBuy(pid, g);
        btn('Buy 1', 'Buy 1 bale of ' + G.name + ' for ' + bp + ' doubloons', 'b1' + g, 1, true, mb < 1);
        btn('Buy 5', 'Buy 5 bales of ' + G.name + ' for ' + fmt(costOf(pid, g, 5)) + ' doubloons', 'b5' + g, 5, true, mb < 5);
        btn('Buy max (' + mb + ')', 'Buy as many bales of ' + G.name + ' as you can: ' + mb + ' for ' + fmt(costOf(pid, g, mb)) + ' doubloons', 'bm' + g, mb, true, mb < 1);
      }
      btn('Sell 1', 'Sell 1 bale of ' + G.name + ' for ' + spr + ' doubloons', 's1' + g, 1, false, have < 1);
      btn('Sell all (' + have + ')', 'Sell all ' + have + ' bales of ' + G.name + ' for ' + fmt(payOf(pid, g, have)) + ' doubloons', 'sa' + g, have, false, have < 1);
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
    var A = place(from), B = place(to), mid = A.map, at = A.dock, len = 0, seas = [mid], v = null;
    for (var hops = 0; mid !== B.map && hops < 6; hops++) {
      var next = nextSea(mid, B.map), ex = next && MAPS[mid].exits.filter(function (e) { return e.to === next; })[0];
      if (!ex) break;
      var pt = exitPointFrom(ex, at), L = legLength(mid, at, pt);
      if (L === null) break;
      len += L;
      E.prepareMap(next);
      at = E.crossing(mid, ex, pt[0], pt[1]);
      mid = next; seas.push(mid);
    }
    if (mid === B.map) {
      var L2 = legLength(mid, at, B.dock);
      if (L2 !== null) { len += L2; v = {len: Math.round(len), days: Math.max(1, Math.round(len / 900)), seas: seas, to: to}; }
    }
    voyCache[key] = v;
    return v;
  }
  // Whole-number odds of meeting Customs or pirates on a passage. These are exactly the odds rolled.
  // Pirates watch the sea lanes every day you're out, and a rich cargo draws them like gulls: the longer and richer the run, the likelier a fight.
  function passageRisk(v) {
    var b = boost(), f = clamp(v.days / 2, 0.6, 1.5), top = 1, sea = v.to ? place(v.to).map : v.seas[v.seas.length - 1], lk = lawOf(sea), bs = standOf('brethren');
    v.seas.forEach(function (s) { top = Math.max(top, D.SEA_TIER[s] || 1); });
    // Customs at the far end: keener if that nation dislikes you, twice as likely in a crackdown.
    var c = openCount() || openParcels() ? Math.min(0.9, 0.15 * noseFactor() * f * stand(lk).law * (seaNews('crack', sea) ? 2 : 1)) : 0;
    var raid = v.seas.some(function (s) { return seaNews('raid', s); });
    var perDay = b && b.calm ? 0 : clamp(0.05 + 0.03 * top + 0.1 * Math.min(1, cargoValue() / 2500) - 0.02 * state.up.sails + (raid ? 0.08 : 0) + (bs === 1 ? 0.03 : bs === 0 ? 0.06 : 0), 0.04, 0.38);
    var p = 1 - Math.pow(1 - perDay, v.days);
    // A warship of a nation that's wary of you may be waiting at the far end.
    var navyNat = null, navy = 0;
    (D.SEA_NAVY[sea] || []).forEach(function (k) { var s = standOf(k); if (s <= 1 && (!navyNat || s < standOf(navyNat))) navyNat = k; });
    if (navyNat) navy = standOf(navyNat) === 0 ? 35 : 15;
    return {customs: Math.round(c * 100), pirates: Math.round(p * 100), second: v.days >= 3 ? Math.round(p * 50) : 0, top: top, navy: navy, navyNat: navyNat};
  }
  function sailText(days) { return days + (days === 1 ? ' day’s' : ' days’') + ' sail'; }
  function riskText(v) {
    var rk = passageRisk(v);
    return 'On the way: ' + (rk.customs ? 'Customs ' + rk.customs + '% chance, ' : '') + (rk.navy ? 'a ' + NAT[rk.navyNat].adj + ' warship ' + rk.navy + '% chance, ' : '') + 'pirates ' + rk.pirates + '% chance' + (rk.second ? ', and ' + rk.second + '% of a second pirate ship' : '') + '.';
  }
  // One turn: the days pass, Customs and pirates get their rolls (two run-ins at most), then you land.
  function passage(to) {
    var from = state.docked || (state.atBase ? 'hideout' : null), v = from && to !== from ? voyage(from, to) : null;
    if (!v) return false;
    var risk = passageRisk(v), meet = [];
    if (Math.random() * 100 < risk.customs) meet.push('customs');
    if (risk.navy && Math.random() * 100 < risk.navy) meet.push('navy');
    if (Math.random() * 100 < risk.pirates) {
      meet.push('pirate');
      if (Math.random() * 100 < risk.second * 2 && meet.length < 2) meet.push('pirate');
    }
    // A wanted pirate whose sea you cross may cross your path.
    state.jobs.forEach(function (j) { if (j.kind === 'bounty' && !j.hit && v.seas.indexOf(j.sea) >= 0 && meet.length < 3 && Math.random() < 0.4) meet.push('bounty:' + j.id); });
    if (from === 'hideout') leaveBase(true); else leavePort(true, true);
    auto = null; ship.vx = ship.vy = 0; wake = []; keys = {};
    // A passage takes whole days, so the day counter moves by exactly the days shown.
    state.dist += v.days * 900;
    var worn = boostTick(v.days * 900);
    v.seas.forEach(function (s) { state.flags['seen_' + s] = 1; });
    var news = dayTick();
    var P = place(to), m = enterMap(P.map), f = E.nearestFreePoint(m, P.dock[0], P.dock[1]);
    state.map = P.map; state.x = f[0]; state.y = f[1];
    justLeft = null;
    snapCamera();
    needRender = true;
    track('passage');
    var lead = '⛵ ' + v.days + ' ' + plural(v.days, 'day') + ' at sea from ' + place(from).name + '. It’s now day ' + day() + '.' + (worn ? ' ' + worn : '') + (news ? ' ' + news : '');
    var land = to === 'hideout' ? function () { enterBase(lead); } : function () { dock(to, lead); };
    var sea = v.seas.filter(function (s) { return (D.SEA_TIER[s] || 1) === risk.top; }).pop();
    // Each run-in hands over to the next; a ship that sinks never lands.
    function next() {
      var k = meet.shift();
      if (!k) return land();
      sfx('boom');
      if (k === 'customs') {
        var lk = lawOf(state.map);
        if (openCount() || openParcels()) customs({kind: 'customs', nation: lk, name: pick(NAT[lk].officers), cool: 0}, next);
        else next();
      } else if (k === 'navy') {
        var nv = makeNavy(enterMap(state.map), risk.navyNat);
        nv.cool = 0;
        fight(nv, next);
      } else if (k.indexOf('bounty:') === 0) {
        var bj = state.jobs.filter(function (j) { return 'bounty:' + j.id === k; })[0];
        if (!bj || bj.hit) return next();
        enterMap(bj.sea);
        var bn = npcs[bj.sea].filter(function (x) { return x.bounty === bj.id; })[0];
        if (!bn) return next();
        bn.cool = 0;
        fight(bn, next);
      } else {
        var n = makePirate(enterMap(sea));
        n.cool = 0;
        fight(n, next);
      }
    }
    if (meet.length) next();
    else {
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
  // Every port you know (and your hideout, once it's yours), nearest first, with the days and the dangers on the way.
  function passageList(from) {
    var ids = Object.keys(PORTS).filter(function (q) { return q !== from && portKnown(q); });
    if (legacy.base && from !== 'hideout') ids.push('hideout');
    var list = ids.map(function (q) { return {pid: q, v: voyage(from, q)}; }).filter(function (o) { return o.v; }).sort(function (a, b) { return a.v.len - b.v.len; });
    var box = el('div'), ul = el('ul', {class: 'goods'}), held = Object.keys(state.cargo);
    if (!list.length) { box.appendChild(el('p', null, 'No other ports on your chart yet. Ask around in the tavern.')); return box; }
    list.forEach(function (o) {
      var P = place(o.pid), base = o.pid === 'hideout', name = base ? 'Your hideout on ' + HIDE.name : P.name;
      var li = el('li', {class: 'good'}), head = el('div', {class: 'g-head'}), seen = state.seen[o.pid];
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, base ? '🏚️' : '⚓'));
      if (!base) head.appendChild(flagSwatch(natOf(o.pid)));
      head.appendChild(el('h3', null, name));
      head.appendChild(el('span', {class: 'tag'}, MAPS[P.map].short));
      li.appendChild(head);
      li.appendChild(el('p', {class: 'g-note'}, 'About ' + sailText(o.v.days) + '. ' + riskText(o.v)));
      var heard = state.news.filter(function (x) { return x.pid === o.pid || (x.sea && o.v.seas.indexOf(x.sea) >= 0); });
      if (heard.length) li.appendChild(el('p', {class: 'g-note'}, '📰 ' + heard.map(newsLine).join(' ')));
      var work = state.jobs.filter(function (j) { return j.to === o.pid || ((j.kind === 'supply' || (j.kind === 'bounty' && j.hit)) && j.from === o.pid); });
      if (work.length) li.appendChild(el('p', {class: 'g-note'}, '📋 Job here: ' + andList(work.map(jobTitle)) + '.'));
      if (level() >= 2 && state.food < o.v.days) li.appendChild(el('p', {class: 'g-note warn'}, '🍞 Not enough provisions: the crew will go hungry ' + (state.food ? 'after ' + state.food + ' ' + plural(state.food, 'day') : 'the whole way') + '.'));
      if (base) li.appendChild(el('p', {class: 'g-note'}, '🪙 ' + fmt(legacy.base.gold) + ' doubloons and ' + baleWord(baseBales()) + ' stashed there.'));
      else if (!seen) li.appendChild(el('p', {class: 'g-note'}, '📒 You haven’t seen this market yet.'));
      else {
        var sells = Object.keys(seen.b).map(function (g) { return GOODS[g].name + ' ' + seen.b[g]; });
        if (sells.length) li.appendChild(el('p', {class: 'g-note'}, '📒 Sells ' + andList(sells) + ' (day ' + seen.d + ').'));
        var bestG = null;
        held.forEach(function (g) { if (seen.s[g] && (!bestG || seen.s[g] > seen.s[bestG])) bestG = g; });
        if (bestG) li.appendChild(el('p', {class: 'g-note'}, '📒 Pays best for your hold: ' + seen.s[bestG] + ' for ' + GOODS[bestG].name + '.'));
      }
      var btns = el('div', {class: 'g-btns'}), b = el('button', {type: 'button', 'data-key': 'go' + o.pid, 'aria-label': 'Quick passage to ' + name + ', about ' + o.v.days + ' ' + plural(o.v.days, 'day')}, '⛵ Sail to ' + (base ? 'your hideout' : P.name));
      b.addEventListener('click', function () { passage(o.pid); });
      btns.appendChild(b);
      li.appendChild(btns);
      ul.appendChild(li);
    });
    box.appendChild(ul);
    return box;
  }
  function renderRoutes(pid, panel) {
    panel.appendChild(el('p', {class: 'hint'}, 'Pick a port you know and your crew sails straight there. The days pass, prices move, and you might meet Customs, pirates or a surprise on the way. The longer the trip and the richer your hold, the likelier a fight.'));
    panel.appendChild(el('h3', null, '🧭 Quick passage'));
    panel.appendChild(passageList(pid));
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
    else if (k === 'base') r = !!legacy.base;
    else if (k === 'gold') r = state.gold >= +v;
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
      else if (k === 'base' && v === 'know' && !baseKnown()) {
        state.flags.baseKnown = 1;
        reveal(HIDE.map, HIDE.at[0], HIDE.at[1], 140);
        say('🧭 The cave on ' + HIDE.name + ' (' + MAPS[HIDE.map].short + ') is now on your chart.');
      }
      else if (k === 'base' && v === 'buy' && !legacy.base && state.gold >= HIDE.price) {
        state.gold -= HIDE.price;
        legacy.base = {lvl: 0, gold: 0, bales: {}, basis: {}, grow: {beds: [], seeds: {}}};
        state.flags.baseKnown = 1;
        saveLegacy();
        sfx('fanfare');
        track('hideout');
        say('🗝️ The cave on ' + HIDE.name + ' is yours. Whatever you leave there stays there, even if your ship goes down.');
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
    if (PORTS[pid].history) {
      var hist = el('p', {class: 'history'});
      hist.appendChild(flagSwatch(natOf(pid)));
      hist.appendChild(document.createTextNode(' 📜 Real history: ' + PORTS[pid].history));
      panel.appendChild(hist);
    }
    seedTrader(pid, panel);
    if (level() >= 4 && D.FIRE_PORTS.indexOf(pid) >= 0) {
      var fbox = el('div', {class: 'repair'});
      fbox.appendChild(el('p', null, '🔥 Fire ship: an old hulk packed with tar, powder and brimstone, with a skeleton crew who light the fuses and row clear. In a fight, send her into one enemy ship. ' + (state.fireship ? 'One already sails with you.' : 'You can lead one at a time.')));
      var fb = el('button', {type: 'button', class: 'secondary', 'data-key': 'fireship', 'aria-label': state.fireship ? null : 'Hire a fire ship for ' + fmt(FIRE_COST) + ' doubloons'}, state.fireship ? 'One is enough' : 'Hire a fire ship · ' + fmt(FIRE_COST) + ' 🪙');
      fb.disabled = !!state.fireship || state.gold < FIRE_COST;
      fb.addEventListener('click', function () {
        if (state.fireship || state.gold < FIRE_COST) return;
        state.gold -= FIRE_COST; state.fireship = 1; sfx('fanfare'); track('hire-fireship');
        say('🔥 A low, black hulk falls in astern of you, reeking of tar. Her skeleton crew waves cheerfully and nobody lights a pipe.');
        save(); renderPanel('fireship');
      });
      fbox.appendChild(fb);
      var fh = el('p', {class: 'history'}, '📜 Real history: ' + D.FIRESHIP_NOTE);
      fbox.appendChild(fh);
      panel.appendChild(fbox);
    }
    if (level() >= 2) {
      panel.appendChild(el('h4', null, '📰 Harbour news'));
      if (!state.news.length) panel.appendChild(el('p', {class: 'hint'}, 'Quiet week. Nothing worth repeating.'));
      else {
        var nl = el('ul', {class: 'checks'});
        state.news.forEach(function (x) { var li = el('li'); li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, '📰')); li.appendChild(document.createTextNode(newsLine(x))); nl.appendChild(li); });
        panel.appendChild(nl);
      }
    }
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
      var now = k === 'hold' ? 'Holds ' + U.levels[lvl] + ' bales now.' : k === 'hull' ? U.levels[lvl] + ' hull points now.' : k === 'lavender' ? (lvl ? 'Fitted.' : 'Not fitted yet.')
        : k === 'secret' ? (lvl ? 'Hides ' + U.levels[lvl] + ' bales now.' : 'Not built yet.') : 'Level ' + lvl + ' of ' + max + '.';
      li.appendChild(el('p', {class: 'g-note'}, U.note + ' ' + now));
      var btns = el('div', {class: 'g-btns'});
      if (lvl < max) {
        var cost = U.cost[lvl], label = k === 'hold' ? 'Grow to ' + U.levels[lvl + 1] + ' bales' : k === 'hull' ? 'Strengthen to ' + U.levels[lvl + 1] + ' points' : k === 'lavender' ? 'Fit it'
          : k === 'secret' ? (lvl ? 'Hide ' + U.levels[lvl + 1] + ' bales' : 'Build it to hide ' + U.levels[1] + ' bales') : 'Upgrade to level ' + (lvl + 1);
        var b = el('button', {type: 'button', 'data-key': 'up' + k, 'aria-label': label + ' for ' + fmt(cost) + ' doubloons'}, label + ' · ' + fmt(cost) + ' 🪙');
        b.disabled = state.gold < cost;
        b.addEventListener('click', function () {
          if (state.gold < cost) return;
          state.gold -= cost; state.up[k]++;
          if (k === 'hull') state.hull += U.levels[state.up.hull] - U.levels[state.up.hull - 1];
          sfx('fanfare');
          say('🔨 ' + U.name + ': done! ' + (k === 'hold' ? 'Your hold now takes ' + capacity() + ' bales.' : k === 'hull' ? 'Your ship now has ' + hullMax() + ' hull points.'
            : k === 'secret' ? 'Your ' + secretCap() + ' most valuable bales now ride where Customs and pirates never look.' : 'The shipwright wipes their hands and grins.'));
          checkGoals(); save(); renderPanel('up' + k);
        });
        btns.appendChild(b);
      } else btns.appendChild(el('span', {class: 'tag'}, 'Fully fitted'));
      li.appendChild(btns);
      ul.appendChild(li);
    });
    // Decoys: from level 3, a cheap sloop that sails in your wake and leads trouble away.
    if (level() >= 3) {
      var dli = el('li', {class: 'good'}), dh = el('div', {class: 'g-head'}), dbtns = el('div', {class: 'g-btns'});
      dh.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, '🚩'));
      dh.appendChild(el('h3', null, 'Decoy sloop'));
      dli.appendChild(dh);
      dli.appendChild(el('p', {class: 'g-note'}, 'A cheap, quick little sloop with a skeleton crew that sails in your wake. When pirates, a warship or the customs catch you, send her to harass them and lead the chase away. It always works, and you lose her. You have ' + state.decoys + ' of ' + DECOY_MAX + '.'));
      if (state.decoys < DECOY_MAX) {
        var db = el('button', {type: 'button', 'data-key': 'decoy', 'aria-label': 'Buy a decoy sloop for ' + fmt(DECOY_COST) + ' doubloons'}, 'Buy a decoy · ' + fmt(DECOY_COST) + ' 🪙');
        db.disabled = state.gold < DECOY_COST;
        db.addEventListener('click', function () {
          if (state.gold < DECOY_COST || state.decoys >= DECOY_MAX) return;
          state.gold -= DECOY_COST; state.decoys++; sfx('fanfare'); track('buy-decoy');
          say('🚩 A decoy sloop falls in astern of you, and her crew waves. You now sail with ' + state.decoys + ' ' + plural(state.decoys, 'decoy') + '.');
          save(); renderPanel('decoy');
        });
        dbtns.appendChild(db);
      } else dbtns.appendChild(el('span', {class: 'tag'}, 'Two decoys is all you can lead'));
      dli.appendChild(dbtns);
      ul.appendChild(dli);
    }
    panel.appendChild(ul);
  }

  /* ---------- goals and the captain's log ---------- */
  // relic: what the goal earns. Relics help for the rest of the voyage and go down with the ship.
  function goalList() {
    var visited = Object.keys(state.visited).length, strains = STRAINS.filter(function (g) { return state.collected[g]; }).length, lv = level();
    var reqs = Object.keys(QUESTS).filter(function (q) { return state.quests[q] === 'done'; }).length;
    return [
      {id: 'full', text: 'Fill your hold to the brim', done: !!state.flags.full},
      {id: 'k1', text: 'Have 1,000 doubloons in your purse', done: !!state.flags.k1},
      {id: 'pillage', text: 'Pillage a merchant ship', done: state.pillaged > 0},
      {id: 'pirate', text: 'Beat a pirate ship in battle', done: state.sunk > 0},
      {id: 'ports5', text: 'Drop anchor in 5 ports', n: Math.min(5, visited) + ' of 5', done: visited >= 5, relic: 'spyglass'},
      {id: 'stash', text: 'Stash gold or cargo in a hideout', done: !!state.flags.stashed},
      {id: 'lv5', text: 'Reach level 5, ' + title(5), done: lv >= 5},
      {id: 'pirates3', text: 'Beat 3 pirate ships', n: Math.min(3, state.sunk) + ' of 3', done: state.sunk >= 3, relic: 'tooth'},
      {id: 'requests', text: 'Finish 3 requests for tavern folk', n: Math.min(3, reqs) + ' of 3', done: reqs >= 3, relic: 'wig'},
      {id: 'bricks', text: 'Hit enemy ships with 10 bales of Brick Weed', n: Math.min(10, state.bricks) + ' of 10', done: state.bricks >= 10, relic: 'goldbrick'},
      {id: 'maps', text: 'Dig up 3 treasure maps', n: Math.min(3, state.dug) + ' of 3', done: state.dug >= 3, relic: 'doubloon'},
      {id: 'sales', text: 'Sell 5,000 doubloons’ worth of cargo', n: fmt(Math.min(5000, state.earned)) + ' of 5,000', done: state.earned >= 5000, relic: 'seal'},
      {id: 'big', text: 'Beat a pirate frigate or man-o’-war', done: !!state.flags.bigwin, relic: 'figure'},
      {id: 'jobs10', text: 'Finish 10 jobs from the job boards', n: Math.min(10, state.jobsDone) + ' of 10', done: state.jobsDone >= 10},
      {id: 'bounty3', text: 'Collect 3 bounties on wanted pirates', n: Math.min(3, state.bounties) + ' of 3', done: state.bounties >= 3},
      {id: 'honour', text: 'Be Honoured by a nation', done: NAT_ORDER.some(function (k) { return standOf(k) === 4; })},
      {id: 'navy', text: 'Beat a navy warship', done: !!state.flags.navywin},
      {id: 'ports', text: 'Drop anchor in all ' + NPORTS + ' ports', n: visited + ' of ' + NPORTS, done: visited >= NPORTS},
      {id: 'pieces', text: 'Find the 3 pieces of Captain Featherstone’s map', n: pieces() + ' of 3', done: pieces() >= 3},
      {id: 'emerald', text: 'Dig up the Emerald Bale', done: !!state.found.emerald, relic: 'compass'},
      {id: 'strains', text: 'Collect all ' + STRAINS.length + ' strains', n: strains + ' of ' + STRAINS.length, done: strains >= STRAINS.length},
      {id: 'boss', text: 'Beat ' + D.BOSS.captain + ' of ' + D.BOSS.ship + ' (sails the Spanish Main from level ' + D.BOSS.level + ')', done: !!state.flags.boss, relic: 'flag'},
      {id: 'lv10', text: 'Reach level 10, ' + title(10), done: lv >= 10}
    ];
  }
  // Sail colours and flags, earned once and kept for every voyage after.
  function checkUnlocks() {
    var got = [];
    function earn(kind, key, ok) {
      if (!ok || legacy[kind][key]) return;
      legacy[kind][key] = 1;
      got.push(kind === 'sails' ? SAILS[key].name.toLowerCase() + ' sails' : 'the ' + FLAGS[key].name.toLowerCase() + ' flag');
    }
    earn('sails', 'black', state.sunk > 0);
    earn('sails', 'crimson', !!state.flags.bigwin);
    earn('sails', 'gold', state.gold >= 5000);
    earn('sails', 'emerald', !!state.found.emerald);
    earn('flags', 'kraken', !!state.collected.kraken);
    earn('flags', 'crown', level() >= 10);
    if (!got.length) return '';
    saveLegacy();
    return '🎨 Earned for every voyage: ' + andList(got) + '. Dress your ship in Settings, under Captain and ship.';
  }
  function checkGoals() {
    if (!state) return;
    if (cargoCount() + jobLoad() >= capacity()) state.flags.full = 1;
    if (state.gold >= 1000) state.flags.k1 = 1;
    var msgs = [];
    goalList().forEach(function (g) {
      if (!g.done) return;
      var R = g.relic && RELICS[g.relic], gain = !!(R && !state.relics[g.relic]);
      if (gain) { state.relics[g.relic] = 1; if (R.hull) state.hull = Math.min(hullMax(), state.hull + R.hull); }
      if (!state.flags['g_' + g.id]) {
        state.flags['g_' + g.id] = 1;
        msgs.push('🏆 Goal complete: ' + g.text.replace(/ \(.*\)$/, '') + '!' + (gain ? ' Your reward: ' + R.icon + ' the ' + R.name + '. ' + R.does : ''));
      } else if (gain) msgs.push('🎁 For a goal you’d already reached: ' + R.icon + ' the ' + R.name + '. ' + R.does);
    });
    var un = checkUnlocks();
    if (un) msgs.push(un);
    if (msgs.length) { sfx('fanfare'); say(msgs.join(' ')); }
    if (state.docked && openDialogEl() === $('dlg-port')) $('port-status').textContent = portStatus();
    if (state.atBase && openDialogEl() === $('dlg-hideout')) $('base-status').textContent = baseStatus();
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
    var lv = levelUp, wrap = el('div'), un = lv > 0 ? unlockText(lv) : '';
    levelUp = 0;
    if (!state.pts && !un) return;
    function draw(key) {
      if (!state.pts && !wrap.childNodes.length && un) return;
      wrap.textContent = '';
      wrap.appendChild(el('p', {class: 'win'}, state.pts ? 'Skill points to spend: ' + state.pts + '.' : 'All spent. Fair winds, Captain.'));
      wrap.appendChild(skillList(function (k) { draw(k); refocus(wrap, k, $('note-ok')); }));
    }
    draw();
    note(lv > 0 ? '🎖️ Level ' + lv + ': ' + title(lv) + '!' : '⭐ A new skill point',
      [lv > 0 ? 'Word of your exploits is spreading through every tavern in the Caribbean.' : '', state.pts ? 'Pick a skill to train now, or later from your captain’s log.' : ''].filter(Boolean).join(' ') + (un ? '\n\n' + un : ''), wrap);
    var first = wrap.querySelector('[data-key^="sk"]');
    if (first) setTimeout(function () { first.focus(); }, 0);
  }

  function openLog() { renderLog(); openDialog($('dlg-log'), $('log-close')); }
  function renderLog(key) {
    var b = $('log-body'), lv = level(), next = D.LEVELS[lv], st = stats();
    b.textContent = '';
    b.appendChild(el('h3', {class: 'log-top'}, '🏴‍☠️ ' + captainName() + ', captain of ' + shipName()));
    b.appendChild(el('p', {class: 'hint'}, state.gentle ? '🌤️ Gentle seas: a beaten ship limps away and the voyage goes on, though pirates who take you over keep your open hold and nine doubloons in ten.' : '⚠️ Real danger: a ship sunk in battle ends the voyage. Your hideout and the colours you earn carry over.'));
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
    b.appendChild(el('p', null, '🛡️ Hull ' + state.hull + ' of ' + st.hullMax + ' · 💣 Broadside about ' + st.fire + ' damage, ' + state.shot + ' ' + plural(state.shot, 'cannonball') + ' left · 👥 Boarders: level ' + st.crew + ' · ⛵ Sails: level ' + st.sails +
      (lv >= 2 ? ' · 🍞 ' + state.food + ' ' + plural(state.food, 'day') + ' of provisions' + (hungry() ? ' (the crew is hungry)' : '') : '') + (state.decoys ? ' · 🚩 ' + state.decoys + ' ' + plural(state.decoys, 'decoy') : '') + (state.fireship ? ' · 🔥 a fire ship' : '')));
    if (legacy.base) b.appendChild(el('p', null, '🏚️ Your hideout on ' + HIDE.name + ': ' + fmt(legacy.base.gold) + ' doubloons and ' + baseBales() + ' of ' + baseCap() + ' bales stashed.'));
    var bz = boost();
    if (bz) b.appendChild(el('p', {class: 'win'}, '🔥 ' + bz.name + ': ' + bz.does + ' About ' + boostLeft() + ' ' + plural(boostLeft(), 'day') + ' left.'));
    if (state.pts) b.appendChild(el('p', {class: 'win'}, 'You have ' + state.pts + ' skill ' + plural(state.pts, 'point') + ' to spend.'));
    b.appendChild(skillList(function (k) { renderLog(k); }));
    renderPowers(b);
    b.appendChild(el('h3', null, 'Goals'));
    var ul = el('ul', {class: 'checks'});
    goalList().forEach(function (g) {
      var li = el('li', {class: g.done ? 'done' : ''});
      li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, g.done ? '✅' : '⬜'));
      li.appendChild(el('span', {class: 'sr-only'}, g.done ? 'Done: ' : 'Not yet: '));
      li.appendChild(document.createTextNode(g.text + (g.n ? ' (' + g.n + ')' : '') + (g.relic ? '. Reward: ' + RELICS[g.relic].name : '')));
      ul.appendChild(li);
    });
    b.appendChild(ul);
    var rl = Object.keys(RELICS).filter(function (r) { return state.relics[r]; });
    b.appendChild(el('h3', null, 'Relics: ' + rl.length + ' of ' + Object.keys(RELICS).length));
    if (!rl.length) b.appendChild(el('p', {class: 'hint'}, 'Some goals earn a relic, a one-of-a-kind find that helps for the rest of the voyage. Relics go down with the ship.'));
    else {
      var rel = el('ul', {class: 'checks'});
      rl.forEach(function (r) {
        var li = el('li');
        li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, RELICS[r].icon));
        li.appendChild(document.createTextNode(RELICS[r].name + ': ' + RELICS[r].does));
        rel.appendChild(li);
      });
      b.appendChild(rel);
    }
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
    b.appendChild(el('h3', null, 'Cargo hold: ' + (cargoCount() + jobLoad()) + ' of ' + capacity()));
    if (jobLoad()) b.appendChild(el('p', {class: 'hint'}, '📋 ' + jobLoad() + ' of those spaces hold job cargo' + (parcels() ? ', including ' + parcels() + ' sealed ' + plural(parcels(), 'parcel') + (secretCap() ? ' that ride in your smuggler’s hold first' : '') : '') + '.'));
    if (secretCap()) b.appendChild(el('p', {class: 'hint'}, '🕳️ Your smuggler’s hold hides your ' + secretCap() + ' most valuable bales (' + hiddenCount() + ' in it now). Customs never find them and pirates never take them.'));
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
    if (boardShown()) b.appendChild(boardBox(BOARD.max));
    if (legacy.fame.length) {
      b.appendChild(el('h3', null, 'Hall of fame'));
      b.appendChild(fameList(legacy.fame.length));
    }
    if (key) refocus(b, key, $('log-close'));
  }

  /* ---------- your hideout on Île-à-Vache: what you leave there outlives any one ship ---------- */
  function baseBales() { var n = 0; if (legacy.base) for (var g in legacy.base.bales) n += legacy.base.bales[g]; return n; }
  function baseCap() { return legacy.base ? HIDE.caps[legacy.base.lvl] : 0; }
  function baseStatus() {
    return '🪙 ' + fmt(state.gold) + ' doubloons aboard · 📦 ' + cargoCount() + ' of ' + capacity() + ' bales aboard · 🛡️ Hull ' + state.hull + ' of ' + hullMax();
  }
  function enterBase(lead) {
    auto = null; ship.vx = ship.vy = 0;
    state.flags.baseKnown = 1;
    if (!legacy.base) {
      justLeft = 'hideout';
      say((lead ? lead + ' ' : '') + '🔒 The cave door on ' + HIDE.name + ' is locked tight. Grandpère Toussaint in Petit-Goâve has the key.');
      return;
    }
    var m = enterMap(HIDE.map), f = E.nearestFreePoint(m, HIDE.dock[0], HIDE.dock[1]), first = !state.flags.baseVisit;
    state.map = HIDE.map; state.x = f[0]; state.y = f[1]; state.docked = null; state.atBase = true;
    state.flags.baseVisit = 1;
    reveal(HIDE.map, HIDE.at[0], HIDE.at[1], 170);
    sfx('splash');
    checkGoals();
    save();
    updateWhere(true);
    $('base-title').textContent = '🏚️ Your hideout on ' + HIDE.name;
    renderHideout();
    openDialog($('dlg-hideout'), $('base-body').querySelector('button:not([disabled])') || $('base-leave'));
    var msg = (lead ? lead + ' ' : '') + (first ? '🗝️ The rusty key turns, the door groans, and the cave smells of goat and old adventures.' : '');
    if (msg) say(msg.trim());
  }
  function leaveBase(silent) {
    if (!state.atBase) return;
    state.atBase = false;
    justLeft = 'hideout';
    grace = 1.2;
    closeDialog('dlg-hideout');
    if (!silent) say('⛵ You lock the cave door and cast off from ' + HIDE.name + '.');
    updateWhere(true);
    save();
    focusSea();
  }
  /* ---------- the grow: two beds above the hideout ---------- */
  function growOf() { var B = legacy.base; if (!B.grow) B.grow = {beds: [], seeds: {}}; return B.grow; }
  // A bed planted on an earlier voyage has had all the time it needs.
  function bedReady(b) { return !!b && (b.voy !== state.seed || day() >= b.ready); }
  function crossOf(a, b) {
    for (var i = 0; i < CROSSES.length; i++) { var c = CROSSES[i]; if ((c[0] === a && c[1] === b) || (c[0] === b && c[1] === a)) return c[2]; }
    return null;
  }
  function parentsOf(id) { for (var i = 0; i < CROSSES.length; i++) if (CROSSES[i][2] === id) return CROSSES[i]; return null; }
  function geneGood(id) { return (GENES[id] && GENES[id].good) || 'g_home'; }
  function buySeed(id) {
    var Gr = legacy.base && growOf();
    if (!Gr || !GENES[id] || GENES[id].kind !== 'landrace' || Gr.seeds[id] || state.gold < GROW.price) return false;
    state.gold -= GROW.price; Gr.seeds[id] = 1;
    saveLegacy(); save(); track('buy-seed');
    return true;
  }
  function plant(i, id) {
    var Gr = growOf();
    if (i < 0 || i >= GROW.beds || Gr.beds[i] || !Gr.seeds[id]) return false;
    Gr.beds[i] = {s: id, voy: state.seed, ready: day() + GROW.days, x: 0};
    track('plant');
    return true;
  }
  function harvest(i) {
    var Gr = growOf(), b = Gr.beds[i];
    if (!bedReady(b)) return null;
    var g = geneGood(b.s), n = Math.min(GROW.yield, baseCap() - baseBales());
    if (n <= 0) return null;
    Gr.beds[i] = null;
    legacy.base.bales[g] = (legacy.base.bales[g] || 0) + n;
    track('harvest');
    return {g: g, n: n, s: b.s};
  }
  // Both beds in flower: pollinate one with the other. A known breeding line gives seeds of the new strain for good.
  function crossBeds() {
    var Gr = growOf(), a = Gr.beds[0], b = Gr.beds[1];
    if (!bedReady(a) || !bedReady(b) || a.x || b.x) return null;
    a.x = b.x = 1;
    if (a.s === b.s) return {same: true};
    var r = crossOf(a.s, b.s);
    if (!r) return {none: true};
    var fresh = !Gr.seeds[r];
    Gr.seeds[r] = 1;
    track('cross');
    return {r: r, fresh: fresh};
  }
  function renderGrow(body, btn) {
    var Gr = growOf(), known = Object.keys(GENES).filter(function (id) { return Gr.seeds[id]; }), room = baseCap() - baseBales();
    body.appendChild(el('h3', null, '🌱 The grow'));
    body.appendChild(el('p', {class: 'hint'}, 'Two beds in a sunny clearing above the cave. A crop takes ' + GROW.days + ' days and puts ' + baleWord(GROW.yield) + ' in your stash. When both beds are in flower, cross them: if the pair is a real breeding line, you keep seeds of the new strain for good. Your seed chest and your beds outlast any ship.'));
    if (!known.length) body.appendChild(el('p', null, '🧺 Your seed chest is empty. Seed traders in the taverns of ' + andList(['willemstad', 'cartagena', 'veracruz'].map(function (p) { return PORTS[p].name; })) + ' sell landrace seeds.'));
    var ul = el('ul', {class: 'goods'});
    for (var i = 0; i < GROW.beds; i++) (function (i) {
      var b = Gr.beds[i], ready = bedReady(b), li = el('li', {class: 'good'}), head = el('div', {class: 'g-head'}), bx = el('div', {class: 'g-btns'});
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, b ? (ready ? '🌳' : '🌱') : '🟫'));
      head.appendChild(el('h3', null, 'Bed ' + (i + 1) + ': ' + (b ? GENES[b.s].name : 'empty')));
      li.appendChild(head);
      if (b) {
        var left = Math.max(1, b.ready - day()), g = geneGood(b.s);
        li.appendChild(el('p', {class: 'g-note'}, ready ? 'In full flower. It harvests as ' + baleWord(GROW.yield) + ' of ' + GOODS[g].name + '.' + (b.x ? ' Already crossed this season.' : '')
          : 'Growing: ready in ' + left + ' ' + plural(left, 'day') + ', on day ' + b.ready + '. It will harvest as ' + GOODS[g].name + '.'));
        if (ready) btn(bx, room > 0 ? 'Harvest' : 'Stash is full', room > 0 ? 'Harvest bed ' + (i + 1) + ', ' + GENES[b.s].name + ', into your stash' : null, 'hv' + i, function () {
          var h = harvest(i);
          if (h) baseDone('🌿 You harvest ' + baleWord(h.n) + ' of ' + GOODS[h.g].name + ' and hang them to dry in the cave.' + (h.n < GROW.yield ? ' The stash is full, so the goats get the rest.' : ''), 'hv' + i);
        }, room < 1);
      } else if (known.length) {
        var sid = 'seed-' + i, sel = el('select', {id: sid});
        known.forEach(function (id) { sel.appendChild(el('option', {value: id}, GENES[id].name)); });
        var row = el('p', {class: 'lookup'});
        row.appendChild(el('label', {for: sid}, 'Seeds for bed ' + (i + 1)));
        row.appendChild(sel);
        li.appendChild(row);
        btn(bx, 'Plant', 'Plant the chosen seeds in bed ' + (i + 1), 'pl' + i, function () {
          if (plant(i, sel.value)) baseDone('🌱 You plant ' + GENES[sel.value].name + ' in bed ' + (i + 1) + '. It will be ready on day ' + growOf().beds[i].ready + '.', 'pl' + i);
        });
      } else li.appendChild(el('p', {class: 'g-note'}, 'Bare earth, waiting for seeds.'));
      li.appendChild(bx);
      ul.appendChild(li);
    })(i);
    body.appendChild(ul);
    var A = Gr.beds[0], Bd = Gr.beds[1];
    if (bedReady(A) && bedReady(Bd) && !A.x && !Bd.x) {
      var cb = el('div', {class: 'g-btns'});
      btn(cb, '🧬 Cross the two beds', 'Cross ' + GENES[A.s].name + ' with ' + GENES[Bd.s].name, 'cross', function () {
        var c = crossBeds();
        if (!c) return;
        var msg;
        if (c.same) msg = '🧬 Crossing ' + GENES[A.s].name + ' with itself just gives you more of the same. Try two different plants.';
        else if (c.none) msg = '🧬 You dust one bed with the other’s pollen. The seeds come up a scraggly backyard mix, nothing a breeder would keep. Check your breeder’s notebook for real lines.';
        else {
          var R = GENES[c.r];
          sfx('fanfare');
          msg = '🧬 You dust one bed with the other’s pollen and save the seeds: ' + R.name + '. ' + (c.fresh ? 'New in your seed chest!' + (R.kind === 'strain' ? gainXp(GROW.xp) : '') : 'You already had those.') + ' ' + R.note;
        }
        baseDone(msg, 'cross');
      });
      body.appendChild(cb);
    }
    // The breeder's notebook: every named strain, its real lineage, and what you've bred so far.
    var nb = el('details', {class: 'notebook'}), names = Object.keys(GENES).filter(function (id) { return GENES[id].kind === 'strain'; });
    nb.appendChild(el('summary', null, '📓 Breeder’s notebook: ' + names.filter(function (id) { return Gr.seeds[id]; }).length + ' of ' + names.length + ' strains bred'));
    var nl = el('ul', {class: 'checks'});
    names.forEach(function (id) {
      var R = GENES[id], P = parentsOf(id), has = !!Gr.seeds[id], li = el('li', {class: has ? 'done' : ''});
      li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, has ? '✅' : '📜'));
      li.appendChild(el('span', {class: 'sr-only'}, has ? 'Bred: ' : 'Not yet: '));
      li.appendChild(document.createTextNode(R.name + ': cross ' + GENES[P[0]].name + ' with ' + GENES[P[1]].name + '. ' + R.note));
      nl.appendChild(li);
    });
    nb.appendChild(nl);
    D.GROW_LESSONS.forEach(function (t) { nb.appendChild(el('p', {class: 'history'}, '🧬 ' + t)); });
    body.appendChild(nb);
  }
  // The seed trader: landrace seeds in three taverns. Packets go to the seed chest at your hideout.
  function seedTrader(pid, panel) {
    var here = Object.keys(GENES).filter(function (id) { return GENES[id].from === pid; });
    if (!here.length) return;
    var box = el('div', {class: 'repair'}), names = here.map(function (id) { return GENES[id].name; });
    if (!legacy.base) {
      box.appendChild(el('p', null, '🌱 A seed trader here sells ' + andList(names) + ' seeds, but you’d need somewhere to grow them, like the cave Grandpère Toussaint in Petit-Goâve has for sale.'));
      panel.appendChild(box);
      return;
    }
    var Gr = growOf();
    box.appendChild(el('p', null, '🌱 Seed trader: landrace seeds, ' + fmt(GROW.price) + ' doubloons a packet. A packet goes in the seed chest at your hideout and stays there for good, ship or no ship.' +
      (pid === 'willemstad' ? ' These came by way of Amsterdam: the Dutch East India Company traded in Persia, India and Siam.' : '')));
    here.forEach(function (id) {
      var R = GENES[id];
      box.appendChild(el('p', {class: 'g-note'}, R.name + ': ' + R.note));
      if (Gr.seeds[id]) { box.appendChild(el('span', {class: 'tag'}, R.name + ' is in your seed chest')); return; }
      var b = el('button', {type: 'button', class: 'secondary', 'data-key': 'seed-' + id, 'aria-label': 'Buy ' + R.name + ' seeds for ' + fmt(GROW.price) + ' doubloons'}, 'Buy ' + R.name + ' seeds · ' + fmt(GROW.price) + ' 🪙');
      b.disabled = state.gold < GROW.price;
      b.addEventListener('click', function () {
        if (!buySeed(id)) return;
        sfx('coin');
        say('🌱 A paper twist of ' + R.name + ' seeds goes into your coat. They’ll wait in the seed chest at your hideout.');
        renderPanel('seed-' + id);
      });
      box.appendChild(b);
    });
    panel.appendChild(box);
  }
  // Bales keep what you paid for them, so selling them later earns renown only for the real profit.
  function stash(g, n) {
    var B = legacy.base, have = state.cargo[g] || 0;
    n = Math.min(n, have, baseCap() - baseBales());
    if (n <= 0) return 0;
    var cost = have ? Math.round((state.basis[g] || 0) * n / have) : 0;
    takeCargo(g, n);
    B.bales[g] = (B.bales[g] || 0) + n;
    if (cost) B.basis[g] = (B.basis[g] || 0) + cost;
    state.flags.stashed = 1;
    return n;
  }
  function unstash(g, n) {
    var B = legacy.base, have = B.bales[g] || 0;
    n = Math.min(n, have, space());
    if (n <= 0) return 0;
    var cost = Math.round((B.basis[g] || 0) * n / have);
    addCargo(g, n);
    if (cost) state.basis[g] = (state.basis[g] || 0) + cost;
    B.bales[g] = have - n;
    B.basis[g] = Math.max(0, (B.basis[g] || 0) - cost);
    if (!B.bales[g]) { delete B.bales[g]; delete B.basis[g]; }
    return n;
  }
  function baseDone(msg, key) {
    sfx('coin');
    saveLegacy();
    checkGoals();
    save();
    renderHideout(key);
    say(msg);
  }
  function renderHideout(keepKey) {
    var B = legacy.base, body = $('base-body');
    if (!B) return;
    body.textContent = '';
    $('base-status').textContent = baseStatus();
    body.appendChild(el('p', {class: 'hint'}, 'Whatever you leave in the cave stays here, even if your ship goes down. Your next voyage can pick it up.'));
    function btn(box, label, aria, key, fn, off) {
      var b = el('button', {type: 'button', 'data-key': key, 'aria-label': aria || null}, label);
      b.disabled = !!off;
      b.addEventListener('click', fn);
      box.appendChild(b);
    }
    // The strongbox
    body.appendChild(el('h3', null, '🪙 Strongbox: ' + fmt(B.gold) + ' doubloons'));
    var gb = el('div', {class: 'g-btns'}), half = Math.floor(state.gold / 2);
    function leave(n, key) { return function () { n = Math.min(n, state.gold); if (n <= 0) return; state.gold -= n; B.gold += n; state.flags.stashed = 1; baseDone('🪙 You lock ' + fmt(n) + ' doubloons in the strongbox. It holds ' + fmt(B.gold) + ' now.', key); }; }
    function take(n, key) { return function () { n = Math.min(n, B.gold); if (n <= 0) return; B.gold -= n; state.gold += n; baseDone('🪙 You take ' + fmt(n) + ' doubloons from the strongbox.', key); }; }
    btn(gb, 'Leave 100', 'Leave 100 doubloons in the strongbox', 'gl100', leave(100, 'gl100'), state.gold < 100);
    btn(gb, 'Leave half (' + fmt(half) + ')', 'Leave half your gold, ' + fmt(half) + ' doubloons, in the strongbox', 'glhalf', leave(half, 'glhalf'), half < 1);
    btn(gb, 'Leave all (' + fmt(state.gold) + ')', 'Leave all ' + fmt(state.gold) + ' of your doubloons in the strongbox', 'glall', leave(state.gold, 'glall'), state.gold < 1);
    btn(gb, 'Take 100', 'Take 100 doubloons from the strongbox', 'gt100', take(100, 'gt100'), B.gold < 100);
    btn(gb, 'Take all (' + fmt(B.gold) + ')', 'Take all ' + fmt(B.gold) + ' doubloons from the strongbox', 'gtall', take(B.gold, 'gtall'), B.gold < 1);
    body.appendChild(gb);
    // The stash
    var inCave = baseBales(), room = baseCap() - inCave;
    body.appendChild(el('h3', null, '📦 Stash: ' + inCave + ' of ' + baseCap() + ' bales'));
    var goods = ORDER.filter(function (g) { return state.cargo[g] || B.bales[g]; });
    if (!goods.length) body.appendChild(el('p', null, 'Nothing aboard and nothing in the cave but a goat-shaped smell.'));
    var ul = el('ul', {class: 'goods'});
    goods.forEach(function (g) {
      var G = GOODS[g], have = state.cargo[g] || 0, kept = B.bales[g] || 0, li = el('li', {class: 'good'}), head = el('div', {class: 'g-head'});
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, G.icon));
      head.appendChild(el('h3', null, G.name));
      li.appendChild(head);
      li.appendChild(el('p', {class: 'g-prices'}, 'Aboard: ' + have + ' · In the cave: ' + kept));
      var bx = el('div', {class: 'g-btns'}), sAll = Math.min(have, room), tAll = Math.min(kept, space());
      function mv(fn, n, key, word) { return function () { var k = fn(g, n); if (k) baseDone(word + ' ' + baleWord(k) + ' of ' + G.name + '.', key); }; }
      btn(bx, 'Stash 1', 'Stash 1 bale of ' + G.name + ' in the cave', 'st1' + g, mv(stash, 1, 'st1' + g, '📦 You stash'), have < 1 || room < 1);
      btn(bx, 'Stash all (' + sAll + ')', 'Stash ' + sAll + ' bales of ' + G.name + ' in the cave', 'sta' + g, mv(stash, sAll, 'sta' + g, '📦 You stash'), sAll < 1);
      btn(bx, 'Take 1', 'Take 1 bale of ' + G.name + ' from the cave', 'tk1' + g, mv(unstash, 1, 'tk1' + g, '📦 You load'), kept < 1 || space() < 1);
      btn(bx, 'Take all (' + tAll + ')', 'Take ' + tAll + ' bales of ' + G.name + ' from the cave', 'tka' + g, mv(unstash, tAll, 'tka' + g, '📦 You load'), tAll < 1);
      li.appendChild(bx);
      ul.appendChild(li);
    });
    body.appendChild(ul);
    renderGrow(body, btn);
    // Digging deeper, and patching the hull yourself
    var more = el('div', {class: 'g-btns base-more'});
    if (B.lvl < HIDE.caps.length - 1) {
      var dc = HIDE.capCost[B.lvl], dn = HIDE.caps[B.lvl + 1];
      btn(more, '⛏️ Dig deeper to hold ' + dn + ' bales · ' + fmt(dc) + ' 🪙', 'Dig the cave deeper to hold ' + dn + ' bales, for ' + fmt(dc) + ' doubloons', 'dig', function () {
        if (state.gold < dc || B.lvl >= HIDE.caps.length - 1) return;
        state.gold -= dc; B.lvl++;
        baseDone('⛏️ Your crew digs for three days and finds two skeletons and a lot of room. The cave holds ' + baseCap() + ' bales now.', 'dig');
      }, state.gold < dc);
    }
    var need = hullMax() - state.hull, fix = Math.min(need, state.gold);
    if (need > 0) {
      btn(more, '🔧 Patch ' + fix + ' hull ' + plural(fix, 'point') + ' yourself · ' + fmt(fix) + ' 🪙', 'Patch ' + fix + ' hull points yourself for ' + fmt(fix) + ' doubloons, half the shipyard price', 'fix', function () {
        var k = Math.min(hullMax() - state.hull, state.gold);
        if (k <= 0) return;
        state.gold -= k; state.hull += k;
        baseDone('🔧 Your crew patches ' + k + ' hull points with driftwood and stubbornness, for ' + fmt(k) + ' doubloons.', 'fix');
      }, fix < 1);
    }
    if (more.children.length) body.appendChild(more);
    body.appendChild(el('h3', null, '🧭 Quick passage'));
    body.appendChild(passageList('hideout'));
    if (keepKey) {
      var again = body.querySelector('[data-key="' + keepKey + '"]');
      if (again && !again.disabled) again.focus();
      else { var h = body.querySelector('h3'); if (h) { h.tabIndex = -1; h.focus(); } }
    }
  }

  /* ---------- the hall of fame: the best voyages on this device, sunk or retired ---------- */
  function addFame(s, how, by) {
    if (!s || !(s.dist > 0 || s.xp > 25)) return;
    legacy.fame.push({captain: s.look.captain || 'A nameless captain', ship: s.look.ship || 'the Lucky Leaf', lvl: E.levelOf(s.xp), xp: Math.round(s.xp) || 0,
      day: E.dayOf(s.dist), gold: Math.round(s.gold) || 0, how: how, by: String(by || '').slice(0, 90), gentle: !!s.gentle, at: Date.now(), st: voyageStats(s)});
    legacy.fame.sort(function (a, b) { return (b.xp || 0) - (a.xp || 0); });
    legacy.fame = legacy.fame.slice(0, 8);
    saveLegacy();
  }
  function retireVoyage() {
    var s = loadSaved();
    if (s) { try { addFame(fromSave(s), 'retired', 'retired ashore'); } catch (e) { /* a damaged save just doesn't make the list */ } }
    try { localStorage.removeItem(SAVE_KEY); } catch (e) { /* ignore */ }
  }
  function fameList(max) {
    var ol = el('ol', {class: 'fame'});
    legacy.fame.slice(0, max).forEach(function (f) {
      var lv = clamp(Math.floor(f.lvl) || 1, 1, D.LEVELS.length);
      ol.appendChild(el('li', null, f.captain + ', ' + f.ship + ': level ' + lv + ' ' + D.LEVELS[lv - 1].title + ', day ' + (Math.floor(f.day) || 1) + ', ' +
        fmt(Math.max(0, +f.gold || 0)) + ' doubloons, ' + (f.how === 'sunk' ? f.by || 'sunk' : 'retired ashore') + (f.gentle ? ' (gentle seas)' : '') + '.'));
    });
    return ol;
  }

  /* ---------- the MJBizCon week board: your best voyage this week beside the players you've swapped scores with ---------- */
  var boardMsg = '';
  function boardShown() { var n = Date.now(); return !!BOARD && n >= BOARD.open && n < BOARD.hide; }
  function boardOpen() { var n = Date.now(); return !!BOARD && n >= BOARD.open && n < BOARD.close; }
  function inWeek(at) { return !!BOARD && at >= BOARD.open && at < BOARD.close; }
  function playerId() {
    if (!legacy.pid) {
      var s = '';
      for (var i = 0; i < 6; i++) s += '0123456789abcdefghijklmnopqrstuvwxyz'.charAt(Math.floor(Math.random() * 36));
      legacy.pid = s;
      saveLegacy();
    }
    return legacy.pid;
  }
  // What a voyage has done, for the breakout boards. Days at sea count whole days, as the log shows them.
  function voyageStats(s) {
    var st = {};
    STAT_KEYS.forEach(function (k) { st[k] = k === 'days' ? E.dayOf(s.dist) : Math.max(0, Math.floor(s[k]) || 0); });
    return st;
  }
  // A score from a link, or one saved on this device: names cleaned, numbers in range, or nothing at all.
  // Stats a code doesn't carry (codes made before the breakout boards) stay unknown, so those players sit out those boards.
  function cleanEntry(r) {
    if (!r || typeof r !== 'object' || typeof r.pid !== 'string' || !/^[a-z0-9]{6}$/.test(r.pid)) return null;
    var xp = Math.floor(+r.xp), at = Math.floor(+r.t);
    if (!(xp >= 0 && xp <= 9999999) || !(at > 0)) return null;
    var day = clamp(Math.floor(+r.day) || 1, 1, 99999), src = r.st && typeof r.st === 'object' ? r.st : {}, st = {};
    STAT_KEYS.forEach(function (k) {
      if (src[k] === undefined || src[k] === null || src[k] === '') return;
      var v = Math.floor(+src[k]);
      if (v >= 0 && v <= 9999999) st[k] = v;
    });
    if (STAT_KEYS.indexOf('days') >= 0 && !(st.days >= day)) st.days = day;
    return {pid: r.pid, captain: cleanName(r.captain, 'A nameless captain'), ship: cleanName(r.ship, 'the Lucky Leaf'), xp: xp,
      day: day, gold: clamp(Math.floor(+r.gold) || 0, 0, 99999999), gentle: !!r.gentle, t: at, st: st};
  }
  // A light seal on each code: it catches a typo or a mangled link, not a determined cheat.
  function seal(s) {
    var h = 0x811c9dc5;
    s = 'pillage:' + s;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
    return ('0000' + h.toString(36)).slice(-4);
  }
  function toB64(s) { return btoa(unescape(encodeURIComponent(s))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
  function fromB64(s) {
    s = String(s).replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    return decodeURIComponent(escape(atob(s)));
  }
  // Version 2 codes add the breakout stats, in the order BOARD.stats lists them. Version 1 codes (from before) still read.
  function scoreCode(e) {
    var st = e.st || {}, packed = STAT_KEYS.map(function (k) { return st[k] >= 0 ? Math.floor(st[k]).toString(36) : ''; }).join('.');
    var body = ['2', e.pid, e.captain.replace(/~/g, '-'), e.ship.replace(/~/g, '-'), e.xp, e.day, e.gold, e.gentle ? 1 : 0, Math.floor(e.t / 60000).toString(36), packed].join('~');
    return toB64(body + '~' + seal(body));
  }
  function readScore(code) {
    try {
      var p = fromB64(code).split('~'), st = {};
      if (p[0] === '1') { if (p.length !== 10 || p[9] !== seal(p.slice(0, 9).join('~'))) return null; }
      else if (p[0] === '2') {
        if (p.length !== 11 || p[10] !== seal(p.slice(0, 10).join('~'))) return null;
        p[9].split('.').forEach(function (v, i) { if (STAT_KEYS[i] && /^[0-9a-z]+$/.test(v)) st[STAT_KEYS[i]] = parseInt(v, 36); });
      } else return null;
      return cleanEntry({pid: p[1], captain: p[2], ship: p[3], xp: p[4], day: p[5], gold: p[6], gentle: p[7] === '1', t: parseInt(p[8], 36) * 60000, st: st});
    } catch (e) { return null; }
  }
  function scoreLink(e) { return BOARD.url + '?vs=' + scoreCode(e); }
  // The higher of each stat in two records.
  function mergeStats(a, b) {
    var st = {};
    [a || {}, b || {}].forEach(function (x) { for (var k in x) if (STAT_KEYS.indexOf(k) >= 0 && x[k] >= 0 && !(st[k] >= x[k])) st[k] = x[k]; });
    return st;
  }
  // Your best voyage this week: a finished one from the hall of fame, or the one you're sailing now.
  // Each breakout stat is your best from any voyage this week.
  function myBest() {
    var best = null, live = null, top = {};
    legacy.fame.forEach(function (f) {
      if (!(f.at && inWeek(f.at))) return;
      top = mergeStats(top, f.st || {days: f.day});
      if (!best || (f.xp || 0) > best.xp) best = {captain: f.captain, ship: f.ship, xp: f.xp || 0, day: f.day, gold: f.gold, gentle: f.gentle, t: f.at};
    });
    if (boardOpen()) {
      if ($('title-screen').hidden) live = state;
      else { var sv = loadSaved(); if (sv) { try { live = fromSave(sv); } catch (e) { live = null; } } }
    }
    if (live && (live.dist > 0 || live.xp > 25)) {
      top = mergeStats(top, voyageStats(live));
      if (!best || live.xp >= best.xp) {
        best = {captain: live.look.captain || 'A nameless captain', ship: live.look.ship || 'the Lucky Leaf', xp: Math.round(live.xp) || 0,
          day: E.dayOf(live.dist), gold: Math.round(live.gold) || 0, gentle: !!live.gentle, t: Date.now()};
      }
    }
    if (!best) return null;
    best.pid = playerId();
    best.st = top;
    best = cleanEntry(best);
    best.me = true;
    return best;
  }
  // One line per player: the better overall score, and the best of each stat from every code they've shown you.
  function addRival(r) {
    var old = null;
    legacy.rivals.forEach(function (x) { if (x.pid === r.pid) old = x; });
    if (old) {
      var keep = r.xp > old.xp || (r.xp === old.xp && r.t > old.t) ? r : old;
      keep.st = mergeStats(old.st, r.st);
      legacy.rivals[legacy.rivals.indexOf(old)] = keep;
    } else legacy.rivals.push(r);
    legacy.rivals.sort(function (a, b) { return b.xp - a.xp; });
    legacy.rivals = legacy.rivals.slice(0, BOARD.max);
    saveLegacy();
  }
  // Someone opened a score link, or scanned a QR code: put that captain on this board and tidy the address bar.
  function takeScoreFromLink() {
    var code = null;
    try { code = new URLSearchParams(location.search).get('vs'); } catch (e) { return; }
    if (!code) return;
    try { history.replaceState(null, '', location.pathname + location.hash); } catch (e) { /* the address keeps the code: harmless */ }
    if (!boardShown()) return;
    var r = readScore(code);
    if (!r) boardMsg = 'That score link got mangled on the way, so it couldn’t go on your board. Ask for it again.';
    else if (r.pid === legacy.pid) boardMsg = 'That’s your own score. Show it to another player, then scan theirs.';
    else if (!boardOpen() || !inWeek(r.t)) boardMsg = 'That score is from outside ' + BOARD.name + ', so it stays off the board.';
    else {
      addRival(r);
      boardMsg = r.captain + ' of ' + r.ship + ' is on your ' + BOARD.name + ' board with ' + fmt(r.xp) + ' renown. Can you beat that?';
      track('board-add');
    }
  }
  function boardLine(r) {
    return r.captain + ', ' + r.ship + (r.me ? ' (you)' : '') + ': ' + fmt(r.xp) + ' renown, level ' + E.levelOf(r.xp) + ', day ' + r.day + (r.gentle ? ' (gentle seas)' : '') + '.';
  }
  function statWords(S, n) { return fmt(n) + ' ' + plural(n, S.one, S.many); }
  // A breakout board: everyone with that stat, best first; ties go to whoever got there first.
  function statRows(rows, k) {
    return rows.filter(function (r) { return r.st && r.st[k] > 0; })
      .sort(function (a, b) { return b.st[k] - a.st[k] || (a.me ? -1 : b.me ? 1 : a.t - b.t); });
  }
  // The titles each player holds: one for the top of the overall board, one for the top of each breakout board.
  function crownsOf(rows) {
    var crowns = {};
    function give(r, t) { (crowns[r.pid] = crowns[r.pid] || []).push(t); }
    if (rows.length && rows[0].xp > 0) give(rows[0], BOARD.top);
    STATS.forEach(function (S) { var lead = statRows(rows, S.k)[0]; if (lead) give(lead, S.crown); });
    return crowns;
  }
  function crownTag(titles) {
    var c = el('span', {class: 'crowns'});
    c.appendChild(el('span', {'aria-hidden': 'true'}, ' 👑 '));
    c.appendChild(el('span', {class: 'sr-only'}, ' ' + plural(titles.length, 'Title', 'Titles') + ': '));
    c.appendChild(document.createTextNode(titles.join(' · ')));
    return c;
  }
  function boardBox(max) {
    var open = boardOpen(), me = myBest(), rows = legacy.rivals.filter(function (r) { return inWeek(r.t); });
    if (me) rows.push(me);
    rows.sort(function (a, b) { return b.xp - a.xp || (a.me ? -1 : b.me ? 1 : a.t - b.t); });
    var crowns = crownsOf(rows), few = max <= 5 ? 1 : 5;
    var box = el('div', {class: 'board'}), h = el('h3');
    h.appendChild(el('span', {'aria-hidden': 'true'}, '🏆 '));
    h.appendChild(document.createTextNode(BOARD.name + ' board' + (open ? '' : ': final standings')));
    box.appendChild(h);
    if (boardMsg) box.appendChild(el('p', {class: 'win', role: 'status'}, boardMsg));
    box.appendChild(el('p', {class: 'hint'}, open ? BOARD.blurb : 'The board closed at the end of show week. Thanks for sailing.'));
    var oh = el('h4');
    oh.appendChild(el('span', {'aria-hidden': 'true'}, '⭐ '));
    oh.appendChild(document.createTextNode('Overall: most renown'));
    box.appendChild(oh);
    if (rows.length) {
      var ol = el('ol', {class: 'fame board-list'}), mine = rows.indexOf(me);
      var line = function (r, at) {
        var li = el('li', {class: r.me ? 'me' : null, value: at}, boardLine(r));
        if (crowns[r.pid]) li.appendChild(crownTag(crowns[r.pid]));
        return li;
      };
      rows.slice(0, max).forEach(function (r) { ol.appendChild(line(r)); });
      if (mine >= max) ol.appendChild(line(me, mine + 1));
      box.appendChild(ol);
      if (rows.length > max && mine < max) box.appendChild(el('p', {class: 'hint'}, (rows.length - max) + ' more in your captain’s log.'));
    } else box.appendChild(el('p', null, 'Nobody on it yet. Set sail and you will be.'));
    // The breakout boards, each with its own leader and title.
    if (STATS.length) {
      box.appendChild(el('p', {class: 'hint board-cats-intro'}, STATS.length + ' breakout boards. Lead one and its title is yours.' + (max <= 5 ? ' The full boards are in your captain’s log.' : '')));
      var grid = el('div', {class: 'board-cats'});
      STATS.forEach(function (S) {
        var card = el('div', {class: 'board-cat'}), ch = el('h4'), sr = statRows(rows, S.k), at = sr.indexOf(me);
        ch.appendChild(el('span', {'aria-hidden': 'true'}, S.icon + ' '));
        ch.appendChild(document.createTextNode(S.board));
        card.appendChild(ch);
        if (!sr.length) card.appendChild(el('p', {class: 'hint'}, 'Nobody yet. ' + S.how));
        else {
          var co = el('ol', {class: 'board-mini'});
          var put = function (r, i) {
            var li = el('li', {class: r.me ? 'me' : null, value: i ? i : null});
            if (r === sr[0]) {
              var cr = el('span', {class: 'crown'});
              cr.appendChild(el('span', {'aria-hidden': 'true'}, '👑 '));
              cr.appendChild(document.createTextNode(S.crown + ': '));
              li.appendChild(cr);
            }
            li.appendChild(document.createTextNode(r.captain + (r.me ? ' (you)' : '') + ', ' + statWords(S, r.st[S.k])));
            return li;
          };
          sr.slice(0, few).forEach(function (r) { co.appendChild(put(r)); });
          if (at >= few) co.appendChild(put(me, at + 1));
          card.appendChild(co);
        }
        grid.appendChild(card);
      });
      box.appendChild(grid);
    }
    if (open && me) {
      var b = el('button', {type: 'button', class: 'secondary board-share', 'data-key': 'share'});
      b.appendChild(el('span', {'aria-hidden': 'true'}, '📲 '));
      b.appendChild(document.createTextNode('Show or send my score'));
      b.addEventListener('click', function () { openShare(myBest() || me); });
      box.appendChild(b);
    }
    return box;
  }
  // The score card's list of what you've done this week, for the player you're showing it to.
  function statList(e) {
    var ul = el('ul', {class: 'share-stats', 'aria-label': 'Your tallies this week'});
    STATS.forEach(function (S) {
      var n = e.st && e.st[S.k];
      if (!(n > 0)) return;
      var li = el('li');
      li.appendChild(el('span', {'aria-hidden': 'true'}, S.icon + ' '));
      li.appendChild(document.createTextNode(statWords(S, n)));
      ul.appendChild(li);
    });
    return ul;
  }
  function openShare(e) {
    var url = scoreLink(e), qbox = $('share-qr'), label = 'QR code for your score. Another player scans it with their phone camera to put you on their board.';
    $('share-score').textContent = boardLine(e);
    var sl = $('share-stats');
    if (sl) { sl.textContent = ''; var ul = statList(e); if (ul.children.length) sl.appendChild(ul); sl.hidden = !ul.children.length; }
    qbox.textContent = '';
    var q = QR && QR.svg(url, label);
    if (QR && !q) {
      // Very long names (emoji count four bytes each) don't fit a small code: shorten them in the code only.
      var cut = function (s) { return Array.from(s).slice(0, 8).join(''); };
      url = scoreLink(Object.assign({}, e, {captain: cut(e.captain), ship: cut(e.ship)}));
      q = QR.svg(url, label);
    }
    if (q) qbox.appendChild(q);
    qbox.hidden = !q;
    $('share-link').value = url;
    $('share-send').hidden = !navigator.share;
    track('board-share');
    openDialog($('dlg-share'), $('share-done'));
  }
  function shareSay(msg) { var live = $('dlg-share').querySelector('.dlg-live'); live.hidden = false; live.textContent = msg; }

  /* ---------- the captain: names, colours, flag and how rough the seas are ---------- */
  var capDone = null, capFresh = false;
  function swatches(id, name, table, earned, now) {
    var fs = $(id);
    Array.prototype.slice.call(fs.querySelectorAll('label')).forEach(function (l) { l.remove(); });
    Object.keys(table).forEach(function (k) {
      var T = table[k], locked = T.earn && !earned[k], lab = el('label', {class: 'swatch' + (locked ? ' locked' : '')});
      var inp = el('input', {type: 'radio', name: name, value: k});
      inp.checked = k === now;
      inp.disabled = !!locked;
      lab.appendChild(inp);
      var chip = el('span', {class: 'chip', 'aria-hidden': 'true'}, T.icon || '');
      chip.style.background = T.color;
      lab.appendChild(chip);
      lab.appendChild(el('span', null, T.name + (locked ? ' (locked: ' + T.earn.charAt(0).toLowerCase() + T.earn.slice(1) + ')' : '')));
      fs.appendChild(lab);
    });
  }
  function openCaptain(fresh, done) {
    var L = state.look;
    capFresh = !!fresh; capDone = done || null;
    $('cap-name').value = L.captain;
    $('cap-ship').value = L.ship;
    swatches('cap-sails', 'cap-sail', SAILS, legacy.sails, L.sail);
    swatches('cap-flags', 'cap-flag', FLAGS, legacy.flags, L.flag);
    $('cap-mode').hidden = !fresh;
    $('cap-mode-note').hidden = !!fresh;
    $('cap-mode-note').textContent = state.gentle ? 'This voyage sails gentle seas. You pick real danger or gentle seas when you start a new voyage.'
      : 'This voyage sails in real danger. You pick real danger or gentle seas when you start a new voyage.';
    if (fresh) $('cap-real').checked = true;
    $('cap-ok').textContent = fresh ? 'Set sail' : 'Done';
    openDialog($('dlg-captain'), $('cap-name'));
  }
  function applyCaptain() {
    var L = state.look, s = document.querySelector('input[name="cap-sail"]:checked'), f = document.querySelector('input[name="cap-flag"]:checked');
    L.captain = cleanName($('cap-name').value, '');
    L.ship = cleanName($('cap-ship').value, 'the Lucky Leaf');
    if (s && SAILS[s.value] && (!SAILS[s.value].earn || legacy.sails[s.value])) L.sail = s.value;
    if (f && FLAGS[f.value] && (!FLAGS[f.value].earn || legacy.flags[f.value])) L.flag = f.value;
    if (capFresh) state.gentle = !!$('cap-gentle').checked;
    needRender = true;
    save();
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
    if (HIDE.map === mid && baseKnown()) out.push({type: 'base', id: 'hideout', map: mid, x: HIDE.dock[0], y: HIDE.dock[1], label: legacy.base ? 'your hideout on ' + HIDE.name : 'the old cave on ' + HIDE.name, icon: legacy.base ? '🏚️' : '🔒', here: !!state.atBase});
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
    var pt = exitPoint(e.exit), a = E.crossing(state.map, e.exit, pt[0], pt[1]);
    return {type: 'point', map: e.exit.to, x: a[0], y: a[1], label: MAPS[e.exit.to].name};
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
    else if (state.atBase) { txt = '🏚️ At your hideout on ' + HIDE.name + ', ' + m.name + '.'; key = 'base'; }
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
    customs: {hull: '#2b394d', deck: '#8494ab', sail: '#2f6fd6', flag: '#ffffff'},
    merchant: {hull: '#8a5a2b', deck: '#d2aa74', sail: '#efd59e', flag: '#c0392b'},
    looted: {hull: '#6d5a48', deck: '#a99780', sail: '#b2a993', flag: '#7f7f7f'},
    pirate: {hull: '#2b2420', deck: '#6a5d52', sail: '#1c1c1c', flag: '#f2f2f2', mark: '#f2f2f2'},
    boss: {hull: '#3a1010', deck: '#7a4a3a', sail: '#4d0b0b', flag: '#f2d34a', mark: '#f2d34a'},
    navy: {hull: '#3a2618', deck: '#a98b62', sail: '#f7f2e4', flag: '#c8102e'},
    fireship: {hull: '#241a14', deck: '#4a3a2c', sail: '#6e6256', flag: '#c0392b', mark: '#e0702a'}
  };
  var NAVY_SIZE = [22, 25, 28];
  // Real ensigns of 1718, small: British red with the Union in the corner, Spain's ragged red X on white,
  // French royal white with gold lilies, Dutch stripes, and pirate black.
  var FLAG_INK = {britain: ['#c8102e', '#012169'], spain: ['#f4f1e8', '#b5121b'], france: ['#f7f5ef', '#d4a52a'], dutch: ['#ae1c28', '#f7f5ef', '#21468b'], brethren: ['#141414', '#f2f2f2']};
  function drawFlag(c, L, nat) {
    var w = L * 0.42, h = L * 0.32, x = -L * 1.1, y = -h / 2, k = FLAG_INK[nat];
    c.fillStyle = k[0]; c.fillRect(x, y, w, h);
    if (nat === 'britain') { c.fillStyle = k[1]; c.fillRect(x + w * 0.55, y, w * 0.45, h * 0.5); }
    else if (nat === 'spain') { c.strokeStyle = k[1]; c.lineWidth = Math.max(0.8, h * 0.2); c.beginPath(); c.moveTo(x, y); c.lineTo(x + w, y + h); c.moveTo(x + w, y); c.lineTo(x, y + h); c.stroke(); }
    else if (nat === 'france') { c.fillStyle = k[1]; [[0.3, 0.3], [0.7, 0.3], [0.5, 0.72]].forEach(function (q) { c.beginPath(); c.arc(x + w * q[0], y + h * q[1], Math.max(0.6, h * 0.13), 0, Math.PI * 2); c.fill(); }); }
    else if (nat === 'dutch') { c.fillStyle = k[1]; c.fillRect(x, y + h / 3, w, h / 3); c.fillStyle = k[2]; c.fillRect(x, y + h * 2 / 3, w, h / 3); }
    else { c.fillStyle = k[1]; c.beginPath(); c.arc(x + w * 0.5, y + h * 0.45, h * 0.2, 0, Math.PI * 2); c.fill(); }
    c.lineWidth = 0.6; c.strokeStyle = 'rgba(0,0,0,.5)'; c.strokeRect(x, y, w, h);
  }
  function playerLook() {
    var s = SAILS[state.look.sail] || SAILS.canvas, f = FLAGS[state.look.flag] || FLAGS.skull;
    return {hull: '#7a4b26', deck: '#c29560', sail: s.color, flag: f.color, mark: state.look.sail === 'emerald' || state.look.sail === 'seafoam' ? '#fbf4e2' : '#2f8f4e'};
  }
  var PIRATE_SIZE = [15, 17, 19, 22, 25];
  function drawCave(c, at, owned) {
    var x = at[0], y = at[1];
    c.fillStyle = '#8a7a64'; c.beginPath(); c.ellipse(x, y + 2, 13, 9, 0, 0, Math.PI * 2); c.fill();
    c.fillStyle = '#2a2018'; c.beginPath(); c.moveTo(x - 6, y + 6); c.lineTo(x - 6, y); c.quadraticCurveTo(x, y - 8, x + 6, y); c.lineTo(x + 6, y + 6); c.closePath(); c.fill();
    if (owned) { c.fillStyle = '#e9b949'; c.fillRect(x + 2, y + 1, 2, 2); }
  }
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
  function drawShip(c, x, y, a, look, L, nat) {
    c.save(); c.translate(x, y); c.rotate(a);
    c.fillStyle = 'rgba(0,30,40,.22)'; c.beginPath(); c.ellipse(1.5, 3, L * 0.95, L * 0.42, 0, 0, Math.PI * 2); c.fill();
    c.beginPath(); c.moveTo(L, 0); c.quadraticCurveTo(L * 0.35, -L * 0.5, -L * 0.8, -L * 0.36); c.lineTo(-L * 0.8, L * 0.36); c.quadraticCurveTo(L * 0.35, L * 0.5, L, 0); c.closePath();
    c.fillStyle = look.hull; c.fill(); c.lineWidth = 1.2; c.strokeStyle = 'rgba(0,0,0,.55)'; c.stroke();
    c.beginPath(); c.moveTo(L * 0.7, 0); c.quadraticCurveTo(L * 0.25, -L * 0.32, -L * 0.62, -L * 0.22); c.lineTo(-L * 0.62, L * 0.22); c.quadraticCurveTo(L * 0.25, L * 0.32, L * 0.7, 0); c.closePath();
    c.fillStyle = look.deck; c.fill();
    c.beginPath(); c.moveTo(-L * 0.02, -L * 0.85); c.quadraticCurveTo(L * 0.52, 0, -L * 0.02, L * 0.85); c.lineTo(-L * 0.18, L * 0.8); c.quadraticCurveTo(L * 0.28, 0, -L * 0.18, -L * 0.8); c.closePath();
    c.fillStyle = look.sail; c.fill(); c.lineWidth = 0.8; c.strokeStyle = 'rgba(0,0,0,.4)'; c.stroke();
    if (look.mark) { c.fillStyle = look.mark; c.beginPath(); c.ellipse(L * 0.13, 0, L * 0.09, L * 0.2, 0, 0, Math.PI * 2); c.fill(); }
    if (nat && FLAG_INK[nat]) drawFlag(c, L, nat);
    else { c.fillStyle = look.flag; c.fillRect(-L * 1.0, -L * 0.13, L * 0.3, L * 0.26); }
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
    if (HIDE.map === mid && baseKnown()) drawCave(c, HIDE.at, !!legacy.base);
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
        drawShip(c, n.x, n.y, n.angle, look, n.kind === 'merchant' ? 20 : n.kind === 'boss' ? 26 : n.kind === 'pirate' ? PIRATE_SIZE[(n.tier || 1) - 1] || 17 : n.kind === 'navy' ? NAVY_SIZE[clamp(n.tier || 3, 3, 5) - 3] : 15,
          n.kind === 'pirate' || n.kind === 'boss' ? null : n.nation);
      });
      var bob = anim ? Math.sin(t * 1.6) * 0.06 : 0;
      // Decoys and a fire ship sail in your wake.
      var ex = Math.cos(state.angle), ey = Math.sin(state.angle), tail = (state.decoys || 0) + (state.fireship ? 1 : 0);
      for (var di = 0; di < tail; di++) {
        var back = 28 + 16 * di, side = (di % 2 ? 1 : -1) * 11;
        drawShip(c, state.x - ex * back - ey * side, state.y - ey * back + ex * side, state.angle + bob, di < (state.decoys || 0) ? playerLook() : LOOK.fireship, 10);
      }
      drawShip(c, state.x, state.y, state.angle + bob, playerLook(), 15);
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
    m.lands.concat(m.labels || []).forEach(function (L) {
      var at = L.label || L.at;
      if (!at || !explored(mid, at[0], at[1])) return;
      c.font = 'italic 700 ' + (chart ? 11 : 13) + 'px Georgia, "Times New Roman", serif';
      c.fillStyle = 'rgba(22,52,28,.8)';
      c.fillText(L.name, sx(at[0]), sy(at[1]));
    });
    Object.keys(PORTS).forEach(function (pid) {
      var p = PORTS[pid];
      if (p.map !== mid || !portKnown(pid)) return;
      pill(c, '⚓ ' + p.name, sx(p.town[0]), sy(p.town[1]) - (chart ? 12 : 20), chart ? {font: '700 11px system-ui, sans-serif', h: 18} : null);
    });
    if (HIDE.map === mid && baseKnown()) pill(c, legacy.base ? '🏚️ Your hideout' : '🔒 Old cave', sx(HIDE.at[0]), sy(HIDE.at[1]) - (chart ? 14 : 22), {font: '700 11px system-ui, sans-serif', h: 18, bg: 'rgba(255,240,220,.94)', ink: '#4a2f1c'});
    stashMarks(mid).forEach(function (at) {
      var s = {at: at};
      pill(c, 'Buried treasure?', sx(s.at[0]), sy(s.at[1]) + (chart ? 22 : 34), {font: '700 11px system-ui, sans-serif', h: 18, bg: 'rgba(255,240,220,.94)', ink: '#7a1712'});
    });
    if (!chart && mid === state.map) {
      npcs[mid].forEach(function (n) {
        if (n.gone || (n.kind !== 'pirate' && n.kind !== 'boss' && n.kind !== 'navy') || !explored(mid, n.x, n.y)) return;
        if (((n.kind === 'pirate' && !n.bounty) || n.kind === 'navy') && Math.hypot(n.x - state.x, n.y - state.y) > 380) return;
        var label = n.kind === 'boss' ? '💀 Gristle' : n.kind === 'navy' ? '⚓ ' + cap(NAT[n.nation].adj) + ' ' + shipClass(n) : n.bounty ? '🎯 Wanted: ' + n.captain : '☠️ ' + cap(shipClass(n));
        pill(c, label, sx(n.x), sy(n.y) - 30, {font: '700 11px system-ui, sans-serif', h: 18, bg: n.kind === 'navy' ? 'rgba(18,40,80,.92)' : n.bounty ? 'rgba(122,23,18,.92)' : 'rgba(24,18,16,.9)', ink: '#fff', line: 'rgba(255,255,255,.5)'});
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
    setText('h-hold', (cargoCount() + jobLoad()) + '/' + capacity());
    setText('h-shot', String(state.shot));
    var dry = state.shot < 1;
    if (hudCache.dry !== dry) { hudCache.dry = dry; $('h-shot').parentNode.classList.toggle('low', dry); }
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
    var fd = level() >= 2 ? String(state.food) : '';
    if (hudCache.food !== fd) { hudCache.food = fd; $('h-food').textContent = fd; $('h-food-li').hidden = !fd; $('h-food-li').classList.toggle('low', !!fd && state.food <= 5); }
    var fl = (state.decoys || 0) + '/' + (state.fireship || 0);
    if (hudCache.fleet !== fl) {
      hudCache.fleet = fl;
      $('h-fleet-li').hidden = !state.decoys && !state.fireship;
      $('h-fleet').textContent = (state.decoys ? '🚩' + state.decoys : '') + (state.fireship ? (state.decoys ? ' ' : '') + '🔥' : '');
      $('h-fleet-sr').textContent = (state.decoys ? state.decoys + ' ' + plural(state.decoys, 'decoy') : '') + (state.fireship ? (state.decoys ? ' and ' : '') + 'a fire ship' : '');
    }
  }

  /* ---------- starting, continuing, starting over ---------- */
  function begin(fresh, saved) {
    fogs = {}; npcs = {}; floaters = {}; auto = null; wake = []; keys = {}; actionKey = ''; lastWhereKey = ''; justLeft = null;
    state = fresh ? newState() : fromSave(saved);
    if (!fresh && state.fog) for (var mid in state.fog) if (MAPS[mid]) decodeFog(mid, state.fog[mid]);
    var m = enterMap(state.map);
    if (state.tmap && state.tmap.redraw) redrawMap();
    if (E.shipBlocked(m, state.x, state.y)) { var f = E.nearestFreePoint(m, state.x, state.y); state.x = f[0]; state.y = f[1]; }
    reveal(state.map, state.x, state.y, REVEAL);
    Object.keys(state.known).forEach(function (pid) { if (PORTS[pid]) reveal(PORTS[pid].map, PORTS[pid].dock[0], PORTS[pid].dock[1], 110); });
    started = true;
    levelUp = 0; evClock = 70 + Math.random() * 30; evRecent = []; lastPortEv = -999; hudCache = {}; mendAcc = 0;
    if (fresh) state.flags.r5 = state.flags.r6 = state.flags.geo = 1;
    dayTick();
    $('title-screen').hidden = true;
    boardMsg = '';
    $('hud').hidden = false; $('tools').hidden = false;
    resize();
    updateHud();
    updateWhere();
    try { $('game').scrollIntoView({block: 'start', behavior: calm() ? 'auto' : 'smooth'}); } catch (er) { /* old browsers */ }
    if (fresh) {
      track('new-game');
      save();
      openCaptain(true, function () {
        track(state.gentle ? 'gentle-seas' : 'real-danger');
        var base = legacy.base ? '\n\nYour hideout on ' + HIDE.name + ', just south of Petit-Goâve, still holds ' + fmt(legacy.base.gold) + ' doubloons and ' + baleWord(baseBales()) + ' from your last voyage.' : '';
        note('🏴‍☠️ Ahoy, ' + (state.look.captain || 'Captain') + '!', 'You’ve just spent your last coins on a leaky little sloop called ' + shipName() + ', twelve cannonballs and one parrot of questionable loyalty: ' + D.PARROT + '.\n\n' +
          'The plan: buy cheap where it grows, sell dear where it doesn’t, pillage the odd fat merchantman and maybe, just maybe, dig up Captain Ines Featherstone’s legendary Emerald Bale.\n\n' +
          (state.gentle ? 'These are gentle seas: lose a fight and you limp away poorer, but your voyage goes on.' : 'Fair warning: these seas are real. Lose a sea battle and your ship goes down, voyage over. When a fight looks bad, run, pay or strike your colours.') + base + '\n\n' +
          'Start at the Leaky Lantern tavern here in Tortuga. Mama Ruthie hears everything.', null, function () { dock('tortuga'); });
      });
    } else if (!state.flags.r5 || !state.flags.r6) {
      // A voyage from before the nations or the law: say once what's new, then carry on where it left off.
      var was5 = !!state.flags.r5, lv0 = level();
      state.flags.r5 = state.flags.r6 = 1;
      // Unlocks already announced in part one don't repeat; provisions, decoys and fire ships get a word here instead.
      var more = unlockText(lv0), lawText = 'Customs and warships now follow the law: get caught with a small haul and it’s a warning, then a fine. Get caught with ' + LAW_BIG + ' or more bales in plain sight, or as a nation’s enemy, and it’s jail. Pirates who take you over strip your open hold and most of your gold.';
      var extra = [lv0 >= 2 && was5 ? '🍞 Your crew eats now: a day’s provisions for every day at sea, and two more every time you smoke. Buy provisions in any market.' : '', lv0 >= 3 && was5 ? '🚩 Shipwrights sell decoy sloops that lead trouble away from you.' : ''].filter(Boolean).join('\n\n');
      note('⚓ New since your last voyage', (was5 ? '' : 'Every port now flies a real flag of 1718, British, Spanish, French, Dutch or pirate, and every nation keeps track of how it feels about you. Pillage its merchants and it turns cold: its ports charge you more, its Customs lean harder and its warships come looking. Pay its fees, do its jobs and salute its ships and it warms up again.\n\n') +
        lawText + (more ? '\n\n' + more : '') + (extra ? '\n\n' + extra : '') +
        (lv0 < 2 ? '\n\nAt level 2, port taverns post paid jobs and harbour news, and your crew starts eating. At level 3, bounties, letters of marque and decoys. At level 4, fire ships.' : '') +
        '\n\nYour captain’s log has the full picture.', null, resume);
    } else resume();
    function resume() {
      if (state.atBase && legacy.base) {
        state.atBase = false;
        enterBase();
      } else if (state.docked) {
        openPort(state.docked, 'market');
      } else {
        say('Welcome back, Captain. Your voyage continues on day ' + day() + '.' + (state.gentle && !state.flags.gentleNote ? ' It sails gentle seas, so a lost fight won’t sink you. Start a new voyage for real danger.' : ''));
        state.flags.gentleNote = 1;
        focusSea();
      }
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
    var tb = $('title-board');
    tb.textContent = '';
    tb.hidden = !boardShown();
    if (boardShown()) tb.appendChild(boardBox(5));
    var tf = $('title-fame');
    tf.hidden = !legacy.fame.length;
    if (legacy.fame.length) { var old = tf.querySelector('ol'); if (old) old.remove(); tf.appendChild(fameList(3)); }
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
    $('btn-confirm-new').addEventListener('click', function () { $('title-confirm').hidden = true; retireVoyage(); begin(true); });
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
    $('opt-motion').addEventListener('change', function () { prefs.motion = this.checked; savePrefs(); wake = []; calmClass(); });
    $('opt-fast').addEventListener('change', function () { prefs.fast = this.checked; savePrefs(); });
    $('opt-new').addEventListener('click', function () { $('settings-confirm').hidden = false; $('opt-new-yes').focus(); });
    $('opt-new-no').addEventListener('click', function () { $('settings-confirm').hidden = true; $('opt-new').focus(); });
    $('opt-new-yes').addEventListener('click', function () {
      closeDialog('dlg-settings');
      save();
      retireVoyage();
      begin(true);
    });
    $('opt-captain').addEventListener('click', function () { closeDialog('dlg-settings'); openCaptain(false); });
    $('cap-ok').addEventListener('click', function () { closeDialog('dlg-captain'); });
    // Closing the captain's card any way at all keeps what's on it.
    $('dlg-captain').addEventListener('close', function () {
      if (!state) return;
      applyCaptain();
      var f = capDone; capDone = null;
      if (f) f(); else setTimeout(focusSea, 0);
    });
    $('base-leave').addEventListener('click', function () { leaveBase(); });
    $('dlg-hideout').addEventListener('close', function () { if (state && state.atBase && !$('dlg-hideout').open) leaveBase(); });

    Array.prototype.forEach.call(document.querySelectorAll('[data-close]'), function (b) {
      b.addEventListener('click', function () { closeDialog(b.closest('dialog')); });
    });
    $('note-ok').addEventListener('click', function () { closeDialog('dlg-note'); });
    $('share-copy').addEventListener('click', function () {
      var inp = $('share-link');
      function done(ok) { shareSay(ok ? 'Link copied. Paste it in a text or a message.' : 'Your browser wouldn’t copy it. The link is selected, so copy it yourself.'); }
      track('board-copy');
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(inp.value).then(function () { done(true); }, function () { inp.select(); done(false); });
      else { inp.select(); var ok = false; try { ok = document.execCommand('copy'); } catch (e) { ok = false; } done(ok); }
    });
    $('share-send').addEventListener('click', function () {
      if (!navigator.share) return;
      track('board-send');
      navigator.share({title: 'Pillage the Reefer', text: 'Can you beat my score on the ' + BOARD.name + ' board?', url: $('share-link').value}).catch(function () { /* they changed their mind */ });
    });
    // Back to where the share began: the captain's log, the title screen or the sea.
    $('dlg-share').addEventListener('close', function () {
      setTimeout(function () {
        var back = document.querySelector('dialog[open] .board-share') || (!$('title-screen').hidden && $('title-board').querySelector('.board-share'));
        if (back) back.focus(); else focusSea();
      }, 0);
    });
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
    if (osReduce && osReduce.addEventListener) osReduce.addEventListener('change', function () { needRender = true; calmClass(); });
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
  calmClass();
  takeScoreFromLink();
  var howBoard = $('how-board');
  if (howBoard) howBoard.hidden = !boardShown();
  showTitle();
  loadJokes();
  requestAnimationFrame(frame);
  window.__pillage = {get state() { return state; }, step: step, begin: begin, dock: dock, planRoute: planRoute, openChart: openChart, encounter: encounter, tryDig: tryDig,
    npcs: function () { return npcs; }, runEvent: runEvent, giveMap: giveMap, gainXp: gainXp, events: EV,
    smoke: smoke, stats: stats, passage: passage, voyage: voyage, passageRisk: passageRisk, bestRuns: bestRuns, odds: {chanceOf: chanceOf, pct: pct, roll: roll},
    fight: fight, checkGoals: checkGoals, openCargo: openCargo, hiddenCount: hiddenCount, mkt: mkt, stockOf: stockOf, buyBales: buyBales, sellBales: sellBales,
    buyAt: buyAt, sellAt: sellAt, enterBase: enterBase, leaveBase: leaveBase, stash: stash, unstash: unstash, effects: effects, lobPick: lobPick,
    get legacy() { return legacy; }, openCaptain: openCaptain, showTitle: showTitle,
    jobOffers: jobOffers, takeJob: takeJob, settleJobs: settleJobs, dayTick: dayTick, standOf: standOf, shift: shift, buyFor: buyFor, sellFor: sellFor,
    makeNews: makeNews, jobLoad: jobLoad, space: space, openParcels: openParcels, showTab: showTab, openPort: openPort,
    hungry: hungry, buyFood: buyFood, customs: customs, bigHaul: bigHaul,
    buySeed: buySeed, plant: plant, harvest: harvest, crossBeds: crossBeds, bedReady: bedReady, crossOf: crossOf, renderHideout: renderHideout,
    scoreCode: scoreCode, readScore: readScore, scoreLink: scoreLink, myBest: myBest, takeScoreFromLink: takeScoreFromLink, boardOpen: boardOpen, openShare: openShare,
    renderLog: renderLog};
})();
