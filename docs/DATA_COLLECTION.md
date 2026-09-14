# Data collection and source policy

## Policy gate

Every adapter implements the common contract in `ml/src/scraping/base.py`. An adapter may collect listing rows only after all of these pass:

1. robots policy permits the exact route;
2. terms and database-reuse conditions permit automated extraction;
3. no login, CAPTCHA, access-control, rate-limit, or anti-bot bypass is needed;
4. a bounded pilot passes manual field validation;
5. the authorization basis is recorded.

Robots allowance alone is not database-reuse permission. The client uses per-domain delays, timeouts, exponential backoff, `Retry-After`, and a circuit breaker for 401/403/429. Checkpoints are append-only; Excel is generated only after collection.

## Current adapter decisions (checked 2026-09-02)

| Source | Decision | Evidence/reason |
|---|---|---|
| [data.gov.ma](https://data.gov.ma/) | enabled for reference metadata only | Public [CKAN API](https://data.gov.ma/fr/guide-api); [ODbL terms](https://www.data.gov.ma/fr/node/14). It does not provide current listing-level observations. |
| [Mubawab](https://www.mubawab.ma/) | disabled | [robots.txt](https://www.mubawab.ma/robots.txt) mostly permits public pages, but [conditions/privacy](https://www.mubawab.ma/fr/privacy) restrict substantial extraction/reuse and extraction software. Written license required. |
| [Agenz](https://agenz.ma/fr) | disabled | [robots.txt](https://agenz.ma/robots.txt) blocks search/list/map routes; [terms](https://agenz.ma/fr/conditions-d-utilisation) restrict copying and point to professional services/APIs. |
| [MarocAnnonces](https://www.marocannonces.com/) | disabled | [robots.txt](https://www.marocannonces.com/robots.txt) disallows generic crawlers; [terms](https://www.marocannonces.com/conditions-utilisation.html) prohibit reproduction/derivatives. |
| [Avito.ma](https://www.avito.ma/) | disabled | Cloudflare managed challenges were encountered and no clear bulk-use permission was found. No bypass attempted. |
| [360annonces](https://www.360annonces.com/) | disabled | [robots.txt](https://www.360annonces.com/robots.txt) allows public pages but [conditions](https://www.360annonces.com/conditions-generales) prohibit collection without authorization. |
| [Sarouty](https://www.sarouty.ma/) | disabled | Public listing routes are robots-allowed with a 10-second crawl delay, but the [terms](https://www.sarouty.ma/en/terms-and-conditions/) do not establish permission for bulk database reuse. Written permission or a licensed feed is required. |

The recovered `ml/scraping/` package is retained for engineering evidence and offline parser tests. Its live Mubawab crawl must not be executed without a documented authorization reference.

## Legitimate reference/benchmark sources

- `data.gov.ma` provides regional rent statistics and postal locality/neighborhood references under ODbL.
- Bank Al-Maghrib/ANCFCC IPAI publications provide official transaction-price benchmarks; no open bulk-redistribution license was located, so they are not copied into the listing corpus.
- GeoNames supplies populated-place coordinates/aliases under CC BY 4.0.
- geoBoundaries gbOpen supplies the map polygons used here; its Morocco layer is OSM-derived ODbL and represents a 2017 boundary vintage.

## Operational commands

```bash
python -m ml.src.scraping.pilot
python -m ml.src.geography.build_reference
python -m ml.src.pipeline
```

The pipeline deliberately stops at the recovered lawful data volume. It does not fabricate rows or evade restrictions to reach a numeric target.
