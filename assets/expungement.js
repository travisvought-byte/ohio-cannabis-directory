/* Route suggestions only: no personal case data, storage or requests. */
(function () {
  'use strict';
  var routes = {
    marijuana: ['marijuana', 'Read the marijuana-specific route first. Check the exact offense subsection and whether the disposition predates March 20, 2026.'],
    general: ['general', 'Review the general adult-conviction route, then check the waiting periods and exclusions with legal help.'],
    nonconviction: ['nonconviction', 'Read the nonconviction route. Dismissed and no-bill cases have different rules.'],
    special: ['special', 'Start with individual legal review for this type of record or an unclear case.']
  };
  var select = document.getElementById('case-route');
  document.getElementById('finder').hidden = false;
  select.addEventListener('change', function () {
    var route = routes[select.value];
    document.getElementById('route-result').textContent = route ? route[1] : 'Choose a description to see the next section to read.';
    var link = document.getElementById('route-link');
    link.href = '#' + (route ? route[0] : 'routes');
    link.textContent = route ? 'Read this starting route →' : 'Review all routes';
  });
  function reveal(hash) {
    if (!hash || hash.charAt(0) !== '#') return;
    var target = document.getElementById(hash.slice(1));
    if (!target) return;
    for (var parent = target.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === 'DETAILS') parent.open = true;
    }
  }
  document.addEventListener('click', function (event) {
    var link = event.target.closest('a[href^="#"]');
    if (link) reveal(link.getAttribute('href'));
  });
  window.addEventListener('hashchange', function () { reveal(window.location.hash); });
  reveal(window.location.hash);
  var print = document.getElementById('print-guide');
  print.hidden = false;
  print.addEventListener('click', function () { window.print(); });
})();
