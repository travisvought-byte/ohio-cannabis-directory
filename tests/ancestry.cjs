const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
function setup(url='https://example.test/ancestry.html'){return new JSDOM(fs.readFileSync('ancestry.html','utf8'),{runScripts:'dangerously',url});}
const dom=setup(),d=dom.window.document,change=(id,v)=>{d.getElementById(id).value=v;d.getElementById(id).dispatchEvent(new dom.window.Event(id==='q'?'input':'change'));};
assert.match(d.getElementById('count').textContent,/100 matching/);assert.equal(d.querySelectorAll('#results article').length,20);
change('q','Girl Scout Cookies');assert.match(d.getElementById('count').textContent,/1 matching/);assert.equal(d.querySelector('#results article').id,'profile-gsc');
change('q','');change('effect','Relaxed');const filtered=Number(d.getElementById('count').textContent.split(' ')[0]);assert(filtered>1&&filtered<100);
change('effect','');change('mode','review');assert(d.querySelector('#profile-biscotti'));assert(!d.querySelector('#profile-pineapple-express'));
change('mode','lines');assert.equal(d.querySelectorAll('#results article').length,2);
change('mode','popular');change('sort','reviews');const counts=[...d.querySelectorAll('#results article>.tag')].map(x=>+x.textContent.match(/([\d,]+) reader/)[1].replaceAll(',',''));assert(counts.every((x,i)=>i===0||x<=counts[i-1]));
const linked=setup('https://example.test/ancestry.html?strain=profile-gelato');assert.equal(linked.window.document.querySelectorAll('#results article').length,1);assert.equal(linked.window.document.querySelector('#results article').id,'profile-gelato');
change('q','nonexistent-strain-zz');assert.match(d.getElementById('results').textContent,/No matching/);
console.log('PASS strain UI: 100-profile default, aliases, effect filter, review filter, breeder separation, sorting, exact record links and empty results');
