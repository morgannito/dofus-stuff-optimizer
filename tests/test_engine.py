# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import engine as E
import rotation as R


def eff(name, lo, hi=0):
    return {'type': {'name': name, 'is_active': False},
            'int_minimum': lo, 'int_maximum': hi}


def item(aid, name, typ, effects, conds=None, parent_set=None):
    return {'ankama_id': aid, 'name': name, 'level': 200,
            'type': {'name': typ}, 'effects': effects,
            '_conds': conds or [], 'parent_set': parent_set,
            'image_urls': {'icon': ''}}


W = {'PA': 350, 'PM': 260, 'Portée': 35, 'Force': 1.0, 'Vitalité': 0.7,
     '% Résistance Neutre': 8, '% Résistance Terre': 8, '% Résistance Feu': 8,
     '% Résistance Eau': 8, '% Résistance Air': 8, '% Critique': 3,
     'Puissance': 0.9, 'Dommage': 9, 'Dommage Terre': 9, 'Dommage Critiques': 1.5,
     '% Dommages aux sorts': 11, '% Dommages mêlée': 9, 'Tacle': 1.3, 'Soin': 1.0,
     'Intelligence': 0, 'Chance': 0, 'Agilité': 0}
SLOTS = {'coiffe': {'Chapeau'}, 'anneau1': {'Anneau'}, 'anneau2': {'Anneau'}}


def make_engine(items, sets=None, **kw):
    return E.Engine(W, items, sets or {}, SLOTS, **kw)


# --- effect_lines / rolls ---

def test_effect_lines_rolls():
    effs = [eff('Force', 40, 60)]
    assert dict(E.effect_lines(effs, 'max'))['Force'] == 60
    assert dict(E.effect_lines(effs, 'avg'))['Force'] == 50
    assert dict(E.effect_lines(effs, 'p80'))['Force'] == 56


def test_effect_lines_sans_max():
    # ex: "12% Résistance Feu" (int_maximum absent) — toujours la valeur min
    effs = [eff('% Résistance Feu', 12)]
    for roll in ('max', 'avg', 'p80'):
        assert dict(E.effect_lines(effs, roll))['% Résistance Feu'] == 12


def test_effect_lines_ignore_actives():
    effs = [{'type': {'name': 'Dommage', 'is_active': True}, 'int_minimum': 99, 'int_maximum': 99}]
    assert list(E.effect_lines(effs)) == []


# --- water-filling des runes res ---

def waterfill(res, budget, cap=50.0):
    items = [item(1, 'x', 'Chapeau', [])]
    eng = make_engine(items, res_exo_budget=budget, res_cap=cap)
    st = E.State(eng)
    return st._waterfill(list(res))


def test_waterfill_remonte_la_res_min():
    gained, after = waterfill([10, 40, 40, 40, 40], 20)
    assert gained == 20
    assert after[0] == 30          # tout le budget sur la plus basse
    assert after[1:] == [40, 40, 40, 40]


def test_waterfill_respecte_le_cap():
    gained, after = waterfill([49, 49, 49, 49, 49], 30)
    assert max(after) <= 50
    assert gained <= 5


def test_waterfill_egalise():
    _, after = waterfill([10, 20, 40, 40, 40], 30)
    assert abs(after[0] - after[1]) < 1e-6   # les deux plus basses finissent au même niveau


# --- état incrémental ---

def test_etat_incremental_coherent():
    sets = {77: {'ankama_id': 77, 'effects': {'2': [eff('Force', 30, 30)]}}}
    a = item(1, 'A', 'Chapeau', [eff('Force', 10, 20), eff('PA', 1, 1)])
    b = item(2, 'B', 'Anneau', [eff('Force', 5, 5)], parent_set={'id': 77})
    c = item(3, 'C', 'Anneau', [eff('Vitalité', 100, 100)], parent_set={'id': 77})
    d = item(4, 'D', 'Anneau', [eff('Force', 50, 50)])
    eng = make_engine([a, b, c, d], sets)
    st = E.State(eng)
    st.put('coiffe', a); st.put('anneau1', b); st.put('anneau2', c)
    ix = eng.stat_ix['Force']
    assert st.tot[ix] == 20 + 5 + 30        # bonus pano 2 pièces actif
    st.put('anneau2', d)                     # casse la pano
    assert st.tot[ix] == 20 + 5 + 50
    # re-construire de zéro donne le même total
    st2 = E.State(eng)
    st2.put('coiffe', a); st2.put('anneau1', b); st2.put('anneau2', d)
    assert st.tot == st2.tot


