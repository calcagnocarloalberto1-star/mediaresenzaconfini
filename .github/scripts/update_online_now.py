"""Fetch an approximate "online now" visitor count from GoatCounter and write static/online-now.json.

Runs from a GitHub Actions workflow (.github/workflows/update-online-now.yml), on the same
schedule pattern as update_countries.py. Requires the GC_TOKEN environment variable (a
GoatCounter API token with "Read statistics" permission), supplied via the
GOATCOUNTER_API_TOKEN repository secret. If the token is not set, this script exits without
making changes so the workflow doesn't fail.

This is only an approximation: it counts unique visitors GoatCounter recorded in the last
WINDOW_MINUTES minutes, not a true real-time concurrent-session count (GoatCounter's API
doesn't expose that). nav-counter.js on the site already treats this as approximate and
hides the "online now" widget if the data is older than 30 minutes.
"""
import json
import os
import sys
import datetime
import urllib.request
import urllib.parse

GOATCOUNTER_SITE = "https://mediaresenzaconfini.goatcounter.com"
WINDOW_MINUTES = 10  # finestra usata per approssimare i visitatori "online ora"
OUTPUT_PATH = "static/online-now.json"

def fetch_recent_unique_visitors(token, window_minutes):
    now = datetime.datetime.now(datetime.timezone.utc)
    start = now - datetime.timedelta(minutes=window_minutes)
    qs = urllib.parse.urlencode({
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    req = urllib.request.Request(
        GOATCOUNTER_SITE + "/api/v0/stats/total?" + qs,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data.get("total", 0)

def main():
    token = os.environ.get("GC_TOKEN", "").strip()
    if not token:
        print("Nessun GOATCOUNTER_API_TOKEN impostato: salto l'aggiornamento.")
        return 0

    online = fetch_recent_unique_visitors(token, WINDOW_MINUTES)

    out = {
        "online": online,
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Scritto online=" + str(online) + " in " + OUTPUT_PATH)
    return 0

if __name__ == "__main__":
    sys.exit(main())
