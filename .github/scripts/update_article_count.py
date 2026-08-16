"""Calcola il numero di articoli pubblicati (file YYYY/MM/DD/slug/index.html)
e lo scrive in static/article-count.json, cosi' la homepage puo' leggerlo
con un fetch same-origin invece di interrogare l'API di GitHub lato client
a ogni caricamento pagina (issue #9)."""
import json
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
matches = sorted(repo_root.glob('[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]/*/index.html'))
count = len(matches)

out_path = repo_root / 'static' / 'article-count.json'
out_path.write_text(json.dumps({'count': count}) + '\n', encoding='utf-8')

print(f'Articoli trovati: {count}')
