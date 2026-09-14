# MaisonDeLUX scraping pipeline V3

## Safe entry point

Open `notebooks/data_maisondelux_scraper_v3.ipynb`, leave `MODE = "PILOT"`,
and run all cells only after an authorized source feed has been enabled. The
notebook locates the repository root dynamically and uses only project-relative
paths. V3.1 intentionally has no enabled source: the preserved local evidence
is disabled so it cannot be mixed into a new collection by accident.

`FAST` and `FULL` always execute the pilot first. If any release check fails,
the run stops before `data/processed/maisondelux_clean_v3.csv` is created. The
existing `data/processed/maisondelux_clean.csv` is never modified.

## Source decision

The live access review was refreshed on 2026-09-04 and extended beyond the
original three portals. No candidate currently clears both the access/reuse gate
and the modeling-data gate:

| Source | Decision | Reason |
|---|---|---|
| Mubawab | disabled pending written permission | Its current conditions prohibit software-based extraction and substantial database extraction/reuse. |
| Agenz | disabled pending professional API/feed | Its conditions limit free site data to direct personal consultation and prohibit extraction outside that use. |
| Sarouty | disabled pending written clarification/feed | Public listing routes are allowed by robots with a 10-second crawl delay, but the public terms do not grant bulk database reuse permission. |
| Marsad Immo | conditional shortlist; disabled | Strong national inventory and an Enterprise API are advertised, but public terms prohibit mass extraction. A contract must cover listing-level modeling use. |
| marocain.investments | conditional shortlist; disabled | The public API is structured and traceable, but current terms prohibit derivative datasets/products. |
| Groupe Al Omrane | conditional authorized export; disabled | Nationwide first-party project catalogue, but no open reuse licence was found and unit-level modeling fields are uncertain. |

The ranked V3.1 audit and decision are in
`reports/scraping/v3/SOURCE_RECOVERY_V3_1.md` and
`reports/scraping/v3/source_recovery_v3_1.json`. `data.gov.ma` remains an open
reference source only; it does not provide current listing-level observations.
No login, CAPTCHA, 403, 429, or anti-bot control is bypassed.

## Architecture

- `ml/src/scraping_v3/schema.py`: exact V3 schema, URL, price, date, and tri-state parsing.
- `ml/src/scraping_v3/geography.py`: all 12 Morocco regions, city aliases, and strict neighborhood validation.
- `ml/src/scraping_v3/sources.py`: independent file/feed adapters plus an authorization-gated HTTP/JSON-LD collector.
- `ml/src/scraping_v3/checkpoints.py`: append-only JSONL checkpoints and stable resume keys.
- `ml/src/scraping_v3/normalization.py`: property-type contradiction rules, sale/rent classification, coordinates, surfaces, rooms, and amenities.
- `ml/src/scraping_v3/validation.py`: broad property-aware plausibility flags and four-level deduplication.
- `ml/src/scraping_v3/reporting.py`: quality metrics, distributions, missingness, and acceptance gates.
- `ml/src/scraping_v3/pipeline.py`: pilot-first orchestration, geographic balancing, raw/processed separation, and safe export.

The HTTP path processes seed URLs page-major, so every configured city/category
gets a first page before any receives a second. It extracts cards and structured
JSON-LD at Level 1. FAST enriches only the highest-missingness fraction of cards
(25% by default); FULL may enrich every detail page. Requests use timeouts,
bounded exponential retries, per-domain jittered delays, and stop immediately on
HTTP 401/403/429. Up to four independent sources can run concurrently; per-source
detail concurrency is capped at 15.

## Adding an authorized source

The preferred route is a licensed CSV, Parquet, JSON, or JSONL feed. Put it in
`data/input/authorized/`, set the matching entry's `enabled` value to `true` in
`config/scraping_v3.json`, and record the contract/feed identifier in
`authorization_reference`. Keep `preserved_local_evidence` false for every new
source-recovery run.

For written permission to scrape public pages, change that source's `kind` to
`live_html`, add geographically interleaved `search_urls` (use `{page}` for
pagination), and add CSS selectors where JSON-LD is incomplete. A live adapter
will still refuse to run without an authorization reference and a robots check.

Raw observations are appended under `data/raw/v3/`; per-source resume state is
under `data/checkpoints/v3/`. The checkpoint uses source/native ID first and
canonical URL second.

## V3.1 acceptance philosophy

The pilot target is 200 rows for the currently enabled source. A single strong
nationwide source is acceptable. For every modeling-valid row, traceability is
defined as `source AND (source_listing_id OR canonical URL)`; at least 90% must
pass, with 95% preferred. Price, city, region, and resolved property type target
99% availability, and surface targets 90%.

Publication date is important but non-blocking. Missing evidence remains null
with `publication_date_status = "unavailable"`; `scraped_at` is never used as a
substitute. Coordinates are also non-blocking. Bedrooms and bathrooms are
reported by property type rather than treated as universal requirements.

## Normalization and validation rules

The canonical dataset contains the 43 columns listed in
`ml/src/scraping_v3/schema.py`. Dates retain one of `exact`,
`relative_parsed`, `updated_date`, or `unavailable`; no collection timestamp is
used as a publication date. Coordinates are accepted only when source evidence
provides them. Amenities are `yes`, `no`, or `unknown`.

Property type uses source category plus title and description. Strong title
evidence can override an incorrect global category and records the contradiction
in `validation_reasons`. `Hay Riad` is explicitly protected from being mistaken
for a riad property. Bedrooms are null for terrain and non-residential commercial
types. Terrain bathrooms and zero-valued commercial bathroom placeholders are
also null; a meaningful positive office/shop bathroom count is retained.

Deduplication order is source/native ID, canonical URL, a conservative structured
fingerprint, then cross-source title similarity inside tight city/price/surface
blocks. The last level is marked `possible_duplicate_text` and is not silently
removed.

## Executed pilot (2026-09-04)

The bounded pilot used 500 rows from preserved local evidence and did not make
new listing-page requests.

| Metric | Result |
|---|---:|
| Clean modeling rows | 410 |
| Rejected rows | 83 |
| Confirmed duplicates | 15 |
| Sources | 1 |
| Regions | 11 |
| Cities | 32 |
| Property types | 11 |
| Largest city share | 12.20% |
| Publication-date availability | 0% |
| URL availability | 27.07% |
| Native-ID availability | 27.07% |

The property distribution includes apartments, duplexes, houses, studios,
villas, buildings, offices, riads, commercial premises, land, and shops. The
historical pilot failed the original release gate. Under V3.1, one source and no
verified publication dates would not block release, but its 27.07% row-level
URL/native-ID traceability still fails the new 90% gate. FAST/FULL therefore
remain blocked and the final V3 dataset has not been created.

The historical pilot results are in
`reports/scraping/v3/pilot_quality_report_v3.{json,md}`.

The V3.1 source-recovery result is `READY_FOR_FAST = NO`: no candidate was
authorized, so no live micro-pilot or manual 20-row QA sample was performed.

## Runtime expectations

- Current 500-row local pilot: about 10–15 seconds on this machine, including report/export work.
- Licensed local/API feeds: roughly 1–3 minutes for 15,000–30,000 rows and 3–8 minutes for 40,000–50,000 rows, excluding provider delivery latency.
- Authorized public HTML: source-dependent. With the conservative default delays and 25% detail enrichment, FAST can take tens of minutes to several hours; FULL can take several hours. Server policy and response latency dominate, not CPU/GPU speed.

These are engineering estimates, not promises. The notebook reports actual
elapsed time per adapter.
