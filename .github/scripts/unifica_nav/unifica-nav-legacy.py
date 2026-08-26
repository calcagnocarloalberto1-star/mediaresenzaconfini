import re, os, sys

OLD_TEMPLATE_FILES = [
    "2019/12/02/corso-di-aggiornamento-per-mediatori-civili-e-commerciali-a-reggio-emilia/index.html",
    "2023/04/05/corso-di-aggiornamento-per-mediatori-17-20-aprile-2023/index.html",
    "2020/05/26/webinar-gratuito-sullavvocato-negoziatore/index.html",
    "2020/05/19/webinar-gratuito-sulla-mediazione-in-europa/index.html",
    "2018/01/18/corso-di-aggiornamento-per-mediatori-a-genova-nel-marzo-2018/index.html",
    "404.html",
    "2017/11/16/corso-di-aggiornamento-per-mediatori-civili-e-commerciali-in-reggio-emilia/index.html",
    "2017/09/07/corso-di-aggiornamento-per-mediatori-in-genova/index.html",
    "2017/01/27/corso-di-aggiornamento-per-mediatori-a-genova-marzo-2017/index.html",
    "2017/01/27/corso-di-aggiornamento-per-mediatori-a-como-marzo-2017/index.html",
    "2015/09/27/convegno-sulla-degiurisdizionalizzazione-ad-acqui-terme/index.html",
    "2016/03/10/corso-di-aggiornamento-per-mediatori-a-monza/index.html",
    "2016/11/14/mediazioni-e-discipline-psicologiche-un-seminario-a-reggio-emilia/index.html",
    "2016/08/11/corso-di-aggiornamento-dei-mediatori-a-monza/index.html",
    "2016/09/11/corso-di-aggiornamento-per-mediatori-civili-e-commerciali-in-como/index.html",
    "2016/09/30/corso-di-aggiornamento-dei-mediatori-a-genova/index.html",
    "2016/04/11/corso-di-aggiornamento-per-mediatori-a-genova/index.html",
    "2016/10/19/corso-di-aggiornamento-mediatori-genova-novembre-2016/index.html",
    "2022/11/30/3896/index.html",
]

# Canonical modern nav block, taken verbatim from the site home page (index.html),
# which is the fullest/most complete nav variant on the current site (includes
# "Eventi" and every section link, plus search box and mobile nav-toggle).
NEW_NAV = '''<nav class="main-nav">
<div class="wrap">
<input type="checkbox" id="nav-toggle" class="nav-toggle-input">
<label for="nav-toggle" class="nav-toggle-label" aria-label="Apri il menu">&#9776;</label>
<div class="nav-links">
<a href="/">Home</a>
<a href="/categoria/mediazione/">Mediazione</a>
<a href="/categoria/arbitrato/">Arbitrato</a>
<a href="/categoria/conciliazione/">Conciliazione</a>
<a href="/categoria/eventi/">Eventi</a>
<a href="/legislazione-internazionale/">Legislazione internazionale</a>
<a href="/storia-della-legislazione-per-paese/">Legislazione storica</a>
<a href="/testi-in-vigore/">Testi in vigore multilingue</a>
<a href="/progetti-di-legge-in-itinere/">Progetti di legge in itinere</a>
<a href="/paesi-ue-in-numeri/">Paesi UE in numeri</a>
<a href="/categoria/saggi/">Saggi</a>
<a href="/about/">Chi sono</a>
<a href="/preferisci-ascoltare/">Preferisci ascoltare?</a>
<a href="/utilita/">Utilità</a>
<a href="/come-si-scrive-e-come-si-dice/">Come si scrive e come si dice</a>
</div>
<form class="search-box" action="/cerca/" method="get" role="search">
<input type="search" name="q" placeholder="Cerca…" aria-label="Cerca nel sito">
</form>
</div>
</nav>'''

NAV_BLOCK_RE = re.compile(r'<nav class="main-nav">.*?</nav>', re.DOTALL)

ALREADY_MARKER = '<a href="/come-si-scrive-e-come-si-dice/">Come si scrive e come si dice</a>'


def process(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if ALREADY_MARKER in content:
        return "skip-already"

    if '<nav class="main-nav">' not in content:
        return "skip-no-nav"

    new_content, n = NAV_BLOCK_RE.subn(NEW_NAV, content, count=1)
    if n == 0:
        return "skip-no-match"

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return "patched"
    return "skip-no-change"


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    counts = {}
    results = []
    for rel in OLD_TEMPLATE_FILES:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            result = "skip-missing"
        else:
            result = process(path)
        counts[result] = counts.get(result, 0) + 1
        results.append((rel, result))

    print("Riepilogo:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    print("\nDettaglio:")
    for rel, result in results:
        print(f"  {result}: {rel}")


if __name__ == "__main__":
    main()
