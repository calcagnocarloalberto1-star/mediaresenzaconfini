# -*- coding: utf-8 -*-
"""
Applica le 5 correzioni individuate dall'audit generale del 26/08/2026
(vedi claude/audit-generale-sito-26-08-2026.md nel Project):

1. Rimuove i 15 link rotti (verso 3 articoli mai migrati) dalle 15 pagine tag.
2. Ripulisce il contenuto orfano residuo sulle 2 pagine "(pagina duplicata)".
3. Sostituisce le 7 meta description rotte (shortcode WordPress non elaborato)
   con testo reale e pertinente.
4. Aggiunge a sitemap.xml le 18 pagine reali del vecchio template che ne
   erano prive.
5. Cambia <h1> in <h2> per le 4 intestazioni di lingua sulle 3 pagine
   testi-in-vigore-irlanda/messico/lituania (12 sostituzioni totali).

Idempotente: ogni funzione verifica lo stato prima di modificare, quindi
può essere rieseguito in sicurezza (una seconda esecuzione non produce
ulteriori modifiche).
"""
import re, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


# ---------------------------------------------------------------------------
# 1. Link interni rotti nelle pagine tag
# ---------------------------------------------------------------------------

LINK_PAIRS = [
    ("tag/circolare/index.html", "/2013/12/03/due-parole-sulla-circolare-27-novembre-2013-entrata-in-vigore-dellart-84-del-d-l-692013-come-convertito-dalla-l-982013-recante-disposizioni-urgenti-per-il-rilancio-delleconomia-che/"),
    ("tag/conciliatore/pagina/3/index.html", "/2013/12/03/due-parole-sulla-circolare-27-novembre-2013-entrata-in-vigore-dellart-84-del-d-l-692013-come-convertito-dalla-l-982013-recante-disposizioni-urgenti-per-il-rilancio-delleconomia-che/"),
    ("tag/conciliazione/pagina/4/index.html", "/2013/12/03/due-parole-sulla-circolare-27-novembre-2013-entrata-in-vigore-dellart-84-del-d-l-692013-come-convertito-dalla-l-982013-recante-disposizioni-urgenti-per-il-rilancio-delleconomia-che/"),
    ("tag/controversia-bancaria-e-finanziaria/index.html", "/2018/05/23/lobbligo-di-assistenza-in-mediazione-e-compatibile-col-diritto-comunitario-il-rifiuto-di-farsi-assistere-in-mediazione-obbligatoria-costituisce-violazione-di-legge-meritevole-di-sanzione-anche-in-c/"),
    ("tag/controversia/pagina/2/index.html", "/2013/12/03/due-parole-sulla-circolare-27-novembre-2013-entrata-in-vigore-dellart-84-del-d-l-692013-come-convertito-dalla-l-982013-recante-disposizioni-urgenti-per-il-rilancio-delleconomia-che/"),
    ("tag/direttiva-2008-52/index.html", "/2017/10/09/risoluzione-del-parlamento-europeo-del-12-settembre-2017-sullattuazione-della-direttiva-200852ce-del-parlamento-europeo-e-del-consiglio-del-21-maggio-2008-relativa-a-determinati-aspetti-della-me/"),
    ("tag/diritto-comunitario/index.html", "/2018/05/23/lobbligo-di-assistenza-in-mediazione-e-compatibile-col-diritto-comunitario-il-rifiuto-di-farsi-assistere-in-mediazione-obbligatoria-costituisce-violazione-di-legge-meritevole-di-sanzione-anche-in-c/"),
    ("tag/formazione/index.html", "/2013/12/03/due-parole-sulla-circolare-27-novembre-2013-entrata-in-vigore-dellart-84-del-d-l-692013-come-convertito-dalla-l-982013-recante-disposizioni-urgenti-per-il-rilancio-delleconomia-che/"),
    ("tag/mediazione-controversia/index.html", "/2018/05/23/lobbligo-di-assistenza-in-mediazione-e-compatibile-col-diritto-comunitario-il-rifiuto-di-farsi-assistere-in-mediazione-obbligatoria-costituisce-violazione-di-legge-meritevole-di-sanzione-anche-in-c/"),
    ("tag/mediazione-ministero-della-giustizia/index.html", "/2013/12/03/due-parole-sulla-circolare-27-novembre-2013-entrata-in-vigore-dellart-84-del-d-l-692013-come-convertito-dalla-l-982013-recante-disposizioni-urgenti-per-il-rilancio-delleconomia-che/"),
    ("tag/mediazione-obbligatoria/index.html", "/2013/12/03/due-parole-sulla-circolare-27-novembre-2013-entrata-in-vigore-dellart-84-del-d-l-692013-come-convertito-dalla-l-982013-recante-disposizioni-urgenti-per-il-rilancio-delleconomia-che/"),
    ("tag/ministero/index.html", "/2013/12/03/due-parole-sulla-circolare-27-novembre-2013-entrata-in-vigore-dellart-84-del-d-l-692013-come-convertito-dalla-l-982013-recante-disposizioni-urgenti-per-il-rilancio-delleconomia-che/"),
    ("tag/parametri-forensi/index.html", "/2018/05/23/lobbligo-di-assistenza-in-mediazione-e-compatibile-col-diritto-comunitario-il-rifiuto-di-farsi-assistere-in-mediazione-obbligatoria-costituisce-violazione-di-legge-meritevole-di-sanzione-anche-in-c/"),
    ("tag/risoluzione-del-parlamento-europe/index.html", "/2017/10/09/risoluzione-del-parlamento-europeo-del-12-settembre-2017-sullattuazione-della-direttiva-200852ce-del-parlamento-europeo-e-del-consiglio-del-21-maggio-2008-relativa-a-determinati-aspetti-della-me/"),
    ("tag/tribunale-di-vasto-9-aprile-2018/index.html", "/2018/05/23/lobbligo-di-assistenza-in-mediazione-e-compatibile-col-diritto-comunitario-il-rifiuto-di-farsi-assistere-in-mediazione-obbligatoria-costituisce-violazione-di-legge-meritevole-di-sanzione-anche-in-c/"),
]


