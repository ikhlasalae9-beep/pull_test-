"""MaisonDeLUX V1 inference. Run from the repository: python -m backend.app."""
import json
import math
import struct
from pathlib import Path
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

try:
    import pandas as pd
except ImportError:
    pd = None

ROOT = Path(__file__).resolve().parents[1]
metadata = json.loads((ROOT / 'models/maisondelux_price_model_v1_metadata.json').read_text(encoding='utf-8'))
locations = json.loads((ROOT / 'models/locations_v1.json').read_text(encoding='utf-8'))
FEATURES = metadata['features']


def _to_f32(val):
    return struct.unpack('f', struct.pack('f', float(val)))[0]


class LightweightModel:
    """Pure-Python inference model with zero ML runtime dependencies (no xgboost, no numpy, no scikit-learn)."""

    def __init__(self, booster_path, prep_config_path):
        with open(prep_config_path, 'r', encoding='utf-8') as f:
            self.cfg = json.load(f)
        with open(booster_path, 'r', encoding='utf-8') as f:
            booster_data = json.load(f)

        trees = booster_data['learner']['gradient_booster']['model']['trees']
        base_score_str = booster_data['learner']['learner_model_param']['base_score'].strip('[]')
        self.base_score = _to_f32(float(base_score_str))

        self.tree_data = [
            (
                t['left_children'],
                t['right_children'],
                t['split_indices'],
                [_to_f32(c) for c in t['split_conditions']],
                t['default_left']
            )
            for t in trees
        ]

        self.frequent_cities_set = set(self.cfg['frequent_cities'])
        self.frequent_neighborhoods_set = set(self.cfg['frequent_neighborhoods'])
        self.num_means = [float(x) for x in self.cfg['num_scaler_mean']]
        self.num_scales = [float(x) for x in self.cfg['num_scaler_scale']]
        self.num_medians = [float(x) for x in self.cfg['num_imputer_medians']]

    @property
    def regressor_(self):
        if not hasattr(self, '_cached_joblib_regressor'):
            import joblib
            orig = joblib.load(ROOT / 'models/maisondelux_price_model_v1.joblib')
            self._cached_joblib_regressor = orig.regressor_
        return self._cached_joblib_regressor

    def transform_row_to_dict(self, row_dict):
        x_d = {}
        for i, col in enumerate(self.cfg['num_features']):
            val = row_dict.get(col)
            if val is None or val == '' or (isinstance(val, (int, float)) and not math.isfinite(val)):
                val = self.num_medians[i]
            else:
                val = float(val)
            scaled = (val - self.num_means[i]) / self.num_scales[i]
            x_d[i] = _to_f32(scaled)

        region = str(row_dict.get('region', '')).strip()
        if region in self.cfg['cat_offsets']['region']:
            x_d[self.cfg['cat_offsets']['region'][region]] = 1.0

        city = str(row_dict.get('city', '')).strip()
        city_token = city if city in self.frequent_cities_set else self.cfg['rare_label']
        if city_token in self.cfg['cat_offsets']['city']:
            x_d[self.cfg['cat_offsets']['city'][city_token]] = 1.0

        neigh = row_dict.get('neighborhood')
        if neigh is None or neigh == '' or neigh == self.cfg['missing_label'] or (isinstance(neigh, float) and math.isnan(neigh)):
            neigh_token = self.cfg['missing_label']
        else:
            s_neigh = str(neigh).strip()
            neigh_token = s_neigh if s_neigh in self.frequent_neighborhoods_set else self.cfg['rare_label']
        if neigh_token in self.cfg['cat_offsets']['neighborhood']:
            x_d[self.cfg['cat_offsets']['neighborhood'][neigh_token]] = 1.0

        pt = str(row_dict.get('property_type', '')).strip()
        if pt in self.cfg['cat_offsets']['property_type']:
            x_d[self.cfg['cat_offsets']['property_type'][pt]] = 1.0

        for feat in ['parking', 'balcony', 'sea_view', 'furnished_status']:
            val = row_dict.get(feat)
            val = str(val).strip() if val is not None and val != '' and (not isinstance(val, float) or not math.isnan(val)) else 'unknown'
            if val in self.cfg['cat_offsets'][feat]:
                x_d[self.cfg['cat_offsets'][feat][val]] = 1.0

        return x_d

    def _predict_single(self, x_d):
        total = self.base_score
        for lefts, rights, splits, conds, default_lefts in self.tree_data:
            node = 0
            while lefts[node] != -1:
                feat = splits[node]
                val = x_d.get(feat, 0.0)
                if val == 0.0 or math.isnan(val):
                    node = lefts[node] if default_lefts[node] == 1 else rights[node]
                else:
                    node = lefts[node] if val < conds[node] else rights[node]
            total = _to_f32(total + conds[node])
        return math.expm1(total)

    def predict(self, X):
        if isinstance(X, dict):
            return [self._predict_single(self.transform_row_to_dict(X))]
        elif hasattr(X, 'to_dict') and callable(X.to_dict):
            records = X.to_dict(orient='records')
            return [self._predict_single(self.transform_row_to_dict(r)) for r in records]
        elif isinstance(X, (list, tuple)):
            if len(X) > 0 and isinstance(X[0], dict):
                return [self._predict_single(self.transform_row_to_dict(r)) for r in X]
            elif len(X) > 0 and hasattr(X[0], '__getitem__'):
                res = []
                for row in X:
                    x_d = {i: _to_f32(v) for i, v in enumerate(row) if v != 0.0}
                    res.append(self._predict_single(x_d))
                return res
        elif hasattr(X, '__getitem__') and hasattr(X, 'shape'):
            if len(X.shape) == 1:
                x_d = {i: _to_f32(v) for i, v in enumerate(X) if v != 0.0}
                return [self._predict_single(x_d)]
            else:
                res = []
                for row in X:
                    x_d = {i: _to_f32(v) for i, v in enumerate(row) if v != 0.0}
                    res.append(self._predict_single(x_d))
                return res
        return [self._predict_single(self.transform_row_to_dict(dict(X)))]


