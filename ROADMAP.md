# Roadmap — 100 améliorations explorées

Légende : ✅ fait · 🔨 dans cette itération · ⏳ planifié · 💭 idée (valeur/effort discutable)

## Moteur de recherche (1-15)

1. ✅ Évaluation incrémentale O(1) par mouvement
2. ✅ Polissage steepest-ascent (optimum local 1-swap certifié)
3. ✅ Arrêt anticipé sur convergence des restarts
4. ✅ Restarts parallèles par processus (CLI `--jobs`)
5. 🔨 Graine reproductible (`--seed`)
6. ⏳ Move 2-swap (échange simultané des 2 anneaux / paires de pano)
7. ⏳ Recuit adaptatif (température calée sur le taux d'acceptation)
8. ⏳ Tabu-list courte pour éviter les cycles en fin de recuit
9. ⏳ Preuve d'optimalité ILP (linéarisation des bonus de pano) en mode `--exact`
10. ⏳ Front de Pareto complet en un run (archive des non-dominés)
11. 💭 Portage numpy/numba du DP de rotation
12. 💭 Portage Rust (pyo3) du moteur chaud
13. ⏳ Cache LRU des fitness par hash de build (restarts qui se recroisent)
14. 💭 Recherche par faisceau (beam) comparée au recuit sur benchmark
15. ✅ Pools élargis + porteurs PA/PM garantis

## Modélisation du jeu (16-35)

16. ✅ Formule officielle de dégâts (carac + puissance + %do additifs, plats après)
17. ✅ Crits espérés (taux du sort + % crit stuff, lignes CC, do crit)
18. ✅ Rotation optimale par knapsack DP (limites lancers/tour)
19. ✅ Conditions d'équipement (PA<12, PM<6, bonus panos, seuils de stats)
20. ✅ Water-filling des runes res (cap 50 %)
21. ✅ Rolls max / moyens / p80
22. 🔨 Budget PA de rotation configurable (`--pa-budget`, ex: tour à 11 PA)
23. 🔨 Points investis / vita de base configurables (`--invest`, `--base-vita`)
24. ⏳ Sorts à paliers de charge : modéliser la montée en charge sur 2-3 tours
25. ⏳ Coups de pied / attaque d'arme dans le DP (armes = vraie ligne de dégâts)
26. ⏳ Vol de vie dans l'EHP (sustain/tour ajouté aux PV effectifs)
27. ⏳ Érosion (les do crit érodent — pondérer contre les boucliers)
28. ⏳ % Dommages distance vs mêlée selon la PO réelle des sorts retenus
29. ⏳ Builds multi-éléments (Strigide) : DP sur l'union des livres de sorts
30. 💭 Modéliser les états/buffs de classe (Folie Sanguinaire, etc.)
31. ⏳ PO des sorts : pénaliser les rotations impossibles à distance
32. ⏳ Exos par item (PA OU PM OU PO par pièce, puits de forgemagie réel)
33. 💭 Sorts communs des variantes (choix exclusifs de variantes)
34. ⏳ Res fixes adverses paramétrables (elles grignotent les petites lignes)
35. 💭 Simulateur de duel 1v1 simplifié comme fitness alternative

## Données (36-50)

36. ✅ DofusDude complet (items, panos, conditions via `fields`)
37. ✅ Sorts des 20 classes (API DofusBook)
38. ✅ spells.json versionné dans le repo
39. 🔨 Exclusion d'items (`--ban`, répétable)
40. ✅ Locks d'items possédés (`--lock slot=Item`)
41. ⏳ Prix HDV (aucune API publique fiable — à surveiller: Vulbis.com, marchés tiers)
42. ⏳ Optimisation à budget kamas contraint (dès qu'une source de prix existe)
43. ⏳ Import de perso (export Dofus / DofusBook -> locks automatiques)
44. ⏳ Détection de patch : diff des dumps DofusDude et changelog auto
45. 💭 Multi-langue (les stats FR sont des clés — table de mapping EN)
46. ⏳ Valider les sorts non-Sacrieur (au moins Iop, Crâ, Ouginak)
47. ✅ Refresh hebdo automatique (GitHub Actions)
48. ⏳ Étendre aux niveaux < 200 (`--niveau`, base PA/PM ajustée)
49. 💭 Mode Dofus Touch (données différentes)
50. 💭 Mode Rétro 1.29

## CLI & API (51-60)

51. ✅ CLI complet (classe, élément, mode, profil, rolls, locks, dofus, jobs)
52. 🔨 Sortie JSON (`--json fichier`) pour scripter par-dessus
53. 🔨 `--ban` répétable
54. 🔨 `--seed` reproductible
55. ⏳ `--compare build.json` : diff de deux builds (stats + DPT/EHP)
56. ⏳ Export DofusBook (URL de stuff pré-rempli)
57. ⏳ Barre de progression CLI (tqdm-like sans dépendance)
58. 💭 Serveur FastAPI pour exposer l'optimiseur en API
59. ⏳ `--profil` étendu (lock/anti-retrait/érosion préconfigurés)
60. ✅ Entry-point packagé (`pip install -e .`)

## Web (61-80)

61. ✅ Page statique 5 profils (icônes, stats, res, rotation)
62. ✅ Forge interactive 100 % navigateur
63. 🔨 Sélecteur de classe (les 20 classes des données)
64. 🔨 Profondeur de recherche (rapide / normale / longue)
65. 🔨 Bannir un item d'un clic (chips + re-forge)
66. 🔨 Partage par URL (config encodée dans le hash)
67. 🔨 Lien croisé index ↔ forge
68. ⏳ Lock d'un item depuis la grille (clic long / icône cadenas)
69. ⏳ Comparateur côte à côte de deux forges
70. ⏳ Tooltips de stats par item dans la forge (comme la page statique)
71. ⏳ Historique des forges (localStorage) + favoris
72. ⏳ Web Worker pour le recuit (UI jamais bloquée, multi-thread)
73. 💭 WASM du moteur Python (pyodide) au lieu du port JS
74. ⏳ Icônes des sorts dans la rotation
75. ⏳ Mode sombre/clair forcé (toggle, pas seulement prefers-color-scheme)
76. 💭 i18n EN de l'interface
77. ⏳ PWA (manifest + service worker, forge offline)
78. ⏳ Graphe du front interactif dans la forge (tous les essais tracés)
79. 💭 Animation de forge (marteau qui tape pendant le recuit)
80. ⏳ SEO/OpenGraph (partage Discord avec preview)

## Qualité & infra (81-100)

81. ✅ Tests unitaires (parsing, waterfill, état, conditions, DP)
82. 🔨 Tests locks/bans/rolls/paliers de charge
83. ✅ CI tests sur push
84. ✅ CI refresh hebdo + redéploiement Pages
85. 🔨 Lint ruff en CI
86. ⏳ Test de non-régression sur build de référence (golden file)
87. ⏳ Benchmark suivi en CI (perf du moteur, alerte si régression)
88. ⏳ Couverture de tests publiée (codecov)
89. 🔨 Tag de release + notes (v1.1.0)
90. 🔨 Topics GitHub + homepage du repo
91. ⏳ CHANGELOG.md tenu par release
92. ⏳ Issues templates (bug/data erronée/idée)
93. ⏳ Dependabot pour les actions GitHub
94. 💭 Docker image (inutile: zéro dépendance)
95. ⏳ Docstrings + doc générée (pdoc) sur Pages /api
96. ⏳ Type hints complets + mypy en CI
97. 💭 Publier sur PyPI
98. ⏳ Protéger main (CI verte obligatoire)
99. ⏳ Page "méthodologie" détaillée (les maths de l'optimiseur)
100. ⏳ Communauté : post Reddit r/Dofus + retours joueurs sur les builds

---
**Bilan : 27 ✅ · 16 🔨 (cette itération) · 43 ⏳ · 14 💭**
