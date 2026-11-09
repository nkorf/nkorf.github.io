// Sidebar behaviour: collapse on narrow screens, highlight the section in
// view, and filter the publications list.
(function () {
  'use strict';

  var wide = window.matchMedia('(min-width: 1024px)');
  var disclosures = document.querySelectorAll('details.nk-disclosure');
  function syncDisclosure() {
    disclosures.forEach(function (d) { d.open = wide.matches; });
  }
  syncDisclosure();
  wide.addEventListener('change', syncDisclosure);

  var links = Array.prototype.slice.call(
    document.querySelectorAll('.nk-sidebar a[href^="#"]'));
  var targets = links.map(function (a) {
    return document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)));
  });

  function spy() {
    var line = window.innerHeight * 0.3;
    var current = -1;
    targets.forEach(function (t, i) {
      if (t && t.offsetParent !== null && t.getBoundingClientRect().top <= line) current = i;
    });
    links.forEach(function (a, i) { a.classList.toggle('is-active', i === current); });
  }
  window.addEventListener('scroll', spy, { passive: true });
  spy();

  // On narrow screens, close the disclosure after following a link.
  links.forEach(function (a) {
    a.addEventListener('click', function () {
      if (!wide.matches) disclosures.forEach(function (d) { d.open = false; });
    });
  });

  var query = document.getElementById('nk-pub-filter');
  if (!query) return;
  var cabs = document.getElementById('nk-pub-cabs');
  var status = document.getElementById('nk-pub-status');
  var pubs = Array.prototype.slice.call(document.querySelectorAll('.nk-pub'));
  var sections = Array.prototype.slice.call(document.querySelectorAll('.nk-pub-section'));

  function applyFilter() {
    var terms = query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    var onlyCabs = cabs && cabs.checked;
    var shown = 0;
    pubs.forEach(function (li) {
      var text = li.getAttribute('data-text') || '';
      var ok = terms.every(function (w) { return text.indexOf(w) !== -1; }) &&
        (!onlyCabs || li.getAttribute('data-cabs'));
      li.hidden = !ok;
      if (ok) shown++;
    });
    sections.forEach(function (s) {
      var n = s.querySelectorAll('.nk-pub:not([hidden])').length;
      s.hidden = n === 0;
      var counts = document.querySelectorAll(
        '.nk-sidebar a[href="#' + s.id + '"] .nk-count, #' + s.id + ' > h2 .nk-count');
      counts.forEach(function (c) { c.textContent = n; });
      var link = document.querySelector('.nk-sidebar a[href="#' + s.id + '"]');
      if (link) link.classList.toggle('is-empty', n === 0);
    });
    status.textContent = (terms.length || onlyCabs) ? shown + ' of ' + pubs.length + ' shown' : '';
    spy();
  }
  query.addEventListener('input', applyFilter);
  if (cabs) cabs.addEventListener('change', applyFilter);
})();
