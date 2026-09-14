import json
from pathlib import Path

from ml.src.scraping_v3.checkpoints import JsonlCheckpoint
from ml.src.scraping_v3.geography import canonical_city, region_for_city, valid_neighborhood
from ml.src.scraping_v3.normalization import infer_property_type, normalize_record
from ml.src.scraping_v3.reporting import build_report
from ml.src.scraping_v3.schema import V3_COLUMNS, parse_price_mad, parse_publication_date
from ml.src.scraping_v3.sources import (
    SourceSpec,
    collect_file_source,
    collect_live_source,
    parse_detail_html,
)
from ml.src.scraping_v3.validation import mark_duplicates, validate_record


def test_required_v3_schema_is_complete():
    required = {
        "listing_id", "source", "source_listing_id", "url", "scraped_at",
        "publication_date", "publication_date_status", "transaction_type", "region",
        "city", "neighborhood", "latitude", "longitude", "property_type", "surface_m2",
        "land_surface_m2", "built_surface_m2", "bedrooms", "bathrooms", "floor",
        "total_floors", "price_mad", "price_raw", "price_per_m2", "furnished_status",
        "parking", "balcony", "terrace", "garden", "pool", "elevator", "garage",
        "security", "air_conditioning", "sea_view", "title_raw", "description_raw",
        "location_raw", "validation_status", "validation_reasons",
        "deduplication_status", "duplicate_of", "source_record_path",
    }
    assert required == set(V3_COLUMNS)


def test_price_and_publication_date_parsing_is_honest():
    assert parse_price_mad("1,25 million MAD")[0] == 1_250_000
    assert parse_price_mad("12 000 DH/m²")[0] is None
    assert parse_price_mad("250 000 EUR")[1] == "non_mad_currency"
    date, status = parse_publication_date("il y a 2 jours", "2026-09-04T12:00:00+00:00")
    assert date.startswith("2026-09-02") and status == "relative_parsed"
    assert parse_publication_date(None, "2026-09-04T12:00:00+00:00") == (None, "unavailable")


def test_property_type_overrides_bad_global_apartment_label():
    property_type, reasons = infer_property_type({
        "property_type": "appartement",
        "title_raw": "Villa moderne à vendre avec jardin",
    })
    assert property_type == "villa"
    assert "property_type_contradiction:appartement->villa" in reasons
    assert infer_property_type({"title_raw": "Appartement à vendre à Hay Riad"})[0] == "appartement"
    assert infer_property_type({"property_type": "appartement", "title_raw": "Appartement à vendre à Riad El Oulfa"})[0] == "appartement"
    assert infer_property_type({"property_type": "appartement", "title_raw": "Riad traditionnel à rénover"})[0] == "riad"
    assert infer_property_type({"property_type": "appartement", "title_raw": "Appartement proche terrain de sport"})[0] == "appartement"
    assert infer_property_type({"property_type": "appartement", "title_raw": "Appartement ou bureau à vendre"})[0] == "appartement"
    assert infer_property_type({"property_type": "appartement", "title_raw": "Vends immeuble complet avec studios"})[0] == "immeuble"
    assert infer_property_type({"property_type": "appartement", "title_raw": "Appartement duplex à vendre"})[0] == "duplex"


def test_neighborhood_filter_rejects_sentence_fragments():
    assert valid_neighborhood("Maârif", "Casablanca")
    assert not valid_neighborhood("À quelques minutes du centre-ville", "Casablanca")
    assert not valid_neighborhood("Dans un quartier idéal proche de la mer", "Agadir")
    assert not valid_neighborhood("proximité de la zone industrielle de", "Berrechid")
    assert not valid_neighborhood("beautiful house located in", "Chefchaouen")
    assert canonical_city("Casa") == "Casablanca"
    assert region_for_city("Dakhla") == "Dakhla-Oued Ed-Dahab"


def test_jsonld_detail_recovers_date_coordinates_and_type():
    payload = {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "url": "https://example.test/annonce/12345",
        "name": "Riad à vendre",
        "description": "Riad avec terrasse",
        "datePosted": "2026-09-01",
        "offers": {"price": 3500000, "priceCurrency": "MAD"},
        "itemOffered": {
            "@type": "House",
            "address": {"addressLocality": "Marrakech", "streetAddress": "Médina, Marrakech"},
            "floorSize": {"value": 180},
            "numberOfBedrooms": 4,
            "geo": {"latitude": 31.63, "longitude": -7.99},
        },
    }
    html = f'<script type="application/ld+json">{json.dumps(payload)}</script>'
    raw = parse_detail_html(html, payload["url"], "licensed.test")
    row = normalize_record(raw, "fixture.html")
    assert row["publication_date_status"] == "exact"
    assert row["property_type"] == "riad"
    assert row["city"] == "Marrakech"
    assert row["latitude"] == 31.63
    assert row["source_listing_id"] == "12345"


