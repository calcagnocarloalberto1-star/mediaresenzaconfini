# -*- coding: utf-8 -*-
"""
Risolve i 5 "punti aperti" (osservazioni minori) dell'audit generale del
26/08/2026 (vedi claude/audit-generale-sito-26-08-2026.md nel Project):

1. Aggiunge <link rel="canonical"> alle 24 pagine che ne erano prive
   (26 individuate dall'audit, meno 404.html e pubblica/editor-strutturato.html,
   escluse di proposito: la prima non ha un URL indicizzabile singolo, la
   seconda e' uno strumento interno escluso dall'indicizzazione).
2. Scrive le 27 meta description mancanti (28 individuate dall'audit, meno
   pubblica/editor-strutturato.html, stesso motivo).
3. Rimuove i commenti HTML residui di WordPress Gutenberg (<!-- wp:... -->)
   da 151 pagine (l'audit ne indicava 152; la ricognizione puntuale su
   questo giro ne ha confermate 151 — vedi handoff).
4. Cambia in <h2> gli <h1> multipli presenti in 12 pagine (delle 13
   individuate dall'audit; pubblica/index.html e' un falso positivo: le
   occorrenze di "<h1" li' sono dentro stringhe JavaScript del pannello di
   pubblicazione, non tag HTML resi nella pagina).
5. Rimuove l'immagine con sorgente esterna morta (s0.wp.com) e i 2 link
   collegati, che puntano ormai verso una pagina inesistente, nel post del
   2015 "Analisi del 2014".

Idempotente: ogni funzione verifica lo stato prima di modificare.
"""
import re, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


# ---------------------------------------------------------------------------
# 1. Canonical mancanti
# ---------------------------------------------------------------------------

CANONICAL_PAGES = [
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
    "carta-dei-diritti-asiatici/",
    "comunita-europea-regolamento-odr-e-direttiva-adr/",
    "la-legislazione-della-mediazione-belize/",
    "la-mediazione-familiare-francia/",
    "la-mediazione-familiare-italia/",
    "legge-cinese-sulla-mediazione-news/",
]


def fix_canonical():
    results = []
    desc_re = re.compile(r'(<meta name="description"[^>]*>\n)')
    for rel_dir in CANONICAL_PAGES:
        rel = rel_dir + "index.html"
        path = os.path.join(ROOT, rel)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if '<link rel="canonical"' in content:
            results.append(("skip-already", rel))
            continue

        canonical_url = f"https://mediaresenzaconfini.it/{rel_dir}"
        canonical_line = f'<link rel="canonical" href="{canonical_url}">\n'

        new_content, n = desc_re.subn(
            lambda m: m.group(1) + canonical_line, content, count=1
        )
        if n == 0:
            results.append(("error-no-description-line", rel))
            continue

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        results.append(("fixed", rel))
    return results


# ---------------------------------------------------------------------------
# 2. Meta description mancanti
# ---------------------------------------------------------------------------

