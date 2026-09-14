# MaisonDeLUX data quality report

Generated: 2026-09-02T22:59:19.454425+00:00

## Outcome

- Raw recovered rows: **25,433**
- Valid unique rows: **13,867** (54.52%)
- Rejected or warning rows: **11,566**
- Confirmed duplicate rows: **1,142**
- Sources: **1**; cities: **34**; neighborhoods: **1,043**

`price_per_m2` is retained for validation and analysis only. It must never be a feature when predicting `price_mad`.

## Validation reasons

| Reason | Rows |
|---|---:|
| `missing_or_invalid_neighborhood` | 7,404 |
| `missing_city` | 3,446 |
| `missing_price` | 2,344 |
| `price_per_m2_outlier` | 1,453 |
| `unknown_property_type` | 1,342 |
| `duplicate_listing_id` | 1,141 |
| `implausible_price` | 1,105 |
| `missing_surface` | 1,073 |
| `unknown_transaction` | 219 |
| `implausible_bedrooms` | 7 |
| `implausible_bathrooms` | 6 |
| `implausible_rooms` | 2 |
| `implausible_surface` | 1 |
| `duplicate_fingerprint` | 1 |

## Missing-value rates

| Field | Missing |
|---|---:|
| `latitude` | 100.0% |
| `longitude` | 100.0% |
| `publication_date` | 100.0% |
| `duplicate_of` | 95.5% |
| `source_listing_id` | 69.9% |
| `url` | 66.3% |
| `validation_reasons` | 54.5% |
| `details_raw` | 33.6% |
| `price_raw` | 33.2% |
| `title_raw` | 33.1% |
| `location_raw` | 33.1% |
| `neighborhood` | 29.1% |
| `price_per_m2` | 13.4% |
| `price_mad` | 9.2% |
| `bathrooms` | 5.4% |
| `property_type` | 5.3% |
| `bedrooms` | 4.7% |
| `surface_m2` | 4.2% |
| `region` | 0.0% |
| `listing_id` | 0.0% |
| `source` | 0.0% |
| `city` | 0.0% |
| `furnished_status` | 0.0% |
| `parking` | 0.0% |
| `balcony` | 0.0% |
| `sea_view` | 0.0% |
| `transaction_type` | 0.0% |
| `publication_date_status` | 0.0% |
| `scraped_at` | 0.0% |
| `validation_status` | 0.0% |
| `deduplication_status` | 0.0% |
| `source_record_path` | 0.0% |

## Explicit unknown rates

Tri-state `unknown` values are not counted as nulls above; they are reported separately here.

| Field | Unknown |
|---|---:|
| `furnished_status` | 81.6% |
| `parking` | 76.7% |
| `balcony` | 81.4% |
| `sea_view` | 96.8% |
| `publication_date_status` | 100.0% |

## Recovery inputs

| Input | Rows | Role |
|---|---:|---|
| `data\external\recovery_archive\20260902T224619Z\misplaced_notebook_data\data\raw\maisondelux_raw.csv` | 8,425 | URL-rich recovery base |
| `data\external\recovery_archive\20260902T224619Z\dangling_v3_tree_87e06eeb\data\raw\maisonlux_listings_v3.csv` | 20 | recovered V3 pilot evidence |
| `data\external\recovery_archive\20260902T224619Z\dangling_v3_tree_87e06eeb\data\raw\maisonlux_scrapy_v3.csv` | 130 | recovered V3 pilot evidence |
| `git:HEAD:data/raw/maisonlux_maroc_complet.csv` | 16,858 | historical four-column recovery dataset |
