(function(){'use strict';
const byId=id=>document.getElementById(id),letter=byId('letter'),status=byId('status');
let selected=null,letterEdited=false;
const asks={lounges:'Create a licensing route for adult consumption lounges with age checks, ventilation, worker protections and impaired-driving safeguards.',outofstate:'Revisit Ohio restrictions and penalties involving cannabis legally purchased in another state, while recognizing that federal interstate restrictions require separate action.',accessories:'Provide clear protections for ordinary lawful-use accessories and practical transport standards.',clarity:'Review SB 56 restrictions for clarity, proportionality and their effects on adults, medical patients and small businesses.'};
const questions={lounges:'Will you support legislation authorizing licensed adult consumption lounges?',outofstate:'Will you support revisiting Ohio penalties involving cannabis legally purchased in another state?',accessories:'Will you support clear statutory protections for ordinary lawful-use accessories?',clarity:'Will you support a review of SB 56 restrictions for clarity, proportionality and practical effects?'};
const topics={lounges:'licensed consumption lounges',outofstate:'Ohio restrictions involving out-of-state purchases',accessories:'protections for ordinary lawful-use accessories',clarity:'clear and proportionate SB 56 rules'};
const value=(id,fallback)=>byId(id).value.trim()||fallback;
const priorities=()=>Array.from(document.querySelectorAll('input[name="priority"]:checked')).map(el=>el.value);
const intro=()=> 'I am '+(byId('connection').value==='constituent'?'a constituent':'an Ohio resident')+' in '+value('town','[Ohio town]')+'.';
function syncPrint(){byId('print-letter').textContent=letter.value;}
function buildScripts(){
 const chosen=priorities();if(!chosen.length){status.textContent='Choose at least one change to include. Your scripts were kept.';return;}
 byId('call-script').value='Hello, my name is '+value('sender','[Your name]')+'. '+intro()+' Who handles cannabis policy for '+value('recipient','this lawmaker')+'? I would like to discuss '+chosen.map(p=>topics[p]).join(' and ')+'. '+chosen.map(p=>questions[p]).join(' ')+' How can I receive a written response?';
 byId('followup-script').value='Dear '+value('recipient','Representative / Senator [Name]')+',\n\n'+intro()+' I wrote on '+value('sent-date','[date sent]')+' about '+chosen.map(p=>topics[p]).join(' and ')+'. Could you please update me on your position and any legislative action you plan to take? I would appreciate a written response.\n\nThank you,\n'+value('sender','[Your name]');
}
function build(){
 const chosen=priorities();if(!chosen.length){status.textContent='Choose at least one change to include. Your draft was kept.';return;}
 letter.value='Dear '+value('recipient','Representative / Senator [Name]')+',\n\n'+intro()+' I am asking you to support the following '+(chosen.length===1?'change':'changes')+' to Ohio’s cannabis laws:\n\n'+chosen.map((p,i)=>(i+1)+'. '+asks[p]).join('\n')+'\n\n'+value('reason','[Add a short personal reason here.]')+'\n\n'+chosen.map(p=>questions[p]).join('\n')+'\nPlease explain what action you will take. I would appreciate a written response.\n\nThank you,\n'+value('sender','[Your name]');
 letterEdited=false;syncPrint();buildScripts();status.textContent='Draft ready. Review and edit it before sending.';
}
async function copy(id){const field=byId(id);try{await navigator.clipboard.writeText(field.value);status.textContent='Text copied. Paste it into your notes, contact form or email.';}catch(error){field.focus();field.select();status.textContent='Your text is selected. Use your device’s Copy command.';}}
function download(content,filename,type){const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
['compose-fields','letter-actions','followup-actions','copy-call','copy-followup'].forEach(id=>byId(id).hidden=false);syncPrint();
byId('build').addEventListener('click',build);letter.addEventListener('input',()=>{letterEdited=true;syncPrint();});window.addEventListener('beforeprint',syncPrint);
byId('copy').addEventListener('click',()=>copy('letter'));byId('copy-call').addEventListener('click',()=>copy('call-script'));byId('copy-followup').addEventListener('click',()=>copy('followup-script'));
byId('download').addEventListener('click',()=>{download(letter.value,'ohio-cannabis-constituent-letter.txt','text/plain;charset=utf-8');status.textContent='Text download prepared.';});
byId('print').addEventListener('click',()=>{syncPrint();window.print();});byId('refresh-tools').addEventListener('click',()=>{buildScripts();if(priorities().length)status.textContent='Call and follow-up scripts rebuilt. Review your edits.';});
byId('sent-date').addEventListener('change',()=>{const raw=byId('sent-date').value;if(!raw){byId('followup-date').textContent='If you have not heard back after about two weeks, ask the office for an update.';return;}const date=new Date(raw+'T12:00:00Z');date.setUTCDate(date.getUTCDate()+14);byId('followup-date').textContent='Suggested follow-up: '+date.toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric',timeZone:'UTC'})+'.';});
byId('download-notes').addEventListener('click',()=>{const notes={member_id:selected?.id||null,recipient:byId('recipient').value,official_contact:selected?.contact_url||null,sent_date:byId('sent-date').value,suggested_followup:byId('followup-date').textContent,notes:byId('reply-notes').value,letter:letter.value,call_script:byId('call-script').value,followup_message:byId('followup-script').value};download(JSON.stringify(notes,null,2),'ohio-cannabis-followup-notes.json','application/json');status.textContent='Follow-up notes download prepared.';});
const id=new URLSearchParams(location.search).get('member');
if(id){fetch('data/legislators.json').then(r=>{if(!r.ok)throw new Error('Unavailable');return r.json();}).then(data=>{
 selected=data.members.find(m=>m.id===id&&!m.vacant);const target=byId('target-info');target.hidden=false;
 if(!selected){target.textContent='This link does not identify a current lawmaker. Choose a name from the roster.';return;}
 const name=(selected.chamber==='House'?'Representative ':'Senator ')+selected.name;
 if(!byId('recipient').value)byId('recipient').value=name;
 const title=document.createElement('p');title.textContent='Selected office: '+name+' · '+selected.chamber+' District '+selected.district+' · checked '+selected.checked_on+'.';target.append(title);
 const contact=document.createElement('a');contact.href=selected.contact_url;contact.className='button secondary';contact.textContent='Open this office’s contact form';contact.dataset.track='advocacy-selected-contact';target.append(contact);
 if(selected.phone){const phone=document.createElement('a');phone.href='tel:+1'+selected.phone.replace(/\D/g,'');phone.textContent='Call '+selected.phone;phone.className='button secondary';target.append(document.createTextNode(' '),phone);}
 const verify=document.createElement('p');verify.textContent='Confirm this office represents you before choosing “Constituent.” Otherwise you can write as an Ohio resident.';target.append(verify);
 if(!letterEdited)build();
 }).catch(()=>{const target=byId('target-info');target.hidden=false;target.textContent='The selected office could not load. Use the roster or official lookup and enter the name manually.';});}
})();
