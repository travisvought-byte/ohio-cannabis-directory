const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
function setup(url='https://example.test/ancestry.html'){return new JSDOM(require('./read-page.cjs')('ancestry.html'),{runScripts:'dangerously',url});}
const model=JSON.parse(fs.readFileSync('data/strains/ancestry.json','utf8')),total=model.selection.expected_profile_count;
const dom=setup(),d=dom.window.document,change=(id,v)=>{d.getElementById(id).value=v;d.getElementById(id).dispatchEvent(new dom.window.Event(id==='q'?'input':'change'));};
assert.match(d.getElementById('count').textContent,new RegExp(total+' matching'));assert.equal(d.querySelectorAll('#results article').length,20);
change('mode','classics');change('q','Girl Scout Cookies');assert.match(d.getElementById('count').textContent,/1 matching/);assert.equal(d.querySelector('#results article').id,'profile-gsc');
change('q','');change('mode','popular');change('effect','Relaxed');const filtered=Number(d.getElementById('count').textContent.split(' ')[0]);assert(filtered>1&&filtered<total);
change('effect','');change('mode','review');assert(d.querySelector('#profile-biscotti'));assert(!d.querySelector('#profile-pineapple-express'));
change('mode','lines');assert.equal(d.querySelectorAll('#results article').length,2);
assert(!d.getElementById('sort').textContent.includes('Most reviewed'));
const linked=setup('https://example.test/ancestry.html?strain=profile-gelato');assert.equal(linked.window.document.querySelectorAll('#results article').length,1);assert.equal(linked.window.document.querySelector('#results article').id,'profile-gelato');
change('sort','name');change('mode','menu');const menuCount=new Set(model.observations.map(o=>o.strain_id)).size;assert.match(d.getElementById('count').textContent,new RegExp(menuCount+' matching'));assert.match(d.getElementById('results').textContent,/Inventory is not confirmed/);change('mode','producer');change('producer','Certified Cultivators');assert.equal(Number(d.getElementById('count').textContent.split(' ')[0]),36);change('q','Sour Tangie');assert.match(d.getElementById('results').textContent,/Cheetah P/);assert(!d.getElementById('results').textContent.includes('East Coast Sour Diesel'));change('producer','');change('mode','popular');change('q','nonexistent-strain-zz');assert.match(d.getElementById('results').textContent,/No matching/);
console.log('PASS strain UI: dynamic catalog, Ohio menus and producer identity, aliases, effect filter, review filter, breeder separation, sorting, exact record links and empty results');
