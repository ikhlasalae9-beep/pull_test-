# MaisonDeLUX V3 PILOT quality report

## Summary

| Metric | Value |
|---|---:|
| total raw listings | 500 |
| total normalized | 500 |
| total valid | 309 |
| total warnings | 108 |
| total rejected | 83 |
| total duplicates | 15 |
| total modeling rows | 410 |
| number of sources | 1 |
| number of regions | 11 |
| number of cities | 32 |
| number of neighborhoods | 202 |
| median price mad | 1300000.0 |
| median surface m2 | 99.5 |
| median price per m2 | 12524.130000000001 |
| largest city share percent | 12.2 |

## Missing values

| Field | Missing % |
|---|---:|
| publication_date | 100.00 |
| url | 72.93 |
| source_listing_id | 72.93 |
| city | 0.00 |
| neighborhood | 17.80 |
| surface_m2 | 0.00 |
| price_mad | 0.00 |
| bedrooms | 0.49 |
| bathrooms | 0.00 |
| latitude | 100.00 |
| longitude | 100.00 |

## Acceptance checks

| Check | Passed |
|---|:---:|
| A_unique_listing_id | YES |
| B_sale_only | YES |
| C_price_present | YES |
| D_surface_large_majority | YES |
| E_city_present | YES |
| F_region_present | YES |
| G_property_not_hardcoded | YES |
| H_publication_date_retrieved | NO |
| I_neighborhood_no_fragments | YES |
| J_city_balanced | YES |
| K_several_property_types | YES |
| L_several_regions | YES |
| M_traceability_majority | NO |
| pilot_multiple_sources | NO |
| pilot_size_300_to_1000 | YES |
| checkpoint_resume_tested | YES |

## Source status

| Adapter | Status |
|---|---|
| mubawab_authorized_feed | disabled |
| agenz_authorized_feed | disabled |
| sarouty_authorized_feed | disabled |
| preserved_local_evidence | loaded:25433:elapsed_seconds=0.39 |

## Publication date by source

| Source | Rows | Available | Available % |
|---|---:|---:|---:|
| mubawab.ma | 410 | 0 | 0.00 |
