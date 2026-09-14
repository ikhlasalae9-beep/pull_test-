import numpy as np
import pandas as pd

from ml.src.data_repair.model_ready import (
    SAFE_CANDIDATE_FEATURES,
    classify_property_type,
    repair_dataset,
    validate_neighborhood,
)


def test_property_type_rules_are_conservative_and_protect_hay_riad():
    assert classify_property_type({"title_raw": "Riad traditionnel à rénover"})[0] == "riad"
    assert classify_property_type({"title_raw": "Appartement à vendre à Hay Riad"})[0] == "appartement"
    assert classify_property_type({"title_raw": "Immeuble R+3 avec quatre appartements"})[0] == "immeuble"
    assert classify_property_type({"title_raw": "Appartement calme dans un immeuble neuf"})[0] == "appartement"
    assert classify_property_type({"title_raw": "Appartement duplex à vendre"})[0] == "duplex"
    assert classify_property_type({"url": "https://example.test/a/1/studio-a-vendre-casablanca"})[0] == "studio"
    assert classify_property_type({"title_raw": "Belle opportunité au centre"})[0] == "unknown"


def test_neighborhood_validator_rejects_sentences_without_inventing_replacements():
    assert validate_neighborhood("Maârif", "Casablanca") == ("Maârif", "valid", None)
    clean, status, reason = validate_neighborhood("à quelques minutes du centre de", "Marrakech")
    assert clean is None and status == "invalid"
    assert "sentence_or_promotional_phrase" in reason
    assert validate_neighborhood("Casablanca", "Casablanca")[0] is None


def _fixture_rows() -> pd.DataFrame:
    base = {
        "source": "licensed.test",
        "city": "Casablanca",
        "region": "Casablanca-Settat",
        "latitude": np.nan,
        "longitude": np.nan,
        "bedrooms": 2.0,
        "bathrooms": 1.0,
        "furnished_status": "unknown",
        "parking": "unknown",
        "balcony": "unknown",
        "sea_view": "unknown",
        "property_type": "appartement",
        "transaction_type": "sale",
        "publication_date": np.nan,
        "publication_date_status": "unavailable",
        "scraped_at": "2026-09-01T00:00:00Z",
        "validation_status": "valid",
        "validation_reasons": np.nan,
        "deduplication_status": "unique",
        "duplicate_of": np.nan,
    }
    rows = []
    for listing_id, native_id, path in [
        ("one", 1, "git:HEAD:data/raw/a.csv"),
        ("two", 2, "data/external/recovery_archive/dangling_v3_tree/data/raw/b.csv"),
    ]:
        rows.append({
            **base,
            "listing_id": listing_id,
            "source_listing_id": native_id,
            "url": f"https://example.test/a/{native_id}",
            "neighborhood": "Racine",
            "surface_m2": 100.0,
            "price_mad": 1_500_000.0,
            "price_per_m2": 15_000.0,
            "title_raw": "Appartement familial rénové à Racine",
            "price_raw": "1 500 000 DH",
            "location_raw": "Racine, Casablanca",
            "details_raw": "100 m² 2 Chambres 1 Salle de bain",
            "source_record_path": path,
        })
    return pd.DataFrame(rows)


def test_cross_batch_exact_title_and_fingerprint_removes_only_one_confirmed_duplicate():
    repaired, artifacts = repair_dataset(_fixture_rows())
    assert repaired["duplicate_status_repaired"].eq("confirmed_duplicate").sum() == 1
    assert len(artifacts["model_ready"]) == 1
    assert len(artifacts["duplicate_groups"]) == 2


def test_price_per_m2_never_enters_safe_features():
    assert "price_per_m2" not in SAFE_CANDIDATE_FEATURES
