# -*- coding: utf-8 -*-
"""Construit docs/webdata.json — données slim pour l'optimiseur navigateur."""
import json
from pathlib import Path

import engine as M2

ROOT = Path(__file__).resolve().parent
KEEP = set(M2.RES_NAMES) | {
    'PA', 'PM', 'Portée', 'Vitalité', 'Force', 'Intelligence', 'Chance', 'Agilité',
    'Puissance', 'Sagesse', '% Critique', 'Dommage', 'Dommage Terre', 'Dommage Feu',
    'Dommage Eau', 'Dommage Air', 'Dommage Neutre', 'Dommage Critiques',
    '% Dommages aux sorts', '% Dommages mêlée', '% Résistance mêlée',
    '% Résistance distance', 'Résistance Critiques', 'Tacle', 'Fuite',
    'Esquive PA', 'Esquive PM', 'Retrait PA', 'Retrait PM', 'Soin',
}


def slim_effects(effects):
    out = {}
    for e in effects or []:
        if e['type'].get('is_active'):
            continue
        n = e['type']['name']
        if n not in KEEP:
            continue
        lo, hi = e.get('int_minimum') or 0, e.get('int_maximum') or 0
        prev = out.get(n, [0, 0])
        out[n] = [prev[0] + lo, prev[1] + (hi or lo)]
    return out


def main():
    items, sets, _ = M2.load_data(dofus_allowed=True)
    slim_items = []
    for it in items:
        eff = slim_effects(it.get('effects'))
        if not eff and it['type']['name'] not in ('Dofus', 'Trophée', 'Prysmaradite'):
            continue
        slim_items.append({
            'id': it['ankama_id'], 'n': it['name'], 't': it['type']['name'],
            'lv': it['level'], 'ic': it['image_urls']['icon'],
            'fx': eff, 'cd': it['_conds'],
            'set': it['parent_set']['id'] if it.get('parent_set') else 0,
        })
    slim_sets = {}
    for sid, s in sets.items():
        eff = {k: slim_effects(v) for k, v in (s.get('effects') or {}).items()}
        eff = {k: v for k, v in eff.items() if v}
        if eff:
            slim_sets[sid] = eff
    spells = json.load(open(ROOT / 'data' / 'spells.json', encoding='utf-8'))
    data = {'items': slim_items, 'sets': slim_sets, 'spells': spells}
    out = ROOT / 'docs' / 'webdata.json'
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'{out}: {out.stat().st_size // 1024} Ko, {len(slim_items)} items, {len(slim_sets)} panos')


if __name__ == '__main__':
    main()
