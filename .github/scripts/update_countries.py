"""Fetch per-country visitor stats from GoatCounter and write static/countries.json.

Runs from a GitHub Actions workflow (.github/workflows/update-stats.yml). Requires the
GC_TOKEN environment variable (a GoatCounter API token with read access to stats),
supplied via the GOATCOUNTER_API_TOKEN repository secret. If the token is not set,
this script exits without making changes so the workflow doesn't fail.
"""
import json
import os
import sys
import datetime
import urllib.request
import urllib.parse

GOATCOUNTER_SITE = "https://mediaresenzaconfini.goatcounter.com"
TRACKING_START = "2026-08-12"  # data di attivazione di GoatCounter sul nuovo sito
OUTPUT_PATH = "static/countries.json"


def fetch_all_locations(token):
    base = GOATCOUNTER_SITE + "/api/v0/stats/locations"
    offset = 0
    limit = 100
    all_stats = []
    while True:
        qs = urllib.parse.urlencode({"start": TRACKING_START, "limit": limit, "offset": offset})
        req = urllib.request.Request(
            base + "?" + qs,
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        stats = data.get("stats", [])
        all_stats.extend(stats)
        if not data.get("more") or not stats:
            break
        offset += limit
        if offset > 1000:
            break
    return all_stats


def main():
    token = os.environ.get("GC_TOKEN", "").strip()
    if not token:
        print("Nessun GOATCOUNTER_API_TOKEN impostato: salto l'aggiornamento.")
        return 0

    stats = fetch_all_locations(token)
    countries = sorted(
        (
            {"id": s.get("id"), "name": s.get("name") or s.get("id"), "count": s.get("count", 0)}
            for s in stats
            if s.get("id")
        ),
        key=lambda c: c["count"],
        reverse=True,
    )

    out = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(countries),
        "countries": countries,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Scritti " + str(len(countries)) + " paesi in " + OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
