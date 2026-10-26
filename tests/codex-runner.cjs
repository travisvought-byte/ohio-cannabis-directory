const assert = require('node:assert/strict');
const {eligible,linked,fileOK,notes,approval,prepare,deliver} = require('../scripts/codex_runner.cjs');
const owner='travisvought-byte';
const bot='directory-runner[bot]';
const issue={number:21,title:'Research banking',body:'Research only',state:'open',labels:[{name:'codex'},{name:'codex-execute'}],assignees:[]};
const authorize={id:100,updated_at:'2026-10-26',user:{login:owner},body:'/codex-run {"files":["data/research/banking.json"],"domains":["example.org"]}'};
const initial={issue,comments:[authorize],events:[{id:1,event:'labeled',label:{name:'codex-execute'},actor:{login:owner}}],prs:[],owner,repo:'ohio-cannabis-directory',runId:'9'};
const clone=x=>structuredClone(x);
const fingerprint=eligible(initial).fingerprint;
for(const mutate of [
  x=>x.issue.state='closed',
  x=>x.issue.pull_request={},
  x=>x.issue.assignees=[{login:'someone'}],
  x=>x.issue.labels.push({name:'claude'}),
  x=>x.issue.labels.pop(),
  x=>x.events[0].actor.login='another-collaborator',
  x=>x.events.push({event:'unlabeled',label:{name:'codex-execute'}}),
  x=>x.comments=[],
  x=>x.comments.push({id:200,user:{login:'codex'},body:'Claimed; working on this issue'}),
  x=>x.prs.push({body:'Closes travisvought-byte/ohio-cannabis-directory#21'}),
  x=>x.prs.push({head:{ref:'codex/21-automated-research'}})
]) {const x=clone(initial);mutate(x);assert.throws(()=>eligible(x));}
for(const value of [
  {files:['data/directory.json'],domains:[]},
  {files:['data/research/../secret.json'],domains:[]},
  {files:['data/research/a.json','data/research/a.json'],domains:[]},
  {files:['data/research/a.json'],domains:['*.example.org']},
  {files:['data/research/a.json'],domains:['example.org\n"*" = "allow"']},
  {files:['data/research/a.json'],domains:[],extra:true}
]) {assert.throws(()=>approval([{...authorize,body:'/codex-run '+JSON.stringify(value)}],owner));}
assert(!fileOK('data/research/a.py'));
assert.equal(notes('Closes #42; fixes owner/repo#3; @person'),'addresses #42; addresses owner/repo#3; ＠person');
assert(!linked({body:'Closes other/repo#21'},21,`${owner}/ohio-cannabis-directory`));
assert(!linked({body:'Closes #210'},21,`${owner}/ohio-cannabis-directory`));
for(const body of ['Closes #21',`https://github.com/${owner}/ohio-cannabis-directory/issues/21`,`${owner}/ohio-cannabis-directory#21`])assert(linked({body},21,`${owner}/ohio-cannabis-directory`));
const claim={id:101,user:{login:bot},body:'<!-- codex-runner:claim:9 -->\nCodex is working on this issue. Run: https://github.com/travisvought-byte/ohio-cannabis-directory/actions/runs/9'};
const claimed={...clone(initial),comments:[authorize,claim],claimId:101,botLogin:bot,expected:fingerprint};
assert.equal(eligible(claimed).fingerprint,fingerprint);
const changed=clone(claimed);changed.issue.body+=' changed';assert.throws(()=>eligible(changed));
const changedApproval=clone(claimed);changedApproval.comments[0].updated_at='edited';assert.throws(()=>eligible(changedApproval));
const changedClaim=clone(claimed);changedClaim.comments[1].body='edited';assert.throws(()=>eligible(changedClaim));
const released={...clone(initial),comments:[authorize,claim,{id:102,user:{login:owner},body:'/codex-release-comment 101'}]};
assert.throws(()=>eligible(released),/consumed/);
released.comments.push({...authorize,id:103});assert(eligible(released));

// Exercise actual controller sequencing with a mock paginated GitHub API.
(async()=>{
  const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'runner-controller-'));
  process.env.TASK_DIR=dir;process.env.RESULT_DIR=dir;process.env.ISSUE_NUMBER='21';
  const calls=[];let refExists=false;let nextComment=101;const comments=[clone(authorize)];
  const context={eventName:'workflow_dispatch',ref:'refs/heads/main',actor:owner,repo:{owner,repo:'ohio-cannabis-directory'},runId:9,sha:'a'.repeat(40)};
  const github={paginate:async(fn,args)=>{calls.push(['paginate',args.per_page]);return fn();},rest:{
    issues:{get:async()=>({data:issue}),listComments:()=>comments,listEvents:()=>initial.events,
      createComment:async({body})=>{const c={id:nextComment++,body,user:{login:bot}};comments.push(c);return {data:c};}},
    pulls:{list:()=>[],create:async(args)=>{calls.push(['create-pr',args]);return {data:{html_url:'https://github.com/example/pr/1'}};}},
    git:{getRef:async({ref})=>{if(ref!=='heads/main'&&!refExists){const e=new Error();e.status=404;throw e;}return {data:{object:{sha:context.sha}}};},
      getCommit:async()=>({data:{tree:{sha:'tree'}}}),createBlob:async()=>({data:{sha:'blob'}}),createTree:async()=>({data:{sha:'newtree'}}),createCommit:async()=>({data:{sha:'newcommit'}}),createRef:async()=>{calls.push(['branch']);refExists=true;}}
  }};
  const core={setOutput:(k,v)=>calls.push([k,v])};
  try {
    await prepare({github,context,core});
    const task=JSON.parse(fs.readFileSync(path.join(dir,'task.json')));
    assert.equal(task.claim_id,101);assert.equal(task.base_sha,context.sha);
    assert.equal(calls.filter(x=>x[0]==='paginate').length,3);
    fs.writeFileSync(path.join(dir,'bundle.json'),JSON.stringify({base_sha:context.sha,issue:21,run_id:'9',files:[{path:'data/research/banking.json',content:'[]'}],summary:'Reviewed sources',limitations:['Availability unknown']}));
    await deliver({github,context,core});
    assert(calls.find(x=>x[0]==='create-pr')[1].body.includes('Closes #21'));
    assert.equal(calls.filter(x=>x[0]==='create-pr').length,1);
    await assert.rejects(()=>prepare({github,context,core}));
    await assert.rejects(()=>prepare({github,context:{...context,actor:'someone'},core}));
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
  console.log('Codex controller eligibility, claim, delivery, duplicate and recovery tests passed');
})().catch(e=>{console.error(e);process.exit(1);});
