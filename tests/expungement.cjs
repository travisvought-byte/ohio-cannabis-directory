const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require('jsdom');
const html = fs.readFileSync('expungement.html', 'utf8');
const d = new JSDOM(html, {runScripts:'outside-only', url:'https://example.org/expungement.html'});
const doc = d.window.document;
// Every route remains readable without JavaScript; the enhancement is initially hidden.
assert(doc.getElementById('finder').hidden);
for (const id of ['marijuana','general','nonconviction','special','timing','steps','form-fields','worked-example','court-packets','case-worksheet','checklist','help']) {
  assert(doc.getElementById(id) && !doc.getElementById(id).hidden, id + ' readable without JavaScript');
}
for (const a of doc.querySelectorAll('a[href^="#"]')) assert(doc.getElementById(a.hash.slice(1)), a.hash);
assert([...doc.querySelectorAll('.extra-help details')].every(el => !el.open), 'extra detail starts collapsed');
let prints = 0;
d.window.print = () => prints++;
d.window.eval(fs.readFileSync('assets/expungement.js', 'utf8'));
assert(!doc.getElementById('finder').hidden);
const select = doc.getElementById('case-route');
for (const [choice, destination] of [['marijuana','marijuana'],['general','general'],['nonconviction','nonconviction'],['special','special'],['','routes']]) {
  select.value = choice;
  select.dispatchEvent(new d.window.Event('change'));
  assert.equal(doc.getElementById('route-link').hash, '#' + destination);
  assert(doc.getElementById('route-result').textContent.length > 30);
}
doc.querySelector('a[href="#hearing"]').click();
assert(doc.getElementById('hearing').closest('details').open, 'help link opens its detail');
doc.getElementById('print-guide').click();
assert.equal(prints, 1);
assert.equal(d.window.localStorage.length, 0);
assert.equal(doc.querySelectorAll('input:not([type="checkbox"])').length, 0);
assert.equal(doc.querySelectorAll('form').length, 0);
assert.equal(doc.querySelectorAll('.checklist input[type="checkbox"]').length, 6);
assert(doc.querySelector('a[href="https://codes.ohio.gov/ohio-revised-code/section-2953.321"]'));
console.log('PASS: record-relief routes, no-script content, print action and no personal-data intake.');