model = LightweightModel(
    ROOT / 'models/maisondelux_price_model_v1.json',
    ROOT / 'models/maisondelux_preprocessing_v1.json'
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Un objet JSON est requis.')
    if set(data) - set(FEATURES):
        raise ValueError('Le formulaire contient des champs non pris en charge.')
    row = {}
    for key in FEATURES[:3]:
        value = data.get(key)
        if key != 'surface_m2' and (value is None or value == ''):
            row[key] = math.nan
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'{key} doit être numérique.')
        if not math.isfinite(value) or (value <= 0 if key == 'surface_m2' else value < 0):
            raise ValueError(f'{key} doit être fini et positif.')
        if key != 'surface_m2' and value != int(value):
            raise ValueError(f'{key} doit être entier.')
        row[key] = value
    for key in FEATURES[3:]:
        value = data.get(key)
        if value is not None and not isinstance(value, str):
            raise ValueError(f'{key} doit être du texte.')
        value = value.strip() if value else ''
        if len(value) > 200:
            raise ValueError(f'{key} est trop long.')
        if key in ('city', 'region', 'property_type') and not value:
            raise ValueError(f'{key} est requis.')
        row[key] = value or ('unknown' if key in FEATURES[7:] else math.nan)
    if pd is not None:
        return pd.DataFrame([row], columns=FEATURES)
    return row


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify(error=error.description), error.code


@app.post('/api/estimate')
@app.post('/estimate')
def estimate():
    try:
        frame = validate(request.get_json())
    except ValueError as error:
        return jsonify(error=str(error)), 400
    try:
        price = float(model.predict(frame)[0])
        if not math.isfinite(price) or price <= 0:
            raise ValueError('Invalid model output')
    except Exception:
        app.logger.exception('Inference failed')
        return jsonify(error="Le service d'estimation est momentanément indisponible."), 503
    return jsonify(estimated_price_mad=round(price), currency='MAD', model_version='v1')


@app.get('/api/villes')
@app.get('/villes')
def cities():
    return jsonify(villes=sorted(locations))


@app.get('/api/metrics')
@app.get('/metrics')
def metrics():
    return jsonify(**metadata, currency='MAD', model_version='v1')


@app.get('/')
@app.get('/api')
@app.get('/api/')
def health():
    return jsonify(status='ok', model_version='v1')


if __name__ == '__main__':
    app.run(port=5000, debug=False)
