# -*- coding: utf-8 -*-
"""Sweep du front dégâts/survie (5 profils) + téléchargement des icônes.

Produit data/pareto.json et data/icons_b64.json, consommés par gen_page.py.
Exemple câblé: Sacrieur terre 200, PvP, 12/6 naturel, runes res ~28%.
"""
import base64
import concurrent.futures
import json
import urllib.request
from pathlib import Path

import engine as M2
import rotation as M3

DATA = Path(__file__).resolve().parent / 'data'

# Pondérations de présélection des pools (le score final vient de RotationFitness)
W = {'PA': 350, 'PM': 260, 'Portée': 35, 'Force': 1.0, 'Puissance': 0.9, 'Intelligence': 0,
     'Dommage': 9, 'Dommage Terre': 9, 'Dommage Feu': 0, 'Dommage Neutre': 0.4,
     'Dommage Critiques': 1.5, '% Critique': 3, 'Vitalité': 0.7, 'Sagesse': 0.05, 'Soin': 1.0,
     '% Résistance Neutre': 8, '% Résistance Terre': 8, '% Résistance Feu': 8,
     '% Résistance Eau': 8, '% Résistance Air': 8, '% Résistance mêlée': 4,
     '% Résistance distance': 3, 'Résistance Critiques': 0.6, 'Résistance Poussée': 0.4,
     'Tacle': 1.3, 'Fuite': 0.8, 'Esquive PA': 0.7, 'Esquive PM': 0.7,
     'Retrait PA': 0.6, 'Retrait PM': 0.6,
     '% Dommages aux sorts': 11, '% Dommages mêlée': 9, "% Dommages d'armes": 1,
     'Initiative': 0.02}

# (nom, base, base critique, % crit de base, PA) — rotation terre 12 PA
ROTATION = [('Entaille', 49, 58.5, 25, 4), ('Décimation', 30.5, 36.5, 15, 3),
            ('Ravage', 30, 36, 15, 3), ('Afflux', 13.5, 17.5, 15, 2)]
PROFILS = [('Offensif', 0.7), ('Semi-offensif', 0.85), ('Équilibré', 1.0),
           ('Semi-tank', 1.2), ('Tank', 1.5)]


def run_sweep():
    items, sets, slots = M2.load_data()
    eng = M2.Engine(W, items, sets, slots, pa_target=5, pm_target=3, res_exo_budget=28)
    out = []
    for name, wd in PROFILS:
        fit = M3.RotationFitness(eng, ROTATION, 'Force', 'Terre', w_off=1.0, w_def=wd)
        b, _, _ = M3.optimize_rotation(eng, fit, starts=10, iters=120000, seed=42)
        st = M2.State(eng)
        for s, it in b.items():
            st.put(s, it)
        stats, _ = M2.report(eng, b)
        res = [float(stats.get(r, 0)) for r in M2.RES_NAMES]
        _, ra = st._waterfill(res)
        build = [{'slot': slot, 'name': b[slot]['name'], 'level': b[slot]['level'],
                  'type': b[slot]['type']['name'], 'icon': b[slot]['image_urls']['icon'],
                  'stats': dict(M2.effect_lines(b[slot].get('effects'))),
                  'conds': [list(c) for c in b[slot]['_conds']]}
                 for slot in M2.ORDER]
        out.append({'profil': name, 'w_def': wd, 'dpt': round(fit.dpt(st.tot)),
                    'ehp': round(fit.ehp(st.tot, ra)), 'stats': stats,
                    'res_apres': [round(v) for v in ra], 'items': build})
        print(f"[{name}] DPT={out[-1]['dpt']} EHP={out[-1]['ehp']}")
    json.dump(out, open(DATA / 'pareto.json', 'w', encoding='utf-8'), ensure_ascii=False)
    return out


def fetch_icons(builds):
    urls = sorted({i['icon'] for p in builds for i in p['items']})

    def fetch(u):
        with urllib.request.urlopen(u, timeout=30) as r:
            return u, 'data:image/png;base64,' + base64.b64encode(r.read()).decode()

    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        b64 = dict(ex.map(fetch, urls))
    json.dump(b64, open(DATA / 'icons_b64.json', 'w'))
    print(f'{len(b64)} icônes')


if __name__ == '__main__':
    fetch_icons(run_sweep())
