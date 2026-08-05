# -*- coding: utf-8 -*-
"""Télécharge les données items/panoplies/conditions depuis l'API DofusDude (Dofus 3/Unity)."""
import json
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data'
BASE = 'https://api.dofusdu.de/dofus3/v1/fr'
FILES = {
    'equipment_all.json': f'{BASE}/items/equipment/all',
    'sets_all.json': f'{BASE}/sets/all',
    'eq_cond.json': f'{BASE}/items/equipment/all?fields%5Bitem%5D=conditions',
}


def main():
    DATA.mkdir(exist_ok=True)
    for name, url in FILES.items():
        dest = DATA / name
        print(f'{name} <- {url}')
        with urllib.request.urlopen(url, timeout=120) as r:
            dest.write_bytes(r.read())
        n = len(json.load(open(dest, encoding='utf-8')).get('items', []))
        print(f'  ok ({n or "?"} entrées)')


if __name__ == '__main__':
    main()
