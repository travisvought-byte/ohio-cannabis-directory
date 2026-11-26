'use strict';
/* Silver Cup checker: takes the runs waiting on the server, replays each one (verify.cjs) and sends back what the
   replay made of it. Run by .github/workflows/pillage-cup-check.yml, which proves to the server who it is with a token
   GitHub signs for that workflow alone. A run is replayed with the game exactly as it stood when the contest froze (the
   git tag pillage-<version>), so a later change to the game can't change anyone's score.
   Usage: node check.cjs [--for SECONDS]   (the server's address comes from pillage/cup-api.js, or PILLAGE_API) */
const zlib = require('zlib'), path = require('path'), {execFileSync} = require('child_process');
const {verify} = require('./verify.cjs');

const GAME_FILES = ['index.html', 'coasts.js', 'data.js', 'engine.js', 'events.js', 'qr.js', 'game.js'];
const frozen = {};
// The game's files at the contest's version, from its git tag; with no tag yet (practice), the files as they are.
function filesFor(ver) {
  if (!ver) return undefined;
  if (frozen[ver] !== undefined) return frozen[ver] || undefined;
  const root = path.join(__dirname, '..', '..');
  try {
    const files = {};
    for (const f of GAME_FILES) files[f] = execFileSync('git', ['show', 'pillage-' + ver + ':pillage/' + f], {cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 64e6});
    frozen[ver] = files;
  } catch (e) { frozen[ver] = null; }
  return frozen[ver] || undefined;
}

// One pass: every run waiting, replayed and answered. Returns how many were checked.
async function checkOnce({api, token, fetch, files, log}) {
  log = log || (() => {});
  files = files || filesFor;
  const auth = async extra => Object.assign({authorization: 'Bearer ' + await token()}, extra || {});
  const r = await fetch(api + '/api/pending', {headers: await auth()});
  const list = await r.json();
  if (!list.ok) throw new Error('the server would not list the runs: ' + (list.error || r.status));
  let n = 0;
  for (const s of list.subs) {
    const b = await fetch(api + '/api/body?sid=' + s.id, {headers: await auth()});
    if (b.status === 404) continue;   // replaced by a newer send in the meantime
    let res;
    try {
      const sub = JSON.parse(zlib.gunzipSync(Buffer.from(await b.arrayBuffer()), {maxOutputLength: 40e6}).toString('utf8'));
      if (!sub || !sub.run || sub.run.seed !== s.seed || sub.run.id !== s.run) res = {ok: false, reason: 'not the run the server started'};
      else res = verify(sub, {files: files(s.ver)});
    } catch (e) { res = {ok: false, reason: 'the run could not be read'}; }
    log((res.ok ? 'ok ' : 'refused ') + s.id + ' xp ' + (res.xp || 0) + (res.reason ? ' (' + res.reason + ')' : ''));
    const v = await fetch(api + '/api/verdict', {method: 'POST', headers: await auth({'content-type': 'application/json'}),
      body: JSON.stringify({sid: s.id, ok: !!res.ok, broke: !!res.broke, xp: res.xp || 0, level: res.level || 0, day: res.day || 0, stats: res.stats || {}, reason: res.reason || ''})});
    if (!(await v.json()).ok) throw new Error('the server would not take a verdict');
    n++;
  }
  return n;
}

// GitHub Actions: a fresh signed token for the server every few minutes (they don't last long).
function actionsToken() {
  let tok = '', at = 0;
  return async () => {
    if (tok && Date.now() - at < 180000) return tok;
    const u = process.env.ACTIONS_ID_TOKEN_REQUEST_URL, k = process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN;
    if (!u || !k) throw new Error('no GitHub token: run this from the workflow, which has id-token: write');
    const r = await fetch(u + '&audience=pillage-cup', {headers: {authorization: 'bearer ' + k}});
    tok = (await r.json()).value; at = Date.now();
    return tok;
  };
}

// The Cup server's address: PILLAGE_API if set, otherwise the one the game uses (pillage/cup-api.js).
function apiAddress() {
  let api = process.env.PILLAGE_API || '';
  if (!api) {
    try { api = (/PILLAGE_CUP_API\s*=\s*'([^']*)'/.exec(require('fs').readFileSync(path.join(__dirname, '..', '..', 'pillage', 'cup-api.js'), 'utf8')) || [])[1] || ''; } catch (e) { api = ''; }
  }
  return api.replace(/\/+$/, '');
}

module.exports = {checkOnce, filesFor, actionsToken, apiAddress};

if (require.main === module) {
  (async () => {
    const api = apiAddress(), i = process.argv.indexOf('--for');
    if (!api) { console.log('The Cup server has no address yet (pillage/cup-api.js): nothing to check.'); return; }
    const until = Date.now() + (i > 0 ? +process.argv[i + 1] : 0) * 1000, token = actionsToken();
    for (;;) {
      const n = await checkOnce({api, token, fetch, log: m => console.log(m)});
      if (Date.now() >= until) break;
      if (!n) await new Promise(r => setTimeout(r, 20000));
    }
  })().catch(e => { console.error(e.message); process.exit(1); });
}
