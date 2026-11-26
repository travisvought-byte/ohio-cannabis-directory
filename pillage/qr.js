// Pillage the Reefer: a small QR code maker for score cards. Byte mode, error correction level M, versions 1 to 10
// (up to 213 bytes), following the QR Code standard (ISO/IEC 18004). Written for this game; no outside code.
(function () {
  'use strict';
  // Per version: all codewords, blocks and error-correction codewords per block at level M, and alignment centres.
  var RAW = [0, 26, 44, 70, 100, 134, 172, 196, 242, 292, 346];
  var BLOCKS = [0, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5];
  var ECC = [0, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26];
  var ALIGN = [null, [], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34], [6, 22, 38], [6, 24, 42], [6, 26, 46], [6, 28, 50]];

  function gmul(x, y) {
    var z = 0;
    for (var i = 7; i >= 0; i--) { z = (z << 1) ^ ((z >>> 7) * 0x11d); z ^= ((y >>> i) & 1) * x; }
    return z & 0xff;
  }
  function rsDivisor(deg) {
    var r = [], i, j, root = 1;
    for (i = 0; i < deg - 1; i++) r.push(0);
    r.push(1);
    for (i = 0; i < deg; i++) {
      for (j = 0; j < r.length; j++) { r[j] = gmul(r[j], root); if (j + 1 < r.length) r[j] ^= r[j + 1]; }
      root = gmul(root, 2);
    }
    return r;
  }
  function rsRem(data, div) {
    var r = div.map(function () { return 0; });
    data.forEach(function (b) {
      var f = b ^ r.shift();
      r.push(0);
      div.forEach(function (c, i) { r[i] ^= gmul(c, f); });
    });
    return r;
  }
  function utf8(s) {
    if (typeof TextEncoder === 'function') return Array.prototype.slice.call(new TextEncoder().encode(s));
    var u = unescape(encodeURIComponent(s)), a = [];
    for (var i = 0; i < u.length; i++) a.push(u.charCodeAt(i));
    return a;
  }
  function maskOn(m, x, y) {
    switch (m) {
      case 0: return (x + y) % 2 === 0;
      case 1: return y % 2 === 0;
      case 2: return x % 3 === 0;
      case 3: return (x + y) % 3 === 0;
      case 4: return (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0;
      case 5: return x * y % 2 + x * y % 3 === 0;
      case 6: return (x * y % 2 + x * y % 3) % 2 === 0;
      default: return ((x + y) % 2 + x * y % 3) % 2 === 0;
    }
  }

  // Returns {version, size, mod: rows of booleans (true is dark)}, or null if the text is too long.
  function encode(text) {
    var bytes = utf8(String(text)), v, cap, i, j;
    for (v = 1; v <= 10; v++) {
      cap = (RAW[v] - BLOCKS[v] * ECC[v]) * 8;
      if (4 + (v < 10 ? 8 : 16) + bytes.length * 8 <= cap) break;
    }
    if (v > 10) return null;

    // The bit stream: byte mode, the length, the bytes, a terminator and the standard padding.
    var bits = [];
    function put(val, len) { for (var k = len - 1; k >= 0; k--) bits.push((val >>> k) & 1); }
    put(4, 4);
    put(bytes.length, v < 10 ? 8 : 16);
    bytes.forEach(function (b) { put(b, 8); });
    put(0, Math.min(4, cap - bits.length));
    put(0, (8 - bits.length % 8) % 8);
    for (var pad = 0xec; bits.length < cap; pad ^= 0xec ^ 0x11) put(pad, 8);
    var data = [];
    for (i = 0; i < bits.length; i += 8) { var by = 0; for (j = 0; j < 8; j++) by = (by << 1) | bits[i + j]; data.push(by); }

    // Split into blocks, add Reed-Solomon error correction to each, then interleave.
    var nb = BLOCKS[v], ec = ECC[v], raw = RAW[v], nShort = nb - raw % nb, shortLen = Math.floor(raw / nb);
    var div = rsDivisor(ec), blocks = [], at = 0;
    for (i = 0; i < nb; i++) {
      var dat = data.slice(at, at + shortLen - ec + (i < nShort ? 0 : 1));
      at += dat.length;
      var e = rsRem(dat, div);
      if (i < nShort) dat.push(0);
      blocks.push(dat.concat(e));
    }
    var cw = [];
    for (i = 0; i < blocks[0].length; i++) blocks.forEach(function (bl, k) { if (i !== shortLen - ec || k >= nShort) cw.push(bl[i]); });

    // The grid: finder squares, timing lines, alignment squares, format and version information.
    var size = v * 4 + 17, mod = [], fn = [];
    for (i = 0; i < size; i++) { mod.push([]); fn.push([]); for (j = 0; j < size; j++) { mod[i].push(false); fn[i].push(false); } }
    function set(x, y, d) { mod[y][x] = d; fn[y][x] = true; }
    for (i = 0; i < size; i++) { set(6, i, i % 2 === 0); set(i, 6, i % 2 === 0); }
    function finder(cx, cy) {
      for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++) {
        var x = cx + dx, y = cy + dy, d = Math.max(Math.abs(dx), Math.abs(dy));
        if (x >= 0 && x < size && y >= 0 && y < size) set(x, y, d !== 2 && d !== 4);
      }
    }
    finder(3, 3); finder(size - 4, 3); finder(3, size - 4);
    var al = ALIGN[v], last = al.length - 1;
    for (i = 0; i < al.length; i++) for (j = 0; j < al.length; j++) {
      if ((i === 0 && j === 0) || (i === 0 && j === last) || (i === last && j === 0)) continue;
      for (var ay = -2; ay <= 2; ay++) for (var ax = -2; ax <= 2; ax++) set(al[i] + ax, al[j] + ay, Math.max(Math.abs(ax), Math.abs(ay)) !== 1);
    }
    function format(mask) {
      var d = mask, r = d, k; // level M is 00
      for (k = 0; k < 10; k++) r = (r << 1) ^ ((r >>> 9) * 0x537);
      var b = ((d << 10) | r) ^ 0x5412, g = function (n) { return ((b >>> n) & 1) === 1; };
      for (k = 0; k <= 5; k++) set(8, k, g(k));
      set(8, 7, g(6)); set(8, 8, g(7)); set(7, 8, g(8));
      for (k = 9; k < 15; k++) set(14 - k, 8, g(k));
      for (k = 0; k < 8; k++) set(size - 1 - k, 8, g(k));
      for (k = 8; k < 15; k++) set(8, size - 15 + k, g(k));
      set(8, size - 8, true);
    }
    format(0);
    if (v >= 7) {
      var vr = v;
      for (i = 0; i < 12; i++) vr = (vr << 1) ^ ((vr >>> 11) * 0x1f25);
      var vb = (v << 12) | vr;
      for (i = 0; i < 18; i++) { var c = ((vb >>> i) & 1) === 1, a = size - 11 + i % 3, bb = Math.floor(i / 3); set(a, bb, c); set(bb, a, c); }
    }

    // The data, in the standard zig-zag up and down two columns at a time.
    var bi = 0, total = cw.length * 8;
    for (var right = size - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      for (var vert = 0; vert < size; vert++) for (j = 0; j < 2; j++) {
        var x = right - j, up = ((right + 1) & 2) === 0, y = up ? size - 1 - vert : vert;
        if (!fn[y][x] && bi < total) { mod[y][x] = ((cw[bi >>> 3] >>> (7 - (bi & 7))) & 1) === 1; bi++; }
      }
    }

    // Try the eight masks and keep the one that scans most easily.
    function apply(m) { for (var yy = 0; yy < size; yy++) for (var xx = 0; xx < size; xx++) if (!fn[yy][xx] && maskOn(m, xx, yy)) mod[yy][xx] = !mod[yy][xx]; }
    function line(get) {
      var p = 0, run = 1, k, s = '';
      for (k = 0; k < size; k++) {
        s += get(k) ? '1' : '0';
        if (k > 0) { if (get(k) === get(k - 1)) run++; else { if (run >= 5) p += run - 2; run = 1; } }
      }
      if (run >= 5) p += run - 2;
      s = '0000' + s + '0000';
      for (k = 0; k + 11 <= s.length; k++) { var w = s.substr(k, 11); if (w === '10111010000' || w === '00001011101') p += 40; }
      return p;
    }
    function penalty() {
      var p = 0, dark = 0, x2, y2;
      for (y2 = 0; y2 < size; y2++) {
        p += line(function (k) { return mod[y2][k]; });
        p += line(function (k) { return mod[k][y2]; });
      }
      for (y2 = 0; y2 < size; y2++) for (x2 = 0; x2 < size; x2++) {
        if (mod[y2][x2]) dark++;
        if (y2 < size - 1 && x2 < size - 1) { var cc = mod[y2][x2]; if (mod[y2][x2 + 1] === cc && mod[y2 + 1][x2] === cc && mod[y2 + 1][x2 + 1] === cc) p += 3; }
      }
      var all = size * size;
      p += Math.max(0, Math.ceil(Math.abs(dark * 20 - all * 10) / all) - 1) * 10;
      return p;
    }
    var best = 0, bestP = Infinity;
    for (var m = 0; m < 8; m++) {
      apply(m); format(m);
      var pp = penalty();
      if (pp < bestP) { bestP = pp; best = m; }
      apply(m);
    }
    apply(best); format(best);
    return {version: v, size: size, mod: mod};
  }

  // An SVG of the code with a white quiet zone, so it scans in dark mode too.
  function svg(text, label) {
    var q = encode(text);
    if (!q) return null;
    var n = q.size + 8, d = '', ns = 'http://www.w3.org/2000/svg';
    for (var y = 0; y < q.size; y++) for (var x = 0; x < q.size; x++) if (q.mod[y][x]) d += 'M' + (x + 4) + ' ' + (y + 4) + 'h1v1h-1z';
    var s = document.createElementNS(ns, 'svg'), bg = document.createElementNS(ns, 'rect'), p = document.createElementNS(ns, 'path');
    s.setAttribute('viewBox', '0 0 ' + n + ' ' + n);
    s.setAttribute('role', 'img');
    s.setAttribute('aria-label', label || 'QR code');
    s.setAttribute('shape-rendering', 'crispEdges');
    bg.setAttribute('width', n); bg.setAttribute('height', n); bg.setAttribute('fill', '#fff');
    p.setAttribute('d', d); p.setAttribute('fill', '#000');
    s.appendChild(bg); s.appendChild(p);
    return s;
  }

  window.PILLAGE_QR = {encode: encode, svg: svg};
})();
