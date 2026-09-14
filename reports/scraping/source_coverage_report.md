# Source coverage and access policy

Only sources that pass robots, access-policy and extraction-quality checks may be enabled for live acquisition.

## Recovered data

| source | raw_rows | valid_rows | cities |
|---|---|---|---|
| mubawab.ma | 25433 | 13867 | 34 |

## Live adapter decisions

| Source | Status | Robots | Terms | Pilot | Reason |
|---|---|---|---|---|---|
| [data.gov.ma](https://data.gov.ma/) | enabled_reference_only | [allowed](https://data.gov.ma/robots.txt) | [policy](https://www.data.gov.ma/fr/node/14) | passed | CKAN API returned open-data metadata; no listing-level rows imported |
| [mubawab.ma](https://www.mubawab.ma/fr/) | disabled | [http_200](https://www.mubawab.ma/robots.txt) | [policy](https://www.mubawab.ma/fr/privacy) | not_run | Terms prohibit substantial database extraction/reuse; written license required |
| [agenz.ma](https://agenz.ma/fr) | disabled | [http_200](https://agenz.ma/robots.txt) | [policy](https://agenz.ma/fr/conditions-d-utilisation) | not_run | Robots blocks search/list/map routes and terms restrict data to personal use; request professional API |
| [marocannonces.com](https://www.marocannonces.com/) | disabled | [http_200](https://www.marocannonces.com/robots.txt) | [policy](https://www.marocannonces.com/conditions-utilisation.html) | not_run | robots.txt disallows all generic crawling and terms prohibit reuse |
| [avito.ma](https://www.avito.ma/) | disabled | [http_200](https://www.avito.ma/robots.txt) | not publicly verified | not_run | Cloudflare access challenge encountered and no clear automated-use permission; no bypass |
| [360annonces.com](https://www.360annonces.com/) | disabled | [http_200](https://www.360annonces.com/robots.txt) | [policy](https://www.360annonces.com/conditions-generales) | not_run | Terms prohibit collection without authorization |
| [sarouty.ma](https://www.sarouty.ma/) | disabled | [http_200](https://www.sarouty.ma/robots.txt) | [policy](https://www.sarouty.ma/en/terms-and-conditions/) | not_run | Public routes are robots-allowed with a 10-second crawl delay, but bulk database reuse permission is not established; written permission or a licensed feed is required |

Recovered data does not imply continuing permission to scrape its origin. Historical and recovery inputs are preserved separately from live adapter status.