def fix_broken_links():
    results = []
    for rel, href in LINK_PAIRS:
        path = os.path.join(ROOT, rel)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if href not in content:
            results.append(("skip-already", rel))
            continue

        href_escaped = re.escape(href)
        card_re = re.compile(
            r'[ \t]*<div class="card">\s*?\n(?:(?!<div class="card">|^\s*</div>\s*$).)*?'
            + href_escaped +
            r'.*?\n[ \t]*</div>\s*\n?',
            re.DOTALL | re.MULTILINE,
        )

        m = re.search(r'(\d+) articoli su questo argomento\.(?:</p>)?', content)
        paginated = re.search(r'\d+ articoli su questo argomento &mdash; pagina \d+ di \d+', content)

        new_content, n = card_re.subn("", content, count=1)
        if n == 0:
            results.append(("error-card-not-matched", rel))
            continue

        if paginated:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            results.append(("fixed-paginated", rel))
            continue

        if not m:
            results.append(("error-no-count", rel))
            continue
        old_count = int(m.group(1))
        new_count = old_count - 1
        if new_count < 0:
            results.append(("error-negative-count", rel))
            continue

        old_text = f"{old_count} articoli su questo argomento."
        new_text = f"{new_count} articoli su questo argomento."
        new_content = new_content.replace(old_text, new_text)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        results.append((f"fixed ({old_count}->{new_count})", rel))
    return results


# ---------------------------------------------------------------------------
# 2. Contenuto orfano sulle 2 pagine "(pagina duplicata)"
# ---------------------------------------------------------------------------

