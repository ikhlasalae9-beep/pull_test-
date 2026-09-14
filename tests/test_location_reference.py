import json
from backend.app import ROOT, model, validate
from ml.src.build_location_reference import build_reference

def test_location_reference_matches_final_repaired_dataset():
    assert json.loads((ROOT/'models/neighborhoods_v1.json').read_text(encoding='utf-8')) == build_reference()

def test_other_neighborhood_uses_fitted_rare_behavior():
    from backend.app import app
    row = dict(surface_m2=120, bedrooms=3, bathrooms=2, city='Casablanca', region='Casablanca-Settat', property_type='appartement')
    rare = model.regressor_.named_steps['preprocessor'].named_steps['rare']
    other = rare.transform(validate(dict(row, neighborhood='Rare')))
    unseen = rare.transform(validate(dict(row, neighborhood='Unseen test neighborhood')))
    assert other.neighborhood.iloc[0] == unseen.neighborhood.iloc[0] == rare.rare_label
    with app.test_client() as client:
        response = client.post('/api/estimate', json=dict(row, neighborhood='Rare'))
        assert response.status_code == 200
        assert response.json['estimated_price_mad'] > 0
