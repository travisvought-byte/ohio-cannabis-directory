// The home page picture: every word in the drawing reads left to right, for the mirrored sailor too. Run: node tests/picture-browser.cjs
const {chromium}=require('playwright'),assert=require('node:assert/strict');
(async()=>{
 const server=await require('./server.cjs')(),browser=await chromium.launch({headless:true});
 try{
  for(const width of [390,1200]){
   const page=await browser.newPage({viewport:{width,height:844}}),errors=[];
   page.on('pageerror',e=>errors.push(e.message));await page.route('**/gc.zgo.at/**',r=>r.abort());
   await page.goto(server.base+'national/index.html');
   assert.equal(await page.locator('svg.ship .sailor').count(),2,'two sailors');
   assert.equal(await page.locator('svg.ship text.cough').count(),2,'each sailor has a cough');
   // Step through the whole 9-second loop with the animation held still, and look at each word as the browser draws it.
   const shown=[0,0];
   for(let ms=0;ms<9000;ms+=250){
    const words=await page.evaluate(t=>{
     document.getAnimations().forEach(a=>{a.pause();a.currentTime=t;});
     const svg=document.querySelector('svg.ship'),box=svg.getBoundingClientRect();
     return [...svg.querySelectorAll('text')].map(el=>{const m=el.getScreenCTM(),r=el.getBoundingClientRect(),own=el.parentElement.querySelector('.sailor').getBoundingClientRect();
      return{shown:+getComputedStyle(el).opacity>.9,across:m.a,down:m.d,inside:r.left>=box.left&&r.right<=box.right&&r.top>=box.top&&r.bottom<=box.bottom,
       away:Math.abs((r.left+r.right)/2-(own.left+own.right)/2)/box.width};});},ms);
    words.forEach((w,i)=>{
     assert(w.across>0,'word '+(i+1)+' is mirrored at '+ms+'ms, '+width+'px wide');assert(w.down>0,'word '+(i+1)+' is upside down at '+ms+'ms');
     if(w.shown){shown[i]++;assert(w.inside,'word '+(i+1)+' stays inside the picture');assert(w.away<.08,'word '+(i+1)+' is beside its own sailor');}});
   }
   assert(shown[0]>0&&shown[1]>0,'both sailors cough during the loop, so the check above looked at real words');
   assert.deepEqual(errors,[]);await page.close();
  }
  console.log('PASS: home page picture at phone and desktop width: both sailors cough, and each "*cough*" reads left to right beside its own sailor.');
 }finally{await browser.close();await server.close();}
})().catch(e=>{console.error(e);process.exit(1);});
