"""Invia automaticamente una newsletter (via API Buttondown, piano gratuito) quando
feed.xml viene aggiornato con un nuovo articolo in cima.

Runs from a GitHub Actions workflow (.github/workflows/send-newsletter.yml). Richiede
la variabile d'ambiente BUTTONDOWN_API_KEY (chiave API di Buttondown, Settings >
Programming > API keys), fornita tramite il secret di repository BUTTONDOWN_API_KEY.
Se la chiave non è impostata, lo script esce senza errori così il workflow non fallisce.

Logica anti-duplicati: confronta il <guid> del primo <item> di feed.xml con il valore
salvato in static/last-newsletter-guid.txt. Se sono uguali, non c'è un nuovo articolo
da annunciare e lo script non fa nulla. Se sono diversi, crea e invia (status "sent")
una email via API con titolo, estratto e link dell'articolo, poi aggiorna il file di
tracking con il nuovo guid.
"""
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

FEED_PATH = "feed.xml"
LAST_GUID_PATH = "static/last-newsletter-guid.txt"
API_URL = "https://api.buttondown.com/v1/emails"


def read_last_guid():
    if os.path.exists(LAST_GUID_PATH):
        with open(LAST_GUID_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def write_last_guid(guid):
    os.makedirs(os.path.dirname(LAST_GUID_PATH), exist_ok=True)
    with open(LAST_GUID_PATH, "w", encoding="utf-8") as f:
        f.write(guid.strip() + "\n")


def parse_latest_item():
    tree = ET.parse(FEED_PATH)
    root = tree.getroot()
    item = root.find("./channel/item")
    if item is None:
        return None
    return {
        "title": (item.findtext("title") or "").strip(),
        "link": (item.findtext("link") or "").strip(),
        "guid": (item.findtext("guid") or item.findtext("link") or "").strip(),
        "description": (item.findtext("description") or "").strip(),
    }


def send_email(api_key, subject, body):
    payload = json.dumps({
        "subject": subject,
        "body": body,
        "status": "sent",
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": "Token " + api_key,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    api_key = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    if not api_key:
        print("Nessuna BUTTONDOWN_API_KEY impostata: salto l'invio della newsletter.")
        return 0

    item = parse_latest_item()
    if item is None or not item["guid"]:
        print("feed.xml non ha voci valide: salto l'invio della newsletter.")
        return 0

    last_guid = read_last_guid()
    if item["guid"] == last_guid:
        print("Nessun articolo nuovo rispetto all'ultimo inviato: salto l'invio della newsletter.")
        return 0

    subject = item["title"]
    body = (
        "<p>" + item["description"] + "</p>"
        "<p><a href=\"" + item["link"] + "\">Leggi l'articolo completo su mediaresenzaconfini &rarr;</a></p>"
    )

    result = send_email(api_key, subject, body)
    print("Email inviata via Buttondown: " + json.dumps(result.get("id", result), ensure_ascii=False))

    write_last_guid(item["guid"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
