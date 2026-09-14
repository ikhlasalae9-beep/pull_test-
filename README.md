# MaisonDeLUX

Prototype PFE d'estimation des prix d'annonces immobilières au Maroc. L'application Next.js conserve son parcours français/arabe et utilise le modèle Python final, sans prix simulé.

## Architecture et fichiers de référence

- Site : `app/`, `components/`, `config/`, `messages/` (Next.js à la racine).
- API : `app/api/estimate/route.ts` relaie vers `backend/app.py` (Flask).
- Dataset final : `data/processed/maisondelux_model_ready_v1.csv` (13 537 lignes, versionné).
- Notebook exécuté : `ml/notebooks/maisondelux_notebook1.ipynb`.
- Modèle : `models/maisondelux_price_model_v1.joblib`, prétraitement et inversion logarithmique inclus.
- Transformer réutilisable : `ml/src/inference.py`.
- Collecte/récupération : `ml/scraping/`, `ml/src/pipeline.py`, `ml/src/data_repair/`, `ml/src/scraping_v3/`.

## Installation et lancement

Depuis la racine, avec Python 3.12 et Node.js :

```sh
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m backend.app
```

Dans un second terminal :

```sh
npm ci
npm run dev
```

Ouvrir `http://localhost:3000/fr/estimation` ou `/ar/estimation`. Le navigateur appelle la route du site ; le serveur Next.js contacte Flask sur `http://127.0.0.1:5000`. Pour un autre hôte, définir `INFERENCE_API_URL` côté serveur. Pour vérifier la version optimisée : `npm run build`, puis `npm run start`.

Tester une prédiction (PowerShell) :

```powershell
$body = @{surface_m2=120; bedrooms=3; bathrooms=2; region='Casablanca-Settat'; city='Casablanca'; neighborhood='Maârif'; property_type='appartement'} | ConvertTo-Json
Invoke-RestMethod http://localhost:3000/api/estimate -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

## Vérification et documentation

```sh
python -m pytest tests/test_inference.py -q -p no:cacheprovider
python -m pip install -r requirements-scraping.txt
python -m pytest -q -p no:cacheprovider --basetemp=outputs/pytest
npm run build
```

Certains tests historiques des exports nécessitent les données locales de récupération et les références géographiques, qui ne sont pas toutes versionnées. Les tests d'inférence utilisent uniquement le dataset final et le modèle versionnés. Aucun réentraînement n'est nécessaire pour lancer le site.

- [Historique des données](docs/DATA_PIPELINE.md)
- [Collecte et récupération](docs/SCRAPING_AND_RECOVERY.md)
- [Modèle V1 et contrat API](docs/MODEL_V1.md)
- [Inventaire final](reports/inventory/finalization_inventory.md)

Le prototype est principalement adapté aux appartements à vendre. Les prix sont indicatifs, non des expertises officielles. Les documents historiques sont conservés pour la traçabilité ; MODEL_V1 décrit le modèle servi actuellement.
