'use strict';
/* Silver Cup admin, run only by .github/workflows/pillage-cup-admin.yml, which GitHub lets only the repository's
   owners start. OP is dq (disqualify a captain, with a reason), undq, recheck (replay a captain's runs again) or purge
   (wipe every email now). It prints how many records changed and nothing about anyone. */
const {actionsToken, apiAddress} = require('./check.cjs');

(async () => {
  const api = apiAddress(), op = process.env.OP || '', handle = (process.env.HANDLE || '').trim(), reason = (process.env.REASON || '').trim();
  if (!api) throw new Error('The Cup server has no address yet (pillage/cup-api.js).');
  if (!['dq', 'undq', 'recheck', 'purge'].includes(op)) throw new Error('Pick dq, undq, recheck or purge.');
  if (op !== 'purge' && !handle) throw new Error('Give the captain name for ' + op + '.');
  const token = await actionsToken()();
  const r = await fetch(api + '/api/admin', {method: 'POST', headers: {authorization: 'Bearer ' + token, 'content-type': 'application/json'},
    body: JSON.stringify({op, handle, reason})});
  const out = await r.json();
  if (!out.ok) throw new Error('The server said no: ' + (out.error || r.status));
  console.log(op + (handle ? ' ' + handle : '') + ': ' + (out.changed || 0) + ' changed.');
})().catch(e => { console.error(e.message); process.exit(1); });
