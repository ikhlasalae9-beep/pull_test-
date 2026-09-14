"""Expériences reproductibles MaisonDeLUX, sans sélection sur le holdout."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import re
import time
import unicodedata
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import HistGradientBoostingRegressor, ExtraTreesRegressor, RandomForestRegressor
from sklearn.metrics import r2_score
from scipy.optimize import minimize

TARGET = 'price_mad'
FAST_MODE = False
N_TRIALS = 50
CONFIG = dict(random_state=42, target=TARGET, n_splits=5, run_optuna=True,
              optuna_trials=N_TRIALS, use_gpu_if_available=False,
              primary_metric='MAE', secondary_metric='R2', threads=4,
              iterations=650, calibration_fraction=.15, alpha=.10)
NUMERIC = ['surface_m2', 'bedrooms', 'bathrooms']
CATEGORICAL = ['region', 'city', 'neighborhood', 'property_type',
               'parking', 'balcony', 'sea_view', 'furnished_status']
FORBIDDEN = {TARGET, 'price_per_m2', 'price_per_m2_original',
             'price_per_m2_recomputed', 'price_raw', 'log_price', 'listing_id',
             'source_listing_id', 'url', 'canonical_url_repaired', 'split_group'}


def find_root():
    """Cherche le projet sans chemin spécifique à une machine."""
    for root in [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]:
        if (root / 'data/processed/maisondelux_test_real_holdout_v2.csv').exists():
            return root
    raise FileNotFoundError('Données MaisonDeLUX introuvables.')


def normalized(value):
    """Normalisation déterministe, sans information supervisée."""
    if pd.isna(value) or not str(value).strip():
        return 'unknown'
    value = unicodedata.normalize('NFKD', str(value).lower().strip())
    return re.sub(r'\s+', ' ', ''.join(c for c in value if not unicodedata.combining(c)))


def detect_leakage_columns(columns):
    """Liste de refus complémentaire à une liste blanche de prédicteurs."""
    return [c for c in columns if c in FORBIDDEN or
            re.search(r'price|prix|duplicate|outlier|repair_evidence|source_|batch_|validation_', c)]


def build_safe_features(frame):
    """Seuls les champs du formulaire sont autorisés, jamais les colonnes d'audit."""
    x = pd.DataFrame(index=frame.index)
    for c in NUMERIC:
        x[c] = pd.to_numeric(frame.get(c, pd.Series(np.nan, index=frame.index)), errors='coerce')
        x[c] = x[c].where(x[c] >= (1 if c == 'surface_m2' else 0))
    for c in CATEGORICAL:
        source = {'neighborhood': 'neighborhood_clean', 'property_type': 'property_type_repaired'}.get(c, c)
        values = frame[source] if source in frame else frame.get(c, pd.Series('unknown', index=frame.index))
        x[c] = values.map(normalized).astype(object)
    x['furnished_status'] = x.furnished_status.replace({'furnished': 'yes', 'unfurnished': 'no'})
    for c in CATEGORICAL[4:]:
        x[c] = x[c].where(x[c].isin(['yes', 'no']), 'unknown')
    assert not detect_leakage_columns(x.columns)
    return x.replace([np.inf, -np.inf], np.nan)


def add_numeric_features(x, square=False):
    """Interactions physiques, valeurs manquantes et divisions protégées."""
    x = x.copy()
    s, b, a = x.surface_m2, x.bedrooms, x.bathrooms
    x['log_surface_m2'], x['sqrt_surface_m2'] = np.log1p(s), np.sqrt(s)
    if square:
        x['surface_squared'] = s ** 2
    x['rooms_total'] = b + a
    x['surface_per_bedroom'] = s / b.where(b > 0)
    x['surface_per_room'] = s / (b + a).where(b + a > 0)
    x['bathroom_bedroom_ratio'] = a / b.where(b > 0)
    x['surface_bedrooms'], x['surface_bathrooms'] = s*b, s*a
    x['is_large_property'], x['is_small_property'] = (s >= 200).astype(int), (s < 50).astype(int)
    for c in NUMERIC:
        x[c + '_missing'] = x[c].isna().astype(int)
    x['surface_category'] = pd.cut(s, [0, 35, 70, 120, 200, np.inf],
                                    labels=['studio', 'small', 'medium', 'large', 'luxury']).astype(object).fillna('unknown')
    amen = x[CATEGORICAL[4:]]
    x['amenities_positive'] = amen.eq('yes').sum(axis=1)
    x['amenities_unknown'] = amen.eq('unknown').sum(axis=1)
    known = 4 - x.amenities_unknown
    x['amenities_ratio'] = x.amenities_positive / known.where(known > 0)
    x['parking_balcony'] = x.parking + '|' + x.balcony
    x['sea_furnished'] = x.sea_view + '|' + x.furnished_status
    return x.replace([np.inf, -np.inf], np.nan)


def add_location_features(x):
    """Hiérarchie géographique non supervisée."""
    x = x.copy()
    for name, cols in {'region_city': ['region', 'city'], 'city_neighborhood': ['city', 'neighborhood'],
                       'city_property_type': ['city', 'property_type'],
                       'neighborhood_property_type': ['city', 'neighborhood', 'property_type']}.items():
        x[name] = x[cols].agg('|'.join, axis=1)
    x['neighborhood_length'] = x.neighborhood.str.len()
    x['neighborhood_words'] = x.neighborhood.str.split().str.len()
    return x


