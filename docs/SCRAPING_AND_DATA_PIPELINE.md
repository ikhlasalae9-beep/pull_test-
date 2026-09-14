# MaisonDeLUX scraping and data pipeline

This is the authoritative engineering guide for the recovered MaisonDeLUX
listing corpus. It replaces obsolete long-running notebook instructions.

## Objective and verified outcome

The data layer prepares a traceable corpus of Moroccan apartment sale asking
prices for analysis and later model development. The verified outputs contain:

| Measure | Rows |
|---|---:|
| Raw recovered evidence | 25,433 |
| Valid unique listings | 13,867 |
| Rejected or warning rows | 11,566 |
| Confirmed duplicate rows | 1,142 |

All listing observations are Mubawab-derived. Valid rows cover 9 regions, 31
cities, and 876 neighborhoods. Publication dates are unavailable for every row.

These are advertised asking prices, not signed or notarized transaction prices.
They include seller/agent negotiation margins and portal-selection bias.

## Why recovery and normalization were required

The original repository mixed a historical four-column CSV, URL-rich outputs,
small Scrapy checkpoints, raw text, generated files, and notebook-local data.
Fields used different names and types; locations and prices were embedded in
text; some records lacked stable source IDs; and interrupted runs left duplicate
evidence. The current Python modules recover those inputs without inventing rows,
normalize them into one schema, preserve lineage, and separate accepted rows from
warnings/rejections.

## Source policy gate

Robots permission alone does not authorize database extraction or reuse. Every
live adapter must pass all of the following before it can emit listing rows:

1. the exact route is allowed by robots policy;
2. terms and database-reuse conditions allow the intended collection;
3. no login, CAPTCHA, access-control, rate-limit, or anti-bot bypass is needed;
4. a small pilot passes manual field validation; and
5. the authorization basis is recorded.

No protection was bypassed during this project. HTTP 403 and 429 are stop/slow
signals, never invitations to evade controls.

| Source | Status | Reason |
|---|---|---|
| `data.gov.ma` | enabled for reference metadata only | Its CKAN API exposes open-data metadata, not current property listings. |
| Mubawab | disabled for new live collection | Current terms restrict substantial extraction/reuse; written permission is required. |
| Agenz | disabled | Robots blocks listing/search/map routes and terms restrict copying; request a professional feed/API. |
| MarocAnnonces | disabled | Robots and terms do not permit the proposed generic collection/reuse. |
| Avito.ma | disabled | A Cloudflare challenge was encountered and no clear bulk-use permission was found; no bypass was attempted. |
| 360annonces | disabled | Terms prohibit collection without authorization. |
| Sarouty | disabled | Public listing routes are robots-allowed with a 10-second crawl delay, but public terms do not establish permission for bulk database reuse; written permission or a licensed feed is required. |

The dated evidence and direct policy URLs are recorded in
`reports/scraping/source_policy_audit.json` and
`reports/scraping/source_coverage_report.md`. Recovered historical possession
does not create permission for a new crawl.

## How the Mubawab evidence was originally collected

The retained legacy Scrapy package under `ml/scraping/` documents the collector:

- diversified public city seed pages discover detail links;
- canonical listing URLs and native IDs provide stable resume keys;
- detail parsing prefers `RealEstateListing` JSON-LD and uses conservative HTML
  fallbacks;
- item parsing extracts location, price, surface, bedrooms, bathrooms, property
  and transaction type, amenity flags, URL, title/details, and timestamps when
  genuinely available;
- each accepted item is appended and flushed to a CSV checkpoint;
- structured failure records preserve URL, status, stage, and error context.

The package is retained for offline parser/checkpoint tests and future licensed
work. Its live Mubawab spider must not be run under the current policy record.

## Request discipline, retries, and interruption

The legacy settings use one concurrent request per domain, a six-second base
delay randomized to roughly three–nine seconds, AutoThrottle up to 60 seconds,
and a 45-second timeout. Transient 408/5xx responses receive at most two retries
with exponential 10–60 second backoff.

HTTP 429 is not retried in the same crawl. The middleware persists a cooldown
marker (minimum 900 seconds), closes the crawl, and leaves the append-only
checkpoint valid. HTTP 401/403/429 also trip the active client circuit breaker.
Existing native IDs and canonical URLs are loaded on restart, so an authorized
run resumes without scheduling known rows. `Ctrl+C` is safe between stages; CSV
checkpoints are flushed incrementally and Excel is generated only after a run.

## Canonical raw schema

The authoritative order is `CANONICAL_COLUMNS` in
`ml/src/cleaning/normalization.py`:

- identity/provenance: `listing_id`, `source`, `source_listing_id`, `url`,
  `source_record_path`;
