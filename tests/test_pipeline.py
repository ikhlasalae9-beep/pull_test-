from copy import deepcopy
from pathlib import Path

import pandas as pd

from ml.src.cleaning.normalization import CANONICAL_COLUMNS, repair_neighborhood
from ml.src.data_schema import canonicalize_url, normalize_iso_date, valid_neighborhood
from ml.src.geography.matching import MoroccoGeography
from ml.src.validation.deduplication import mark_duplicates
from ml.src.validation.rules import validate_canonical


ROOT = Path(__file__).resolve().parents[1]


def valid_row(**overrides):
    row = {
        "listing_id": "mubawab.ma:native:1", "source": "mubawab.ma", "source_listing_id": "1",
        "city": "Casablanca", "neighborhood": "Maârif", "surface_m2": 100,
        "bedrooms": 2, "bathrooms": 1, "price_mad": 1_500_000,
        "price_per_m2": 15_000, "property_type": "appartement", "transaction_type": "sale",
        "latitude": None, "longitude": None, "validation_reasons": "",
        "deduplication_status": "unique", "title_raw": "Appartement unique à Maârif",
        "location_raw": "Maârif, Casablanca", "url": "https://example.test/a/1",
    }
    row.update(overrides)
    return row


def test_url_canonicalization_removes_tracking_and_fragment():
    assert canonicalize_url("https://EXAMPLE.com/a/?utm_source=x&keep=1#top") == "https://example.com/a?keep=1"


def test_publication_date_parser_preserves_unknown():
    assert normalize_iso_date("2024-03-01") == "2024-03-01T00:00:00+00:00"
    assert normalize_iso_date(None) is None
    assert normalize_iso_date("not a date") is None


def test_neighborhood_repair_rejects_generic_and_uses_city_vocabulary():
    vocabulary = {"casablanca": {"maarif": "Maârif"}}
    assert not valid_neighborhood("Appartements")
    assert repair_neighborhood("Casablanca", "Publier une annonce", "https://example.test/appartement-maarif", None, vocabulary) == ("Maârif", "url_or_title_vocabulary_match")


def test_validation_rejects_rental_and_price_per_m2_outlier():
    status, reasons = validate_canonical(valid_row(transaction_type="rent", price_per_m2=500_000))
    assert status == "rejected"
    assert {"rental_listing", "price_per_m2_outlier"}.issubset(reasons)


def test_deduplication_prefers_exact_source_id_and_is_conservative():
    rows = [valid_row(), valid_row(listing_id="other", url="https://example.test/a/1-new")]
    counts = mark_duplicates(rows)
    assert counts["source_id"] == 1
    assert rows[1]["deduplication_status"] == "duplicate_source_id"


def test_canonical_output_schema_and_parquet_match():
    csv_frame = pd.read_csv(ROOT / "data" / "processed" / "maisondelux_clean.csv", nrows=5)
    parquet_frame = pd.read_parquet(ROOT / "data" / "processed" / "maisondelux_clean.parquet").head(5)
    assert list(csv_frame.columns) == CANONICAL_COLUMNS
    assert list(parquet_frame.columns) == CANONICAL_COLUMNS


def test_geographic_matching_uses_city_centroid_only_for_region():
    geography = MoroccoGeography(ROOT / "data" / "geographic")
    match = geography.enrich("Casablanca")
    assert match["city"] == "Casablanca"
    assert match["region"] == "Casablanca-Settat"
    assert 20 < match["latitude"] < 37
    assert -18 < match["longitude"] < 0
