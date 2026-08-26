#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera la sezione "Come si scrive e come si dice" (terminologia multilingue
della mediazione, per Stato, con IPA + pronuncia facilitata + ascolto del
singolo termine) e la integra nel sito:

- crea come-si-scrive-e-come-si-dice/index.html (indice)
- crea come-si-scrive-e-come-si-dice-<slug>/index.html per ciascuno dei 193 Stati
- crea static/js/pronuncia.js
- aggiunge il blocco CSS dedicato in static/css/style.css (se non già presente)
- aggiunge il link "Come si scrive e come si dice" al footer delle pagine
  principali e del template /pubblica/ (se non già presente)
- aggiunge le 194 nuove URL a sitemap.xml (se non già presenti)
- aggiunge le 194 nuove voci a static/search-index.json (se non già presenti)

Pensato per girare da GitHub Actions con il repository già checked-out come
working directory (stesso schema di .github/scripts/marca_lingue.py).
Idempotente: rieseguirlo non duplica nulla.
"""
import json
import os
import re
import html as htmllib

ROOT = os.environ.get("REPO_ROOT", ".")
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_full.json")
OGGI = os.environ.get("DATA_PUBBLICAZIONE", "2026-08-26")

SITE = "https://mediaresenzaconfini.it"
SEZ_SLUG = "come-si-scrive-e-come-si-dice"
SEZ_NOME = "Come si scrive e come si dice"

FOOTER_OLD = (
    '<a href="/pubblica/">Pubblica</a> &middot; <a href="/categoria/eventi/">Eventi</a></div>'
)
FOOTER_NEW = (
    '<a href="/pubblica/">Pubblica</a> &middot; <a href="/categoria/eventi/">Eventi</a> '
    '&middot; <a href="/' + SEZ_SLUG + '/">' + SEZ_NOME + '</a></div>'
)

MAIN_PAGES = [
    "index.html",
    "about/index.html",
    "link-utili/index.html",
    "statistiche/index.html",
    "privacy-policy/index.html",
    "cookie-policy/index.html",
    "legislazione-internazionale/index.html",
    "cerca/index.html",
    "contatti/index.html",
    "pubblica/index.html",
]


def slugify(s):
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", s)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    out, prev_dash = [], False
    for ch in stripped.lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
                prev_dash = True
    return "".join(out).strip("-")


def esc(s):
    return htmllib.escape(s or "", quote=True)


SPEAK_TEXT_RE = re.compile(r"^(.*?)\s\(([^()]*)\)$")


def speak_text(traduzione):
    m = SPEAK_TEXT_RE.match(traduzione or "")
    if m and m.group(1).strip():
        return m.group(1).strip()
    return traduzione or ""


HEAD_TMPL = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="mediaresenzaconfini">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://mediaresenzaconfini.it/static/img/header-mediazione.jpg">
<meta property="og:locale" content="it_IT">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://mediaresenzaconfini.it/static/img/header-mediazione.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/css/style.css">
<script data-goatcounter="https://mediaresenzaconfini.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script type="application/ld+json">{{"@context": "https://schema.org", "@type": "WebSite", "name": "mediaresenzaconfini", "url": "https://mediaresenzaconfini.it/", "publisher": {{"@type": "Person", "name": "Carlo Alberto Calcagno"}}, "potentialAction": {{"@type": "SearchAction", "target": "https://mediaresenzaconfini.it/cerca/?q={{search_term_string}}", "query-input": "required name=search_term_string"}}}}</script>
<script type="application/ld+json">{{"@context": "https://schema.org", "@type": "Person", "name": "Carlo Alberto Calcagno", "url": "https://mediaresenzaconfini.it/about/", "jobTitle": "Avvocato, mediatore civile e commerciale, mediatore familiare, formatore ADR", "worksFor": {{"@type": "Organization", "name": "mediaresenzaconfini", "url": "https://mediaresenzaconfini.it/"}}}}</script>
<script type="application/ld+json">{breadcrumb_ld}</script>
</head>
<body>
<header class="site-header">
<div class="site-header-photo" style="background-image: url('/static/img/header-mediazione.jpg');">
<div class="site-header-overlay">
<div class="wrap site-header-brand">
<a href="/"><span class="brand-name">mediaresenzaconfini</span></a>
</div>
</div>
</div>
<nav class="main-nav">
<div class="wrap">
<input type="checkbox" id="nav-toggle" class="nav-toggle-input">
<label for="nav-toggle" class="nav-toggle-label" aria-label="Apri il menu">&#9776;</label>
<div class="nav-links">
<a href="/">Home</a>
<a href="/categoria/mediazione/">Mediazione</a>
<a href="/categoria/arbitrato/">Arbitrato</a>
<a href="/categoria/conciliazione/">Conciliazione</a>
<a href="/legislazione-internazionale/">Legislazione internazionale</a>
<a href="/storia-della-legislazione-per-paese/">Legislazione storica</a>
<a href="/testi-in-vigore/">Testi in vigore multilingue</a>
<a href="/progetti-di-legge-in-itinere/">Progetti di legge in itinere</a>
<a href="/paesi-ue-in-numeri/">Paesi UE in numeri</a>
<a href="/categoria/saggi/">Saggi</a>
<a href="/about/">Chi sono</a>
<a href="/preferisci-ascoltare/">Preferisci ascoltare?</a>
<a href="/utilita/">Utilit&agrave;</a>
</div>
<form class="search-box" action="/cerca/" method="get" role="search">
<input type="search" name="q" placeholder="Cerca&hellip;" aria-label="Cerca nel sito">
</form>
</div>
</nav>
</header>
<main class="wrap">
"""

