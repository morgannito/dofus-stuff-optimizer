# Dofus Stuff Optimizer

Optimiseur de stuff pour **Dofus 3 (Unity)** — trouve les meilleurs équipements niveau 200
sous contraintes réelles du jeu, avec un objectif physique (dégâts de rotation × survie
effective) plutôt que des pondérations arbitraires.

Exemple câblé : **Sacrieur terre 200 PvP**, 12 PA / 6 PM naturels, sans Dofus, runes de
résistance. Démo visuelle : `docs/index.html` (5 builds le long du front dégâts/survie,
icônes, stats, rotation).

## Méthode

- **Données** : [API DofusDude](https://docs.dofusdu.de) (~4300 équipements, panoplies,
  conditions d'équipement), rolls max.
- **Recherche** : recuit simulé multi-départs + polissage steepest-ascent exhaustif
  (optimum local 1-swap certifié). Évaluation **incrémentale O(1)** par mouvement :
  stats projetées en vecteurs indexés, bonus de panoplies appliqués par delta.
- **Objectif** (`rotation.py`) : `score = ln(DPT) · w_off + ln(EHP) · w_def`
  - DPT : formule officielle de dégâts, sort par sort, crits espérés
    (taux de base du sort + % crit du stuff, lignes critiques avec dommages critiques)
  - EHP : PV totaux / (1 − res effective), res après allocation optimale des runes
    (*water-filling* : la résistance la plus basse d'abord, cap 50 %)
- **Contraintes modélisées** : cibles PA/PM (12/6 naturel ou avec exo), unicité des items,
  et **conditions d'équipement** — `PA < 12`, `PM < 6`, `Bonus de panoplies < 3`
  (trophées majeurs), seuils de caractéristiques. Sans elles, l'optimiseur adore les
  items sur-statés réservés aux builds hors 12/6.

## Usage

```bash
python fetch_data.py   # télécharge les dumps DofusDude dans data/
python sweep.py        # optimise les 5 profils (Offensif -> Tank) + icônes
python gen_page.py     # génère la page visuelle docs/index.html
```

Python 3.10+, aucune dépendance externe.

Pour un autre élément/classe : adapter `W` (présélection des pools), `ROTATION`
(bases des sorts, coûts PA, % crit) et l'élément dans `sweep.py`.

## Structure

| Fichier | Rôle |
|---|---|
| `engine.py` | Moteur : chargement données, vecteurs de stats, état incrémental, recuit + polish, water-filling des runes, conditions |
| `rotation.py` | Objectif physique DPT × EHP |
| `sweep.py` | Front dégâts/survie (5 profils) |
| `gen_page.py` | Page visuelle autonome (icônes embarquées en base64) |
| `fetch_data.py` | Téléchargement des données DofusDude |

## Limites connues

- Rolls supposés parfaits ; exos modélisés en agrégat (budget de runes, cible PA/PM).
- Le recuit trouve d'excellents optima locaux, pas une preuve d'optimalité globale.
- Les bases de sorts sont saisies à la main (scrapées de DofusBook) — à mettre à jour
  aux équilibrages.

Projet non affilié à Ankama. Données © Ankama via DofusDude.
