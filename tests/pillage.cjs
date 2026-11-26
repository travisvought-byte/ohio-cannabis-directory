// Pillage the Reefer (November 26, 2026): the pirate game at /pillage/. Every sea links up, every port and dig site
// sits in open water a ship can reach, trade routes the characters recommend actually pay, delivery requests can't be
// filled at the port that asks, levels climb, every fight can end, and a new game boots, sails, fights and saves cleanly.
// Round three: products trade on their own swings, every good can be smoked, the odds on a button are the odds rolled,
// burning a bale is a real 50-50, and a quick passage lands you in port with the routes tab and trade ledger ready.
// Round four: every check is a d20 roll, cannonballs run out and Brick Weed fills in, markets run out and prices move
// as you trade, pirates come in five sizes, a sunk ship ends the voyage but the hideout and the hall of fame outlive it,
// the smuggler's hold hides bales from Customs and pirates, goals earn relics, and old saves keep gentle seas.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const dir=path.join(__dirname,'..','pillage'),read=f=>fs.readFileSync(path.join(dir,f),'utf8');

// data and engine run outside a browser
const ctx={Math};ctx.window=ctx;vm.createContext(ctx);
for(const f of ['data.js','engine.js','events.js']) vm.runInContext(read(f),ctx);
const D=ctx.PILLAGE_DATA,E=ctx.PILLAGE_ENGINE,EV=ctx.PILLAGE_EVENTS;

// seas: exits pair up, every sea is reachable from home waters
const seas=Object.keys(D.MAPS),seen={windward:1},q=['windward'];
while(q.length) for(const e of D.MAPS[q.shift()].exits){ assert(D.MAPS[e.to],'exit to a real sea'); if(!seen[e.to]){seen[e.to]=1;q.push(e.to);} }
assert.deepEqual(Object.keys(seen).sort(),seas.slice().sort(),'every sea can be reached');
for(const mid of seas) for(const e of D.MAPS[mid].exits) assert(D.MAPS[e.to].exits.some(b=>b.to===mid),mid+' and '+e.to+' link both ways');

// ports and dig sites sit in reachable open water
const maps={};for(const mid of seas) maps[mid]=E.prepareMap(mid);
for(const pid in D.PORTS){ const p=D.PORTS[pid],m=maps[p.map]; const f=E.nearestFreePoint(m,p.dock[0],p.dock[1]);
  assert(Math.hypot(f[0]-p.dock[0],f[1]-p.dock[1])<40,pid+' dock is at sea');
  const a=D.MAPS[p.map].exits[0].arrive, start=E.nearestFreePoint(m,a[0]==='x'?800:a[0],a[1]);
  assert(E.findPath(m,start[0],start[1],f[0],f[1]),pid+' can be sailed to'); }
for(const sid in D.STASHES){ const s=D.STASHES[sid],m=maps[s.map],f=E.nearestFreePoint(m,s.at[0],s.at[1]); assert(Math.hypot(f[0]-s.at[0],f[1]-s.at[1])<60,sid+' can be dug from a ship'); }

// prices: every common strain grows somewhere and pays somewhere else; tips in the dialogue hold up
const avg=f=>{let s=0;for(let d=1;d<=30;d++)s+=f(d);return s/30;};
for(const g of D.COMMON){ const home=D.GOODS[g].home; assert(D.PORTS[home].sells.includes(g),g+' sold at home');
  const buy=avg(d=>E.buyPrice(home,g,d)); const best=Math.max(...Object.keys(D.PORTS).map(p=>avg(d=>E.sellPrice(p,g,d))));
  assert(best>buy*1.5&&best<buy*2.4,g+' best margin is worth the trip but not silly: '+buy.toFixed(0)+' -> '+best.toFixed(0)); }
const pays=(g,from,to)=>avg(d=>E.sellPrice(to,g,d))>avg(d=>E.buyPrice(from,g,d))*1.4;
assert(pays('tangerine','tortuga','havana'),'Ruthie: tangerine to Havana');
assert(pays('purple','portroyal','havana'),'Catalina: purple to Havana');
assert(pays('vanilla','veracruz','barbados'),'Esperanza: vanilla to Barbados');
// hash, rosin and biscuits trade on their own swings and pay extra where they're wanted; every good can be smoked
for(const g of Object.keys(D.GOODS)) assert(D.SMOKE[g]&&D.SMOKE[g].name&&D.SMOKE[g].does&&D.SMOKE[g].flavor,g+' can be smoked');
const products=Object.keys(D.GOODS).filter(g=>D.GOODS[g].kind==='product');
// the grow: real breeding lines, every one reachable from the five landraces, every strain a good any market buys
{ const G=D.GENES,pairs=new Set(); for(const [a,b,r] of D.CROSSES){ assert(G[a]&&G[b]&&G[r],'a real cross: '+a+' x '+b); const k=[a,b].sort().join('+'); assert(!pairs.has(k),'one result per pair: '+k); pairs.add(k); }
  const got=new Set(Object.keys(G).filter(id=>G[id].kind==='landrace')); assert.equal(got.size,5);
  for(const id of got) assert(D.PORTS[G[id].from],id+' is sold somewhere');
  for(let more=true;more;){ more=false; for(const [a,b,r] of D.CROSSES) if(got.has(a)&&got.has(b)&&!got.has(r)){ got.add(r); more=true; } }
  assert.equal(got.size,Object.keys(G).length,'every strain can be bred');
  for(const id in G) if(G[id].kind==='strain'){ const g=D.GOODS[G[id].good]; assert(g&&g.kind==='grown'&&!g.rare&&!g.home&&G[id].note,id+' grows into a good');
    for(const p in D.PORTS) assert(E.sellPrice(p,G[id].good,3)>g.base*0.8&&E.buyPrice(p,G[id].good,3)===null,id+' sells in '+p+' and is sold nowhere'); }
  assert(D.GOODS.g_home&&D.GOODS.g_jack.base>D.GOODS.g_nl.base,'the hardest strain is worth the most'); }
