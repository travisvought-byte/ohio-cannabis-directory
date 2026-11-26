/* Pillage the Reefer: geometry, sailing routes and prices. No drawing here, so it can be checked outside a browser. */
(function (root) {
  'use strict';
  var D = root.PILLAGE_DATA;
  var CELL = 20;    // route-finding grid, in map units
  var MARGIN = 13;  // how far routes keep from the shore
  var SHIP_R = 7;   // the ship's own size, for running aground
  // Plain square roots, not Math.hypot: every browser rounds them the same, so a voyage replays exactly anywhere.
  function hyp(x, y) { return Math.sqrt(x * x + y * y); }

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
      var dx = b[0] - a[0], dy = b[1] - a[1], L = hyp(dx, dy) || 1, tx = dx / L, ty = dy / L;
      if (i > 0) len += hyp(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
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
  // A real coastline has hundreds of corners, so its edges are filed by row and by square: a check then only
  // looks at the edges nearby. Small islands are quick enough without.
  var IX = 40;
  function indexPoly(p) {
    var pts = p.pts, n = pts.length;
    if (n < 150) return;
    var rows = {}, cells = {};
    for (var i = 0, j = n - 1; i < n; j = i++) {
      var a = pts[j], b = pts[i];
      var r0 = Math.floor(Math.min(a[1], b[1]) / IX), r1 = Math.floor(Math.max(a[1], b[1]) / IX);
      var c0 = Math.floor(Math.min(a[0], b[0]) / IX), c1 = Math.floor(Math.max(a[0], b[0]) / IX);
      for (var r = r0; r <= r1; r++) {
        (rows[r] = rows[r] || []).push(j);
        for (var c = c0; c <= c1; c++) (cells[r + ',' + c] = cells[r + ',' + c] || []).push(j);
      }
    }
    p.rows = rows; p.cells = cells;
  }
  function inPoly(p, x, y) {
    if (!p.rows) return pip(p.pts, x, y);
    var list = p.rows[Math.floor(y / IX)], pts = p.pts, n = pts.length, inside = false;
    if (!list) return false;
    for (var k = 0; k < list.length; k++) {
      var j = list[k], i = (j + 1) % n, xi = pts[i][0], yi = pts[i][1], xj = pts[j][0], yj = pts[j][1];
      if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) inside = !inside;
    }
    return inside;
  }
  function nearEdge(p, x, y, r) {
    var pts = p.pts, n = pts.length;
    if (!p.cells) {
      for (var k = 0, j = n - 1; k < n; j = k++) if (segDist(x, y, pts[j][0], pts[j][1], pts[k][0], pts[k][1]) < r) return true;
      return false;
    }
    var r0 = Math.floor((y - r) / IX), r1 = Math.floor((y + r) / IX), c0 = Math.floor((x - r) / IX), c1 = Math.floor((x + r) / IX);
    for (var rr = r0; rr <= r1; rr++) {
      for (var cc = c0; cc <= c1; cc++) {
        var list = p.cells[rr + ',' + cc];
        if (!list) continue;
        for (var q = 0; q < list.length; q++) {
          var a = list[q], b = (a + 1) % n;
          if (segDist(x, y, pts[a][0], pts[a][1], pts[b][0], pts[b][1]) < r) return true;
        }
      }
    }
    return false;
  }
  function segDist(px, py, ax, ay, bx, by) {
    var dx = bx - ax, dy = by - ay, l = dx * dx + dy * dy, t = l ? ((px - ax) * dx + (py - ay) * dy) / l : 0;
    t = clamp(t, 0, 1);
    return hyp(px - (ax + t * dx), py - (ay + t * dy));
  }
  function landAt(m, x, y) {
    for (var i = 0; i < m.polys.length; i++) {
      var p = m.polys[i], b = p.bb;
      if (x < b.x0 || x > b.x1 || y < b.y0 || y > b.y1) continue;
      if (inPoly(p, x, y)) return p;
    }
    return null;
  }
  function nearLand(m, x, y, r) {
    if (landAt(m, x, y)) return true;
    for (var i = 0; i < m.polys.length; i++) {
      var p = m.polys[i], b = p.bb;
      if (x < b.x0 - r || x > b.x1 + r || y < b.y0 - r || y > b.y1 + r) continue;
      if (nearEdge(p, x, y, r)) return true;
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
    var d = hyp(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.ceil(d / 6));
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
      // coast: a real outline, used as it is. blob: a small island drawn round. ribbon and poly: hand-drawn shapes.
      var pts = L.coast ? L.coast : L.ribbon ? ribbon(L.ribbon, 101 + i + hashStr(id) % 97) : L.blob ? blob(L.blob) : chaikin(L.poly, 2);
      var poly = {pts: pts, bb: bbox(pts), land: L, c: centroid(pts)};
      indexPoly(poly);
      L.shape = poly;
      return poly;
    });
    buildNav(m);
    m.ready = true;
    return m;
  }

  /* ---------- real positions: every sea is a Mercator window onto the Caribbean, all at one scale ---------- */
  function merc(lat) { return Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) * 180 / Math.PI; }
  function unmerc(y) { return (2 * Math.atan(Math.exp(y * Math.PI / 180)) - Math.PI / 2) * 180 / Math.PI; }
  function scaleOf(m) { return m.w / (m.geo.east - m.geo.west); }
  // [longitude, latitude] of a point on a sea's chart, and back.
  function toLonLat(m, x, y) { var k = scaleOf(m); return [m.geo.west + x / k, unmerc(merc(m.geo.north) - y / k)]; }
  function fromLonLat(m, lon, lat) { var k = scaleOf(m); return [(lon - m.geo.west) * k, (merc(m.geo.north) - merc(lat)) * k]; }
  // Where a ship that sails out through an exit at (x, y) comes in on the next sea: the same real spot, just inside
  // that sea's own exit back, so it doesn't sail straight back out.
  function crossing(fromId, exit, x, y) {
    var A = D.MAPS[fromId], B = D.MAPS[exit.to], ll = toLonLat(A, x, y), p = fromLonLat(B, ll[0], ll[1]);
    var back = B.exits.filter(function (e) { return e.to === fromId; })[0];
    if (!back) return [B.w / 2, B.h / 2];
    var r = back.rect, IN = 30;
    if (r[2] > r[3]) {
      p[0] = clamp(p[0], r[0] + 40, r[0] + r[2] - 40);
      p[1] = r[1] < B.h / 2 ? r[1] + r[3] + IN : r[1] - IN;
    } else {
      p[1] = clamp(p[1], r[1] + 20, r[1] + r[3] - 20);
      p[0] = r[0] < B.w / 2 ? r[0] + r[2] + IN : r[0] - IN;
    }
    // Rounded to a 256th of a unit: browsers can disagree in the last digit of a logarithm, and a replayed voyage can't.
    return [Math.round(p[0] * 256) / 256, Math.round(p[1] * 256) / 256];
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
    else if (G.kind === 'grown') m = 1 + 0.3 * rand01('g' + pid + g);
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
  // What the captain's relics add up to for one stat (fight, sail, charm, hull, luck, sell, ...).
  function relicSum(s, key) {
    var R = D.RELICS || {}, rel = (s && s.relics) || {}, n = 0;
    for (var r in rel) if (rel[r] && R[r] && R[r][key]) n += R[r][key];
    return n;
  }
  function stats(s) {
    var U = D.UPGRADES, up = s.up || {}, k = s.skill || {};
    var fight = (k.fight || 0) + relicSum(s, 'fight'), sail = (k.sail || 0) + relicSum(s, 'sail'), charm = (k.charm || 0) + relicSum(s, 'charm');
    return {
      fire: 4 + 2 * (up.cannons || 0) + fight,
      hullMax: U.hull.levels[up.hull || 0] + relicSum(s, 'hull'),
      crew: up.crew || 0, sails: up.sails || 0, cannons: up.cannons || 0,
      fight: fight, sail: sail, charm: charm,
      speed: 95 * (1 + 0.15 * (up.sails || 0)) * (1 + 0.05 * sail)
    };
  }
  // kind: merchant, pirate, navy or boss. tier: 1 (a sloop) to 5 (a man-o'-war).
  function foe(kind, tier) {
    tier = Math.max(1, Math.min(5, Math.round(tier) || 1));
    var cls = (D.SHIP_CLASS || [])[tier - 1] || 'sloop';
    if (kind === 'boss') return {kind: kind, tier: 4, hull: 100, fire: 12, cls: 'flagship'};
    // A navy warship: a pirate of her size with a drilled crew behind every gun, so a little tougher.
    if (kind === 'navy') {
      tier = Math.max(3, tier);
      return {kind: kind, tier: tier, hull: 10 + 16 * tier, fire: 3 * tier + 1, cls: (D.NAVY_CLASS || [])[tier - 3] || 'frigate'};
    }
    if (kind === 'merchant') return {kind: kind, tier: tier, hull: 8 + 5 * tier, fire: 1 + tier, cls: 'merchantman'};
    return {kind: kind, tier: tier, hull: 4 + 14 * tier, fire: 3 * tier, cls: cls};
  }
  // How tough a pirate is: the sea's own roughness, one size up once you're famous, then the luck of the draw:
  // 10% a size smaller, 50% as expected, 28% one bigger, 12% two bigger. A new captain only meets the small ones.
  function pirateTier(sea, lv, r, early) {
    var off = r < 0.1 ? -1 : r < 0.6 ? 0 : r < 0.88 ? 1 : 2;
    if (early) off = Math.min(0, off);
    return Math.max(1, Math.min(5, (sea || 1) + (lv >= 8 ? 1 : 0) + off));
  }
  // Standing with a nation, -100 to 100, as a tier: 0 Hostile, 1 Wary, 2 Neutral, 3 Friendly, 4 Honoured.
  function standTier(v) {
    v = +v || 0;
    return v <= -60 ? 0 : v <= -20 ? 1 : v < 20 ? 2 : v < 60 ? 3 : 4;
  }
  // A twenty-sided die: a chance becomes the number you need to roll. 50% means 11 or better.
  function need(chance) { return 21 - Math.round(chance / 5); }

  /* ---------- markets: limited stock, and prices that move as you trade ---------- */
  // How many bales a market keeps on its shelves when it's fully stocked.
  function stockMax(pid, g) {
    var p = D.PORTS[pid], G = D.GOODS[g];
    if (!p || !G || p.sells.indexOf(g) < 0) return 0;
    var home = G.home === pid;
    if (G.kind === 'brick') return home ? 30 : 12;
    if (G.kind === 'product') return home ? 8 : 4;
    return home ? 16 : 8;
  }
  // Every bale you've bought here lately costs a little more; every bale you've sold fetches a little less.
  // Both wear off as the days pass (half a day's worth each day).
  var BUY_PUSH = 0.01, SELL_PUSH = 0.015;
  function pushed(price, n, buying) {
    if (!price) return price;
    return Math.max(1, Math.round(price * (buying ? 1 + BUY_PUSH * (n || 0) : Math.max(0.5, 1 - SELL_PUSH * (n || 0)))));
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
    toLonLat: toLonLat, fromLonLat: fromLonLat, crossing: crossing,
    cellIdx: cellIdx, cellCenter: cellCenter, nearestFreePoint: nearestFreePoint, walkable: walkable, findPath: findPath,
    dayOf: dayOf, buyPrice: buyPrice, sellPrice: sellPrice, wanted: wanted,
    levelOf: levelOf, stats: stats, foe: foe, hit: hit, boardChance: boardChance, fleeChance: fleeChance, danger: danger,
    relicSum: relicSum, pirateTier: pirateTier, need: need, standTier: standTier, stockMax: stockMax, pushed: pushed, BUY_PUSH: BUY_PUSH, SELL_PUSH: SELL_PUSH
  };
})(typeof window !== 'undefined' ? window : globalThis);