MISSING_DESC = {
    "2012/06/12/362/index.html":
        "Locandina dell'evento «Mediare, un'opportunità per tutti», 12 giugno 2012.",
    "2012/06/19/parliamo-di-mediazione/index.html":
        "Un'immagine a corredo dell'articolo «Parliamo di mediazione?», pubblicato il 19 giugno 2012.",
    "2012/12/07/che-cosa-pensa-locse-nel-settembre-2012-degli-strumenti-alternativi-in-italia/index.html":
        "Che cosa diceva l'OCSE nel rapporto del settembre 2012 sugli strumenti alternativi di risoluzione delle controversie in Italia e sulla lentezza della giustizia civile.",
    "2013/09/04/corso-base-di-arbitrato/index.html":
        "Locandina del Corso base di arbitrato a Milano, 4 settembre 2013.",
    "2013/12/10/la-presenza-dellavvocato-nella-mediazione-civile-obbligatoria/index.html":
        "Locandina del convegno sulla presenza dell'avvocato nella mediazione civile obbligatoria, 10 dicembre 2013.",
    "2014/03/27/i-mediatori-europei-in-una-pagina/index.html":
        "Un'infografica di sintesi sui mediatori europei, pubblicata il 27 marzo 2014.",
    "2014/12/02/come-comunicare-nella-mediazione-e-nella-negoziazione/index.html":
        "Uno schema su come comunicare efficacemente in mediazione e in negoziazione, 2 dicembre 2014.",
    "2015/05/03/analisi-della-performance-psicofisica-nei-processi-decisionali-assistiti/index.html":
        "Materiale illustrativo sull'analisi della performance psicofisica nei processi decisionali assistiti, 3 maggio 2015.",
    "2015/09/27/convegno-sulla-degiurisdizionalizzazione-ad-acqui-terme/index.html":
        "Locandina del convegno sulla degiurisdizionalizzazione tenutosi ad Acqui Terme, 27 settembre 2015.",
    "2015/10/03/lavvocato-e-le-capacita-negoziali-nella-negoziazione-assistita/index.html":
        "Materiale sull'avvocato e le capacità negoziali richieste nella negoziazione assistita, 3 ottobre 2015.",
    "2016/01/25/corso-di-leadership-strategica-e-operativa/index.html":
        "Locandina del corso di Leadership strategica e operativa, 25 gennaio 2016.",
    "2016/05/02/aumentare-la-produttivita-in-tempi-di-crisi-le-persone-come-risorse/index.html":
        "Locandina dell'incontro «Aumentare la produttività in tempi di crisi: le persone come risorse», 2 maggio 2016.",
    "2016/06/23/tecniche-di-mediazione-le-esperienze-internazionali/index.html":
        "Una rassegna delle tecniche di mediazione e delle esperienze internazionali in materia, 23 giugno 2016.",
    "2017/01/27/corso-di-aggiornamento-per-mediatori-a-como-marzo-2017/index.html":
        "Locandine del corso di aggiornamento per mediatori a Como, marzo 2017.",
    "2017/01/27/corso-di-aggiornamento-per-mediatori-a-genova-marzo-2017/index.html":
        "Locandine del corso di aggiornamento per mediatori a Genova, marzo 2017.",
    "2017/03/21/annullabile-il-regolamento-di-mediazione-che-vieti-di-proporre-tar-abruzzo-pescara-sez-i-sentenza-n-9817/index.html":
        "Nota alla sentenza del TAR Abruzzo - Pescara, sez. I, n. 98/2017, sull'annullabilità della norma del regolamento di mediazione che vieti di formulare la proposta.",
    "2017/04/04/prassi-e-pratica-della-mediazione-e-della-negoziazione/index.html":
        "Locandina del corso «Prassi e pratica della mediazione e della negoziazione», aprile 2017.",
    "2017/10/03/il-termine-di-tre-mesi-non-e-prorogabile/index.html":
        "Nota sul termine di tre mesi della mediazione civile e commerciale, non prorogabile, 3 ottobre 2017.",
    "2018/10/18/giornata-europea-della-giustizia-civile/index.html":
        "Locandine per la Giornata europea della giustizia civile, 18 ottobre 2018.",
    "2020/05/26/webinar-gratuito-sullavvocato-negoziatore/index.html":
        "Materiale del webinar gratuito sull'avvocato negoziatore, 26 maggio 2020.",
    "2020/06/23/gestire-il-conflitto-in-tempo-di-emergenza-la-mediazione-come-forma-di-giustizia-complementare/index.html":
        "Locandina dell'evento «Gestire il conflitto in tempo di emergenza: la mediazione come forma di giustizia complementare», 29 giugno 2020.",
    "2020/10/23/aggiornamento-on-line-mediatori-civili-e-commerciali/index.html":
        "Locandina del corso di aggiornamento online per mediatori civili e commerciali, novembre 2020.",
    "2022/09/29/il-consiglio-dei-ministri-ha-approvato-il-28-settembre-la-riforma-della-giustizia/index.html":
        "Il Consiglio dei Ministri ha approvato il 28 settembre 2022 la riforma della giustizia: una sintesi dei contenuti principali.",
    "2022/11/30/3896/index.html":
        "Locandina del convegno sulla mediazione familiare del 15 dicembre 2022.",
    "2023/02/03/il-genogramma-teoria-e-pratica/index.html":
        "Locandina dell'evento «Il Genogramma: teoria e pratica», 8 marzo 2023.",
    "2023/03/03/il-genogramma-teoria-e-pratica-2/index.html":
        "Il genogramma tra teoria e pratica: uno strumento per ricostruire la storia familiare e il proprio vissuto, con una riflessione ispirata a Oliver Sacks.",
    "2025/01/17/lorigine-della-mediazione-moderna-e-il-canone/index.html":
        "L'origine della mediazione moderna e il Canone: un percorso tra il pensiero di Christian Wolff e le radici filosofiche della mediazione.",
}


