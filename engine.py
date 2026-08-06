# -*- coding: utf-8 -*-
"""Optimiseur v2 — évaluation incrémentale O(1), recuit + polissage steepest-ascent.

Gains vs v1 : ~15x plus d'itérations/s, pools 2x plus larges, optimum local
1-swap certifié, arrêt anticipé quand les restarts convergent.
"""
import json
import random
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data'

WEAPON_TYPES = {'Épée', 'Marteau', 'Bâton', 'Dague', 'Baguette', 'Arc', 'Hache', 'Pelle', 'Faux', 'Lance'}
RES_NAMES = ['% Résistance Neutre', '% Résistance Terre', '% Résistance Feu', '% Résistance Eau', '% Résistance Air']
ORDER = ['coiffe', 'cape', 'amulette', 'ceinture', 'bottes', 'anneau1', 'anneau2', 'arme',
         'bouclier', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'familier']


def parse_conditions(c, out):
    if not isinstance(c, dict):
        return
    if c.get('is_operand') and 'condition' in c:
        cc = c['condition']
        out.append((cc['element']['name'], cc['operator'], cc.get('int_value')))
    for ch in (c.get('children') or []):
        parse_conditions(ch, out)


def load_data(dofus_allowed=False):
    data = json.load(open(DATA / 'equipment_all.json', encoding='utf-8'))['items']
    try:
        conds = {i['ankama_id']: i['conditions']
                 for i in json.load(open(DATA / 'eq_cond.json', encoding='utf-8'))['items']
                 if i.get('conditions')}
    except FileNotFoundError:
        conds = {}
    for it in data:
        raw = conds.get(it['ankama_id'])
        parsed = []
        if raw:
            parse_conditions(raw, parsed)
        it['_conds'] = [c for c in parsed if 'niveau' not in c[0] and 'abonné' not in c[0]]
    sets = {s['ankama_id']: s for s in json.load(open(DATA / 'sets_all.json', encoding='utf-8'))['sets']}
    dofus_types = {'Trophée'} | ({'Dofus', 'Prysmaradite'} if dofus_allowed else set())
    slot_types = {
        'coiffe': {'Chapeau'}, 'cape': {'Cape'}, 'amulette': {'Amulette'},
        'anneau1': {'Anneau'}, 'anneau2': {'Anneau'}, 'bottes': {'Bottes'},
        'ceinture': {'Ceinture'}, 'bouclier': {'Bouclier'}, 'arme': WEAPON_TYPES,
        **{f'd{i}': dofus_types for i in range(1, 7)},
        'familier': {'Familier', 'Montilier'},
    }
    items = []
    for it in data:
        ok = it['level'] >= 160 or it['type']['name'] in dofus_types | {'Familier', 'Montilier'}
        if ok and '(MJ)' not in it['name'] and 'Percepteur' not in it['type']['name']:
            items.append(it)
    return items, sets, slot_types


def effect_lines(effects, roll='max'):
    for e in effects or []:
        if e['type'].get('is_active'):
            continue
        lo, hi = e.get('int_minimum') or 0, e.get('int_maximum') or 0
        if not hi:
            v = lo
        elif roll == 'avg':
            v = (lo + hi) / 2
        elif roll == 'p80':
            v = lo + 0.8 * (hi - lo)
        else:
            v = hi
        yield e['type']['name'], v


