/* Pillage the Reefer: geometry, sailing routes and prices. No drawing here, so it can be checked outside a browser. */
(function (root) {
  'use strict';
  var D = root.PILLAGE_DATA;
  var CELL = 20;    // route-finding grid, in map units
  var MARGIN = 13;  // how far routes keep from the shore
  var SHIP_R = 7;   // the ship's own size, for running aground

  function hashStr(s) {
    var h = 2166136261 >>> 0;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return h;
  }
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function rand01(key) { return rng(hashStr(String(key)))(); }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  /* ---------- island shapes ---------- */
  function blob(spec) {
    var cx = spec[0], cy = spec[1], rx = spec[2], ry = spec[3], rot = spec[4] || 0, seed = spec[5] || 1;
    var r = rng(seed * 7919 + 13), p1 = r() * 6.283, p2 = r() * 6.283, p3 = r() * 6.283;
    var n = clamp(Math.round((rx + ry) / 3), 16, 48), c = Math.cos(rot), s = Math.sin(rot), pts = [];
    for (var i = 0; i < n; i++) {
      var t = i / n * Math.PI * 2;
      var k = 1 + 0.11 * Math.sin(2 * t + p1) + 0.07 * Math.sin(3 * t + p2) + 0.04 * Math.sin(5 * t + p3);
      var x = Math.cos(t) * rx * k, y = Math.sin(t) * ry * k;
      pts.push([cx + x * c - y * s, cy + x * s + y * c]);
    }
    return pts;
  }

  function catmull(pts, steps) {
    var out = [];
    for (var i = 0; i < pts.length - 1; i++) {
      var p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || pts[i + 1];
      for (var s = 0; s < steps; s++) {
        var t = s / steps, t2 = t * t, t3 = t2 * t, q = [];
        for (var d = 0; d < p1.length; d++) {
          q.push(0.5 * (2 * p1[d] + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3));
        }
        out.push(q);
      }
    }
    out.push(pts[pts.length - 1].slice());
    return out;
  }

  function ribbon(spine, seed) {
    var pts = catmull(spine, 6), r = rng(seed), ph1 = r() * 6.28, ph2 = r() * 6.28;
    var left = [], right = [], len = 0, tan = [];
    for (var i = 0; i < pts.length; i++) {
      var a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      var dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, tx = dx / L, ty = dy / L;
      if (i > 0) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      var w = Math.max(3, pts[i][2]);
      var wl = w * (1 + 0.13 * Math.sin(len * 0.045 + ph1) + 0.07 * Math.sin(len * 0.11 + ph2));
      var wr = w * (1 + 0.13 * Math.sin(len * 0.05 + ph2) + 0.07 * Math.sin(len * 0.12 + ph1));
      tan.push([tx, ty, (wl + wr) / 2]);
      left.push([pts[i][0] - ty * wl, pts[i][1] + tx * wl]);
      right.push([pts[i][0] + ty * wr, pts[i][1] - tx * wr]);
    }
    function cap(p, t, sign) {
      var out = [], w = t[2];
      for (var k = 1; k < 6; k++) {
        var f = k / 6 * Math.PI, nx = -t[1], ny = t[0];
        out.push([p[0] + nx * w * Math.cos(f) * sign + t[0] * sign * w * Math.sin(f) * 0.9,
                  p[1] + ny * w * Math.cos(f) * sign + t[1] * sign * w * Math.sin(f) * 0.9]);
      }
      return out;
    }
    var end = pts.length - 1;
    return left.concat(cap(pts[end], tan[end], 1), right.reverse(), cap(pts[0], tan[0], -1));
  }

  function chaikin(pts, it) {
    for (var k = 0; k < it; k++) {
      var out = [];
      for (var i = 0; i < pts.length; i++) {
        var a = pts[i], b = pts[(i + 1) % pts.length];
        out.push([a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25], [a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75]);
      }
      pts = out;
    }
    return pts;
  }

  function bbox(pts) {
    var b = {x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity};
    pts.forEach(function (p) {
      if (p[0] < b.x0) b.x0 = p[0]; if (p[0] > b.x1) b.x1 = p[0];
      if (p[1] < b.y0) b.y0 = p[1]; if (p[1] > b.y1) b.y1 = p[1];
    });
    return b;
  }

  function centroid(pts) {
    var x = 0, y = 0;
    pts.forEach(function (p) { x += p[0]; y += p[1]; });
    return [x / pts.length, y / pts.length];
  }

  /* ---------- land tests ---------- */
  function pip(pts, x, y) {
    var inside = false;
    for (var i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      var xi = pts[i][0], yi = pts[i][1], xj = pts[j][0], yj = pts[j][1];
      if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) inside = !inside;
    }
    return inside;
  }
  function segDist(px, py, ax, ay, bx, by) {
    var dx = bx - ax, dy = by - ay, l = dx * dx + dy * dy, t = l ? ((px - ax) * dx + (py - ay) * dy) / l : 0;
    t = clamp(t, 0, 1);
    return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
  }
  function landAt(m, x, y) {
    for (var i = 0; i < m.polys.length; i++) {
      var p = m.polys[i], b = p.bb;
      if (x < b.x0 || x > b.x1 || y < b.y0 || y > b.y1) continue;
      if (pip(p.pts, x, y)) return p;
    }
    return null;
  }
  function nearLand(m, x, y, r) {
    if (landAt(m, x, y)) return true;
    for (var i = 0; i < m.polys.length; i++) {
      var p = m.polys[i], b = p.bb;
      if (x < b.x0 - r || x > b.x1 + r || y < b.y0 - r || y > b.y1 + r) continue;
      for (var k = 0, j = p.pts.length - 1; k < p.pts.length; j = k++) {
        if (segDist(x, y, p.pts[j][0], p.pts[j][1], p.pts[k][0], p.pts[k][1]) < r) return true;
      }
    }
    return false;
  }
  function shipBlocked(m, x, y) {
    if (x < 4 || y < 4 || x > m.w - 4 || y > m.h - 4) return true;
    return !!(landAt(m, x, y) || landAt(m, x + SHIP_R, y) || landAt(m, x - SHIP_R, y) || landAt(m, x, y + SHIP_R) || landAt(m, x, y - SHIP_R));
  }

  /* ---------- the route grid ---------- */
  function buildNav(m) {
    var cols = Math.ceil(m.w / CELL), rows = Math.ceil(m.h / CELL), blocked = new Uint8Array(cols * rows);
    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) {
        blocked[r * cols + c] = nearLand(m, (c + 0.5) * CELL, (r + 0.5) * CELL, MARGIN) ? 1 : 0;
      }
    }
    m.nav = {cols: cols, rows: rows, blocked: blocked};
  }
  function cellIdx(m, x, y) {
    var n = m.nav;
    return clamp(Math.floor(y / CELL), 0, n.rows - 1) * n.cols + clamp(Math.floor(x / CELL), 0, n.cols - 1);
  }
  function cellCenter(m, i) { var c = m.nav.cols; return [(i % c + 0.5) * CELL, (Math.floor(i / c) + 0.5) * CELL]; }
  function nearestFreeCell(m, i) {
    var n = m.nav;
    if (!n.blocked[i]) return i;
    var seen = new Uint8Array(n.blocked.length), q = [i], h = 0;
    seen[i] = 1;
    while (h < q.length) {
      var k = q[h++], c = k % n.cols, r = Math.floor(k / n.cols);
      var nb = [[c + 1, r], [c - 1, r], [c, r + 1], [c, r - 1]];
      for (var j = 0; j < 4; j++) {
        var cc = nb[j][0], rr = nb[j][1];
        if (cc < 0 || rr < 0 || cc >= n.cols || rr >= n.rows) continue;
        var idx = rr * n.cols + cc;
        if (seen[idx]) continue;
        if (!n.blocked[idx]) return idx;
        seen[idx] = 1; q.push(idx);
      }
    }
    return -1;
  }
  function nearestFreePoint(m, x, y) {
    if (!shipBlocked(m, x, y) && !m.nav.blocked[cellIdx(m, x, y)]) return [x, y];
    var i = nearestFreeCell(m, cellIdx(m, x, y));
    return i < 0 ? [x, y] : cellCenter(m, i);
  }
  function walkable(m, a, b) {
    var d = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.ceil(d / 6));
    for (var i = 0; i <= n; i++) {
      var t = i / n;
      if (m.nav.blocked[cellIdx(m, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)]) return false;
    }
    return true;
  }

  function Heap() { this.a = []; }
  Heap.prototype.push = function (f, v) {
    var a = this.a, i = a.length;
    a.push([f, v]);
    while (i > 0) { var p = (i - 1) >> 1; if (a[p][0] <= a[i][0]) break; var t = a[p]; a[p] = a[i]; a[i] = t; i = p; }
  };
  Heap.prototype.pop = function () {
    var a = this.a, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last;
      var i = 0;
      for (;;) {
        var l = 2 * i + 1, r = l + 1, m = i;
        if (l < a.length && a[l][0] < a[m][0]) m = l;
        if (r < a.length && a[r][0] < a[m][0]) m = r;
        if (m === i) break;
        var t = a[m]; a[m] = a[i]; a[i] = t; i = m;
      }
    }
    return top;
  };

  /* A route of points from (sx, sy) to (tx, ty) around the land, or null if there is none. */
  function findPath(m, sx, sy, tx, ty) {
    var n = m.nav, s = nearestFreeCell(m, cellIdx(m, sx, sy)), t = nearestFreeCell(m, cellIdx(m, tx, ty));
    if (s < 0 || t < 0) return null;
    var goal = shipBlocked(m, tx, ty) || n.blocked[cellIdx(m, tx, ty)] ? cellCenter(m, t) : [tx, ty];
    if (s === t) return [goal];
    var size = n.blocked.length, g = new Float64Array(size), came = new Int32Array(size), closed = new Uint8Array(size);
    for (var i = 0; i < size; i++) { g[i] = Infinity; came[i] = -1; }
    var tc = t % n.cols, tr = Math.floor(t / n.cols);
    function hfn(k) { var dc = Math.abs(k % n.cols - tc), dr = Math.abs(Math.floor(k / n.cols) - tr); return Math.max(dc, dr) + 0.414 * Math.min(dc, dr); }
    var open = new Heap();
    g[s] = 0; open.push(hfn(s), s);
    var dirs = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, 1.414], [1, -1, 1.414], [-1, 1, 1.414], [-1, -1, 1.414]];
    var found = false;
    while (open.a.length) {
      var cur = open.pop()[1];
      if (closed[cur]) continue;
      if (cur === t) { found = true; break; }
      closed[cur] = 1;
      var cc = cur % n.cols, cr = Math.floor(cur / n.cols);
      for (var d = 0; d < 8; d++) {
        var nc = cc + dirs[d][0], nr = cr + dirs[d][1];
        if (nc < 0 || nr < 0 || nc >= n.cols || nr >= n.rows) continue;
        var ni = nr * n.cols + nc;
        if (n.blocked[ni] || closed[ni]) continue;
        if (dirs[d][2] > 1 && (n.blocked[cr * n.cols + nc] || n.blocked[nr * n.cols + cc])) continue;
        var ng = g[cur] + dirs[d][2];
        if (ng < g[ni]) { g[ni] = ng; came[ni] = cur; open.push(ng + hfn(ni), ni); }
      }
    }
    if (!found) return null;
    var cells = [];
    for (var k = t; k !== -1; k = came[k]) cells.push(cellCenter(m, k));
    cells.reverse();
    cells[cells.length - 1] = goal;
    var out = [cells[0]], a = 0;
    while (a < cells.length - 1) {
      var b = cells.length - 1;
      while (b > a + 1 && !walkable(m, cells[a], cells[b])) b--;
      out.push(cells[b]); a = b;
    }
    // Start from the ship itself when the first leg is clear.
    if (out.length > 1 && walkable(m, [sx, sy], out[1]) && !n.blocked[cellIdx(m, sx, sy)]) out.shift();
    return out;
  }

  function prepareMap(id) {
    var m = D.MAPS[id];
    if (m.ready) return m;
    m.id = id;
    m.polys = m.lands.map(function (L, i) {
      var pts = L.ribbon ? ribbon(L.ribbon, 101 + i + hashStr(id) % 97) : L.blob ? blob(L.blob) : chaikin(L.poly, 2);
      var poly = {pts: pts, bb: bbox(pts), land: L, c: centroid(pts)};
      L.shape = poly;
      return poly;
    });
    buildNav(m);
    m.ready = true;
    return m;
  }

  /* ---------- prices ---------- */
  function dayOf(dist) { return 1 + Math.floor((dist || 0) / 900); }
  // Daily drift. Strains move 12% either way; products set their own swing.
  function fluct(pid, g, day) { var G = D.GOODS[g], s = (G && G.swing) || 0.24; return 1 - s / 2 + s * rand01('f' + pid + g + day); }
  function wanted(pid, g) { var G = D.GOODS[g]; return !!(G && G.wants && G.wants.indexOf(pid) >= 0); }
  // charm is the captain's Charm skill: each point takes 2% off what you pay and adds 2% to what you get.
  function buyPrice(pid, g, day, charm) {
    var p = D.PORTS[pid], G = D.GOODS[g];
    if (!p || !G || p.sells.indexOf(g) < 0) return null;
    var m = G.home === pid ? 0.68 : 0.95 + 0.15 * rand01('b' + pid + g);
    return Math.max(1, Math.round(G.base * m * fluct(pid, g, day) * (1 - 0.02 * (charm || 0))));
  }
  function sellPrice(pid, g, day, charm) {
    var p = D.PORTS[pid], G = D.GOODS[g], m;
    if (G.home === pid) m = 0.5;
    else if (p.sells.indexOf(g) >= 0) m = 0.8;
    else if (G.rare) m = 0.95 + 0.3 * rand01('r' + pid + g);
    else if (wanted(pid, g)) m = 1.3 + 0.12 * rand01('w' + pid + g);
    else {
      m = 0.95 + 0.35 * rand01('d' + pid + g);
      if (D.PORTS[G.home].map !== p.map) m += 0.12;
    }
    return Math.max(1, Math.round(G.base * m * fluct(pid, g, day) * 0.92 * (1 + 0.02 * (charm || 0))));
  }

  /* ---------- the light RPG: renown, levels, ship stats and battles (plain maths, so a script can play it) ---------- */
  function levelOf(xp) {
    var L = D.LEVELS, n = 1;
    for (var i = 1; i < L.length; i++) if ((xp || 0) >= L[i].xp) n = i + 1;
    return n;
  }
  function stats(s) {
    var U = D.UPGRADES, up = s.up || {}, k = s.skill || {};
    return {
      fire: 4 + 2 * (up.cannons || 0) + (k.fight || 0),
      hullMax: U.hull.levels[up.hull || 0],
      crew: up.crew || 0, sails: up.sails || 0, cannons: up.cannons || 0,
      fight: k.fight || 0, sail: k.sail || 0, charm: k.charm || 0,
      speed: 95 * (1 + 0.15 * (up.sails || 0)) * (1 + 0.05 * (k.sail || 0))
    };
  }
  // kind: merchant, pirate or boss. tier: how rough the sea is, 1 to 3.
  function foe(kind, tier) {
    tier = Math.max(1, Math.min(3, Math.round(tier) || 1));
    if (kind === 'boss') return {kind: kind, tier: 4, hull: 100, fire: 12};
    if (kind === 'merchant') return {kind: kind, tier: tier, hull: 8 + 5 * tier, fire: 1 + tier};
    return {kind: kind, tier: tier, hull: 4 + 14 * tier, fire: 3 * tier};
  }
  // Damage stays within 15% of the ship's firepower, so the number on the button is what you get.
  function hit(fire, r) { return Math.max(1, Math.round((fire || 1) * (0.85 + 0.3 * r)) || 1); }
  function boardChance(st, en, enHull) {
    return clamp(0.2 + 0.55 * (1 - enHull / en.hull) + 0.05 * st.fight + 0.08 * st.crew - 0.05 * en.tier, 0.08, 0.95);
  }
  function fleeChance(st, en) { return clamp(0.5 + 0.08 * st.sails + 0.05 * st.sail - 0.07 * en.tier, 0.15, 0.92); }
  // 0 easy, 1 fair, 2 risky, 3 too strong: how much of your hull a straight broadside fight would cost.
  function danger(st, hull, en, enHull) {
    var rounds = Math.ceil((enHull === undefined ? en.hull : enHull) / st.fire), r = (rounds - 1) * en.fire / Math.max(1, hull);
    return r < 0.35 ? 0 : r < 0.7 ? 1 : r < 1 ? 2 : 3;
  }

  root.PILLAGE_ENGINE = {
    CELL: CELL, MARGIN: MARGIN, SHIP_R: SHIP_R,
    hashStr: hashStr, rng: rng, rand01: rand01, clamp: clamp,
    prepareMap: prepareMap, landAt: landAt, nearLand: nearLand, shipBlocked: shipBlocked,
    cellIdx: cellIdx, cellCenter: cellCenter, nearestFreePoint: nearestFreePoint, walkable: walkable, findPath: findPath,
    dayOf: dayOf, buyPrice: buyPrice, sellPrice: sellPrice, wanted: wanted,
    levelOf: levelOf, stats: stats, foe: foe, hit: hit, boardChance: boardChance, fleeChance: fleeChance, danger: danger
  };
})(typeof window !== 'undefined' ? window : globalThis);
