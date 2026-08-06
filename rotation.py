# -*- coding: utf-8 -*-
"""Objectif physique v5 — DPT de la MEILLEURE rotation (knapsack DP) × EHP.

La rotation n'est plus figée : à chaque évaluation, un sac-à-dos 0/1 sur les PA
choisit la meilleure combinaison de sorts (limites de lancers respectées) selon
les stats courantes du stuff. Un stuff crit et un stuff plats ne jouent pas les
mêmes sorts — l'optimiseur le sait.
"""
import json
import math
from pathlib import Path

import engine as M2

BASE_VITA = 1200      # vita de base niv 200 + parcho
CARAC_INVEST = 550    # points de caracs + parchemins sur l'élément principal
ELEM_STAT = {'t': ('Force', 'Dommage Terre'), 'f': ('Intelligence', 'Dommage Feu'),
             'e': ('Chance', 'Dommage Eau'), 'a': ('Agilité', 'Dommage Air')}


class SpellBook:
    """Sorts de dégâts d'une classe/élément, agrégés pour le DP de rotation."""

    def __init__(self, classe, element, roll='avg', spells_path=None):
        path = spells_path or Path(__file__).resolve().parent / 'data' / 'spells.json'
        all_spells = json.load(open(path, encoding='utf-8'))
        if classe not in all_spells:
            raise KeyError(f"classe inconnue: {classe} (dispo: {', '.join(sorted(all_spells))})")
        pick = {'max': lambda e: e['max'] or e['min'],
                'avg': lambda e: (e['min'] + e['max']) / 2 if e['max'] else e['min'],
                'p80': lambda e: e['min'] + 0.8 * (e['max'] - e['min']) if e['max'] else e['min']}[roll]
        self.entries = []  # (pa, base_normale, base_cc, nb_lignes, cc_rate, lancers/tour)
        for s in all_spells[classe]:
            norm = [pick(e) for e in s['effects'] if e['el'] == element and not e['cc']]
            crit = [pick(e) for e in s['effects'] if e['el'] == element and e['cc']]
            if not norm:
                continue
            if len(norm) > 2:   # >2 lignes = paliers de charge, pas du multi-hit: ligne de base seule
                norm, crit = norm[:1], crit[:1]
            self.entries.append((s['name'], s['pa'], sum(norm), sum(crit) or sum(norm),
                                 len(norm), s['cc_rate'], min(s['lt'], 4)))

    def best_rotation(self, pa_budget, mult, flats, crit_bonus, docrit):
        """Knapsack 0/1 (sorts dupliqués par lancer) -> (dégâts, [(sort, casts)])."""
        items = []
        for name, pa, bn, bcc, nl, ccr, lt in self.entries:
            p = max(0.0, min(1.0, (ccr + crit_bonus) / 100))
            val = mult * ((1 - p) * bn + p * bcc) + nl * (flats + p * docrit)
            if val > 0:
                items.extend([(pa, val, name)] * lt)
        dp = [0.0] * (pa_budget + 1)
        take = [dict() for _ in range(pa_budget + 1)]
        for pa, val, name in items:
            for b in range(pa_budget, pa - 1, -1):
                cand = dp[b - pa] + val
                if cand > dp[b] and take[b - pa].get(name, 0) < 99:
                    dp[b] = cand
                    take[b] = dict(take[b - pa])
                    take[b][name] = take[b].get(name, 0) + 1
        best = max(range(pa_budget + 1), key=lambda b: dp[b])
        return dp[best], sorted(take[best].items())

    def dpt_fast(self, pa_budget, mult, flats, crit_bonus, docrit):
        """Version sans reconstruction, pour la boucle chaude."""
        dp = [0.0] * (pa_budget + 1)
        for name, pa, bn, bcc, nl, ccr, lt in self.entries:
            p = (ccr + crit_bonus) / 100
            p = 0.0 if p < 0 else (1.0 if p > 1 else p)
            val = mult * ((1 - p) * bn + p * bcc) + nl * (flats + p * docrit)
            if val <= 0:
                continue
            for _ in range(lt):
                for b in range(pa_budget, pa - 1, -1):
                    cand = dp[b - pa] + val
                    if cand > dp[b]:
                        dp[b] = cand
        return dp[pa_budget]


