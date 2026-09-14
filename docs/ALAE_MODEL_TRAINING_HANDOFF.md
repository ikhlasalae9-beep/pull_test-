> Historical record: model serving is now documented in [MODEL_V1.md](MODEL_V1.md). Earlier runtime/artifact references below are superseded.

# Alae model-training handoff

## Start here

```text
Primary dataset: data/processed/maisondelux_clean.parquet
Fallback:        data/processed/maisondelux_clean.csv
Quick sample:    data/sample/maisondelux_model_sample.csv
Target:          price_mad
```

Use the 750-row tracked sample for schema and code smoke tests. Switch to the
full Parquet file for all scientific model selection and final metrics. The full
dataset is a local generated artifact; if it is not present after cloning, obtain
the verified handoff copy or run the local-evidence rebuild described in
`SCRAPING_AND_DATA_PIPELINE.md`.

## Dataset profile

- 13,867 valid unique apartment-sale listing rows.
- One recovered source: Mubawab.
- 9 regions, 31 cities, and 876 neighborhoods.
- Target median 1,550,000 MAD; mean 2,077,007 MAD; range 60,000–34,000,000 MAD.
- Surface median 104 m²; range 14–2,200 m².
- Bedrooms are missing in 94 rows (0.68%); bathrooms in 196 rows (1.41%).
- Latitude, longitude, and publication date are 100% missing.
- Explicit `unknown` rates: furnished status 84.45%, parking 80.26%, balcony
  85.83%, and sea view 98.00%.
- Asking prices are not verified transaction prices and include source/selection
  noise.

The canonical upstream status is useful but should still be re-audited before
modeling. In particular, inspect title/URL evidence for the small number of
misclassified rental or non-apartment advertisements. Document any exclusions;
do not tune target-derived trimming rules against the holdout.

## Candidate features

Start with fields reproducible from the website:

```text
region
city
neighborhood
surface_m2
bedrooms
bathrooms
furnished_status
parking
balcony
sea_view
```

`latitude` and `longitude` are schema candidates only; they currently contain no
listing-level values. Do not replace them with city centroids while pretending
they are property coordinates. `property_type` and `transaction_type` are
constants in the clean data (`appartement`, `sale`) and add no signal.

Useful target-independent engineering includes log surface, surface bands,
surface-per-bedroom, bathroom/bedroom interactions, amenity/unknown counts,
train-fitted category frequencies, and city-neighborhood combinations. Every
engineered value must be reproducible from a website request.

## Leakage exclusions

Never place these in the feature matrix:

```text
price_per_m2
listing_id
source_listing_id
url
validation_status
validation_reasons
scraped_at
publication_date
publication_date_status
duplicate_of
price_raw
title_raw or details_raw when they contain price text
source_record_path
```

`price_per_m2` is `price_mad / surface_m2` and therefore direct target leakage.
Use IDs, URLs, fingerprints, and provenance only to prevent duplicate leakage or
to audit errors.

## Evaluation protocol

1. Freeze a train/validation/test manifest before fitting preprocessing.
2. Use normalized `city + neighborhood` as the primary spatial group so the same
   neighborhood cannot appear across splits.
3. Keep exact and conservative near-duplicate property fingerprints in one split.
4. Balance group sizes and price quantile distributions using split logic only;
   never select a split because a model scores well on it.
5. Fit encoders, imputers, rare-category handling, frequency mappings, scalers,
   and outlier decisions on training data only.
6. Tune on grouped cross-validation or the fixed validation partition. Open the
   final test once after model and parameter selection.
7. Also report a seeded leakage-safe random benchmark, clearly labeled as
   secondary and usually more optimistic.
8. Report R², MAE, RMSE, median absolute error, MAPE, prediction latency, and
   city/price/surface segment errors. Regression does not use SMOTE.

An R² over 0.90 should trigger mandatory checks for target-derived fields,
duplicate/near-duplicate crossover, raw price text, preprocessing before split,
and holdout contamination.

## First experiments

- Median, city-median, and city-plus-surface heuristics.
- Ridge/ElasticNet with unknown-safe one-hot encoding.
- Extra Trees and HistGradientBoosting with bounded depth/leaf size.
- CatBoost with native categorical strings, both raw price and
  `log1p(price_mad)` targets. Convert log predictions with `expm1` before MAD
  metrics.

CatBoost is a strong first candidate for high-cardinality neighborhoods, but it
must win validation rather than be assumed best. XGBoost/LightGBM are optional;
do not add dependencies unless their expected value justifies them.

## Previous benchmarks

The retained legacy production pipeline reports test R² 0.6392, MAE 395,559 MAD,
and RMSE 888,301 MAD. A later offline experiment reported R² 0.6560, MAE 386,983
MAD, RMSE 867,343 MAD, median absolute error 197,475 MAD, and MAPE 24.36%.

Treat these only as historical references: they used a different recovered cohort
and non-spatial duplicate grouping; the 0.656 result also blended raw title/detail
text unavailable to the website. A new neighborhood-grouped result is not directly
comparable and may be materially lower.

## Notebook and expected outputs

Create the official notebook at:

```text
ml/notebooks/maisondelux_model_training.ipynb
```

Keep reusable code under a new `ml/src/modeling/` package. Do not overwrite the
current backend artifacts until a candidate has passed reload and contract tests.
Expected candidate outputs are:

```text
ml/artifacts/maisondelux_model.joblib
ml/artifacts/maisondelux_model.cbm       # only when CatBoost is selected
ml/artifacts/preprocessor.joblib
ml/artifacts/feature_schema.json
ml/artifacts/model_metadata.json
ml/artifacts/model_metrics.json
reports/model/model_evaluation.md
reports/model/model_leaderboard.csv
reports/model/error_analysis.csv
reports/model/feature_importance.csv
reports/model/final_test_predictions.csv
```

Save a complete inference system, dataset hash, exact split manifests, package
versions, parameters, known categories, and expected input schema. Predictions
before and after reload must agree within a documented tolerance.

## Current website/backend contract

`backend/app.py` currently sends the legacy model these request-derived fields:

```text
ville -> city
quartier -> neighborhood
surface -> surface_m2
chambres -> bedrooms
salles_bain -> bathrooms
pieces, haut_standing, en_construction, type_bien -> legacy-only fields
```

The clean dataset has no `pieces`, high-standing, or construction field. The
current frontend also offers villa/studio/duplex and Martil, which are not
supported by the clean apartment-only training corpus. Do not silently return an
apartment estimate for another property type or unsupported city. Either reject
it clearly or keep the legacy path until representative data exists. Missing
amenities may default to explicit `unknown`; invalid required fields must raise a
validation error.

The currently retained `pipeline.pkl`, `metrics.json`, and `model_metadata.json`
are legacy runtime dependencies. Integrate a new model through a separate adapter
and shadow endpoint first, test the exact request/response contract, then replace
the production path in a dedicated reviewed change.

## Alae's first step

Create `ml/notebooks/maisondelux_model_training.ipynb`, load the tracked sample,
assert the schema and leakage exclusions, and implement the fixed grouped split
manifest. Once that smoke test passes, change the loader to the full clean
Parquet file and run baselines before any tuning.
