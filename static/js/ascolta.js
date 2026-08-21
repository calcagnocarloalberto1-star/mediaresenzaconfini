/* ==========================================================================
   mediaresenzaconfini — «Ascolta l'articolo»
   Lettore vocale accessibile per le pagine articolo.

   Due motori, stessa interfaccia:
     1. se la pagina dichiara un file audio  -> riproduce quel file (voce ElevenLabs)
        <link rel="alternate" type="audio/mpeg" href="/static/audio/<slug>.mp3">
     2. altrimenti -> sintesi vocale del browser (Web Speech API), gratuita e
        illimitata, disponibile su Windows, macOS, iOS, Android e Chrome/Edge.

   Non richiede alcuna libreria esterna. Nessuna richiesta di rete.
   Va incluso in fondo al <body>:  <script src="/static/js/ascolta.js" defer></script>
   ========================================================================== */
(function () {
  "use strict";

  var art = document.querySelector("article.post");
  var header = art && art.querySelector(".post-header");
  var body = art && art.querySelector(".post-body");
  if (!art || !header || !body) return;

  var hasTTS = "speechSynthesis" in window && typeof window.SpeechSynthesisUtterance === "function";
  var mp3link = document.querySelector('link[rel="alternate"][type="audio/mpeg"]');
  var mp3 = mp3link ? mp3link.getAttribute("href") : null;
  if (!mp3 && !hasTTS) return; // nessun motore disponibile: non mostriamo nulla

  var PAROLE_AL_MINUTO = 155;      // ritmo medio di lettura in italiano
  var MAX_CHUNK = 300;             // caratteri per singola pronuncia
  var CHIAVE_VELOCITA = "mrc-ascolto-velocita";

  /* ---------------------------------------------------------------- stile */
  var css = document.createElement("style");
  css.textContent = [
    ".ascolto{max-width:760px;margin:0 0 30px;border:1px solid var(--line,#e0dcd2);border-left:4px solid var(--gold,#8f7a55);border-radius:6px;background:var(--paper-alt,#f1efe9);padding:14px 18px;font-family:var(--sans,system-ui,sans-serif)}",
    ".ascolto-testa{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:.9rem;font-weight:600;color:var(--navy,#1e2c3d)}",
    ".ascolto-testa svg{flex:0 0 auto}",
    ".ascolto-durata{font-weight:400;color:var(--ink-soft,#5b6470);font-size:.83rem}",
    ".ascolto-comandi{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px}",
    ".ascolto button{font:inherit;font-size:.85rem;font-weight:600;cursor:pointer;border-radius:5px;border:1px solid var(--navy,#1e2c3d);background:var(--navy,#1e2c3d);color:#fff;padding:7px 15px;line-height:1.2}",
    ".ascolto button:hover{background:var(--gold,#8f7a55);border-color:var(--gold,#8f7a55)}",
    ".ascolto button:focus-visible{outline:3px solid var(--gold,#8f7a55);outline-offset:2px}",
    ".ascolto button[disabled]{opacity:.4;cursor:default}",
    ".ascolto button[disabled]:hover{background:var(--navy,#1e2c3d);border-color:var(--navy,#1e2c3d)}",
    ".ascolto .secondario{background:transparent;color:var(--navy,#1e2c3d)}",
    ".ascolto .secondario:hover{background:var(--navy,#1e2c3d);color:#fff}",
    ".ascolto-velocita{display:flex;align-items:center;gap:6px;margin-left:auto;font-size:.8rem;color:var(--ink-soft,#5b6470)}",
    ".ascolto-velocita select{font:inherit;font-size:.8rem;padding:4px 6px;border:1px solid var(--line,#e0dcd2);border-radius:4px;background:#fff;color:var(--ink,#22282f)}",
    ".ascolto-barra{margin-top:12px;height:6px;border-radius:3px;background:#fff;border:1px solid var(--line,#e0dcd2);overflow:hidden}",
    ".ascolto-barra i{display:block;height:100%;width:0;background:var(--gold,#8f7a55);transition:width .25s linear}",
    ".ascolto-stato{margin-top:7px;font-size:.78rem;color:var(--ink-soft,#5b6470);min-height:1.2em}",
    ".ascolto-nota{margin-top:8px;font-size:.76rem;color:var(--ink-soft,#5b6470);line-height:1.45}",
    ".mrc-in-lettura{background:rgba(143,122,85,.16);box-shadow:0 0 0 4px rgba(143,122,85,.16);border-radius:3px}",
    "@media(prefers-reduced-motion:reduce){.ascolto-barra i{transition:none}}",
    "@media(max-width:520px){.ascolto-velocita{margin-left:0;width:100%}}"
  ].join("\n");
  document.head.appendChild(css);

  /* ------------------------------------------------- costruzione della UI */
  var box = document.createElement("section");
  box.className = "ascolto";
  box.setAttribute("role", "region");
  box.setAttribute("aria-label", "Ascolta l'articolo");
  box.innerHTML =
    '<div class="ascolto-testa">' +
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M19 5a9 9 0 0 1 0 14"/>' +
      "</svg>" +
      "<span>Ascolta l'articolo</span>" +
      '<span class="ascolto-durata" data-durata></span>' +
    "</div>" +
    '<div class="ascolto-comandi">' +
      '<button type="button" data-play>Ascolta</button>' +
      '<button type="button" class="secondario" data-stop disabled>Interrompi</button>' +
      '<label class="ascolto-velocita">Velocit&agrave;' +
        '<select data-velocita aria-label="Velocit&agrave; di lettura">' +
          '<option value="0.8">0,8&times;</option>' +
          '<option value="0.9">0,9&times;</option>' +
          '<option value="1" selected>1&times;</option>' +
          '<option value="1.15">1,15&times;</option>' +
          '<option value="1.3">1,3&times;</option>' +
          '<option value="1.5">1,5&times;</option>' +
        "</select>" +
      "</label>" +
    "</div>" +
    '<div class="ascolto-barra" role="presentation"><i data-barra></i></div>' +
    '<p class="ascolto-stato" data-stato role="status" aria-live="polite"></p>';
  header.insertAdjacentElement("afterend", box);

  var bPlay = box.querySelector("[data-play]");
  var bStop = box.querySelector("[data-stop]");
  var selVel = box.querySelector("[data-velocita]");
  var barra = box.querySelector("[data-barra]");
  var stato = box.querySelector("[data-stato]");
  var durata = box.querySelector("[data-durata]");

  var velocita = parseFloat(localStorage.getItem(CHIAVE_VELOCITA) || "1") || 1;
  selVel.value = String(velocita);

  function dì(t) { stato.textContent = t; }
  function avanzamento(f) { barra.style.width = Math.max(0, Math.min(1, f)) * 100 + "%"; }

  /* ============================== MOTORE 1: file audio (voce ElevenLabs) === */
  if (mp3) {
    var au = new Audio(mp3);
    au.preload = "metadata";
    var nota = document.createElement("p");
    nota.className = "ascolto-nota";
    nota.textContent = "Lettura con voce naturale. È possibile scaricare il file audio.";
    box.appendChild(nota);

    au.addEventListener("loadedmetadata", function () {
      if (isFinite(au.duration)) durata.textContent = "· " + Math.round(au.duration / 60) + " min";
    });
    au.addEventListener("timeupdate", function () {
      if (isFinite(au.duration) && au.duration > 0) avanzamento(au.currentTime / au.duration);
    });
    au.addEventListener("ended", function () { bPlay.textContent = "Ascolta"; bStop.disabled = true; avanzamento(0); dì("Lettura terminata."); });

    bPlay.addEventListener("click", function () {
      if (au.paused) { au.playbackRate = velocita; au.play(); bPlay.textContent = "Pausa"; bStop.disabled = false; dì("In riproduzione."); }
      else { au.pause(); bPlay.textContent = "Riprendi"; dì("In pausa."); }
    });
    bStop.addEventListener("click", function () {
      au.pause(); au.currentTime = 0; bPlay.textContent = "Ascolta"; bStop.disabled = true; avanzamento(0); dì("Lettura interrotta.");
    });
    selVel.addEventListener("change", function () {
      velocita = parseFloat(selVel.value) || 1; au.playbackRate = velocita;
      try { localStorage.setItem(CHIAVE_VELOCITA, String(velocita)); } catch (e) {}
    });
    return;
  }

  /* ================== MOTORE 2: sintesi vocale del browser (Web Speech) === */
  var synth = window.speechSynthesis;

  // --- 1. estrazione del testo leggibile -----------------------------------
  // Si legge il titolo e poi i blocchi del corpo, nell'ordine.
  // Si escludono: i richiami di nota <sup>, le tabelle (annunciate a voce),
  // e tutto ciò che segue il paragrafo «Note» in fondo all'articolo.
  var segmenti = [];
  var tabelleAnnunciate = 0, stop = false;

  var h1 = art.querySelector(".post-header h1");
  if (h1) segmenti.push({ el: h1, testo: pulisci(h1), lang: null });

  percorri(body);

  if (stop) segmenti.push({ el: null, testo: "L'articolo prosegue con le note, che non vengono lette.", lang: null });
  if (!segmenti.length) { box.remove(); return; }

  // Percorre i blocchi nell'ordine in cui compaiono nella pagina.
  function percorri(contenitore) {
    var figli = contenitore.children;
    for (var i = 0; i < figli.length; i++) {
      if (stop) return;
      var el = figli[i], tag = el.tagName.toUpperCase();

      if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT") continue;

      // tabelle: il contenuto non si legge, si annuncia soltanto
      if (tag === "TABLE" || el.querySelector && el.querySelector("table") && (tag === "DIV" || tag === "FIGURE")) {
        var tab = tag === "TABLE" ? el : el.querySelector("table");
        var did = tab.querySelector("caption");
        tabelleAnnunciate++;
        segmenti.push({ el: el, testo: did ? "Segue una tabella: " + pulisci(did) + ". Il contenuto non viene letto." : "Segue una tabella, che non viene letta.", lang: null });
        continue;
      }

      if (tag === "UL" || tag === "OL") { percorri(el); continue; }

      if (/^(P|H2|H3|H4|H5|LI|BLOCKQUOTE|FIGCAPTION)$/.test(tag)) {
        var t = pulisci(el);
        if (!t) continue;
        if (/^H[2345]$/.test(tag) && /^note$/i.test(t)) { stop = true; return; }   // stop all'apparato di note
        segmenti.push({ el: el, testo: t, lang: el.getAttribute("lang") || null });
        continue;
      }

      // contenitori generici: si scende dentro
      if (el.children.length) { percorri(el); continue; }
      var tt = pulisci(el);
      if (tt) segmenti.push({ el: el, testo: tt, lang: el.getAttribute("lang") || null });
    }
  }

  function pulisci(el) {
    var c = el.cloneNode(true);
    Array.prototype.forEach.call(c.querySelectorAll("sup, .footnote-ref, script, style"), function (n) { n.remove(); });
    var t = (c.textContent || "").replace(/ /g, " ").replace(/\s+/g, " ").trim();
    return t;
  }

  // durata stimata
  var caratteri = segmenti.reduce(function (n, s) { return n + s.testo.length; }, 0);
  var minuti = Math.max(1, Math.round((caratteri / 6.2) / PAROLE_AL_MINUTO));
  durata.textContent = "· circa " + minuti + " min";

  var nota2 = document.createElement("p");
  nota2.className = "ascolto-nota";
  nota2.textContent = "Lettura con la voce del dispositivo. Si può mettere in pausa, cambiare velocità e riprendere."
    + (tabelleAnnunciate ? " Le tabelle e le note non vengono lette." : "");
  box.appendChild(nota2);

  // --- 2. suddivisione in pronunce brevi -----------------------------------
  function spezza(testo) {
    var frasi = testo.match(/[^.!?;:]+[.!?;:]*\s*/g) || [testo];
    var out = [], buf = "";
    frasi.forEach(function (f) {
      if ((buf + f).length > MAX_CHUNK && buf) { out.push(buf.trim()); buf = f; }
      else buf += f;
    });
    if (buf.trim()) out.push(buf.trim());
    return out.filter(Boolean);
  }
  var coda = [];
  segmenti.forEach(function (s, idx) {
    spezza(s.testo).forEach(function (p) { coda.push({ testo: p, seg: idx, lang: s.lang }); });
  });

  // --- 3. scelta della voce italiana ---------------------------------------
  var voce = null;
  function scegliVoce() {
    var vs = synth.getVoices() || [];
    if (!vs.length) return null;
    var it = vs.filter(function (v) { return /^it(-|_|$)/i.test(v.lang || ""); });
    if (!it.length) return null;
    var preferite = ["Alice", "Elsa", "Federica", "Google italiano", "Luca", "Cosimo", "Paolina", "Isabella", "Emma"];
    for (var p = 0; p < preferite.length; p++) {
      for (var k = 0; k < it.length; k++) if ((it[k].name || "").indexOf(preferite[p]) !== -1) return it[k];
    }
    var loc = it.filter(function (v) { return v.localService; });
    return loc[0] || it[0];
  }
  voce = scegliVoce();
  if (synth.onvoiceschanged !== undefined) {
    synth.addEventListener("voiceschanged", function () { if (!voce) voce = scegliVoce(); });
  }

  // --- 4. riproduzione ------------------------------------------------------
  var pos = 0, inLettura = false, inPausa = false, segCorrente = -1, keepAlive = null;

  function evidenzia(idx) {
    if (idx === segCorrente) return;
    if (segCorrente >= 0 && segmenti[segCorrente] && segmenti[segCorrente].el) segmenti[segCorrente].el.classList.remove("mrc-in-lettura");
    segCorrente = idx;
    var el = segmenti[idx] && segmenti[idx].el;
    if (!el) return;
    el.classList.add("mrc-in-lettura");
    var r = el.getBoundingClientRect();
    if (r.top < 90 || r.bottom > window.innerHeight - 60) {
      var ridotto = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      el.scrollIntoView({ behavior: ridotto ? "auto" : "smooth", block: "center" });
    }
  }
  function ripulisci() {
    if (segCorrente >= 0 && segmenti[segCorrente] && segmenti[segCorrente].el) segmenti[segCorrente].el.classList.remove("mrc-in-lettura");
    segCorrente = -1;
  }

  function parla() {
    if (pos >= coda.length) return fine();
    var pezzo = coda[pos];
    evidenzia(pezzo.seg);
    avanzamento(pos / coda.length);
    var u = new SpeechSynthesisUtterance(pezzo.testo);
    if (voce) u.voice = voce;
    u.lang = pezzo.lang || (voce && voce.lang) || "it-IT";
    u.rate = velocita;
    u.pitch = 1;
    u.onend = function () { if (inLettura && !inPausa) { pos++; parla(); } };
    u.onerror = function (e) {
      if (e && (e.error === "interrupted" || e.error === "canceled")) return;
      pos++; if (inLettura && !inPausa) parla();
    };
    synth.speak(u);
  }

  // Chrome interrompe la sintesi dopo ~15 secondi: si tiene sveglia la coda.
  // Il rimedio serve solo ai browser basati su Chromium; altrove darebbe scatti.
  var chromium = /Chrome|Chromium|Edg\//.test(navigator.userAgent) && !/Firefox/.test(navigator.userAgent);
  function avviaKeepAlive() {
    fermaKeepAlive();
    if (!chromium) return;
    keepAlive = setInterval(function () {
      if (!inLettura || inPausa) return;
      if (synth.speaking) { synth.pause(); synth.resume(); }
    }, 9000);
  }
  function fermaKeepAlive() { if (keepAlive) { clearInterval(keepAlive); keepAlive = null; } }

  function avvia() {
    if (!voce) voce = scegliVoce();
    synth.cancel();
    inLettura = true; inPausa = false;
    bPlay.textContent = "Pausa"; bStop.disabled = false;
    dì(voce ? "In lettura con la voce «" + voce.name + "»." : "In lettura con la voce predefinita del dispositivo.");
    avviaKeepAlive();
    parla();
  }
  function pausa() {
    inPausa = true; synth.pause();
    bPlay.textContent = "Riprendi"; dì("In pausa.");
  }
  function riprendi() {
    inPausa = false; bPlay.textContent = "Pausa"; dì("In lettura.");
    if (synth.paused) synth.resume();
    else { synth.cancel(); parla(); }   // alcuni browser non sospendono davvero: si riparte dal pezzo corrente
  }
  function ferma() {
    inLettura = false; inPausa = false; pos = 0;
    synth.cancel(); fermaKeepAlive(); ripulisci(); avanzamento(0);
    bPlay.textContent = "Ascolta"; bStop.disabled = true; dì("Lettura interrotta.");
  }
  function fine() {
    inLettura = false; inPausa = false; pos = 0;
    fermaKeepAlive(); ripulisci(); avanzamento(1);
    bPlay.textContent = "Ascolta di nuovo"; bStop.disabled = true; dì("Lettura terminata.");
    setTimeout(function () { avanzamento(0); }, 1500);
  }

  bPlay.addEventListener("click", function () {
    if (!inLettura) avvia();
    else if (inPausa) riprendi();
    else pausa();
  });
  bStop.addEventListener("click", ferma);

  selVel.addEventListener("change", function () {
    velocita = parseFloat(selVel.value) || 1;
    try { localStorage.setItem(CHIAVE_VELOCITA, String(velocita)); } catch (e) {}
    if (inLettura && !inPausa) { synth.cancel(); parla(); }   // riparte dal pezzo corrente
  });

  // se l'utente lascia la pagina, si tace (altrimenti la voce prosegue altrove)
  window.addEventListener("beforeunload", function () { try { synth.cancel(); } catch (e) {} });
  window.addEventListener("pagehide", function () { try { synth.cancel(); } catch (e) {} });
})();
