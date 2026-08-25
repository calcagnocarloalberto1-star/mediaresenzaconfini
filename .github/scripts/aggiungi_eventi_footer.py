#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggiunge il link "Eventi" al footer di tutte le pagine del sito.

Il footer contiene una riga di link (Chi sono/Chi siamo, Link utili,
Statistiche, Contatti, Privacy, Cookie, a volte Pubblica o Feed RSS) che
finora non includeva la nuova sezione Eventi. Questo script aggiunge
"Eventi" come ultimo link di quella riga, su tutte le varianti trovate nel
sito (compresa quella minimale con il solo "Chi siamo").

Non riscrive l'HTML: individua la riga dei link del footer con una regex
mirata sul solo contenuto di quel <div> (che non contiene mai markup
annidato) e inserisce il nuovo link subito prima della chiusura </div>,
lasciando il resto della pagina identico. È ripetibile: le pagine che hanno
già il link vengono saltate.
"""
import glob, re, sys, json

LINK_EVENTI = '<a href="/categoria/eventi/">Eventi</a>'

FOOTER_LINKS_RE = re.compile(
    r'(<div><a href="/about/">Chi (?:sono|siamo)</a>.*?)(</div>)'
)

def adatta(percorso):
    """Ritorna (serve, nuovo_contenuto|None)."""
    s = open(percorso, encoding='utf-8').read()
    m = FOOTER_LINKS_RE.search(s)
    if not m:
        return False, None                      # nessun footer noto
    if '/categoria/eventi/' in m.group(0):
        return False, None                      # già presente: ripetibile
    nuovo = (s[:m.start()] + m.group(1) + ' &middot; ' + LINK_EVENTI
             + m.group(2) + s[m.end():])
    return True, nuovo

def main():
    prova = '--prova' in sys.argv
    fatti, elenco = 0, []
    file_html = set(glob.glob('**/index.html', recursive=True))
    file_html.add('404.html')
    for f in sorted(file_html):
        if f.startswith(('.git/', 'node_modules/')) or not glob.os.path.isfile(f):
            continue
        serve, nuovo = adatta(f)
        if not serve:
            continue
        fatti += 1
        elenco.append(f)
        if not prova:
            open(f, 'w', encoding='utf-8').write(nuovo)
    print('Pagine a cui è stato aggiunto il link Eventi nel footer: %d' % fatti)
    if prova:
        print('(prova: nessun file scritto)')
        json.dump(elenco, open('/tmp/elenco-footer-eventi.json', 'w'))

if __name__ == '__main__':
    main()
