# -*- coding: utf-8 -*-
"""CLI de l'optimiseur de stuff Dofus 3.

Exemples:
  python optimize.py --classe sacrieur --element terre
  python optimize.py --classe sacrieur --element feu --mode exo-pa --profil tank
  python optimize.py --element terre --rolls p80 --lock "arme=Masse Étacée" --dofus
"""
import argparse
import json
from concurrent.futures import ProcessPoolExecutor

ELEMENTS = {'terre': 't', 'feu': 'f', 'eau': 'e', 'air': 'a'}
CARAC = {'terre': 'Force', 'feu': 'Intelligence', 'eau': 'Chance', 'air': 'Agilité'}
MODES = {'12/6': (5, 3), 'exo-pa': (4, 3), 'exo-pa-pm': (4, 2)}
PROFILS = {'offensif': 0.7, 'equilibre': 1.0, 'tank': 1.4}


def base_weights(element):
    W = {'PA': 350, 'PM': 260, 'Portée': 35, 'Puissance': 0.9,
         'Force': 0, 'Intelligence': 0, 'Chance': 0, 'Agilité': 0,
         'Dommage': 9, 'Dommage Neutre': 0.4, 'Dommage Critiques': 1.5,
         'Dommage Terre': 0, 'Dommage Feu': 0, 'Dommage Eau': 0, 'Dommage Air': 0,
         '% Critique': 3, 'Vitalité': 0.7, 'Sagesse': 0.05, 'Soin': 1.0,
         '% Résistance Neutre': 8, '% Résistance Terre': 8, '% Résistance Feu': 8,
         '% Résistance Eau': 8, '% Résistance Air': 8, '% Résistance mêlée': 4,
         '% Résistance distance': 3, 'Résistance Critiques': 0.6, 'Résistance Poussée': 0.4,
         'Tacle': 1.3, 'Fuite': 0.8, 'Esquive PA': 0.7, 'Esquive PM': 0.7,
         'Retrait PA': 0.6, 'Retrait PM': 0.6,
         '% Dommages aux sorts': 11, '% Dommages mêlée': 9, "% Dommages d'armes": 1,
         'Initiative': 0.02}
    W[CARAC[element]] = 1.0
    W[f'Dommage {element.capitalize()}'] = 9
    return W


def parse_locks(pairs):
    locks = {}
    for p in pairs or []:
        slot, _, name = p.partition('=')
        if not name:
            raise SystemExit(f"--lock attend slot=Nom d'item, reçu: {p}")
        locks[slot.strip()] = name.strip()
    return locks


def make_engine(args):
    import engine as M2
    items, sets, slots = M2.load_data(dofus_allowed=args.dofus)
    pa_t, pm_t = MODES[args.mode]
    return M2, M2.Engine(base_weights(args.element), items, sets, slots,
                         pa_target=pa_t, pm_target=pm_t, res_exo_budget=args.runes,
                         roll=args.rolls, locks=parse_locks(args.lock))


def worker(payload):
    args, seed = payload
    import rotation as M3
    M2, eng = make_engine(args)
    book = M3.SpellBook(args.classe, ELEMENTS[args.element], roll=args.rolls if args.rolls != 'max' else 'avg')
    fit = M3.RotationFitness(eng, book, ELEMENTS[args.element],
                             w_off=1.0, w_def=args.wdef)
    b, f, _ = M3.optimize_rotation(eng, fit, starts=max(1, args.starts // args.jobs),
                                   iters=args.iters, seed=seed)
    return f, {slot: it['ankama_id'] for slot, it in b.items()}


def main():
    ap = argparse.ArgumentParser(description='Optimiseur de stuff Dofus 3 (DPT réel x EHP)')
    ap.add_argument('--classe', default='sacrieur')
    ap.add_argument('--element', choices=ELEMENTS, default='terre')
    ap.add_argument('--mode', choices=MODES, default='12/6',
                    help='12/6 naturel, ou avec exo PA / exo PA+PM')
    ap.add_argument('--runes', type=float, default=28, help='budget total de %% res en runes')
    ap.add_argument('--profil', choices=PROFILS, default=None)
    ap.add_argument('--wdef', type=float, default=1.0, help='poids défense (ignoré si --profil)')
    ap.add_argument('--rolls', choices=['max', 'avg', 'p80'], default='max')
    ap.add_argument('--lock', action='append', metavar='SLOT=ITEM',
                    help='forcer un item (ex: "arme=Masse Étacée"), répétable')
    ap.add_argument('--dofus', action='store_true', help='autoriser Dofus et Prysmaradites')
    ap.add_argument('--starts', type=int, default=12)
    ap.add_argument('--iters', type=int, default=100000)
    ap.add_argument('--jobs', type=int, default=4, help='processus parallèles')
    args = ap.parse_args()
    if args.profil:
        args.wdef = PROFILS[args.profil]

    with ProcessPoolExecutor(args.jobs) as ex:
        results = list(ex.map(worker, [(args, 1000 + 17 * k) for k in range(args.jobs)]))
    best_f, best_ids = max(results, key=lambda r: r[0])

    import engine as M2
    import rotation as M3
    M2b, eng = make_engine(args)
    by_id = {it['ankama_id']: it for it in eng.items}
    st = M2.State(eng)
    build = {}
    for slot, aid in best_ids.items():
        build[slot] = by_id[aid]
        st.put(slot, by_id[aid])
    book = M3.SpellBook(args.classe, ELEMENTS[args.element], roll='avg')
    fit = M3.RotationFitness(eng, book, ELEMENTS[args.element], w_off=1.0, w_def=args.wdef)
    stats, _ = M2.report(eng, build)
    res = [float(stats.get(r, 0)) for r in M2.RES_NAMES]
    ra = res
    if eng.res_budget:
        _, ra = st._waterfill(res)
    dpt, rot = fit.rotation(st.tot)
    viol = st._violations(stats.get('PA', 0), stats.get('PM', 0))

    print(f"\n=== {args.classe} {args.element} — {args.mode}, rolls {args.rolls}, "
          f"w_def {args.wdef} (score {best_f:,.0f}, violations {viol}) ===")
    for slot in M2.ORDER:
        if slot in build:
            print(f"  {slot:10s} {build[slot]['name']}")
    print(f"\n  PA:{stats.get('PA', 0)} PM:{stats.get('PM', 0)} vita:{stats.get('Vitalité', 0)}"
          f" crit:{stats.get('% Critique', 0)}%")
    print(f"  res: {'/'.join(str(round(v)) for v in res)} -> "
          f"{'/'.join(str(round(v)) for v in ra)} après runes")
    print(f"  EHP: {fit.ehp(st.tot, ra):,.0f}   DPT: {dpt:,.0f}")
    print('  rotation: ' + ', '.join(f'{n} x{c}' for n, c in rot))


if __name__ == '__main__':
    main()