# --- conditions d'équipement ---

def test_condition_pa_totaux():
    # base 200 = 7 PA; +5 PA de stuff => 12 => "PA < 12" violée
    a = item(1, 'A', 'Chapeau', [eff('PA', 5, 5)], conds=[('PA', '<', 12)])
    eng = make_engine([a])
    st = E.State(eng)
    st.put('coiffe', a)
    assert st._violations(5, 0) == 1
    assert st._violations(4, 0) == 0


def test_condition_bonus_panoplies():
    sets = {9: {'ankama_id': 9, 'effects': {'2': [eff('Force', 1, 1)]}}}
    t = item(1, 'Trophée majeur', 'Chapeau', [], conds=[('Bonus de panoplies', '<', 1)])
    r1 = item(2, 'R1', 'Anneau', [], parent_set={'id': 9})
    r2 = item(3, 'R2', 'Anneau', [], parent_set={'id': 9})
    eng = make_engine([t, r1, r2], sets)
    st = E.State(eng)
    st.put('coiffe', t)
    assert st._violations(0, 0) == 0
    st.put('anneau1', r1); st.put('anneau2', r2)   # 1 bonus de pano actif
    assert st._violations(0, 0) == 1


# --- rotation DP ---

def test_spellbook_dp(tmp_path):
    spells = {'test': [
        {'name': 'Gros', 'pa': 4, 'cc_rate': 0, 'lt': 1,
         'effects': [{'el': 't', 'steal': 0, 'cc': 0, 'min': 40, 'max': 40, 'zone': 0}]},
        {'name': 'Petit', 'pa': 2, 'cc_rate': 0, 'lt': 4,
         'effects': [{'el': 't', 'steal': 0, 'cc': 0, 'min': 15, 'max': 15, 'zone': 0}]},
    ]}
    p = tmp_path / 'spells.json'
    p.write_text(json.dumps(spells), encoding='utf-8')
    book = R.SpellBook('test', 't', spells_path=p)
    # mult=1, flats=0: 12 PA -> Gros(40) + 4x Petit(15)=60 -> 100
    dmg, rot = book.best_rotation(12, 1.0, 0, 0, 0)
    assert dmg == 100
    assert dict(rot) == {'Gros': 1, 'Petit': 4}
    # avec +30 plats/ligne, les petits sorts dominent: 4xPetit(45)+Gros(70)=250
    dmg2, _ = book.best_rotation(12, 1.0, 30, 0, 0)
    assert dmg2 == 250


def test_spellbook_paliers_de_charge(tmp_path):
    # >2 lignes du même élément = paliers de charge -> seule la ligne de base compte
    spells = {'test': [{'name': 'Chargé', 'pa': 4, 'cc_rate': 0, 'lt': 1, 'effects': [
        {'el': 't', 'steal': 0, 'cc': 0, 'min': 10, 'max': 10, 'zone': 0},
        {'el': 't', 'steal': 0, 'cc': 0, 'min': 50, 'max': 50, 'zone': 0},
        {'el': 't', 'steal': 0, 'cc': 0, 'min': 90, 'max': 90, 'zone': 0}]}]}
    p = tmp_path / 's.json'
    p.write_text(json.dumps(spells), encoding='utf-8')
    book = R.SpellBook('test', 't', spells_path=p)
    assert book.entries[0][2] == 10   # base normale = ligne 1 seule


def test_lock_force_un_item():
    a = item(1, 'A', 'Chapeau', [eff('Force', 99, 99)])
    b = item(2, 'B', 'Chapeau', [eff('Force', 1, 1)])
    eng = make_engine([a, b], locks={'coiffe': 'B'})
    assert [it['name'] for it in eng.pools['coiffe']] == ['B']


def test_ban_exclut_du_pool():
    a = item(1, 'A', 'Chapeau', [eff('Force', 99, 99)])
    b = item(2, 'B', 'Chapeau', [eff('Force', 1, 1)])
    eng = make_engine([a, b], bans=['A'])
    assert [it['name'] for it in eng.pools['coiffe']] == ['B']


def test_roll_avg_dans_les_vecteurs():
    a = item(1, 'A', 'Chapeau', [eff('Force', 40, 60)])
    eng = make_engine([a], roll='avg')
    ix = eng.stat_ix['Force']
    assert dict(a['_vec'])[ix] == 50
