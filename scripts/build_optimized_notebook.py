"""Construit une copie du notebook ; conserve strictement le fichier source."""
from pathlib import Path
import hashlib
import json
import textwrap
import nbformat

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'ml/notebooks/maisondelux_notebook1.ipynb'
TARGET = ROOT/'ml/notebooks/maisondelux_notebook_optimized.ipynb'


def build():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    notebook = nbformat.read(SOURCE,as_version=4)
    # Neutralisation structurelle : les sections historiques réévaluaient le
    # holdout, testaient des sous-populations et écrasaient le modèle de production.
    for index,cell in enumerate(notebook.cells):
        if cell.cell_type=='code':
            cell.outputs=[]
            cell.execution_count=None
            if index>=96:
                cell.source = '# Archive historique : exécution remplacée par la partie 7.\nif False:\n'+textwrap.indent(cell.source,'    ')
        if cell.cell_type=='markdown' and 'Conclusion' in cell.source or index==196:
            cell.source = '> **Archive historique** : chiffres et interprétations antérieurs, non validés par cette nouvelle expérience.\n\n'+cell.source
    notebook.cells[3].source = notebook.cells[3].source.replace(
        'test_raw = pd.read_csv(test_path, low_memory=False)',
        'test_raw = pd.read_csv(test_path, low_memory=False, usecols=lambda c: c != "price_mad")')
    notebook.cells.insert(0,nbformat.v4.new_markdown_cell(
        '# MaisonDeLUX — notebook optimisé\n\n'
        'Source disponible : `maisondelux_notebook1.ipynb` (la version `(5)` n’était pas jointe). '
        'Original conservé, SHA-256 : `'+digest+'`.\n\n'
        'L’EDA est conservée. Les cellules de preprocessing/modélisation historiques sont archivées '
        'sous `if False` pour empêcher leurs évaluations répétées du test et leurs écritures sur le modèle existant. '
        'La partie 7 les remplace. Les anciens commentaires chiffrés sont historiques. '
        'Les fonctions réutilisables sont dans `ml/src/advanced_optimization.py`, livré avec ce notebook.'))
    md=nbformat.v4.new_markdown_cell
    code=nbformat.v4.new_code_cell
    notebook.cells.extend([
        md('## PARTIE 7 — OPTIMISATION AVANCÉE DU MODÈLE\n\n'
           'Sélection par MAE OOF sur cinq folds groupés. Le R² reste secondaire : atteindre 0,80 ne justifie '
           'ni un changement de population test ni une fuite de cible. Le test historique a déjà été consulté : '
           'il ne constitue plus un jeu externe totalement inédit. Une seule nouvelle évaluation est autorisée.'),
        code('from pathlib import Path\nimport sys\nimport json\nimport pandas as pd\n'
             'PROJECT_ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "ml/src/advanced_optimization.py").exists())\n'
             'if str(PROJECT_ROOT) not in sys.path:\n    sys.path.insert(0, str(PROJECT_ROOT))\n'
             'from ml.src.advanced_optimization import (CONFIG as DEFAULT_CONFIG, audit_dataset,\n'
             '    detect_leakage_columns, build_safe_features, add_numeric_features, add_location_features,\n'
             '    add_text_features, prepare_catboost_frame, create_group_cv, evaluate_oof_predictions,\n'
             '    regression_metrics, calculate_segment_metrics, tune_model, optimize_blend_weights,\n'
             '    train_final_model, validate_final_pipeline, predict_property_price, run_experiments)\n'
             'FAST_MODE = False\nN_TRIALS = 50\n'
             'CONFIG = DEFAULT_CONFIG | {"optuna_trials": 3 if FAST_MODE else N_TRIALS,\n'
             '                           "iterations": 150 if FAST_MODE else 650}\nCONFIG'),
        md('### 7.1 Audit et population autorisée\n\n'
           'Les groupes sont les composantes connexes des identifiants, URL et signatures '
           '(ville, quartier, type, surface arrondie à 5 m², chambres, salles de bains). '
           'La signature peut regrouper des biens distincts : ce choix prudent rend le protocole plus strict. '
           'Les groupes touchant le holdout sont retirés uniquement du train ; aucune ligne test n’est retirée.\n\n'
           'L’augmentation fournie ne contient pas de parent vérifiable et son générateur est absent. '
           'Les scénarios à poids 1 et 0,25 sont déclarés non évaluables, et non présentés comme des expériences réussies. '
           'Leur effet sur la performance demeure inconnu. Il faut le générateur et la correspondance parent/enfant '
           'pour les produire au sein de chaque fold sans contamination.\n\n'
           '15 % des groupes réels sûrs sont réservés à la calibration avant le tuning. '
           'Les distributions de cible du holdout ne sont pas consultées avant le gel.'),
        md('### 7.2 Features et protocole\n\n'
           'Liste blanche du formulaire, catégories natives CatBoost, valeurs tri-state conservées. '
           'Interactions de surface/pièces, indicateurs de manque, équipements, hiérarchie géographique, '
           'fréquences et winsorisation apprises au fit. Le carré de surface est un candidat séparé. '
           'Aucune coordonnée inventée. Les textes sont audités et leurs chiffres masqués ; '
           'TF-IDF n’est pas testé puisque le formulaire ne fournit aucun texte d’annonce.\n\n'
           'CatBoost, LightGBM, XGBoost, HistGradientBoosting, ExtraTrees et RandomForest ; RAW/LOG ; '
           'pertes RMSE/MAE/Huber/Quantile. Early stopping sur un sous-split groupé interne, '
           'puis réentraînement avant prédiction du fold externe. CPU à quatre threads pour la reproductibilité. '
           'Optuna : 50 essais maximum, stockage SQLite reprenable, sélection MAE puis R².\n\n'
           'Le modèle résiduel apprend ses offsets géographiques par cross-fitting interne. '
           'Les experts par ville sont choisis dans une CV interne avec gain local minimal de 2 %. '
           'Les ensembles moyenne, poids convexes et Ridge disposent d’une validation imbriquée ; '
           'ils ne remplacent le meilleur individuel que pour un gain MAE d’au moins 1 % dans au moins quatre folds. '
           'Des blends post-hoc sont aussi exportés, explicitement non éligibles à la sélection.'),
        md('### 7.3 Exécution et reprise\n\n'
           'Cette cellule lance réellement les expériences si elles n’existent pas. Après l’évaluation finale, '
           'elle recharge les résultats figés sans réinterroger le holdout. Les caches conservent les candidats terminés. '
           'Le budget de 50 essais peut demander un temps de calcul important.'),
        code('advanced_results = run_experiments(CONFIG)\n'
             'REPORT_DIR = PROJECT_ROOT / "reports/advanced_optimization"\n'
             'display(pd.read_csv(REPORT_DIR / "oof_leaderboard.csv").drop(columns="spec"))'),
        md('### 7.4 Résultats OOF et erreurs par segment'),
        code('display(pd.read_csv(REPORT_DIR / "augmentation_scenarios.csv"))\n'
             'display(pd.read_csv(REPORT_DIR / "seed_stability.csv"))\n'
             'segments = pd.read_csv(REPORT_DIR / "oof_segments.csv")\n'
             'for dimension in segments.segment.unique():\n'
             '    print(dimension)\n    display(segments[segments.segment.eq(dimension)])'),
        code('import matplotlib.pyplot as plt\n'
             'price_errors = segments[segments.segment.eq("price_band")]\n'
             'fig, axes = plt.subplots(1, 2, figsize=(13, 4))\n'
             'axes[0].bar(price_errors.value, price_errors.MAE)\n'
             'axes[0].set_title("MAE OOF par tranche de prix")\n'
             'axes[1].bar(price_errors.value, price_errors.bias_mad)\n'
             'axes[1].set_title("Biais OOF : positif = surestimation")\n'
             'for ax in axes:\n    ax.tick_params(axis="x", rotation=60)\n    ax.set_ylabel("MAD")\n'
             'fig.tight_layout()\nplt.show()'),
        md('### 7.5 Modèle figé et holdout réel\n\n'
           'Seul le modèle sélectionné est évalué sur les 2 708 lignes test. '
           'Les lignes de comparaison OOF et historique ne sont pas des évaluations du même protocole. '
           'Les métriques historiques non disponibles restent vides.'),
        code('display(pd.read_csv(REPORT_DIR / "final_comparison.csv"))\n'
             'print("Configuration retenue :", advanced_results["spec"])\n'
             'print("Itérations finales :", advanced_results["iterations"])\n'
             'print("Meilleur R² OOF exploré :", advanced_results["best_oof_R2"])\n'
             'print("Objectif R² holdout ≥ 0,80 atteint :", advanced_results["holdout"]["R2"] >= .80)'),
        md('### 7.6 Sauvegarde et inférence\n\n'
           '`models/advanced_optimization/pipeline.joblib` contient le préprocesseur, le modèle et le rayon conforme. '
           'Les versions, paramètres, schémas et mappings sont enregistrés dans `metadata.json`. '
           'Le modèle de production existant est conservé.\n\n'
           'Calibration split-conformal à 90 % sur les groupes réservés : maximum du résidu absolu par groupe '
           'et quantile corrigé en échantillon fini. Validité marginale sous échangeabilité des groupes ; '
           'aucune garantie de couverture conditionnelle par ville. Les groupes de calibration ne sont pas '
           'réincorporés dans l’entraînement final.'),
        code('predict_property_price({"ville": "Casablanca", "quartier": "Maarif",\n'
             '                        "type_bien": "appartement", "surface": 85,\n'
             '                        "chambres": 2, "salles_bain": 1, "parking": "unknown"})'),
        md('### 7.7 Conclusions et limites mesurées'),
        code('print(json.dumps(advanced_results["audit"], ensure_ascii=False, indent=2))\n'
             'for limitation in advanced_results["limitations"]:\n    print("•", limitation)\n'
             'print("Variables à collecter : coordonnées fiables, étage/ascenseur, état et âge du bien, "\n'
             '      "qualité des finitions, équipements renseignés et prix de transaction datés.")\n'
             'print("Ces données pourraient aider ; aucun gain jusqu’à 0,80 ne peut être garanti.")'),
    ])
    notebook.metadata.kernelspec = dict(display_name='Python 3',language='python',name='python3')
    nbformat.write(notebook,TARGET)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
    print(TARGET)


if __name__=='__main__':
    build()