FOOT_TMPL = """</main>
<footer class="site-footer">
<div class="wrap">
<div>&copy; 2026 mediaresenzaconfini &mdash; Carlo Alberto Calcagno. Tutti i diritti riservati.</div>
<div><a href="/about/">Chi sono</a> &middot; <a href="/link-utili/">Link utili</a> &middot; <a href="/statistiche/">Statistiche</a> &middot; <a href="/contatti/">Contatti</a> &middot; <a href="/privacy-policy/">Privacy</a> &middot; <a href="/cookie-policy/">Cookie</a> &middot; <a href="/pubblica/">Pubblica</a> &middot; <a href="/categoria/eventi/">Eventi</a> &middot; <a href="/{sez}/">{sez_nome}</a></div>
</div>
</footer>
<script src="/static/js/pronuncia.js" defer></script>
</body>
</html>
"""


def breadcrumb_json(items):
    els = []
    for i, (name, url) in enumerate(items, start=1):
        els.append({"@type": "ListItem", "position": i, "name": name, "item": url})
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": els}, ensure_ascii=False)


def build_lang_table(lang):
    rows = []
    for i, term_it in enumerate(TERMS):
        trad, ipa, semp = lang["righe"][i]
        if trad:
            sp_text = speak_text(trad)
            cella_trad = (
                '<div class="pron-cell"><span class="pron-trad" lang="{lg}">{trad}</span>'
                '<button type="button" class="pron-speak" data-pron-speak '
                'data-pron-text="{sp}" data-pron-lang="{lg}" aria-label="Ascolta la pronuncia">&#128266;</button></div>'
            ).format(lg=esc(lang["codice"]), trad=esc(trad), sp=esc(sp_text))
        else:
            cella_trad = "&ndash;"
        ipa_txt = esc(ipa) if ipa else "&ndash;"
        semp_txt = esc(semp) if semp else "&ndash;"
        rows.append(
            "<tr><td class=\"pron-term\">{t}</td><td>{tr}</td><td class=\"pron-ipa\">{ip}</td><td>{se}</td></tr>".format(
                t=esc(term_it), tr=cella_trad, ip=ipa_txt, se=semp_txt
            )
        )
    return (
        '<div class="pron-table-wrap"><table class="pron-table">'
        '<thead><tr><th>Termine (italiano)</th><th>Traduzione</th><th>IPA</th><th>Pronuncia facilitata</th></tr></thead>'
        "<tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def build_country_page(stato, languages):
    nome = stato["nome"]
    slug = slugify(nome)
    lingue_keys = stato["lingue"]
    lingue_nomi = [languages[k]["nome"] if k in languages else "Italiano" for k in lingue_keys]
    lingue_label = ", ".join(lingue_nomi)

    if len(lingue_nomi) == 1:
        desc = "{s}: come si scrive e come si pronuncia mediazione e altri 21 termini della giustizia consensuale in {l}, con IPA, pronuncia facilitata e ascolto del singolo termine.".format(s=nome, l=lingue_label)
    else:
        desc = "{s}: i 22 termini della giustizia consensuale in {l} ({n} lingue), come si scrivono e come si pronunciano, con IPA, pronuncia facilitata e ascolto del singolo termine.".format(s=nome, l=lingue_label, n=len(lingue_nomi))
    if lingue_keys == ["italiano"]:
        desc = "{s}: i 22 termini della giustizia consensuale nella lingua del sito, senza bisogno di guida alla pronuncia.".format(s=nome)

    title = "Come si scrive e come si dice: {s} &mdash; mediaresenzaconfini".format(s=nome)
    canonical = "{site}/{sez}-{slug}/".format(site=SITE, sez=SEZ_SLUG, slug=slug)
    bc = breadcrumb_json([
        ("Home", SITE + "/"),
        (SEZ_NOME, "{}/{}/".format(SITE, SEZ_SLUG)),
        (nome, canonical),
    ])

    parts = [HEAD_TMPL.format(title=title, desc=esc(desc), canonical=canonical, breadcrumb_ld=bc)]
    parts.append('<article class="static-page pron-page">')
    parts.append('<a class="pron-back" href="/{}/">&larr; Indice: {}</a>'.format(SEZ_SLUG, SEZ_NOME))
    parts.append("<h1>{}</h1>".format(esc(nome)))
    parts.append("<p><strong>Lingua ufficiale:</strong> {}.</p>".format(esc(lingue_label)))
    if stato.get("note"):
        parts.append('<p class="pron-lang-note">{}</p>'.format(esc(stato["note"])))

    for key in lingue_keys:
        if key == "italiano":
            parts.append("<h2>Lingua: Italiano (it-IT)</h2>")
            parts.append(
                '<p class="pron-lang-note">I 22 termini sono, per definizione, gi&agrave; nella lingua del sito: non serve una guida di pronuncia.</p>'
            )
            continue
        lang = languages[key]
        parts.append("<h2>Lingua: {} ({})</h2>".format(esc(lang["nome"]), esc(lang["codice"])))
        parts.append(build_lang_table(lang))

    parts.append('<a class="pron-back" href="/{}/">&larr; Indice: {}</a>'.format(SEZ_SLUG, SEZ_NOME))
    parts.append("</article>")
    parts.append(FOOT_TMPL.format(sez=SEZ_SLUG, sez_nome=SEZ_NOME))
    return "".join(parts), slug, title, desc, canonical


def build_index_page(stati, languages):
    title = "{} &mdash; mediaresenzaconfini".format(SEZ_NOME)
    desc = "I 22 termini fondamentali della mediazione, in 94 lingue, riorganizzati Stato per Stato: come si scrivono, come si pronunciano (IPA e pronuncia facilitata) e come ascoltarli, termine per termine."
    canonical = "{}/{}/".format(SITE, SEZ_SLUG)
    bc = breadcrumb_json([("Home", SITE + "/"), (SEZ_NOME, canonical)])

    parts = [HEAD_TMPL.format(title=title, desc=esc(desc), canonical=canonical, breadcrumb_ld=bc)]
    parts.append('<article class="static-page pron-index-intro">')
    parts.append("<h1>{}</h1>".format(SEZ_NOME))
    parts.append(
        "<p>Il lessico multilingue del sito (22 termini fondamentali della giustizia consensuale, tradotti in 95 lingue ufficiali) era organizzato per lingua. Questa sezione lo riorganizza per Stato: ogni scheda-Paese riporta la propria lingua ufficiale (o le proprie lingue, quando sono pi&ugrave; di una) e la tavola completa dei 22 termini in quella lingua, con trascrizione IPA, pronuncia facilitata per un lettore italiano e un pulsante di ascolto per ogni singolo termine.</p>"
    )
    parts.append("<h2>Le quattro colonne</h2>")
    parts.append("<p><strong>Termine (italiano)</strong> &mdash; l'etichetta italiana di riferimento, identica in tutte le schede.<br>"
                  "<strong>Traduzione</strong> &mdash; la resa nella lingua ufficiale dello Stato; per le lingue non latine la trascrizione in caratteri latini compare tra parentesi accanto alla grafia nativa.<br>"
                  "<strong>IPA</strong> &mdash; l'Alfabeto Fonetico Internazionale, la trascrizione pi&ugrave; rigorosa.<br>"
                  "<strong>Pronuncia facilitata</strong> &mdash; una resa \"a orecchio\" con le convenzioni della lettura italiana (sillabe separate da trattino, accento tonico in MAIUSCOLO).</p>")
    parts.append("<h2>Il parlato: come si ascolta</h2>")
    parts.append(
        "<p>Accanto a ogni traduzione c'&egrave; un piccolo pulsante &#128266;: fa leggere quel singolo termine con la voce del sistema nella sua lingua (la stessa tecnologia di sintesi vocale gi&agrave; usata nel lettore degli articoli, applicata qui parola per parola invece che a un intero testo). Se il dispositivo non ha una voce installata per quella lingua, il pulsante lo segnala e non forza una pronuncia sbagliata: la guida IPA e la pronuncia facilitata restano comunque a schermo.</p>"
    )
    parts.append("<h2>Copertura e un'avvertenza sui numeri</h2>")
    parts.append(
        "<p>Questa sezione copre <strong>193 Stati</strong>: tutte le giurisdizioni del lessico linguistico di partenza, con un solo accorpamento &mdash; le tre voci del lessico originario per il Regno Unito (Inghilterra e Galles, Irlanda del Nord, Scozia) condividono la stessa lingua e sono qui riunite in un'unica scheda. La convenzione &laquo;197 Stati/enti&raquo; usata altrove sul sito include anche due enti sovranazionali (Unione Europea e ONU) privi di una propria lingua ufficiale ai fini di un lessico linguistico, e quindi non hanno una scheda qui.</p>"
    )
    parts.append(
        "<p>Le trascrizioni IPA e le pronunce facilitate sono state elaborate appositamente per questo progetto, lingua per lingua: sono una guida pratica, non una fonte fonetica certificata da terzi. Il margine di imprecisione &egrave; maggiore per le lingue meno diffuse o documentate. Due termini (&laquo;arbitrato&raquo; e &laquo;imparzialit&agrave;&raquo; in dhivehi, &laquo;arbitrato&raquo; in dzongkha) non erano presenti nel lessico di partenza e sono segnalati con \"&ndash;\" anzich&eacute; inventati.</p>"
    )

    parts.append('<h2 id="lingue">Lingue e codici (per l\'attributo lang)</h2>')
    parts.append('<div class="pron-code-table"><table><thead><tr><th>Lingua</th><th>Codice</th></tr></thead><tbody>')
    for lname in sorted(languages.keys(), key=lambda k: languages[k]["nome"]):
        l = languages[lname]
        parts.append("<tr><td>{}</td><td>{}</td></tr>".format(esc(l["nome"]), esc(l["codice"])))
    parts.append("</tbody></table></div>")

    parts.append("<h2>Stati disponibili ({})</h2>".format(len(stati)))
    parts.append('<ul class="flat-list">')
    for s in sorted(stati, key=lambda s: strip_accents(s["nome"]).lower()):
        slug = slugify(s["nome"])
        parts.append('<li><a href="/{sez}-{slug}/">{nome}</a></li>'.format(sez=SEZ_SLUG, slug=slug, nome=esc(s["nome"])))
    parts.append("</ul>")

    parts.append("</article>")
    parts.append(FOOT_TMPL.format(sez=SEZ_SLUG, sez_nome=SEZ_NOME))
    return "".join(parts), title, desc, canonical


def strip_accents(s):
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    changed = True
    if os.path.exists(full):
        with open(full, "r", encoding="utf-8") as f:
            if f.read() == content:
                changed = False
    if changed:
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
    return changed


def main():
    data = json.load(open(DATA_PATH, encoding="utf-8"))
    global TERMS
    TERMS = data["terms"]
    languages = data["languages"]
    stati = data["stati"]

    written = []

    # 1) static/js/pronuncia.js
    js_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pronuncia.js")
    with open(js_src, encoding="utf-8") as f:
        js_content = f.read()
    if write("static/js/pronuncia.js", js_content):
        written.append("static/js/pronuncia.js")

    # 2) style.css addition
    css_path = os.path.join(ROOT, "static/css/style.css")
    with open(css_path, encoding="utf-8") as f:
        css = f.read()
    addition_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style_addition.css")
    with open(addition_path, encoding="utf-8") as f:
        addition = f.read()
    if "/* Come si scrive e come si dice" not in css:
        with open(css_path, "a", encoding="utf-8") as f:
            f.write(addition)
        written.append("static/css/style.css")

    # 3) country pages
    sitemap_new_urls = []
    search_new_entries = []

    for stato in stati:
        content, slug, title, desc, canonical = build_country_page(stato, languages)
        path = "{}-{}/index.html".format(SEZ_SLUG, slug)
        if write(path, content):
            written.append(path)
        sitemap_new_urls.append(canonical)
        search_new_entries.append({
            "t": "Come si scrive e come si dice: {}".format(stato["nome"]),
            "u": "/{}-{}/".format(SEZ_SLUG, slug),
            "e": desc,
            "c": "Terminologia",
            "d": OGGI,
        })

    # 4) index page
    idx_content, idx_title, idx_desc, idx_canonical = build_index_page(stati, languages)
    if write("{}/index.html".format(SEZ_SLUG), idx_content):
        written.append("{}/index.html".format(SEZ_SLUG))
    sitemap_new_urls.append(idx_canonical)
    search_new_entries.insert(0, {
        "t": SEZ_NOME,
        "u": "/{}/".format(SEZ_SLUG),
        "e": idx_desc,
        "c": "Terminologia",
        "d": OGGI,
    })

    # 5) sitemap.xml
    sm_path = os.path.join(ROOT, "sitemap.xml")
    with open(sm_path, encoding="utf-8") as f:
        sm = f.read()
    added_sm = 0
    for url in sitemap_new_urls:
        entry = "<url><loc>{}</loc></url>".format(url)
        if url not in sm:
            sm = sm.replace("</urlset>", "  " + entry + "\n</urlset>")
            added_sm += 1
    if added_sm:
        with open(sm_path, "w", encoding="utf-8") as f:
            f.write(sm)
        written.append("sitemap.xml (+{})".format(added_sm))

    # 6) search-index.json
    si_path = os.path.join(ROOT, "static/search-index.json")
    with open(si_path, encoding="utf-8") as f:
        si = json.load(f)
    existing_urls = {e.get("u") for e in si}
    added_si = 0
    for e in search_new_entries:
        if e["u"] not in existing_urls:
            si.append(e)
            added_si += 1
    if added_si:
        with open(si_path, "w", encoding="utf-8") as f:
            json.dump(si, f, ensure_ascii=False, separators=(",", ":"))
        written.append("static/search-index.json (+{})".format(added_si))

    # 7) footer link on main pages
    for rel in MAIN_PAGES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            c = f.read()
        if FOOTER_OLD in c and SEZ_SLUG not in c.split("<footer", 1)[-1]:
            c2 = c.replace(FOOTER_OLD, FOOTER_NEW)
            if c2 != c:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(c2)
                written.append(rel + " (footer)")

    print("File creati/aggiornati: {}".format(len(written)))
    for w in written[:20]:
        print(" -", w)
    if len(written) > 20:
        print(" ... e altri {}".format(len(written) - 20))


if __name__ == "__main__":
    main()