def add_text_features(frame):
    """Diagnostic seulement : masque tous les chiffres et montants potentiels.

    Le formulaire ne fournit pas de texte : cette branche n'est pas déployable.
    Aucune représentation de texte n'entre dans les modèles sélectionnables.
    """
    text = pd.Series('', index=frame.index)
    for c in ['title_raw', 'details_raw', 'location_raw']:
        if c in frame:
            text += ' ' + frame[c].fillna('').map(normalized)
    text = text.str.replace(r'\d+(?:[\s.,]\d+)*', ' ', regex=True)
    return pd.DataFrame({'text_length': text.str.len(), 'text_words': text.str.split().str.len()})


class SafePreprocessor:
    """Fréquences, winsorisation et catégories apprises exclusivement au fit."""
    def __init__(self, advanced=True, square=False, native=False):
        self.advanced, self.square, self.native = advanced, square, native

    def base(self, frame):
        x = build_safe_features(frame)
        return add_location_features(add_numeric_features(x, self.square)) if self.advanced else x

    def fit(self, frame):
        x = self.base(frame)
        self.bounds = x.surface_m2.quantile([.01, .99]).to_numpy()
        self.frequencies = {c: x[c].value_counts(normalize=True).to_dict()
                            for c in ['city', 'neighborhood', 'city_neighborhood'] if c in x}
        self.counts = {c: x[c].value_counts().to_dict() for c in ['city', 'neighborhood']}
        x = self.enrich(x)
        self.columns = x.columns.tolist()
        self.cats = x.select_dtypes(exclude='number').columns.tolist()
        self.nums = [c for c in x if c not in self.cats]
        self.medians = x[self.nums].median().fillna(0)
        self.encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
        self.encoder.fit(x[self.cats])
        return self

    def enrich(self, x):
        if self.advanced:
            x['surface_winsorized'] = x.surface_m2.clip(*self.bounds)
            for c, mapping in self.frequencies.items():
                x[c + '_frequency'] = x[c].map(mapping).fillna(0)
            for c, mapping in self.counts.items():
                x[c + '_rare'] = (x[c].map(mapping).fillna(0) < 10).astype(int)
        return x

    def transform(self, frame):
        x = self.enrich(self.base(frame)).reindex(columns=self.columns)
        x[self.nums] = x[self.nums].fillna(self.medians)
        if not self.native:
            x[self.cats] = self.encoder.transform(x[self.cats])
        assert not detect_leakage_columns(x.columns)
        assert len(x) == len(frame)
        return x


def prepare_catboost_frame(frame, preprocessor):
    """Applique exactement le préprocesseur enregistré."""
    return preprocessor.transform(frame)


def create_group_cv(frame, n_splits=5):
    """GroupKFold déterministe ; aucune séparation d'un groupe."""
    folds = list(GroupKFold(n_splits).split(frame, groups=frame.split_group))
    for tr, va in folds:
        assert not set(frame.iloc[tr].split_group) & set(frame.iloc[va].split_group)
    return folds


