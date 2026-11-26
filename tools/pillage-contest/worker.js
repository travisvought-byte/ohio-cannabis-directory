/* Pillage the Reefer: the Silver Cup server (a Cloudflare Worker, with D1 for the runs and a Durable Object for the
   ships you can see sailing live).
   - POST /api/start   enter a run: captain name, email (never shown), optional crew, 21+ and rules. Returns the run's seed.
   - POST /api/submit  send a run's recorded moves. They wait for the replay check; a phone's own score is never trusted.
   - GET  /api/board   the verified boards: captains, crews and each tally.
   - GET  /api/run     how one run stands (needs the run's key).
   - GET  /api/live    a WebSocket: where other players' ships are, live. Drawing only, never part of a score.
   - GET  /api/pending, GET /api/body, POST /api/verdict, POST /api/admin: for the replay checker and the contest's
     own GitHub workflows, which prove who they are with GitHub's signed tokens. No password is kept anywhere.
   - A daily cron wipes every email 60 days after the close. Winners' emails are read in Cloudflare's D1 console. */

const AUD = 'pillage-cup';
const DAY = 86400000;

function cfg(env) {
  return {
    start: Date.parse(env.START || '2026-12-01T08:00:00Z'),
    end: Date.parse(env.END || '2026-12-05T08:00:00Z'),
    grace: +(env.GRACE_MS || 5 * 60000),
    ver: env.VER || '',
    repo: env.REPO || 'travisvought-byte/ohio-cannabis-directory',
    origins: String(env.ORIGINS || 'https://the-reefer.com,https://www.the-reefer.com').split(',').map(s => s.trim()),
    jwks: env.JWKS_URL || 'https://token.actions.githubusercontent.com/.well-known/jwks',
    maxBody: +(env.MAX_BODY || 1800000),
    // New runs a day: from one network (a convention hall's Wi-Fi is one network for thousands) and for one captain.
    perIp: +(env.LIMIT_IP || 1500),
    perCaptain: +(env.LIMIT_RUNS || 60),
    // When entrants' emails are wiped: 60 days after the close, once winners have been reached and prizes shipped.
    purge: Date.parse(env.PURGE || '2027-02-03T08:00:00Z')
  };
}

/* ---------- small helpers ---------- */
function cors(req, env) {
  const o = req.headers.get('origin') || '', ok = cfg(env).origins.includes(o);
  return ok ? {'access-control-allow-origin': o, 'vary': 'origin', 'access-control-allow-headers': 'content-type, x-run-key', 'access-control-allow-methods': 'GET, POST, OPTIONS', 'access-control-max-age': '86400'} : {'vary': 'origin'};
}
function json(req, env, data, status, extra) {
  return new Response(JSON.stringify(data), {status: status || 200, headers: Object.assign({'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store'}, cors(req, env), extra || {})});
}
const fail = (req, env, status, msg) => json(req, env, {ok: false, error: msg}, status);
function hex(buf) { return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join(''); }
async function sha(s) { return hex(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))); }
function randHex(n) { const a = new Uint8Array(n); crypto.getRandomValues(a); return hex(a); }
function clean(v, max) { return String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f<>]/g, '').replace(/\s+/g, ' ').trim().slice(0, max); }
function fold(v) { return String(v).toLowerCase().normalize('NFKD').replace(/[^a-z0-9]/g, ''); }
async function gzip(bytes) { return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer()); }
async function gunzip(bytes, limit) {
  const reader = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')).getReader(), parts = [];
  let size = 0;
  for (;;) {
    const {done, value} = await reader.read();
    if (done) break;
    size += value.length;
    if (size > limit) { try { await reader.cancel(); } catch (e) { /* done */ } throw new Error('too big'); }
    parts.push(value);
  }
  const out = new Uint8Array(size);
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}
async function ipKey(req) { return (await sha('pillage-ip:' + (req.headers.get('cf-connecting-ip') || 'none') + ':' + new Date().toISOString().slice(0, 10))).slice(0, 24); }
// A simple counter per key and window, kept in D1: returns false once the key is over its limit.
async function allow(env, key, max, ms) {
  const now = Date.now(), row = await env.DB.prepare('SELECT n, until FROM limits WHERE k = ?').bind(key).first();
  if (!row || row.until < now) { await env.DB.prepare('INSERT OR REPLACE INTO limits (k, n, until) VALUES (?, 1, ?)').bind(key, now + ms).run(); return true; }
  if (row.n >= max) return false;
  await env.DB.prepare('UPDATE limits SET n = n + 1 WHERE k = ?').bind(key).run();
  return true;
}

