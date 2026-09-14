"""Canonical listing normalization and conservative neighborhood repair."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit

from ml.src.data_schema import (
    CITY_ALIASES,
    build_v3_record,
    clean_raw_text,
    normalize_for_matching,
    valid_neighborhood,
)


CANONICAL_COLUMNS = [
    "listing_id", "source", "source_listing_id", "city", "neighborhood", "region",
    "latitude", "longitude", "surface_m2", "bedrooms", "bathrooms",
    "furnished_status", "parking", "balcony", "sea_view", "price_mad",
    "price_per_m2", "property_type", "transaction_type", "publication_date",
    "publication_date_status", "scraped_at", "url", "validation_status",
    "validation_reasons", "deduplication_status", "duplicate_of", "title_raw",
    "price_raw", "location_raw", "details_raw", "source_record_path",
]


def tri_state(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    normalized = normalize_for_matching(value)
    if normalized in {"yes", "oui", "true", "1", "furnished", "meuble"}:
        return "yes"
    if normalized in {"no", "non", "false", "0", "unfurnished", "non meuble"}:
        return "no"
    return "unknown"


def furnished_status(value: Any) -> str:
    state = tri_state(value)
    return {"yes": "furnished", "no": "unfurnished", "unknown": "unknown"}[state]


def build_neighborhood_vocabulary(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    display: dict[tuple[str, str], str] = {}
    for row in rows:
        city = clean_raw_text(row.get("city"))
        neighborhood = clean_raw_text(row.get("neighborhood") or row.get("quartier"))
        if not city or not valid_neighborhood(neighborhood):
            continue
        city_key = normalize_for_matching(city)
        name_key = normalize_for_matching(neighborhood)
        counts[city_key][name_key] += 1
        display[(city_key, name_key)] = neighborhood
    result: dict[str, dict[str, str]] = {}
    for city_key, candidates in counts.items():
        result[city_key] = {
            key: display[(city_key, key)] for key, count in candidates.items()
            if count >= 2 and len(key) >= 4
        }
    return result


def repair_neighborhood(city: Any, current: Any, url: Any, title: Any,
                        vocabulary: dict[str, dict[str, str]]) -> tuple[str | None, str]:
    if valid_neighborhood(current):
        return clean_raw_text(current), "source_location"
    city_key = normalize_for_matching(city)
    candidates = vocabulary.get(city_key, {})
    evidence = normalize_for_matching(" ".join(filter(None, [clean_raw_text(title), unquote(urlsplit(clean_raw_text(url) or "").path.replace("-", " "))])))
    if not evidence:
        return None, "missing"
    matches = [(len(key.split()), len(key), display) for key, display in candidates.items() if re.search(rf"(?:^| )({re.escape(key)})(?: |$)", evidence)]
    if not matches:
        return None, "unresolved"
    matches.sort(reverse=True)
    best = matches[0]
    if len(matches) > 1 and matches[1][:2] == best[:2] and normalize_for_matching(matches[1][2]) != normalize_for_matching(best[2]):
        return None, "ambiguous"
    return best[2], "url_or_title_vocabulary_match"


def canonical_from_evidence(evidence: dict[str, Any], source_path: str,
                            neighborhood_vocabulary: dict[str, dict[str, str]] | None = None) -> dict[str, Any]:
    record = build_v3_record(evidence)
    native_id = clean_raw_text(evidence.get("native_id") or evidence.get("source_listing_id"))
    if native_id is None and record["listing_id_strategy"] == "native_id":
        native_id = record["listing_id"].rsplit(":", 1)[-1]
    neighborhood, neighborhood_reason = repair_neighborhood(
        record.get("city"), evidence.get("neighborhood") or record.get("quartier"),
        record.get("url"), record.get("title_raw"), neighborhood_vocabulary or {},
    )
    publication_date = record.get("listing_date")
    publication_status = "known" if publication_date else "unknown"
    price_mad = record.get("price_mad")
    surface = record.get("surface_total_m2")
    result = {
        "listing_id": record["listing_id"], "source": record["source"],
        "source_listing_id": native_id, "city": record.get("city"),
        "neighborhood": neighborhood, "region": evidence.get("region"),
        "latitude": record.get("latitude"), "longitude": record.get("longitude"),
        "surface_m2": surface, "bedrooms": record.get("bedrooms"),
        "bathrooms": record.get("bathrooms"),
        "furnished_status": furnished_status(record.get("furnished")),
        "parking": tri_state(record.get("parking")), "balcony": tri_state(record.get("balcony")),
        "sea_view": tri_state(record.get("sea_view")), "price_mad": price_mad,
        "price_per_m2": round(float(price_mad) / float(surface), 2) if price_mad and surface and float(surface) > 0 else None,
        "property_type": record.get("property_type"),
        "transaction_type": record.get("transaction_type", "UNKNOWN").casefold(),
        "publication_date": publication_date, "publication_date_status": publication_status,
        "scraped_at": record.get("scraped_at"), "url": record.get("url"),
        "validation_status": record.get("validation_status", "INVALID").casefold(),
        "validation_reasons": record.get("validation_reasons") or "",
        "deduplication_status": "unique", "duplicate_of": None,
        "title_raw": record.get("title_raw"), "price_raw": record.get("raw_price_text"),
        "location_raw": record.get("location_raw"), "details_raw": record.get("details_raw"),
        "source_record_path": source_path,
    }
    if neighborhood_reason not in {"source_location", "url_or_title_vocabulary_match"}:
        reasons = [reason for reason in result["validation_reasons"].split("|") if reason]
        reasons.append("missing_or_invalid_neighborhood")
        result["validation_reasons"] = "|".join(dict.fromkeys(reasons))
        if result["validation_status"] == "valid":
            result["validation_status"] = "warning"
    return {column: result.get(column) for column in CANONICAL_COLUMNS}