def fix_orphan_content():
    results = []

    # --- Bangladesh: 3 tag di chiusura orfani ---
    bpath = os.path.join(ROOT, "la-legislazione-sulla-mediazione-bangladesh/index.html")
    with open(bpath, "r", encoding="utf-8") as f:
        b = f.read()

    old_b = """</div>
</div>
      </li>
    </ul>
  </div>

</article>"""
    new_b = """</div>
</div>

</article>"""

    if old_b in b:
        b2 = b.replace(old_b, new_b, 1)
        with open(bpath, "w", encoding="utf-8") as f:
            f.write(b2)
        results.append(("fixed", "bangladesh"))
    else:
        results.append(("skip-already", "bangladesh"))

    # --- Spagna: note a piè di pagina orfane + commenti WordPress ---
    spath = os.path.join(
        ROOT,
        "2020/12/29/la-rivoluzione-dei-mezzi-alternativi-di-risoluzione-delle-controversie-in-spagna-2/index.html",
    )
    with open(spath, "r", encoding="utf-8") as f:
        s = f.read()

    start_marker = "</div>\n</div></figure>"
    end_marker = "d.l. 132/14).</p>\n<!-- /wp:paragraph -->\n  </div>"

    start_idx = s.find(start_marker)
    end_idx = s.find(end_marker)
    if start_idx != -1 and end_idx != -1:
        end_idx_full = end_idx + len(end_marker)
        old_block = s[start_idx:end_idx_full]
        new_block = "</div>\n</div>"
        s2 = s.replace(old_block, new_block, 1)
        with open(spath, "w", encoding="utf-8") as f:
            f.write(s2)
        results.append(("fixed", "spagna"))
    else:
        results.append(("skip-already", "spagna"))

    return results


# ---------------------------------------------------------------------------
# 3. Meta description rotte da shortcode WordPress
# ---------------------------------------------------------------------------

META_DESC_FIXES = {
    "2018/05/30/uno-schema-delle-differenze-tra-la-mediazione-civile-e-commerciale-e-la-negoziazione-assistita/index.html":
        "Uno schema comparativo tra la mediazione civile e commerciale e la negoziazione assistita, con le immagini di sintesi del confronto.",
    "2016/03/10/corso-di-aggiornamento-per-mediatori-a-monza/index.html":
        "Corso di aggiornamento per mediatori a Monza (10 marzo 2016), 18 ore, a cura dell'avv. Carlo Alberto Calcagno: programma, contatti e iscrizione.",
    "2016/11/14/mediazioni-e-discipline-psicologiche-un-seminario-a-reggio-emilia/index.html":
        "Immagini del seminario “Mediazioni e discipline psicologiche”, Reggio Emilia, 14 novembre 2016.",
    "2016/08/11/corso-di-aggiornamento-dei-mediatori-a-monza/index.html":
        "Corso di aggiornamento dei mediatori a Monza (11 agosto 2016), 18 ore: locandina e informazioni per l'iscrizione.",
    "2016/09/30/corso-di-aggiornamento-dei-mediatori-a-genova/index.html":
        "Corso di aggiornamento dei mediatori a Genova (30 settembre 2016), 18 ore: locandina e informazioni per l'iscrizione.",
    "2016/04/11/corso-di-aggiornamento-per-mediatori-a-genova/index.html":
        "Corso di aggiornamento per mediatori a Genova (11 aprile 2016), 18 ore accreditato dall'Ordine dei Commercialisti di Genova: programma e iscrizione.",
    "2016/10/19/corso-di-aggiornamento-mediatori-genova-novembre-2016/index.html":
        "Immagini del corso di aggiornamento per mediatori a Genova, novembre 2016.",
}


def fix_meta_descriptions():
    results = []
    for rel, new_desc in META_DESC_FIXES.items():
        path = os.path.join(ROOT, rel)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        replaced = 0
        already_correct = 0
        for i, line in enumerate(lines):
            stripped = line.rstrip("\n")
            target_desc_line = f'<meta name="description" content="{new_desc}">'
            target_og_line = f'<meta property="og:description" content="{new_desc}">'
            target_tw_line = f'<meta name="twitter:description" content="{new_desc}">'
            if stripped == target_desc_line or stripped == target_og_line or stripped == target_tw_line:
                already_correct += 1
                continue
            if stripped.startswith('<meta name="description" content="'):
                lines[i] = target_desc_line + "\n"
                replaced += 1
            elif stripped.startswith('<meta property="og:description" content="'):
                lines[i] = target_og_line + "\n"
                replaced += 1
            elif stripped.startswith('<meta name="twitter:description" content="'):
                lines[i] = target_tw_line + "\n"
                replaced += 1

        if replaced:
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            results.append((f"fixed ({replaced} tag)", rel))
        else:
            results.append(("skip-already", rel))
    return results


# ---------------------------------------------------------------------------
# 4. Pagine mancanti da sitemap.xml
# ---------------------------------------------------------------------------

