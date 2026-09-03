import os, urllib.request, urllib.error

token = os.environ["GC_TOKEN"]
site = "https://mediaresenzaconfini.goatcounter.com"
paths = [
    "/api/v0/me",
    "/api/v0/stats/browsers?limit=1",
    "/api/v0/stats/systems?limit=1",
    "/api/v0/stats/locations?limit=1",
    "/api/v0/paths?limit=1",
]
for p in paths:
    req = urllib.request.Request(site + p, headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(p, "->", resp.status)
    except urllib.error.HTTPError as e:
        print(p, "->", e.code, e.reason)
    except Exception as e:
        print(p, "-> ERROR", repr(e))
