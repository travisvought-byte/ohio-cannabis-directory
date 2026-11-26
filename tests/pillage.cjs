// Pillage the Reefer (November 26, 2026): the pirate game at /pillage/. Every sea links up, every port and dig site
// sits in open water a ship can reach, trade routes the characters recommend actually pay, delivery requests can't be
// filled at the port that asks, levels climb, every fight can end, and a new game boots, sails, fights and saves cleanly.
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
$('btn-new').click(); $('note-ok').click();
assert($('dlg-port').open,'starts docked at Tortuga'); assert.equal(P.state.xp,25,'first visit earns renown');
$('set-sail').click(); for(let i=0;i<300;i++) P.step(1/30);
const S=P.state,n={kind:'merchant',tier:1,name:'the Test',captain:'X',cool:0,x:S.x+5,y:S.y,route:[[0,0]],leg:0};
P.encounter(n); [...$('enc-body').querySelectorAll('.choice')].find(b=>/Attack/.test(b.textContent)).click();
for(let i=0;i<30&&$('enc-body').querySelector('.choice');i++) $('enc-body').querySelector('.choice').click();
assert(/strikes her colours|surrenders|Your ship is beaten/.test($('enc-text').textContent),'the fight ends');
$('enc-body').querySelector('.primary').click(); assert(!$('dlg-encounter').open);
w.dispatchEvent(new w.Event('pagehide'));
const saved=JSON.parse(w.localStorage.getItem('pillageTheReefer.v1')); assert.equal(saved.xp,S.xp,'renown is saved');
assert.equal(errors.length,0,String(errors));
console.log('pillage ok');
process.exit(0);
