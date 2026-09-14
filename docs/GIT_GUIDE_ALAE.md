# Guide Git — Alae

Ta branche de travail est toujours `dev/alae`.

Tu peux consulter `develop` pour la mettre à jour, mais tu ne dois pas modifier directement `main`, `test` ou `develop`.

## Comment vérifier que je suis dans la bonne branche ?

```bash
git branch --show-current
```

Résultat attendu :

```text
dev/alae
```

Si le résultat est `main`, `test` ou `develop`, ne commence pas à modifier les fichiers. Reviens d'abord sur ta branche avec :

```bash
git switch dev/alae
```

## Début de journée

Copie les commandes une par une :

```bash
cd MaisonDeLUX
git status
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch dev/alae
git merge develop
```

Tu es maintenant sur ta branche avec les dernières modifications communes. Tu peux travailler.

Si `git status` montre des modifications que tu ne reconnais pas, arrête-toi et demande de l'aide avant de changer de branche.

## Pendant le travail

Tu peux vérifier tes changements à tout moment :

```bash
git status
git diff
```

`git status` liste les fichiers modifiés. `git diff` montre les lignes modifiées.

## Fin de tâche

```bash
git status
git add .
git status
git commit -m "feat: description claire"
git push origin dev/alae
```

- `git add .` prépare les fichiers, mais n'envoie rien sur GitHub.
- `git commit` crée un point de sauvegarde local.
- `git push` envoie ce point de sauvegarde sur GitHub.

Après le push, informe Houssin/Codex que `dev/alae` est prête à être intégrée dans `develop`.

## Si un conflit apparaît

Un conflit signifie que Git ne sait pas choisir entre deux modifications du même endroit.

Si tu vois `CONFLICT`, `<<<<<<<`, `=======` ou `>>>>>>>`, arrête-toi. Lance :

```bash
git status
```

Copie le résultat et envoie-le à Houssin/Codex. Ne choisis pas une version au hasard.

## Si quelque chose semble bizarre

**STOP.**

Ne supprime aucun fichier. Ne réinitialise pas Git.

```bash
git status
git branch --show-current
```

Prends une capture d'écran ou copie le résultat du terminal, puis envoie-le à Houssin/Codex.
