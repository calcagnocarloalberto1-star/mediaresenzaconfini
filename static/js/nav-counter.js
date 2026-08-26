// Contatore visite nell'header, accanto alla ricerca.
// Stesso meccanismo del contatore in home page: storico Jetpack Stats (fisso) + conteggio live GoatCounter (senza cookie).
(function () {
var GC_TOTAL = 'https://mediaresenzaconfini.goatcounter.com/counter/TOTAL.json';
var BASELINE_VIEWS = 185649; // storico Jetpack Stats (WordPress) rilevato il 12/08/2026, prima del passaggio a GoatCounter

function fmtIt(n) {
return Number(n).toLocaleString('it-IT');
}

var el = document.getElementById('nav-visit-counter');
if (el) {
fetch(GC_TOTAL).then(function (r) {
return r.ok ? r.json() : Promise.reject(r.status);
}).then(function (data) {
var live = parseInt(String(data.count).replace(/[^\d]/g, ''), 10);
if (!isNaN(live)) el.textContent = fmtIt(BASELINE_VIEWS + live);
}).catch(function () { /* resta il valore statico dell'ultima build */ });
}

// Utenti online ora: approssimazione (visitatori unici negli ultimi minuti),
// aggiornata ogni pochi minuti da una GitHub Action (vedi update_online_now.py).
// Non è un vero conteggio istantaneo: se il dato manca o è troppo vecchio, resta nascosto.
var ONLINE_NOW_URL = '/static/online-now.json';
var ONLINE_MAX_AGE_MINUTES = 30;
var onlineWrap = document.getElementById('nav-online-now');
var onlineCount = document.getElementById('nav-online-count');
if (onlineWrap && onlineCount) {
fetch(ONLINE_NOW_URL).then(function (r) {
return r.ok ? r.json() : Promise.reject(r.status);
}).then(function (data) {
if (!data || typeof data.online !== 'number' || !data.generated_at) return;
var ageMinutes = (Date.now() - new Date(data.generated_at).getTime()) / 60000;
if (ageMinutes > ONLINE_MAX_AGE_MINUTES) return;
onlineCount.textContent = fmtIt(data.online);
onlineWrap.hidden = false;
}).catch(function () { /* resta nascosto se il file non esiste ancora o la chiamata fallisce */ });
}
})();
