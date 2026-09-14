"""Contrats de fuite, de groupes et d'inférence du nouveau pipeline."""
import numpy as np
import pandas as pd
from ml.src.advanced_optimization import (
    SafePreprocessor, build_safe_features, grouped_data, create_group_cv,
    fit_model, regression_metrics, add_text_features,
)


def sample(n=30):
    return pd.DataFrame({
        'surface_m2':np.arange(n)+50.,'bedrooms':2.,'bathrooms':1.,
        'city':['A','B']*(n//2),'neighborhood':'Centre','region':'R',
        'property_type':'appartement','parking':'unknown','balcony':'no',
        'furnished_status':'unknown','sea_view':'yes',
        'price_mad':np.arange(n)*10000.+500000,
        'listing_id':[f'id{i}' for i in range(n)],'split_group':[f'g{i}' for i in range(n)],
        'source':'s','source_listing_id':None,'duplicate_group_id':None,
        'canonical_url_repaired':None,'url':None,
    })


def test_target_and_technical_columns_never_influence_features():
    data = sample()
    modified = data.assign(price_mad=1e12,price_per_m2=1e10,listing_id='changed',
                           outlier_reasons='target derived',price_proxy=12)
    pd.testing.assert_frame_equal(build_safe_features(data),build_safe_features(modified))
    prep = SafePreprocessor(native=True).fit(data)
    pd.testing.assert_frame_equal(prep.transform(data),prep.transform(modified))


def test_validation_does_not_change_train_statistics_and_unknown_is_distinct():
    data = sample()
    prep = SafePreprocessor(native=True).fit(data)
    before = prep.transform(data)
    alien = sample(2).assign(surface_m2=1e12,city='unseen',bedrooms=0,bathrooms=np.nan)
    transformed = prep.transform(alien)
    assert transformed.city_frequency.eq(0).all()
    assert transformed.parking.eq('unknown').all()
    assert transformed.balcony.eq('no').all()
    assert np.isfinite(transformed[prep.nums]).all().all()
    pd.testing.assert_frame_equal(before,prep.transform(data))


def test_identity_overlap_removed_transitively_without_removing_test():
    train = sample()
    train.loc[0,'url']='shared'
    train.loc[1,'url']='shared'
    held = sample(2).assign(listing_id=['new0','new1'],city='other')
    held.loc[0,'url']='shared'
    safe,test = grouped_data(train,held)
    assert not {'id0','id1'} & set(safe.listing_id)
    assert len(test)==2
    assert not set(safe.split_group)&set(test.split_group)
    for tr,va in create_group_cv(safe,5):
        assert not set(safe.iloc[tr].split_group)&set(safe.iloc[va].split_group)


def test_raw_and_log_fit_missing_inference_and_repeatability():
    data = sample()
    for mode in ['RAW','LOG']:
        spec = dict(family='hist',target=mode)
        model = fit_model(data,spec,10)
        p = model.predict(pd.DataFrame([{'city':'unknown city'}]))
        assert p.shape==(1,) and np.isfinite(p).all()
        np.testing.assert_array_equal(model.predict(data),fit_model(data,spec,10).predict(data))
        assert regression_metrics(data.price_mad,model.predict(data))['MAE']>=0


def test_text_numbers_masked_before_feature_count():
    a = pd.DataFrame({'title_raw':['Appartement 1 500 000 DH']})
    b = pd.DataFrame({'title_raw':['Appartement 9 999 999 DH']})
    pd.testing.assert_frame_equal(add_text_features(a),add_text_features(b))


def test_boosters_residual_and_nested_ensemble_are_serializable(tmp_path):
    import joblib
    data = sample()
    specifications = [dict(family=family,target='LOG') for family in ['cat','lgb','xgb']]
    specifications += [dict(family='cat',target='LOG',strategy='residual'),
                       dict(family='ensemble',target='RAW',method='ridge')]
    for index,spec in enumerate(specifications):
        model = fit_model(data,spec,5)
        path = tmp_path/f'model_{index}.joblib'
        joblib.dump(model,path)
        np.testing.assert_array_equal(model.predict(data),joblib.load(path).predict(data))
