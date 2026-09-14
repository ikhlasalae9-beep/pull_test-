> Historical record: model serving is now documented in [MODEL_V1.md](MODEL_V1.md). Earlier runtime/artifact references below are superseded.

# Audit Machine Learning — MaisonDeLUX

> Historical audit record. The superseded experiment notebooks, standalone model
> files, and Phase 4.1 manifest described below were removed from the active tree
> during the repository cleanup after being copied to the external recovery
> checkpoint. The backend contract and retained production artifacts are current.

## Résumé

MaisonDeLUX estime le prix de vente d'un bien immobilier marocain. Il s'agit d'un problème de **régression** évalué avec R², MAE et RMSE.

L'audit a montré que les anciennes métriques étaient affectées par des fuites de données et qu'elles ne correspondaient plus exactement au modèle sauvegardé. Le modèle final utilise une évaluation groupée sans fuite et une pipeline complète compatible avec l'API.

Sur le même test intact, le modèle final réduit la MAE de **30,09%** et le RMSE de **13,20%** par rapport à un Random Forest reproduisant la stratégie actuelle sans fuite.

## Pipeline de production avant Phase 4

L'ancien backend chargeait séparément :

- `model.pkl` : Random Forest de 200 arbres ;
- `scaler.pkl` : standardisation des variables numériques ;
- `feature_columns.pkl` : ordre des colonnes ;
- `quartier_freq.pkl` : fréquence des quartiers ;
- `mode_par_ville.pkl` : valeur de secours par ville ;
- `metrics.json` : résultats historiques.

Le backend reconstruisait manuellement les mêmes transformations. Cette duplication créait un risque de différence entre entraînement et prédiction.

## Contrat réel de l'API

`POST /api/predict` reçoit :

| Champ | Utilisation |
|---|---|
| `ville` | Ville du bien |
| `quartier` | Quartier libre |
| `type_bien` | appartement, studio, maison, villa ou duplex |
| `surface` | Surface en m² |
| `pieces` | Nombre de pièces |
| `chambres` | Nombre de chambres |
| `salles_bain` | Nombre de salles de bain |
| `haut_standing` | Indicateur 0/1 |
| `en_construction` | Indicateur 0/1 |

Le nouveau modèle utilise uniquement ces informations. Aucune feature ne dépend du prix cible.

## Audit du dataset brut

Le fichier `data/raw/maisonlux_maroc_complet.csv` contient :

- **16 858 lignes** ;
- **4 colonnes** : `Titre`, `Prix`, `Localisation`, `Details` ;
- quatre colonnes textuelles ;
- aucune valeur manquante au format CSV brut ;
- **1 006 doublons exacts**.

### Problèmes détectés

| Problème | Nombre de lignes |
|---|---:|
| Doublons exacts | 1 006 |
| Prix non exploitable après déduplication | 1 169 |
| Type non reconnu par le contrat API | 1 762 |
| Valeurs d'entrée hors limites du formulaire | 23 |
| Titres explicitement liés à la location | 109 |
| Prix/m² manifestement mal formé ou hors périmètre | 472 |

Les prix bruts contiennent notamment :

- `Prix à consulter` et des prix de projet sans étiquette exploitable ;
- des annonces de location mélangées aux ventes ;
- des valeurs très basses proches d'un loyer mensuel ;
- des valeurs très hautes probablement saisies en centimes ou avec des zéros supplémentaires ;
- des valeurs EUR converties avec le taux historique de 10,8 MAD.

Le fichier brut n'a pas été modifié. Les règles de cohorte de cette expérience
historique sont conservées dans le présent audit ; le notebook d'expérience a été
retiré de l'arbre actif après sauvegarde externe.

## Cohorte de modélisation

La cohorte finale contient **12 267 lignes**, **150 villes**, **736 quartiers** et **12 182 groupes de listings**.

Règles fixées avant le split :

- type résidentiel reconnu par l'API ;
- surface entre 15 et 1 000 m² ;
- pièces, chambres et salles de bain dans les limites du formulaire ;
- exclusion des locations explicites ;
- prix entre 1 000 et 150 000 MAD/m² pour isoler les étiquettes manifestement erronées.

La cible reste fortement asymétrique : médiane 1,30 M MAD, 95e percentile 4,20 M MAD et maximum 150 M MAD. Les observations de luxe restantes ne sont pas retirées du test.

### Valeurs manquantes et variables faibles