- geography: `city`, `neighborhood`, `region`, `latitude`, `longitude`;
- property: `surface_m2`, `bedrooms`, `bathrooms`, `property_type`,
  `furnished_status`, `parking`, `balcony`, `sea_view`;
- transaction: `transaction_type`, `price_mad`, `price_per_m2`;
- time: `publication_date`, `publication_date_status`, `scraped_at`;
- quality: `validation_status`, `validation_reasons`,
  `deduplication_status`, `duplicate_of`;
- raw evidence: `title_raw`, `price_raw`, `location_raw`, `details_raw`.

Null means unavailable. For tri-state attributes, `unknown` is not equivalent to
`no`. `scraped_at` is never substituted for a missing publication date.

## Recovery, cleaning, and normalization

`ml/src/pipeline.py` loads three evidence families: the URL-rich recovery base,
small V3 checkpoints, and the Git-preserved historical CSV. Every row records its
source path. Normalization then:

1. parses currency-aware total prices into MAD;
2. extracts numeric surface/room fields without inventing missing values;
3. standardizes city, neighborhood, property, transaction, and tri-state values;
4. repairs neighborhoods only from source location evidence or a conservative
   city-specific vocabulary;
5. rejects generic navigation/sales fragments as neighborhoods;
6. preserves raw strings beside normalized values; and
7. computes `price_per_m2` for audit only.

## Geographic enrichment

`ml/src/geography/` uses geoBoundaries gbOpen/OSM-derived region and province
polygons plus GeoNames populated-place coordinates and aliases. City centroids
may identify a region, but they are not written as precise property coordinates.
The output layers retain source/license metadata. Zero-listing locations remain
zero; geographic references never fabricate property observations.

## Validation and rejection reasons

Validation checks required identity/location fields, total price, surface, rooms,
apartment-sale scope, Morocco coordinate bounds when coordinates exist, and a
wide price-per-square-metre plausibility band. Multiple reasons are preserved as
pipe-delimited codes, including missing/implausible values, unknown scope,
generic neighborhoods, coordinate failures, unit-price warnings, and duplicate
methods. Rejected/warning rows remain in the rejected audit file.

`price_per_m2` is derived from `price_mad`; it must never enter a model that
predicts `price_mad`.

## Duplicate detection

The ordered checks are:

1. canonical listing ID;
2. source plus native ID;
3. canonical URL;
4. a conservative fingerprint of title, city, neighborhood, surface, rooms,
   price, and property type; and
5. cross-source fuzzy matching only inside tight city/price/surface blocks at a
   0.96 similarity threshold.

Attribute-only candidate groups from older experiments are not automatically
treated as confirmed duplicates.

## Output layout

```text
data/raw/maisondelux_raw.{csv,xlsx,parquet}
data/processed/maisondelux_clean.{csv,xlsx,parquet}
data/processed/maisondelux_rejected.csv
data/geographic/morocco_{regions,cities,neighborhoods}.geojson
data/sample/maisondelux_model_sample.csv
reports/data_quality/
reports/scraping/
```

The full generated datasets and large geographic layers are intentionally local
and ignored when appropriate. Their hashes and row-level reconciliation are in
`reports/data_quality/verification_report.json`. The small sample is tracked.

## Safe commands

Install project and legacy parser dependencies separately:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-scraping.txt
```

Re-run the non-listing policy/API preflight (safe under the current policy):

```bash
python -m ml.src.scraping.pilot
```

Rebuild outputs entirely from recovered local/Git evidence, without scraping:

```bash
python -m ml.src.pipeline
python -m ml.src.verify_outputs
```

Refresh attributed geographic reference files only when network/source updates
are intended:

```bash
python -m ml.src.geography.build_reference
```

Only after written Mubawab permission is recorded, a bounded four-listing pilot
would be:

```bash
python ml/scraping/run.py --max-city-pages 1 --max-listings 4 --output data/raw/authorized_mubawab_pilot.csv --failures-output data/raw/authorized_mubawab_pilot_failures.jsonl
```

Do not run that command under the current disabled policy.

## Reusable components and limitations

Reusable modules cover policy-gated HTTP behavior, offline parsers, append-only
checkpoints, normalization, validation, deduplication, geographic matching,
exports, auditing, and verification. GPU hardware does not accelerate network
latency, HTML transfer, robots checks, or server-imposed rate limits; a GPU is
relevant only to later numerical/ML workloads.

Remaining limitations are single-portal source bias, no verified publication
dates, sparse optional amenities, no property-level coordinates, noisy asking
prices, and incomplete evidence for removed historical listings. Expanding the
corpus requires a licensed feed or written permission, not technical bypasses.