assert(products.length>=3,'there is more than strains to trade');
for(const g of products){ const G=D.GOODS[g]; assert(D.PORTS[G.home].sells.includes(g),g+' sold where it is made');
  const buy=avg(d=>E.buyPrice(G.home,g,d)),sell=p=>avg(d=>E.sellPrice(p,g,d)),others=Object.keys(D.PORTS).filter(p=>p!==G.home&&!G.wants.includes(p));
  const best=Math.max(...Object.keys(D.PORTS).map(sell)),mean=a=>a.reduce((s,p)=>s+sell(p),0)/a.length;
  assert(best>buy*1.5&&best<buy*2.4,g+' margin '+buy.toFixed(0)+' -> '+best.toFixed(0));
  assert(G.wants.every(p=>D.PORTS[p])&&mean(G.wants)>mean(others)*1.1,g+' pays more where it is wanted'); }
assert.notEqual(D.GOODS.hash.swing,D.GOODS.rosin.swing,'products swing differently');
for(const k in D.QUESTS){ const r=D.QUESTS[k]; assert(!D.PORTS[r.port].sells.includes(r.good),k+' asks for something the port does not sell'); }

// levels, upgrades and fights
D.LEVELS.forEach((l,i)=>{ if(i) assert(l.xp>D.LEVELS[i-1].xp,'levels climb'); });
assert.equal(E.levelOf(0),1); assert.equal(E.levelOf(D.LEVELS[9].xp),10);
for(const k in D.UPGRADES){ const u=D.UPGRADES[k]; assert.equal(u.cost.length,u.levels.length-1,k+' has a price per level'); u.cost.forEach((c,i)=>{ if(i) assert(c>u.cost[i-1],k+' costs climb'); }); }
const ship=(c,h,f)=>({up:{cannons:c,hull:h},skill:{fight:f},hull:D.UPGRADES.hull.levels[h]});
function odds(s,kind,tier){ let w=0; for(let i=0;i<500;i++){ const st=E.stats(s),en=E.foe(kind,tier); let eh=en.hull,h=s.hull,r=0;
  while(r++<60){ eh-=E.hit(st.fire,Math.random()); if(eh<=0||(kind==='merchant'&&eh<=en.hull*0.35)){w++;break;} h-=E.hit(en.fire,Math.random()); if(h<=0)break; }
  assert(r<60,'a fight ends'); } return w/500; }
assert(odds(ship(0,0,0),'merchant',1)>0.95,'a new ship can take a small merchant');
assert(odds(ship(0,0,0),'pirate',1)>0.9,'a new ship can beat home-waters pirates');
assert(odds(ship(2,2,2),'pirate',3)>0.9,'a mid-upgraded ship can beat the roughest pirates');
assert(odds(ship(4,3,5),'boss',4)>0.9&&odds(ship(2,2,2),'boss',4)<0.1,'Gristle needs a strong ship');
for(const kind of ['merchant','pirate','boss','navy']) for(const t of [undefined,0,1,2,3,9]){ const f=E.foe(kind,t); assert(Number.isFinite(f.hull)&&Number.isFinite(f.fire),'foe stats are numbers'); }
assert(EV.sea.length>=10&&EV.port.length>=5,'surprises at sea and in port');
// round five: nations of 1718, standing, warships and real history
assert.deepEqual([-80,-30,0,30,80].map(E.standTier),[0,1,2,3,4],'five steps of standing');
assert(E.foe('navy',1).cls===D.NAVY_CLASS[0]&&E.foe('navy',5).cls===D.NAVY_CLASS[2]&&E.foe('navy',3).hull>E.foe('pirate',3).hull,'warships are big');
for(const pid in D.PORTS) assert(D.NATIONS[D.PORTS[pid].nation]&&D.PORTS[pid].history.length>40,pid+' flies a flag and has a real history note');
for(const mid of seas) assert(D.NATIONS[D.SEA_LAW[mid]]&&D.SEA_NAVY[mid].length&&D.SEA_TRADE[mid].every(k=>D.NATIONS[k]),mid+' has a law, a navy and traders');
for(const k of D.NATION_ORDER) assert(D.NATIONS[k].flag&&D.STAND.length===5&&Array.isArray(D.WAR[k]),k+' is described');
assert(/buck-an-ear/.test(read('data.js'))&&/Buccaneer/.test(read('data.js')),'Ruthie knows the corn joke');
assert(/nobody in the Caribbean smoked cannabis/.test(read('index.html')),'the fine print keeps the history honest');
// round four: the die, pirate sizes, stock and price pressure
assert.equal(E.need(50),11); assert.equal(E.need(95),2); assert.equal(E.need(5),20);
for(let r=0;r<1;r+=0.01){ assert(E.pirateTier(1,1,r,true)<=1,'new captains only meet small pirates in home waters'); const t=E.pirateTier(3,9,r,false); assert(t>=3&&t<=5,'tiers stay in range'); }
assert.equal(E.pirateTier(3,9,0.95,false),5,'a famous captain can meet a man-o-war'); assert.equal(E.foe('pirate',5).cls,'man-o’-war');
assert(odds(ship(0,0,0),'pirate',2)<0.2&&odds(ship(2,2,2),'pirate',5)<0.2,'bigger pirates out-gun you, so there is real danger');
assert.equal(E.stockMax('tortuga','tangerine'),16); assert.equal(E.stockMax('havana','tangerine'),0,'no stock where it is not sold'); assert(E.stockMax('nassau','brick')>=20,'Brick Weed is plentiful');
assert(E.pushed(100,10,true)>100&&E.pushed(100,10,false)<100&&E.pushed(100,0,true)===100,'trading moves the price');
assert(D.GOODS.brick.kind==='brick'&&!D.COMMON.includes('brick')&&!D.COMMON.includes('pearl'),'brick and pearl are not loot strains');
{ const H=D.HIDEOUT,m=maps[H.map],f=E.nearestFreePoint(m,H.dock[0],H.dock[1]),p=D.PORTS.tortuga.dock;
  assert(Math.hypot(f[0]-H.dock[0],f[1]-H.dock[1])<40&&E.findPath(m,p[0],p[1],f[0],f[1]),'the hideout cove can be sailed to'); }
