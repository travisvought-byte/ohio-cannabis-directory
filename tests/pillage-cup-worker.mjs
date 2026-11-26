// Silver Cup server: entering, sending runs, the checker's signed access, the boards and the live ships room.
// Runs the Worker itself in Node, with an in-memory SQLite database standing in for D1 and a made-up signing key
// standing in for GitHub's.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import zlib from 'node:zlib';
import {createRequire} from 'node:module';
import {DatabaseSync} from 'node:sqlite';
import {fileURLToPath, pathToFileURL} from 'node:url';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIR = path.join(ROOT, 'tools', 'pillage-contest');
const tmp = path.join(os.tmpdir(), 'pillage-worker-' + process.pid + '.mjs');
fs.copyFileSync(path.join(DIR, 'worker.js'), tmp);
const W = await import(pathToFileURL(tmp).href);
fs.unlinkSync(tmp);
const {boot} = require(path.join(DIR, 'verify.cjs'));
const {checkOnce} = require(path.join(DIR, 'check.cjs'));

// D1, as far as the Worker uses it.
function d1() {
  const db = new DatabaseSync(':memory:');
  db.exec(fs.readFileSync(path.join(DIR, 'schema.sql'), 'utf8'));
  return {db, prepare(sql) {
    let args = [];
    const st = {
      bind(...a) { args = a; return st; },
      async first() { return db.prepare(sql).get(...args) ?? null; },
      async all() { return {results: db.prepare(sql).all(...args)}; },
      async run() { const r = db.prepare(sql).run(...args); return {meta: {last_row_id: Number(r.lastInsertRowid), changes: Number(r.changes)}}; }
    };
    return st;
  }};
}

