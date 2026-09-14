import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scrapy import Spider
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse, Request
from scrapy.settings import Settings

from ml.scraping.maisondelux_scraper.middlewares import (
    ConservativeRetryMiddleware,
    retry_backoff_seconds,
)
from ml.scraping.maisondelux_scraper.persistence import CheckpointCsvStore
from ml.scraping.maisondelux_scraper.rate_limit import active_cooldown, parse_retry_after
from ml.scraping.maisondelux_scraper.spiders.mubawab import (
    CITY_SEEDS,
    extract_dom_evidence,
    find_real_estate_listing,
    jsonld_evidence,
)
from ml.src.data_schema import SCHEMA_V3_COLUMNS, build_v3_record


JSON_LD = {
    "@context": "https://schema.org",
    "@type": "RealEstateListing",
    "url": "https://www.mubawab.ma/fr/a/98765/appartement-jsonld",
    "name": "Titre JSON-LD",
    "description": "Description JSON-LD avec terrasse",
    "datePosted": "2026-08-10",
    "offers": {"@type": "Offer", "price": 1_500_000, "priceCurrency": "MAD"},
    "itemOffered": {
        "@type": "Apartment",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Casablanca",
            "streetAddress": "Maârif, Casablanca",
        },
        "numberOfRooms": 3,
        "numberOfBedrooms": 2,
        "numberOfBathroomsTotal": 1,
        "floorSize": {"@type": "QuantitativeValue", "value": 90, "unitCode": "MTR"},
        "geo": {"latitude": 33.58, "longitude": -7.63},
    },
    "seller": {"@type": "RealEstateAgent", "name": "Agence Exemple"},
}


def response_for(body: str) -> HtmlResponse:
    return HtmlResponse(
        url="https://www.mubawab.ma/fr/a/98765/appartement-dom",
        body=body.encode("utf-8"),
        encoding="utf-8",
    )


class JsonLdParserTests(unittest.TestCase):
    def test_jsonld_is_primary_and_complete(self):
        html = f"""
        <html><head>
          <meta name="description" content="Description DOM contradictoire">
          <script type="application/ld+json">{json.dumps(JSON_LD)}</script>
        </head><body><h1>Titre DOM contradictoire</h1></body></html>
        """
        response = response_for(html)
        evidence = jsonld_evidence(find_real_estate_listing(response))

        self.assertEqual(evidence["title_raw"], "Titre JSON-LD")
        self.assertEqual(evidence["description_raw"], "Description JSON-LD avec terrasse")
        self.assertEqual(evidence["price_value"], 1_500_000)
        self.assertEqual(evidence["currency"], "MAD")
        self.assertEqual(evidence["city"], "Casablanca")
        self.assertEqual(evidence["property_type"], "appartement")
        self.assertEqual(evidence["surface_total_m2"], 90)
        self.assertEqual(evidence["rooms"], 3)
        self.assertEqual(evidence["bedrooms"], 2)
        self.assertEqual(evidence["bathrooms"], 1)
        self.assertEqual(evidence["seller_type"], "AGENCY")
        self.assertEqual(evidence["seller_name"], "Agence Exemple")
        self.assertEqual((evidence["latitude"], evidence["longitude"]), (33.58, -7.63))

        record = build_v3_record(
            {
                "native_id": "98765",
                "url": JSON_LD["url"],
                "source_category": "appartements à vendre",
                "transaction_type": "SALE",
                **evidence,
            }
        )
        self.assertEqual(record["seller_name"], "Agence Exemple")
        self.assertEqual(record["listing_date"], "2026-08-10T00:00:00+00:00")

    def test_missing_jsonld_does_not_invent_core_values(self):
        response = response_for("<html><body><h1>Annonce sans données</h1></body></html>")
        self.assertIsNone(find_real_estate_listing(response))
        self.assertEqual(jsonld_evidence(None), {})


class DomEnrichmentTests(unittest.TestCase):
    def test_only_explicit_dom_evidence_is_enriched(self):
        html = """
        <html><head><time datetime="2026-08-11"></time></head><body>
          <span class="locationHint">Maârif, Casablanca</span>
          <div class="adMainFeature">
            <p class="adMainFeatureContentLabel">Étage du bien</p>
            <p class="adMainFeatureContentValue">4ème</p>
          </div>
          <div class="adMainFeature">
            <p class="adMainFeatureContentLabel">Etat</p>
            <p class="adMainFeatureContentValue">Bon état / habitable</p>
          </div>
          <div class="adFeature"><p>Ascenseur</p></div>
          <div class="adFeature"><p>Garage</p><p>1 place</p></div>
          <p>Le texte libre évoque une piscine hypothétique.</p>
        </body></html>
        """
        evidence = extract_dom_evidence(response_for(html), "Casablanca")
        self.assertEqual(evidence["quartier"], "Maârif")
        self.assertEqual(evidence["floor"], 4)
        self.assertEqual(evidence["condition"], "Bon état / habitable")
        self.assertTrue(evidence["elevator"])
        self.assertTrue(evidence["garage"])
        self.assertNotIn("pool", evidence)
        self.assertEqual(evidence["listing_date"], "2026-08-11")