- `Pieces` : 1 394 valeurs manquantes dans la cohorte ;
- `Chambres` : 116 ;
- `Salles_Bain` : 179.

L'imputation médiane est apprise uniquement sur le train. `Is_Haut_Standing` est détecté dans le titre et les détails, soit 285 annonces. `En_Construction` reste constant dans la cohorte : les projets concernés n'ont généralement pas de prix ou de surface exploitable. Son absence de signal est une limite connue.

## Doublons et stratégie de groupes

Après les doublons exacts, 158 lignes appartiennent encore à une signature répétée, soit 85 lignes supplémentaires au-delà d'un exemplaire par groupe.

La signature regroupe le titre, la localisation et les détails normalisés. `GroupShuffleSplit` empêche un même groupe d'apparaître dans plusieurs ensembles.

| Ensemble | Lignes |
|---|---:|
| Train | 8 585 |
| Validation | 1 838 |
| Test | 1 844 |

Il n'existe aucun groupe commun entre train, validation et test.

## Fuites de données historiques

Les notebooks historiques sont conservés sans modification, mais leur pipeline présente les problèmes suivants :

1. Isolation Forest est ajusté avant le split avec `Prix` parmi ses variables.
2. KNNImputer est ajusté avant le split et inclut également `Prix`.
3. La fréquence des quartiers est calculée sur tout le dataset.
4. Les catégories de ville sont créées avant le split.
5. Les hyperparamètres sont choisis sans jeu de validation séparé.
6. Le test est filtré avec son vrai `Prix_par_m2` avant l'évaluation.
7. Les transformations apprises sont réparties dans plusieurs artefacts et recodées manuellement dans le backend.

Le point 6 retire les observations difficiles après consultation de leur cible. Les anciennes métriques ne représentent donc pas un test intact.

## Baseline de production reproduite

Le modèle sauvegardé a été réévalué sur le sous-ensemble historique exact :

| Version | R² | MAE (MAD) | RMSE (MAD) |
|---|---:|---:|---:|
| Valeurs historiques dans l'ancien `metrics.json` | 0,640 | 349 342 | 542 509 |
| Artefact `model.pkl` réellement reproduit | 0,554 | 423 485 | 603 469 |

Cette différence prouve une dérive entre métriques et artefact. De plus, ce test historique est filtré avec la cible ; il ne doit pas être comparé directement au nouveau test groupé.

## Évaluation sans fuite

Le test reste intact jusqu'au choix final. La cross-validation à trois folds groupés est effectuée uniquement sur le train. La validation sert au choix du modèle, du target transform et du poids de l'ensemble.

Toutes les statistiques apprises sont encapsulées dans des pipelines scikit-learn :

- imputation médiane numérique ;
- imputation catégorielle par la modalité la plus fréquente ;
- one-hot encoding avec gestion des catégories inconnues ;
- scaling uniquement pour Ridge.

## Features testées

Features de base : surface, pièces, chambres, salles de bain, haut standing, construction, type, ville et quartier.

Features dérivées testées :

- surface par pièce ;
- surface par chambre ;
- ratio chambres/pièces ;
- densité des salles de bain ;
- écart pièces/chambres ;
- indicateur chambres supérieures aux pièces ;
- interactions surface × standing et surface × construction ;
- interaction catégorielle ville × type.

Les features dérivées n'ont pas amélioré la validation de manière stable. Le modèle final garde donc les features de base, plus simples à maintenir.

## Modèles comparés

- DummyRegressor ;
- Ridge ;
- DecisionTreeRegressor ;
- RandomForestRegressor ;
- ExtraTreesRegressor ;
- GradientBoostingRegressor ;
- HistGradientBoostingRegressor ;
- versions `log1p(Prix)` des familles les plus prometteuses.

Le log de la cible réduit la MAE et l'erreur médiane des arbres, mais les modèles bruts sont parfois meilleurs sur les très grandes erreurs. Un mélange Extra Trees log + Ridge apporte le meilleur compromis.

## Hyperparamètres

`RandomizedSearchCV` a testé 14 configurations Extra Trees et 10 configurations HistGradientBoosting. Ridge a comparé sept valeurs d'alpha. Chaque recherche utilise trois folds groupés du train.

Paramètres Extra Trees retenus :

- `max_depth=40` ;
- `min_samples_leaf=2` ;
- `min_samples_split=2` ;
- `max_features=0.6` ;
- 220 arbres en production.