class RotationFitness:
    def __init__(self, eng, spellbook, element, w_off=1.0, w_def=1.0, pa_budget=12,
                 carac_invest=CARAC_INVEST, base_vita=BASE_VITA):
        self.e, self.book = eng, spellbook
        self.invest, self.base_vita = carac_invest, base_vita
        carac, do_elem = ELEM_STAT[element]
        ix = eng.stat_ix
        g = ix.get
        self.i_car, self.i_doe = ix[carac], g(do_elem)
        self.i_pui, self.i_crit = g('Puissance'), g('% Critique')
        self.i_do, self.i_docrit = g('Dommage'), g('Dommage Critiques')
        self.i_dosorts, self.i_domelee = g('% Dommages aux sorts'), g('% Dommages mêlée')
        self.i_vita, self.i_tacle, self.i_soin = g('Vitalité'), g('Tacle'), g('Soin')
        self.w_off, self.w_def, self.pa_budget = w_off, w_def, pa_budget

    def _mult_flats(self, t):
        mult = 1 + (t[self.i_car] + self.invest + t[self.i_pui]
                    + t[self.i_dosorts] + t[self.i_domelee]) / 100
        flats = t[self.i_do] + (t[self.i_doe] if self.i_doe is not None else 0)
        return mult, flats

    def dpt(self, t):
        mult, flats = self._mult_flats(t)
        return max(1.0, self.book.dpt_fast(self.pa_budget, mult, flats,
                                           t[self.i_crit], t[self.i_docrit]))

    def rotation(self, t):
        mult, flats = self._mult_flats(t)
        return self.book.best_rotation(self.pa_budget, mult, flats,
                                       t[self.i_crit], t[self.i_docrit])

    def ehp(self, t, res):
        hp = self.base_vita + t[self.i_vita]
        eff = 0.75 * (sum(res) / 5) + 0.25 * min(res)
        return max(hp, 1.0) / max(0.05, 1 - eff / 100)

    def __call__(self, st):
        e, t = self.e, st.tot
        pa, pm, po = t[e.i_pa], t[e.i_pm], t[e.i_po]
        res = [t[i] for i in e.i_res]
        if e.res_budget:
            _, res = st._waterfill(res)
        sc = 3000 * (self.w_off * math.log(self.dpt(t)) + self.w_def * math.log(self.ehp(t, res)))
        sc += e.w_pa * min(pa, e.pa_t) + e.w_pm * min(pm, e.pm_t) + e.w_po * min(po, 3)
        sc -= 150 * (max(0, pa - e.pa_t) + max(0, pm - e.pm_t))
        sc -= 20000 * (max(0, e.pa_t - pa) + max(0, e.pm_t - pm))
        sc -= 20000 * st._violations(pa, pm)
        sc += 1.2 * t[self.i_tacle] + 0.8 * t[self.i_soin]
        return sc


def optimize_rotation(eng, fit, starts=12, iters=120000, seed=0, converge_stop=3):
    import random
    rng = random.Random(seed)
    slots = list(eng.pools)
    best_build, best_f, hits = None, float('-inf'), 0
    for _ in range(starts):
        st = M2.State(eng)
        for slot in slots:
            it = rng.choice(eng.pools[slot])
            while it['ankama_id'] in st.used:
                it = rng.choice(eng.pools[slot])
            st.put(slot, it)
        cur_f = fit(st)
        for i in range(iters):
            slot = slots[rng.randrange(len(slots))]
            cand = eng.pools[slot][rng.randrange(len(eng.pools[slot]))]
            if cand['ankama_id'] in st.used and cand is not st.build[slot]:
                continue
            old = st.put(slot, cand)
            f = fit(st)
            temp = max(1.0, 3000 * (1 - i / iters))
            if f >= cur_f or rng.random() < 2.718 ** ((f - cur_f) / temp):
                cur_f = f
            else:
                st.put(slot, old)
        cur_f = polish_rotation(eng, st, fit)
        if abs(cur_f - best_f) < 1e-6:
            hits += 1
        elif cur_f > best_f:
            best_build, best_f, hits = dict(st.build), cur_f, 1
        if hits >= converge_stop:
            break
    return best_build, best_f, hits


def polish_rotation(eng, st, fit):
    """Steepest-ascent exhaustif: optimum local 1-swap sur les pools."""
    cur_f = fit(st)
    improved = True
    while improved:
        improved = False
        for slot in eng.pools:
            best_item, best_f = st.build[slot], cur_f
            for cand in eng.pools[slot]:
                if cand['ankama_id'] in st.used and cand is not st.build[slot]:
                    continue
                old = st.put(slot, cand)
                f = fit(st)
                if f > best_f + 1e-9:
                    best_item, best_f = cand, f
                st.put(slot, old)
            if best_item is not st.build[slot]:
                st.put(slot, best_item)
                cur_f = best_f
                improved = True
    return cur_f
