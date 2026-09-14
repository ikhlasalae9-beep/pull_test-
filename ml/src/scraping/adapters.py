"""Source registry. Listing portals default to disabled without authorization."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from ml.src.scraping.base import PilotResult, SourceAdapter, SourcePolicy


class DisabledListingAdapter(SourceAdapter):
    def pilot(self) -> PilotResult:
        return PilotResult(self.policy.source, "disabled", "not_checked", "not_run", self.policy.reason)

    def collect(self, checkpoint: Path, limit: int | None = None) -> Iterable[dict[str, Any]]:
        raise PermissionError(f"{self.policy.source} is disabled: {self.policy.reason}")


class DataGovCkanReferenceAdapter(SourceAdapter):
    """Legal open-data reference discovery; never emits listing observations."""
    API_URL = "https://data.gov.ma/data/api/3/action/package_search?q=immobilier&rows=3"

    def pilot(self) -> PilotResult:
        try:
            response = self.client.get(self.API_URL)
            payload = response.json()
            records = [
                {"dataset_id": item.get("id"), "title": item.get("title"), "url": f"https://data.gov.ma/data/fr/dataset/{item.get('name')}", "role": "benchmark_or_reference_not_listing"}
                for item in payload.get("result", {}).get("results", [])
            ]
            return PilotResult(self.policy.source, "enabled_reference_only", "allowed", "passed", "CKAN API returned open-data metadata; no listing-level rows imported", http_status=response.status_code, records=records)
        except Exception as error:
            return PilotResult(self.policy.source, "disabled", "allowed", "failed", f"CKAN pilot failed: {type(error).__name__}: {error}")

    def collect(self, checkpoint: Path, limit: int | None = None) -> Iterable[dict[str, Any]]:
        return iter(())


POLICIES = [
    SourcePolicy("data.gov.ma", "https://data.gov.ma/", "https://data.gov.ma/robots.txt", "https://www.data.gov.ma/fr/node/14", True, "reference_only", "ODbL open-data API; reference/benchmark data only"),
    SourcePolicy("mubawab.ma", "https://www.mubawab.ma/fr/", "https://www.mubawab.ma/robots.txt", "https://www.mubawab.ma/fr/privacy", False, "none", "Terms prohibit substantial database extraction/reuse; written license required"),
    SourcePolicy("agenz.ma", "https://agenz.ma/fr", "https://agenz.ma/robots.txt", "https://agenz.ma/fr/conditions-d-utilisation", False, "none", "Robots blocks search/list/map routes and terms restrict data to personal use; request professional API"),
    SourcePolicy("marocannonces.com", "https://www.marocannonces.com/", "https://www.marocannonces.com/robots.txt", "https://www.marocannonces.com/conditions-utilisation.html", False, "none", "robots.txt disallows all generic crawling and terms prohibit reuse"),
    SourcePolicy("avito.ma", "https://www.avito.ma/", "https://www.avito.ma/robots.txt", None, False, "none", "Cloudflare access challenge encountered and no clear automated-use permission; no bypass"),
    SourcePolicy("360annonces.com", "https://www.360annonces.com/", "https://www.360annonces.com/robots.txt", "https://www.360annonces.com/conditions-generales", False, "none", "Terms prohibit collection without authorization"),
    SourcePolicy("sarouty.ma", "https://www.sarouty.ma/", "https://www.sarouty.ma/robots.txt", "https://www.sarouty.ma/en/terms-and-conditions/", False, "none", "Robots permits public listing routes with a 10-second crawl delay, but bulk database reuse permission is not established; written permission or a licensed feed is required"),
]


def adapters() -> list[SourceAdapter]:
    return [DataGovCkanReferenceAdapter(policy) if policy.source == "data.gov.ma" else DisabledListingAdapter(policy) for policy in POLICIES]
