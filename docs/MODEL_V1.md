# MaisonDeLUX model V1

## Objective and supported use

Predict sale-listing asking price `price_mad` in Moroccan dirhams. The website conservatively offers residential apartments; the training dataset also contains small numbers of other repaired types, for which reliable segment performance is not established. Rentals, transaction-price appraisal, official valuations and reliable estimates for unrepresented markets are unsupported.

## Final selection and artifact

Source of truth: executed `ml/notebooks/maisondelux_notebook1.ipynb`, especially cells 170–176 and 195 (zero-based). Selected configuration: **XGBoost / EXTENDED / LOG**. Both tuned three-fold selection and five-fold confirmation select this configuration. Five-fold confirmation MAE is approximately 429,572 MAD and R² 0.5471.

The fitted artifact at `models/maisondelux_price_model_v1.joblib` is a `TransformedTargetRegressor` wrapping preprocessing and XGBoost. It learns `log1p(price_mad)` and automatically returns `expm1` predictions in MAD. Never apply the inverse a second time.

The custom RareCategoryGrouper was moved, with identical implementation, from notebook scope to `ml/src/inference.py` and the existing object reserialized with that importable module. No fit or retraining was performed. Predictions before/after serialization were exactly equal on all 13,537 rows. `models/maisondelux_price_model_v1_metadata.json` contains the original precise Test metrics.

Fitted hyperparameters: `n_estimators=900`, `max_depth=4`, `learning_rate=0.1`, `subsample=0.85`, `colsample_bytree=0.7`, `min_child_weight=5`, `objective=reg:squarederror`, `random_state=42`, `n_jobs=-1`. The fitted XGBoost object records `enable_categorical=True`; inputs are nevertheless the notebook's encoded numeric matrix. Other parameters retain the fitted library defaults. Runtime used Python 3.12, XGBoost 3.4.1, scikit-learn 1.8.0, pandas 2.2.3, NumPy 2.4.4 and joblib 1.5.3.

## Inputs and preprocessing

Exact ordered features:

`surface_m2`, `bedrooms`, `bathrooms`, `region`, `city`, `neighborhood`, `property_type`, `parking`, `balcony`, `sea_view`, `furnished_status`.

The notebook copies repaired property types and cleaned neighborhoods into the corresponding input columns and strips categorical whitespace. Inference strips strings and preserves category spelling. Missing bedroom/bathroom values become NaN; unspecified amenities become the observed `unknown` category.

Within the fitted pipeline: neighborhoods with fewer than 10 Train observations and cities with fewer than 20 become `Rare`; unseen values also map to `Rare`. Numeric values receive Train median imputation and standard scaling. Other missing categories use `Unknown`, followed by one-hot encoding with unknown categories ignored. EXTENDED produces 237 encoded columns. All transformations remain inside the serialized estimator.

No `price_per_m2`, price-derived field, listing ID, batch, duplicate/audit field or target enters inference. The API rejects undeclared inputs.

## Validation and final Test performance

GroupShuffleSplit uses duplicate group IDs where available and listing IDs otherwise. Seed 18 was chosen among candidate splits by geographic/type balance, without target-based split selection. Train has 10,852 rows; Test has 2,685, with no shared groups. GroupKFold screening, tuning and confirmation use Train only; preprocessing is fitted within each fold.

| Metric | Official Test value |
|---|---:|
| MAE | 427,233.7566 MAD |
| RMSE | 1,024,909.6699 MAD |
| R² | 0.6104168049 |
| Median absolute error | 201,411.5625 MAD |
| Median absolute percentage error | 14.12495% |
| Within ±10% | 37.24395% |
| Within ±20% | 63.24022% |
| Within ±30% | 79.06890% |

The obtained R² reflects meaningful predictive signal for a first real-estate prototype under the current data limitations. There is no universal R² quality classification. Performance varies by city and market segment. The prototype validates feasibility; future work should prioritize coverage, quality and feature richness.

The notebook's sensitivity experiment excluding uncertain outliers gives R² about 0.77 and MAE 340,509 MAD on a different subset; unique-only gives R² about 0.59. These are not the official final Test performance. Conformal intervals were disabled, so the API intentionally returns no purported confidence range.

## API contract and operation

Run `python -m backend.app` from the project root, then `npm run dev` in another terminal. Installation and a PowerShell request are in the root README.

`POST /api/estimate` on the website proxies to the same Flask route. Server configuration: `INFERENCE_API_URL`, default `http://127.0.0.1:5000`.

```json
{"surface_m2":120,"bedrooms":3,"bathrooms":2,"region":"Casablanca-Settat","city":"Casablanca","neighborhood":"Maârif","property_type":"appartement","parking":"unknown","balcony":"unknown","sea_view":"unknown","furnished_status":"unknown"}
```

Successful response: `{"estimated_price_mad": <positive integer>, "currency": "MAD", "model_version": "v1"}`.

Surface is required, numeric, finite and positive. Bedrooms/bathrooms may be omitted/null; provided values must be nonnegative finite integers. Region, city and property type require nonempty strings; neighborhood and amenities may be omitted. Categories are trimmed; unseen strings do not crash preprocessing. Validation returns JSON error with status 400, malformed/unsupported content uses the appropriate HTTP error, and model/proxy failures return 503 without fabricated prices. The form derives the exact region from the selected dataset city using `models/locations_v1.json`.

The same-origin route avoids browser CORS configuration. Flask's local server is for local submission/demo; hosted service operation requires an appropriate WSGI server and protected deployment configuration. Load only the trusted repository artifact.

## Limitations

One main source, asking prices, uneven geographic coverage, predominantly apartments, missing dates/coordinates, extensive missing traceability, uncertain outliers and mostly unknown amenities constrain generalization. The final model is the Train-fitted evaluated artifact, not an all-data refit. Historical source audits and recovery limitations are documented separately.
