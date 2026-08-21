#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggiunge il lettore vocale «Ascolta l'articolo» alle pagine degli articoli.

Il lettore è un solo file, static/js/ascolta.js, ma non esiste un template
condiviso: ogni pagina deve dichiararlo per conto proprio con una riga prima
di </body>. Finora era su 8 pagine soltanto.

Il lettore si disegna da sé e non ha bisogno d'altro: se in una pagina non
trova article.post con .post-header e .post-body, esce in silenzio senza
lasciare traccia. Qui però la riga si aggiunge SOLO alle pagine dove funziona
davvero, per non appesantire inutilmente le altre.

Non riscrive l'HTML: inserisce la riga nel testo originale prima dell'ultimo
</body> e lascia tutto il resto identico. È ripetibile: le pagine che hanno
già la riga vengono saltate.
"""
import glob, sys, json
from bs4 import BeautifulSoup

RIGA = '<script src="/static/js/ascolta.js" defer></script>\n'

def adatta(percorso):
    """Ritorna (serve, nuovo_contenuto|None)."""
    s = open(percorso, encoding='utf-8').read()
    if 'ascolta.js' in s:
        return False, None                      # già presente: ripetibile
    if 'post-body' not in s or 'post-header' not in s:
        return False, None                      # scarto rapido, senza parsing
    soup = BeautifulSoup(s, 'html.parser')
    art = soup.select_one('article.post')
    if not art: return False, None
    if not art.select_one('.post-header') or not art.select_one('.post-body'):
        return False, None
    i = s.rfind('</body>')
    if i == -1: return False, None
    return True, s[:i] + RIGA + s[i:]

def main():
    prova = '--prova' in sys.argv
    fatti, elenco = 0, []
    for f in sorted(glob.glob('**/index.html', recursive=True)):
        if f.startswith(('.git/', 'node_modules/')): continue
        serve, nuovo = adatta(f)
        if not serve: continue
        fatti += 1; elenco.append(f)
        if not prova:
            open(f, 'w', encoding='utf-8').write(nuovo)
    print('Pagine a cui è stato aggiunto il lettore: %d' % fatti)
    if prova:
        print('(prova: nessun file scritto)')
        json.dump(elenco, open('/tmp/elenco-lettore.json', 'w'))

if __name__ == '__main__':
    main()