def regression_metrics(y, p):
    """Toutes les erreurs sont mesurées en MAD, même pour une cible LOG."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    assert y.shape == p.shape and np.isfinite(p).all() and np.isfinite(y).all()
    error = np.abs(y-p)
    relative = error / np.maximum(np.abs(y), 1)
    return dict(MAE=float(error.mean()), RMSE=float(np.sqrt(np.mean((y-p)**2))),
                R2=float(r2_score(y,p)) if len(y)>1 else None, MedianAE=float(np.median(error)),
                MdAPE=float(np.median(relative)*100),
                **{f'Within_{v}': float(np.mean(relative <= v/100)*100) for v in [10,20,30]})


def evaluate_oof_predictions(y, p, folds):
    """Score OOF global et dispersion sur tous les folds."""
    result = regression_metrics(y, p)
    fold_metrics = pd.DataFrame([regression_metrics(np.asarray(y)[va], p[va]) for _, va in folds])
    for c in ['MAE', 'RMSE', 'R2']:
        result['CV_' + c] = float(fold_metrics[c].mean())
        result['CV_' + c + '_std'] = float(fold_metrics[c].std(ddof=0))
    return result, fold_metrics


def calculate_segment_metrics(frame, predictions, min_n=30):
    """Analyse OOF : géographie, surfaces, prix, rareté et biais signé."""
    x = build_safe_features(frame)
    x['price_band'] = pd.cut(frame[TARGET], [0,750000,1500000,3000000,5000000,np.inf]).astype(str)
    x['surface_band'] = pd.cut(x.surface_m2, [0,50,100,200,500,np.inf]).astype(str)
    x['rare_location'] = x.city.map(x.city.value_counts()).lt(100)
    rows = []
    for c in ['city','region','neighborhood','property_type','price_band','surface_band','rare_location']:
        for label, idx in x.groupby(c, dropna=False).groups.items():
            positions = frame.index.get_indexer(idx)
            if len(idx) >= min_n:
                y, p = frame.loc[idx,TARGET].to_numpy(), predictions[positions]
                rows.append(dict(segment=c, value=str(label), n=len(idx), bias_mad=float(np.mean(p-y)),
                                 **regression_metrics(y,p)))
    return pd.DataFrame(rows)


def grouped_data(train, test):
    """Composantes connexes d'identifiants et signatures non supervisées.

    Le holdout intervient uniquement par ses identifiants et ses caractéristiques,
    jamais par sa cible. Les groupes qui le touchent sont exclus du train.
    """
    both = pd.concat([train, test], ignore_index=True)
    parent = np.arange(len(both))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    safe = build_safe_features(both)
    keys = []
    for c in ['listing_id','duplicate_group_id','canonical_url_repaired','url']:
        keys.append((c, both[c].fillna('').astype(str)))
    native = both.source.fillna('') + '|' + both.source_listing_id.fillna('').astype(str)
    keys.append(('native', native.where(both.source_listing_id.notna(), '')))
    signature = safe[['city','neighborhood','property_type']].copy()
    signature['surface_bin'] = (safe.surface_m2/5).round()
    signature['bedrooms'], signature['bathrooms'] = safe.bedrooms, safe.bathrooms
    # Signature prudente : regroupe aussi certaines annonces distinctes similaires.
    keys.append(('near', signature.fillna('unknown').astype(str).agg('|'.join,axis=1)))
    for kind, values in keys:
        seen = {}
        for i, value in enumerate(values):
            if value and value != 'unknown':
                if value in seen:
                    a,b = root(i),root(seen[value])
                    parent[max(a,b)] = min(a,b)
                else:
                    seen[value] = i
    both['split_group'] = [f'g{root(i)}' for i in range(len(both))]
    test_groups = set(both.iloc[len(train):].split_group)
    real = both.iloc[:len(train)].copy()
    real = real[~real.split_group.isin(test_groups)].reset_index(drop=True)
    held = both.iloc[len(train):].reset_index(drop=True)
    assert not set(real.split_group) & set(held.split_group)
    return real, held


def audit_dataset(train, augmented, output):
    """Audit du train ; les distributions holdout attendent le gel du modèle."""
    safe = build_safe_features(train)
    summary = dict(real_rows=len(train), synthetic_rows=len(augmented),
                   exact_duplicates=int(train.duplicated().sum()),
                   invalid_target=int((~np.isfinite(train[TARGET]) | train[TARGET].le(0)).sum()),
                   rounded_100k_pct=float(train[TARGET].mod(100000).eq(0).mean()*100),
                   missing_percent=safe.isna().mean().mul(100).to_dict(),
                   unknown_percent={c:float(safe[c].eq('unknown').mean()*100) for c in CATEGORICAL},
                   coordinates_missing={c:float(train[c].isna().mean()) for c in ['latitude','longitude']},
                   augmentation_status='EXCLUE : générateur et filiation parentale non disponibles',
                   text_status='NON DEPLOYABLE : aucun texte dans le formulaire')
    for c in ['city','region','neighborhood','property_type']:
        safe[c].value_counts().to_csv(output / f'audit_{c}.csv')
    train[NUMERIC+[TARGET]].describe(percentiles=[.01,.5,.95,.99]).to_csv(output/'audit_numeric.csv')
    add_text_features(train).describe().to_csv(output/'audit_text.csv')
    (output/'audit.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    pd.DataFrame([{'scenario':'réel seul','status':'évalué'},
                  {'scenario':'réel + augmentation','status':summary['augmentation_status']},
                  {'scenario':'réel + augmentation poids 0.25','status':summary['augmentation_status']}]).to_csv(output/'augmentation_scenarios.csv',index=False)
    return summary


def make_model(spec, iterations, seed=42):
    """CPU déterministe ; limites de threads explicites."""
    family = spec['family']
    params = dict(spec.get('params', {}))
    if family == 'cat':
        from catboost import CatBoostRegressor
        defaults = dict(iterations=iterations, depth=6, learning_rate=.05, loss_function=spec.get('loss','RMSE'),
                        l2_leaf_reg=5, random_seed=seed, thread_count=4, verbose=False, allow_writing_files=False)
        return CatBoostRegressor(**(defaults | params))
    if family == 'lgb':
        from lightgbm import LGBMRegressor
        return LGBMRegressor(**(dict(n_estimators=iterations, learning_rate=.04,num_leaves=31,
                                   reg_lambda=5,verbosity=-1,n_jobs=4,random_state=seed,
                                   deterministic=True,force_col_wise=True) | params))
    if family == 'xgb':
        from xgboost import XGBRegressor
        return XGBRegressor(**(dict(n_estimators=iterations,learning_rate=.04,max_depth=5,
                                   reg_lambda=5,n_jobs=4,random_state=seed,tree_method='hist') | params))
    if family == 'hist':
        return HistGradientBoostingRegressor(**(dict(max_iter=iterations,learning_rate=.05,
                  max_leaf_nodes=31,l2_regularization=5,early_stopping=False,random_state=seed,
                  loss=spec.get('loss','squared_error')) | params))
    cls = ExtraTreesRegressor if family == 'extra' else RandomForestRegressor
    return cls(**(dict(n_estimators=min(iterations,250),min_samples_leaf=3,max_features=.8,
                       n_jobs=4,random_state=seed) | params))


class FittedModel:
    """Objet sérialisable incluant transformations et éventuel offset géographique."""
    def __init__(self, spec, preprocessor, model, geography=None, fallback=0):
        self.spec,self.preprocessor,self.model = spec,preprocessor,model
        self.geography,self.fallback = geography,fallback
        self.city_models = {}

    def offset(self, frame):
        x = build_safe_features(frame)
        if self.spec.get('strategy') == 'multiplicative':
            return np.log1p(x.surface_m2.fillna(100)).to_numpy()
        if self.geography is not None:
            key = x.city + '|' + x.neighborhood
            return key.map(self.geography).fillna(self.fallback).to_numpy()
        return np.zeros(len(frame))

    def predict(self, frame):
        pred = self.model.predict(self.preprocessor.transform(frame)) + self.offset(frame)
        if self.spec['target'] == 'LOG':
            pred = np.expm1(pred)
        if self.city_models:
            cities = build_safe_features(frame).city
            for city,model in self.city_models.items():
                mask = cities.eq(city).to_numpy()
                if mask.any():
                    pred[mask] = model.predict(frame.iloc[np.flatnonzero(mask)])
        assert np.isfinite(pred).all(), 'Prédictions non finies'
        return np.maximum(pred,0)


def geographic_map(frame):
    x = build_safe_features(frame)
    values = pd.DataFrame({'key':x.city+'|'+x.neighborhood,'y':np.log1p(frame[TARGET])})
    fallback = float(values.y.median())
    stats = values.groupby('key').y.agg(['mean','count'])
    mapping = ((stats['mean']*stats['count']+20*fallback)/(stats['count']+20)).to_dict()
    return mapping,fallback


def fit_model(frame, spec, iterations, early_frame=None):
    """Fit local au fold ; offsets supervisés de train calculés en cross-fitting."""
    if spec.get('strategy')=='hierarchical':
        return fit_hierarchical(frame,spec,iterations)
    if spec['family']=='ensemble':
        return fit_ensemble(frame,spec,iterations)
    prep = SafePreprocessor(spec.get('advanced',True),spec.get('square',False),spec['family']=='cat').fit(frame)
    model = make_model(spec, iterations, spec.get('seed',42))
    fitted = FittedModel(spec,prep,model)
    y = frame[TARGET].to_numpy(float,copy=True)
    if spec['target']=='LOG':
        y = np.log1p(y)
    if spec.get('strategy') == 'residual':
        offset = np.empty(len(frame))
        for tr,va in create_group_cv(frame,3):
            mapping,fallback = geographic_map(frame.iloc[tr])
            temp = FittedModel(spec,prep,model,mapping,fallback)
            offset[va] = temp.offset(frame.iloc[va])
        fitted.geography,fitted.fallback = geographic_map(frame)
        y -= offset
    else:
        y -= fitted.offset(frame)
    x = prep.transform(frame)
    kwargs = {}
    if spec['family']=='cat':
        kwargs['cat_features'] = prep.cats
    if early_frame is not None and spec['family'] in ['cat','lgb','xgb']:
        ey = early_frame[TARGET].to_numpy(float,copy=True)
        if spec['target']=='LOG':
            ey = np.log1p(ey)
        ey -= fitted.offset(early_frame)
        kwargs['eval_set'] = [(prep.transform(early_frame),ey)]
        if spec['family']=='cat':
            kwargs['early_stopping_rounds'] = 60
        elif spec['family']=='lgb':
            from lightgbm import early_stopping
            kwargs['callbacks'] = [early_stopping(60,verbose=False)]
        else:
            model.set_params(early_stopping_rounds=60)
            kwargs['verbose'] = False
    model.fit(x,y,**kwargs)
    return fitted


def run_candidate(frame,spec,folds,config):
    """Early stopping sur sous-split interne, jamais sur le fold OOF externe."""
    start = time.perf_counter()
    pred, counts = np.full(len(frame),np.nan), []
    for fold,(tr,va) in enumerate(folds):
        train = frame.iloc[tr].reset_index(drop=True)
        iterations = config['iterations']
        if spec['family'] in ['cat','lgb','xgb'] and spec.get('strategy')!='hierarchical':
            split = GroupShuffleSplit(n_splits=1,test_size=.15,random_state=42)
            a,b = next(split.split(train,groups=train.split_group))
            probe = fit_model(train.iloc[a],spec,iterations,train.iloc[b])
            if spec['family']=='cat':
                iterations = max(30,probe.model.get_best_iteration()+1)
            elif spec['family']=='lgb':
                iterations = max(30,probe.model.best_iteration_)
            else:
                iterations = max(30,probe.model.best_iteration+1)
        model = fit_model(train,spec,iterations)
        pred[va] = model.predict(frame.iloc[va])
        counts.append(iterations)
    metrics, fold_metrics = evaluate_oof_predictions(frame[TARGET],pred,folds)
    return dict(spec=spec,predictions=pred,metrics=metrics,fold_metrics=fold_metrics,
                iterations=counts,duration=time.perf_counter()-start)


def tune_model(frame,base,folds,config,output):
    """Optuna reprenable ; chaque essai utilise les cinq folds réels."""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    fingerprint = hashlib.sha256(pd.util.hash_pandas_object(frame,index=True).values.tobytes()).hexdigest()[:12]
    study = optuna.create_study(direction='minimize',study_name='mae_'+fingerprint,
              storage='sqlite:///'+(output/'optuna.sqlite3').as_posix(),load_if_exists=True,
              sampler=optuna.samplers.TPESampler(seed=42))
    results = []
    def objective(trial):
        spec = dict(base)
        family = spec['family']
        if family=='cat':
            params = dict(depth=trial.suggest_int('depth',4,8),
                          learning_rate=trial.suggest_float('learning_rate',.025,.09,log=True),
                          l2_leaf_reg=trial.suggest_float('l2_leaf_reg',2,30,log=True),
                          random_strength=trial.suggest_float('random_strength',.1,3),
                          bootstrap_type='Bernoulli',subsample=trial.suggest_float('subsample',.7,1),
                          rsm=trial.suggest_float('rsm',.7,1))
        else:
            params = dict(learning_rate=trial.suggest_float('learning_rate',.025,.09,log=True),
                          reg_alpha=trial.suggest_float('reg_alpha',.001,10,log=True),
                          reg_lambda=trial.suggest_float('reg_lambda',1,30,log=True),
                          subsample=trial.suggest_float('subsample',.7,1),
                          colsample_bytree=trial.suggest_float('colsample_bytree',.7,1))
            if family=='lgb':
                params.update(num_leaves=trial.suggest_int('num_leaves',15,63),subsample_freq=1,
                              min_child_samples=trial.suggest_int('min_child_samples',15,60))
            else:
                params.update(max_depth=trial.suggest_int('max_depth',3,7),
                              min_child_weight=trial.suggest_float('min_child_weight',1,20))
        spec['params'],spec['name'] = params,f'tuned_{trial.number}'
        result = run_candidate(frame,spec,folds,config)
        results.append(result)
        trial.set_user_attr('spec',spec)
        for k in ['MAE','RMSE','R2']:
            trial.set_user_attr(k,result['metrics'][k])
        trial.set_user_attr('duration_s',result['duration'])
        print('Trial',trial.number,result['metrics'],flush=True)
        return result['metrics']['MAE']
    remaining = max(0,config['optuna_trials']-len(study.trials))
    try:
        study.optimize(objective,n_trials=remaining)
    finally:
        study.trials_dataframe().to_csv(output/'optuna_trials.csv',index=False)
    if not results or study.best_trial.user_attrs['spec'] not in [r['spec'] for r in results]:
        results.append(run_candidate(frame,study.best_trial.user_attrs['spec'],folds,config))
    return results


def optimize_blend_weights(y,predictions):
    """Poids convexes ; utilisés uniquement sur les OOF autorisées."""
    n = predictions.shape[1]
    result = minimize(lambda w:np.mean(np.abs(y-predictions@w)),np.ones(n)/n,
                      method='SLSQP',bounds=[(0,1)]*n,
                      constraints={'type':'eq','fun':lambda w:w.sum()-1},
                      options={'maxiter':500,'ftol':1e-8})
    return result.x/result.x.sum() if result.success else np.ones(n)/n


def fit_hierarchical(frame,spec,iterations):
    """Choix des experts par CV interne ; amélioration locale minimale de 2 %."""
    base = spec | {'strategy':None}
    global_model = fit_model(frame,base,iterations)
    cities = build_safe_features(frame).city
    eligible = cities.value_counts().loc[lambda s:s>=300].index
    folds = create_group_cv(frame,3)
    global_oof = np.empty(len(frame))
    local_oof = np.full(len(frame),np.nan)
    for tr,va in folds:
        global_oof[va] = fit_model(frame.iloc[tr],base,iterations).predict(frame.iloc[va])
        for city in eligible:
            a = tr[cities.iloc[tr].eq(city).to_numpy()]
            b = va[cities.iloc[va].eq(city).to_numpy()]
            if len(a)>=150 and len(b):
                local_oof[b] = fit_model(frame.iloc[a],base,iterations).predict(frame.iloc[b])
    for city in eligible:
        mask = cities.eq(city).to_numpy()
        if np.isfinite(local_oof[mask]).all():
            y = frame[TARGET].to_numpy()[mask]
            if np.abs(y-local_oof[mask]).mean() < .98*np.abs(y-global_oof[mask]).mean():
                global_model.city_models[city] = fit_model(frame.iloc[np.flatnonzero(mask)],base,iterations)
    return global_model


class EnsembleModel:
    """Méta-modèle entraîné exclusivement sur OOF internes au train autorisé."""
    def __init__(self,models,weights,meta=None):
        self.models,self.weights,self.meta = models,weights,meta
        self.preprocessor = models[0].preprocessor
    def predict(self,frame):
        matrix = np.column_stack([m.predict(frame) for m in self.models])
        p = matrix@self.weights if self.meta is None else self.meta.predict(matrix/1e6)*1e6
        assert np.isfinite(p).all()
        return np.maximum(p,0)


def fit_ensemble(frame,spec,iterations):
    """CV imbriquée complète : aucun label OOF externe n'influence les poids."""
    bases = [dict(name='blend_lgb_raw',family='lgb',target='RAW'),
             dict(name='blend_lgb_log',family='lgb',target='LOG'),
             dict(name='blend_xgb_log',family='xgb',target='LOG')]
    models = []
    if spec['method']=='mean':
        return EnsembleModel([fit_model(frame,s,iterations) for s in bases],np.ones(3)/3)
    inner = create_group_cv(frame,3)
    matrix = np.empty((len(frame),3))
    for col,base in enumerate(bases):
        for tr,va in inner:
            model = fit_model(frame.iloc[tr],base,iterations)
            matrix[va,col] = model.predict(frame.iloc[va])
        models.append(fit_model(frame,base,iterations))
    weights = optimize_blend_weights(frame[TARGET].to_numpy(),matrix)
    meta = None
    if spec['method']=='ridge':
        from sklearn.linear_model import Ridge
        meta = Ridge(alpha=10).fit(matrix/1e6,frame[TARGET].to_numpy()/1e6)
    return EnsembleModel(models,weights,meta)