for(const k of ['spyglass','tooth','wig','compass','doubloon','figure','seal','goldbrick','flag']) assert(D.RELICS[k]&&D.RELICS[k].does,k+' relic is described');
for(const t of [D.SAILS,D.FLAGS]) for(const k in t) assert(t[k].name&&/^#[0-9a-f]{6}$/.test(t[k].color),k+' has a name and colour');

// the page boots, a new game docks, sails, fights a merchant and saves
const {JSDOM}=require('jsdom');
const dom=new JSDOM(read('index.html'),{runScripts:'outside-only',pretendToBeVisual:true,url:'https://the-reefer.com/pillage/'}),w=dom.window,errors=[];
w.addEventListener('error',e=>errors.push(e.error||e.message));
const noop=()=>{},c2d=new Proxy({},{get(t,k){ if(k in t) return t[k]; if(k==='measureText') return ()=>({width:10});
  if(/Gradient|Pattern/.test(k)) return ()=>({addColorStop:noop}); return noop; },set(t,k,v){t[k]=v;return true;}});
w.HTMLCanvasElement.prototype.getContext=()=>c2d; w.Path2D=class{moveTo(){} lineTo(){} closePath(){} quadraticCurveTo(){} arc(){} rect(){} ellipse(){}};
w.Element.prototype.getBoundingClientRect=()=>({left:0,top:0,width:390,height:520,right:390,bottom:520,x:0,y:0});
w.fetch=()=>Promise.resolve({ok:true,json:()=>Promise.resolve({})});
if(!w.HTMLDialogElement.prototype.showModal){ w.HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');};
  w.HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');this.dispatchEvent(new w.Event('close'));}; }
for(const f of ['data.js','engine.js','events.js','game.js']) w.eval(read(f));
const $=id=>w.document.getElementById(id),P=w.__pillage;
assert(read('game.js').includes("window.directoryTrack('pillage-'"),'milestones go to the site visit counter');
assert(/21\+|21 or older/.test(read('index.html')),'adults only');
$('btn-new').click(); assert($('dlg-captain').open,'a new voyage starts by naming the captain');
assert($('cap-real').checked&&!P.state.gentle,'real danger is the default');
$('cap-name').value='  Anne <b>Bonny</b>\u0007 '; $('cap-ship').value=''; $('cap-ok').click();
assert.equal(P.state.look.captain,'Anne bBonny/b','names are cleaned'); assert.equal(P.state.look.ship,'the Lucky Leaf','a blank ship name keeps the default');
assert(/the Lucky Leaf/.test($('note-body').textContent)&&/ship goes down/.test($('note-body').textContent),'the welcome note warns about real danger');
$('note-ok').click();
assert($('dlg-port').open,'starts docked at Tortuga'); assert.equal(P.state.xp,25,'first visit earns renown'); assert.equal(P.state.shot,12,'twelve cannonballs to start');
$('set-sail').click(); for(let i=0;i<300;i++) P.step(1/30);
const S=P.state,n={kind:'merchant',tier:1,name:'the Test',captain:'X',cool:0,x:S.x+5,y:S.y,route:[[0,0]],leg:0};
P.encounter(n); [...$('enc-body').querySelectorAll('.choice')].find(b=>/Attack/.test(b.textContent)).click();
for(let i=0;i<30&&$('enc-body').querySelector('.choice');i++) $('enc-body').querySelector('.choice:not([disabled])').click();
assert(/strikes her colours|surrenders|rolls over and sinks|Your ship is beaten/.test($('enc-text').textContent),'the fight ends');
assert(P.state.shot<12,'firing uses cannonballs');
$('enc-body').querySelector('.primary').click(); assert(!$('dlg-encounter').open);
// odds: the number on the button is the number rolled, and a miss earns a second wind
const rnd=w.Math.random;
// Docking can open a random port event first; tests that dock to use a tab keep the dice quiet.
const dockAt=pid=>{ w.Math.random=()=>0.99; try{ P.dock(pid); } finally { w.Math.random=rnd; } };
S.buff=null; S.grit=2; assert.equal(P.odds.chanceOf(0.5),70); assert.equal(P.odds.pct(0.5),'🎲 7+, 70%','the button shows the number to roll');
S.grit=0; assert.equal(P.odds.chanceOf(0.99),95,'never certain'); assert.equal(P.odds.chanceOf(0),5,'never hopeless'); assert.equal(P.odds.pct(0.5),'🎲 11+, 50%');
w.Math.random=()=>0; P.odds.roll(0.5); assert.equal(S.grit,1,'a 1 misses'); P.odds.roll(0.5); P.odds.roll(0.5); P.odds.roll(0.5); assert.equal(S.grit,3,'second wind caps at three misses'); assert.equal(P.odds.chanceOf(0.5),80);
w.Math.random=()=>0.99; assert(P.odds.roll(0.5),'a 20 hits'); assert.equal(S.grit,0,'a hit resets it'); w.Math.random=rnd;
let hits=0; for(let i=0;i<6000;i++){ S.grit=0; if(P.odds.roll(0.6)) hits++; } S.grit=0;
assert(Math.abs(hits/6000-0.6)<0.03,'rolls land as often as the label says: '+hits/6000);
// smoking a bale costs one bale and gives the boost on its label
S.cargo={breath:2,tangerine:1}; const f0=P.stats().fight;
assert(P.smoke('breath')); assert.equal(S.cargo.breath,1,'one bale burned'); assert.equal(P.stats().fight,f0+2,'Old Sea Dog adds Fighting');
assert(P.odds.chanceOf(0.5)===50&&!P.smoke('kraken'),'no luck from Old Sea Dog, and you cannot smoke what you lack');
// Customs offers to burn a bale at even odds; it costs the cheapest bale whatever happens
P.encounter({kind:'customs',name:'Officer Test',cool:0,x:S.x+5,y:S.y,route:[[0,0]],leg:0});
let burn=[...$('enc-body').querySelectorAll('.choice')].find(b=>/Burn a bale/.test(b.textContent));
assert(burn&&/Burn a bale of Tortuga Tangerine \(🎲 11\+, 50%\)/.test(burn.textContent),'burn a bale shows its real odds: '+(burn&&burn.textContent));
assert([...$('enc-body').querySelectorAll('.choice')].every(b=>/%|fee/.test(b.textContent)),'every Customs option shows a percentage');
w.Math.random=()=>0.99; burn.click(); w.Math.random=rnd;
assert(/wanders off/.test($('enc-text').textContent)&&!S.cargo.tangerine,'the cutter wanders off and the bale is gone');
assert(/You rolled 20|natural 20/.test($('enc-text').textContent)&&$('enc-body').querySelector('.die.hit'),'the roll is shown, with the die');
$('enc-body').querySelector('.primary').click(); assert(!$('dlg-encounter').open);
// a quick passage takes days, may bring one run-in, and lands you in port with the routes tab ready
P.dock('tortuga'); const d0=S.dist; S.cargo={}; S.gentle=true; assert(P.voyage('tortuga','havana'),'a route to Havana');
assert(P.passage('havana'));
for(let i=0;i<40&&$('dlg-encounter').open;i++) ($('enc-body').querySelector('.choice:not([disabled])')||$('enc-body').querySelector('.primary')).click();
assert.equal(S.docked,'havana','landed in Havana'); assert.equal(Math.round(S.dist-d0),P.voyage('tortuga','havana').days*900,'the day counter moves by the days shown');
assert(S.seen.tortuga&&S.seen.havana,'both ports are in the ledger');
// browsers fire the old port's close event after the new port has opened; it must not cast you off again
$('dlg-port').dispatchEvent(new w.Event('close')); assert.equal(S.docked,'havana','still docked after a late close event'); assert($('dlg-port').open);
$('tab-routes').click(); assert(/Sail to/.test($('port-panel').textContent)&&/Trade ledger/.test($('port-panel').textContent),'routes tab lists passages and the ledger');
// longer, richer runs draw more pirates
S.cargo={}; const vs=P.voyage('tortuga','portroyal'),vl=P.voyage('tortuga','barbados');
assert(vl.days>vs.days&&P.passageRisk(vl).pirates>P.passageRisk(vs).pirates,'a longer passage is riskier');
const r0=P.passageRisk(vl).pirates; S.cargo={haze:20}; assert(P.passageRisk(vl).pirates>r0,'a rich hold draws pirates'); S.cargo={};
w.dispatchEvent(new w.Event('pagehide'));
const saved=JSON.parse(w.localStorage.getItem('pillageTheReefer.v1')); assert.equal(saved.xp,S.xp,'renown is saved');
// markets run out, and every bale you trade moves the price
$('set-sail').click(); P.dock('tortuga'); S.gold=10000; S.cargo={}; S.mk={}; S.news=[];
const p0=P.buyAt('tortuga','tangerine'),got=P.buyBales('tortuga','tangerine',100);
assert.equal(got.n,16,'Tortuga only has 16 bales on the shelf'); assert.equal(P.stockOf('tortuga','tangerine'),0); assert(P.buyAt('tortuga','tangerine')>p0,'buying pushes the price up');
const s0=P.sellAt('tortuga','tangerine'); P.sellBales('tortuga','tangerine',8); assert(P.sellAt('tortuga','tangerine')<s0,'selling pushes the price down');
S.dist+=900; assert(P.stockOf('tortuga','tangerine')>0,'the shelves refill as the days pass');
S.shot=12; $('tab-market').click(); assert(/in stock|Sold out/.test($('port-panel').textContent)&&/Cannonballs: 12 of 40/.test($('port-panel').textContent),'the market shows stock and sells cannonballs');
$('port-panel').querySelector('[data-key="shot10"]').click(); assert.equal(S.shot,22,'buying cannonballs');
// the smuggler's hold hides the most valuable bales from Customs and pirates
S.up.secret=1; S.cargo={kraken:2,tangerine:5,brick:3};
assert.deepEqual(JSON.parse(JSON.stringify(P.openCargo())),{tangerine:3,brick:3},'kraken and two tangerine ride hidden'); assert.equal(P.hiddenCount(),4);
$('set-sail').click();
// a pirate fight: lob Brick Weed, then strike your colours and sail on
const pir=()=>({kind:'pirate',tier:1,name:'the Test Pirate',captain:'Captain Test',cool:0,x:S.x+5,y:S.y,route:[[0,0]],leg:0});
S.hull=P.stats().hullMax; P.fight(pir(),null);
const lob=[...$('enc-body').querySelectorAll('.choice')].find(b=>/Lob a bale of Brick Weed/.test(b.textContent)); assert(lob,'Brick Weed is offered as ammunition');
const b0=S.bricks; lob.click(); assert.equal(S.cargo.brick,2,'a bale of Brick Weed is fired'); assert.equal(S.bricks,b0+1);
assert(/THWUMP/.test($('enc-text').textContent)||/sinks|surrender/.test($('enc-text').textContent),'the bale lands');
if($('enc-body').querySelector('.choice')){ assert(/giggly/.test($('enc-body').textContent),'their crew gets high');
  const g0=S.gold; [...$('enc-body').querySelectorAll('.choice')].find(b=>/Strike your colours/.test(b.textContent)).click();
  assert.equal(S.cargo.kraken,2,'the smuggler’s hold keeps its kraken'); assert(!S.cargo.brick&&S.cargo.tangerine===2,'they take the open hold'); assert.equal(S.gold,g0-Math.floor(g0/2),'and half the gold');
  assert(/smuggler’s hold/.test($('enc-text').textContent)); }
$('enc-body').querySelector('.primary').click(); assert(!$('dlg-encounter').open);
// goals earn relics
S.visited={tortuga:1,portroyal:1,petitgoave:1,havana:1,nassau:1}; P.checkGoals(); assert(S.relics.spyglass,'five ports earn the spyglass');
// the hideout: buy the key, leave gold and bales, cast off
S.gold=3000; P.effects('base:buy'); assert(P.legacy.base&&S.gold===2500,'Toussaint sells the key');
P.enterBase(); assert($('dlg-hideout').open&&S.atBase,'the hideout opens');
$('base-body').querySelector('[data-key="gl100"]').click(); assert.equal(P.legacy.base.gold,100,'gold in the strongbox');
$('base-body').querySelector('[data-key="statangerine"]').click(); assert.equal(P.legacy.base.bales.tangerine,2,'bales in the stash');
assert(/Sail to/.test($('base-body').textContent),'quick passage from the hideout');
$('base-leave').click(); assert(!$('dlg-hideout').open&&!S.atBase,'cast off');
assert(JSON.parse(w.localStorage.getItem('pillageTheReefer.legacy')).base.gold===100,'the hideout is saved apart from the voyage');
// real danger: a sunk ship ends the voyage; the hideout and the hall of fame stay
S.sunk=Math.max(1,S.sunk); P.checkGoals(); assert(P.legacy.sails.black,'beating a pirate earns black sails for every voyage');
S.gentle=false; S.hull=1; S.shot=5; const big={kind:'pirate',tier:5,name:'the Huge Problem',captain:'Admiral Test',cool:0,x:S.x+5,y:S.y,route:[[0,0]],leg:0};
P.fight(big,null); assert(/could sink you/.test($('enc-body').textContent),'fair warning before a sinking shot');
[...$('enc-body').querySelectorAll('.choice')].find(b=>/Fire cannonballs/.test(b.textContent)).click();
assert(/goes down/.test($('enc-title').textContent)&&/voyage is over/.test($('enc-body').textContent),'the ship sinks');
assert.equal(w.localStorage.getItem('pillageTheReefer.v1'),null,'the voyage is gone');
const fame=JSON.parse(w.localStorage.getItem('pillageTheReefer.legacy')).fame; assert(fame.length===1&&fame[0].how==='sunk'&&/Admiral Test/.test(fame[0].by),'the hall of fame remembers');
$('enc-body').querySelector('.primary').click(); assert(!$('title-screen').hidden&&/Anne/.test($('title-fame').textContent),'back to the title, with the hall of fame');
assert(P.legacy.sails.black,'earned sails stay earned');
$('btn-new').click(); assert($('dlg-captain').open); assert($('cap-sails').querySelector('input[value="black"]:not([disabled])'),'black sails are unlocked now');
$('cap-gentle').click(); $('cap-ok').click(); assert(P.state.gentle,'gentle seas chosen');
assert(/still holds 100 doubloons and 2 bales/.test($('note-body').textContent),'the next voyage hears about the hideout'); $('note-ok').click();
assert.equal(P.state.gold,250,'a fresh purse'); assert(!P.state.relics.spyglass,'relics went down with the ship'); assert.equal(P.legacy.base.gold,100,'the strongbox survived');
// a voyage saved before ships could sink keeps gentle seas
const old=JSON.parse(JSON.stringify(saved)); delete old.gentle; delete old.shot; P.begin(false,old); assert(P.state.gentle&&P.state.shot===12,'old saves sail gentle seas with twelve cannonballs');
// round five: an old voyage meets the nations of 1718 and starts neutral with everyone
const o5=JSON.parse(JSON.stringify(saved)); for(const k of ['rep','marque','jobs','jobsTaken','jobsDone','bounties','news','lastDay','salute','seed']) delete o5[k]; delete o5.flags.r5;
P.begin(false,o5); const T=P.state;
assert(Object.values(T.rep).every(v=>v===0)&&T.jobs.length===0&&Number.isFinite(T.seed),'an old voyage starts neutral with every nation');
assert($('dlg-note').open&&/real flag of 1718/.test($('note-body').textContent),'and hears what is new'); $('note-ok').click();
// level 2 opens the Jobs tab; a delivery takes room in the hold and pays on arrival
T.xp=Math.max(T.xp,D.LEVELS[1].xp); T.gentle=true; T.cargo={}; T.jobs=[]; T.jobsTaken={}; T.news=[]; T.hull=P.stats().hullMax;
dockAt('tortuga'); assert($('tab-jobs'),'level 2 opens the Jobs tab'); $('tab-jobs').click();
assert(/Carry|Smuggle|Bring/.test($('port-panel').textContent)&&/French port/.test($('port-panel').textContent),'the board posts French jobs');
const job=P.jobOffers('tortuga').find(j=>j.kind==='deliver'); assert(job&&job.pay>0&&D.PORTS[job.to]&&job.by==='france','Tortuga has a delivery');
const sp0=P.space(); assert(P.takeJob(job)); assert.equal(P.space(),sp0-job.n,'job cargo takes room in the hold'); assert.equal(P.jobLoad(),job.n);
assert(!P.jobOffers('tortuga').some(j=>j.id===job.id),'a taken job leaves the board');
const g5=T.gold,r5=T.rep.france; w.Math.random=()=>0.99; assert(P.passage(job.to),'sail for the delivery');
for(let i=0;i<40&&$('dlg-encounter').open;i++) ($('enc-body').querySelector('.choice:not([disabled])')||$('enc-body').querySelector('.primary')).click();
w.Math.random=rnd;
assert.equal(T.docked,job.to); assert.equal(T.jobs.length,0,'the job is done on arrival'); assert(T.gold>=g5+job.pay&&T.rep.france>r5&&T.jobsDone===1,'it pays, and France thinks better of you');
// standing and news set prices
const hg=D.PORTS.havana.sells[0],hp=P.buyAt('havana',hg); T.rep.spain=-80; assert(P.buyAt('havana',hg)>hp,'a hostile port charges more'); T.rep.spain=0;
const sg=D.COMMON.find(g=>!D.PORTS.havana.sells.includes(g)),spr=P.sellAt('havana',sg); T.news=[{kind:'spike',pid:'havana',g:sg,mult:2,until:99999,text:'Test'}];
assert(P.sellAt('havana',sg)>spr*1.5,'news of a shortage sends the price up'); T.news=[];
// pillaging a merchant turns its nation cold
if($('dlg-port').open) $('set-sail').click();
T.marque=''; T.rep.dutch=0; T.shot=30; T.hull=P.stats().hullMax; w.Math.random=()=>0.99;
P.fight({kind:'merchant',nation:'dutch',tier:1,name:'the Test',captain:'X',cool:0,x:T.x+5,y:T.y,route:[[0,0]],leg:0},null);
for(let i=0;i<30&&$('enc-body').querySelector('.choice');i++) $('enc-body').querySelector('.choice:not([disabled])').click();
w.Math.random=rnd;
assert(/strikes her colours|surrenders|rolls over and sinks/.test($('enc-text').textContent)&&T.rep.dutch<0,'the Dutch remember a pillaged merchant: '+T.rep.dutch);
$('enc-body').querySelector('.primary').click();
// a friendly warship takes a salute; a hostile one takes a fine and cleans the slate
const navy=()=>({kind:'navy',nation:'britain',tier:3,name:'the Test',captain:'Captain Test',cool:0,x:T.x+5,y:T.y,route:[[0,0]],leg:0});
T.rep.britain=30; T.salute={}; P.encounter(navy()); [...$('enc-body').querySelectorAll('.choice')].find(b=>/salute/.test(b.textContent)).click();
assert.equal(T.rep.britain,32,'a salute warms Britain up'); $('enc-body').querySelector('.primary').click();
T.rep.britain=-80; T.gold=1000; P.encounter(navy()); assert(/Pay what you owe Britain \(250 doubloons/.test($('enc-body').textContent),'a hostile warship wants a quarter of your gold');
[...$('enc-body').querySelectorAll('.choice')].find(b=>/Pay what you owe/.test(b.textContent)).click();
assert(T.gold===750&&T.rep.britain===-19,'the fine clears the worst of it'); $('enc-body').querySelector('.primary').click();
w.dispatchEvent(new w.Event('pagehide')); const s5=JSON.parse(w.localStorage.getItem('pillageTheReefer.v1'));
assert(s5.rep.britain===-19&&s5.jobsDone===1&&s5.flags.r5,'standing and jobs are saved');
$('btn-log').click(); assert(/The powers of 1718/.test($('log-body').textContent)&&/Great Britain: ⚪ Neutral \(-19\)/.test($('log-body').textContent)&&$('log-body').querySelectorAll('.fl').length>=5,'the log shows every nation with its flag');
$('log-close').click();
// Round five, part two: provisions, the law, decoys and fire ships
const closeEnc=()=>{ for(let i=0;i<20&&$('dlg-encounter').open;i++) ($('enc-body').querySelector('.primary')||$('enc-body').querySelector('.choice:not([disabled])')).click(); };
const choose=re=>{ const b=[...$('enc-body').querySelectorAll('.choice')].find(x=>re.test(x.textContent)); assert(b,'offered: '+re); b.click(); };
const cust=k=>({kind:'customs',nation:k,name:'the Test Cutter',captain:'X',cool:0,x:T.x+5,y:T.y,route:[[0,0]],leg:0});
T.up.secret=0; T.gentle=true; T.marque=''; T.jobs=[]; T.news=[]; T.cargo={}; T.gold=1000; T.hull=P.stats().hullMax;
// the crew eats a day's provisions for every day at sea from level 2, and two more for a smoke
dockAt('tortuga'); $('tab-market').click(); assert(/Provisions: \d+ of 40 days/.test($('port-panel').textContent),'markets sell provisions from level 2');
T.food=20; const fd0=E.dayOf(T.dist); w.Math.random=()=>0.99; assert(P.passage('portroyal'),'sail to Port Royal'); closeEnc(); w.Math.random=rnd;
const fdays=E.dayOf(T.dist)-fd0; assert(fdays>0&&T.food===20-fdays,'the crew eats a day for each of the '+fdays+' days at sea: '+T.food);
const sm=Object.keys(D.SMOKE).find(g=>!D.CONTRABAND||!D.CONTRABAND.includes(g)); T.cargo[sm]=1; T.food=10; assert(P.smoke(sm)); assert.equal(T.food,8,'the munchies eat two days of provisions');
T.food=0; const hc=P.odds.chanceOf(0.5); assert(P.hungry(),'no food, hungry crew'); T.food=5; assert.equal(P.odds.chanceOf(0.5),hc+10,'a hungry crew rolls 10% worse');
T.gold=100; T.food=35; assert.equal(P.buyFood(10),5,'the lockers hold 40 days'); assert(T.food===40&&T.gold===90,'provisions cost 2 doubloons a day');
if($('dlg-port').open) $('set-sail').click();
// the law: a small haul gets a warning, then a fine
T.food=20; T.gold=1000; T.record={}; T.rep.france=0; T.cargo={brick:5}; w.Math.random=()=>0;
P.customs(cust('france')); choose(/Run for it/); assert(/first offence/.test($('enc-text').textContent)&&T.gold===1000,'a first offence is a warning'); closeEnc();
T.cargo={brick:5}; P.customs(cust('france')); choose(/Run for it/); assert(/fine as well: 100 doubloons/.test($('enc-text').textContent)&&T.gold===900,'a second is a fine'); closeEnc();
// a big haul in plain sight means jail: the open hold, half the gold, days inside, and a nation against you
T.cargo={brick:60}; T.gold=1000; T.rep.britain=0; T.record={}; assert(P.bigHaul()); const jd0=E.dayOf(T.dist);
P.customs(cust('britain')); assert(/jail, not a fine/.test($('enc-body').textContent),'the customs warn you about jail'); choose(/Run for it/);
assert(/locks you up for 5 days/.test($('enc-text').textContent)&&T.gold===500&&!T.cargo.brick&&T.rep.britain===-80,'jail takes the hold and half the gold');
w.Math.random=()=>0.99; $('enc-body').querySelector('.primary').click(); w.Math.random=rnd;
assert(D.PORTS[T.docked]&&D.PORTS[T.docked].nation==='britain'&&$('dlg-port').open,'you walk out on a British dock: '+T.docked);
assert(E.dayOf(T.dist)>=jd0+5&&P.standOf('britain')===0,'five days pass, and Britain is still hostile');
// decoys at level 3: bought at the shipwright, they draw off the customs or a pirate
T.rep.britain=0; T.xp=Math.max(T.xp,D.LEVELS[2].xp); T.gold=1000; T.decoys=0; $('set-sail').click(); dockAt('tortuga'); $('tab-yard').click();
$('port-panel').querySelector('[data-key=decoy]').click(); $('port-panel').querySelector('[data-key=decoy]').click();
assert(T.decoys===2&&T.gold===500&&/Two decoys is all/.test($('port-panel').textContent),'two decoys at 250 each');
$('set-sail').click(); T.cargo={brick:5}; P.customs(cust('france')); choose(/Send a decoy/); assert(T.decoys===1&&T.cargo.brick===5,'a decoy draws off the customs'); closeEnc();
const gd=T.gold; P.fight(pir(),null); choose(/Send a decoy/); assert(T.decoys===0&&T.gold===gd&&!$('enc-body').querySelector('.choice'),'and ends a fight'); closeEnc();
// fire ships at level 4: hired in a Nassau tavern, they burn one ship
T.xp=Math.max(T.xp,D.LEVELS[3].xp); T.gold=1000; T.fireship=0; dockAt('nassau'); $('tab-tavern').click();
assert(/Maracaibo/.test($('port-panel').textContent),'the tavern tells the real story'); $('port-panel').querySelector('[data-key=fireship]').click();
assert(T.fireship===1&&T.gold===500,'a fire ship costs 500'); $('set-sail').click();
w.Math.random=()=>0.99; P.fight(pir(),null); choose(/Send in your fire ship/); w.Math.random=rnd;
assert(T.fireship===0&&/fire ship/i.test($('enc-text').textContent)&&/burns with her/.test($('enc-text').textContent),'the fire ship burns her'); closeEnc();
// taken over by pirates: the open hold and nine doubloons in ten
T.gold=1000; T.cargo={brick:4}; T.hull=1; w.Math.random=()=>0; P.fight(pir(),null); choose(/^⚔️ Board/); w.Math.random=rnd;
assert(T.gold===100&&!T.cargo.brick&&/nine in every ten/.test($('enc-text').textContent),'pirates take 90% of the gold'); closeEnc();
// the grow: buy seeds, plant, wait, cross, harvest, and breed Northern Lights
const L=P.legacy; L.base=L.base||{lvl:0,gold:0,bales:{},basis:{}}; L.base.grow={beds:[],seeds:{}}; L.base.bales={}; L.base.lvl=1;
T.gold=1000; dockAt('willemstad'); $('tab-tavern').click(); assert(/Seed trader/.test($('port-panel').textContent)&&/Siam/.test($('port-panel').textContent),'Willemstad has a seed trader');
$('port-panel').querySelector('[data-key=seed-afghani]').click(); $('port-panel').querySelector('[data-key=seed-thai]').click();
assert(T.gold===760&&L.base.grow.seeds.afghani&&L.base.grow.seeds.thai&&/Afghani is in your seed chest/.test($('port-panel').textContent),'two packets of seeds');
assert(!P.buySeed('afghani')&&!P.buySeed('nl'),'one packet each, and only landraces are for sale'); $('set-sail').click();
assert(P.plant(0,'afghani')&&P.plant(1,'thai')&&!P.plant(0,'thai')&&!P.plant(1,'colgold'),'plant what you have in empty beds');
assert(!P.bedReady(L.base.grow.beds[0])&&P.crossBeds()===null,'nothing to cross until they flower'); T.dist+=D.GROW.days*900;
assert(P.bedReady(L.base.grow.beds[1]),'six days later they flower'); const cx=P.crossBeds(); assert(cx&&cx.r==='nl'&&cx.fresh&&L.base.grow.seeds.nl,'Afghani x Thai breeds Northern Lights');
assert.equal(P.crossBeds(),null,'one cross a season'); const hv=P.harvest(0); assert(hv&&hv.g==='g_home'&&hv.n===6&&L.base.bales.g_home===6&&!L.base.grow.beds[0],'a landrace harvests as Homegrown');
P.harvest(1); assert(P.plant(0,'nl')); L.base.grow.beds[0].voy=-1; assert(P.bedReady(L.base.grow.beds[0]),'a bed planted on an earlier voyage is ready');
assert(P.harvest(0).g==='g_nl'&&L.base.bales.g_nl===6,'Northern Lights harvests as itself');
assert(P.crossOf('nl','skunk1')==='shiva'&&P.crossOf('afghani','acapulco')===null,'crosses work either way round, and only real lines');
assert(P.sellAt('havana','g_nl')>D.GOODS.g_nl.base*0.8&&P.buyAt('havana','g_nl')===null,'any market buys what you grow');
// the hideout shows the beds, the seed chest and the notebook
w.Math.random=()=>0.99; P.enterBase(); w.Math.random=rnd; const bb=$('base-body');
assert(/The grow/.test(bb.textContent)&&/Breeder’s notebook: 1 of 7 strains bred/.test(bb.textContent)&&/Jack Herer/.test(bb.textContent)&&/landrace is a local variety/.test(bb.textContent),'the grow and its notebook');
$('seed-0').value='afghani'; bb.querySelector('[data-key=pl0]').click(); assert(L.base.grow.beds[0]&&L.base.grow.beds[0].s==='afghani','plant from the hideout');
assert(/Growing: ready in 6 days/.test($('base-body').textContent),'the bed says when it is ready');
const lg=JSON.parse(w.localStorage.getItem('pillageTheReefer.legacy')); assert(lg.base.grow.seeds.nl&&lg.base.grow.beds[0].s==='afghani'&&lg.base.bales.g_nl===6,'the grow is saved with the hideout');
P.leaveBase(true);
w.dispatchEvent(new w.Event('pagehide')); const s6=JSON.parse(w.localStorage.getItem('pillageTheReefer.v1'));
assert(s6.flags.r6&&Number.isFinite(s6.food)&&s6.record,'provisions and the record are saved');
assert.equal(errors.length,0,String(errors));
console.log('pillage ok');
process.exit(0);