/* ---------- GitHub's signed tokens, for the replay checker and the admin workflow ---------- */
let jwksCache = null;
function b64u(s) { s = s.replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; const b = atob(s), a = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; }
async function github(req, env, workflow) {
  const m = /^Bearer ([\w-]+)\.([\w-]+)\.([\w-]+)$/.exec(req.headers.get('authorization') || '');
  if (!m) return null;
  try {
    const head = JSON.parse(new TextDecoder().decode(b64u(m[1]))), body = JSON.parse(new TextDecoder().decode(b64u(m[2]))), c = cfg(env);
    if (head.alg !== 'RS256') return null;
    if (!jwksCache || jwksCache.url !== c.jwks || jwksCache.at < Date.now() - 3600000 || !jwksCache.keys.some(k => k.kid === head.kid)) {
      const r = await fetch(c.jwks);
      if (!r.ok) return null;
      jwksCache = {url: c.jwks, at: Date.now(), keys: (await r.json()).keys || []};
    }
    const jwk = jwksCache.keys.find(k => k.kid === head.kid);
    if (!jwk) return null;
    const key = await crypto.subtle.importKey('jwk', {kty: jwk.kty, n: jwk.n, e: jwk.e, alg: 'RS256', ext: true}, {name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256'}, false, ['verify']);
    if (!await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, b64u(m[3]), new TextEncoder().encode(m[1] + '.' + m[2]))) return null;
    const now = Date.now() / 1000;
    if (body.iss !== 'https://token.actions.githubusercontent.com' || body.aud !== AUD || !(body.exp > now) || (body.nbf && body.nbf > now + 60)) return null;
    if (body.repository !== c.repo || body.ref !== 'refs/heads/main') return null;
    if (!String(body.workflow_ref || '').startsWith(c.repo + '/.github/workflows/' + workflow + '@')) return null;
    return body;
  } catch (e) { return null; }
}

/* ---------- entering and sending runs ---------- */
async function start(req, env) {
  const c = cfg(env), now = Date.now();
  if (now >= c.end) return fail(req, env, 410, 'The Silver Cup is over. Thanks for sailing!');
  let b;
  try { b = await req.json(); } catch (e) { return fail(req, env, 400, 'That entry didn’t come through. Try again.'); }
  if (c.ver && b.ver !== c.ver) return fail(req, env, 409, 'This page is out of date. Reload it to enter the latest version of the contest.');
  const handle = clean(b.handle, 24), email = clean(b.email, 120).toLowerCase(), crew = clean(b.crew, 30), hkey = fold(handle), ckey = fold(crew);
  if (hkey.length < 2) return fail(req, env, 400, 'Pick a captain name of at least two letters or numbers.');
  if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(email)) return fail(req, env, 400, 'That email doesn’t look right. It’s only used to reach you if you win.');
  if (b.adult !== true || b.rules !== true) return fail(req, env, 400, 'You need to be 21 or older and agree to the official rules to enter.');
  if (!await allow(env, 'start:' + await ipKey(req), c.perIp, DAY)) return fail(req, env, 429, 'That’s a lot of new runs from here today. Try again tomorrow.');
  const who = await env.DB.prepare('SELECT * FROM entrants WHERE hkey = ?').bind(hkey).first();
  if (who && who.email !== email) return fail(req, env, 409, 'That captain name is taken. Pick another, or use the email you entered it with.');
  if (who && who.dq) return fail(req, env, 403, 'This captain can’t enter the Silver Cup.');
  if (!await allow(env, 'run:' + hkey, c.perCaptain, DAY)) return fail(req, env, 429, 'That’s a lot of new runs for one captain today. Keep sailing the one you have.');
  if (!who) await env.DB.prepare('INSERT INTO entrants (hkey, handle, email, crew, ckey, created) VALUES (?, ?, ?, ?, ?, ?)').bind(hkey, handle, email, crew, ckey, now).run();
  else if (who.crew !== crew || who.handle !== handle) await env.DB.prepare('UPDATE entrants SET crew = ?, ckey = ?, handle = ? WHERE hkey = ?').bind(crew, ckey, handle, hkey).run();
  const id = randHex(12), key = randHex(16), seedA = new Uint32Array(1);
  crypto.getRandomValues(seedA);
  const seed = (seedA[0] % 2147483646) + 1, practice = now < c.start ? 1 : 0;
  await env.DB.prepare('INSERT INTO runs (id, hkey, seed, tok, practice, ver, started) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(id, hkey, seed, await sha(key), practice, c.ver, now).run();
  return json(req, env, {ok: true, run: {id, key, seed, practice: !!practice, ver: c.ver, at: now, handle, crew}, start: c.start, end: c.end});
}

async function runOf(req, env, id) {
  const run = await env.DB.prepare('SELECT r.*, e.dq, e.handle FROM runs r JOIN entrants e ON e.hkey = r.hkey WHERE r.id = ?').bind(String(id || '')).first();
  if (!run || run.tok !== await sha(req.headers.get('x-run-key') || '')) return null;
  return run;
}

async function submit(req, env) {
  const c = cfg(env), now = Date.now();
  const raw = new Uint8Array(await req.arrayBuffer());
  if (raw.length > c.maxBody) return fail(req, env, 413, 'This run is too long to send. Start a new one.');
  let text, gz;
  try {
    if (/x-pillage-gz/.test(req.headers.get('content-type') || '')) { gz = raw; text = new TextDecoder().decode(await gunzip(raw, 40e6)); }
    else { text = new TextDecoder().decode(raw); gz = await gzip(raw); }
  } catch (e) { return fail(req, env, 400, 'That run didn’t come through. Try again.'); }
  let sub;
  try { sub = JSON.parse(text); } catch (e) { return fail(req, env, 400, 'That run didn’t come through. Try again.'); }
  if (!sub || !sub.run || !Array.isArray(sub.segs) || !sub.segs.length) return fail(req, env, 400, 'That isn’t a contest run.');
  const run = await runOf(req, env, sub.run.id);
  if (!run) return fail(req, env, 403, 'This run’s key doesn’t match. It may be from another phone.');
  if (run.dq) return fail(req, env, 403, 'This captain can’t enter the Silver Cup.');
  if (sub.run.seed !== run.seed) return fail(req, env, 400, 'This run doesn’t match the one the server started.');
  if (now > c.end + c.grace) return fail(req, env, 410, 'The Silver Cup is over, and runs can’t be sent any more.');
  let steps = 0;
  for (const s of sub.segs) { if (!s || !Number.isInteger(s.n) || s.n < 0 || !Array.isArray(s.ev)) return fail(req, env, 400, 'That run is damaged.'); steps += s.n; }
  // Sixty steps make a second, and a phone can't play faster than the clock: more steps than time since the start is a forgery.
  // Play after the end doesn't count either, so the clock stops there.
  if (steps > (Math.min(now, c.end) - run.started) / 1000 * 60 * 1.01 + 600) return fail(req, env, 400, 'That run claims more time at sea than has passed.');
  const over = clean(sub.over, 12);
  if (!over && run.last_sub && now - run.last_sub < 40000) return fail(req, env, 429, 'Sent a moment ago. It’ll go again soon.');
  await env.DB.prepare('UPDATE subs SET status = ?, body = NULL WHERE run = ? AND status = ?').bind('superseded', run.id, 'pending').run();
  const claim = Math.max(0, Math.min(1e9, Math.round(+(sub.claim && sub.claim.xp) || 0)));
  const ins = await env.DB.prepare('INSERT INTO subs (run, at, steps, size, body, claim, over) VALUES (?, ?, ?, ?, ?, ?, ?)').bind(run.id, now, steps, gz.length, gz, claim, over).run();
  await env.DB.prepare('UPDATE runs SET last_sub = ? WHERE id = ?').bind(now, run.id).run();
  return json(req, env, {ok: true, sid: ins.meta && ins.meta.last_row_id, status: 'pending'});
}

async function runStatus(req, env, url) {
  const run = await runOf(req, env, url.searchParams.get('id'));
  if (!run) return fail(req, env, 403, 'This run’s key doesn’t match.');
  const last = await env.DB.prepare('SELECT id, at, status, xp, reason FROM subs WHERE run = ? AND status != ? ORDER BY id DESC LIMIT 1').bind(run.id, 'superseded').first();
  const best = await env.DB.prepare('SELECT MAX(xp) AS xp FROM subs WHERE run = ? AND status = ?').bind(run.id, 'ok').first();
  return json(req, env, {ok: true, practice: !!run.practice, last: last || null, best: best && best.xp != null ? best.xp : null});
}

/* ---------- the boards ---------- */
async function board(req, env, url) {
  const c = cfg(env), practice = url.searchParams.get('kind') === 'practice' ? 1 : 0;
  const rows = (await env.DB.prepare(
    'SELECT e.hkey, e.handle, e.crew, e.ckey, s.xp, s.level, s.day, s.stats, s.at FROM subs s JOIN runs r ON r.id = s.run JOIN entrants e ON e.hkey = r.hkey ' +
    'WHERE s.status = ? AND r.practice = ? AND e.dq = ? AND r.started >= ? ORDER BY s.xp DESC, s.at ASC LIMIT 4000'
  ).bind('ok', practice, '', practice ? 0 : c.start).all()).results || [];
  const seen = new Set(), captains = [];
  for (const r of rows) if (!seen.has(r.hkey)) { seen.add(r.hkey); captains.push(r); }
  const best = captains.map(r => ({name: r.handle, crew: r.crew, xp: r.xp, level: r.level, day: r.day, at: r.at, st: (() => { try { return JSON.parse(r.stats); } catch (e) { return {}; } })(), ck: r.ckey}));
  // A crew's score: its three best captains added up, so a big crew doesn't win on numbers alone.
  const crews = {};
  best.forEach(r => { if (!r.ck) return; const k = crews[r.ck] = crews[r.ck] || {name: r.crew, xp: 0, members: 0, top: []}; k.members++; if (k.top.length < 3) { k.top.push(r.name); k.xp += r.xp; } });
  const tallies = {};
  for (const r of best) for (const k in r.st) {
    if (!(r.st[k] > 0)) continue;
    (tallies[k] = tallies[k] || []).push({name: r.name, crew: r.crew, n: r.st[k], at: r.at});
  }
  for (const k in tallies) tallies[k] = tallies[k].sort((a, b) => b.n - a.n || a.at - b.at).slice(0, 10);
  const pending = await env.DB.prepare('SELECT COUNT(*) AS n FROM subs WHERE status = ?').bind('pending').first();
  return json(req, env, {ok: true, practice: !!practice, start: c.start, end: c.end, now: Date.now(),
    captains: best.slice(0, 100).map(r => ({name: r.name, crew: r.crew, xp: r.xp, level: r.level, day: r.day, at: r.at})),
    crews: Object.values(crews).sort((a, b) => b.xp - a.xp).slice(0, 30), tallies, checking: pending ? pending.n : 0}, 200, {'cache-control': 'public, max-age=20'});
}

/* ---------- the replay checker's side ---------- */
async function pending(req, env) {
  if (!await github(req, env, 'pillage-cup-check.yml')) return fail(req, env, 401, 'no');
  const rows = (await env.DB.prepare('SELECT s.id, s.run, s.at, s.steps, s.size, r.seed, r.practice, r.ver FROM subs s JOIN runs r ON r.id = s.run WHERE s.status = ? ORDER BY s.id LIMIT 25').bind('pending').all()).results || [];
  return json(req, env, {ok: true, subs: rows});
}
async function body(req, env, url) {
  if (!await github(req, env, 'pillage-cup-check.yml')) return fail(req, env, 401, 'no');
  const row = await env.DB.prepare('SELECT body FROM subs WHERE id = ?').bind(+url.searchParams.get('sid')).first();
  if (!row || !row.body) return fail(req, env, 404, 'gone');
  return new Response(row.body instanceof ArrayBuffer ? row.body : new Uint8Array(row.body), {headers: {'content-type': 'application/octet-stream', 'cache-control': 'no-store'}});
}
async function verdict(req, env) {
  if (!await github(req, env, 'pillage-cup-check.yml')) return fail(req, env, 401, 'no');
  const v = await req.json(), sid = +v.sid;
  const sub = await env.DB.prepare('SELECT id, run, status FROM subs WHERE id = ?').bind(sid).first();
  if (!sub) return fail(req, env, 404, 'gone');
  const stats = {};
  for (const k in (v.stats || {})) if (/^[a-z]{1,12}$/.test(k)) stats[k] = Math.max(0, Math.min(1e9, Math.floor(+v.stats[k]) || 0));
  await env.DB.prepare('UPDATE subs SET status = ?, xp = ?, level = ?, day = ?, stats = ?, reason = ?, checked = ? WHERE id = ?')
    .bind(v.ok ? 'ok' : v.broke ? 'error' : 'refused', Math.max(0, Math.round(+v.xp) || 0), Math.round(+v.level) || 0, Math.round(+v.day) || 0, JSON.stringify(stats), clean(v.reason, 200), Date.now(), sid).run();
  // Once a later send of a run checks out, the earlier ones' moves aren't needed: the later one holds them all.
  if (v.ok) await env.DB.prepare('UPDATE subs SET body = NULL WHERE run = ? AND id < ? AND status IN (?, ?)').bind(sub.run, sid, 'ok', 'refused').run();
  return json(req, env, {ok: true});
}
async function admin(req, env) {
  if (!await github(req, env, 'pillage-cup-admin.yml')) return fail(req, env, 401, 'no');
  const v = await req.json(), hkey = fold(v.handle || '');
  if (v.op === 'dq') {
    const r = await env.DB.prepare('UPDATE entrants SET dq = ? WHERE hkey = ?').bind(clean(v.reason || 'disqualified', 120), hkey).run();
    return json(req, env, {ok: true, changed: r.meta && r.meta.changes});
  }
  if (v.op === 'undq') {
    const r = await env.DB.prepare('UPDATE entrants SET dq = ? WHERE hkey = ?').bind('', hkey).run();
    return json(req, env, {ok: true, changed: r.meta && r.meta.changes});
  }
  if (v.op === 'purge') return json(req, env, {ok: true, changed: await purge(env, true)});
  if (v.op === 'recheck') {
    // Sends a captain's checked runs through the checker again (their moves are kept until a later send of the run checks out).
    const r = await env.DB.prepare('UPDATE subs SET status = ? WHERE status IN (?, ?, ?) AND body IS NOT NULL AND run IN (SELECT id FROM runs WHERE hkey = ?)').bind('pending', 'ok', 'refused', 'error', hkey).run();
    return json(req, env, {ok: true, changed: r.meta && r.meta.changes});
  }
  return fail(req, env, 400, 'unknown');
}

// Wipes every entrant's email: on its own once the purge date has passed (a daily cron), or early from the admin workflow.
export async function purge(env, now) {
  if (!now && Date.now() < cfg(env).purge) return 0;
  const r = await env.DB.prepare('UPDATE entrants SET email = ? WHERE email != ?').bind('', '').run();
  return (r.meta && r.meta.changes) || 0;
}

/* ---------- live ships ---------- */
// One room for the whole Caribbean. Each ship says where it is every couple of seconds; the room passes everyone's
// position on, no more than about once a second, and asks phones to slow down when it gets busy, to stay in the free plan.
export class Seas {
  constructor(ctx, env) { this.ctx = ctx; this.env = env; this.last = 0; }
  async fetch(req) {
    if (req.headers.get('upgrade') !== 'websocket') return new Response('websocket only', {status: 426});
    const pair = new WebSocketPair();
    this.ctx.acceptWebSocket(pair[1]);
    const id = randHex(4);
    pair[1].serializeAttachment({id, t: 0});
    pair[1].send(JSON.stringify({you: id, every: this.every()}));   // so a phone can leave its own ship out
    return new Response(null, {status: 101, webSocket: pair[0]});
  }
  every() { return Math.max(2000, this.ctx.getWebSockets().length * 120); }
  async webSocketMessage(ws, msg) {
    let m;
    try { m = JSON.parse(typeof msg === 'string' ? msg : new TextDecoder().decode(msg)); } catch (e) { return; }
    const a = ws.deserializeAttachment() || {}, now = Date.now();
    if (now - (a.t || 0) < 900) return;  // too chatty: ignored
    const ship = shipOf(m);
    if (!ship) return;
    ws.serializeAttachment(Object.assign(ship, {id: a.id, t: now}));
    if (now - this.last >= 1000) { this.last = now; this.cast(now); }
  }
  cast(now) {
    const all = this.ctx.getWebSockets(), ships = [];
    for (const s of all) { const a = s.deserializeAttachment(); if (a && a.t && now - a.t < 20000 && a.m) ships.push(a); }
    const msg = JSON.stringify({every: this.every(), ships});
    for (const s of all) { try { s.send(msg); } catch (e) { /* gone */ } }
  }
  async webSocketClose(ws) { try { ws.close(); } catch (e) { /* closed */ } }
  async webSocketError(ws) { try { ws.close(); } catch (e) { /* closed */ } }
}
// What a ship may share: its sea, where it is, its heading, its look and its captain's names. Nothing else.
export function shipOf(m) {
  if (!m || typeof m !== 'object' || !/^[a-z]{2,16}$/.test(m.m || '')) return null;
  const x = +m.x, y = +m.y, a = +m.a;
  if (!isFinite(x) || !isFinite(y) || Math.abs(x) > 20000 || Math.abs(y) > 20000) return null;
  return {m: m.m, x: Math.round(x), y: Math.round(y), a: isFinite(a) ? Math.round(a * 100) / 100 : 0,
    n: clean(m.n, 24), c: clean(m.c, 30), s: /^[a-z]{2,16}$/.test(m.s || '') ? m.s : 'canvas', f: /^[a-z]{2,16}$/.test(m.f || '') ? m.f : 'skull',
    l: Math.max(1, Math.min(20, Math.round(+m.l) || 1)), d: m.d ? 1 : 0};
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), p = url.pathname;
    if (req.method === 'OPTIONS') return new Response(null, {status: 204, headers: cors(req, env)});
    try {
      if (p === '/api/live') {
        const o = req.headers.get('origin') || '';
        if (!cfg(env).origins.includes(o)) return new Response('no', {status: 403});
        return env.SEAS.get(env.SEAS.idFromName('caribbean')).fetch(req);
      }
      if (p === '/api/start' && req.method === 'POST') return await start(req, env);
      if (p === '/api/submit' && req.method === 'POST') return await submit(req, env);
      if (p === '/api/board' && req.method === 'GET') return await board(req, env, url);
      if (p === '/api/run' && req.method === 'GET') return await runStatus(req, env, url);
      if (p === '/api/pending' && req.method === 'GET') return await pending(req, env);
      if (p === '/api/body' && req.method === 'GET') return await body(req, env, url);
      if (p === '/api/verdict' && req.method === 'POST') return await verdict(req, env);
      if (p === '/api/admin' && req.method === 'POST') return await admin(req, env);
      if (p === '/' || p === '/api') return json(req, env, {ok: true, name: 'Pillage the Reefer: the Silver Cup', start: cfg(env).start, end: cfg(env).end, ver: cfg(env).ver});
      return fail(req, env, 404, 'Not here.');
    } catch (e) {
      return fail(req, env, 500, 'Something went wrong on our side. Try again in a minute.');
    }
  },
  // Daily: drops the day-old entry counters (they hold only a scrambled, daily-changing form of an IP address), and wipes
  // the emails once the purge date has passed.
  async scheduled(event, env, ctx) {
    ctx.waitUntil(Promise.all([purge(env), env.DB.prepare('DELETE FROM limits WHERE until < ?').bind(Date.now()).run()]));
  }
};
