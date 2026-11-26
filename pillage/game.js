/* Pillage the Reefer: the game screen, controls, ports, people and saving. */
(function () {
  'use strict';
  var D = window.PILLAGE_DATA, E = window.PILLAGE_ENGINE;
  if (!D || !E || !document.getElementById('sea')) return;
  var GOODS = D.GOODS, MAPS = D.MAPS, PORTS = D.PORTS, STASHES = D.STASHES, PEOPLE = D.PEOPLE, QUESTS = D.QUESTS, UP = D.UPGRADES;
  var SAVE_KEY = 'pillageTheReefer.v1', PREF_KEY = 'pillageTheReefer.prefs';
  var FOG = 40, REVEAL = 190, ORDER = Object.keys(GOODS);
  var clamp = E.clamp;
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
  function oddsWord(p) { return p < 0.35 ? 'long odds' : p < 0.5 ? 'even odds' : p < 0.65 ? 'decent odds' : p < 0.8 ? 'good odds' : 'great odds'; }
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
  var keys = {}, timers = {reveal: 0, save: 4, where: 0, wake: 0}, lastRank = '', lastWhereKey = '', toastTimer = 0;

  function newState() {
    var p = PORTS.tortuga;
    return {v: 1, map: 'windward', x: p.dock[0], y: p.dock[1], angle: -Math.PI / 2, gold: 150, cargo: {},
      up: {hold: 0, sails: 0, cannons: 0, lavender: 0}, dist: 0, hints: {}, found: {}, quests: {}, visited: {},
      known: {tortuga: 1, portroyal: 1, petitgoave: 1}, collected: {}, pillaged: 0, flags: {}, docked: null, fog: {}};
  }
  function curMap() { return MAPS[state.map]; }
  function cargoCount() { var n = 0; for (var g in state.cargo) n += state.cargo[g]; return n; }
  function capacity() { return UP.hold.levels[state.up.hold]; }
  function space() { return Math.max(0, capacity() - cargoCount()); }
  function addCargo(g, n) {
    n = Math.max(0, Math.min(n, space()));
    if (n > 0) { state.cargo[g] = (state.cargo[g] || 0) + n; state.collected[g] = 1; }
    return n;
  }
  function takeCargo(g, n) {
    n = Math.max(0, Math.min(n, state.cargo[g] || 0));
    state.cargo[g] -= n;
    if (!state.cargo[g]) delete state.cargo[g];
    return n;
  }
  function cargoValue() { var v = 0; for (var g in state.cargo) v += state.cargo[g] * GOODS[g].base; return v; }
  function day() { return E.dayOf(state.dist); }
  function pieces() { return ['s1', 's2', 's3'].filter(function (k) { return state.found[k]; }).length; }
  function speed() { return 95 * (1 + 0.18 * state.up.sails); }
  function rank() {
    if (state.found.emerald) return 'Legend of the Reefer';
    var w = state.gold + cargoValue(), r = D.RANKS[0][1];
    D.RANKS.forEach(function (x) { if (w >= x[0]) r = x[1]; });
    return r;
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
        if (typeof s[k] === 'object') b[k] = k === 'up' ? Object.assign(b[k], s[k]) : s[k];
      } else if (typeof b[k] === typeof s[k]) b[k] = s[k];
    }
    if (s.docked && PORTS[s.docked]) b.docked = s.docked; else b.docked = null;
    for (var g in b.cargo) if (!GOODS[g] || !(b.cargo[g] > 0)) delete b.cargo[g];
    for (var u in b.up) if (!(b.up[u] >= 0) || b.up[u] >= UP[u].levels.length) b.up[u] = 0;
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
        return {kind: p.kind, route: p.route, leg: 0, path: null, pi: 0, x: s[0], y: s[1], angle: 0, cool: 8, chase: false, looted: false,
          name: pick(p.kind === 'customs' ? D.CUSTOMS_NAMES : D.MERCHANT_NAMES)};
      });
    }
    if (!floaters[mid]) {
      floaters[mid] = {list: [], timer: 12, bottle: 25};
      for (var i = 0; i < 3; i++) { var b = spawnFloater(m, false); if (b) floaters[mid].list.push(b); }
    }
    return m;
  }
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
  function exitPoint(e) {
    var r = e.rect;
    if (r[2] > r[3]) return [clamp(state.x, r[0] + 40, r[0] + r[2] - 40), r[1] + r[3] / 2];
    return [r[0] + r[2] / 2, clamp(state.y, r[1] + 20, r[1] + r[3] - 20)];
  }
  function planRoute(goal) {
    var m = curMap(), target, exit = null;
    if (goal.map === state.map) target = [goal.x, goal.y];
    else {
      var next = state.map === 'windward' ? goal.map : 'windward';
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
    else if (g.type === 'stash') tryDig(g.id);
  }
  function transition(exit, goal) {
    goal = goal || (auto && auto.goal);
    auto = null;
    var m = enterMap(exit.to), a = exit.arrive;
    var x = a[0] === 'x' ? clamp(state.x, 80, m.w - 80) : a[0];
    var f = E.nearestFreePoint(m, x, a[1]);
    state.map = exit.to; state.x = f[0]; state.y = f[1];
    ship.vx *= 0.5; ship.vy *= 0.5; wake = [];
    grace = 1.5;
    reveal(state.map, state.x, state.y, REVEAL);
    snapCamera();
    say('⛵ You sail into ' + m.name + '. ' + m.blurb);
    if (goal && goal.type !== 'point') planRoute(goal);
    updateWhere(true);
    save();
  }
  function dock(pid) {
    var p = PORTS[pid], first = !state.visited[pid];
    auto = null; ship.vx = ship.vy = 0;
    state.docked = pid; state.visited[pid] = 1; state.known[pid] = 1;
    var f = E.nearestFreePoint(curMap(), p.dock[0], p.dock[1]);
    state.x = f[0]; state.y = f[1];
    reveal(state.map, p.dock[0], p.dock[1], 170);
    sfx('splash');
    checkGoals();
    save();
    updateWhere(true);
    openPort(pid, first ? 'tavern' : 'market');
  }
  function leavePort(silent) {
    if (!state.docked) return;
    var pid = state.docked;
    state.docked = null;
    justLeft = pid;
    grace = 1.2;
    closeDialog('dlg-port');
    if (!silent) say('⛵ You cast off from ' + PORTS[pid].name + '.');
    updateWhere(true);
    if (!state.flags.p_steer) setTimeout(function () { parrot('steer', 'Arrow keys or tap the sea to steer! Chart & sail picks a port for you! Squawk!', true); }, 1200);
    save();
    focusSea();
  }

  function step(dt) {
    t += dt;
    if (toastTimer > 0) { toastTimer -= dt; if (toastTimer <= 0) $('toast').classList.remove('show'); }
    if (paused() || state.docked) return;
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
    if (timers.reveal <= 0) { timers.reveal = 0.2; reveal(state.map, state.x, state.y, REVEAL); }

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
      F.timer = 16 + Math.random() * 18;
      if (F.list.filter(function (b) { return b.g !== 'bottle'; }).length < 4) { var b = spawnFloater(m, false); if (b) F.list.push(b); }
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
    var list = npcs[state.map], hasCargo = cargoCount() > 0;
    for (var i = 0; i < list.length; i++) {
      var n = list[i];
      if (n.cool > 0) n.cool -= dt;
      if (n.looted && n.cool <= 0) { n.looted = false; n.name = pick(D.MERCHANT_NAMES); }
      var d = Math.hypot(n.x - state.x, n.y - state.y), tx, ty, sp = n.kind === 'customs' ? 78 : 48;
      var nose = 210 * (state.up.lavender ? 0.55 : 1) * (state.flags.vicar ? 0.7 : 1);
      var chase = n.kind === 'customs' && n.cool <= 0 && hasCargo && d < nose && E.walkable(m, [n.x, n.y], [state.x, state.y]);
      if (chase && !n.chase) parrot('customs', 'Blue sails! Blue sails! Customs! Squawk!', false, 30);
      if (!chase && n.chase) n.path = null;
      n.chase = chase;
      if (chase) { tx = state.x; ty = state.y; sp = 84; }
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
      if (d < 26 && grace <= 0 && n.cool <= 0 && !(n.kind === 'merchant' && n.looted)) { encounter(n); return; }
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

  function tryDig(sid) {
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
    var text = s.text;
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
      extra = el('p', {class: 'win'}, 'You are now a Legend of the Reefer. Day ' + day() + ', ' + fmt(state.gold) + ' doubloons, ' + state.pillaged + ' ' + plural(state.pillaged, 'ship') + ' pillaged, ' + Object.keys(state.collected).length + ' of 10 strains collected. The sea is still yours: keep sailing as long as you like.');
    }
    checkGoals();
    save();
    note(title, text, extra);
  }

  /* ---------- run-ins at sea ---------- */
  function confiscate(frac) {
    var total = 0;
    Object.keys(state.cargo).forEach(function (g) { total += takeCargo(g, Math.ceil(state.cargo[g] * frac)); });
    return total;
  }
  function encounter(n) {
    ship.vx *= 0.2; ship.vy *= 0.2;
    keys = {};
    sfx('boom');
    if (n.kind === 'customs') customs(n); else merchant(n);
  }
  function customs(n) {
    var done = function () { n.cool = 18; grace = 3; };
    if (!cargoCount()) {
      showEncounter('🔵 Crown Customs', n.name + ' of the Crown Customs pulls alongside, sniffs the air and peers into your empty hold. “Nothing aboard but a parrot? Carry on, Captain.”', [{label: 'Carry on'}], done);
      return;
    }
    var bribe = Math.max(15, Math.round(cargoValue() * 0.18));
    var runP = Math.min(0.95, 0.35 + 0.17 * state.up.sails + (state.flags.vicar ? 0.1 : 0));
    var shotP = Math.min(0.95, 0.2 + 0.17 * state.up.cannons);
    var talkP = 0.3 + (state.flags.vicar ? 0.3 : 0);
    showEncounter('🔵 Crown Customs!', n.name + ' of the Crown Customs blocks your way. “Inspection! What is that smell? Is that… citrus?”', [
      {label: '🪙 Pay a “paperwork fee” of ' + fmt(bribe) + ' doubloons', disabled: state.gold < bribe, fn: function () {
        state.gold -= bribe; sfx('coin');
        return pick([n.name + ' pockets the fee, stamps a form in triplicate and wishes you a pleasant voyage.',
          'The fee vanishes into a very large hat. “Everything appears to be in order,” says ' + n.name + ', not looking at anything.']);
      }},
      {label: '⛵ Run for it (' + oddsWord(runP) + ')', fn: function () {
        if (Math.random() < runP) return 'You crowd on every scrap of sail and leave the cutter wallowing in your wake. Somewhere behind you, a whistle is blown very angrily.';
        var lost = confiscate(0.5); sfx('bad');
        return 'They catch you before you clear the reef. ' + n.name + ' confiscates ' + baleWord(lost) + ' “for evidence.” You hear coughing from their ship for the rest of the afternoon.';
      }},
      {label: '💣 Fire a warning shot (' + oddsWord(shotP) + ')', fn: function () {
        if (Math.random() < shotP) return 'BOOM. The cannonball lands a polite distance from their bow. After a short meeting, the cutter decides it left the kettle on and sails home.';
        var lost = confiscate(1 / 3), fine = Math.min(state.gold, Math.round(state.gold * 0.1));
        state.gold -= fine; sfx('bad');
        return 'BOOM. You hit their flagpole. ' + n.name + ' is furious, seizes ' + baleWord(lost) + ' and fines you ' + fmt(fine) + ' doubloons for damage to Crown property.';
      }},
      {label: '🗣️ Ask about their day (' + oddsWord(talkP) + ')', fn: function () {
        if (Math.random() < talkP) return pick(['“Rough day?” you ask. ' + n.name + ' talks for forty minutes about a stapler. Everyone forgets about the inspection.',
          'You compliment their hat. They blush, wave you through and ask where you got your parrot.',
          'You explain it’s all for a botanist in Cartagena. Technically true. They let you go with a warning and a pamphlet.']);
        var lost = confiscate(0.25); sfx('bad');
        return n.name + ' is not interested in your thoughts on the weather and confiscates ' + baleWord(lost) + '.';
      }}
    ], done);
  }
  function merchant(n) {
    var boardP = Math.min(0.95, 0.45 + 0.13 * state.up.cannons);
    showEncounter('🟤 A fat merchantman!', cap(n.name) + ' wallows alongside, low in the water. Her crew looks nervous. Her cargo smells wonderful.', [
      {label: '⚔️ Board her! (' + oddsWord(boardP) + ')', fn: function () {
        if (Math.random() >= boardP) {
          var cost = Math.min(state.gold, 30 + Math.floor(Math.random() * 40));
          state.gold -= cost; sfx('bad');
          return 'Her crew fends you off with mops, buckets and a strongly worded letter. Repairs cost you ' + fmt(cost) + ' doubloons.';
        }
        n.looted = true; n.cool = 60; state.pillaged++;
        var haul = {}, count = 3 + Math.floor(Math.random() * 5) + state.up.cannons, total = 0;
        if (Math.random() < 0.4) { haul.kraken = Math.random() < 0.3 ? 2 : 1; total = haul.kraken; }
        while (total < count) { var g = pick(D.COMMON); haul[g] = (haul[g] || 0) + 1; total++; }
        var gold = 30 + Math.floor(Math.random() * 90), got = [], left = 0;
        state.gold += gold;
        Object.keys(haul).forEach(function (g) {
          var k = addCargo(g, haul[g]);
          if (k) got.push(baleWord(k) + ' of ' + GOODS[g].name);
          left += haul[g] - k;
        });
        sfx('coin');
        if (state.pillaged === 1) track('first-pillage');
        return 'With a mighty “Arrr!” your crew swings aboard. The merchants surrender at once; they’re paid by the hour. You take ' + fmt(gold) + ' doubloons' +
          (got.length ? ' and ' + andList(got) : '') + '.' + (left ? ' Your hold can’t fit the other ' + baleWord(left) + '.' : '');
      }},
      {label: '👋 Wave politely', fn: function () {
        if (Math.random() < 0.25 && space() > 0) { var g = pick(D.COMMON); addCargo(g, 1); return 'The merchants wave back. Touched, they toss you a bale of ' + GOODS[g].name + ' out of pure pity.'; }
        return 'The merchants wave back. Everyone feels good about it. Nothing else happens.';
      }},
      {label: '⛵ Leave her be', fn: function () { return 'You let ' + n.name + ' waddle on. The sea is big enough for everyone.'; }}
    ], function () { if (!n.looted) n.cool = 12; grace = 3; });
  }
  function showEncounter(title, text, opts, onDone) {
    var dlg = $('dlg-encounter'), body = $('enc-body');
    $('enc-title').textContent = title;
    body.textContent = '';
    var p = el('p', {id: 'enc-text'}, text), list = el('div', {class: 'choices'});
    body.appendChild(p);
    body.appendChild(list);
    function finish() { closeDialog(dlg); if (onDone) onDone(); checkGoals(); save(); }
    opts.forEach(function (o) {
      var b = el('button', {type: 'button', class: 'choice'}, o.label);
      if (o.disabled) { b.disabled = true; b.setAttribute('aria-describedby', 'enc-text'); }
      b.addEventListener('click', function () {
        var res = o.fn ? o.fn() : null;
        if (!res) { finish(); return; }
        p.textContent = res;
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

  /* ---------- ports ---------- */
  var portTab = 'market', talkNode = 'start';
  function portTabs(pid) {
    var p = PORTS[pid], tabs = [['market', '🛒 Market'], ['tavern', '🍺 Tavern']];
    if (p.yard) tabs.push(['yard', '🔨 Shipwright']);
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
    $('port-status').textContent = '🪙 ' + fmt(state.gold) + ' doubloons · 📦 ' + cargoCount() + ' of ' + capacity() + ' bales · 📅 Day ' + day();
    if (portTab === 'market') renderMarket(pid, panel);
    else if (portTab === 'tavern') renderTavern(pid, panel);
    else renderYard(panel);
    if (keepKey) {
      var again = panel.querySelector('[data-key="' + keepKey + '"]');
      if (again && !again.disabled) again.focus();
      else { var h = panel.querySelector('h3'); if (h) { h.tabIndex = -1; h.focus(); } }
    }
  }
  function trade(pid, g, n, buying) {
    var price = buying ? E.buyPrice(pid, g, day()) : E.sellPrice(pid, g, day());
    if (buying) {
      n = Math.min(n, space(), Math.floor(state.gold / price));
      if (n <= 0) return;
      state.gold -= n * price;
      addCargo(g, n);
      say('Bought ' + baleWord(n) + ' of ' + GOODS[g].name + ' for ' + fmt(n * price) + ' doubloons.');
    } else {
      n = takeCargo(g, n);
      if (n <= 0) return;
      state.gold += n * price;
      say('Sold ' + baleWord(n) + ' of ' + GOODS[g].name + ' for ' + fmt(n * price) + ' doubloons.');
    }
    sfx('coin');
    checkGoals();
    save();
  }
  function renderMarket(pid, panel) {
    var p = PORTS[pid], d = day();
    var list = ORDER.filter(function (g) { return p.sells.indexOf(g) >= 0 || state.cargo[g]; });
    list.sort(function (a, b) { return (GOODS[b].home === pid) - (GOODS[a].home === pid); });
    var held = Object.keys(state.cargo), total = 0;
    held.forEach(function (g) { total += state.cargo[g] * E.sellPrice(pid, g, d); });
    var intro = el('p', {class: 'hint'}, 'Prices change every day. Each port grows one strain cheaply and pays more for strains from elsewhere, most of all from another sea.');
    panel.appendChild(intro);
    if (held.length) {
      var all = el('button', {type: 'button', class: 'secondary sellall', 'data-key': 'sellall'}, '💰 Sell the whole hold for ' + fmt(total) + ' doubloons');
      all.addEventListener('click', function () {
        var n = cargoCount();
        Object.keys(state.cargo).forEach(function (g) { state.gold += state.cargo[g] * E.sellPrice(pid, g, d); });
        state.cargo = {};
        sfx('coin');
        say('Sold all ' + baleWord(n) + ' for ' + fmt(total) + ' doubloons.');
        checkGoals(); save(); renderPanel('sellall');
      });
      panel.appendChild(all);
    }
    var ul = el('ul', {class: 'goods'});
    list.forEach(function (g) {
      var G = GOODS[g], bp = E.buyPrice(pid, g, d), spr = E.sellPrice(pid, g, d), have = state.cargo[g] || 0;
      var li = el('li', {class: 'good'});
      var head = el('div', {class: 'g-head'});
      head.appendChild(el('span', {class: 'g-ico', 'aria-hidden': 'true'}, G.icon));
      head.appendChild(el('h3', null, G.name));
      if (G.home === pid) head.appendChild(el('span', {class: 'tag'}, 'Grown here'));
      li.appendChild(head);
      li.appendChild(el('p', {class: 'g-note'}, G.note));
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
      li.appendChild(btns);
      ul.appendChild(li);
    });
    panel.appendChild(ul);
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
        say('🪙 Delivered! +' + fmt(qq.gold) + ' doubloons.');
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
      var now = k === 'hold' ? 'Holds ' + U.levels[lvl] + ' bales now.' : k === 'lavender' ? (lvl ? 'Fitted.' : 'Not fitted yet.') : 'Level ' + lvl + ' of ' + max + '.';
      li.appendChild(el('p', {class: 'g-note'}, U.note + ' ' + now));
      var btns = el('div', {class: 'g-btns'});
      if (lvl < max) {
        var cost = U.cost[lvl], label = k === 'hold' ? 'Grow to ' + U.levels[lvl + 1] + ' bales' : k === 'lavender' ? 'Fit it' : 'Upgrade to level ' + (lvl + 1);
        var b = el('button', {type: 'button', 'data-key': 'up' + k, 'aria-label': label + ' for ' + fmt(cost) + ' doubloons'}, label + ' · ' + fmt(cost) + ' 🪙');
        b.disabled = state.gold < cost;
        b.addEventListener('click', function () {
          if (state.gold < cost) return;
          state.gold -= cost; state.up[k]++;
          sfx('fanfare');
          say('🔨 ' + U.name + ': done! ' + (k === 'hold' ? 'Your hold now takes ' + capacity() + ' bales.' : 'The shipwright wipes their hands and grins.'));
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
    var visited = Object.keys(state.visited).length, strains = Object.keys(state.collected).length;
    return [
      {id: 'full', text: 'Fill your hold to the brim', done: !!state.flags.full},
      {id: 'k1', text: 'Have 1,000 doubloons in your purse', done: !!state.flags.k1},
      {id: 'pillage', text: 'Pillage a merchant ship', done: state.pillaged > 0},
      {id: 'ports', text: 'Drop anchor in all 8 ports', n: visited + ' of 8', done: visited >= 8},
      {id: 'pieces', text: 'Find the 3 pieces of Captain Featherstone’s map', n: pieces() + ' of 3', done: pieces() >= 3},
      {id: 'emerald', text: 'Dig up the Emerald Bale', done: !!state.found.emerald},
      {id: 'strains', text: 'Collect all 10 strains', n: strains + ' of 10', done: strains >= 10},
      {id: 'commodore', text: 'Reach the rank of Commodore (12,000 doubloons in gold and cargo)', done: !!state.flags.commodore}
    ];
  }
  function checkGoals() {
    if (!state) return;
    if (cargoCount() >= capacity()) state.flags.full = 1;
    if (state.gold >= 1000) state.flags.k1 = 1;
    if (state.gold + cargoValue() >= 12000) state.flags.commodore = 1;
    goalList().forEach(function (g) {
      if (g.done && !state.flags['g_' + g.id]) {
        state.flags['g_' + g.id] = 1;
        sfx('fanfare');
        say('🏆 Goal complete: ' + g.text.replace(/ \(.*\)$/, '') + '!');
      }
    });
    var r = rank();
    if (lastRank && r !== lastRank && r !== 'Deckhand') say('🎖️ Promoted! You are now a ' + r + '.');
    lastRank = r;
    if (state.docked && openDialogEl() === $('dlg-port')) $('port-status').textContent = '🪙 ' + fmt(state.gold) + ' doubloons · 📦 ' + cargoCount() + ' of ' + capacity() + ' bales · 📅 Day ' + day();
  }
  function openLog() {
    var b = $('log-body');
    b.textContent = '';
    b.appendChild(el('p', null, '🎖️ ' + rank() + ' · 📅 Day ' + day() + ' · 🪙 ' + fmt(state.gold) + ' doubloons · ⛵ ' + fmt(state.dist / 100) + ' leagues sailed · ⚔️ ' + state.pillaged + ' ' + plural(state.pillaged, 'ship') + ' pillaged'));
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
    if (rum.length) {
      b.appendChild(el('h3', null, 'Treasure rumors'));
      var ru = el('ul', {class: 'checks'});
      rum.forEach(function (s) {
        var li = el('li');
        li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, '✖️'));
        li.appendChild(document.createTextNode('Something is buried on ' + STASHES[s].name + ' (' + MAPS[STASHES[s].map].short + ').'));
        ru.appendChild(li);
      });
      b.appendChild(ru);
    }
    b.appendChild(el('h3', null, 'Cargo hold: ' + cargoCount() + ' of ' + capacity() + ' bales'));
    var held = Object.keys(state.cargo);
    if (!held.length) b.appendChild(el('p', null, 'Empty, apart from a parrot and a smell.'));
    else {
      var cu = el('ul', {class: 'checks'});
      held.forEach(function (g) {
        var li = el('li');
        li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, GOODS[g].icon));
        li.appendChild(document.createTextNode(GOODS[g].name + ': ' + baleWord(state.cargo[g])));
        cu.appendChild(li);
      });
      b.appendChild(cu);
    }
    b.appendChild(el('h3', null, 'Strain ledger: ' + Object.keys(state.collected).length + ' of 10'));
    var lu = el('ul', {class: 'checks ledger'});
    ORDER.forEach(function (g) {
      var G = GOODS[g], has = state.collected[g], li = el('li', {class: has ? 'done' : ''});
      li.appendChild(el('span', {'aria-hidden': 'true', class: 'mark'}, has ? G.icon : '❔'));
      li.appendChild(el('span', {class: 'sr-only'}, has ? 'Collected: ' : 'Not yet: '));
      li.appendChild(document.createTextNode(G.name + ' · ' + (G.rare || 'Grown in ' + PORTS[G.home].name + '.')));
      lu.appendChild(li);
    });
    b.appendChild(lu);
    openDialog($('dlg-log'), $('log-close'));
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
    looted: {hull: '#6d5a48', deck: '#a99780', sail: '#b2a993', flag: '#7f7f7f'}
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
    return Object.keys(STASHES).filter(function (sid) {
      var s = STASHES[sid];
      return s.map === mid && !state.found[sid] && (state.hints[sid] || (s.needs && pieces() >= s.needs));
    });
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
        drawShip(c, n.x, n.y, n.angle, n.kind === 'customs' ? LOOK.customs : n.looted ? LOOK.looted : LOOK.merchant, n.kind === 'merchant' ? 20 : 15);
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
    stashMarks(mid).forEach(function (sid) {
      var s = STASHES[sid];
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
    stashMarks(mid).forEach(function (sid) {
      var s = STASHES[sid];
      pill(c, 'Buried treasure?', sx(s.at[0]), sy(s.at[1]) + (chart ? 22 : 34), {font: '700 11px system-ui, sans-serif', h: 18, bg: 'rgba(255,240,220,.94)', ink: '#7a1712'});
    });
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
    setText('h-day', String(day()));
    setText('h-rank', rank());
    setText('h-sea', MAPS[state.map].short);
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
    lastRank = rank();
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
      $('continue-note').textContent = 'Day ' + E.dayOf(s.dist) + ' · ' + fmt(s.gold) + ' doubloons · ' + MAPS[s.map].name;
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
    $('dlg-port').addEventListener('close', function () { if (state && state.docked) leavePort(); });
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
  window.__pillage = {get state() { return state; }, step: step, begin: begin, dock: dock, planRoute: planRoute, openChart: openChart, encounter: encounter, tryDig: tryDig, npcs: function () { return npcs; }};
})();