class Engine:
    """Indexe les stats utiles, projette items et bonus de panos en vecteurs compacts."""

    def __init__(self, W, items, sets, slot_types, pa_target=5, pm_target=3,
                 res_exo_budget=0.0, res_cap=50.0, roll='max', locks=None, bans=None):
        # res_exo_budget: total de % res ajoutable à la rune (ex: 8 pièces x 3.5%),
        # alloué optimalement par water-filling dans fitness(). Trophées/Dofus non magables.
        # roll: 'max' | 'avg' | 'p80' — jet des stats d'items.
        # locks: {slot: nom d'item} — force un item possédé dans un slot.
        self.res_budget, self.res_cap = res_exo_budget, res_cap
        self.roll = roll
        self.bans = set(bans or ())
        self.stat_ix = {}
        for name in list(W) + ['PA', 'PM', 'Portée'] + RES_NAMES:
            self.stat_ix.setdefault(name, len(self.stat_ix))
        self.n = len(self.stat_ix)
        self.pa_t, self.pm_t = pa_target, pm_target
        special = {'PA', 'PM', 'Portée'}
        self.wlin = [0.0] * self.n
        for name, w in W.items():
            if name not in special:
                self.wlin[self.stat_ix[name]] = w
        self.w_pa, self.w_pm, self.w_po = W['PA'], W['PM'], W['Portée']
        self.i_pa, self.i_pm, self.i_po = (self.stat_ix[k] for k in ('PA', 'PM', 'Portée'))
        self.i_res = [self.stat_ix[r] for r in RES_NAMES]
        self.items, self.sets = items, sets
        for it in items:
            it['_vec'] = self._vec(it.get('effects'))
        self.set_vecs = {}
        for sid, s in sets.items():
            eff = s.get('effects') or {}
            self.set_vecs[sid] = {int(k): self._vec(v) for k, v in eff.items()}
        self.pools = self._pools(W, slot_types)
        for slot, name in (locks or {}).items():
            match = [it for it in items if it['name'] == name
                     and it['type']['name'] in slot_types[slot]]
            if not match:
                raise KeyError(f"lock impossible: '{name}' introuvable pour le slot {slot}")
            self.pools[slot] = match[:1]

    def _vec(self, effects):
        acc = defaultdict(float)
        for name, v in effect_lines(effects, self.roll):
            if name in self.stat_ix:
                acc[self.stat_ix[name]] += v
        return list(acc.items())

    def _pools(self, W, slot_types):
        pools = {}
        for slot, types in slot_types.items():
            cand = [it for it in self.items
                    if it['type']['name'] in types and it['name'] not in self.bans]
            score = lambda it: sum(self.wlin[i] * v for i, v in it['_vec'])
            cand.sort(key=score, reverse=True)
            top = cand[:90]
            for key in ('PA', 'PM'):
                ix = self.stat_ix[key]
                gain = lambda it: sum(v for i, v in it['_vec'] if i == ix)
                top += [it for it in sorted(cand, key=gain, reverse=True)[:12] if it not in top]
            pools[slot] = top
        return pools


class State:
    """Build mutable avec score maintenu incrémentalement."""

    def __init__(self, eng):
        self.e = eng
        self.tot = [0.0] * eng.n
        self.lin = 0.0
        self.counts = defaultdict(int)
        self.build = {}
        self.used = set()

    def _add_vec(self, vec, sign):
        for i, v in vec:
            self.tot[i] += sign * v
            self.lin += self.e.wlin[i] * sign * v

    def _set_delta(self, sid, before, after):
        vecs = self.e.set_vecs.get(sid) or {}
        if before in vecs:
            self._add_vec(vecs[before], -1)
        if after in vecs:
            self._add_vec(vecs[after], +1)

    def put(self, slot, item):
        old = self.build.get(slot)
        if old is not None:
            self._add_vec(old['_vec'], -1)
            self.used.discard(old['ankama_id'])
            ps = old.get('parent_set')
            if ps:
                c = self.counts[ps['id']]
                self._set_delta(ps['id'], c, c - 1)
                self.counts[ps['id']] = c - 1
        self.build[slot] = item
        self._add_vec(item['_vec'], +1)
        self.used.add(item['ankama_id'])
        ps = item.get('parent_set')
        if ps:
            c = self.counts[ps['id']]
            self._set_delta(ps['id'], c, c + 1)
            self.counts[ps['id']] = c + 1
        return old

    def fitness(self):
        e, t = self.e, self.tot
        pa, pm, po = t[e.i_pa], t[e.i_pm], t[e.i_po]
        sc = self.lin
        sc += e.w_pa * min(pa, e.pa_t) + e.w_pm * min(pm, e.pm_t) + e.w_po * min(po, 3)
        sc -= 150 * (max(0, pa - e.pa_t) + max(0, pm - e.pm_t))
        sc -= 8000 * (max(0, e.pa_t - pa) + max(0, e.pm_t - pm))
        res = [t[i] for i in e.i_res]
        if e.res_budget:
            gained, res = self._waterfill(res)
            w_res = e.wlin[e.i_res[0]]
            sc += w_res * gained
        sc += 22 * min(res)
        sc -= 8000 * self._violations(pa, pm)
        return sc

    def _violations(self, pa, pm):
        """Conditions d'équipement: PA/PM totaux (base 200 = 7/3), bonus de panos, seuils de stats."""
        e = self.e
        n_bonus = sum(1 for c in self.counts.values() if c >= 2)
        char = {'PA': 7 + pa, 'PM': 3 + pm, 'Bonus de panoplies': n_bonus}
        bad = 0
        for it in self.build.values():
            for name, op, val in it['_conds']:
                cur = char.get(name)
                if cur is None:  # stat de carac: stuff + parcho 100 (+450 si investie)
                    ix = e.stat_ix.get(name)
                    cur = (self.tot[ix] if ix is not None else 0) + 100
                    if e.wlin[ix] >= 0.5 if ix is not None else False:
                        cur += 450
                if op == '<' and not cur < val:
                    bad += 1
                elif op == '>' and not cur > val:
                    bad += 1
        return bad

    def _waterfill(self, res):
        """Alloue le budget de runes res: remonte la res min, cap res_cap. O(5 log 5)."""
        e, budget = self.e, self.e.res_budget
        vals = sorted(res)
        level = vals[0]
        for nxt in vals[1:] + [e.res_cap]:
            below = sum(1 for v in vals if v <= level)
            need = below * (min(nxt, e.res_cap) - level)
            if need >= budget:
                level += budget / below
                budget = 0
                break
            budget -= need
            level = min(nxt, e.res_cap)
        new = [max(v, min(level, e.res_cap)) for v in res]
        return sum(new) - sum(res), new


