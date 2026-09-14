"""Tests for the production Vercel Python API entrypoint and ML inference."""
import math
import pytest
from pathlib import Path
from api.index import app

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def client():
    return app.test_client()

def test_model_file_loading():
    """Verify that model artifacts and reference files exist and are readable."""
    assert (ROOT / 'models/maisondelux_price_model_v1.joblib').is_file()
    assert (ROOT / 'models/maisondelux_price_model_v1_metadata.json').is_file()
    assert (ROOT / 'models/locations_v1.json').is_file()
    assert (ROOT / 'models/neighborhoods_v1.json').is_file()

def test_health_endpoint(client):
    """Verify health check on root and /api."""
    res1 = client.get('/')
    assert res1.status_code == 200
    assert res1.get_json()['status'] == 'ok'
    assert res1.get_json()['model_version'] == 'v1'

    res2 = client.get('/api')
    assert res2.status_code == 200
    assert res2.get_json()['status'] == 'ok'

def test_valid_apartment_estimate(client):
    """Verify valid apartment estimation returns proper structure."""
    payload = {
        'city': 'Casablanca',
        'region': 'Casablanca-Settat',
        'neighborhood': 'MaÂrif',
        'property_type': 'appartement',
        'surface_m2': 100,
        'bedrooms': 2,
        'bathrooms': 1,
        'parking': 'unknown',
        'balcony': 'unknown',
        'sea_view': 'unknown',
        'furnished_status': 'unknown'
    }
    res = client.post('/api/estimate', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert 'estimated_price_mad' in data
    assert math.isfinite(data[
        'estimated_price_mad']) and data[
        'estimated_price_mad'] > 0
    assert data['currency'] == 'MAD'
    assert data['model_version'] == 'v1'

def test_invalid_request(client):
    """Verify invalid payloads return 400 with descriptive error."""
    res = client.post('/api/estimate', json={'surface_m2': -10})
    assert res.status_code == 400
    assert 'error' in res.get_json()

    res = client.post('/api/estimate', json={'surface_m2': 'cent'})
    assert res.status_code == 400

    res = client.post('/api/estimate', data='not json', content_type='application/json')
    assert res.status_code == 400

def test_same_origin_api_request(client):
    """Verify supporting endpoints used by same-origin frontend client."""
    villes_res = client.get('/api/villes')
    assert villes_res.status_code == 200
    assert 'villes' in villes_res.get_json()
    assert 'Casablanca' in villes_res.get_json()['villes']

    metrics_res = client.get('/api/metrics')
    assert metrics_res.status_code == 200
    assert metrics_res.get_json()['model_name'] == 'XGBoost'

def test_known_sanity_prediction(client):
    """Verify known sanity prediction for Casablanca / Maârif 90m2 apartment."""
    payload = {
        'city': 'Casablanca',
        'region': 'Casablanca-Settat',
        'neighborhood': 'Maârif',
        'property_type': 'appartement',
        'surface_m2': 90,
        'bedrooms': 2,
        'bathrooms': 1,
        'parking': 'unknown',
        'balcony': 'unknown',
        'sea_view': 'unknown',
        'furnished_status': 'unknown'
    }
    res = client.post('/api/estimate', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['currency'] == 'MAD'
    assert data['model_version'] == 'v1'
    # Expected: approx 1,288,988 MAD
    assert abs(data['estimated_price_mad'] - 1288988) <= 1000

def test_lightweight_joblib_parity():
    """Verify that LightweightModel exactly reproduces the original joblib pipeline."""
    import joblib
    import pandas as pd
    import ml.src.inference  # noqa: F401
    from backend.app import model, validate

    orig_model = joblib.load(ROOT / 'models/maisondelux_price_model_v1.joblib')

    # 1. Sanity case parity
    sanity_dict = {
        'city': 'Casablanca', 'region': 'Casablanca-Settat', 'neighborhood': 'Maârif',
        'property_type': 'appartement', 'surface_m2': 90, 'bedrooms': 2, 'bathrooms': 1,
        'parking': 'unknown', 'balcony': 'unknown', 'sea_view': 'unknown', 'furnished_status': 'unknown'
    }
    pred_orig_sanity = float(orig_model.predict(validate(sanity_dict))[0])
    pred_light_sanity = float(model.predict(sanity_dict)[0])
    assert abs(pred_orig_sanity - pred_light_sanity) < 0.01

    # 2. 100+ dataset rows parity
    csv_path = ROOT / 'data/processed/maisondelux_model_ready_v1.csv'
    if csv_path.is_file():
        df_sample = pd.read_csv(csv_path).sample(100, random_state=42)
        for _, row in df_sample.iterrows():
            row_dict = {
                'city': str(row['city']),
                'region': str(row['region']),
                'neighborhood': str(row['neighborhood_clean']) if pd.notna(row['neighborhood_clean']) else None,
                'property_type': str(row['property_type_repaired']),
                'surface_m2': float(row['surface_m2']),
                'bedrooms': float(row['bedrooms']) if pd.notna(row['bedrooms']) else None,
                'bathrooms': float(row['bathrooms']) if pd.notna(row['bathrooms']) else None,
                'parking': str(row['parking']) if pd.notna(row['parking']) else 'unknown',
                'balcony': str(row['balcony']) if pd.notna(row['balcony']) else 'unknown',
                'sea_view': str(row['sea_view']) if pd.notna(row['sea_view']) else 'unknown',
                'furnished_status': str(row['furnished_status']) if pd.notna(row['furnished_status']) else 'unknown',
            }
            pred_orig = float(orig_model.predict(validate(row_dict))[0])
            pred_light = float(model.predict(row_dict)[0])
            assert abs(pred_orig - pred_light) < 1.0


def test_requirements_file_is_minimal():
    """Verify requirements.txt contains strictly minimal web runtime without ML heavyweights."""
    reqs_text = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
    lines = [l.strip() for l in reqs_text.splitlines() if l.strip() and not l.startswith('#')]
    assert 'flask>=3.1,<4' in lines
    assert 'werkzeug>=3.1,<4' in lines
    assert len(lines) == 2
    for forbidden in ['numpy', 'xgboost', 'scipy', 'scikit-learn', 'pandas', 'joblib']:
        assert not any(forbidden in l for l in lines)