class CheckpointTests(unittest.TestCase):
    def test_resume_upgrades_schema_preserves_row_and_deduplicates_native_id(self):
        old_columns = [column for column in SCHEMA_V3_COLUMNS if column != "seller_name"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=old_columns)
                writer.writeheader()
                writer.writerow(
                    {
                        "listing_id": "mubawab.ma:native:98765",
                        "source": "mubawab.ma",
                        "url": "https://www.mubawab.ma/fr/a/98765/ancien-slug",
                    }
                )

            store = CheckpointCsvStore(path)
            store.open()
            self.assertEqual(store.existing_rows, 1)
            duplicate = build_v3_record(
                {
                    "native_id": "98765",
                    "url": "https://www.mubawab.ma/fr/a/98765/nouveau-slug",
                    "transaction_type": "SALE",
                }
            )
            self.assertFalse(store.append(duplicate))

            new_record = build_v3_record(
                {
                    "native_id": "12345",
                    "url": "https://www.mubawab.ma/fr/a/12345/nouvelle-annonce",
                    "transaction_type": "SALE",
                }
            )
            self.assertTrue(store.append(new_record))
            store.close()

            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
            self.assertEqual(reader.fieldnames, SCHEMA_V3_COLUMNS)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["listing_id"], "mubawab.ma:native:98765")


class RateLimitPolicyTests(unittest.TestCase):
    def test_retry_backoff_is_exponential_and_capped(self):
        self.assertEqual(retry_backoff_seconds(1, base=10, maximum=60), 10)
        self.assertEqual(retry_backoff_seconds(2, base=10, maximum=60), 20)
        self.assertEqual(retry_backoff_seconds(5, base=10, maximum=60), 60)

    def test_retry_after_seconds(self):
        self.assertEqual(parse_retry_after("120"), 120)
        self.assertIsNone(parse_retry_after("not-a-date"))

    def test_http_429_persists_cooldown_and_closes_without_retry(self):
        class Stats:
            def __init__(self):
                self.values = {}

            def inc_value(self, key):
                self.values[key] = self.values.get(key, 0) + 1

            def set_value(self, key, value):
                self.values[key] = value

        class Engine:
            def __init__(self):
                self.closed = None

            def close_spider(self, spider, reason):
                self.closed = (spider, reason)

        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "cooldown.json"
            settings = Settings({
                "RATE_LIMIT_STATE_PATH": str(marker),
                "RATE_LIMIT_COOLDOWN_SECONDS": 900,
            })
            spider = Spider(name="rate-limit-test")
            crawler = SimpleNamespace(
                settings=settings,
                stats=Stats(),
                engine=Engine(),
                spider=spider,
            )
            middleware = ConservativeRetryMiddleware(crawler)
            request = Request("https://www.mubawab.ma/fr/a/1/test")
            response = HtmlResponse(
                url=request.url,
                status=429,
                headers={"Retry-After": "1200"},
                request=request,
            )

            with self.assertRaises(IgnoreRequest):
                middleware.process_response(request, response)

            self.assertEqual(crawler.stats.values["rate_limit/http_429"], 1)
            self.assertTrue(crawler.engine.closed[1].startswith("rate_limited_429"))
            cooldown = active_cooldown(marker)
            self.assertIsNotNone(cooldown)
            self.assertGreater(cooldown["remaining_seconds"], 1100)

    def test_transient_http_error_builds_delayed_retry(self):
        class Stats:
            def __init__(self):
                self.values = {}

            def inc_value(self, key):
                self.values[key] = self.values.get(key, 0) + 1

        settings = Settings({
            "RETRY_HTTP_CODES": [503],
            "RETRY_BACKOFF_BASE": 10,
            "RETRY_BACKOFF_MAX": 60,
        })
        spider = Spider(name="retry-test")
        crawler = SimpleNamespace(settings=settings, stats=Stats(), spider=spider)
        spider.crawler = crawler
        middleware = ConservativeRetryMiddleware(crawler)
        request = Request("https://www.mubawab.ma/fr/a/1/test")
        response = HtmlResponse(url=request.url, status=503, request=request)

        with patch(
            "twisted.internet.task.deferLater",
            side_effect=lambda reactor, delay, callback: (delay, callback()),
        ):
            delay, retry_request = middleware.process_response(request, response)

        self.assertEqual(delay, 10)
        self.assertEqual(retry_request.meta["retry_times"], 1)
        self.assertTrue(retry_request.dont_filter)
        self.assertEqual(crawler.stats.values["retry/count"], 1)

    def test_city_seeds_are_public_first_pages_without_blocked_colon_pagination(self):
        self.assertGreaterEqual(len(CITY_SEEDS), 8)
        urls = [url for _, url in CITY_SEEDS]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(":p:" not in url for url in urls))
        self.assertTrue(any("f%C3%A8s" in url for url in urls))
        self.assertTrue(any("k%C3%A9nitra" in url for url in urls))
        self.assertTrue(any("sal%C3%A9" in url for url in urls))
        self.assertTrue(any("t%C3%A9touan" in url for url in urls))


if __name__ == "__main__":
    unittest.main()
