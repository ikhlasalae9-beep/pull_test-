# Canonical data schema

The authoritative final column order is `CANONICAL_COLUMNS` in `ml/src/cleaning/normalization.py`.

| Group | Fields |
|---|---|
| Identity/provenance | `listing_id`, `source`, `source_listing_id`, `url`, `source_record_path` |
| Geography | `city`, `neighborhood`, `region`, `latitude`, `longitude` |
| Property | `surface_m2`, `bedrooms`, `bathrooms`, `property_type`, `furnished_status`, `parking`, `balcony`, `sea_view` |
| Transaction/target | `transaction_type`, `price_mad`, `price_per_m2` |
| Time | `publication_date`, `publication_date_status`, `scraped_at` |
| Quality | `validation_status`, `validation_reasons`, `deduplication_status`, `duplicate_of` |
| Raw evidence | `title_raw`, `price_raw`, `location_raw`, `details_raw` |

## Rules

- Null means unknown; `unknown` is distinct from `no`.
- `publication_date` is populated only from publication evidence. `scraped_at` is never substituted.
- Raw evidence is preserved alongside normalized values.
- Generic neighborhoods (`Appartements`, `Publier une annonce`, `Accueil`, `Maroc`, sales phrases and fragments) are rejected.
- Neighborhood repair uses source location evidence first, then a city-specific vocabulary matched conservatively against the URL/title.
- Coordinates must fall inside a conservative Morocco bounding box; city centroids are used only to determine `region`, not written as precise listing coordinates.
- `price_per_m2` is audit-only and forbidden from any model predicting `price_mad`.
- Validation produces multiple pipe-delimited reason codes. Rejected and warning rows are retained in `maisondelux_rejected.csv`.

## Deduplication order

1. exact canonical `listing_id`;
2. source + native listing ID;
3. canonical URL;
4. conservative fingerprint including title, city, neighborhood, surface, rooms, price and property type;
5. cross-source fuzzy comparison only inside tight price/surface/city blocks and at a 0.96 similarity threshold.

Attribute-only candidate groups from the old scraper are not trusted as confirmed duplicates.
