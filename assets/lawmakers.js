(async function(){'use strict';
const byId=id=>document.getElementById(id),params=new URLSearchParams(location.search),size=12;
let data,events,results=[],page=0;
const fields={q:'member-search',chamber:'chamber',party:'party',vote:'vote',role:'role'};
const element=(tag,text,cls)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;};
const link=(label,url,cls)=>{const el=element('a',label,cls);el.href=url;return el;};
const dateLabel=s=>new Date(s+'T12:00:00Z').toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric',timeZone:'UTC'});
function finalVote(member){return member.votes.find(v=>events.get(v.event_id).is_final_agreement);}
function card(member){
 const article=element('article');article.id=member.id;
 article.append(element('h3',member.vacant?'Vacant seat':member.name));
 article.append(element('p',member.chamber+' District '+member.district+(member.party?' · '+member.party:'')));
 if(member.vacant){article.append(element('p','Vacant in the official directory as of '+member.checked_on+'.'));article.append(link('Check the official directory',member.directory_source));return article;}
 if(member.roles.length){const roles=element('div',undefined,'roles');member.roles.forEach(r=>{const p=element('p');p.append(link(r.label,r.source));roles.append(p);});article.append(roles);}
 const final=finalVote(member),event=data.vote_events.find(e=>e.chamber===member.chamber&&e.is_final_agreement),vote=element('div',undefined,'vote');
 vote.append(element('p','Final SB 56 agreement: '+(final?final.vote:'No recorded yea/nay'),'vote-label'));
 const source=element('p',undefined,'review');source.append(link(dateLabel(event.date)+' · Conference report',event.source));vote.append(source);article.append(vote);
 const history=member.votes.filter(v=>!events.get(v.event_id).is_final_agreement);
 if(history.length){const details=element('details'),list=element('ul',undefined,'vote-history');details.append(element('summary','Other SB 56 votes ('+history.length+')'));history.forEach(v=>{const e=events.get(v.event_id),li=element('li');li.append(link(dateLabel(e.date)+' · '+e.stage+' · '+v.vote,e.source));list.append(li);});details.append(list);article.append(details);}
 const actions=element('div',undefined,'actions'),write=link('Write to this lawmaker','advocacy.html?member='+member.id+'#write','button');write.dataset.track='lawmakers-start-letter';actions.append(write,link('Official contact',member.contact_url,'button secondary'));article.append(actions);
 const contact=element('p');if(member.phone)contact.append(link('Call '+member.phone,'tel:+1'+member.phone.replace(/\D/g,'')),document.createTextNode(' · '));contact.append(link('Profile',member.profile_url),document.createTextNode(' · '),link('Share this listing','lawmakers.html#'+member.id));article.append(contact);
 if(member.contact_note)article.append(element('p',member.contact_note,'review'));
 article.append(element('p','Contact and roster checked '+member.checked_on,'review'));return article;
}
function render(){
 const start=page*size,visible=results.slice(start,start+size),root=byId('member-results');root.replaceChildren(...visible.map(card));
 byId('roster-count').textContent=results.length?results.length+' matching districts · showing '+(start+1)+'–'+(start+visible.length):'No matching lawmakers. Try a name or reset the filters.';
 byId('pager').hidden=results.length<=size;byId('previous').disabled=page===0;byId('next').disabled=start+size>=results.length;byId('page-position').textContent='Page '+(page+1)+' of '+Math.max(1,Math.ceil(results.length/size));
}
function filter(updateUrl=true){
 const query=byId('member-search').value.toLowerCase().trim().split(/\s+/).filter(Boolean),chamber=byId('chamber').value,party=byId('party').value,vote=byId('vote').value,role=byId('role').value;
 results=data.members.filter(m=>{const search=(m.name+' '+m.chamber+' District '+m.district+' '+(m.party||'')+' '+m.roles.map(r=>r.label).join(' ')).toLowerCase();return query.every(q=>search.includes(q))&&(!chamber||m.chamber===chamber)&&(!party||m.party===party)&&(!role||m.roles.some(r=>role==='leadership'?r.source.includes('/members/'):r.label.startsWith(role)))&&(!vote||(vote==='vacant'?m.vacant:!m.vacant&&(vote==='unrecorded'?!finalVote(m):finalVote(m)?.vote===vote)));});
 page=0;render();
 if(updateUrl){const url=new URL(location.href);for(const [key,id]of Object.entries(fields)){const value=byId(id).value;if(value)url.searchParams.set(key,value);else url.searchParams.delete(key);}url.hash='';history.replaceState(null,'',url);}
}
function showHash(){const id=location.hash.slice(1),member=data.members.find(m=>m.id===id);if(member){results=[member];page=0;render();byId(id).scrollIntoView({block:'nearest'});}else filter(false);}
try{
 const response=await fetch('data/legislators.json');if(!response.ok)throw new Error('Roster unavailable');data=await response.json();events=new Map(data.vote_events.map(e=>[e.id,e]));
 for(const [key,id]of Object.entries(fields)){const field=byId(id),value=params.get(key)||'';if(field.tagName==='INPUT'||Array.from(field.options).some(o=>o.value===value))field.value=value;field.addEventListener(field.tagName==='INPUT'?'input':'change',()=>filter());}
 byId('filters').hidden=false;byId('fallback').hidden=true;
 byId('reset').addEventListener('click',()=>{Object.values(fields).forEach(id=>byId(id).value='');filter();});
 byId('previous').addEventListener('click',()=>{page--;render();byId('roster-count').scrollIntoView({block:'nearest'});});byId('next').addEventListener('click',()=>{page++;render();byId('roster-count').scrollIntoView({block:'nearest'});});
 addEventListener('hashchange',showHash);showHash();
}catch(error){byId('roster-count').textContent='Use the complete list below while the searchable roster is unavailable.';byId('fallback').hidden=false;byId('fallback').open=true;}
})();