// A signing key standing in for GitHub's, and tokens signed with it.
const KEYS = await crypto.subtle.generateKey({name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256'}, true, ['sign', 'verify']);
const OTHER = await crypto.subtle.generateKey({name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256'}, true, ['sign', 'verify']);
const JWK = Object.assign(await crypto.subtle.exportKey('jwk', KEYS.publicKey), {kid: 'k1'});
const b64u = b => Buffer.from(b).toString('base64url');
const REPO = 'travisvought-byte/ohio-cannabis-directory';
async function token(over, key) {
  const now = Math.floor(Date.now() / 1000);
  const body = Object.assign({iss: 'https://token.actions.githubusercontent.com', aud: 'pillage-cup', exp: now + 300, nbf: now - 5, repository: REPO,
    ref: 'refs/heads/main', workflow_ref: REPO + '/.github/workflows/pillage-cup-check.yml@refs/heads/main'}, over || {});
  const head = b64u(JSON.stringify({alg: 'RS256', kid: 'k1'})), pay = b64u(JSON.stringify(body));
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', (key || KEYS).privateKey, new TextEncoder().encode(head + '.' + pay));
  return head + '.' + pay + '.' + b64u(sig);
}
const realFetch = globalThis.fetch;
globalThis.fetch = async (u, o) => String(u).includes('.well-known/jwks') ? new Response(JSON.stringify({keys: [JWK]})) : realFetch(u, o);

const ORIGIN = 'https://the-reefer.com';
function server(vars) {
  const env = Object.assign({DB: d1(), VER: 'cup1'}, vars);
  const call = async (method, p, body, headers) => {
    const h = Object.assign({origin: ORIGIN, 'cf-connecting-ip': '203.0.113.9'}, headers || {});
    let b = body;
    if (body && !(body instanceof Uint8Array) && typeof body !== 'string') { b = JSON.stringify(body); h['content-type'] = h['content-type'] || 'application/json'; }
    const r = await W.default.fetch(new Request('https://cup.example' + p, {method, headers: h, body: b}), env);
    const ct = r.headers.get('content-type') || '';
    return {status: r.status, headers: r.headers, data: ct.includes('json') ? await r.json() : new Uint8Array(await r.arrayBuffer())};
  };
  return {env, call, db: env.DB.db};
}
const entry = (o) => Object.assign({handle: 'Anne Bonny', email: 'anne@example.com', crew: 'Calico Crew', adult: true, rules: true, ver: 'cup1'}, o || {});

// A short honest run, played in the real game, for the run the server started.
function playRun(run, steps) {
  const env = boot({});
  const {P} = env;
  P.cup.start({id: run.id, seed: run.seed, practice: run.practice});
  for (let i = 1; i <= steps; i++) {
    if (i === 30) P.cup.input(['kd', 'ArrowUp']);
    if (i === 200) P.cup.input(['ku', 'ArrowUp']);
    P.cup.tick();
  }
  const sub = JSON.parse(JSON.stringify(P.cup.sub()));
  env.dom.window.close();
  return sub;
}

const H = Date.now();
{
  // ----- before the start: practice runs, kept off the prize board -----
  const S = server({START: new Date(H + 3600e3).toISOString(), END: new Date(H + 7200e3).toISOString()});
  let r = await S.call('GET', '/api');
  assert.equal(r.data.ok, true);
  r = await S.call('POST', '/api/start', entry());
  assert.equal(r.status, 200, JSON.stringify(r.data));
  assert.equal(r.data.run.practice, true, 'a run before the start is practice');
  assert.equal(r.headers.get('access-control-allow-origin'), ORIGIN, 'the site may call the server');
  const run = r.data.run;
  assert(Number.isInteger(run.seed) && run.seed > 0 && /^[0-9a-f]{32}$/.test(run.key), 'a seed and a key');
  assert.equal(S.db.prepare('SELECT tok FROM runs').get().tok.length, 64, 'only a hash of the key is kept');
  assert.notEqual(S.db.prepare('SELECT tok FROM runs').get().tok, run.key);

  // Entries the server turns away.
  for (const [bad, why] of [[{email: 'nope'}, 'email'], [{handle: '!'}, 'name'], [{adult: false}, '21'], [{rules: false}, 'rules'], [{ver: 'old'}, 'version']]) {
    r = await S.call('POST', '/api/start', entry(bad));
    assert(r.status >= 400 && r.data.ok === false, 'turned away: ' + why);
  }
  r = await S.call('POST', '/api/start', entry({handle: 'anne-bonny', email: 'someone@example.com'}));
  assert.equal(r.status, 409, 'a captain name belongs to the email that took it, however it is written');
  r = await S.call('POST', '/api/start', entry({handle: 'Anne <Bonny>', email: 'ANNE@example.com'}));
  assert.equal(r.status, 200, 'the same captain may start again');
  assert.deepEqual(S.db.prepare('SELECT handle FROM entrants').all().map(x => x.handle), ['Anne Bonny'], 'no markup is kept, and it is one captain');

  // Sending a run.
  const sub = playRun(run, 400);
  r = await S.call('POST', '/api/submit', JSON.stringify(sub), {'x-run-key': 'f'.repeat(32), 'content-type': 'application/json'});
  assert.equal(r.status, 403, 'another key can’t send the run');
  const wrongSeed = JSON.parse(JSON.stringify(sub)); wrongSeed.run.seed++;
  r = await S.call('POST', '/api/submit', JSON.stringify(wrongSeed), {'x-run-key': run.key, 'content-type': 'application/json'});
  assert.equal(r.status, 400, 'a run on a seed the server didn’t give is turned away');
  const tooLong = JSON.parse(JSON.stringify(sub)); tooLong.segs[0].n = 60 * 60 * 5;
  r = await S.call('POST', '/api/submit', JSON.stringify(tooLong), {'x-run-key': run.key, 'content-type': 'application/json'});
  assert.equal(r.status, 400, 'a run claiming five hours at sea a minute after it began is turned away');
  const gz = new Uint8Array(zlib.gzipSync(JSON.stringify(sub)));
  r = await S.call('POST', '/api/submit', gz, {'x-run-key': run.key, 'content-type': 'application/x-pillage-gz'});
  assert.equal(r.status, 200, JSON.stringify(r.data));
  assert.equal(r.data.status, 'pending');
  r = await S.call('POST', '/api/submit', gz, {'x-run-key': run.key, 'content-type': 'application/x-pillage-gz'});
  assert.equal(r.status, 429, 'sends of one run are spaced out');
  S.db.prepare('UPDATE runs SET last_sub = 0').run();
  const fake = JSON.parse(JSON.stringify(sub)); fake.claim = {xp: 999999};
  r = await S.call('POST', '/api/submit', JSON.stringify(fake), {'x-run-key': run.key, 'content-type': 'application/json'});
  assert.equal(r.status, 200);
  assert.deepEqual(S.db.prepare('SELECT status FROM subs ORDER BY id').all().map(x => x.status), ['superseded', 'pending'], 'a newer send replaces the waiting one');

  // The checker's side needs GitHub's signed token for the checker workflow, from this repository's main branch.
  r = await S.call('GET', '/api/pending');
  assert.equal(r.status, 401, 'nobody else can list the runs');
  for (const [over, why] of [[{aud: 'other'}, 'audience'], [{repository: 'someone/else'}, 'repository'], [{ref: 'refs/heads/feature'}, 'branch'],
    [{workflow_ref: REPO + '/.github/workflows/other.yml@refs/heads/main'}, 'workflow'], [{exp: Math.floor(H / 1000) - 10}, 'expired']]) {
    r = await S.call('GET', '/api/pending', null, {authorization: 'Bearer ' + await token(over)});
    assert.equal(r.status, 401, 'a token with the wrong ' + why + ' is refused');
  }
  r = await S.call('GET', '/api/pending', null, {authorization: 'Bearer ' + await token(null, OTHER)});
  assert.equal(r.status, 401, 'a token signed by another key is refused');
  r = await S.call('POST', '/api/admin', {op: 'dq', handle: 'Anne Bonny'}, {authorization: 'Bearer ' + await token()});
  assert.equal(r.status, 401, 'the checker’s token can’t disqualify anyone');

  // The checker replays the waiting run with the real game and reports the replay's own score, not the claim.
  const fetchW = (u, o) => {
    const url = new URL(u), h = Object.assign({}, (o && o.headers) || {});
    return W.default.fetch(new Request('https://cup.example' + url.pathname + url.search, {method: (o && o.method) || 'GET', headers: h, body: o && o.body}), S.env);
  };
  const n = await checkOnce({api: 'https://cup.example', token: () => token(), fetch: fetchW});
  assert.equal(n, 1, 'one run checked');
  const row = S.db.prepare("SELECT status, xp, reason FROM subs WHERE status != 'superseded'").get();
  assert.equal(row.status, 'ok', 'the honest run checks out: ' + row.reason);
  assert(row.xp < 1000, 'the claimed score was not used');
  r = await S.call('GET', '/api/board?kind=practice');
  assert.equal(r.data.captains.length, 1, 'it is on the practice board');
  assert.equal(r.data.captains[0].name, 'Anne Bonny');
  r = await S.call('GET', '/api/board');
  assert.equal(r.data.captains.length, 0, 'and not on the prize board');
  r = await S.call('GET', '/api/run?id=' + run.id, null, {'x-run-key': run.key});
  assert.equal(r.data.last.status, 'ok');
  assert.equal(r.data.practice, true);

  // A run changed after it was played doesn't check out.
  S.db.prepare('UPDATE runs SET last_sub = 0').run();
  const forged = JSON.parse(JSON.stringify(sub)); forged.segs[0].ev.push([forged.segs[0].n, 'kd', 'ArrowLeft']); forged.segs[0].h = 'x';
  r = await S.call('POST', '/api/submit', JSON.stringify(forged), {'x-run-key': run.key, 'content-type': 'application/json'});
  assert.equal(r.status, 200);
  await checkOnce({api: 'https://cup.example', token: () => token(), fetch: fetchW});
  assert.equal(S.db.prepare('SELECT status FROM subs ORDER BY id DESC').get().status, 'refused', 'a forged run is refused');
}

{
  // ----- during the contest: the prize board, crews, tallies, ties and disqualifying -----
  const S = server({START: new Date(H - 3600e3).toISOString(), END: new Date(H + 3600e3).toISOString(), LIMIT_RUNS: '2'});
  const runs = {};
  const people = [['Anne Bonny', 'anne@example.com', 'Calico Crew'], ['Mary Read', 'mary@example.com', 'calico crew'], ['Jack Rackham', 'jack@example.com', 'Calico Crew'],
    ['Ned Low', 'ned@example.com', 'Calico Crew'], ['Ben Hornigold', 'ben@example.com', ''], ['Sam Bellamy', 'sam@example.com', 'Whydah']];
  for (const [handle, email, crew] of people) {
    const r = await S.call('POST', '/api/start', entry({handle, email, crew}));
    assert.equal(r.status, 200);
    assert.equal(r.data.run.practice, false, 'a run after the start counts');
    runs[handle] = r.data.run;
  }
  let r = await S.call('POST', '/api/start', entry());
  assert.equal(r.status, 200);
  r = await S.call('POST', '/api/start', entry());
  assert.equal(r.status, 429, 'one captain can only start so many runs a day');
  // Verdicts as the checker would send them.
  const xp = {'Anne Bonny': 500, 'Mary Read': 700, 'Jack Rackham': 300, 'Ned Low': 900, 'Ben Hornigold': 700, 'Sam Bellamy': 100};
  let at = H - 1000;
  for (const [handle] of people) {
    S.db.prepare('INSERT INTO subs (run, at, steps, size, body, status, xp, level, day, stats) VALUES (?, ?, 1, 1, NULL, ?, ?, 2, 3, ?)')
      .run(runs[handle].id, handle === 'Mary Read' ? at - 5000 : at++, 'ok', xp[handle], JSON.stringify({sunk: xp[handle] / 100, days: 3}));
  }
  r = await S.call('GET', '/api/board');
  const names = r.data.captains.map(c => c.name);
  assert.deepEqual(names, ['Ned Low', 'Mary Read', 'Ben Hornigold', 'Anne Bonny', 'Jack Rackham', 'Sam Bellamy']);
  assert.equal(names.indexOf('Mary Read') < names.indexOf('Ben Hornigold'), true, 'a tie goes to the earlier verified run');
  assert.equal(r.data.crews[0].name, 'Calico Crew');
  assert.equal(r.data.crews[0].xp, 900 + 700 + 500, 'a crew scores its three best captains');
  assert.equal(r.data.crews[0].members, 4, 'a crew name matches however it is written');
  assert.equal(r.data.tallies.sunk[0].name, 'Ned Low');
  assert(!JSON.stringify(r.data).includes('@'), 'no email is ever shown');
  // Disqualifying, with the admin workflow's token only.
  const adm = {authorization: 'Bearer ' + await token({workflow_ref: REPO + '/.github/workflows/pillage-cup-admin.yml@refs/heads/main'})};
  r = await S.call('POST', '/api/admin', {op: 'dq', handle: 'ned low', reason: 'test'}, adm);
  assert.equal(r.data.changed, 1);
  r = await S.call('GET', '/api/board');
  assert.equal(r.data.captains[0].name, 'Mary Read', 'a disqualified captain leaves the board');
  r = await S.call('POST', '/api/start', entry({handle: 'Ned Low', email: 'ned@example.com'}));
  assert.equal(r.status, 403, 'and can’t start again');
  r = await S.call('POST', '/api/admin', {op: 'undq', handle: 'Ned Low'}, adm);
  r = await S.call('GET', '/api/board');
  assert.equal(r.data.captains[0].name, 'Ned Low', 'and comes back when that is undone');
  // Other sites can't call the server from a browser.
  r = await S.call('GET', '/api/board', null, {origin: 'https://evil.example'});
  assert.equal(r.headers.get('access-control-allow-origin'), null);
}

{
  // ----- after the end -----
  const S = server({START: new Date(H - 7200e3).toISOString(), END: new Date(H - 600e3).toISOString(), GRACE_MS: '300000'});
  let r = await S.call('POST', '/api/start', entry());
  assert.equal(r.status, 410, 'no new runs after the end');
  S.db.prepare("INSERT INTO entrants (hkey, handle, email, crew, ckey, created) VALUES ('annebonny', 'Anne Bonny', 'anne@example.com', '', '', 0)").run();
  S.db.prepare("INSERT INTO runs (id, hkey, seed, tok, practice, ver, started) VALUES ('r1', 'annebonny', 5, ?, 0, 'cup1', ?)").run(
    Buffer.from(await crypto.subtle.digest('SHA-256', new TextEncoder().encode('k'))).toString('hex'), H - 7000e3);
  r = await S.call('POST', '/api/submit', JSON.stringify({run: {id: 'r1', seed: 5}, segs: [{ev: [], n: 10, h: 'x'}]}), {'x-run-key': 'k', 'content-type': 'application/json'});
  assert.equal(r.status, 410, 'nor sends once the last few minutes have passed');
  // Emails are wiped by the daily cron, but only once the purge date has passed. Old entry counters go every day.
  S.db.prepare("INSERT INTO limits (k, n, until) VALUES ('old', 3, ?), ('new', 1, ?)").run(H - 1000, H + 864e5);
  const waits = [];
  await W.default.scheduled({}, S.env, {waitUntil(p) { waits.push(p); }});
  await Promise.all(waits);
  assert.equal(S.db.prepare('SELECT email FROM entrants').get().email, 'anne@example.com', 'kept until the purge date');
  assert.deepEqual(S.db.prepare('SELECT k FROM limits ORDER BY k').all().map(r => r.k).filter(k => k === 'old' || k === 'new'), ['new'], 'a day-old counter is dropped');
  const later = Object.assign({}, S.env, {PURGE: new Date(H - 1000).toISOString()});
  waits.length = 0;
  await W.default.scheduled({}, later, {waitUntil(p) { waits.push(p); }});
  await Promise.all(waits);
  assert.equal(S.db.prepare('SELECT email FROM entrants').get().email, '', 'and wiped after it');
}

{
  // ----- the live ships room -----
  const s = W.shipOf({m: 'windward', x: 10.6, y: -4, a: 1.234, n: 'Anne <script>', c: 'Calico', s: 'red', f: 'leaf', l: 4, extra: 'dropped'});
  assert.deepEqual(s, {m: 'windward', x: 11, y: -4, a: 1.23, n: 'Anne script', c: 'Calico', s: 'red', f: 'leaf', l: 4, d: 0});
  assert.equal(W.shipOf({m: 'windward', x: 1e9, y: 0}), null, 'a ship off the map is dropped');
  assert.equal(W.shipOf({m: '../x', x: 0, y: 0}), null);
  assert.equal(W.shipOf('nonsense'), null);
  // A room with two phones in it.
  const sockets = [], sent = [];
  const mk = (i) => { let att = null; return {i, serializeAttachment(a) { att = JSON.parse(JSON.stringify(a)); }, deserializeAttachment() { return att; }, send(m) { sent.push([i, JSON.parse(m)]); }, close() {}}; };
  const ctx = {acceptWebSocket(ws) { sockets.push(ws); }, getWebSockets() { return sockets; }};
  const room = new W.Seas(ctx, {});
  const a = mk(0), b = mk(1);
  room.ctx.acceptWebSocket(a); a.serializeAttachment({id: 'a', t: 0});
  room.ctx.acceptWebSocket(b); b.serializeAttachment({id: 'b', t: 0});
  await room.webSocketMessage(a, JSON.stringify({m: 'windward', x: 100, y: 200, a: 0, n: 'Anne', c: 'Calico', l: 2}));
  assert.equal(sent.length, 2, 'both phones hear where Anne is');
  assert.equal(sent[1][1].ships[0].n, 'Anne');
  assert(sent[1][1].every >= 2000, 'and how often to say where they are');
  await room.webSocketMessage(a, JSON.stringify({m: 'windward', x: 101, y: 200}));
  assert.equal(sent.length, 2, 'a phone that talks too often is ignored');
  assert.equal(room.every(), 2000);
}

globalThis.fetch = realFetch;
console.log('pillage cup server ok');
