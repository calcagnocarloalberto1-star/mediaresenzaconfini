/*
 * pronuncia.js — ascolto del singolo termine nella sezione "Come si scrive e come si dice".
 *
 * Indipendente da ascolta.js (che non legge il contenuto delle tabelle, per scelta
 * deliberata sulle tabelle giuridiche del resto del sito). Due modalità di lettura:
 *
 * 1. Audio pre-registrato (ElevenLabs), quando il pulsante ha l'attributo
 *    data-pron-audio: viene sempre preferito, perché garantisce una pronuncia
 *    corretta su ogni dispositivo, indipendentemente dalle voci di sistema
 *    installate nel browser di chi legge.
 * 2. Sintesi vocale del browser (Web Speech API), come prima, per i termini che
 *    non hanno ancora un audio pre-registrato: la voce è scelta in base alla lingua.
 *
 * Nessuna dipendenza, nessun dato salvato. L'unica richiesta di rete è, se presente,
 * il file audio mp3 stesso (stessa origine del sito).
 */
(function () {
  "use strict";

  var sintesiDisponibile = "speechSynthesis" in window;
  var registro = null; // lang (minuscolo) -> SpeechSynthesisVoice migliore disponibile
  var audioCorrente = null; // <audio> in riproduzione, per poterlo fermare

  function costruisciRegistro() {
    if (!sintesiDisponibile) return null;
    var voci = window.speechSynthesis.getVoices() || [];
    if (!voci.length) return null;
    var reg = {};
    voci.forEach(function (v) {
      var lang = (v.lang || "").toLowerCase();
      if (!lang) return;
      var punteggio = 0;
      if (/(natural|online|neural)/i.test(v.name || "")) punteggio += 2;
      if (v.localService) punteggio += 0; // nessuna preferenza forte: online spesso più naturale
      var attuale = reg[lang];
      if (!attuale || punteggio > attuale._punteggio) {
        v._punteggio = punteggio;
        reg[lang] = v;
      }
    });
    return reg;
  }

  function vocePer(lang) {
    if (!sintesiDisponibile) return null;
    if (!registro) registro = costruisciRegistro();
    if (!registro) return null;
    var l = (lang || "").toLowerCase();
    if (registro[l]) return registro[l];
    var base = l.split("-")[0];
    var chiave = Object.keys(registro).filter(function (k) { return k.split("-")[0] === base; })[0];
    return chiave ? registro[chiave] : null;
  }

  function parla(testo, lang, voce) {
    if (!sintesiDisponibile) return;
    try { window.speechSynthesis.cancel(); } catch (e) {}
    var u = new SpeechSynthesisUtterance(testo);
    u.lang = (voce && voce.lang) || lang || "it-IT";
    if (voce) u.voice = voce;
    u.rate = 0.85;
    u.pitch = 0.98;
    window.speechSynthesis.speak(u);
  }

  function riproduciAudio(src, btn) {
    try {
      if (audioCorrente) {
        audioCorrente.pause();
        audioCorrente.currentTime = 0;
      }
      var a = new Audio(src);
      audioCorrente = a;
      var fallbackGiaFatto = false;
      var vaiAlFallback = function () {
        if (fallbackGiaFatto) return;
        fallbackGiaFatto = true;
        fallbackSintesi(btn);
      };
      // errore di rete/decodifica (es. file mancante): non sempre fa fallire la promise di play()
      a.addEventListener("error", vaiAlFallback);
      a.play().catch(vaiAlFallback);
    } catch (e) {
      fallbackSintesi(btn);
    }
  }

  function fallbackSintesi(btn) {
    var testo = btn.getAttribute("data-pron-text") || "";
    var lang = btn.getAttribute("data-pron-lang") || "";
    if (!testo) return;
    var v = vocePer(lang);
    parla(testo, lang, v);
  }

  function aggiornaPulsanti() {
    var pulsanti = document.querySelectorAll("[data-pron-speak]");
    Array.prototype.forEach.call(pulsanti, function (btn) {
      var audioSrc = btn.getAttribute("data-pron-audio");
      if (audioSrc) {
        // Audio pre-registrato disponibile: il pulsante funziona sempre.
        btn.classList.remove("pron-speak-fallback");
        btn.title = "Ascolta la pronuncia";
        return;
      }
      var lang = btn.getAttribute("data-pron-lang");
      var v = vocePer(lang);
      if (v) {
        btn.classList.remove("pron-speak-fallback");
        btn.title = "Ascolta (" + v.name + ")";
      } else {
        btn.classList.add("pron-speak-fallback");
        btn.title = "Nessuna voce disponibile su questo dispositivo per questa lingua: si aggiunge dalle impostazioni di sistema, alla voce lingua.";
      }
    });
  }

  document.addEventListener("click", function (ev) {
    var btn = ev.target.closest && ev.target.closest("[data-pron-speak]");
    if (!btn) return;
    ev.preventDefault();
    var audioSrc = btn.getAttribute("data-pron-audio");
    btn.classList.add("pron-speak-active");
    window.setTimeout(function () { btn.classList.remove("pron-speak-active"); }, 700);
    if (audioSrc) {
      riproduciAudio(audioSrc, btn);
      return;
    }
    fallbackSintesi(btn);
  });

  if (sintesiDisponibile && window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = function () {
      registro = costruisciRegistro();
      aggiornaPulsanti();
    };
  }
  document.addEventListener("DOMContentLoaded", function () {
    if (sintesiDisponibile) registro = costruisciRegistro();
    aggiornaPulsanti();
  });
})();