def fix_missing_descriptions():
    """
    Copre due varianti dello stesso difetto (description mancante):
    - tag realmente vuoti: content="">
    - tag "vuoti" ma con testo che ha rotto l'attributo HTML: un estratto
      dell'articolo iniziava con una virgoletta non escapata, chiudendo
      prematuramente l'attributo content="" e lasciando il resto del testo
      come markup penzolante (colpisce 3 delle 27 pagine). Entrambe le
      varianti iniziano con `content=""`, quindi lo stesso controllo di
      prefisso le individua e le sostituisce entrambe con l'intera riga.
    """
    results = []
    for rel, new_desc in MISSING_DESC.items():
        path = os.path.join(ROOT, rel)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_desc_line = f'<meta name="description" content="{new_desc}">'
        target_og_line = f'<meta property="og:description" content="{new_desc}">'
        target_tw_line = f'<meta name="twitter:description" content="{new_desc}">'

        replaced = 0
        for i, line in enumerate(lines):
            stripped = line.rstrip("\n")
            if stripped in (target_desc_line, target_og_line, target_tw_line):
                continue
            if stripped.startswith('<meta name="description" content=""'):
                lines[i] = target_desc_line + "\n"
                replaced += 1
            elif stripped.startswith('<meta property="og:description" content=""'):
                lines[i] = target_og_line + "\n"
                replaced += 1
            elif stripped.startswith('<meta name="twitter:description" content=""'):
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
# 3. Commenti HTML residui di WordPress Gutenberg
# ---------------------------------------------------------------------------

WP_COMMENT_RE = re.compile(r"[ \t]*<!--\s*/?wp:.*?-->[ \t]*\n?", re.DOTALL)

