# MaisonDeLUX V3.1 source recovery report

Audit date: 2026-09-04

Outcome: no source cleared the combined reuse, access, and data-quality screen. No live micro-pilot, FAST run, or FULL run was started. The earlier local evidence remains separate and is disabled in the V3.1 configuration.

## A. Candidate sources investigated

Each dimension is scored from 0 to 5 in this order: access/reuse feasibility, Morocco coverage, sale volume, structured quality, URL/ID traceability, geographic diversity, property-type diversity, and collection speed.

| Rank | Candidate | Mechanism and technical result | Robots / terms result | Estimated useful volume | Score / 40 | Decision |
|---:|---|---|---|---:|---:|---|
| 1 | Marsad Immo | Enterprise API and CSV exports; public site reachable | Public robots reserves training and API paths; CGU forbids mass extraction. Contract required. | 512,847 listings and 75 cities claimed | 37 | Conditional shortlist only |
| 2 | marocain.investments | Public JSON search API returned IDs, URLs, price, city, district, type, surface and first-seen date | Robots allows the catalogue/API interface, but Terms §§9–10 prohibit derivative datasets/products and grant only limited internal use | 24,767 API records reported | 35 | Rejected under current terms; written exception could qualify it |
| 3 | Groupe Al Omrane | First-party nationwide public project catalogue; HTML reachable | Project routes allowed by robots, but downloadable commercial documents are restricted and no open reuse licence was found | 521 project pages reported | 28 | Conditional authorized export only; weak unit-level fit |
| 4 | Yakeey | Public sale pages are structured and traceable | CGU Article 12 prohibits extracting, compiling, sharing, or exploiting platform content | 2,377 sale properties reported | 28 | Rejected |
| 5 | 360annonces | Public HTML contains price, surface, city, type and canonical listing links | Robots blocks `/api`; CGU prohibits collecting data without authorization | 515 sale properties reported | 26 | Rejected |
| 6 | Lesiteimmo API | Documented REST/JSON API with stable IDs | API key and subscription required; Moroccan inventory could not be established | Unknown for Morocco | 25 | Not selected |
| 7 | data.gov.ma | Public CKAN API, ODbL reuse licence | Permitted and technically accessible | No current listing-level sale observations found | 25 | Reference only |
| 8 | Kaggle `housing-data-in-morocco` | Direct downloadable CSV | Licence says “Other” without an actual grant in the description | 4,675 rows, seven cities | 20 | Rejected: zero URL/native-ID traceability and unclear provenance/licence |
| 9 | AnnoncesMaroc | Public HTML | Database/content rights reserved; single-computer copy limitation; robots content signal says reference use and no AI training | Unknown | 21 | Rejected |
| 10 | OpenSooq Morocco | Public marketplace | Terms prohibit robot, spider, scraping and data-mining access | Unknown | 23 | Rejected |
| 11 | 1immo | Public HTML | Site content is reserved for personal access/use; no extraction grant | Unknown | 20 | Rejected |
| 12 | Third-party scraper APIs (Apify, Parse.bot, PropAPIS) | Paid structured APIs | Vendor access does not establish upstream portal reuse rights | Potentially large | 29 technical, 0 legal | Rejected |

Mubawab, Agenz, Sarouty, Avito, and MarocAnnonces retain their earlier disabled decisions in the main policy audit. No authentication, CAPTCHA, 403, API restriction, or rate limit was bypassed.

## B. Sources rejected and why

High-volume portals and aggregators were rejected where terms expressly prohibit extraction or derivative datasets. Open data and downloadable community datasets were rejected when they lacked listing rows, an explicit licence, source provenance, or the required identifier coverage. Paid scraper wrappers were not treated as permission from the underlying publisher.

## C. Sources accepted

None. The configuration now contains disabled, authorization-ready feed entries for the three conditional shortlist candidates. Enabling one requires a written contract/export reference, not merely a reachable URL.

## D. Micro-pilot metrics

