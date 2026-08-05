# -*- coding: utf-8 -*-
"""Optimiseur v4 — objectif physique: DPT réel de la rotation x EHP, plus de poids arbitraires.

DPT: formule officielle Dofus par ligne, crits espérés (base sort + %crit stuff).
EHP: PV totaux / (1 - res_moyenne_après_runes), pénalisé par la res min.
Score = ln(DPT)*w_off + ln(EHP)*w_def + utilité (tacle, soin, esquives) — le produit
force le compromis: doubler ses dégâts vaut autant que doubler sa survie.
"""
import math
import engine as M2

BASE_VITA = 1200      # vita de base niv 200 + parcho
CARAC_INVEST = 550    # points de caracs + parcho sur l'élément principal


class RotationFitness:
    def __init__(self, eng, rotation, carac_name, element, w_off=1.0, w_def=1.0):
        self.e = eng
        self.rot = rotation  # [(nom, base, base_cc, cc_rate, pa)]
        ix = eng.stat_ix
        self.i_car = ix[carac_name]
        g = lambda n: ix.get(n)
        self.i_pui, self.i_crit = g('Puissance'), g('% Critique')
        self.i_do, self.i_doe = g('Dommage'), g(f'Dommage {element}')
        self.i_docrit = g('Dommage Critiques')
        self.i_dosorts, self.i_domelee = g('% Dommages aux sorts'), g('% Dommages mêlée')
        self.i_vita, self.i_tacle, self.i_soin = g('Vitalité'), g('Tacle'), g('Soin')
        self.w_off, self.w_def = w_off, w_def

    def dpt(self, t):
        mult = 1 + (t[self.i_car] + CARAC_INVEST + t[self.i_pui]
                    + t[self.i_dosorts] + t[self.i_domelee]) / 100
        flats = t[self.i_do] + (t[self.i_doe] or 0)
        crit_bonus = t[self.i_crit]
        total = 0.0
        for _, base, base_cc, cc, _pa in self.rot:
            p = max(0.0, min(1.0, (cc + crit_bonus) / 100))
            normal = base * mult + flats
            critic = base_cc * mult + flats + t[self.i_docrit]
            total += (1 - p) * normal + p * critic
        return max(total, 1.0)

    def ehp(self, t, res):
        hp = BASE_VITA + t[self.i_vita]
        avg = sum(res) / 5
        eff = 0.75 * avg + 0.25 * min(res)   # la res min est celle qu'on exploite
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


def optimize_rotation(eng, fit, starts=12, iters=150000, seed=0, converge_stop=3):
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
