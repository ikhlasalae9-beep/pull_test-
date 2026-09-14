# Data pipeline

## Objective and engineering history

Build an auditable sale-listing dataset for predicting `price_mad`, the asking price in MAD. According to the project team's account, approximately three days of iterative engineering were needed to inspect scraping inconsistencies, recover displaced/misaligned records, normalize geography, repair property types, validate neighborhoods, reconstruct canonical URLs where evidence allowed, identify duplicates, recompute numeric consistency, inspect extreme values, separate modeling data from audit information, and prevent leakage. This duration describes the overall engineering effort, not one crawler run.

## Original collection and recovery

Mubawab is the main historical source. The preserved Scrapy collector (`ml/scraping/maisondelux_scraper/`) extracts listing cards/detail evidence, including structured JSON-LD where available, and maintains checkpoints. Later recovery in `ml/src/pipeline.py` combined Git-preserved evidence and displaced notebook exports. Original batches total 13,867 rows: `git_head_complete` 10,109, `recovery_misplaced_notebook` 3,665, and `recovery_dangling_v3` 93.

The original schema carried inconsistent property labels, geographic text, missing traceability and a suspicious high price-per-square-metre tail in the displaced-notebook batch. A repaired schema was necessary to retain original evidence while recording each repair and exclusion separately. Raw provenance must not be mistaken for a production feature.

## Final preparation and validation

`ml/src/data_repair/model_ready.py`, orchestrated by `notebooks/data_repair_model_ready.ipynb`, preserves the source CSV and its hash. It repairs types using textual evidence, checks neighborhood validity and city/region consistency, reconstructs URLs only when evidence exists, and audits numerical plausibility. It validates CSV/Parquet dimensions, positive finite prices/surfaces, required geography and explicit exclusion reasons.

The quality report records 1,659 changed property types and 610 invalid neighborhoods detected before exclusions. Final output retains 13,537 rows across 10 regions and 30 cities. The report counts 646 values in its neighborhood field; the modeling notebook uses `neighborhood_clean`, including 534 unavailable values, so these counts should not be confused with validated nonmissing modeling categories.

Confirmed duplicate removal is conservative: 26 rows removed using high-confidence evidence. The 3,455 possible duplicates remain, with group identifiers for splitting. Another 304 probable parsing/numeric errors are excluded. The final dataset retains 233 uncertain outliers and 41 plausible extremes; global IQR trimming is not applied. Sensitivity analyses do not replace the official dataset.

## Modeling choice and leakage prevention

`data/processed/maisondelux_model_ready_v1.csv` is selected because it contains the audited repairs and exclusion decisions and is the exact source of the executed final model notebook. The notebook assigns `property_type_repaired` to `property_type`, `neighborhood_clean` to `neighborhood`, and strips categorical whitespace. Only the 11 declared EXTENDED features enter inference. Target-derived price/m², IDs, batches, URLs and audit fields remain excluded.

The Train/Test split groups related listings, with no group overlap, seed 18 and 10,852/2,685 rows. Imputation, rare-category grouping, scaling and encoding are fitted inside training pipelines and cross-validation folds.

## Limitations and reproducibility

URLs are missing for 74.48% of final rows and native source IDs for 77.69%. Coordinates and publication dates are entirely unavailable; collection timestamps are not substituted for publication dates. Bedrooms and bathrooms are missing in 0.72% and 1.43% of rows. Unreported amenities remain `unknown`, never assumed absent. Apartments dominate (11,918 rows); cities and segments are unevenly represented.

The final CSV, executed notebook, model and audit reports are retained. Local recovery archives and intermediate exports are preserved but ignored by Git; full historical reconstruction requires those inputs. To reproduce the repair, run the repair notebook with those inputs present. To verify the final artifact without retraining, run `python -m pytest tests/test_inference.py -q -p no:cacheprovider`. The test recreates the held-out split and checks notebook metrics. Do not rerun benchmark/tuning cells merely to serve predictions.

See `reports/data_quality/model_ready_v1_quality_report.md` and its JSON/CSV audit companions for measured counts. The newer V3 pilot failed traceability gates and did not replace this final modeling dataset.