def validate_final_pipeline(pipeline,frame):
    """Assertions d'inférence, catégories inconnues et sérialisation."""
    p = pipeline.predict(frame.head(10))
    np.testing.assert_array_equal(p,pipeline.predict(frame.head(10)))
    unknown = pd.DataFrame([{'city':'ville jamais vue','surface_m2':85}])
    assert np.isfinite(pipeline.predict(unknown)).all()
    assert len(p)==min(10,len(frame))


def train_final_model(frame,result):
    """Nombre d'arbres figé par médiane des sous-validations internes."""
    return fit_model(frame,result['spec'],int(np.median(result['iterations'])))


def predict_property_price(property_data:dict)->dict:
    """Accepte les noms du formulaire ; intervalle split-conformal à 90 %."""
    artifact = joblib.load(find_root()/'models/advanced_optimization/pipeline.joblib')
    aliases = {'ville':'city','quartier':'neighborhood','type_bien':'property_type',
               'surface':'surface_m2','chambres':'bedrooms','salles_bain':'bathrooms'}
    data = {aliases.get(k,k):v for k,v in property_data.items()}
    p = float(artifact['pipeline'].predict(pd.DataFrame([data]))[0])
    q = artifact['conformal_radius']
    return dict(predicted_price_mad=p,lower_bound_mad=max(0,p-q),upper_bound_mad=p+q,
                model_version=artifact['model_version'])


