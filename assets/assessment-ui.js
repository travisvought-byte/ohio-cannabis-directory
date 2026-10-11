const fields=[...document.querySelectorAll('select[data-weight]')], KEY='ohio-cannabis-assessment-v1';
const status=document.getElementById('save-status');
const value=(id,kind)=>document.querySelector('[data-'+kind+'="'+id+'"]').value;
const note=(id,kind)=>document.querySelector('[data-'+kind+'="'+id+'"]');
function snapshot(){return {version:1,saved_on:new Date().toISOString(),purpose:document.getElementById('purpose').value,assessment:qs.map(q=>({id:q.id,score:value(q.id,'id'),notes:value(q.id,'note'),owner:value(q.id,'owner'),due:value(q.id,'due'),action:value(q.id,'action')}))};}
function validate(data){
 if(!data||!Array.isArray(data.assessment)||!data.assessment.length||data.assessment.length>qs.length)throw Error('Choose a valid assessment export.');
 if(data.version!==undefined&&data.version!==1)throw Error('Unsupported assessment version.');
 const seen=new Set();for(const r of data.assessment){if(!r||!qs.some(q=>q.id===r.id)||seen.has(r.id))throw Error('Unknown or duplicate question ID.');seen.add(r.id);
 if(!['','0','1','2','3',0,1,2,3].includes(r.score))throw Error('Scores must be blank or 0-3.');
 for(const key of ['notes','owner','due','action'])if(r[key]!==undefined&&(typeof r[key]!=='string'||r[key].length>10000))throw Error('Invalid '+key+' field.');
 if(r.due && !/^\d{4}-\d{2}-\d{2}$/.test(r.due))throw Error('Invalid target date.');}
 return data;
}
function restore(data){validate(data);fields.forEach(e=>e.value='');document.querySelectorAll('[data-note],[data-owner],[data-due],[data-action]').forEach(e=>e.value='');
 for(const r of data.assessment){note(r.id,'id').value=String(r.score);for(const k of ['note','owner','due','action'])note(r.id,k).value=r[k==='note'?'notes':k]||'';}
 const purpose=document.getElementById('purpose');purpose.value=[...purpose.options].some(o=>o.value===data.purpose)?data.purpose:'internal';purpose.dispatchEvent(new Event('change'));calculate();
}
function element(tag,text){const e=document.createElement(tag);e.textContent=text;return e;}
function calculate(){
 const answered=fields.filter(e=>e.value!==''), weight=answered.reduce((s,e)=>s+Number(e.dataset.weight),0),points=answered.reduce((s,e)=>s+Number(e.value)/3*Number(e.dataset.weight),0);
 const pct=weight?100*points/weight:null,critical=answered.filter(e=>e.dataset.weight==='3'&&e.value==='0').length,complete=answered.length===fields.length;
 const rating=critical?'CRITICAL GAPS - Address before relying on readiness.':pct>=80?'GREEN - Strong readiness.':pct>=60?'YELLOW - Improvement needed.':'RED - Material gaps.';
 document.getElementById('score').textContent=answered.length+'/'+fields.length+' assessed. '+(pct===null?'No score yet.':(complete?'Weighted score: ':'Partial score (answered items only): ')+pct.toFixed(1)+'%. ')+(complete?rating:'Finish all questions before using an overall rating. ')+(critical?' '+critical+' critical zero-score gaps.':'');
 const domains=document.getElementById('domains');domains.replaceChildren();
 for(const d of [...new Set(qs.map(q=>q.domain))]){const group=qs.filter(q=>q.domain===d),a=group.filter(q=>value(q.id,'id')!==''),w=a.reduce((s,q)=>s+q.weight,0),n=a.reduce((s,q)=>s+Number(value(q.id,'id'))/3*q.weight,0);const li=element('li',d+': '+a.length+'/'+group.length+' assessed'+(w?' · '+(100*n/w).toFixed(1)+'%'+(a.length<group.length?' (partial)':''):''));const bar=element('div','');bar.className='domain-bar';bar.style.width=(w?100*n/w:0)+'%';li.append(bar);domains.append(li);}
 const gaps=qs.filter(q=>value(q.id,'id')!==''&&Number(value(q.id,'id'))<3).sort((a,b)=>{const priority=q=>q.weight===3&&value(q.id,'id')==='0'?0:value(q.id,'id')==='0'?1:q.weight===3?2:3;return priority(a)-priority(b)||a.id.localeCompare(b.id);});
 const list=document.getElementById('action-plan');list.replaceChildren();
 for(const q of gaps){const row=element('article','');row.append(element('h3',q.id+' · '+q.domain+' · '+(q.weight===3&&value(q.id,'id')==='0'?'Critical gap':'Needs improvement')));row.append(element('p',q.question));row.append(element('p','Gather / demonstrate: '+q.evidence));row.append(element('p','Owner: '+(value(q.id,'owner')||'Assign an owner')+' · Target: '+(value(q.id,'due')||'Set a date')));row.append(element('p','Next action: '+(value(q.id,'action')||'Document the gap, gather evidence and retest this control.')));const a=element('a','Edit this item');a.href='#question-'+q.id;row.append(a);list.append(row);}
 if(!gaps.length)list.append(element('p',complete?'No scored gaps. Package your evidence and arrange periodic review.':'Score questions to build your prioritized action plan. Unassessed items remain unknown.'));
 const checklist=document.getElementById('evidence-list');checklist.replaceChildren();qs.filter(q=>value(q.id,'id')!==''&&Number(value(q.id,'id'))<3).forEach(q=>checklist.append(element('li',q.id+': '+q.evidence)));
 document.querySelectorAll('.print-evidence').forEach(p=>{const id=p.dataset.question;p.textContent='Evidence / notes: '+(value(id,'note')||'None recorded')+'\nOwner: '+(value(id,'owner')||'Unassigned')+'\nTarget date: '+(value(id,'due')||'Not set')+'\nNext action: '+(value(id,'action')||'Not set');});
}
function changed(){calculate();status.textContent='Changes are in this page only. Save a draft or export before leaving.';}
document.getElementById('assessment-form').addEventListener('input',changed);fields.forEach(e=>e.addEventListener('change',changed));
document.getElementById('purpose').addEventListener('change',()=>{document.getElementById('purpose-help').textContent=({internal:'Review gaps with process owners and set a retest date.',banking:'Prepare ownership, licensing, business narrative and source-of-funds evidence. Confirm the chosen institution’s requirements.',financing:'Prioritize supportable financial records, ownership and capital documentation before investor or lender review.',startup:'Treat unbuilt controls as absent or unknown. Confirm which requirements apply to your planned license and business.'})[document.getElementById('purpose').value];status.textContent='Purpose changed. Save or export to keep it.';});
document.getElementById('save').onclick=()=>{try{localStorage.setItem(KEY,JSON.stringify(snapshot()));status.textContent='Draft saved on this browser. Reopen this page on the same device to resume. Shared-device users should clear it after use.';}catch(_){status.textContent='This browser cannot save locally. Export a file to keep your answers.';}};
document.getElementById('clear-draft').onclick=()=>{if(!window.confirm('Clear this browser draft and all current answers? Export first if you need a copy.'))return;try{localStorage.removeItem(KEY);localStorage.removeItem('ohio-business-assessment-v1');}catch(_){}restore({assessment:qs.map(q=>({id:q.id,score:''}))});status.textContent='Draft and current answers cleared.';};
document.getElementById('import').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>1000000)throw Error('File exceeds the 1 MB limit.');const data=validate(JSON.parse(await file.text()));restore(data);status.textContent='Answers restored. Save a draft to retain them on this browser.';if(window.directoryTrack)window.directoryTrack('assessment-import');}catch(err){status.textContent='Could not import: '+err.message+' Current answers were kept.';}finally{e.target.value='';}});
document.getElementById('export').onclick=()=>{const u=URL.createObjectURL(new Blob([JSON.stringify(snapshot(),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='my-business-assessment.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
document.getElementById('print').onclick=()=>{calculate();window.print();};
try{let saved=localStorage.getItem(KEY);if(!saved){const legacy=JSON.parse(localStorage.getItem('ohio-business-assessment-v1')||'null');if(Array.isArray(legacy))saved=JSON.stringify({assessment:legacy.map(r=>({id:r.id,score:r.score,notes:r.note||''}))});}if(saved){restore(JSON.parse(saved));status.textContent='Saved browser draft restored. Export for a separate backup.';}}catch(_){status.textContent='Saved draft unavailable. You can import an exported file.';}calculate();