SITEMAP_NEW_PAGES = [
    "2015/09/27/convegno-sulla-degiurisdizionalizzazione-ad-acqui-terme/",
    "2016/03/10/corso-di-aggiornamento-per-mediatori-a-monza/",
    "2016/04/11/corso-di-aggiornamento-per-mediatori-a-genova/",
    "2016/08/11/corso-di-aggiornamento-dei-mediatori-a-monza/",
    "2016/09/11/corso-di-aggiornamento-per-mediatori-civili-e-commerciali-in-como/",
    "2016/09/30/corso-di-aggiornamento-dei-mediatori-a-genova/",
    "2016/10/19/corso-di-aggiornamento-mediatori-genova-novembre-2016/",
    "2016/11/14/mediazioni-e-discipline-psicologiche-un-seminario-a-reggio-emilia/",
    "2017/01/27/corso-di-aggiornamento-per-mediatori-a-como-marzo-2017/",
    "2017/01/27/corso-di-aggiornamento-per-mediatori-a-genova-marzo-2017/",
    "2017/09/07/corso-di-aggiornamento-per-mediatori-in-genova/",
    "2017/11/16/corso-di-aggiornamento-per-mediatori-civili-e-commerciali-in-reggio-emilia/",
    "2018/01/18/corso-di-aggiornamento-per-mediatori-a-genova-nel-marzo-2018/",
    "2019/12/02/corso-di-aggiornamento-per-mediatori-civili-e-commerciali-a-reggio-emilia/",
    "2020/05/19/webinar-gratuito-sulla-mediazione-in-europa/",
    "2020/05/26/webinar-gratuito-sullavvocato-negoziatore/",
    "2022/11/30/3896/",
    "2023/04/05/corso-di-aggiornamento-per-mediatori-17-20-aprile-2023/",
]


def fix_sitemap():
    path = os.path.join(ROOT, "sitemap.xml")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    marker = "</urlset>"
    idx = content.rindex(marker)

    missing = [
        p for p in SITEMAP_NEW_PAGES
        if f'<loc>https://mediaresenzaconfini.it/{p}</loc>' not in content
    ]
    if not missing:
        return [("skip-already", "sitemap.xml")]

    new_lines = "".join(
        f'  <url><loc>https://mediaresenzaconfini.it/{p}</loc></url>\n' for p in missing
    )
    new_content = content[:idx] + new_lines + content[idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return [(f"fixed (+{len(missing)} url)", "sitemap.xml")]


# ---------------------------------------------------------------------------
# 5. <h1> multipli su testi-in-vigore-irlanda/messico/lituania
# ---------------------------------------------------------------------------

H1_PAGES = [
    "testi-in-vigore-irlanda/index.html",
    "testi-in-vigore-messico/index.html",
    "testi-in-vigore-lituania/index.html",
]

H1_RE = re.compile(r"<h1>(.*?)</h1>", re.DOTALL)


def fix_h1_headings():
    results = []
    for rel in H1_PAGES:
        path = os.path.join(ROOT, rel)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        matches = list(H1_RE.finditer(content))
        if len(matches) == 1:
            results.append(("skip-already", rel))
            continue
        if len(matches) != 5:
            results.append((f"error-unexpected-h1-count({len(matches)})", rel))
            continue

        out = []
        last_end = 0
        for i, m in enumerate(matches):
            out.append(content[last_end:m.start()])
            if i == 0:
                out.append(m.group(0))
            else:
                out.append(f"<h2>{m.group(1)}</h2>")
            last_end = m.end()
        out.append(content[last_end:])
        new_content = "".join(out)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        results.append(("fixed", rel))
    return results


def main():
    print("== 1. Link interni rotti nelle pagine tag ==")
    for status, rel in fix_broken_links():
        print(f"{status}\t{rel}")

    print("\n== 2. Contenuto orfano nelle pagine duplicata ==")
    for status, name in fix_orphan_content():
        print(f"{status}\t{name}")

    print("\n== 3. Meta description rotte ==")
    for status, rel in fix_meta_descriptions():
        print(f"{status}\t{rel}")

    print("\n== 4. Pagine mancanti da sitemap.xml ==")
    for status, name in fix_sitemap():
        print(f"{status}\t{name}")

    print("\n== 5. <h1> multipli nelle pagine testi-in-vigore ==")
    for status, rel in fix_h1_headings():
        print(f"{status}\t{rel}")


if __name__ == "__main__":
    main()
