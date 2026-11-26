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
for(const kind of ['merchant','pirate','boss']) for(const t of [undefined,0,1,2,3,9]){ const f=E.foe(kind,t); assert(Number.isFinite(f.hull)&&Number.isFinite(f.fire),'foe stats are numbers'); }
assert(EV.sea.length>=10&&EV.port.length>=5,'surprises at sea and in port');
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
$('set-sail').click(); P.dock('tortuga'); S.gold=10000; S.cargo={}; S.mk={};
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
  assert.equal(S.cargo.kraken,2,'the smuggler’s hold keeps its kraken'); assert(!S.cargo.brick&&S.cargo.tangerine===2,'they take the open hold'); assert.equal(S.gold,g0-Math.floor(g0/3),'and a third of the gold');
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
assert.equal(errors.length,0,String(errors));
console.log('pillage ok');
process.exit(0);
