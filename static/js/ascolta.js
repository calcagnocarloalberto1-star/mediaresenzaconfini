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
  var piste = [];
  var _l = document.querySelectorAll('link[rel="alternate"][type="audio/mpeg"]');
  for (var _i = 0; _i < _l.length; _i++) {
    var _h = _l[_i].getAttribute("href");
    if (_h) piste.push({ src: _h, dur: parseFloat(_l[_i].getAttribute("data-durata")) || 0 });
  }
  var mp3 = piste.length ? piste[0].src : null;
  if (!mp3 && !hasTTS) return; // nessun motore disponibile: non mostriamo nulla

  var PAROLE_AL_MINUTO = 155;      // ritmo medio di lettura in italiano
  var MAX_CHUNK = 420;             // si spezza solo dentro le frasi molto lunghe
  var PAUSA_FRASE = 300;           // ms di silenzio fra una frase e l'altra
  var PAUSA_PARAGRAFO = 750;       // ms fra due paragrafi
  var PAUSA_TITOLO = 950;          // ms dopo un titolo di paragrafo
  var CHIAVE_VELOCITA = "mrc-ascolto-velocita";
  var CHIAVE_VOCE = "mrc-ascolto-voce";

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
    ".ascolto-scelte{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-top:12px}",
    ".ascolto-scelte label{display:flex;align-items:center;gap:6px;font-size:.8rem;color:var(--ink-soft,#5b6470)}",
    ".ascolto-scelte select{font:inherit;font-size:.8rem;padding:4px 6px;border:1px solid var(--line,#e0dcd2);border-radius:4px;background:#fff;color:var(--ink,#22282f);max-width:220px}",
    ".ascolto-salti{display:inline-flex;gap:6px}",
    ".ascolto-salti button{padding:7px 10px;font-size:.8rem}",
    ".ascolto-barra{margin-top:12px;height:6px;border-radius:3px;background:#fff;border:1px solid var(--line,#e0dcd2);overflow:hidden}",
    ".ascolto-barra i{display:block;height:100%;width:0;background:var(--gold,#8f7a55);transition:width .25s linear}",
    ".ascolto-stato{margin-top:7px;font-size:.78rem;color:var(--ink-soft,#5b6470);min-height:1.2em}",
    ".ascolto-nota{margin-top:8px;font-size:.76rem;color:var(--ink-soft,#5b6470);line-height:1.45}",
    ".mrc-in-lettura{background:rgba(143,122,85,.16);box-shadow:0 0 0 4px rgba(143,122,85,.16);border-radius:3px}",
    "@media(prefers-reduced-motion:reduce){.ascolto-barra i{transition:none}}"
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
    "</div>" +
    '<div class="ascolto-scelte">' +
      '<label>Voce <select data-voce aria-label="Voce di lettura"></select></label>' +
      '<label>Velocit&agrave; ' +
        '<select data-velocita aria-label="Velocit&agrave; di lettura">' +
          '<option value="0.5">molto lenta</option>' +
          '<option value="0.6">0,6&times;</option>' +
          '<option value="0.7">0,7&times;</option>' +
          '<option value="0.8">0,8&times;</option>' +
          '<option value="0.9">0,9&times;</option>' +
          '<option value="1">normale</option>' +
          '<option value="1.15">1,15&times;</option>' +
          '<option value="1.3">1,3&times;</option>' +
        "</select>" +
      "</label>" +
    "</div>" +
    '<div class="ascolto-barra" role="presentation"><i data-barra></i></div>' +
    '<p class="ascolto-stato" data-stato role="status" aria-live="polite"></p>';
  header.insertAdjacentElement("afterend", box);

  var bPlay = box.querySelector("[data-play]");
  var bStop = box.querySelector("[data-stop]");
  var selVel = box.querySelector("[data-velocita]");
  var selVoce = box.querySelector("[data-voce]");
  var barra = box.querySelector("[data-barra]");
  var stato = box.querySelector("[data-stato]");
  var durata = box.querySelector("[data-durata]");

  var velocita = parseFloat(localStorage.getItem(CHIAVE_VELOCITA) || "0.8") || 0.8;
  selVel.value = String(velocita);
  if (!selVel.value) { selVel.value = "0.8"; velocita = 0.8; }

  function dì(t) { stato.textContent = t; }
  function avanzamento(f) { barra.style.width = Math.max(0, Math.min(1, f)) * 100 + "%"; }

  /* ============================== MOTORE 1: file audio (voce ElevenLabs) ===
     La pagina puo' dichiarare piu' file, che vengono riprodotti di seguito
     come un unico ascolto continuo:
       <link rel="alternate" type="audio/mpeg" href="..." data-durata="1600">
     L'attributo data-durata (secondi) e' facoltativo: serve solo a mostrare
     subito la durata complessiva e a rendere esatta la barra di avanzamento.
     -------------------------------------------------------------------- */
  if (mp3) {
    box.querySelector("[data-voce]").parentNode.remove();

    var CHIAVE_POS = "mrc-ascolto-pos:" + location.pathname;
    var au = new Audio();
    au.preload = "metadata";

    /* durate note e offset cumulativi */
    var totale = 0, noto = true, k;
    for (k = 0; k < piste.length; k++) {
      piste[k].inizio = totale;
      if (piste[k].dur > 0) totale += piste[k].dur; else noto = false;
    }
    if (!noto) totale = 0;

    var indice = 0, caricato = -1, ripresa = 0, salvato = 0;
    try { salvato = parseFloat(localStorage.getItem(CHIAVE_POS)) || 0; } catch (e) {}

    var nota = document.createElement("p");
    nota.className = "ascolto-nota";
    nota.textContent = piste.length > 1
      ? "Lettura con voce naturale, in " + piste.length + " parti che si succedono da sole."
      : "Lettura con voce naturale.";
    box.appendChild(nota);

    if (totale > 0) durata.textContent = "\u00b7 " + Math.round(totale / 60) + " min";

    function trascorso() {
      var base = piste[indice].inizio || 0;
      return base + (isFinite(au.currentTime) ? au.currentTime : 0);
    }
    function etichettaParte() {
      return piste.length > 1 ? " (parte " + (indice + 1) + " di " + piste.length + ")" : "";
    }
    function carica(n, secondi, subito) {
      indice = n;
      ripresa = Math.max(0, secondi || 0);
      if (caricato !== n) {
        au.src = piste[n].src; au.load(); caricato = n;
      } else if (au.readyState >= 1) {
        var lim = isFinite(au.duration) && au.duration > 0.4 ? au.duration - 0.3 : ripresa;
        try { au.currentTime = Math.min(ripresa, lim); } catch (e) {}
        ripresa = 0;
      }
      au.playbackRate = velocita;
      if (subito) { var pr = au.play(); if (pr && pr["catch"]) pr["catch"](function () {}); }
    }
    function vaiA(assoluti) {
      var n = 0;
      if (totale > 0) {
        for (var q = piste.length - 1; q >= 0; q--) {
          if (assoluti >= piste[q].inizio) { n = q; break; }
        }
      }
      carica(n, assoluti - (piste[n].inizio || 0), !au.paused);
    }

    au.addEventListener("loadedmetadata", function () {
      if (ripresa > 0 && isFinite(au.duration)) {
        try { au.currentTime = Math.min(ripresa, au.duration - 0.5); } catch (e) {}
        ripresa = 0;
      }
      if (totale <= 0 && piste.length === 1 && isFinite(au.duration)) {
        totale = au.duration;
        durata.textContent = "\u00b7 " + Math.round(totale / 60) + " min";
      }
    });

    var ultimoSalvataggio = 0;
    au.addEventListener("timeupdate", function () {
      var t = trascorso();
      if (totale > 0) avanzamento(t / totale);
      else if (isFinite(au.duration) && au.duration > 0) avanzamento(au.currentTime / au.duration);
      if (t - ultimoSalvataggio > 5 || t < ultimoSalvataggio) {
        ultimoSalvataggio = t;
        try { localStorage.setItem(CHIAVE_POS, String(Math.round(t))); } catch (e) {}
      }
    });

    au.addEventListener("ended", function () {
      if (indice + 1 < piste.length) {
        carica(indice + 1, 0, true);
        dì("In riproduzione" + etichettaParte() + ".");
      } else {
        bPlay.textContent = "Ascolta"; bStop.disabled = true; avanzamento(0);
        try { localStorage.removeItem(CHIAVE_POS); } catch (e) {}
        dì("Lettura terminata.");
      }
    });

    au.addEventListener("error", function () {
      dì("Non riesco a caricare l\u2019audio" + etichettaParte() + ".");
    });

    /* barra cliccabile: salto rapido dentro l'intera lettura */
    var salti = document.createElement("span");
    salti.className = "ascolto-salti";
    salti.innerHTML =
      '<button type="button" class="secondario" data-indietro aria-label="Torna indietro di 15 secondi">&minus;15 s</button>' +
      '<button type="button" class="secondario" data-avanti aria-label="Vai avanti di 30 secondi">+30 s</button>';
    bStop.parentNode.insertBefore(salti, bStop.nextSibling);
    salti.querySelector("[data-indietro]").addEventListener("click", function () {
      vaiA(Math.max(0, trascorso() - 15)); bStop.disabled = false;
      dì((au.paused ? "Indietro di 15 secondi" : "In riproduzione") + etichettaParte() + ".");
    });
    salti.querySelector("[data-avanti]").addEventListener("click", function () {
      vaiA(trascorso() + 30); bStop.disabled = false;
      dì((au.paused ? "Avanti di 30 secondi" : "In riproduzione") + etichettaParte() + ".");
    });

    var pista = barra.parentNode;
    if (totale > 0) {
      pista.style.cursor = "pointer";
      pista.setAttribute("title", "Clicca per spostarti nella lettura");
      pista.addEventListener("click", function (ev) {
        var r = pista.getBoundingClientRect();
        if (!r.width) return;
        var f = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width));
        vaiA(f * totale);
        bStop.disabled = false;
        dì((au.paused ? "Posizione impostata" : "In riproduzione") + etichettaParte() + ".");
      });
    }

    if (salvato > 30 && (totale <= 0 || salvato < totale - 30)) {
      var m = Math.floor(salvato / 60);
      dì("Ripartir\u00e0 da " + (m >= 1 ? m + " min" : Math.round(salvato) + " s") + ". Il tasto Interrompi riporta all\u2019inizio.");
      carica(0, 0, false);
      vaiA(salvato);
    } else {
      carica(0, 0, false);
    }

    bPlay.addEventListener("click", function () {
      if (au.paused) {
        au.playbackRate = velocita; au.play();
        bPlay.textContent = "Pausa"; bStop.disabled = false;
        dì("In riproduzione" + etichettaParte() + ".");
      } else {
        au.pause(); bPlay.textContent = "Riprendi"; dì("In pausa.");
      }
    });
    bStop.addEventListener("click", function () {
      au.pause();
      try { localStorage.removeItem(CHIAVE_POS); } catch (e) {}
      ultimoSalvataggio = 0;
      carica(0, 0, false);
      try { au.currentTime = 0; } catch (e) {}
      bPlay.textContent = "Ascolta"; bStop.disabled = true; avanzamento(0);
      dì("Lettura interrotta.");
    });
    selVel.addEventListener("change", function () {
      velocita = parseFloat(selVel.value) || 1; au.playbackRate = velocita;
      try { localStorage.setItem(CHIAVE_VELOCITA, String(velocita)); } catch (e) {}
    });
    return;
  }

  /* ================== MOTORE 2: sintesi vocale del browser (Web Speech) === */
  var synth = window.speechSynthesis;

  /* --- 0. dizionario di pronuncia -----------------------------------------
     Una voce di sintesi legge «d.lgs. 28/2010» come una sequenza di lettere e
     punti: incomprensibile. Qui le abbreviazioni giuridiche ricorrenti sul sito
     vengono sciolte prima della pronuncia. L'ordine conta: le forme più lunghe
     devono essere sostituite per prime.                                      */
  var DIZIONARIO = [
    // gli indirizzi web letti per esteso sono rumore: si tolgono
    [/https?:\/\/\S+/gi, " "],
    [/\bwww\.\S+/gi, " "],
    [/\bd\.\s*p\.\s*r\.\s*/gi, "decreto del Presidente della Repubblica "],
    [/\bd\.\s*lgs\.?\s*/gi, "decreto legislativo "],
    [/\bd\.\s*l\.\s*(?=\d)/gi, "decreto legge "],
    [/\bd\.\s*m\.\s*(?=\d)/gi, "decreto ministeriale "],
    [/\bc\.\s*p\.\s*c\.\s*/gi, "codice di procedura civile "],
    [/\bc\.\s*p\.\s*p\.\s*/gi, "codice di procedura penale "],
    [/\bc\.\s*c\.\s*(?=\d|\s|$)/gi, "codice civile "],
    [/\bartt\.\s*/gi, "articoli "],
    [/\bart\.\s*/gi, "articolo "],
    [/\bcomma\s+(\d)/gi, "comma $1"],
    [/\bco\.\s*(?=\d)/gi, "comma "],
    [/\blett\.\s*/gi, "lettera "],
    [/\bnn\.\s*(?=\d)/gi, "numeri "],
    [/\bn\.\s*(?=\d)/gi, "numero "],
    [/\bpp\.\s*(?=\d)/gi, "pagine "],
    [/\bp\.\s*(?=\d)/gi, "pagina "],
    [/\bsegg?\.\s*/gi, "seguenti "],
    [/\bss\.\s*/gi, "seguenti "],
    [/\bcfr\.\s*/gi, "confronta "],
    [/\bcit\.\s*/gi, "citato "],
    [/\becc\.\s*/gi, "eccetera "],
    [/\bad\s+es\.\s*/gi, "ad esempio "],
    [/\bp\.\s*es\.\s*/gi, "per esempio "],
    [/\bca\.\s*(?=\d)/gi, "circa "],
    [/\bCass\.\s*/g, "Cassazione "],
    [/\bTrib\.\s*/g, "Tribunale "],
    [/\bsent\.\s*/gi, "sentenza "],
    [/\bord\.\s*/gi, "ordinanza "],
    [/\bGU\b/g, "Gazzetta Ufficiale"],
    [/\bUE\b/g, "Unione europea"],
    [/§\s*/g, "paragrafo "],
    [/%/g, " per cento"],
    [/€/g, " euro"],
    // suffissi numerici delle norme: «12-bis» non deve suonare «dodici meno bis»
    [/-(bis|ter|quater|quinquies|sexies|septies|octies)\b/gi, " $1"],
    // intervalli di anni: il trattino verrebbe letto «meno»
    [/(\d)\s*[–—-]\s*(?=\d)/g, "$1 "],
    // ordinali femminili all'italiana: «2ª» -> «seconda»
    [/\b1ª/g, "prima"], [/\b2ª/g, "seconda"], [/\b3ª/g, "terza"],
    [/\b1º/g, "primo"], [/\b2º/g, "secondo"], [/\b3º/g, "terzo"]
  ];

  function pronuncia(t) {
    for (var i = 0; i < DIZIONARIO.length; i++) t = t.replace(DIZIONARIO[i][0], DIZIONARIO[i][1]);
    return t.replace(/\s{2,}/g, " ").trim();
  }

  // --- 1. estrazione del testo leggibile -----------------------------------
  // Si legge il titolo e poi i blocchi del corpo, nell'ordine.
  // Si escludono: i richiami di nota <sup>, le tabelle (annunciate a voce),
  // e tutto ciò che segue il paragrafo «Note» in fondo all'articolo.
  var segmenti = [];
  var tabelleAnnunciate = 0, stop = false;

  var h1 = art.querySelector(".post-header h1");
  if (h1) segmenti.push({ el: h1, testo: pulisci(h1), lang: null, titolo: true });

  percorri(body);

  if (stop) segmenti.push({ el: null, testo: "L'articolo prosegue con le note, che non vengono lette.", lang: null, titolo: false });
  if (!segmenti.length) { box.remove(); return; }

  // Percorre i blocchi nell'ordine in cui compaiono nella pagina.
  function percorri(contenitore) {
    var figli = contenitore.children;
    for (var i = 0; i < figli.length; i++) {
      if (stop) return;
      var el = figli[i], tag = el.tagName.toUpperCase();

      if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT") continue;

      // tabelle: il contenuto non si legge, si annuncia soltanto
      if (tag === "TABLE" || (el.querySelector && el.querySelector("table") && (tag === "DIV" || tag === "FIGURE"))) {
        var tab = tag === "TABLE" ? el : el.querySelector("table");
        var did = tab.querySelector("caption");
        tabelleAnnunciate++;
        segmenti.push({ el: el, titolo: false, lang: null,
          testo: did ? "Segue una tabella: " + pulisci(did) + ". Il contenuto non viene letto."
                     : "Segue una tabella, che non viene letta." });
        continue;
      }

      if (tag === "UL" || tag === "OL") { percorri(el); continue; }

      if (/^(P|H2|H3|H4|H5|LI|BLOCKQUOTE|FIGCAPTION)$/.test(tag)) {
        var t = pulisci(el);
        if (!t) continue;
        if (/^H[2345]$/.test(tag) && /^note$/i.test(t)) { stop = true; return; }   // stop all'apparato di note
        segmenti.push({ el: el, testo: t, lang: el.getAttribute("lang") || null, titolo: /^H[2345]$/.test(tag) });
        continue;
      }

      // contenitori generici: si scende dentro
      if (el.children.length) { percorri(el); continue; }
      var tt = pulisci(el);
      if (tt) segmenti.push({ el: el, testo: tt, lang: el.getAttribute("lang") || null, titolo: false });
    }
  }

  function pulisci(el) {
    var c = el.cloneNode(true);
    Array.prototype.forEach.call(c.querySelectorAll("sup, .footnote-ref, script, style"), function (n) { n.remove(); });
    var t = (c.textContent || "").replace(/ /g, " ").replace(/\s+/g, " ").trim();
    return t;
  }

  // durata stimata (alla velocità corrente, pause comprese)
  var caratteri = segmenti.reduce(function (n, s) { return n + s.testo.length; }, 0);
  function stimaMinuti() {
    var lettura = (caratteri / 6.2) / (PAROLE_AL_MINUTO * velocita);
    return Math.max(1, Math.round(lettura + (coda.length * PAUSA_FRASE) / 60000));
  }
  function aggiornaDurata() { durata.textContent = "· circa " + stimaMinuti() + " min"; }

  var nota2 = document.createElement("p");
  nota2.className = "ascolto-nota";
  nota2.textContent = "Voce di sintesi del dispositivo: legge correttamente, ma non interpreta. "
    + "Se la resa non convince, provare un'altra voce dall'elenco e rallentare."
    + (tabelleAnnunciate ? " Le tabelle e le note non vengono lette." : "");
  box.appendChild(nota2);

  // --- 2. suddivisione: una frase = una pronuncia --------------------------
  // Frasi intere, così il motore può applicare la propria curva d'intonazione;
  // si spezza solo dentro le frasi che superano MAX_CHUNK.
  var SEGNA = String.fromCharCode(1);   // segnaposto: nessun testo lo contiene
  function proteggi(t) {
    // «U.N.A.M.», «C.d.A.», «Avv.»: i punti interni non sono fine di frase
    t = t.replace(/\b([A-Za-zÀ-ÖØ-öø-ÿ])\./g, "$1" + SEGNA);
    t = t.replace(/\b(Avv|Dott|Dr|Prof|Sig|On|Ing|Rag|Sez|Vol|Fasc|Ed|Op|Spa|Srl)\./gi, "$1" + SEGNA);
    // nomi di dominio: «mediareinformati.it» non è la fine di una frase
    t = t.replace(/\.(it|com|org|net|eu|gov|edu|info|io)\b/gi, SEGNA + "$1");
    return t;
  }
  function ripristina(t) { return t.split(SEGNA).join("."); }

  function frasi(testo) {
    testo = proteggi(testo);
    var pezzi = testo.match(/[^.!?…]+[.!?…]+["»')\]]*\s*|[^.!?…]+$/g) || [testo];
    var out = [];
    pezzi.forEach(function (f) {
      f = f.trim();
      if (!f) return;
      if (f.length <= MAX_CHUNK) { out.push(f); return; }
      // Ripiego per le frasi lunghissime: si accumula parola per parola e si
      // stacca preferibilmente dopo una punteggiatura debole. Niente lookbehind:
      // i browser più vecchi non lo compilano e l'intero file fallirebbe.
      var parole = f.split(/\s+/), buf = "";
      parole.forEach(function (w) {
        var cand = buf ? buf + " " + w : w;
        if (cand.length > MAX_CHUNK && buf) { out.push(buf); buf = w; }
        else if (cand.length > MAX_CHUNK * 0.6 && /[;:,]$/.test(w)) { out.push(cand); buf = ""; }
        else buf = cand;
      });
      if (buf.trim()) out.push(buf.trim());
    });
    // Gli elenchi numerati dentro un paragrafo («1. Titolo. 2. Titolo.») fanno
    // scattare il punto fermo su un numero solo: si ricuciono a quel che segue.
    var fuse = [];
    for (var k = 0; k < out.length; k++) {
      if (/^(\d{1,3}|[ivxlcdm]{1,6}|[a-z])[.)]$/i.test(out[k]) && k + 1 < out.length) {
        out[k + 1] = out[k] + " " + out[k + 1];
      } else fuse.push(out[k]);
    }
    return fuse.map(ripristina);
  }
  var coda = [];
  segmenti.forEach(function (s, idx) {
    var fr = frasi(pronuncia(s.testo));
    fr.forEach(function (p, j) {
      coda.push({
        testo: p,
        seg: idx,
        lang: s.lang,
        // pausa DOPO questa pronuncia
        pausa: (j === fr.length - 1) ? (s.titolo ? PAUSA_TITOLO : PAUSA_PARAGRAFO) : PAUSA_FRASE
      });
    });
  });
  aggiornaDurata();

  // --- 3. scelta della voce italiana ---------------------------------------
  // Le voci «neurali» del sistema (Google, Microsoft Natural) hanno una
  // prosodia molto migliore delle vecchie voci SAPI: si mettono per prime.
  var voce = null, vociIt = [];
  var PREFERITE = ["Google italiano", "Natural", "Alice", "Federica", "Elsa", "Cosimo", "Luca", "Paolina", "Isabella"];

  function elencaVoci() {
    var vs = synth.getVoices() || [];
    vociIt = vs.filter(function (v) { return /^it(-|_|$)/i.test(v.lang || ""); });
    if (!vociIt.length) return;
    vociIt.sort(function (a, b) { return punteggio(b) - punteggio(a); });
    var salvata = null;
    try { salvata = localStorage.getItem(CHIAVE_VOCE); } catch (e) {}
    selVoce.innerHTML = "";
    vociIt.forEach(function (v, i) {
      var o = document.createElement("option");
      o.value = v.name;
      o.textContent = etichetta(v.name);
      selVoce.appendChild(o);
      if (salvata ? v.name === salvata : i === 0) { selVoce.value = v.name; voce = v; }
    });
    if (!voce) { voce = vociIt[0]; selVoce.value = voce.name; }
  }
  function punteggio(v) {
    var n = v.name || "", p = 0;
    for (var i = 0; i < PREFERITE.length; i++) if (n.indexOf(PREFERITE[i]) !== -1) { p = PREFERITE.length - i; break; }
    if (/Natural|Online|Neural/i.test(n)) p += 20;   // voci neurali: nettamente migliori
    return p;
  }
  function etichetta(n) {
    return n.replace(/^Microsoft\s+/, "").replace(/\s*-\s*Italian.*$/i, "")
            .replace(/\s*\(.*\)$/, "").trim() || n;
  }
  elencaVoci();
  if (synth.onvoiceschanged !== undefined) {
        synth.addEventListener("voiceschanged", function () { elencaVoci(); selVoce.parentNode.style.display = vociIt.length ? "" : "none"; });
  }
  if (!vociIt.length) selVoce.parentNode.style.display = "none";

  // --- 4. riproduzione ------------------------------------------------------
  var pos = 0, inLettura = false, inPausa = false, segCorrente = -1, keepAlive = null, attesa = null;

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

  function prossima(pausa) {
    if (attesa) { clearTimeout(attesa); attesa = null; }
    // la pausa si allunga quando si legge piano: il respiro deve restare in scala
    var ms = Math.round(pausa / Math.max(0.4, velocita));
    attesa = setTimeout(function () { attesa = null; if (inLettura && !inPausa) parla(); }, ms);
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
    u.pitch = 0.95;      // un filo più grave: meno cantilena, più tono di lettura
    u.volume = 1;
    u.onend = function () { if (inLettura && !inPausa) { pos++; prossima(pezzo.pausa); } };
    u.onerror = function (e) {
      if (e && (e.error === "interrupted" || e.error === "canceled")) return;
      pos++; if (inLettura && !inPausa) prossima(120);
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
    if (!voce) elencaVoci();
    synth.cancel();
    inLettura = true; inPausa = false;
    bPlay.textContent = "Pausa"; bStop.disabled = false;
    dì(voce ? "In lettura con la voce «" + etichetta(voce.name) + "»." : "In lettura con la voce predefinita del dispositivo.");
    avviaKeepAlive();
    parla();
  }
  function pausa() {
    inPausa = true;
    if (attesa) { clearTimeout(attesa); attesa = null; }
    synth.pause();
    bPlay.textContent = "Riprendi"; dì("In pausa.");
  }
  function riprendi() {
    inPausa = false; bPlay.textContent = "Pausa"; dì("In lettura.");
    if (synth.paused) synth.resume();
    else { synth.cancel(); parla(); }   // alcuni browser non sospendono davvero
  }
  function ferma() {
    inLettura = false; inPausa = false; pos = 0;
    if (attesa) { clearTimeout(attesa); attesa = null; }
    synth.cancel(); fermaKeepAlive(); ripulisci(); avanzamento(0);
    bPlay.textContent = "Ascolta"; bStop.disabled = true; dì("Lettura interrotta.");
  }
  function fine() {
    inLettura = false; inPausa = false; pos = 0;
    fermaKeepAlive(); ripulisci(); avanzamento(1);
    bPlay.textContent = "Ascolta di nuovo"; bStop.disabled = true; dì("Lettura terminata.");
    setTimeout(function () { avanzamento(0); }, 1500);
  }
  function riparti() {   // riprende dalla pronuncia corrente con le nuove impostazioni
    if (!inLettura || inPausa) return;
    if (attesa) { clearTimeout(attesa); attesa = null; }
    synth.cancel(); parla();
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
    aggiornaDurata();
    riparti();
  });
  selVoce.addEventListener("change", function () {
    for (var i = 0; i < vociIt.length; i++) if (vociIt[i].name === selVoce.value) voce = vociIt[i];
    try { localStorage.setItem(CHIAVE_VOCE, selVoce.value); } catch (e) {}
    if (inLettura && !inPausa) dì("Voce «" + etichetta(voce.name) + "».");
    riparti();
  });

  // se l'utente lascia la pagina, si tace (altrimenti la voce prosegue altrove)
  window.addEventListener("beforeunload", function () { try { synth.cancel(); } catch (e) {} });
  window.addEventListener("pagehide", function () { try { synth.cancel(); } catch (e) {} });
})();
