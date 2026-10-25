"""Render resident policy proposals from reviewed comparison entries."""
import html
import json


def render(data):
    esc = lambda value: html.escape(value, quote=True)
    sources = {s['id']: s for s in data['sources']}
    portal = {
        'states': data['states'],
        'homes': {
            'OH': [{'label': 'Find Ohio lawmakers', 'url': 'https://legislature.ohio.gov/members/district-maps'}],
            'MI': [{'label': 'Find your Michigan senator', 'url': 'https://www.senate.michigan.gov/senators/find-your-senator/'},
                   {'label': 'Michigan House website', 'url': 'https://www.house.mi.gov/'}],
        },
        'topics': data['topics'],
        'sources': sources,
    }
    short_labels = {'license-limits': 'Business license limits', 'growing-space': 'Licensed growing capacity'}
    topics = ''.join(f'<option value="{esc(t["id"])}">{esc(short_labels.get(t["id"], t["label"]))}</option>' for t in data['topics'])
    markup = r'''<section id="policy-portal" class="card">
<h2>Propose a change in your state</h2>
<p>Start with your state, choose an issue, then compare another state's approach. Use the evidence to explain the change you want.</p>
<p class="muted">First edition: Ohio and Michigan residents; two business-licensing topics. Oregon is a reference where reviewed. More resident states and policy topics are being researched.</p>
<div id="portal-controls" hidden>
<div class="fields"><div><label for="policy-home">Where do you live?</label><select id="policy-home"><option value="OH">Ohio</option><option value="MI">Michigan</option></select></div>
<div><label for="policy-topic">What policy do you want to change?</label><select id="policy-topic">__TOPICS__</select></div>
<div><label for="policy-model">Compare with</label><select id="policy-model"></select></div></div>
<div id="policy-evidence" aria-live="polite"></div>
<p><strong>A policy example is not proof of success.</strong> Check what changed after implementation, how outcomes were measured, and whether the markets are comparable. Consider market age, medical/adult-use scope, local restrictions, taxes and enforcement before drawing conclusions.</p>
<details><summary>What would count as a useful outcome comparison?</summary><p>Look for dated regulator reports or research showing consumer costs and access, entry and survival of independent businesses, ownership concentration, patient protections, illicit-market activity and public revenue. Compare periods and definitions consistently. The two licensing topics here describe legal approaches; they do not establish that one approach caused better outcomes.</p></details>
<label for="policy-goal">What change do you want your lawmakers to consider?</label><textarea id="policy-goal" rows="3" maxlength="3000" placeholder="Describe your proposal and what you want it to improve."></textarea>
<div class="fields"><div><label for="policy-town">Your town (optional)</label><input id="policy-town" maxlength="160" autocomplete="address-level2"></div>
<div><label for="policy-name">Your name (optional)</label><input id="policy-name" maxlength="160" autocomplete="name"></div>
<div><label for="policy-to">Lawmaker's name (optional)</label><input id="policy-to" maxlength="160" placeholder="Representative / Senator [Name]"></div></div>
<label for="policy-draft">Your proposal letter: edit before sending</label><textarea id="policy-draft" rows="16" spellcheck="true"></textarea>
<p id="policy-status" role="status" aria-live="polite"></p>
<div class="actions"><button type="button" id="policy-copy">Copy letter</button><button type="button" class="secondary" id="policy-download">Download text</button><button type="button" class="secondary" id="policy-print">Print letter</button><button type="button" class="secondary" id="policy-rebuild">Rebuild from current choices</button></div>
<p id="policy-lawmakers"></p><p class="muted">Nothing is sent automatically. Names, town and letter text stay on this page and are not saved when you leave. Your state/topic choices are not included in analytics events.</p>
</div>
<noscript><p>Read the cited laws below. To prepare a proposal, state where you live, describe your requested change, cite the two states' statutes, and ask how your lawmaker would evaluate the benefits and tradeoffs.</p><p>Official contacts: <a href="https://legislature.ohio.gov/members/district-maps">Ohio lawmakers</a> · <a href="https://www.senate.michigan.gov/senators/find-your-senator/">Michigan senator lookup</a> · <a href="https://www.house.mi.gov/">Michigan House website</a>.</p></noscript>
</section>
<style>
#policy-portal select{width:100%;max-width:100%;font:inherit;padding:10px;border:1px solid #888;border-radius:5px}
#policy-portal input{width:100%;padding:10px;border:1px solid #888;border-radius:5px}
#policy-evidence{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:20px 0}
#policy-evidence article{min-width:0;border:1px solid #ccc;border-radius:8px;padding:16px}
@media(max-width:650px){#policy-evidence{grid-template-columns:1fr}}
@media print{body.policy-print main>*{display:none!important}body.policy-print main>#policy-portal{display:block!important}body.policy-print #policy-portal>*{display:none!important}body.policy-print #portal-controls{display:block!important}body.policy-print #portal-controls>*{display:none!important}body.policy-print #portal-controls>#policy-print-text{display:block!important;white-space:pre-wrap;font:12pt/1.5 sans-serif;overflow-wrap:anywhere}}
</style>
<script type="application/json" id="policy-data">__DATA__</script>
<script>
(function(){
'use strict';
const D=JSON.parse(document.getElementById('policy-data').textContent),el=id=>document.getElementById(id),value=id=>el(id).value.trim();
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let edited=false,revision=0,draftRevision=0;
function topic(){return D.topics.find(t=>t.id===value('policy-topic'))}
function selected(){const t=topic();return {t,home:t.entries.find(e=>e.state===value('policy-home')),model:t.entries.find(e=>e.state===value('policy-model'))}}
function options(){const previous=value('policy-model');el('policy-model').replaceChildren();topic().entries.filter(e=>e.state!==value('policy-home')).forEach(e=>el('policy-model').add(new Option(D.states[e.state],e.state)));if([...el('policy-model').options].some(o=>o.value===previous))el('policy-model').value=previous}
function evidence(){
 const {home,model}=selected();
 el('policy-evidence').innerHTML=[home,model].map(e=>e?'<article><h3>'+escape(D.states[e.state])+'</h3><p>'+escape(e.summary)+'</p><p class="muted">'+escape(e.citation)+' · checked '+escape(e.reviewed_on)+(e.effective_on?' · effective '+escape(e.effective_on):' · effective date not recorded')+'</p>'+e.source_ids.map(id=>'<a href="'+escape(D.sources[id].url)+'" target="_blank" rel="noopener">'+escape(D.sources[id].publisher)+'</a>').join(' · ')+'</article>':'<article><p>Not yet reviewed for this topic.</p></article>').join('');
 el('policy-lawmakers').innerHTML=D.homes[value('policy-home')].map(l=>'<a href="'+escape(l.url)+'" target="_blank" rel="noopener">'+escape(l.label)+'</a>').join(' · ');
 const ready=!!(home&&model);el('policy-rebuild').disabled=!ready;
 if(!ready)el('policy-status').textContent='This comparison needs further research before a letter can be generated.';
}
function reference(e){return D.states[e.state]+': '+e.citation+' (reviewed '+e.reviewed_on+').\n'+e.source_ids.map(id=>D.sources[id].url).join('\n')}
function build(){
 const {t,home,model}=selected();if(!home||!model)return;
 const state=D.states[home.state],modelName=D.states[model.state];
 el('policy-draft').value='Dear '+(value('policy-to')||'Representative / Senator [Name]')+',\n\nI live in '+(value('policy-town')||'[your town]')+', '+state+'. I am writing about '+t.label.toLowerCase()+'.\n\nThe reviewed '+state+' approach:\n'+home.summary+'\n\nFor comparison, '+modelName+' uses this approach:\n'+model.summary+'\n\n'+(value('policy-goal')||'[Describe the change you want and why it matters to you.]')+'\n\nPlease evaluate whether this approach would fit '+state+', including its effects on consumer access, independent businesses and public oversight. A different law alone does not establish better outcomes. What evidence and tradeoffs would you consider, and what changes would you support?\n\nSources:\n'+reference(home)+'\n\n'+reference(model)+'\n\nI would appreciate a written response.\n\nThank you,\n'+(value('policy-name')||'[Your name]');
 edited=false;draftRevision=revision;el('policy-status').textContent='Letter prepared for '+state+'. Review and edit it before sending.';
}
function change(event){if(event.target.id==='policy-draft'){edited=true;return}if(['policy-home','policy-topic','policy-model'].includes(event.target.id)){revision++;if(event.target.id!=='policy-model')options();evidence()}if(edited){el('policy-status').textContent='Your edited letter is kept. Rebuild explicitly to use your current choices.'}else build()}
el('portal-controls').hidden=false;options();evidence();build();
el('portal-controls').addEventListener('input',change);
el('policy-rebuild').addEventListener('click',build);
function current(){if(draftRevision!==revision){el('policy-status').textContent='Your edited letter uses earlier state or topic choices. Review it, or rebuild before exporting.';return false}return true}
el('policy-copy').addEventListener('click',async()=>{if(!current())return;try{await navigator.clipboard.writeText(el('policy-draft').value)}catch(e){el('policy-draft').select();if(!document.execCommand('copy')){el('policy-status').textContent='Select the letter text and copy it manually.';return}}el('policy-status').textContent='Letter copied. Paste it into your own lawmaker’s contact form or email.'});
el('policy-download').addEventListener('click',()=>{if(!current())return;const u=URL.createObjectURL(new Blob([el('policy-draft').value],{type:'text/plain;charset=utf-8'})),a=document.createElement('a');a.href=u;a.download='cannabis-policy-proposal.txt';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)});
el('policy-print').addEventListener('click',()=>{if(!current())return;let p=el('policy-print-text');if(!p){p=document.createElement('div');p.id='policy-print-text';p.hidden=true;el('portal-controls').append(p)}p.textContent=el('policy-draft').value;document.body.classList.add('policy-print');window.print()});
window.addEventListener('afterprint',()=>document.body.classList.remove('policy-print'));
})();
</script>'''
    return markup.replace('__TOPICS__', topics).replace('__DATA__', json.dumps(portal, ensure_ascii=False).replace('</', '<\\/'))
