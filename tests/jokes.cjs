// The joke of the day: the sailor's speech bubble shows the joke for the visitor's own date. Run: node tests/jokes.cjs
const assert=require('node:assert/strict'),{execFileSync}=require('node:child_process'),{JSDOM}=require('jsdom');
// Build the home page and the list page with three test jokes, using the same code that builds the site.
const build=(dates)=>JSON.parse(execFileSync('python3',['-c',`
import json, sys
from unittest import mock
import build_national as b
jokes = {d: "Joke for " + d + "." for d in ${JSON.stringify(dates)}}
with mock.patch.object(b, "load_jokes", return_value=jokes):
    pages = b.pages()
print(json.dumps({"home": pages["index.html"], "list": pages["jokes.html"]}))
`],{encoding:'utf8',maxBuffer:1<<27}));
// Load a page as it stands on the given day and run its joke script.
function on(day,html){
  const dom=new JSDOM(html,{runScripts:'outside-only'}),w=dom.window,[y,m,d]=day.split('-').map(Number),Real=w.Date;
  w.Date=class extends Real{constructor(...a){if(a.length)super(...a);else super(y,m-1,d,12,0,0);}};
  const script=[...w.document.querySelectorAll('script')].find((s)=>s.textContent.includes('jokes-data')&&s.type!=='application/json');
  assert(script,'the page carries the joke script');
  w.eval(script.textContent);
  return w.document;
}
const said=(d)=>{const box=d.getElementById('joke');return box.hidden?null:d.getElementById('joke-text').textContent;};
const pages=build(['2030-03-30','2030-03-31','2030-04-01']);

// 1. The bubble is in the picture, straight after the drawing, and starts hidden so there is never an empty bubble.
{
  const d=new JSDOM(pages.home).window.document,box=d.getElementById('joke');
  assert(box.hidden&&box.matches('.hero .art .shipbox > .yarn'),'the joke is a bubble in the picture box');
  assert.equal(box.previousElementSibling,d.querySelector('svg.ship'),'the bubble follows the drawing it is laid over');
  assert(!box.closest('[aria-hidden]'),'screen readers read the joke');
  assert.equal(box.querySelector('h2').textContent,'Joke of the day');
  assert.equal(box.querySelector('a').getAttribute('href'),'jokes.html');
  assert.equal(d.querySelectorAll('section.joke').length,0,'no second joke box down the page');
  assert(d.querySelector('svg.ship [aria-hidden="true"] .sailor'),'the two sailors are in the drawing');
}
// 2. Each day's own joke, across a month end; nothing before the first day.
assert.equal(said(on('2030-03-29',pages.home)),null);
assert.equal(said(on('2030-03-30',pages.home)),'Joke for 2030-03-30.');
assert.equal(said(on('2030-03-31',pages.home)),'Joke for 2030-03-31.');
assert.equal(said(on('2030-04-01',pages.home)),'Joke for 2030-04-01.');
// 3. When the batch has run out the list starts over, one a day, so the sailors are never left with nothing to say.
assert.equal(said(on('2030-04-02',pages.home)),'Joke for 2030-03-30.');
assert.equal(said(on('2030-04-03',pages.home)),'Joke for 2030-03-31.');
assert.equal(said(on('2030-04-04',pages.home)),'Joke for 2030-04-01.');
assert.equal(said(on('2030-04-05',pages.home)),'Joke for 2030-03-30.');
// A day with no joke of its own keeps the one before it.
assert.equal(said(on('2030-03-31',build(['2030-03-30','2030-04-01']).home)),'Joke for 2030-03-30.');
// 4. The list page shows only the jokes that have run, newest first, and says so when none have.
{
  const shown=(d)=>[...d.querySelectorAll('#joke-list li')].filter((li)=>!li.hidden).map((li)=>li.getAttribute('data-date'));
  let d=on('2030-03-29',pages.list);
  assert.deepEqual(shown(d),[]);assert(!d.getElementById('joke-none').hidden);
  d=on('2030-03-31',pages.list);
  assert.deepEqual(shown(d),['2030-03-31','2030-03-30']);assert(d.getElementById('joke-none').hidden);
  assert.deepEqual(shown(on('2030-06-01',pages.list)),['2030-04-01','2030-03-31','2030-03-30']);
}
console.log('PASS: the joke of the day is the sailor\'s speech bubble in the picture, follows the visitor\'s date, and starts over when a batch runs out.');
