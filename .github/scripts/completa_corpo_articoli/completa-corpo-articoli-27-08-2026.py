#!/usr/bin/env python3
"""
Script idempotente: sostituisce il corpo-articolo bugged ("None", risultato di
un fallimento della migrazione automatica da WordPress) con una nota redazionale
scritta ex novo, basata su fonti pubbliche, per le 2 pagine individuate durante
la risoluzione dei punti aperti dell'audit generale del 26/08/2026 (vedi
claude/handoff-punti-aperti-26-08-2026.md). Il testo originale di queste 2
pagine non è recuperabile: il vecchio dominio mediaresenzaconfini.org da cui il
sito è stato migrato oggi reindirizza a una pagina di domain-parking vuota.

Decisione confermata da Carlo Alberto Calcagno il 27/08/2026: scrivere una nota
nuova nello stile editoriale del sito, basata su fonti pubbliche verificate,
invece di lasciare il bug visibile o attendere il recupero del testo originale.
"""
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."

OLD_BLOCK = '<div class="post-body">\n    None\n  </div>'

REPLACEMENTS = {
    "2017/03/21/annullabile-il-regolamento-di-mediazione-che-vieti-di-proporre-tar-abruzzo-pescara-sez-i-sentenza-n-9817/index.html": (
        '<div class="post-body">\n'
        '<p class="has-text-align-justify">Con la sentenza n. 98 del 2017 il TAR Abruzzo, sede di Pescara, sez. I, ha annullato le disposizioni del regolamento di un organismo di mediazione che vietavano al mediatore di formulare la proposta di conciliazione quando una delle parti non avesse partecipato al procedimento o si fosse opposta alla sua formulazione.</p>\n'
        '\n'
        '<p class="has-text-align-justify">Il Collegio ha ritenuto tali previsioni regolamentari in contrasto con l’art. 11 del d.lgs. 4 marzo 2010, n. 28, norma primaria che consente al mediatore di formulare la proposta anche in assenza di una richiesta congiunta delle parti in tal senso. Una fonte regolamentare secondaria, hanno osservato i giudici amministrativi, non può comprimere una facoltà che la legge attribuisce espressamente al mediatore.</p>\n'
        '\n'
        '<p class="has-text-align-justify">La pronuncia va salutata con favore: la funzione della mediazione non si esaurisce nella mera verbalizzazione delle posizioni delle parti, ma richiede al mediatore un ruolo attivo, anche quando una parte diserta l’incontro o si oppone al confronto. Svuotare per via regolamentare questo potere significherebbe tradire la funzione deflativa dell’istituto.</p>\n'
        '  </div>'
    ),
    "2022/09/29/il-consiglio-dei-ministri-ha-approvato-il-28-settembre-la-riforma-della-giustizia/index.html": (
        '<div class="post-body">\n'
        '<p class="has-text-align-justify">Il Consiglio dei Ministri, nella riunione del 28 settembre 2022, ha approvato in esame preliminare i decreti legislativi di attuazione della riforma della giustizia penale e delle norme sull’ufficio per il processo, in attuazione delle deleghe conferite con la legge 27 settembre 2021, n. 134 e con la legge 26 novembre 2021, n. 206.</p>\n'
        '\n'
        '<p class="has-text-align-justify">I provvedimenti intervengono sul procedimento penale, sul sistema sanzionatorio e sulla giustizia riparativa, e disciplinano il potenziamento dell’ufficio per il processo, la struttura organizzativa pensata per affiancare i magistrati nella gestione dei procedimenti e ridurre l’arretrato, anche in vista degli obiettivi di riduzione della durata dei processi fissati dal PNRR.</p>\n'
        '\n'
        '<p class="has-text-align-justify">Si tratta di un ulteriore passaggio del più ampio disegno di riorganizzazione della giustizia italiana avviato in questa legislatura, che nei mesi precedenti aveva già interessato il processo civile e la mediazione.</p>\n'
        '  </div>'
    ),
}


def main():
    results = []
    for rel, new_block in REPLACEMENTS.items():
        path = os.path.join(ROOT, rel)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if OLD_BLOCK not in content:
            if new_block in content:
                results.append(("skip-already", rel))
            else:
                results.append(("error-block-not-found", rel))
            continue
        new_content = content.replace(OLD_BLOCK, new_block, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        results.append(("fixed", rel))

    print("=== Completamento corpo-articolo mancante (bug 'None') ===")
    for status, rel in results:
        print(f"{status}\t{rel}")
    print(f"\nTotale: {len(results)}")


if __name__ == "__main__":
    main()
