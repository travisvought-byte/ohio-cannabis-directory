/* Aggregate actions only. Never send searches, worksheet answers, coordinates or URL queries. */
(function () {
  'use strict';
  var page = location.pathname.split('/').pop() || 'index.html', pending = [];
  window.goatcounter = window.goatcounter || {};
  window.goatcounter.path = function () { return location.pathname; };
  window.goatcounter.referrer = function () {
    try { var u = new URL(document.referrer); return u.origin + u.pathname; } catch (_) { return ''; }
  };
  function track(action) {
    var event = {path:'action:' + page + ':' + action, title:action, event:true, referrer:''};
    if (typeof window.goatcounter.count === 'function') window.goatcounter.count(event);
    else if (pending.length < 20) pending.push(event);
  }
  window.directoryTrack = track;
  function loadCounter() {
    if (document.querySelector('script[data-goatcounter]')) return;
    var script = document.createElement('script'); script.async=true; script.src='https://gc.zgo.at/count.js';
    script.dataset.goatcounter='https://travisvought.goatcounter.com/count';
    script.onload=function(){if(typeof window.goatcounter.count==='function'){pending.forEach(function(e){window.goatcounter.count(e);});pending=[];}};
    document.head.appendChild(script);
  }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded',loadCounter,{once:true}); else loadCounter();
  document.addEventListener('click',function(e){
    var el=e.target.closest('a,button');if(!el)return;
    var action=el.dataset.track;
    if(!action&&el.tagName==='A'){
      var raw=el.getAttribute('href')||'';
      if(raw.startsWith('mailto:'))action='email-contact';
      else if(raw.startsWith('tel:'))action='phone-contact';
      else if(!raw.startsWith('#') && !raw.startsWith('blob:')){try{var u=new URL(raw,location.href);
        if(!['http:','https:'].includes(u.protocol))return;
        if(/\.(pdf|csv|json|xlsx)$/.test(u.pathname))action='download:'+u.pathname.split('/').pop();
        else if(u.origin!==location.origin)action='outbound:'+u.hostname;
        else action='navigate:'+(u.pathname.split('/').pop()||'index.html');
      }catch(_){}}
    }
    if(!action&&el.tagName==='BUTTON')action=({dl:'download-results',share:'share-search','state-share':'share-search',near:'distance-sort'})[el.id]||(el.dataset.cat?'category-filter':null);
    if(action)track(action);
  });
  function noResults(){
    var selectors={'index.html':'#results article','relationships.html':'#results article','ancestry.html':'#results article','locations.html':'#cards article','state.html':'#state-results article','seeds.html':'#seed-results article','knowledge.html':'article.topic'};
    var selector=selectors[page];if(!selector)return false;
    return !Array.from(document.querySelectorAll(selector)).some(function(e){return !e.closest('[hidden]')&&getComputedStyle(e).display!=='none';});
  }
  var timer;
  document.addEventListener('input',function(e){
    if(e.target.type!=='search'||e.target.closest('#assessment-form'))return;
    clearTimeout(timer);timer=setTimeout(function(){if(!e.target.value.trim())return;track('search-used');if(noResults())track('search-no-results');},1500);
  });
  document.addEventListener('change',function(e){if(e.target.tagName==='SELECT'&&e.target.closest('.controls,.filters')&&!e.target.closest('#assessment-form'))track('filter-changed');});
})();
