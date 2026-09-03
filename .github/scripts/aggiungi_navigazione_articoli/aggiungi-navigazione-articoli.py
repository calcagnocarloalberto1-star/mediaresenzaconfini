#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggiunge due mini-barre di navigazione (frecce avanti/indietro + home) in
cima e in fondo agli articoli del blog: link all'articolo precedente, alla
home, e all'articolo successivo, in ordine cronologico di pubblicazione.

Riguarda solo gli articoli veri (percorso AAAA/MM/GG/slug/index.html), non le
pagine di paese o le altre pagine statiche del sito.

Non riscrive l'HTML: inserisce due frammenti nel testo originale (uno dopo il
breadcrumb, uno dopo </article>) e lascia tutto il resto identico. È
ripetibile: le pagine che hanno già la classe post-nav vengono saltate.
"""
import glob, sys, json, re, html

ARTICOLO_RE = re.compile(r'^\d{4}/\d{2}/\d{2}/[^/]+/index\.html$')


def trova_articoli():
    file = [f for f in glob.glob('[12][0-9][0-9][0-9]/*/*/*/index.html') if ARTICOLO_RE.match(f)]

    def chiave(f):
        parti = f.split('/')
        return (int(parti[0]), int(parti[1]), int(parti[2]), f)

    return sorted(file, key=chiave)


def estrai_titolo(s):
    m = re.search(r'<div class="post-header">.*?<h1>(.*?)</h1>', s, re.S)
    if not m:
        return None
    return re.sub('<[^>]+>', '', m.group(1)).strip()


def tronca(t, n=48):
    t = html.unescape(t)
    if len(t) <= n:
        return html.escape(t)
    return html.escape(t[:n].rstrip() + '…')


def url_di(f):
    return '/' + '/'.join(f.split('/')[:-1]) + '/'


def costruisci_nav(prev, nxt, classe):
    prev_html = (f'<a href="{url_di(prev[0])}" class="post-nav-prev">&larr; {tronca(prev[1])}</a>'
                 if prev else '<span class="post-nav-empty"></span>')
    next_html = (f'<a href="{url_di(nxt[0])}" class="post-nav-next">{tronca(nxt[1])} &rarr;</a>'
                 if nxt else '<span class="post-nav-empty"></span>')
    return (f'<nav class="post-nav {classe}" aria-label="Navigazione articoli">\n'
            f'{prev_html}\n<a href="/" class="post-nav-home">Home</a>\n{next_html}\n</nav>\n')


def adatta(percorso, prev, nxt):
    s = open(percorso, encoding='utf-8').read()
    if 'post-nav' in s:
        return False, None  # già presente: ripetibile
    if 'post-header' not in s or 'post-body' not in s or '<article class="post">' not in s:
        return False, None

    nav_top = costruisci_nav(prev, nxt, 'post-nav-top')
    nav_bottom = costruisci_nav(prev, nxt, 'post-nav-bottom')

    m = re.search(r'(<div class="breadcrumb">.*?</div>\s*\n)(<article class="post">)', s, re.S)
    if not m:
        return False, None
    s2 = s[:m.end(1)] + nav_top + s[m.end(1):]

    m2 = re.search(r'(</article>\s*\n\s*</main>)', s2, re.S)
    if not m2:
        return False, None
    s2 = s2[:m2.start(1)] + nav_bottom + '\n' + s2[m2.start(1):]

    return True, s2


def main():
    prova = '--prova' in sys.argv
    file = trova_articoli()
    titoli = {}
    for f in file:
        s = open(f, encoding='utf-8').read()
        titoli[f] = estrai_titolo(s) or f

    fatti, elenco = 0, []
    for i, f in enumerate(file):
        prev = (file[i - 1], titoli[file[i - 1]]) if i > 0 else None
        nxt = (file[i + 1], titoli[file[i + 1]]) if i < len(file) - 1 else None
        serve, nuovo = adatta(f, prev, nxt)
        if not serve:
            continue
        fatti += 1
        elenco.append(f)
        if not prova:
            open(f, 'w', encoding='utf-8').write(nuovo)

    print('Articoli trovati: %d' % len(file))
    print('Pagine a cui sono state aggiunte le frecce di navigazione: %d' % fatti)
    if prova:
        print('(prova: nessun file scritto)')
    json.dump(elenco, open('/tmp/elenco-post-nav.json', 'w'))


if __name__ == '__main__':
    main()
