#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggiunge il box commenti (giscus, basato su GitHub Discussions) in fondo
agli articoli del blog, subito prima della chiusura </article>.

Riguarda solo gli articoli veri (percorso AAAA/MM/GG/slug/index.html), non le
pagine di paese o le altre pagine statiche del sito.

Non riscrive l'HTML: inserisce un frammento nel testo originale, appena
prima di </article>, e lascia tutto il resto identico. È ripetibile: le
pagine che hanno già la classe post-comments vengono saltate.

Valori data-repo-id / data-category-id: da compilare con quelli generati su
https://giscus.app dopo aver installato l'app giscus sulla repository
(https://github.com/apps/giscus) e verificato che GitHub Discussions sia
attivo (categoria "Comments").
"""
import glob
import json
import re
import sys

ARTICOLO_RE = re.compile(r'^\d{4}/\d{2}/\d{2}/[^/]+/index\.html$')

REPO = "calcagnocarloalberto1-star/mediaresenzaconfini"
REPO_ID = "R_kgDOT2AL1A"
CATEGORY = "Comments"
CATEGORY_ID = "DIC_kwDOT2AL1M4DDOZM"

GISCUS_HTML = f'''<div class="post-comments">
<script src="https://giscus.app/client.js"
  data-repo="{REPO}"
  data-repo-id="{REPO_ID}"
  data-category="{CATEGORY}"
  data-category-id="{CATEGORY_ID}"
  data-mapping="pathname"
  data-strict="0"
  data-reactions-enabled="1"
  data-emit-metadata="0"
  data-input-position="bottom"
  data-theme="light"
  data-lang="it"
  crossorigin="anonymous"
  async>
</script>
</div>
'''


def trova_articoli():
    file = [f for f in glob.glob('[12][0-9][0-9][0-9]/*/*/*/index.html') if ARTICOLO_RE.match(f)]
    return sorted(file)


def adatta(percorso):
    s = open(percorso, encoding='utf-8').read()
    if 'post-comments' in s:
        return False, None  # già presente: ripetibile
    if '<article class="post">' not in s or '</article>' not in s:
        return False, None

    m = re.search(r'(</article>)', s)
    if not m:
        return False, None
    s2 = s[:m.start(1)] + GISCUS_HTML + s[m.start(1):]
    return True, s2


def main():
    prova = '--prova' in sys.argv
    if REPO_ID.endswith('_DA_COMPILARE') or CATEGORY_ID.endswith('_DA_COMPILARE'):
        print('ERRORE: REPO_ID / CATEGORY_ID non ancora compilati nello script. '
              'Vai su https://giscus.app, configura la repository e incolla i valori generati.')
        sys.exit(1)

    file = trova_articoli()
    fatti, elenco = 0, []
    for f in file:
        serve, nuovo = adatta(f)
        if not serve:
            continue
        fatti += 1
        elenco.append(f)
        if not prova:
            open(f, 'w', encoding='utf-8').write(nuovo)

    print('Articoli trovati: %d' % len(file))
    print('Pagine a cui è stato aggiunto il box commenti: %d' % fatti)
    if prova:
        print('(prova: nessun file scritto)')
    json.dump(elenco, open('/tmp/elenco-commenti-giscus.json', 'w'))


if __name__ == '__main__':
    main()
