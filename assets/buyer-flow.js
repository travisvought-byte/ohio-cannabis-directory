const buyerSteps=[...document.querySelectorAll('[data-tool-step]')],tabs=[...document.querySelectorAll('[data-buyer-step]')];
tabs.forEach(button=>button.onclick=()=>{const n=Number(button.dataset.buyerStep);buyerSteps.forEach((s,i)=>s.hidden=i!==n);tabs.forEach((b,i)=>b.setAttribute('aria-pressed',i===n?'true':'false'));});
let labelTracked=false,supplyTracked=false;
['label-thc','label-cbd','label-amount','label-basis'].forEach(id=>document.getElementById(id).addEventListener('input',()=>{if(!labelTracked&&document.getElementById('label-result').textContent.startsWith('Labeled content')){labelTracked=true;if(window.directoryTrack)window.directoryTrack('label-calculator-used');}}));
['quantity','amount','frequency','weeks','unit'].forEach(id=>document.getElementById(id).addEventListener('input',()=>{if(!supplyTracked&&document.getElementById('estimate').textContent.startsWith('One package')){supplyTracked=true;if(window.directoryTrack)window.directoryTrack('supply-calculator-used');}}));

if(location.hash==="#ohio-basics"){tabs[2].click();document.getElementById("ohio-basics").open=true;}