def run_experiments(config=None):
    """Audit, sélection CV, calibration indépendante, unique évaluation finale."""
    config = CONFIG | (config or {})
    assert config['random_state']==42
    root = find_root()
    output = root/'reports/advanced_optimization'
    output.mkdir(parents=True,exist_ok=True)
    destination = root/'models/advanced_optimization'
    destination.mkdir(parents=True,exist_ok=True)
    # Refus de réévaluer un holdout déjà consulté dans cette expérience.
    if (output/'final_results.json').exists():
        print('Résultats figés rechargés ; aucune nouvelle évaluation du holdout.')
        return json.loads((output/'final_results.json').read_text(encoding='utf-8'))
    train_path = root/'data/processed/maisondelux_train_augmented_safe_v2(1).csv'
    test_path = root/'data/processed/maisondelux_test_real_holdout_v2.csv'
    train = pd.read_csv(train_path,low_memory=False)
    # La cible du holdout n'est pas chargée avant le gel du modèle.
    test_features = pd.read_csv(test_path,low_memory=False,usecols=lambda c:c!=TARGET)
    augmented = train[train.batch_id.eq('augmentation_v2')].copy()
    train = train[~train.batch_id.eq('augmentation_v2')].copy()
    raw_rows = len(train)
    train,test_features = grouped_data(train,test_features)
    assert np.isfinite(train[TARGET]).all() and train[TARGET].gt(0).all()
    audit = audit_dataset(train,augmented,output)
    audit['removed_train_overlap'] = raw_rows-len(train)
    splitter = GroupShuffleSplit(n_splits=1,test_size=config['calibration_fraction'],random_state=42)
    dev_idx,cal_idx = next(splitter.split(train,groups=train.split_group))
    dev,cal = train.iloc[dev_idx].reset_index(drop=True),train.iloc[cal_idx].reset_index(drop=True)
    assert not set(dev.split_group)&set(cal.split_group)
    folds = create_group_cv(dev,config['n_splits'])
    folds2 = create_group_cv(dev,config['n_splits'])
    assert all(np.array_equal(a[1],b[1]) for a,b in zip(folds,folds2))
    fold_ids = np.empty(len(dev),int)
    for k,(_,va) in enumerate(folds):
        fold_ids[va] = k
    pd.DataFrame({'listing_id':dev.listing_id,'split_group':dev.split_group,'fold':fold_ids}).to_csv(output/'fold_assignments.csv',index=False)
    dev.assign(fold=fold_ids).groupby('fold')[TARGET].describe().to_csv(output/'fold_target_distributions.csv')
    print('Train sûr / développement / calibration / holdout :',len(train),len(dev),len(cal),len(test_features),flush=True)
    specs = [dict(name='baseline_cat_log',family='cat',target='LOG',advanced=False)]
    for target in ['RAW','LOG']:
        for loss in ['RMSE','MAE']:
            specs.append(dict(name=f'cat_{target}_{loss}',family='cat',target=target,loss=loss))
        for family in ['lgb','xgb','hist','extra','forest']:
            specs.append(dict(name=f'{family}_{target}',family=family,target=target))
    specs += [dict(name='cat_log_square',family='cat',target='LOG',square=True),
              dict(name='cat_log_huber',family='cat',target='LOG',loss='Huber:delta=0.5'),
              dict(name='cat_log_quantile',family='cat',target='LOG',loss='Quantile:alpha=0.5'),
              dict(name='multiplicative',family='cat',target='LOG',strategy='multiplicative'),
              dict(name='geographic_residual',family='cat',target='LOG',strategy='residual')]
    specs.append(dict(name='hierarchical',family='lgb',target='LOG',strategy='hierarchical'))
    for method in ['mean','weighted','ridge']:
        specs.append(dict(name='ensemble_'+method,family='ensemble',target='RAW',method=method))
    results = []
    cache_tag = hashlib.sha256((json.dumps(config,sort_keys=True)+
                 hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+
                 hashlib.sha256(train_path.read_bytes()).hexdigest()).encode()).hexdigest()[:12]
    cache = output/('cache_'+cache_tag)
    cache.mkdir(exist_ok=True)
    for spec in specs:
        path = cache/(spec['name']+'.joblib')
        print('Candidat',spec['name'],flush=True)
        if path.exists():
            result = joblib.load(path)
        else:
            result = run_candidate(dev,spec,folds,config)
            joblib.dump(result,path)
        results.append(result)
        print(result['metrics'], 'secondes',round(result['duration']),flush=True)
    # Tuning limité au meilleur booster, sur la MAE OOF.
    booster = min((r for r in results if r['spec']['family'] in ['cat','lgb','xgb']),key=lambda r:r['metrics']['MAE'])
    if config['run_optuna']:
        results.extend(tune_model(dev,booster['spec'],folds,config,output))
    results.sort(key=lambda r:(r['metrics']['MAE'],-r['metrics']['R2'],r['metrics']['CV_MAE_std']))
    best_individual = next(r for r in results if r['spec']['family']!='ensemble')
    ensemble_candidates = [r for r in results if r['spec']['family']=='ensemble']
    best_ensemble = min(ensemble_candidates,key=lambda r:r['metrics']['MAE'])
    # Gain >=1 % et amélioration dans au moins 4 folds sur 5.
    stable = (best_ensemble['fold_metrics'].MAE.to_numpy() < best_individual['fold_metrics'].MAE.to_numpy()).sum()>=4
    winner = best_ensemble if stable and best_ensemble['metrics']['MAE'] < .99*best_individual['metrics']['MAE'] else best_individual
    # Seeds supplémentaires après sélection de la configuration uniquement.
    seed_results = []
    for seed in [43,44]:
        spec = winner['spec'] | {'seed':seed,'name':f'seed_{seed}'}
        result = run_candidate(dev,spec,folds,config)
        seed_results.append({'seed':seed,**result['metrics']})
    pd.DataFrame(seed_results).to_csv(output/'seed_stability.csv',index=False)
    rows = []
    for result in results:
        name = result['spec']['name']
        rows.append(dict(name=name,**result['metrics'],duration_s=result['duration'],spec=json.dumps(result['spec'])))
    pd.DataFrame(rows).to_csv(output/'oof_leaderboard.csv',index=False)
    oof = dev[['listing_id','split_group',TARGET]].copy()
    for r in results:
        oof[r['spec']['name']] = r['predictions']
    oof.to_csv(output/'oof_predictions.csv',index=False)
    calculate_segment_metrics(dev,winner['predictions']).to_csv(output/'oof_segments.csv',index=False)
    # Poids et stacking exploratoires. La validation croisée des méta-modèles sur
    # ces mêmes OOF n'est PAS une validation imbriquée complète des modèles de base.
    # Leur score ne peut donc pas autoriser un remplacement du modèle individuel.
    top = results[:3]
    p = np.column_stack([r['predictions'] for r in top])
    y = dev[TARGET].to_numpy()
    weights = optimize_blend_weights(y,p)
    from sklearn.linear_model import Ridge
    stacked = np.empty(len(y))
    for tr,va in folds:
        meta = Ridge(alpha=10).fit(p[tr]/1e6,y[tr]/1e6)
        stacked[va] = np.maximum(meta.predict(p[va]/1e6)*1e6,0)
    blends = []
    for name,pred in [('mean',p.mean(axis=1)),('weighted',p@weights),('ridge_crossfit',stacked)]:
        blends.append(dict(name=name,**regression_metrics(y,pred),
                           status='exploratoire, non éligible sans CV imbriquée complète'))
    pd.DataFrame(blends).to_csv(output/'ensemble_diagnostics.csv',index=False)
    # Gel écrit AVANT calibration et lecture des prix du test.
    selection = dict(spec=winner['spec'],iterations=int(np.median(winner['iterations'])),
                     config=config,augmentation='excluded_unverifiable_provenance',
                     training_rows=len(dev),calibration_rows=len(cal),holdout_rows=len(test_features),
                     oof=winner['metrics'],blend_weights_exploratory=weights.tolist())
    (output/'frozen_selection.json').write_text(json.dumps(selection,indent=2,ensure_ascii=False),encoding='utf-8')
    pipeline = train_final_model(dev,winner)
    validate_final_pipeline(pipeline,dev)
    # Refit reproductible du même modèle : contrôle avant toute cible holdout.
    duplicate = train_final_model(dev,winner)
    np.testing.assert_allclose(pipeline.predict(dev.head(30)),duplicate.predict(dev.head(30)),rtol=1e-10,atol=1e-6)
    calibration_pred = pipeline.predict(cal)
    scores = np.abs(cal[TARGET].to_numpy()-calibration_pred)
    # Une unité = un groupe. Le maximum rend l'intervalle conservateur pour tous
    # les membres du groupe, sous échangeabilité des groupes de calibration/test.
    group_scores = pd.Series(scores).groupby(cal.split_group).max().to_numpy()
    rank = int(np.ceil((len(group_scores)+1)*(1-config['alpha'])))
    if rank > len(group_scores):
        raise ValueError('Nombre de groupes insuffisant pour un intervalle fini.')
    q = float(np.sort(group_scores)[rank-1])
    version = datetime.now(timezone.utc).strftime('advanced-%Y%m%dT%H%M%SZ')
    artifact = dict(pipeline=pipeline,conformal_radius=q,model_version=version)
    joblib.dump(artifact,destination/'pipeline.joblib')
    loaded = joblib.load(destination/'pipeline.joblib')
    np.testing.assert_allclose(loaded['pipeline'].predict(dev.head(10)),pipeline.predict(dev.head(10)))
    # Marqueur exclusif : même après une interruption, aucune deuxième évaluation
    # automatique ne sera lancée. Une exécution terminée recharge ses résultats.
    with (output/'holdout_evaluation_started.lock').open('x',encoding='utf-8') as handle:
        handle.write(version)
    test_y = pd.read_csv(test_path,usecols=[TARGET])[TARGET].to_numpy()
    test_pred = pipeline.predict(test_features)
    final = regression_metrics(test_y,test_pred)
    coverage = float(np.mean(np.abs(test_y-test_pred)<=q))
    pd.DataFrame({'listing_id':test_features.listing_id,'y_true':test_y,'prediction':test_pred,
                  'lower':np.maximum(0,test_pred-q),'upper':test_pred+q}).to_csv(output/'holdout_predictions.csv',index=False)
    comparison = [dict(name='baseline historique déclarée',dataset='ancien holdout',MAE=403757,RMSE=882622,R2=.622),
                  dict(name=best_individual['spec']['name'],dataset='OOF individuel',**best_individual['metrics']),
                  dict(name=best_ensemble['spec']['name'],dataset='OOF ensemble imbriqué',**best_ensemble['metrics']),
                  dict(name='final figé',dataset='holdout réel',**final)]
    pd.DataFrame(comparison).to_csv(output/'final_comparison.csv',index=False)
    versions = {name:importlib.metadata.version(name) for name in ['numpy','pandas','scikit-learn','catboost','lightgbm','xgboost','optuna','joblib']}
    metadata = selection | dict(version=version,versions=versions,holdout=final,
                   best_oof_R2=max(r['metrics']['R2'] for r in results),
                   conformal_radius=q,holdout_coverage=coverage,alpha=config['alpha'],
                   features=pipeline.preprocessor.columns,
                   category_mappings={c:values.tolist() for c,values in zip(pipeline.preprocessor.cats,pipeline.preprocessor.encoder.categories_)},
                   input_schema={'numeric':NUMERIC,'categorical':CATEGORICAL,'missing':'accepté','unknown':'accepté'},
                   source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [train_path,test_path]},audit=audit,
                   limitations=['Holdout déjà consulté dans le notebook historique : nouveau jeu externe nécessaire.',
                                 'Scores OOF utilisés pour sélection : biais de sélection possible.',
                                 'Augmentation non testable sans provenance ; effet inconnu.',
                                 'Texte absent du formulaire ; branche TF-IDF non déployable.',
                                 'Ensembles exploratoires non retenus sans validation imbriquée.',
                                 'Intervalle conforme sous échangeabilité des groupes, sans garantie par ville.'])
    (destination/'metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False),encoding='utf-8')
    (output/'final_results.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False),encoding='utf-8')
    # Audit de distribution post-gel uniquement.
    for c in ['city','region','neighborhood','property_type']:
        pd.concat([build_safe_features(dev)[c].value_counts(normalize=True).rename('train'),
                   build_safe_features(test_features)[c].value_counts(normalize=True).rename('test')],axis=1).fillna(0).to_csv(output/f'postfreeze_shift_{c}.csv')
    print('RÉSULTAT FINAL',final,flush=True)
    return metadata


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials',type=int,default=50)
    parser.add_argument('--iterations',type=int,default=650)
    args = parser.parse_args()
    from ml.src.advanced_optimization import run_experiments as run
    run({'optuna_trials':args.trials,'iterations':args.iterations})
