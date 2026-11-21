// Place map: the dispensaries and stores a page lists, on a map you can zoom, with the closest ones listed beside it.
// Leaflet and its pin grouping (assets/vendor) are served from this site. The only outside requests are the
// OpenStreetMap map pictures. A location you share stays in this page: nothing is stored and nothing is sent.
//
// Markup (built by build_locations.py's template and build_world.py):
//   <section class="placemap" hidden> ... .pm-map, .pm-list, .pm-head, .pm-count, .pm-status, optional button.pm-locate
// Pages with a table of stores add data-table="<table id>" (rows carry data-lat, data-lon, data-sub) and
// data-input="<search box id>"; the map follows the table's search. Other pages call PlaceMap.create() themselves.
(function () {
  'use strict';
  var TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  var still = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  var PIN = null;
  function ok() { return !!(window.L && window.L.markerClusterGroup); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function km(a, b) {
    var t = Math.PI / 180, dLat = (b[0] - a[0]) * t, dLon = (b[1] - a[1]) * t;
    var x = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(a[0] * t) * Math.cos(b[0] * t) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * 6371 * Math.asin(Math.sqrt(Math.min(1, x)));
  }

  function create(root, opts) {
    opts = opts || {};
    PIN = PIN || L.divIcon({ className: 'pm-pin', iconSize: [20, 20], iconAnchor: [10, 10], popupAnchor: [0, -8] });
    var unit = opts.unit === 'mi' ? 'mi' : 'km', noun = opts.noun || ['place', 'places'];
    var pick = function (sel) { return root.querySelector(sel); };
    var mapEl = pick('.pm-map'), list = pick('.pm-list'), head = pick('.pm-head'), count = pick('.pm-count'), status = pick('.pm-status'), locBtn = pick('.pm-locate');
    root.hidden = false;
    if (locBtn) locBtn.hidden = !navigator.geolocation;

    var map = L.map(mapEl, { scrollWheelZoom: false, zoomAnimation: !still, fadeAnimation: !still, markerZoomAnimation: !still })
      .setView(opts.center || [40, -83], opts.zoom || 6);
    // The page keeps scrolling over the map until the map is used; then the wheel zooms.
    map.on('click focus', function () { map.scrollWheelZoom.enable(); });
    mapEl.addEventListener('mouseleave', function () { map.scrollWheelZoom.disable(); });
    L.tileLayer(TILES, { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
    map.attributionControl.setPrefix('<a href="https://leafletjs.com/">Leaflet</a>');
    var cluster = L.markerClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 45, chunkedLoading: true, disableClusteringAtZoom: 16,
      animate: !still, spiderfyOnMaxZoom: true });
    map.addLayer(cluster);
    var youLayer = L.layerGroup().addTo(map);
    var pts = [], cache = {}, from = null, missing = 0, picked = null, timer = null;

    function dist(p) { var d = km(from || [map.getCenter().lat, map.getCenter().lng], [p.lat, p.lon]); return unit === 'mi' ? d * 0.621371 : d; }
    function fmt(d) { return (d < 10 ? d.toFixed(1) : Math.round(d).toLocaleString()) + ' ' + unit; }
    function acts(p) {
      var b = '';
      if (p.dir) b += '<a href="' + esc(p.dir) + '" target="_blank" rel="noopener">Directions</a>';
      if (p.tel) b += '<a href="tel:' + esc(p.tel) + '">Call ' + esc(p.phone || '') + '</a>';
      if (p.more) b += '<a href="' + esc(p.more) + '">' + esc(p.moreLabel || 'Details') + '</a>';
      return b;
    }
    function popup(p) {
      return '<div class="pm-pop"><strong>' + esc(p.name) + '</strong>' + (p.sub ? '<br><span>' + esc(p.sub) + '</span>' : '') +
        (p.note ? '<br><span class="pm-pnote">' + esc(p.note) + '</span>' : '') + '<p class="pm-acts">' + acts(p) + '</p></div>';
    }
    function marker(p) {
      // A small round pin; Leaflet makes it a focusable button named by its title, so Tab and Enter open it too.
      var m = L.marker([p.lat, p.lon], { icon: PIN, title: p.name, riseOnHover: true });
      m.bindPopup(function () { return popup(m.place); }, { maxWidth: 280 });
      return m;
    }

    function renderList() {
      if (!list) return;
      var bounds = map.getBounds().pad(0.05), hits = pts.filter(function (p) { return bounds.contains([p.lat, p.lon]); });
      var widened = hits.length < Math.min(8, pts.length);
      if (widened) hits = pts.slice();
      hits.forEach(function (p) { p.d = dist(p); });
      hits.sort(function (a, b) { return a.d - b.d; });
      var total = hits.length, cap = widened ? 25 : 40;
      hits = hits.slice(0, cap);
      if (head) head.textContent = from ? 'Closest to you' : 'Closest to the middle of the map';
      var miss = missing ? ' ' + missing.toLocaleString() + ' more ' + (missing === 1 ? 'has' : 'have') + ' no map point and ' + (missing === 1 ? 'is' : 'are') + ' only in the list below.' : '';
      if (count) count.textContent = (!pts.length ? 'No ' + noun[1] + ' with a map point match.'
        : widened ? 'Few ' + noun[1] + ' are in view, so these are the closest of all ' + pts.length.toLocaleString() + ' on the map.'
        : total > hits.length ? 'The ' + hits.length + ' closest of ' + total.toLocaleString() + ' ' + noun[1] + ' in view.'
        : total + ' ' + (total === 1 ? noun[0] : noun[1]) + ' in view.') + miss;
      var focused = document.activeElement && list.contains(document.activeElement) && document.activeElement.getAttribute('data-id');
      list.innerHTML = hits.map(function (p) {
        return '<li class="pm-hit"><button type="button" class="pm-name" data-id="' + esc(p.id) + '" aria-pressed="' + (picked === p.id) + '">' + esc(p.name) +
          '<span class="pm-vh"> — show on the map</span></button><span class="pm-sub">' + (p.sub ? esc(p.sub) + ' · ' : '') + fmt(p.d) +
          (from ? ' from you' : '') + '</span><span class="pm-acts">' + acts(p) + '</span></li>';
      }).join('');
      if (focused) { var again = list.querySelector('[data-id="' + focused.replace(/"/g, '') + '"]'); if (again) again.focus({ preventScroll: true }); }
    }
    function mark() {
      if (list) [].forEach.call(list.querySelectorAll('.pm-name'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-id') === picked)); });
    }
    function soon() { clearTimeout(timer); timer = setTimeout(renderList, 60); }

    function fit() {
      if (!pts.length) return;
      map.invalidateSize({ pan: false });
      var b = L.latLngBounds(pts.map(function (p) { return [p.lat, p.lon]; }));
      map.fitBounds(b.pad(0.08), { maxZoom: 14, animate: !still });
    }

    // points: [{id, lat, lon, name, sub, phone, tel, dir, more, moreLabel, note}]; o.fit moves the map to show them all;
    // o.missing counts matching places that have no map point.
    function set(points, o) {
      o = o || {};
      pts = points.filter(function (p) { return typeof p.lat === 'number' && typeof p.lon === 'number' && isFinite(p.lat) && isFinite(p.lon); });
      missing = (o.missing || 0) + (points.length - pts.length);
      var markers = pts.map(function (p) { var m = cache[p.id] || (cache[p.id] = marker(p)); m.place = p; p.marker = m; return m; });
      cluster.clearLayers();
      cluster.addLayers(markers);
      if (o.fit) fit();
      renderList();
    }
    function show(id) {
      var p = pts.filter(function (x) { return x.id === id; })[0];
      if (!p) return;
      picked = id;
      mark();
      // Zoom in just far enough for the pin to stand alone (out of its group), center it, then open it.
      var m = p.marker, z = map.getZoom(), parent = m.__parent;
      var target = Math.min(Math.max(z, parent && parent._zoom != null ? parent._zoom + 1 : z), cluster.options.disableClusteringAtZoom);
      var done = false;
      function open(tries) {
        if (done) return;
        if (m._icon && m._map) { done = true; m.openPopup(); } else if (tries < 25) setTimeout(function () { open(tries + 1); }, 60);
      }
      if (target === z && m._icon && map.getBounds().contains(m.getLatLng())) { open(0); return; }
      map.once('moveend', function () { open(0); });
      setTimeout(function () { open(0); }, 900);
      map.setView(m.getLatLng(), target, { animate: !still });
    }
    function near(at, zoom) {
      from = at;
      youLayer.clearLayers();
      L.circleMarker(at, { radius: 9, color: '#ffffff', weight: 3, fillColor: '#c2410c', fillOpacity: 1, interactive: false }).addTo(youLayer);
      map.setView(at, zoom || 11, { animate: !still });
      renderList();
    }
    function clearNear() { from = null; youLayer.clearLayers(); renderList(); }

    map.on('moveend', soon);
    map.on('popupopen', function (e) { var m = e.popup._source; if (m && m.place) { picked = m.place.id; mark(); } });
    map.on('popupclose', function (e) { var m = e.popup._source; if (m && m.place && m.place.id === picked) { picked = null; mark(); } });
    if (list) list.addEventListener('click', function (e) {
      var b = e.target.closest ? e.target.closest('.pm-name') : null;
      if (b) show(b.getAttribute('data-id'));
    });
    if (locBtn) locBtn.addEventListener('click', function () {
      if (status) status.textContent = 'Finding where you are…';
      navigator.geolocation.getCurrentPosition(function (pos) {
        near([pos.coords.latitude, pos.coords.longitude]);
        if (status) status.textContent = 'Showing the ' + noun[1] + ' closest to you. Your location stays in this page.';
      }, function () {
        if (status) status.textContent = 'Your location was not shared. Zoom the map or use the search instead.';
      }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 });
    });
    // Leaflet sizes the map when it is created; a map that starts hidden or in a resized column needs a nudge.
    setTimeout(function () { map.invalidateSize(); }, 0);
    return { map: map, set: set, show: show, near: near, clearNear: clearNear, fit: fit };
  }

  // A page whose stores are in a table: every row with data-lat and data-lon becomes a pin, and the table's
  // search box narrows the pins as it narrows the rows.
  function table(root) {
    var t = document.getElementById(root.getAttribute('data-table'));
    if (!t || !t.tBodies[0]) return null;
    var input = document.getElementById(root.getAttribute('data-input') || '');
    var rows = [].slice.call(t.tBodies[0].rows);
    var pm = create(root, { unit: root.getAttribute('data-unit') || 'km', noun: (root.getAttribute('data-noun') || 'store,stores').split(',') });
    var all = rows.map(function (r, i) {
      if (!r.id) r.id = t.id + '-' + (i + 1);
      var la = parseFloat(r.getAttribute('data-lat')), lo = parseFloat(r.getAttribute('data-lon'));
      var name = (r.cells[0] ? r.cells[0].textContent : '').trim();
      return { id: r.id, row: r, lat: la, lon: lo, name: name, sub: r.getAttribute('data-sub') || '',
        dir: isFinite(la) && isFinite(lo) ? 'https://www.google.com/maps/dir/?api=1&destination=' + la + ',' + lo : '',
        more: '#' + r.id, moreLabel: 'See it in the table' };
    });
    function update(fit) { pm.set(all.filter(function (p) { return !p.row.hidden; }), { fit: fit }); }
    update(true);
    var wait;
    if (input) input.addEventListener('input', function () { clearTimeout(wait); wait = setTimeout(function () { update(true); }, 250); });
    return pm;
  }

  function start() {
    if (!ok()) return;
    [].forEach.call(document.querySelectorAll('section.placemap[data-table]'), function (root) {
      try { table(root); } catch (e) { root.hidden = true; }
    });
  }
  window.PlaceMap = { ok: ok, create: create, table: table };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
