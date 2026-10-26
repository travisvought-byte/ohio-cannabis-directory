/* Trusted controller: run only from the immutable main checkout, never agent output. */
const fs = require('node:fs');
const crypto = require('node:crypto');
const digest = value => crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');
const fail = message => { throw new Error(message); };
const fileOK = p => typeof p === 'string' && /^data\/research\/[A-Za-z0-9][A-Za-z0-9._-]*\.(json|md)$/.test(p) && !p.includes('..');
// Model notes cannot add closing directives for other issues or notify accounts.
const notes = s => s.replace(/@/g,'＠').replace(/\b(?:close[sd]?|fix(?:es|ed)?|resolve[sd]?)\b/gi,'addresses');

function approval(comments, owner) {
  const candidates = comments.filter(c => c.user.login.toLowerCase() === owner.toLowerCase() && c.body.startsWith('/codex-run '));
  if (!candidates.length) fail('Missing owner /codex-run authorization');
  const c = candidates.at(-1);
  const p = JSON.parse(c.body.slice('/codex-run '.length));
  if (Object.keys(p).sort().join(',') !== 'domains,files' || !Array.isArray(p.files) || !p.files.length || p.files.length > 3 || new Set(p.files).size !== p.files.length || !p.files.every(fileOK)) fail('Authorization must name 1–3 exact research JSON/Markdown paths and domains');
  if (!Array.isArray(p.domains) || p.domains.length > 20 || !p.domains.every(d => typeof d === 'string' && /^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$/.test(d))) fail('Use exact public DNS hostnames, at most 20');
  return {id:c.id, updated_at:c.updated_at, files:p.files, domains:p.domains};
}

function linked(pr, n, fullName) {
  const escaped = fullName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`(?<![\\w/-])#${n}\\b|https://github\\.com/${escaped}/issues/${n}\\b|${escaped}#${n}\\b`, 'i').test(`${pr.title || ''}\n${pr.body || ''}`);
}

function eligible({issue,comments,events,prs,owner,repo,runId,claimId=null,botLogin=null,expected=null}) {
  if (issue.state !== 'open' || issue.pull_request || issue.assignees?.length) fail('Issue must be open, unassigned and not a PR');
  const labels = issue.labels.map(l => typeof l === 'string' ? l : l.name);
  if (!['codex','codex-execute'].every(l => labels.includes(l)) || labels.includes('claude')) fail('Issue needs codex + codex-execute, with no Claude lane');
  const labelEvent = events.filter(e => ['labeled','unlabeled'].includes(e.event) && e.label?.name === 'codex-execute').at(-1);
  if (labelEvent?.event !== 'labeled' || labelEvent.actor?.login?.toLowerCase() !== owner.toLowerCase()) fail('Owner must apply execution label');
  if (prs.some(p => linked(p,issue.number,`${owner}/${repo}`) || p.head?.ref === `codex/${issue.number}-automated-research`)) fail('Issue already has an open PR');
  const auth = approval(comments,owner);
  if (!claimId && comments.some(c => c.id > auth.id && c.body.startsWith('<!-- codex-runner:claim:'))) fail('Authorization already consumed; post a fresh approval after reviewing the previous run');
  const allowed = new Set([auth.id]);
  // Any previous discussion/claim requires explicit owner acknowledgement by comment ID.
  // No free-text claim classifier can safely establish that another agent is idle.
  for (const c of comments) {
    if (c.user.login.toLowerCase() === owner.toLowerCase() && /^\/codex-release-comment [1-9][0-9]*$/.test(c.body)) {
      allowed.add(c.id); allowed.add(Number(c.body.split(' ')[1]));
    }
    if (c.user.login.toLowerCase() === owner.toLowerCase() && c.body.startsWith('/codex-run ') && c.id !== auth.id) allowed.add(c.id);
  }
  if (claimId) {
    const claim = comments.find(c => c.id === claimId);
    if (!claim || claim.user.login !== botLogin || claim.body !== `<!-- codex-runner:claim:${runId} -->\nCodex is working on this issue. Run: https://github.com/${owner}/${repo}/actions/runs/${runId}`) fail('Runner claim changed or disappeared');
    allowed.add(claimId);
  }
  for (const c of comments) if (!allowed.has(c.id)) fail(`Unresolved discussion/claim comment ${c.id}; owner must review it explicitly`);
  const state = {number:issue.number,title:issue.title,body:issue.body || '',auth,label_event:labelEvent.id};
  if (expected && digest(state) !== expected) fail('Issue or authorization changed during execution');
  return {state, fingerprint:digest(state)};
}

async function snapshot(github,context,n,extra={}) {
  const {owner,repo} = context.repo;
  const [issue,comments,events,prs] = await Promise.all([
    github.rest.issues.get({owner,repo,issue_number:n}).then(r=>r.data),
    github.paginate(github.rest.issues.listComments,{owner,repo,issue_number:n,per_page:100}),
    github.paginate(github.rest.issues.listEvents,{owner,repo,issue_number:n,per_page:100}),
    github.paginate(github.rest.pulls.list,{owner,repo,state:'open',per_page:100})
  ]);
  return eligible({issue,comments,events,prs,owner,repo,runId:String(context.runId),...extra});
}

