const assert=require('node:assert/strict'),fs=require('node:fs');
const yaml=fs.readFileSync('.github/workflows/pr-risk-report.yml','utf8');
const script=yaml.split('          script: |\n')[1].split('\n').map(l=>l.startsWith('            ')?l.slice(12):l).join('\n');
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
async function assess(options={}){
 const files=options.files??[{filename:'docs/README.md',status:'modified',changes:2,patch:'@@\n-old\n+new',sha:'new-blob'}];
 const pr={state:'open',draft:false,changed_files:files.length,base:{ref:'main',sha:'base'},head:{sha:'head',repo:{full_name:'owner/repo'}},...options.pr};
 const calls=[],summaries=[];let result;
 const github={rest:{pulls:{get:async()=>({data:pr}),listFiles:()=>{}},git:{getCommit:async({commit_sha})=>{calls.push(commit_sha);if(options.apiError)throw Error('API unavailable');return {data:{tree:{sha:commit_sha+'-tree'}}};},getTree:async({tree_sha})=>({data:{truncated:!!options.truncated,tree:files.map(f=>({path:f.filename,type:options.type??'blob',mode:tree_sha==='base-tree'?(options.baseMode??'100644'):(options.mode??'100644'),sha:tree_sha==='base-tree'?'old-blob':(options.blob??f.sha)})).filter(()=>!options.missing)}})}},paginate:async()=>files};
 const summary={addHeading(){return this},addRaw(s){summaries.push(s);return this},async write(){}};
 await new AsyncFunction('github','context','core',script)(github,{repo:{owner:'owner',repo:'repo'},issue:{number:9}},{summary,info:s=>result=JSON.parse(s)});
 return {result,calls,summary:summaries.join('')};
}
(async()=>{
 assert((await assess()).result.eligible);
 for(const mode of ['100755','120000','160000','040000'])assert(!(await assess({mode})).result.eligible,mode);
 assert(!(await assess({baseMode:'120000'})).result.eligible);
 assert(!(await assess({missing:true})).result.eligible);
 assert(!(await assess({truncated:true})).result.eligible);
 assert(!(await assess({blob:'changed-after-listing'})).result.eligible);
 assert(!(await assess({pr:{changed_files:3}})).result.eligible);
 assert(!(await assess({pr:{draft:true}})).result.eligible);
 assert(!(await assess({pr:{state:'closed'}})).result.eligible);
 assert(!(await assess({pr:{base:{ref:'other',sha:'base'}}})).result.eligible);
 for(const repo of [null,{full_name:'external/fork'}]){const r=await assess({pr:{head:{repo,sha:'head'}}});assert(!r.result.eligible);assert.equal(r.calls.length,0);}
 for(const edit of [{changes:undefined},{changes:-1},{changes:51},{changes:'2'},{patch:undefined},{patch:''},{status:'added'},{status:'removed'},{previous_filename:'old.md'}]){
  assert(!(await assess({files:[{filename:'docs/README.md',status:'modified',changes:2,patch:'@@',sha:'new-blob',...edit}]})).result.eligible);
 }
 assert(!(await assess({files:[]})).result.eligible);
 const malicious=await assess({files:[{filename:'docs/README.md\n<script>bad</script>',status:'modified',changes:2,patch:'@@',sha:'new-blob'}]});
 assert(!malicious.result.eligible);assert(!malicious.summary.includes('<script>'));assert(malicious.summary.includes('&lt;script&gt;'));
 await assert.rejects(()=>assess({apiError:true}),/API unavailable/);
 assert(!/pull_request_target/.test(yaml));assert(!/:\s*write\b/.test(yaml));
 console.log('PASS risk report: complete files, immutable blob identities, symlink/executable modes, missing metadata, fork isolation and report-only permissions.');
})().catch(e=>{console.error(e);process.exit(1)});