WP_COMMENT_PAGES = [
    "2019/08/08/rapporto-roland-2019-sulla-giustizia-ed-i-metodi-alternativi-in-germania/index.html",
    "2019/08/13/la-mediazione-in-belize/index.html",
    "2019/08/26/la-mediazione-in-bosnia-ed-erzegovina/index.html",
    "2019/10/09/le-mediazioni-in-europa/index.html",
    "2019/11/27/la-mediazione-in-bhutan/index.html",
    "2019/12/02/corso-di-aggiornamento-per-mediatori-civili-e-commerciali-a-reggio-emilia/index.html",
    "2019/12/18/porta-a-porta-bonafede-e-lo-ius-pontificale/index.html",
    "2020/01/19/strumenti-del-counseling-rogersiano-nella-mediazione-familiare/index.html",
    "2020/02/03/gli-strumenti-alternativi-in-bolivia/index.html",
    "2020/04/18/la-mediazione-familiare-in-italia-e-in-europa/index.html",
    "2020/05/19/webinar-gratuito-sulla-mediazione-in-europa/index.html",
    "2020/05/26/webinar-gratuito-sullavvocato-negoziatore/index.html",
    "2020/05/30/uno-sguardo-verso-leuropa-dati-a-confronto-sulla-mediazione/index.html",
    "2020/06/06/mediazione-italiana-ed-europea-uno-sguardo-comparato/index.html",
    "2020/06/09/arbitrato-e-negoziato-in-europa/index.html",
    "2020/06/17/la-mediazione-familiare-una-risorsa-per-tutti/index.html",
    "2020/06/23/gestire-il-conflitto-in-tempo-di-emergenza-la-mediazione-come-forma-di-giustizia-complementare/index.html",
    "2020/06/26/lavanzata-degli-strumenti-alternativi/index.html",
    "2020/08/05/ma-il-processo-civile-e-proprio-necessario/index.html",
    "2020/08/07/intervista-con-carlo-mosca/index.html",
    "2020/09/06/lo-stato-della-giustizia-italiana-nel-2020-per-la-ue/index.html",
    "2020/10/01/la-mediazione-e-i-giudici/index.html",
    "2020/10/23/aggiornamento-on-line-mediatori-civili-e-commerciali/index.html",
    "2020/11/21/strumenti-per-tutelare-la-famiglia-ai-tempi-del-covid/index.html",
    "2020/12/19/lo-stato-della-giustizia-in-italia-e-la-riforma-degli-adr/index.html",
    "2020/12/29/la-revolution-des-modes-alternatifs-de-reglement-des-litiges-en-espagne/index.html",
    "2020/12/29/la-rivoluzione-dei-mezzi-alternativi-di-risoluzione-delle-controversie-in-spagna/index.html",
    "2020/12/29/letat-de-la-justice-en-italie-et-la-revision-annoncee-des-regles-sur-les-instruments-alternatifs-de-reglement-des-litiges/index.html",
    "2021/01/01/lenneagramma-e-la-gematria/index.html",
    "2021/01/15/la-mediazione-in-italia-o-le-gioie-e-le-disgrazie-della-mediazione-obbligatoria/index.html",
    "2021/01/18/la-mediazione-familiare-in-europa/index.html",
    "2021/02/05/le-leggi-della-mediazione-in-europa/index.html",
    "2021/05/01/la-mediazione-parla-finlandese/index.html",
    "2021/05/15/federico-ii-faro-della-civilta-giuridica/index.html",
    "2021/05/26/evoluzione-storico-normativa-del-conflitto/index.html",
    "2021/06/02/la-mediazione-lituana-nel-processo-amministrativo/index.html",
    "2021/06/14/statistica-della-mediazione-civile-e-commerciale-in-gran-bretagna/index.html",
    "2021/06/16/la-legge-sulla-mediazione-civile-e-commerciale-in-giappone/index.html",
    "2021/07/16/nuovo-contenzioso-pre-pandemia-in-europa/index.html",
    "2021/10/08/la-riforma-in-itinere-della-mediazione-in-francia/index.html",
    "2021/12/10/la-riforma-del-processo-e-legge/index.html",
    "2021/12/16/considerazioni-a-caldo-sugli-strumenti-complementari-alla-giurisdizione-di-cui-alla-legge-26-novembre-2021-n-206/index.html",
    "2022/02/01/numero-dei-mediatori-nella-ue/index.html",
    "2022/08/03/il-possibile-futuro-del-testo-del-decreto-28-10-alla-luce-della-riforma-cartabia/index.html",
    "2022/08/09/relazione-illustrativa-e-tessuto-normativo-dello-schema-di-decreto-cartabia/index.html",
    "2022/09/19/pareri-del-parlamento-allo-schema-di-decreto-cartabia-sulla-giustizia-civile-atto-407/index.html",
    "2022/10/09/mozione-sulla-consulenza-e-negoziazione-assistita-da-avvocati-trasformata-in-raccomandazione-dal-congresso-nazionale-forense/index.html",
    "2022/10/09/mozione-sulla-mediazione-civile-e-familiare-trasformata-in-raccomandazione-dal-congresso-nazionale-forense/index.html",
    "2022/10/09/mozione-sulla-mediazione-familiare-trasformata-in-raccomandazione-dal-congresso-nazionale-forense/index.html",
    "2022/10/11/enneagramma-e-genogramma-a-casa-serra/index.html",
    "2022/10/17/la-riforma-cartabia-e-legge/index.html",
    "2022/10/18/decreto-legislativo-4-marzo-2010-n-28-attuale-e-dal-30-06-23/index.html",
    "2022/10/20/le-relazioni-alla-riforma-cartabia/index.html",
    "2022/10/24/il-ricorso-al-t-a-r-lazio-contro-u-n-a-m-e-la-giustizia-in-italia-dal-1875-al-1950/index.html",
    "2022/10/25/la-condizione-della-giustizia-civile/index.html",
    "2022/10/27/il-world-justice-project-2022-e-la-posizione-dellitalia/index.html",
    "2022/10/27/le-proposte-del-csm-bulgaro-in-tema-di-mediazione-alla-nuova-legge/index.html",
    "2022/10/28/il-consiglio-nazionale-di-mediazione-in-francia/index.html",
    "2022/10/30/i-44-fattori-dello-stato-di-diritto-in-italia/index.html",
    "2022/11/01/mediazione-e-gratuito-patrocinio-in-grecia/index.html",
    "2022/11/01/una-scheda-di-valutazione-per-mediatori/index.html",
    "2022/11/30/3896/index.html",
    "2022/12/08/la-mediazione-in-danimarca/index.html",
    "2022/12/11/la-tutela-la-conciliazione-larbitrato-e-la-mediazione-e-i-rapporti-tra-consanguinei-nellantichita/index.html",
    "2022/12/19/la-nuova-normativa-della-negoziazione-assistita-in-francia-un-confronto-con-quella-italiana/index.html",
    "2022/12/28/slitta-lapplicazione-nel-nostro-ordinamento-della-giustizia-riparativa/index.html",
    "2022/12/30/cenni-sulla-giustizia-riparativa/index.html",
    "2022/12/31/modifiche-temporali-al-decreto-legislativo-10-ottobre-2022-n-149/index.html",
    "2023/01/07/decreto-legislativo-4-marzo-2010-n-28-versione-2023/index.html",
    "2023/01/28/principali-documenti-sulla-giustizia-riparativa/index.html",
    "2023/02/02/la-negoziazione-assistita-e-la-formazione-dellavvocato/index.html",
    "2023/02/03/il-genogramma-teoria-e-pratica/index.html",
    "2023/02/07/sintesi-della-normativa-cartabia-la-nuova-mediazione-quando-entrera-in-vigore/index.html",
    "2023/02/08/corso-per-formatori-e-mediatori-del-coa-reggio-emilia/index.html",
    "2023/03/03/il-genogramma-teoria-e-pratica-2/index.html",
    "2023/03/03/stato-dellarte-del-decreto-28-10/index.html",
    "2023/03/23/la-formazione-del-mediatore-in-austria/index.html",
    "2023/03/24/il-mediatore-ue-e-la-sua-formazione/index.html",
    "2023/03/25/la-formazione-dellavvocato-e-del-giudice-mediatore-secondo-il-cepej/index.html",
    "2023/04/01/la-formazione-del-mediatore-in-belgio/index.html",
    "2023/04/05/corso-di-aggiornamento-per-mediatori-17-20-aprile-2023/index.html",
    "2023/04/06/circolare-del-ministero-della-giustizia-per-organismi-ed-enti-di-mediazione-del-6-04-23/index.html",
    "2023/04/15/circolare-del-ministero-della-giustizia-del-14-aprile-2023/index.html",
    "2023/04/20/un-posto-al-sole-ossia-nelle-riviste-anvur/index.html",
    "2023/04/30/il-valore-della-mediazione-nella-riforma-della-giustizia/index.html",
    "2023/05/24/in-attesa-della-novella-del-decreto-180-10/index.html",
    "2023/05/25/quanto-si-spende-per-mediare-in-cina-in-un-organismo-di-mediazione/index.html",
    "2023/05/31/il-477-articolo/index.html",
    "2023/06/06/discorso-del-ministro-della-giustizia-francese-sulla-giustizia-complementare-al-congresso-di-gemme/index.html",
    "2023/06/18/le-bozze-di-decreto-ministeriale-in-materia-di-mediazione-cec/index.html",
    "2023/06/20/sullincompatibilita-assoluta-del-mediatore-civile-e-commerciale-e-del-mediatore-familiare-ad-esercitare-la-mediazione-penale/index.html",
    "2023/07/04/pareri-sul-d-m-in-materia-di-giustizia-riparativa/index.html",
    "2023/07/05/usciti-i-decreti-ministeriali-sulla-giustizia-riparativa/index.html",
    "2023/07/10/quanto-guadagna-un-mediatore-civile-e-commerciale-nei-paesi-ue/index.html",
    "2023/07/13/quale-e-il-rapporto-delle-imprese-con-i-meccanismi-di-risoluzione-delle-dispute/index.html",
    "2023/07/14/family-mediation-panel-in-irlanda/index.html",
    "2023/07/24/il-mediatore-penale-a-seguito-della-riforma-cartabia/index.html",
    "2023/07/27/regolamento-relativo-alla-disciplina-del-trattamento-dei-dati-personali-da-parte-dei-centri-per-la-giustizia-riparativa/index.html",
    "2023/08/01/la-relazione-ue-sullo-stato-di-diritto-2023-in-italia/index.html",
    "2023/08/07/decreto-1-agosto-2023-disciplina-del-gratuito-patrocinio-in-mediazione/index.html",
    "2023/08/07/decreto-1-agosto-2023/index.html",
    "2023/08/10/nota-in-merito-ai-crediti-di-imposta-del-decreto-1-agosto-2023-23a04557/index.html",
    "2023/09/15/parere-del-consiglio-di-stato-sullo-schema-di-decreto-in-materia-di-mediazione/index.html",
    "2023/09/16/qualche-considerazione-circa-il-parere-del-consiglio-di-stato-sul-nuovo-regolamento-in-materia-di-mediazione/index.html",
    "2023/09/29/la-formazione-in-mediazione-oggi/index.html",
    "2023/10/17/via-libera-del-cds-al-decreto-mediazione/index.html",
    "2023/10/30/il-rapporto-wjp-globale-e-la-posizione-dellitalia/index.html",
    "2023/10/31/pubblicato-il-decreto-sulla-mediazione/index.html",
    "2023/11/01/il-nuovo-regolamento-della-mediazione-familiare/index.html",
    "2023/11/15/approfondire-la-giustizia-riparativa/index.html",
    "2023/12/30/una-giustizia-alta-e-altra/index.html",
    "2024/01/17/cade-lincompatibilita-tra-mediatori/index.html",
    "2024/02/15/il-compenso-dell-mediatore-nei-paesi-in-italia-e-nei-paesi-ue/index.html",
    "2024/02/17/qualche-considerazione-in-merito-allopera-mediazione-3-0-e-negoziazione-assistita-2-0-a-cura-di-tiziana-rosania-editore-giappichelli/index.html",
    "2024/03/24/statistica-della-mediazione-in-francia-nel-2021/index.html",
    "2024/03/25/dove-sta-andando-la-giustizia-europea-e-quella-italiana/index.html",
    "2024/04/13/la-valutazione-del-giudice-in-cina/index.html",
    "2024/04/14/la-nuova-giustizia-complementare-in-spagna/index.html",
    "2024/05/15/codici-tributo-per-crediti-di-imposta-e-gratuito-patrocinio-mediazione-e-negoziazione-assistita/index.html",
    "2024/06/12/quadro-di-valutazione-della-giustizia-ue-2024/index.html",
    "2024/07/02/dati-rilevanti-della-giustizia-italiana-2022-2024/index.html",
    "2024/07/14/direttiva-ue-2024-1385-sulla-lotta-alla-violenza-contro-le-donne-e-alla-violenza-domestica/index.html",
    "2024/09/12/scuola-di-alta-formazione-u-n-a-m/index.html",
    "2024/09/15/mediazione-obbligatoria-in-inghilterra-e-galles/index.html",
    "2025/01/15/correttivo-e-negoziazione-assistita/index.html",
    "2025/01/17/lorigine-della-mediazione-moderna-e-il-canone/index.html",
    "2025/03/17/importante-sentenza-del-tar-del-lazio-sulle-tariffe-di-mediazione-ed-altro/index.html",
    "2025/06/24/enneagramma-e-mediazione-strumenti-per-comunicare-meglio/index.html",
    "2025/08/10/quadro-di-valutazione-2025-e-caso-italia/index.html",
    "2025/09/03/il-legame-tra-strumenti-di-gestione-del-conflitto-e-letteratura-una-storia-intrecciata/index.html",
    "2025/11/25/la-giustizia-civile-nel-mondo-un-viaggio-tra-virtu-paradossi-e-urgenza-di-riforme/index.html",
    "2026/01/08/la-giustizia-italiana-al-bivio-perche-la-mediazione-e-la-vera-riforma-di-cui-abbiamo-bisogno/index.html",
    "2026/01/13/tra-ordine-cosmico-e-legge-dello-stato-unanalisi-comparata-dei-sistemi-di-giustizia-nel-mondo-antico/index.html",
    "2026/02/18/mediazione-e-causa-ordinaria-trasparenza-sui-costi-come-strumento-di-orientamento-professionale/index.html",
    "2026/02/20/enneagramma-evolutivo/index.html",
    "2026/02/27/giustizia-complementare-e-intelligenza-artificiale/index.html",
    "2026/03/14/5055/index.html",
    "2026/03/15/tra-sportule-e-riforme-a-costo-zero-linee-per-una-critica-storica-della-giustizia-italiana/index.html",
    "2026/03/17/laltra-faccia-dellia-quando-lalgoritmo-sospende-il-professionista-e-chi-paga-davvero-il-prezzo-dellerrore/index.html",
    "2026/03/19/quando-i-numeri-diventano-strategia-maan-zopa-e-bias-cognitivi-nella-mediazione-e-uno-strumento-per-calcolarli/index.html",
    "2026/03/26/enneagramma-ed-analisi-transazionale-al-servizio-della-mediazione-il-progetto-enneagrammaevolutivo-it/index.html",
    "2026/04/25/olismo-integrato-il-nuovo-portale-di-mediazione-con-strumenti-ai/index.html",
    "2026/05/07/la-psicologia-del-conflitto-e-i-bias-cognitivi-nella-mediazione-civile/index.html",
    "2026/05/28/la-soglia-che-non-si-oltrepassa/index.html",
    "2026/06/23/mediazione-amministrativa-a-ginevra/index.html",
    "2026/06/24/lanalisi-transazionale-al-tavolo-di-mediazione/index.html",
    "2026/06/26/che-cosa-puo-fare-la-mediazione/index.html",
    "2026/07/05/la-mediazione-civile-in-italia-nei-numeri/index.html",
    "2026/07/07/la-mediazione-nel-mondo-una-mappa-comparata-di-195-ordinamenti/index.html",
    "2026/08/11/le-esperienze-straniere-che-litalia-potrebbe-recepire-per-favorire-la-diffusione-della-mediazione-e-del-componimento-bonario/index.html",
    "la-legislazione-della-mediazione-belize/index.html",
]


