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
    prepareIndex(data);
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

  // Pre-normalize title/excerpt/category once per entry so we don't redo it on every keystroke.
  function prepareIndex(data) {
    if (data._prepared) return;
    for (var i = 0; i < data.length; i++) {
      var e = data[i];
      e._nt = normalize(e.t);
      e._ne = normalize(e.e);
      e._nc = normalize(e.c || '');
    }
    data._prepared = true;
  }

  function countOccurrences(haystack, needle) {
    if (!needle) return 0;
    var count = 0, pos = 0;
    while (true) {
      var idx = haystack.indexOf(needle, pos);
      if (idx === -1) break;
      count++;
      pos = idx + needle.length;
    }
    return count;
  }

  // Lightweight inverse-document-frequency: rare query words carry a lot more
  // weight than words that show up in most of the site (e.g. "mediazione",
  // which is the core topic and would otherwise swamp every other signal).
  function buildIdf(data, tokens) {
    var idf = {};
    for (var i = 0; i < tokens.length; i++) {
      var t = tokens[i];
      if (idf[t] !== undefined) continue;
      var df = 0;
      for (var k = 0; k < data.length; k++) {
        if (data[k]._nt.indexOf(t) !== -1 || data[k]._ne.indexOf(t) !== -1) df++;
      }
      idf[t] = Math.log((data.length + 1) / (df + 1)) + 1;
    }
    return idf;
  }

  function scoreEntry(entry, tokens, idfMap, fullPhrase) {
    var score = 0;
    var nt = entry._nt, ne = entry._ne, nc = entry._nc;
    for (var i = 0; i < tokens.length; i++) {
      var t = tokens[i];
      var w = idfMap[t] || 1;
      var titleCount = countOccurrences(nt, t);
      if (titleCount > 0) {
        score += w * 4 * Math.min(titleCount, 3);
        var firstIdx = nt.indexOf(t);
        if (firstIdx === 0 || nt.charAt(firstIdx - 1) === ' ') score += w * 2;
      }
      var excerptCount = countOccurrences(ne, t);
      if (excerptCount > 0) score += w * Math.min(excerptCount, 5);
      if (nc.indexOf(t) !== -1) score += w * 3;
    }
    if (tokens.length > 1 && fullPhrase) {
      if (nt.indexOf(fullPhrase) !== -1) score += 20;
      else if (ne.indexOf(fullPhrase) !== -1) score += 8;
    }
    return score;
  }

  // Wraps matched query terms in <mark> so results visibly show *why* they matched,
  // instead of looking like a generic reverse-chronological article list.
  function highlight(original, normalizedHay, tokens) {
    original = original || '';
    if (!tokens.length) return escapeHtml(original);
    var ranges = [];
    for (var i = 0; i < tokens.length; i++) {
      var t = tokens[i];
      var pos = 0;
      while (true) {
        var idx = normalizedHay.indexOf(t, pos);
        if (idx === -1) break;
        ranges.push([idx, idx + t.length]);
        pos = idx + t.length;
      }
    }
    if (!ranges.length) return escapeHtml(original);
    ranges.sort(function (a, b) { return a[0] - b[0]; });
    var merged = [ranges[0]];
    for (var i = 1; i < ranges.length; i++) {
      var last = merged[merged.length - 1];
      if (ranges[i][0] <= last[1]) last[1] = Math.max(last[1], ranges[i][1]);
      else merged.push(ranges[i]);
    }
    var out = '';
    var cursor = 0;
    for (var i = 0; i < merged.length; i++) {
      var r = merged[i];
      if (r[0] >= original.length) break;
      var end = Math.min(r[1], original.length);
      out += escapeHtml(original.slice(cursor, r[0]));
      out += '<mark>' + escapeHtml(original.slice(r[0], end)) + '</mark>';
      cursor = end;
    }
    out += escapeHtml(original.slice(cursor));
    return out;
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

    prepareIndex(data);
    var idfMap = buildIdf(data, tokens);
    var fullPhrase = tokens.join(' ');

    var scored = [];
    for (var i = 0; i < data.length; i++) {
      var e = data[i];
      var s = scoreEntry(e, tokens, idfMap, fullPhrase);
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
      var titleHtml = highlight(item.t, item._nt, tokens);
      var excerptHtml = highlight(item.e, item._ne, tokens);
      card.innerHTML =
        '<div class="eyebrow">' + escapeHtml(item.c || 'ADR') + '</div>' +
        '<h3><a href="' + ROOT.replace(/\/$/, '') + item.u + '">' + titleHtml + '</a></h3>' +
        dateHtml +
        '<p>' + excerptHtml + '</p>';
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
