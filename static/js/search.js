(function () {
  "use strict";

  var ROOT = (function () {
    var el = document.querySelector('link[rel="stylesheet"][href*="static/css/style.css"]');
    if (!el) return '/';
    return el.getAttribute('href').replace('static/css/style.css', '');
  })();

  var input = document.getElementById('search-q');
  var resultsEl = document.getElementById('search-results');
  var metaEl = document.getElementById('search-meta');
  if (!input || !resultsEl) return;

  var INDEX_URL = ROOT + 'static/search-index.json';
  var indexData = null;
  var indexPromise = fetch(INDEX_URL).then(function (r) {
    return r.ok ? r.json() : Promise.reject(r.status);
  }).then(function (data) {
    indexData = data;
    return data;
  }).catch(function () {
    if (metaEl) metaEl.textContent = 'Indice di ricerca non disponibile al momento. Riprova più tardi.';
    return [];
  });

  function normalize(s) {
    return (s || '')
      .toString()
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .toLowerCase();
  }

  function tokenize(q) {
    return normalize(q).split(/[^a-z0-9]+/).filter(function (t) { return t.length >= 2; });
  }

  function escapeHtml(s) {
    return (s || '').replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function scoreEntry(entry, tokens, normTitle, normExcerpt) {
    var score = 0;
    for (var i = 0; i < tokens.length; i++) {
      var t = tokens[i];
      var ti = normTitle.indexOf(t);
      if (ti !== -1) {
        score += 5;
        if (ti === 0 || normTitle.charAt(ti - 1) === ' ') score += 2;
      }
      if (normExcerpt.indexOf(t) !== -1) score += 1;
    }
    return score;
  }

  function formatDate(d) {
    if (!d) return '';
    var parts = d.split('-');
    if (parts.length !== 3) return d;
    return parts[2] + '/' + parts[1] + '/' + parts[0];
  }

  function render(query, data) {
    var tokens = tokenize(query);
    resultsEl.innerHTML = '';

    if (!tokens.length) {
      if (metaEl) metaEl.textContent = data.length ? ('Digita una parola per cercare tra ' + data.length + ' contenuti del sito.') : 'Caricamento indice…';
      return;
    }

    var scored = [];
    for (var i = 0; i < data.length; i++) {
      var e = data[i];
      var nt = normalize(e.t);
      var ne = normalize(e.e);
      var s = scoreEntry(e, tokens, nt, ne);
      if (s > 0) scored.push({ e: e, s: s });
    }
    scored.sort(function (a, b) {
      if (b.s !== a.s) return b.s - a.s;
      return (b.e.d || '').localeCompare(a.e.d || '');
    });

    if (metaEl) {
      metaEl.textContent = scored.length
        ? (scored.length + (scored.length === 1 ? ' risultato per "' : ' risultati per "') + query + '"')
        : ('Nessun risultato per "' + query + '". Prova con un\'altra parola.');
    }

    var frag = document.createDocumentFragment();
    var max = 60;
    for (var j = 0; j < Math.min(scored.length, max); j++) {
      var item = scored[j].e;
      var card = document.createElement('div');
      card.className = 'card';
      var dateHtml = item.d ? '<div class="meta">' + escapeHtml(formatDate(item.d)) + '</div>' : '';
      card.innerHTML =
        '<div class="eyebrow">' + escapeHtml(item.c || 'ADR') + '</div>' +
        '<h3><a href="' + ROOT.replace(/\/$/, '') + item.u + '">' + escapeHtml(item.t) + '</a></h3>' +
        dateHtml +
        '<p>' + escapeHtml(item.e) + '</p>';
      frag.appendChild(card);
    }
    resultsEl.appendChild(frag);

    if (scored.length > max && metaEl) {
      metaEl.textContent += ' — mostrati i primi ' + max + '.';
    }
  }

  var debounceTimer = null;
  function scheduleSearch() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      var q = input.value.trim();
      var url = new URL(window.location.href);
      if (q) url.searchParams.set('q', q); else url.searchParams.delete('q');
      window.history.replaceState(null, '', url.toString());
      indexPromise.then(function (data) { render(q, data); });
    }, 150);
  }

  input.addEventListener('input', scheduleSearch);
  var form = input.closest('form');
  if (form) form.addEventListener('submit', function (ev) { ev.preventDefault(); scheduleSearch(); });

  var initialQ = new URL(window.location.href).searchParams.get('q') || '';
  if (initialQ) input.value = initialQ;
  indexPromise.then(function (data) { render(input.value.trim(), data); });
})();
