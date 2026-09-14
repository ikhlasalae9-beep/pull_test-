"""Regression checks for the saved V1 pipeline and HTTP contract."""
import json
import math
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, r2_score
from backend.app import app, model, metadata, ROOT, FEATURES

@pytest.fixture
def client():
    return app.test_client()

def payload(city='Casablanca', region='Casablanca-Settat'):
    return dict(surface_m2=120, bedrooms=3, bathrooms=2, city=city, region=region,
                neighborhood='Maârif', property_type='appartement')

@pytest.mark.parametrize('city,region', [('Casablanca','Casablanca-Settat'), ('Rabat','Rabat-Salé-Kénitra'), ('Marrakech','Marrakech-Safi'), ('Tanger','Tanger-Tétouan-Al Hoceïma')])
def test_real_predictions(client,city,region):
    response=client.post('/api/estimate',json=payload(city,region))
    assert response.status_code == 200
    data=response.get_json()
    assert math.isfinite(data['estimated_price_mad']) and data['estimated_price_mad']>0
    assert data['currency']=='MAD'

def test_unknown_and_missing(client):
    p=payload(); p.update(neighborhood='Previously unseen neighborhood', bedrooms=None, bathrooms=None)
    assert client.post('/api/estimate',json=p).status_code==200
    p.update(parking=None,balcony=None,sea_view=None,furnished_status=None)
    assert client.post('/api/estimate',json=p).status_code==200

@pytest.mark.parametrize('value',[0,-1,'abc',None,True,float('inf'),float('nan')])
def test_invalid_surface(client,value):
    p=payload(); p['surface_m2']=value
    assert client.post('/api/estimate',json=p).status_code==400

@pytest.mark.parametrize('body',[[],None,{'price_per_m2':15000}])
def test_invalid_body(client,body):
    assert client.post('/api/estimate',data=json.dumps(body),content_type='application/json').status_code==400

def test_model_failure(client,monkeypatch):
    monkeypatch.setattr(model,'predict',lambda _: [float('nan')])
    assert client.post('/api/estimate',json=payload()).status_code==503

def test_artifact_reproduces_notebook_test_metrics():
    d=pd.read_csv(ROOT/'data/processed/maisondelux_model_ready_v1.csv')
    d['neighborhood']=d.neighborhood_clean
    d['property_type']=d.property_type_repaired
    for col in FEATURES[3:]:
        d[col]=d[col].astype('string').str.strip()
    groups=np.where(d.duplicate_group_id.notna(),'dup_'+d.duplicate_group_id.astype('string'),'listing_'+d.listing_id.astype('string'))
    tr,te=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=18).split(d,groups=groups))
    assert len(tr)==10852 and len(te)==2685
    assert not set(groups[tr]) & set(groups[te])
    pred=model.predict(d.iloc[te][FEATURES])
    assert mean_absolute_error(d.iloc[te].price_mad,pred)==pytest.approx(metadata['test_metrics']['MAE'],abs=.01)
    assert r2_score(d.iloc[te].price_mad,pred)==pytest.approx(metadata['test_metrics']['R2'],abs=1e-8)
    pre=model.regressor_.named_steps['preprocessor']
    assert pre.transform(d.iloc[te][FEATURES]).shape==(2685,237)
    assert np.allclose(pred,np.expm1(model.regressor_.predict(d.iloc[te][FEATURES])))
    assert list(pre.named_steps['columns'].feature_names_in_)==FEATURES