La recherche favorisait 450 arbres, mais 220 donnent une validation pratiquement identique avec un artefact environ deux fois plus léger.

Ridge utilise `alpha=3`. Le mélange final est 75% Extra Trees sur `log1p(Prix)` et 25% Ridge.

## Comparaison avant/après

| Modèle / version | Jeu d'évaluation | R² | MAE (MAD) | RMSE (MAD) |
|---|---|---:|---:|---:|
| Production historique réellement reproduite | Test historique filtré | 0,554 | 423 485 | 603 469 |
| Random Forest actuel reconstruit sans fuite | Nouveau test groupé intact | 0,521 | 565 808 | 1 023 389 |
| Meilleur candidat individuel Extra Trees log | Nouveau test groupé intact | 0,620 | 401 553 | 911 493 |
| **Modèle final Extra Trees log + Ridge** | **Nouveau test groupé intact** | **0,639** | **395 559** | **888 301** |

Sur le même test que la baseline sans fuite :

- gain R² absolu : **+0,118** ;
- réduction MAE : **170 249 MAD**, soit **30,09%** ;
- réduction RMSE : **135 088 MAD**, soit **13,20%**.

## Surapprentissage

Le modèle final obtient sur train + validation : R² 0,50, MAE environ 281 k MAD et RMSE 1,44 M MAD. Sur le test : R² 0,639, MAE 396 k et RMSE 888 k.

Le score test supérieur est lié à une observation de validation à 150 M MAD qui domine le RMSE. Les erreurs extrêmes sont donc présentées explicitement plutôt que cachées.

## Performance par segment

Constats principaux sur le test :

- studios : MAE proche de 169 k MAD ;
- appartements : MAE proche de 383 k MAD ;
- duplex : MAE supérieure à 800 k MAD ;
- Casablanca : R² proche de 0,66 et MAE proche de 361 k MAD ;
- Rabat est plus difficile, avec une MAE proche de 765 k MAD ;
- les biens supérieurs à 5 M MAD ont une MAE supérieure à 3 M MAD ;
- l'erreur augmente fortement au-dessus de 250 m².

Les maisons et villas sont trop rares dans le test pour fournir une métrique de segment stable.

## Analyse des résidus

Les plus grandes erreurs sont principalement des biens de luxe ou des annonces dont le prix semble encore mal saisi. Le modèle sous-prédit notamment les duplex et appartements exceptionnels au-dessus de 7–10 M MAD.

La cause principale n'est pas seulement le modèle : le dataset ne contient ni surface terrain, ni géolocalisation précise, ni étage, ni parking, ni piscine, ni état détaillé. Deux biens avec les mêmes champs API peuvent donc avoir des prix très différents.

## Modèle final et production

Le modèle final a été choisi conjointement selon :

- R², MAE et RMSE ;
- écart train/validation ;
- stabilité des erreurs ;
- temps d'inférence ;
- poids de l'artefact ;
- compatibilité backend ;
- simplicité de maintenance.

Nouveaux artefacts :

- `pipeline.pkl` : preprocessing + ensemble complet ;
- `model_metadata.json` : contrat, villes, versions et hash ;
- `metrics.json` : baseline historique, baseline sans fuite, métriques finales et split.

Les anciens fichiers autonomes ont été retirés de l'arbre actif après sauvegarde
externe. Le backend charge `pipeline.pkl` ; seuls cet artefact, `metrics.json` et
`model_metadata.json` sont conservés dans `ml/artifacts/`.

## Changements backend

- chargement d'un seul artefact de pipeline ;
- suppression de la reconstruction manuelle du scaler et du frequency encoding ;
- utilisation des villes exportées dans les métadonnées ;
- RMSE final utilisé pour la fourchette indicative ;
- compatibilité conservée pour le dashboard des métriques ;
- routes accessibles avec ou sans slash final, ce qui correspond aux URLs du frontend.

Le schéma de requête et le format principal de réponse restent inchangés.

## Limites connues

1. La séparation vente/location repose encore en partie sur le titre.
2. Le prix par m² est utilisé uniquement pour auditer les étiquettes, avec des seuils métier perfectibles.
3. La devise EUR utilise le taux historique fixe de 10,8 MAD.
4. Peu de maisons et villas sont disponibles.
5. `En_Construction` n'a aucun exemple exploitable dans la cohorte.
6. Les catégories rares et villes peu représentées restent fragiles.
7. Le modèle sous-prédit les biens très chers.
8. Les annonces n'ont pas de date ni d'identifiant stable fourni par la source.

