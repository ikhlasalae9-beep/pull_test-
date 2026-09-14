# MaisonDeLUX model-ready dataset v1

The original CSV remains unchanged. Publication dates and coordinates were not fabricated.

## Summary

| metric | value |
|---|---|
| original_rows | 13867 |
| final_model_ready_rows | 13537 |
| rows_removed | 330 |
| confirmed_duplicates_removed | 26 |
| probable_parsing_errors_removed | 304 |
| possible_duplicates_retained | 3455 |
| property_type_rows_changed | 1659 |
| invalid_neighborhoods_detected | 610 |
| regions | 10 |
| cities | 30 |
| neighborhoods | 646 |

## Exclusions

| reason | rows | explanation |
|---|---|---|
| probable_parsing_error | 304 | Numeric magnitude or consistency evidence indicates a probable error. |
| confirmed_duplicate | 26 | A higher-evidence row represents the same property observation. |

## Property types after repair

| property_type | rows |
|---|---|
| appartement | 11918 |
| unknown | 1247 |
| studio | 202 |
| duplex | 107 |
| immeuble | 32 |
| villa | 13 |
| riad | 9 |
| maison | 6 |
| bureau | 2 |
| magasin | 1 |

## Batch audit

| batch_id | rows | median_ppm | p95_ppm | p99_ppm | status |
|---|---|---|---|---|---|
| git_head_complete | 10109 | 13750.0 | 27635.86 | 39701.05 | not_flagged |
| recovery_misplaced_notebook | 3665 | 17078.95 | 108318.84 | 140248.22 | suspicious_high_price_per_m2_tail |
| recovery_dangling_v3 | 93 | 16972.48 | 32508.56 | 38248.36 | not_flagged |

## Missing values in final data

| field | missing_percent |
|---|---|
| price_mad | 0.0 |
| surface_m2 | 0.0 |
| city | 0.0 |
| region | 0.0 |
| neighborhood_clean | 3.94 |
| property_type_repaired | 0.0 |
| bedrooms | 0.72 |
| bathrooms | 1.43 |
| url | 74.48 |
| source_listing_id | 77.69 |
| publication_date | 100.0 |
| latitude | 100.0 |
| longitude | 100.0 |

## Modeling feature policy

Target: `price_mad`

Safe candidates: `region`, `city`, `neighborhood_clean`, `property_type_repaired`, `surface_m2`, `bedrooms`, `bathrooms`, `furnished_status`, `parking`, `balcony`, `sea_view`

`price_per_m2` and both derived price/m² audit columns are excluded because they directly encode the target.
