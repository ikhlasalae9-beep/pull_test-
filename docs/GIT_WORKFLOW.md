# Guide Git de l'équipe MaisonDeLUX

Ce guide explique comment travailler avec Git sans risquer de casser le projet. Lis les commandes avant de les lancer et demande de l'aide si un résultat semble bizarre.

## Nos branches

```text
dev/zineb ──┐
            ├──> develop ──> test ──> main
dev/alae ───┘
```

| Branche | Rôle |
|---|---|
| `main` | Version finale, stable et validée. |
| `test` | Version vérifiée avant son arrivée dans `main`. |
| `develop` | Branche commune qui rassemble le travail de l'équipe. |
| `dev/zineb` | Branche personnelle de Zineb. |
| `dev/alae` | Branche personnelle d'Alae. |
| `codex/*` | Branches temporaires pour un travail technique bien séparé. |

> **Règle très importante :** Zineb travaille uniquement sur `dev/zineb` et Alae uniquement sur `dev/alae`. Ne commencez jamais une modification directement sur `main`, `test` ou `develop`.

## Avant de commencer une tâche

Depuis le terminal :

```bash
cd MaisonDeLUX
git status
git branch --show-current
git fetch origin
git switch develop
git pull --ff-only origin develop
```

Retourne ensuite sur ta branche personnelle :

```bash
# Zineb
git switch dev/zineb
git merge develop
```

```bash
# Alae
git switch dev/alae
git merge develop
```

`git merge develop` apporte les dernières modifications communes dans ta branche personnelle. Bdarija : *katjib آخر nouveautés dyal l'équipe l-branche dyalk*.

Si le terminal affiche `CONFLICT`, arrête-toi et demande de l'aide. Ne modifie pas les marqueurs de conflit au hasard.

### Checklist rapide

1. `git status`
2. `git branch --show-current`
3. `git fetch origin`
4. `git switch develop`
5. `git pull --ff-only origin develop`
6. `git switch dev/zineb` ou `git switch dev/alae`
7. `git merge develop`
8. Commencer le travail.

## Enregistrer et envoyer son travail

Ces quatre commandes ont des rôles différents :

| Commande | Explication simple |
|---|---|
| `git status` | Montre les fichiers modifiés et ceux qui sont prêts à être enregistrés. |
| `git add .` | Prépare les modifications pour le prochain point de sauvegarde. Cela n'envoie rien sur GitHub. |
| `git commit -m "message"` | Crée un point de sauvegarde local avec une description. |
| `git push origin branche` | Envoie les commits locaux vers GitHub. |

Workflow normal :

```bash
git status
git add .
git status
git commit -m "feat: description courte de mon travail"
```

Puis pousser la bonne branche :

```bash
# Zineb
git push origin dev/zineb
```

```bash
# Alae
git push origin dev/alae
```

Après le push, préviens Houssin/Codex que ta branche est prête à être intégrée dans `develop`.

## Exemples de bons messages de commit

```bash
git commit -m "feat: improve estimation form"
git commit -m "fix: correct dashboard layout"
git commit -m "data: clean missing property values"
git commit -m "ml: add model evaluation charts"
git commit -m "docs: update project documentation"
git commit -m "fix: correct city selection bug"
git commit -m "chore: clean unused files"
```

Le message doit expliquer ce qui a changé. Évite les messages vagues comme `update`, `test`, `aaa`, `final`, `final2`, `change` ou `stuff`.

## Recevoir les dernières modifications

### Cas A — Aucun travail local en cours

```bash
git switch develop
git pull --ff-only origin develop
git switch dev/zineb
git merge develop
```

Pour Alae, utilise `git switch dev/alae` à la place de `git switch dev/zineb`.

### Cas B — Des fichiers sont déjà modifiés

Commence par vérifier :

```bash
git status
```

Si les changements sont bien les tiens et peuvent être enregistrés :

```bash
git add .
git commit -m "wip: save current work before sync"
git switch develop
git pull --ff-only origin develop
git switch dev/zineb
git merge develop
```

Pour Alae, utilise `git switch dev/alae`. Si tu ne comprends pas les fichiers affichés par `git status`, demande de l'aide avant de continuer.