def test_embedded_hydration_json_recovers_publication_date():
    payload = {
        "props": {"listing": {
            "listingId": "A-77", "canonicalUrl": "https://example.test/property/7788",
            "title": "Bureau à vendre", "description": "Plateau bureau",
            "publishedAt": "2026-08-31T10:00:00Z", "price": 900000,
            "currency": "MAD", "city": "Rabat", "district": "Agdal",
            "surface": 75, "propertyType": "Office",
        }}
    }
    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
    raw = parse_detail_html(html, "https://example.test/fallback", "licensed.test")
    row = normalize_record(raw, "hydration.html")
    assert row["publication_date_status"] == "exact"
    assert row["source_listing_id"] == "A-77"
    assert row["property_type"] == "bureau"
    assert row["surface_m2"] == 75


def test_checkpoint_resume_and_multilevel_dedup(tmp_path: Path):
    checkpoint = JsonlCheckpoint(tmp_path / "rows.jsonl")
    row = {"source": "test", "source_listing_id": "1", "url": "https://example.test/a/1"}
    assert checkpoint.append_batch([row]) == 1
    assert JsonlCheckpoint(checkpoint.path).append_batch([row]) == 0

    left = normalize_record({
        "source": "one", "source_listing_id": "1", "title": "Villa à vendre",
        "transaction_type": "sale", "price_mad": 2_000_000, "surface_m2": 200,
        "city": "Agadir", "neighborhood": "Founty",
    })
    right = dict(left)
    right["listing_id"] = "changed"
    counts = mark_duplicates([left, right])
    assert counts["source_id"] == 1
    assert right["deduplication_status"] == "duplicate_source_id"


def test_sale_validation_and_tri_state_unknown():
    row = normalize_record({
        "source": "licensed.test", "id": "9", "url": "https://licensed.test/listing/9",
        "title": "Maison à vendre", "transaction_type": "sale", "price_mad": 1_200_000,
        "surface_m2": 120, "city": "Rabat", "neighborhood": "Agdal",
    })
    status, reasons = validate_record(row)
    assert status in {"valid", "warning"}
    assert "rental_listing" not in reasons
    assert row["parking"] == "unknown"
    rental = dict(row, transaction_type="rent")
    assert "rental_listing" in validate_record(rental)[1]


def test_non_applicable_room_counts_are_null():
    terrain = normalize_record({
        "source": "licensed.test", "id": "land-1", "url": "https://licensed.test/listing/land-1",
        "title": "Terrain à vendre", "transaction_type": "sale", "price_mad": 800_000,
        "surface_m2": 500, "city": "Rabat", "bedrooms": 0, "bathrooms": 0,
    })
    office = normalize_record({
        "source": "licensed.test", "id": "office-1", "url": "https://licensed.test/listing/office-1",
        "title": "Bureau à vendre", "transaction_type": "sale", "price_mad": 900_000,
        "surface_m2": 75, "city": "Rabat", "bedrooms": 3, "bathrooms": 1,
    })
    assert terrain["bedrooms"] is None and terrain["bathrooms"] is None
    assert office["bedrooms"] is None and office["bathrooms"] == 1


def test_v31_traceability_gate_and_publication_date_is_non_blocking():
    rows = []
    for index in range(100):
        row = normalize_record({
            "source": "licensed.test", "id": f"id-{index}",
            "url": f"https://licensed.test/listing/{index}",
            "title": "Appartement à vendre", "transaction_type": "sale",
            "price_mad": 1_000_000 + index, "surface_m2": 80,
            "city": "Rabat", "neighborhood": "Agdal", "bedrooms": 2, "bathrooms": 1,
        })
        row["validation_status"] = "valid"
        row["deduplication_status"] = "unique"
        rows.append(row)
    report = build_report(100, rows, {"licensed.test": "loaded:100"}, "PILOT")
    assert report["acceptance_checks"]["M_traceability_90_percent"]
    assert report["informational_checks"]["publication_date_available_percent"] == 0
    assert report["informational_checks"]["publication_date_is_non_blocking"]
    assert "H_publication_date_retrieved" not in report["acceptance_checks"]
    assert "region" in report["missing_percent"]
    assert "property_type" in report["missing_percent"]

    for row in rows[:11]:
        row["url"] = None
        row["source_listing_id"] = None
    failed_traceability = build_report(100, rows, {"licensed.test": "loaded:100"}, "PILOT")
    assert failed_traceability["informational_checks"]["traceability_percent"] == 89.0
    assert not failed_traceability["acceptance_checks"]["M_traceability_90_percent"]


def test_live_source_requires_authorization(tmp_path: Path):
    spec = SourceSpec(name="portal.test", kind="live_html", enabled=True, search_urls=["https://example.test/listings"])
    try:
        collect_live_source(spec, JsonlCheckpoint(tmp_path / "x.jsonl"), mode="PILOT", limit=1)
    except PermissionError as error:
        assert "authorization" in str(error)
    else:
        raise AssertionError("live collection must be authorization-gated")


def test_authorized_feed_requires_contract_reference(tmp_path: Path):
    feed = tmp_path / "feed.csv"
    feed.write_text("id,price\n1,1000000\n", encoding="utf-8")
    spec = SourceSpec(
        name="licensed-feed.test",
        kind="authorized_feed",
        enabled=True,
        input_paths=[feed.name],
    )
    try:
        collect_file_source(spec, tmp_path)
    except PermissionError as error:
        assert "authorization" in str(error)
    else:
        raise AssertionError("authorized feeds must require a contract/export reference")