def optimize(eng, starts=8, iters=120000, seed=0, converge_stop=3):
    rng = random.Random(seed)
    slots = list(eng.pools)
    best_build, best_f, hits = None, float('-inf'), 0
    for s in range(starts):
        st = State(eng)
        for slot in slots:
            it = rng.choice(eng.pools[slot])
            while it['ankama_id'] in st.used:
                it = rng.choice(eng.pools[slot])
            st.put(slot, it)
        cur_f = st.fitness()
        for i in range(iters):
            slot = slots[rng.randrange(len(slots))]
            cand = eng.pools[slot][rng.randrange(len(eng.pools[slot]))]
            if cand['ankama_id'] in st.used and cand is not st.build[slot]:
                continue
            old = st.put(slot, cand)
            f = st.fitness()
            temp = max(1.0, 4000 * (1 - i / iters))
            if f >= cur_f or rng.random() < 2.718 ** ((f - cur_f) / temp):
                cur_f = f
            else:
                st.put(slot, old)
        cur_f = polish(eng, st)
        if abs(cur_f - best_f) < 1e-6:
            hits += 1
        elif cur_f > best_f:
            best_build, best_f, hits = dict(st.build), cur_f, 1
        if hits >= converge_stop:
            break
    return best_build, best_f, hits


def polish(eng, st):
    """Steepest-ascent exhaustif: certifie un optimum local 1-swap sur les pools."""
    cur_f = st.fitness()
    improved = True
    while improved:
        improved = False
        for slot in eng.pools:
            best_item, best_f = st.build[slot], cur_f
            for cand in eng.pools[slot]:
                if cand['ankama_id'] in st.used and cand is not st.build[slot]:
                    continue
                old = st.put(slot, cand)
                f = st.fitness()
                if f > best_f + 1e-9:
                    best_item, best_f = cand, f
                st.put(slot, old)
            if best_item is not st.build[slot]:
                st.put(slot, best_item)
                cur_f = best_f
                improved = True
    return cur_f


def report(eng, build):
    st = State(eng)
    for slot, it in build.items():
        st.put(slot, it)
    inv = {v: k for k, v in eng.stat_ix.items()}
    stats = {inv[i]: round(v) for i, v in enumerate(st.tot) if abs(v) > 0.5}
    return stats, st.fitness()