No accepted source exists, so no 100–300-row micro-pilot was run. Reporting zeros as if a pilot had occurred would be misleading.

| Accepted source | Raw | Valid | Rejected | Duplicates | Regions | Cities | Property types |
|---|---:|---:|---:|---:|---:|---:|---:|
| None | not run | not run | not run | not run | not run | not run | not run |

## E. Manual quality findings

No manual 20-row sample was performed because manual QA applies only after a source passes the legal/access gate. Limited technical probes were used solely to establish schema and accessibility; they were not retained as modeling data.

## F. URL / ID traceability

There is no accepted V3.1 corpus to score. The previously preserved 410-row V3 pilot is reported separately: 27.07% had `source AND (source_listing_id OR url)`, well below the new 90% gate. It is not mixed into V3.1.

## G. Date availability

No accepted V3.1 corpus exists. Publication date is now explicitly non-blocking. Missing dates remain null with `publication_date_status = "unavailable"`; collection time is never substituted.

## H. Geographic coverage

No accepted corpus. The best conditional option, Marsad, claims 75-city national coverage; Al Omrane exposes nationwide projects. Neither claim was imported or treated as verified row-level coverage.

## I. Property-type coverage

No accepted corpus. The V3.1 normalizer now nulls bedrooms for terrain, offices, shops, and commercial premises, and nulls non-applicable bathroom placeholders while preserving meaningful positive commercial bathroom counts.

## J. Recommended FAST target

Do not launch FAST now. After a licensed source passes a 100–300-row micro-pilot, keep the existing 20,000-row FAST target. A single nationwide source is sufficient; source count is not a release gate.

## K. Estimated FAST runtime

Conditional estimate for a structured licensed API/feed: approximately 3–10 minutes for 20,000 rows, excluding provider delivery latency. Replace this estimate with measured micro-pilot throughput before launch.

## Audit evidence

- Marsad Immo: [product/coverage page](https://marsadimmo.com/) and [CGU](https://marsadimmo.com/cgu).
- marocain.investments: [public search API](https://marocain.investments/api/public/listings/search), [terms](https://marocain.investments/legal/terms), and [robots policy](https://marocain.investments/robots.txt).
- Groupe Al Omrane: [nationwide project catalogue](https://www.alomrane.gov.ma/Nos-produits/Projets) and [robots policy](https://www.alomrane.gov.ma/robots.txt).
- Yakeey: [Morocco sale catalogue](https://yakeey.com/fr-ma/achat/biens/maroc) and [CGU](https://yakeey.com/fr-ma/cgu).
- 360annonces: [sale catalogue](https://www.360annonces.com/acheter), [general conditions](https://www.360annonces.com/conditions-generales), and [robots policy](https://www.360annonces.com/robots.txt).
- Lesiteimmo: [API documentation](https://api.lesiteimmo.com/doc).
- data.gov.ma: [API guide](https://data.gov.ma/fr/guide-api) and [ODbL reuse terms](https://www.data.gov.ma/fr/node/14).
- Kaggle: [`housing-data-in-morocco` dataset page](https://www.kaggle.com/datasets/yassinesadiki/housing-data-in-morocco).
- AnnoncesMaroc: [site conditions](https://www.annoncesmaroc.ma/page/conditions) and [robots policy](https://www.annoncesmaroc.ma/robots.txt).
- OpenSooq Morocco: [terms of use](https://ma.opensooq.com/en/termOfUse) and [robots policy](https://ma.opensooq.com/robots.txt).
- 1immo: [CGV](https://1immo.ma/page/CGV).

Robots accessibility was treated only as a technical signal, never as a substitute for a reuse licence. The audit used no protected endpoint, account, CAPTCHA bypass, or retained listing corpus.

## Decision

`READY_FOR_FAST = NO`

Reasons: zero accepted sources, therefore no per-source micro-pilot, no 20-row manual QA sample, and no demonstrated 90% traceability or core-field gate compliance on newly authorized data.
