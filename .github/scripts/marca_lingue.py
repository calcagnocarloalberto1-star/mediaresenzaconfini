#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggiunge l'attributo lang ai passaggi in lingua straniera.

PERCHÉ. Le pagine dichiarano <html lang="it">. Un lettore di schermo si fida
di quella dichiarazione e legge TUTTO con fonetica italiana, comprese le
centinaia di citazioni di leggi straniere. Il risultato, per chi ascolta, è
incomprensibile. Marcando il singolo blocco con la sua lingua, il lettore di
schermo cambia voce e pronuncia da solo.

PRINCIPIO DI PRUDENZA. Un lang sbagliato è PEGGIO di nessun lang. Perciò le
soglie sono severe e, nel dubbio, il blocco resta senza attributo. In
particolare non si marcano i blocchi misti: sul sito è frequentissima la frase
italiana che cita un testo straniero fra virgolette o fra parentesi.

COME MODIFICA I FILE. Non riscrive l'HTML: BeautifulSoup serve solo a
individuare gli elementi, poi l'attributo viene inserito nel testo originale
alla posizione esatta del tag. Il file resta identico a se stesso tranne le
stringhe ' lang="xx"' aggiunte. È ripetibile: gli elementi che hanno già lang
vengono saltati.
"""
import glob, re, sys, json
from bs4 import BeautifulSoup
from lingua import Language, LanguageDetectorBuilder

# ----------------------------------------------------------------- parametri
BLOCCHI      = ['p', 'li', 'blockquote', 'td', 'th', 'h2', 'h3', 'h4', 'dd', 'dt']
CONTENITORI  = ['.post-body', '.law-fulltext']
MIN_PAROLE      = 8
MIN_FIDUCIA     = 0.85
MIN_STACCO      = 0.60
MIN_PAROLE_SEGM = 5
ESCLUSE      = {'la', 'yo'}   # v. relazione in fondo
VIRGOLETTE   = r'[«»""„‟\'"]'

det = LanguageDetectorBuilder.from_all_languages().with_preloaded_language_models().build()
_cache = {}

def rileva(s):
    if s in _cache: return _cache[s]
    v = det.compute_language_confidence_values(s)
    it = next((x.value for x in v if x.language == Language.ITALIAN), 0.0)
    r = (v[0].language, v[0].value, it)
    if len(_cache) < 200000: _cache[s] = r
    return r

def pulisci(t):
    t = re.sub(r'\[\d+\]', ' ', t)
    t = re.sub(r'https?://\S+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def segmenti(t):
    pezzi = re.split(VIRGOLETTE + r'|(?<=[.;:!?])\s+', t)
    return [p.strip() for p in pezzi if p and len(p.split()) >= MIN_PAROLE_SEGM]

def fuori_citazioni(t):
    s = re.sub('«[^»]*»', ' ', t)
    s = re.sub('"[^"]*"', ' ', s)
    s = re.sub('“[^”]*”', ' ', s)
    s = re.sub(r'\([^)]*\)', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def lingua_del_blocco(testo):
    t = pulisci(testo)
    if len(t.split()) < MIN_PAROLE: return None
    lg, conf, conf_it = rileva(t)
    if lg is None or lg == Language.ITALIAN: return None
    codice = lg.iso_code_639_1.name.lower()
    if codice in ESCLUSE: return None
    if conf < MIN_FIDUCIA: return None
    if conf - conf_it < MIN_STACCO: return None
    fc = fuori_citazioni(t)
    if len(fc.split()) >= MIN_PAROLE_SEGM and rileva(fc)[0] == Language.ITALIAN:
        return None
    segs = segmenti(t)
    if len(segs) >= 2:
        voti = [rileva(s)[0] for s in segs]
        if any(v == Language.ITALIAN for v in voti): return None
        if sum(1 for v in voti if v == lg) < len(voti) * 0.7: return None
    return codice

# ------------------------------------------------- inserimento nell'originale
def offset_righe(testo):
    off, acc = [0], 0
    for riga in testo.splitlines(keepends=True):
        acc += len(riga); off.append(acc)
    return off

def marca_file(percorso):
    originale = open(percorso, encoding='utf-8').read()
    if 'post-body' not in originale and 'law-fulltext' not in originale:
        return 0, None
    soup = BeautifulSoup(originale, 'html.parser')
    corpo = None
    for sel in CONTENITORI:
        corpo = soup.select_one(sel)
        if corpo: break
    if corpo is None: return 0, None

    off = offset_righe(originale)
    inserimenti = []
    for el in corpo.find_all(BLOCCHI):
        if el.find(BLOCCHI): continue
        if el.get('lang'): continue
        # antenati gia' marcati, ma solo DENTRO il corpo dell'articolo:
        # <html lang="it"> e' l'antenato di tutto e non deve bloccare nulla.
        gia_marcato = False
        p = el.parent
        while p is not None and p is not corpo:
            if getattr(p, 'get', None) and p.get('lang'): gia_marcato = True; break
            p = p.parent
        if gia_marcato: continue
        if el.sourceline is None or el.sourcepos is None: continue
        codice = lingua_del_blocco(el.get_text(' ', strip=True))
        if not codice: continue
        inizio = off[el.sourceline - 1] + el.sourcepos
        # verifica che qui cominci davvero il tag atteso
        atteso = '<' + el.name
        if not originale.startswith(atteso, inizio): continue
        dopo_nome = inizio + len(atteso)
        if originale[dopo_nome] not in ' \t\n>/': continue   # es. <p vs <pre
        inserimenti.append((dopo_nome, ' lang="%s"' % codice))

    if not inserimenti: return 0, None
    nuovo, prec = [], 0
    for pos, testo in sorted(inserimenti):
        nuovo.append(originale[prec:pos]); nuovo.append(testo); prec = pos
    nuovo.append(originale[prec:])
    return len(inserimenti), ''.join(nuovo)

def main():
    prova = '--prova' in sys.argv
    files = sorted(glob.glob('**/index.html', recursive=True))
    tot_file = tot_marche = 0
    dettaglio = {}
    for f in files:
        if f.startswith(('.git/', 'node_modules/')): continue
        n, nuovo = marca_file(f)
        if n and nuovo:
            tot_file += 1; tot_marche += n; dettaglio[f] = n
            if not prova:
                open(f, 'w', encoding='utf-8').write(nuovo)
    print('File modificati: %d — attributi lang aggiunti: %d' % (tot_file, tot_marche))
    if prova:
        json.dump(dettaglio, open('/tmp/dettaglio-prova.json', 'w'))
        print('(prova: nessun file scritto)')

if __name__ == '__main__':
    main()
