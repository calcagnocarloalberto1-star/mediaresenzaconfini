(function () {
  'use strict';
  var PAGE_SIZE = 6;
  var grid = document.getElementById('latest-grid');
  if (!grid) return;
  var navs = Array.prototype.slice.call(document.querySelectorAll('.latest-nav'));
  if (!navs.length) return;

  var articoli = null;
  var pagina = 0;

  function tronca(s, n) {
    if (!s) return '';
    return s.length > n ? s.slice(0, n).replace(/\s+\S*$/, '') + '…' : s;
  }

  function escHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function renderPagina() {
    var tot = articoli.length;
    var pagineTot = Math.max(1, Math.ceil(tot / PAGE_SIZE));
    var inizio = pagina * PAGE_SIZE;
    var blocco = articoli.slice(inizio, inizio + PAGE_SIZE);

    grid.innerHTML = blocco.map(function (a) {
      return '<div class="card">' +
        '<div class="eyebrow">' + escHtml(a.categoria) + '</div>' +
        '<h3><a href="' + escHtml(a.url) + '">' + escHtml(a.titolo) + '</a></h3>' +
        '<div class="meta">' + escHtml(a.data) + '</div>' +
        '<p>' + escHtml(tronca(a.estratto, 200)) + '</p>' +
        '</div>';
    }).join('');

    navs.forEach(function (nav) {
      nav.hidden = pagineTot <= 1;
      var prev = nav.querySelector('.latest-nav-prev');
      var next = nav.querySelector('.latest-nav-next');
      var label = nav.querySelector('.latest-nav-page');
      if (prev) prev.disabled = pagina === 0;
      if (next) next.disabled = pagina >= pagineTot - 1;
      if (label) label.textContent = 'Pagina ' + (pagina + 1) + ' di ' + pagineTot;
    });
  }

  function vai(delta) {
    if (!articoli) return;
    var pagineTot = Math.max(1, Math.ceil(articoli.length / PAGE_SIZE));
    var nuova = pagina + delta;
    if (nuova < 0 || nuova >= pagineTot) return;
    pagina = nuova;
    renderPagina();
    var sezione = document.getElementById('ultimi-articoli');
    if (sezione) {
      sezione.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  navs.forEach(function (nav) {
    var prev = nav.querySelector('.latest-nav-prev');
    var next = nav.querySelector('.latest-nav-next');
    if (prev) prev.addEventListener('click', function () { vai(-1); });
    if (next) next.addEventListener('click', function () { vai(1); });
  });

  fetch('/static/articles.json')
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function (data) {
      if (!Array.isArray(data) || !data.length) return;
      articoli = data;
      pagina = 0;
      renderPagina();
    })
    .catch(function () { /* restano visibili i sei articoli statici della build */ });
})();