## Recommandations futures

- collecter vente et location séparément ;
- conserver URL, identifiant et date de l'annonce ;
- ajouter coordonnées, surface terrain, étage, ascenseur, parking, terrasse, piscine et état ;
- contrôler la devise et les saisies en centimes dès la collecte ;
- enrichir les villes et types sous-représentés ;
- surveiller les métriques par segment dans le temps ;
- tester CatBoost seulement si l'amélioration justifie une nouvelle dépendance ;
- ajouter des tests automatisés de schéma et de dérive de données.

## Phase 4.1 — Investigation de la cible R² 0,90

### Règle d'évaluation et test figé

La Phase 4.1 réutilisait exactement les **1 844 observations de test** de la Phase 4. Son manifeste
historique (index brut + groupe de listing) avait l'empreinte SHA-256
`b0d93a4cf01845a0fead2233a53bcfeb2b12c1ae37b58bb3fa0b99954d9eecdc` ; il a été retiré de
l'arbre actif avec les autres fichiers d'expérience après sauvegarde externe.

Une signature conservatrice supplémentaire combine titre normalisé sans nombres, ville, quartier,
surface, pièces et type. Elle a détecté 15 collisions côté train et 2 côté validation avec le test.
Ces 17 lignes sont mises en quarantaine ; aucune ligne de test n'est supprimée ou déplacée.

Les configurations, modèles spécialisés et poids de mélange ont été choisis uniquement sur le train
et la validation. Le test a ensuite été ouvert une seule fois pour les représentants figés.

### Signal supplémentaire extrait du texte

Les champs `Titre`, `Localisation` et `Details` ont permis de détecter, sans inventer de valeur :

- étage et RDC, ainsi qu'une surface mentionnée dans le titre ;
- ascenseur, parking/garage, terrasse, balcon, jardin et piscine ;
- meublé, neuf, rénové, à rénover et état de construction ;
- sécurité, concierge, climatisation, cheminée, cuisine équipée et double vitrage ;
- vue mer, vue montagne, proximité, titre foncier et signaux résidentiels/commerciaux ;
- nombre d'équipements, nombre d'indices de luxe et score d'état ;
- interactions ville-quartier, ville-type et quartier-type.

Le texte TF-IDF est normalisé et privé de **tous les nombres et termes monétaires** afin qu'il ne
puisse pas reconstruire le prix ou les variables numériques. Les attributs rares existent réellement,
mais plusieurs sont trop peu fréquents pour fournir un signal robuste.

### Qualité des prix

La reproduction exacte de la cohorte confirme les règles Phase 4 : 1 169 prix non utilisables,
109 locations explicites et 472 étiquettes hors de 1 000–150 000 MAD/m². Aucun exemple n'a été
retiré en fonction de son erreur de prédiction. Les valeurs `Prix à consulter` et `Projet` restent
non étiquetées ; les prix EUR utilisent le taux historique documenté de 10,8.

Le champ prix ne contient pas de suffixe mensuel ou prix/m² permettant une correction automatique
supplémentaire sûre. Les annonces suspectes restantes exigent l'URL, la devise, la nature de transaction
et les données détaillées de la page source pour être corrigées sans conjecture.

### Résultats sur le même test intact

| Modèle / architecture | R² | MAE (MAD) | RMSE (MAD) | Médiane AE | MAPE |
|---|---:|---:|---:|---:|---:|
| Phase 4 Voting Ensemble | 0,6392 | 395 559 | 888 301 | 204 586 | 24,98% |
| CatBoost base log1p | 0,6503 | 388 813 | 874 564 | 195 595 | 23,72% |
| CatBoost riche log1p | 0,6393 | 389 893 | 888 204 | 196 110 | 23,48% |
| Modèles par type | -0,0006 | 459 827 | 1 479 299 | 233 216 | 29,11% |
| Modèles par grande ville | 0,4000 | 455 708 | 1 145 453 | 253 491 | 31,21% |
| TF-IDF + structuré Ridge | 0,5772 | 474 702 | 961 554 | 271 914 | 34,53% |
| **75% CatBoost riche log + 25% TF-IDF/Ridge** | **0,6560** | **386 983** | **867 343** | **197 475** | **24,36%** |

Le mélange utilise le poids texte de 25% choisi sur validation. Le meilleur résultat légitime est donc
**R² 0,6560** : aucun niveau supérieur ou égal à 0,70 n'est atteint.