## Différence entre fetch et pull

```bash
git fetch origin
```

Cette commande télécharge seulement les informations récentes de GitHub. Elle ne modifie pas les fichiers actuels. C'est la bonne première étape.

```bash
git pull --ff-only origin develop
```

Cette commande télécharge puis met à jour `develop`. Pour l'équipe, utilise-la uniquement après `git switch develop`.

## Faire intégrer son travail

Zineb et Alae ne fusionnent pas directement leur travail dans `main`.

Le parcours normal est :

```text
dev/zineb → develop
dev/alae  → develop
```

Avant de demander l'intégration :

```bash
git status
git add .
git commit -m "feat: describe completed work"
git push origin dev/zineb
```

Alae utilise `git push origin dev/alae`. Ensuite, dis : « Houssin/Codex, ma branche est prête à être intégrée dans `develop`. » Le mainteneur vérifie puis effectue la fusion.

## De develop vers test puis main

```text
develop → test → main
```

- `develop` rassemble les travaux terminés.
- `test` vérifie que tout fonctionne ensemble.
- `main` reçoit seulement le travail stable et validé.

Cette promotion est gérée par le mainteneur/Codex. Ce n'est pas la responsabilité normale de Zineb ou Alae. Il n'y a jamais de passage direct de `dev/zineb` vers `main`, ni de `dev/alae` vers `main`.

## Après avoir terminé une tâche

```bash
git status
git add .
git status
git commit -m "feat: description claire"
git push origin dev/zineb
```

Alae remplace la dernière commande par `git push origin dev/alae`. Préviens ensuite le mainteneur.

## Commandes utiles

| Commande | Utilité |
|---|---|
| `git status` | Voir les changements actuels. |
| `git branch` | Lister les branches locales. |
| `git branch --show-current` | Voir la branche actuelle. |
| `git switch branch-name` | Changer de branche. |
| `git fetch origin` | Vérifier et télécharger les informations GitHub. |
| `git pull --ff-only origin develop` | Mettre `develop` à jour de manière sûre. |
| `git add .` | Préparer les changements pour le commit. |
| `git commit -m "message"` | Enregistrer un point de sauvegarde local. |
| `git push origin branch` | Envoyer les commits vers GitHub. |
| `git log --oneline -10` | Voir les dix derniers commits. |
| `git diff` | Voir le contenu des modifications non préparées. |

## ⚠️ Commandes dangereuses

> **NE LANCE JAMAIS CES COMMANDES SANS DEMANDER D'ABORD :**

```bash
git reset --hard
git clean -fd
git push --force
git push -f
git rebase
git branch -D
```

Elles peuvent supprimer du travail ou réécrire l'historique partagé. Ne supprime jamais une branche sur GitHub sans autorisation. Ne résous jamais un conflit au hasard, ne copie jamais la branche d'un collègue par-dessus la tienne et ne travaille jamais directement sur `main`.

## Conflits de fusion

Un conflit signifie que deux personnes ont modifié la même partie d'un fichier et que Git ne sait pas quelle version choisir.

Si tu vois `CONFLICT` ou ces marqueurs :

```text
<<<<<<<
=======
>>>>>>>
```

Arrête-toi. Lance seulement :

```bash
git status
```

Copie le résultat et envoie-le à Houssin/Codex. Ne devine pas la solution.

## Problèmes fréquents

### « Your branch is behind »

Ta branche n'a pas encore les dernières modifications :

```bash
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch dev/zineb
git merge develop
```

Alae utilise `git switch dev/alae`.

### « nothing to commit, working tree clean »

Tout est déjà enregistré localement. Il n'y a rien de nouveau à mettre dans un commit.

### « Everything up-to-date »

GitHub possède déjà tes derniers commits. Aucun nouvel envoi n'est nécessaire.

### « Please commit your changes or stash them before you merge »

Ne cache pas les changements au hasard. Lance `git status`. Si ce sont bien tes modifications, enregistre-les avec `git add .` puis un commit. Si tu hésites, demande de l'aide.

### « merge conflict »

Arrête-toi, lance `git status`, copie le résultat et demande de l'aide.
