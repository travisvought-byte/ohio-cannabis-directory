/* Aggregate actions only: no search text, coordinates, form answers or contact values. */
(function () {
  'use strict';
  var page = location.pathname.split('/').pop() || 'index.html';
  window.goatcounter = window.goatcounter || {};
  window.goatcounter.path = function () { return location.pathname; };
  function track(action) {
    if (window.goatcounter && typeof window.goatcounter.count === 'function')
      window.goatcounter.count({path: 'action:' + page + ':' + action, title: action, event: true, referrer: ''});
  }
  window.directoryTrack = track;
  document.addEventListener('click', function (e) {
    var el = e.target.closest('a,button'); if (!el) return;
    var action = el.dataset.track;
    if (!action && el.tagName === 'A') {
      var raw = el.getAttribute('href') || '';
      if (raw.indexOf('mailto:') === 0) action = 'email-contact';
      else if (raw.indexOf('tel:') === 0) action = 'phone-contact';
      else { try {
        var u = new URL(raw, location.href);
        if (/\.(pdf|csv|json|xlsx)$/.test(u.pathname)) action = 'download:' + u.pathname.split('/').pop();
        else if (u.origin !== location.origin) action = 'outbound:' + u.hostname;
        else if (!raw.startsWith('#')) action = 'navigate:' + (u.pathname.split('/').pop() || 'index.html');
      } catch (_) {} }
    }
    if (!action && el.tagName === 'BUTTON') action = ({dl:'download-results',share:'share-search',near:'distance-sort'})[el.id] || (el.dataset.cat ? 'category-filter' : null);
    if (action) track(action);
  });
  var timer;
  document.addEventListener('input', function (e) {
    if (!['q','search'].includes(e.target.id)) return;
    clearTimeout(timer); timer = setTimeout(function () { track('search-used');
      var results=document.getElementById('results');
      if(results && (results.children.length===0 || /Nothing matches|No matches|No results/i.test(results.textContent))) track('search-no-results');
    },1500);
  });
  document.addEventListener('change',function(e){if(e.target.tagName==='SELECT' && !e.target.closest('#assessment-form'))track('filter-changed');});
  if (!document.querySelector('script[data-goatcounter]')) {
    var script=document.createElement('script');script.async=true;script.src='https://gc.zgo.at/count.js';script.dataset.goatcounter='https://travisvought.goatcounter.com/count';document.head.appendChild(script);
  }
})();