def fix_wp_comments():
    results = []
    for rel in WP_COMMENT_PAGES:
        path = os.path.join(ROOT, rel)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if "wp:" not in content:
            results.append(("skip-already", rel))
            continue

        new_content, n = WP_COMMENT_RE.subn("", content)
        if n == 0:
            results.append(("error-no-match", rel))
            continue

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        results.append((f"fixed ({n} commenti)", rel))
    return results


# ---------------------------------------------------------------------------
# 4. <h1> multipli (fuori dal titolo di pagina) -> <h2>
# ---------------------------------------------------------------------------

H1_MULTI_PAGES = [
    "2014/01/18/la-legislazione-della-mediazione-nuova-zelanda-news/index.html",
    "2014/10/24/arbitrato-e-negoziazione-assistita-al-231014-approvazione-del-senato/index.html",
    "2014/11/11/da-oggi-in-vigore-la-legge-sulla-negoziazione-assistita-e-sullarbitrato-endoprocessuale/index.html",
    "2015/02/10/entrata-in-vigore-la-negoziazione-assistita-come-condizione-di-procedibilita/index.html",
    "2015/04/23/per-il-2016-lirlanda-annuncia-la-riforma-della-mediazione/index.html",
    "2022/10/20/le-relazioni-alla-riforma-cartabia/index.html",
    "2023/07/05/usciti-i-decreti-ministeriali-sulla-giustizia-riparativa/index.html",
    "2026/02/20/enneagramma-evolutivo/index.html",
    "2026/03/19/quando-i-numeri-diventano-strategia-maan-zopa-e-bias-cognitivi-nella-mediazione-e-uno-strumento-per-calcolarli/index.html",
    "2026/06/23/mediazione-amministrativa-a-ginevra/index.html",
    "2026/06/26/che-cosa-puo-fare-la-mediazione/index.html",
    "2026/07/05/la-mediazione-civile-in-italia-nei-numeri/index.html",
]