async function prepare({github,context,core}) {
  if (context.eventName !== 'workflow_dispatch' || context.ref !== 'refs/heads/main' || context.actor.toLowerCase() !== context.repo.owner.toLowerCase()) fail('Only owner dispatch on main is allowed');
  const raw = process.env.ISSUE_NUMBER || '';
  if (!/^[1-9][0-9]*$/.test(raw)) fail('Invalid issue number');
  const n = Number(raw);
  if (!Number.isSafeInteger(n)) fail('Issue number is out of range');
  const s = await snapshot(github,context,n);
  const base = (await github.rest.git.getRef({...context.repo,ref:'heads/main'})).data.object.sha;
  if (base !== context.sha) fail('Main advanced since dispatch; start a fresh run');
  const branch = `codex/${n}-automated-research`;
  try { await github.rest.git.getRef({...context.repo,ref:`heads/${branch}`}); fail('Branch already exists; inspect recovery instructions'); }
  catch(e) { if (e.status !== 404) throw e; }
  const body = `<!-- codex-runner:claim:${context.runId} -->\nCodex is working on this issue. Run: https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`;
  const claim = (await github.rest.issues.createComment({...context.repo,issue_number:n,body})).data;
  const task = {schema_version:1,issue:n,run_id:String(context.runId),base_sha:base,branch,claim_id:claim.id,bot_login:claim.user.login,fingerprint:s.fingerprint,...s.state};
  fs.mkdirSync(process.env.TASK_DIR,{recursive:true});
  fs.writeFileSync(`${process.env.TASK_DIR}/task.json`,JSON.stringify(task,null,2));
  core.setOutput('base',base); core.setOutput('issue',n); core.setOutput('claim',claim.id);
}

async function deliver({github,context,core}) {
  const task = JSON.parse(fs.readFileSync(`${process.env.TASK_DIR}/task.json`));
  const bundle = JSON.parse(fs.readFileSync(`${process.env.RESULT_DIR}/bundle.json`));
  await snapshot(github,context,task.issue,{claimId:task.claim_id,botLogin:task.bot_login,expected:task.fingerprint});
  const base = (await github.rest.git.getRef({...context.repo,ref:'heads/main'})).data.object.sha;
  if (base !== task.base_sha) fail('Main advanced; re-authorize a fresh run');
  // Independent Python guard already checked this same immutable artifact in this job.
  if (bundle.base_sha !== base || bundle.issue !== task.issue || bundle.run_id !== String(context.runId)) fail('Wrong artifact identity');
  const tree = (await github.rest.git.getCommit({...context.repo,commit_sha:base})).data.tree.sha;
  const entries = [];
  for (const f of bundle.files) {
    if (!task.auth.files.includes(f.path) || !fileOK(f.path)) fail('Unexpected delivery path');
    const blob = (await github.rest.git.createBlob({...context.repo,content:Buffer.from(f.content).toString('base64'),encoding:'base64'})).data;
    entries.push({path:f.path,mode:'100644',type:'blob',sha:blob.sha});
  }
  const newTree = (await github.rest.git.createTree({...context.repo,base_tree:tree,tree:entries})).data.sha;
  const commit = (await github.rest.git.createCommit({...context.repo,message:`Research for #${task.issue}`,tree:newTree,parents:[base]})).data.sha;
  await github.rest.git.createRef({...context.repo,ref:`refs/heads/${task.branch}`,sha:commit});
  const pr = (await github.rest.pulls.create({...context.repo,base:'main',head:task.branch,title:`Research for #${task.issue}`,body:`Closes #${task.issue}\n\nPrepared by the opt-in research runner. Owner review is required; no merge is performed.\n\nValidation: all repository checks in the independent validation job passed. [Run evidence](https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}). Required PR checks must also run and pass.\n\nModel report (untrusted research notes; mentions and closing directives normalized):\n\n${notes(bundle.summary)}\n\nLimitations:\n${bundle.limitations.map(x=>'- '+notes(x)).join('\n') || '- No additional limitations reported by the model; verify the sources during review.'}`.slice(0,60000)})).data;
  await github.rest.issues.createComment({...context.repo,issue_number:task.issue,body:`Runner completed: ${pr.html_url}. Owner review and PR checks are still required.`});
  core.setOutput('pr',pr.html_url);
}

async function finish({github,context}) {
  const raw = process.env.ISSUE_NUMBER || '';
  if (!/^[1-9][0-9]*$/.test(raw)) return;
  await github.rest.issues.createComment({...context.repo,issue_number:Number(raw),body:`<!-- codex-runner:finished:${context.runId} -->\nRunner finished with status: ${process.env.RUN_STATUS}. Inspect https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}. Before retrying, review this run, any branch/PR, and explicitly acknowledge its claim/report comments with /codex-release-comment COMMENT_ID; then post a fresh /codex-run authorization. A failed or blocked run does not establish fresh source verification.`});
}

module.exports = {fileOK,notes,approval,linked,eligible,prepare,deliver,finish};
