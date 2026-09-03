#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera static/articles.json: un elenco di tutti gli articoli del blog
(titolo, url, data, categoria, estratto), dal piu' recente al piu' vecchio,
usato dalla home per paginare la sezione "Ultimi articoli" a blocchi via
JavaScript (frecce avanti/indietro), senza dover generare centinaia di
pagine statiche.

Riguarda solo gli articoli veri (percorso AAAA/MM/GG/slug/index.html).
Va lanciato con la working directory sulla radice del repository (come
fanno tutti gli altri script in .github/scripts).
Ripetibile: riscrive sempre l'elenco, ma aggiorna il file solo se il
contenuto e' effettivamente cambiato (idempotente per la CI).
"""
import glob, json, re, html
from pathlib import Path

ARTICOLO_RE = re.compile(r'^\d{4}/\d{2}/\d{2}/[^/]+/index\.html$')


def trova_articoli():
    file = [f for f in glob.glob('[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/*/index.html') if ARTICOLO_RE.match(f)]

    def chiave(f):
        parti = f.split('/')
        return (int(parti[0]), int(parti[1]), int(parti[2]), f)

    return sorted(file, key=chiave)


def estrai(percorso):
    s = open(percorso, encoding='utf-8').read()

    m = re.search(r'<div class="post-header">.*?<h1>(.*?)</h1>', s, re.S)
    titolo = re.sub('<[^>]+>', '', m.group(1)).strip() if m else None

    m = re.search(r'<div class="post-meta">(.*?)</div>', s, re.S)
    meta_blocco = m.group(1) if m else ''

    m = re.search(r'<span>(.*?)</span>', meta_blocco, re.S)
    data_vis = re.sub('<[^>]+>', '', m.group(1)).strip() if m else None

    m = re.search(r'class="tag-pill"[^>]*>(.*?)<', meta_blocco, re.S)
    categoria = re.sub('<[^>]+>', '', m.group(1)).strip() if m else ''

    m = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
    estratto = html.unescape(m.group(1)).strip() if m else ''

    if not titolo or not data_vis:
        return None

    return {
        'titolo': html.unescape(titolo),
        'data': html.unescape(data_vis),
        'categoria': html.unescape(categoria),
        'estratto': estratto,
    }


def url_di(f):
    return '/' + '/'.join(f.split('/')[:-1]) + '/'


def main():
    file = trova_articoli()
    articoli = []
    mancanti = []
    for f in reversed(file):  # dal piu' recente al piu' vecchio
        dati = estrai(f)
        if not dati:
            mancanti.append(f)
            continue
        dati['url'] = url_di(f)
        articoli.append(dati)

    out_path = Path('static/articles.json')
    nuovo = json.dumps(articoli, ensure_ascii=False, separators=(',', ':')) + '\n'
    vecchio = out_path.read_text(encoding='utf-8') if out_path.exists() else None
    if nuovo != vecchio:
        out_path.write_text(nuovo, encoding='utf-8')
        print(f'static/articles.json aggiornato: {len(articoli)} articoli')
    else:
        print(f'static/articles.json gia aggiornato: {len(articoli)} articoli')
    if mancanti:
        print('ATTENZIONE, file senza titolo/data estratti:', mancanti)


if __name__ == '__main__':
    main()