def fix_h1_multipli():
    results = []
    h1_pair_re = re.compile(r"<h1(\s[^>]*)?>(.*?)</h1>", re.DOTALL)
    for rel in H1_MULTI_PAGES:
        path = os.path.join(ROOT, rel)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        matches = list(h1_pair_re.finditer(content))
        if len(matches) <= 1:
            results.append(("skip-already", rel))
            continue

        out = []
        last_end = 0
        for i, m in enumerate(matches):
            out.append(content[last_end:m.start()])
            attrs = m.group(1) or ""
            inner = m.group(2)
            if i == 0:
                out.append(m.group(0))  # titolo di pagina, invariato
            else:
                out.append(f"<h2{attrs}>{inner}</h2>")
            last_end = m.end()
        out.append(content[last_end:])
        new_content = "".join(out)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        results.append((f"fixed ({len(matches) - 1} h1->h2)", rel))
    return results


# ---------------------------------------------------------------------------
# 5. Immagine con sorgente esterna morta (s0.wp.com) - post "Analisi del 2014"
# ---------------------------------------------------------------------------

def fix_dead_image_analisi_2014():
    rel = "2015/01/01/analisi-del-2014/index.html"
    path = os.path.join(ROOT, rel)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "s0.wp.com" not in content:
        return [("skip-already", rel)]

    old_img_block = (
        '<a href="http://mediaresenzaconfini.org/2014/annual-report/">'
        '<img src="//s0.wp.com/wp-content/mu-plugins/annual-reports/img/2014-emailteaser.png" '
        'alt="Illustrazione del rapporto annuale di WordPress.com" width="100%" /></a>\n\n'
    )
    old_link_line = (
        '<a href="http://mediaresenzaconfini.org/2014/annual-report/">'
        'Clicca qui per vedere il rapporto completo.</a>\n'
    )

    if old_img_block not in content:
        return [("error-img-block-not-found", rel)]
    if old_link_line not in content:
        return [("error-link-line-not-found", rel)]

    new_content = content.replace(old_img_block, "", 1)
    new_content = new_content.replace(old_link_line, "", 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return [("fixed", rel)]


def main():
    print("== 1. Canonical mancanti ==")
    for status, rel in fix_canonical():
        print(f"{status}\t{rel}")

    print("\n== 2. Meta description mancanti ==")
    for status, rel in fix_missing_descriptions():
        print(f"{status}\t{rel}")

    print("\n== 3. Commenti WordPress residui ==")
    wp_results = fix_wp_comments()
    fixed = [r for r in wp_results if r[0].startswith("fixed")]
    other = [r for r in wp_results if not r[0].startswith("fixed")]
    print(f"fixed: {len(fixed)} pagine")
    for status, rel in other:
        print(f"{status}\t{rel}")

    print("\n== 4. <h1> multipli -> <h2> ==")
    for status, rel in fix_h1_multipli():
        print(f"{status}\t{rel}")

    print("\n== 5. Immagine sorgente esterna morta ==")
    for status, rel in fix_dead_image_analisi_2014():
        print(f"{status}\t{rel}")


if __name__ == "__main__":
    main()
