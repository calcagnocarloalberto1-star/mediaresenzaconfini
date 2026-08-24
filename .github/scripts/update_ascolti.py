"""Fetch "ascolto" event stats from GoatCounter and write static/ascolti.json.

Ogni volta che un visitatore avvia l'ascolto di un articolo (bottone "Ascolta",
sia con MP3 ElevenLabs sia con la sintesi vocale del browser), static/js/ascolta.js
manda un evento GoatCounter con percorso "ascolto<percorso-reale-articolo>"
(vedi mrcTracciaAscolto() in quel file). Questo script legge quegli eventi
tramite l'API di GoatCounter e scrive una classifica ordinata in
static/ascolti.json, usata dalla pagina /preferisci-ascoltare/.

Runs from a GitHub Actions workflow (.github/workflows/update-ascolti.yml).
Requires la stessa variabile d'ambiente GC_TOKEN già usata da
update_countries.py, fornita dal repository secret GOATCOUNTER_API_TOKEN
(nessuna configurazione aggiuntiva richiesta). Se il token non è impostato,
lo script esce senza modificare nulla, così l'azione non fallisce.
"""
import json
import os
import sys
import datetime
import urllib.request
import urllib.parse

GOATCOUNTER_SITE = "https://mediaresenzaconfini.goatcounter.com"
# Data di attivazione del tracciamento degli ascolti (aggiunto ad ascolta.js
# in questa stessa pubblicazione): prima di questa data l'evento non esiste.
TRACKING_START = "2026-08-24"
OUTPUT_PATH = "static/ascolti.json"
PREFIX = "ascolto"  # vedi mrcTracciaAscolto(): path = "ascolto" + location.pathname


def fetch_all_hits(token):
    base = GOATCOUNTER_SITE + "/api/v0/stats/hits"
    exclude = []
    all_hits = []
    for _ in range(20):  # tetto di sicurezza: 20 pagine da 100 = 2000 percorsi
        qs = {
            "start": TRACKING_START,
            "limit": 100,
            "daily": "false",
        }
        if exclude:
            qs["exclude_paths"] = ",".join(str(i) for i in exclude)
        req = urllib.request.Request(
            base + "?" + urllib.parse.urlencode(qs),
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        hits = data.get("hits", [])
        all_hits.extend(hits)
        ids = [h.get("path_id") for h in hits if h.get("path_id") is not None]
        exclude.extend(ids)
        if not data.get("more") or not hits:
            break
    return all_hits


def main():
    token = os.environ.get("GC_TOKEN", "").strip()
    if not token:
        print("Nessun GOATCOUNTER_API_TOKEN impostato: salto l'aggiornamento.")
        return 0

    hits = fetch_all_hits(token)

    items = []
    for h in hits:
        path = h.get("path") or ""
        if not path.startswith(PREFIX):
            continue
        real_path = path[len(PREFIX):]
        if not real_path.startswith("/"):
            real_path = "/" + real_path
        count = h.get("count_unique")
        if not count:
            count = h.get("count", 0)
        items.append({
            "path": real_path,
            "url": "https://mediaresenzaconfini.it" + real_path,
            "title": h.get("title") or real_path,
            "ascolti": count,
        })

    items.sort(key=lambda i: i["ascolti"], reverse=True)

    out = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tracking_start": TRACKING_START,
        "count": len(items),
        "items": items,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Scritti " + str(len(items)) + " ascolti in " + OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
