# Scraping and recovery

## A. ORIGINAL COLLECTION

Historical sale listings came mainly from Mubawab. Preserve `ml/scraping/maisondelux_scraper/` for card/detail parsing, structured JSON-LD extraction, checkpoint persistence and retry behavior. `ml/src/pipeline.py` documents recovery from Git-preserved batches and misplaced notebook data. `ml/notebooks/maisondelux_data_pipeline.ipynb` orchestrates the historical process.

## B. OBSERVED LIMITATIONS

The 13,867-row recovered dataset had inconsistent property types, invalid neighborhood strings, batch-dependent numeric tails and incomplete URLs/native IDs. Geographic and amenity completeness varied by batch. The recovered data cannot establish a publication timeline or precise coordinates. Earlier notebook introductory counts describe this historical stage rather than the final repaired dataset.

## C. RECOVERY / REPAIR

The approximately three-day iterative engineering effort is described in DATA_PIPELINE.md. `ml/src/data_repair/model_ready.py` retains originals and records repair evidence, checks region/city consistency, rejects invalid neighborhoods, repairs types, reconstructs canonical URLs where justified, audits batches and numeric consistency, and identifies duplicate groups. It removes only confirmed duplicates and probable errors under documented rules. Possible duplicates and plausible/uncertain extremes remain visible for group-aware validation and sensitivity analysis.

`notebooks/data_repair_model_ready.ipynb` is the repair entry point. Row-level exclusion, neighborhood, duplicate, batch and outlier reports live under `reports/data_quality/model_ready_v1_*`.

## D. FINAL DATASET

`data/processed/maisondelux_model_ready_v1.csv`: 13,537 rows, 57 columns, 10 regions, 30 cities. Removed: 26 confirmed duplicates and 304 probable parsing errors. Retained possible duplicates: 3,455. Apartments account for 11,918 rows, with 1,247 unknown property types. The modeling notebook selects exactly 11 inputs and excludes all target-derived and technical fields.

The newer V3 pipeline (`ml/src/scraping_v3/` and `notebooks/data_maisondelux_scraper_v3.ipynb`) is preserved as traceable future collection work. Its historical local pilot retained 410 modeling rows but only 27.07% URL/native-ID availability; it failed the release gate and is not the training dataset. The recorded source review left live sources disabled. This finalization performed no new scraping and did not revalidate external source terms; consult the recorded source audits and obtain appropriate authorization before future collection.

## E. KNOWN LIMITATIONS

This is a prototype/PFE dataset of asking prices, not verified transaction prices. Missing publication dates, coordinates and extensive listing traceability cannot be reconstructed reliably from the available evidence. Unknown amenities remain unknown. Geographic imbalance, rare types and uncertain extreme prices limit generalization.

Future versions should improve quantity, diversity and quality using multiple legally usable sources, broader geography and property types, richer property characteristics and stronger listing traceability. Useful additions include temporal observations, coordinates, floor, property condition, building age, proximity to infrastructure/services and appropriate market/economic signals. Such improvements can improve generalization; more rows do not automatically guarantee higher R². Evaluate new versions on independent, leakage-protected data.