### Stabilité par validation croisée groupée

CatBoost riche log1p obtient sur trois folds groupés : R² 0,652, 0,568 et 0,607.
La moyenne est **0,609 ± 0,034**, avec MAE moyenne **381 428 MAD** et RMSE moyenne **876 911 MAD**.
La dispersion ne soutient pas l'hypothèse qu'un score de 0,90 serait obtenu avec un fold favorable.

### Idées rejetées

- Les modèles par type dégradent fortement le résultat : 61 villas et 51 maisons dans train+validation
  sont insuffisantes ; même appartement/studio ne gagnent pas globalement.
- Les modèles dédiés Casablanca, Marrakech et Tanger donnent R² global 0,400.
- Les attributs riches améliorent certaines erreurs typiques mais pas les grandes erreurs quadratiques.
- TF-IDF seul n'est pas compétitif ; il apporte seulement un petit complément dans le mélange.
- CatBoost brut est instable face aux très grandes étiquettes ; `log1p` généralise mieux.
- XGBoost et LightGBM n'ont pas été ajoutés : CatBoost, mieux adapté aux catégories natives, n'apporte
  déjà qu'un faible gain déployable ; deux dépendances supplémentaires ne sont pas justifiées.

### Pourquoi R² 0,90 n'est pas réaliste avec les informations actuelles

Sur le test, l'écart-type du prix est 1 478 831 MAD. R² 0,90 exige donc un RMSE maximal de
**467 648 MAD**. Le meilleur mélange est à 867 343 MAD : il faudrait réduire sa somme des erreurs
quadratiques de **70,93%**.

Les 19 plus grandes erreurs (1% du test) représentent **64,87%** de cette somme, et les 55 biens
supérieurs à 5 M MAD en représentent **71,31%**. Leur MAE est 3,09 M MAD. Le dataset ne décrit pas
la surface du terrain, l'adresse/coordonnée exacte, l'étage de façon systématique, l'état réel,
les prestations complètes ou la date de marché nécessaires pour séparer ces biens.

De plus, 1 642 lignes appartiennent à 702 groupes ayant exactement les mêmes entrées API observables.
Dans 95 groupes, soit 277 lignes, le prix maximal dépasse le minimum de plus de 1,5 fois. Un modèle
recevant les champs actuels ne peut mathématiquement distinguer ces annonces contradictoires.

La courbe d'apprentissage passe de 2 143 à 8 570 lignes de train : la MAE validation baisse de 539 755
à environ 498 569 MAD, mais plafonne. Ajouter uniquement davantage de lignes avec le même schéma ne
suffira donc pas.

### Audit du scraper et plan d'acquisition

Le scraper actuel lit seulement les cartes de résultat et conserve quatre chaînes. Il ne capture ni
URL/identifiant, ni date, ni transaction, ni page détaillée, ni coordonnées, ni liste structurée des
équipements. Il ne permet donc pas de dédupliquer durablement ou de contrôler la dérive temporelle.

Objectif d'acquisition recommandé — sans garantie artificielle de R² 0,90 : atteindre **au moins
50 000 ventes uniques et vérifiées**, soit environ **40 000 nouvelles annonces** après contrôles,
dont 3 000–5 000 biens supérieurs à 5 M MAD et au moins 1 000 exemples pour villa, maison et duplex.
Chaque grande ville devrait disposer de plusieurs milliers de ventes récentes.

Le schéma futur doit ajouter : URL et ID source, date de collecte/publication, vente/location,
devise et prix brut, coordonnées/adresse, surface habitable et terrain, étage/total d'étages,
ancienneté, état, parking, ascenseur, terrasse, balcon, jardin, piscine, orientation, vues,
ameublement, sécurité, titre foncier, frais et texte détaillé. Les contrôles de prix doivent être
effectués à la collecte et les doublons reliés par ID/URL.

### Décision de production

La pipeline Phase 4 reste en production. CatBoost base est déployable avec les entrées actuelles mais
son gain (R² +0,0111 et MAE -1,71%) est trop faible face à une dépendance d'environ 100 MB. Le meilleur
mélange offline gagne R² +0,0168 et MAE -2,17%, mais dépend du titre/détails absents de l'API et du
formulaire. Le frontend n'est donc pas modifié et `pipeline.pkl` n'est pas remplacé.

**BEST LEGITIMATE RESULT: R² 0,6560. TARGET R² 0,90 NON ATTEINTE.**
