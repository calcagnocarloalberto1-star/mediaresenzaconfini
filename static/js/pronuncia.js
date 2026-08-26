/*
 * pronuncia.js — ascolto del singolo termine nella sezione "Come si scrive e come si dice".
 *
 * Indipendente da ascolta.js (che non legge il contenuto delle tabelle, per scelta
 * deliberata sulle tabelle giuridiche del resto del sito). Usa la stessa tecnologia
 * di base — la sintesi vocale del browser (Web Speech API), con la voce scelta in
 * base alla lingua — ma applicata parola per parola invece che a un intero articolo:
 * un piccolo pulsante "altoparlante" accanto a ogni traduzione.
 *
 * Nessuna dipendenza, nessuna richiesta di rete, nessun dato salvato.
 */
(function () {
  "use strict";

  if (!("speechSynthesis" in window)) return;

  var registro = null; // lang (minuscolo) -> SpeechSynthesisVoice migliore disponibile

  function costruisciRegistro() {
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
    if (!registro) registro = costruisciRegistro();
    if (!registro) return null;
    var l = (lang || "").toLowerCase();
    if (registro[l]) return registro[l];
    var base = l.split("-")[0];
    var chiave = Object.keys(registro).filter(function (k) { return k.split("-")[0] === base; })[0];
    return chiave ? registro[chiave] : null;
  }

  function parla(testo, lang, voce) {
    try { window.speechSynthesis.cancel(); } catch (e) {}
    var u = new SpeechSynthesisUtterance(testo);
    u.lang = (voce && voce.lang) || lang || "it-IT";
    if (voce) u.voice = voce;
    u.rate = 0.85;
    u.pitch = 0.98;
    window.speechSynthesis.speak(u);
  }

  function aggiornaPulsanti() {
    var pulsanti = document.querySelectorAll("[data-pron-speak]");
    Array.prototype.forEach.call(pulsanti, function (btn) {
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
    var testo = btn.getAttribute("data-pron-text") || "";
    var lang = btn.getAttribute("data-pron-lang") || "";
    if (!testo) return;
    var v = vocePer(lang);
    parla(testo, lang, v);
    btn.classList.add("pron-speak-active");
    window.setTimeout(function () { btn.classList.remove("pron-speak-active"); }, 700);
  });

  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = function () {
      registro = costruisciRegistro();
      aggiornaPulsanti();
    };
  }
  document.addEventListener("DOMContentLoaded", function () {
    registro = costruisciRegistro();
    aggiornaPulsanti();
  });
})();
