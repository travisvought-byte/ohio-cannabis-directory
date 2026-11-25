// The store and dispensary maps (November 21, 2026): Leaflet and its pin grouping are served from this site, every
// place with a map point in the data gets a pin and nothing else does, the map script contacts only OpenStreetMap
// and stores nothing, the pages say where the map pictures come from, and the privacy page explains it.
const assert=require('node:assert/strict'),fs=require('node:fs');
const read=f=>fs.readFileSync(f,'utf8'),json=f=>JSON.parse(read(f));

// served from this site, with their licences
for(const f of ['assets/vendor/leaflet.js','assets/vendor/leaflet.css','assets/vendor/leaflet.markercluster.js','assets/vendor/markercluster.css','assets/place-map.js','assets/place-map.css'])
 assert(fs.statSync(f).size>800,f);
assert(/Leaflet 1\.9\.4/.test(read('assets/vendor/leaflet.js')),'Leaflet 1.9.4');
assert(/BSD 2-Clause/.test(read('assets/vendor/LICENSE-leaflet.txt'))&&/MIT|Permission is hereby granted/.test(read('assets/vendor/LICENSE-markercluster.txt')),'licences kept');

// the map script: OpenStreetMap only, nothing stored or sent, location asked once and only on a press
const js=read('assets/place-map.js');
assert.deepEqual([...new Set(js.match(/https:\/\/[a-z.]+/g))].sort(),['https://leafletjs.com','https://tile.openstreetmap.org','https://www.google.com','https://www.openstreetmap.org'].sort(),
 'only OpenStreetMap is contacted; Google Maps is only a Directions link');
assert(!/localStorage|sessionStorage|document\.cookie|XMLHttpRequest|sendBeacon|fetch\(/.test(js),'stores and sends nothing');
assert(/getCurrentPosition/.test(js)&&!/watchPosition/.test(js),'asks for the location once, when the button is pressed');
assert(/prefers-reduced-motion: reduce/.test(js)&&/scrollWheelZoom: false/.test(js),'no animation when asked, and the page keeps scrolling over the map');

const order=(t,f)=>{const a=t.indexOf('vendor/leaflet.js'),b=t.indexOf('vendor/leaflet.markercluster.js'),c=t.indexOf('place-map.js');assert(a>0&&b>a&&c>b,f+' loads Leaflet, the grouping, then the map');
 assert(/vendor\/leaflet\.css/.test(t)&&/vendor\/markercluster\.css/.test(t)&&/place-map\.css/.test(t),f+' map styles');assert(!/unpkg\.com|cdn\.jsdelivr|cdnjs/.test(t),f+' no CDN');
 assert(/Map pictures come from OpenStreetMap, which sees your IP address and which area you look at\./.test(t),f+' says where the map pictures come from, beside the map');};

// dispensaries: the map is drawn from the same records as the cards; points are never made up
const loc=read('locations.html');order(loc,'locations.html');
assert(/<section id="loc-map" class="placemap"[^>]*hidden>/.test(loc),'the map stays hidden until it can draw');
assert(/PlaceMap\.ok\(\)/.test(loc)&&/lat:l\.latitude,lon:l\.longitude/.test(loc),'pins use the records\' own coordinates');
const data=json('data/public-locations.json').locations;
assert(data.filter(l=>l.latitude!=null).length>1000&&data.some(l=>l.latitude==null),'records with and without a map point');
assert(/no map point and/.test(js),'records without a map point are counted, not dropped');

// Ontario stores and Amsterdam coffeeshops: one pin per table row that has coordinates in the data
const where=json('data/world-where-to-buy.json').countries.CA.tables.find(t=>t.id==='ontario');
const ca=read('national/world-canada-stores.html');order(ca,'world-canada-stores.html');
const caRows=[...ca.matchAll(/<tr data-lat="([^"]+)" data-lon="([^"]+)"/g)];
assert.equal(caRows.length,where.rows.filter(r=>r.lat!=null).length,'every Ontario store with a map point');
assert.deepEqual(caRows.slice(0,3).map(m=>[+m[1],+m[2]]),where.rows.filter(r=>r.lat!=null).slice(0,3).map(r=>[r.lat,r.lon]),'coordinates copied from the data');
assert(/class="placemap pm-dark" data-table="wtb-ontario" data-input="wtb-ontario-q"/.test(ca),'the Ontario map follows the table search');
assert(!/data-table="wtb-(british-columbia|alberta|saskatchewan|manitoba)"/.test(ca),'no map for provinces without map points');
assert(/privacy\.html#map/.test(ca),'privacy link beside the map');
const nl=read('national/world-netherlands.html'),shops=json('data/world-coffeeshops-nl.json').amsterdam.shops;order(nl,'world-netherlands.html');
assert.equal((nl.match(/<tr data-lat=/g)||[]).length,shops.filter(s=>s.lat!=null).length,'every Amsterdam coffeeshop with a map point');
assert(/data-table="cs-table" data-input="cs-filter"/.test(nl),'the Amsterdam map follows the shop search');

// privacy
const priv=read('national/privacy.html');
assert(/<h2 id="map"[^>]*>(<span class="hi">.*?<\/span>)?Maps<\/h2>/.test(priv)&&/tile\.openstreetmap\.org/.test(priv)&&/OpenStreetMap sees your IP address/.test(priv)&&/never stored or sent to this site/.test(priv),'privacy page explains the map pictures and the near-me button');
console.log(`PASS place maps: Leaflet served from this site, ${caRows.length} Ontario stores and ${shops.filter(s=>s.lat!=null).length} Amsterdam coffeeshops pinned from the data, dispensary pins from the records, OpenStreetMap the only outside source and disclosed, nothing stored.`);
