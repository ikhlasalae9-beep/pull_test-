"""End-to-end recovery, normalization, validation, deduplication and export."""
from __future__ import annotations

import argparse
import io
import json
import math
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from ml.src.cleaning.normalization import CANONICAL_COLUMNS, build_neighborhood_vocabulary, canonical_from_evidence
from ml.src.data_schema import clean_raw_text, normalize_for_matching, parse_location, valid_neighborhood
from ml.src.geography.matching import MoroccoGeography
from ml.src.validation.deduplication import mark_duplicates
from ml.src.validation.rules import validate_canonical


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_GLOB = ROOT / "data" / "external" / "recovery_archive"
HISTORICAL_GIT_PATH = "data/raw/maisonlux_maroc_complet.csv"


def scalar(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        return value.item()
    return value


def extract_native_id(url: Any) -> str | None:
    match = re.search(r"/a/(\d+)(?:/|$)", str(url or ""))
    return match.group(1) if match else None


def git_historical() -> tuple[pd.DataFrame, str]:
    result = subprocess.run(["git", "show", f"HEAD:{HISTORICAL_GIT_PATH}"], cwd=ROOT, check=True, capture_output=True)
    timestamp = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", HISTORICAL_GIT_PATH], cwd=ROOT,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return pd.read_csv(io.BytesIO(result.stdout)), timestamp


def newest_match(pattern: str) -> Path:
    matches = sorted(ARCHIVE_GLOB.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No recovery input matched {pattern}")
    return matches[0]


def load_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evidence_rows: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []

    url_rich_path = newest_match("*/misplaced_notebook_data/data/raw/maisondelux_raw.csv")
    url_rich = pd.read_csv(url_rich_path)
    for source_row in url_rich.to_dict("records"):
        row = {key: scalar(value) for key, value in source_row.items()}
        evidence_rows.append({
            "source": "mubawab.ma", "native_id": extract_native_id(row.get("url")),
            "city": row.get("city"), "neighborhood": row.get("neighborhood"),
            "surface_total_m2": row.get("surface_m2"), "bedrooms": row.get("bedrooms"),
            "bathrooms": row.get("bathrooms"), "furnished": row.get("furnished_status"),
            "parking": row.get("parking"), "balcony": row.get("balcony"), "sea_view": row.get("sea_view"),
            "price_value": row.get("price_mad"), "currency": "MAD" if row.get("price_mad") is not None else None,
            "property_type": row.get("property_type"), "transaction_type": row.get("transaction_type"),
            "url": row.get("url"), "listing_date": row.get("published_at"), "scraped_at": row.get("scraped_at"),
            "source_record_path": str(url_rich_path.relative_to(ROOT)), "recovery_priority": 2,
        })
    lineage.append({"path": str(url_rich_path.relative_to(ROOT)), "rows": len(url_rich), "role": "URL-rich recovery base"})

    dangling_paths = sorted(ARCHIVE_GLOB.glob("*/dangling_v3_tree_*/data/raw/maisonlux*_v3.csv"))
    for path in dangling_paths:
        frame = pd.read_csv(path)
        for source_row in frame.to_dict("records"):
            row = {key: scalar(value) for key, value in source_row.items()}
            row["native_id"] = extract_native_id(row.get("url"))
            row["neighborhood"] = row.get("quartier")
            row["source_record_path"] = str(path.relative_to(ROOT))
            row["recovery_priority"] = 3
            evidence_rows.append(row)
        lineage.append({"path": str(path.relative_to(ROOT)), "rows": len(frame), "role": "recovered V3 pilot evidence"})

    historical, historical_timestamp = git_historical()
    for source_row in historical.to_dict("records"):
        row = {key: scalar(value) for key, value in source_row.items()}
        evidence_rows.append({
            "source": "mubawab.ma", "source_category": "appartements à vendre",
            "title_raw": row.get("Titre"), "raw_price_text": row.get("Prix"),
            "location_raw": row.get("Localisation"), "details_raw": row.get("Details"),
            "scraped_at": historical_timestamp, "source_record_path": f"git:HEAD:{HISTORICAL_GIT_PATH}",
            "recovery_priority": 1,
        })
    lineage.append({"path": f"git:HEAD:{HISTORICAL_GIT_PATH}", "rows": len(historical), "role": "historical four-column recovery dataset"})
    return evidence_rows, lineage


def seed_neighborhood_rows(evidence_rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seeds: list[dict[str, Any]] = []
    for evidence in evidence_rows:
        city = clean_raw_text(evidence.get("city"))
        neighborhood = clean_raw_text(evidence.get("neighborhood") or evidence.get("quartier"))
        if evidence.get("location_raw"):
            parsed = parse_location(evidence["location_raw"])
            city = city or parsed.get("city")
            neighborhood = neighborhood or parsed.get("quartier")
        if city and valid_neighborhood(neighborhood):
            seeds.append({"city": city, "neighborhood": neighborhood})
    return seeds


def completeness(row: dict[str, Any]) -> tuple[int, int, str]:
    score = sum(row.get(field) is not None and row.get(field) != "" for field in (
        "source_listing_id", "url", "title_raw", "publication_date", "neighborhood",
        "price_mad", "surface_m2", "bedrooms", "bathrooms", "parking", "balcony",
    ))
    return (-score, -int(row.pop("_recovery_priority", 0)), row["listing_id"])


def normalize_rows(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vocabulary = build_neighborhood_vocabulary(seed_neighborhood_rows(evidence_rows))
    rows: list[dict[str, Any]] = []
    for evidence in evidence_rows:
        row = canonical_from_evidence(evidence, evidence["source_record_path"], vocabulary)
        row["_recovery_priority"] = evidence.get("recovery_priority", 0)
        rows.append(row)
    rows.sort(key=completeness)
    return rows


def enrich_and_validate(rows: list[dict[str, Any]], geography: MoroccoGeography) -> None:
    city_cache: dict[str, dict[str, Any]] = {}
    for row in rows:
        city_key = normalize_for_matching(row.get("city"))
        if city_key not in city_cache:
            city_cache[city_key] = geography.enrich(row.get("city"))
        match = city_cache[city_key]
        row["city"] = match.get("city") or row.get("city")
        if row.get("latitude") is not None and row.get("longitude") is not None:
            row["region"] = geography.region_for_point(float(row["latitude"]), float(row["longitude"]))
        else:
            # City centroids support region matching but are not written as precise listing coordinates.
            row["region"] = match.get("region")
        status, reasons = validate_canonical(row)
        row["validation_status"] = status
        row["validation_reasons"] = "|".join(reasons)


def frame_for(rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=CANONICAL_COLUMNS)
    for field in ("latitude", "longitude", "surface_m2", "bedrooms", "bathrooms", "price_mad", "price_per_m2"):
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
    return frame


def write_frame(frame: pd.DataFrame, csv_path: Path, parquet_path: Path | None = None) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")
    if parquet_path:
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(parquet_path, index=False)


def percentage(value: int, total: int) -> str:
    return f"{(100 * value / total):.2f}%" if total else "0.00%"


def markdown_table(frame: pd.DataFrame, limit: int = 30) -> list[str]:
    if frame.empty:
        return ["No rows."]
    shown = frame.head(limit).fillna("")
    headers = [str(column) for column in shown.columns]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for values in shown.astype(str).itertuples(index=False, name=None):
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    return lines


def build_reports(raw: pd.DataFrame, clean: pd.DataFrame, rejected: pd.DataFrame,
                  duplicate_counts: dict[str, int], lineage: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    reason_counts = Counter(
        reason for value in raw["validation_reasons"].fillna("")
        for reason in str(value).split("|") if reason
    )
    missing_rates = {column: round(float(raw[column].isna().mean() + (raw[column].astype(str).str.strip().eq("").mean() if raw[column].dtype == object else 0)), 4) for column in raw.columns}
    unknown_rates = {
        column: round(float(raw[column].fillna("unknown").astype(str).str.casefold().eq("unknown").mean()), 4)
        for column in ("furnished_status", "parking", "balcony", "sea_view", "publication_date_status")
    }
    source_summary = raw.groupby("source", dropna=False).agg(
        raw_rows=("listing_id", "size"),
        valid_rows=("validation_status", lambda series: int((series == "valid").sum())),
        rejected_rows=("validation_status", lambda series: int((series != "valid").sum())),
        cities=("city", "nunique"), neighborhoods=("neighborhood", "nunique"),
    ).reset_index()
    city_summary = raw.groupby(["region", "city"], dropna=False).agg(
        raw_rows=("listing_id", "size"),
        valid_rows=("validation_status", lambda series: int((series == "valid").sum())),
        neighborhoods=("neighborhood", "nunique"),
    ).reset_index().sort_values(["valid_rows", "raw_rows"], ascending=False)
    quality_summary = pd.DataFrame(
        [{"metric": "raw_rows", "value": len(raw)}, {"metric": "valid_unique_rows", "value": len(clean)},
         {"metric": "rejected_or_warning_rows", "value": len(rejected)},
         {"metric": "duplicate_rows", "value": int(raw["deduplication_status"].ne("unique").sum())}]
        + [{"metric": f"reason:{key}", "value": value} for key, value in reason_counts.most_common()]
    )
    interim = ROOT / "data" / "interim" / "excel"
    interim.mkdir(parents=True, exist_ok=True)
    source_summary.to_csv(interim / "source_summary.csv", index=False, encoding="utf-8-sig")
    city_summary.to_csv(interim / "city_summary.csv", index=False, encoding="utf-8-sig")
    quality_summary.to_csv(interim / "quality_summary.csv", index=False, encoding="utf-8-sig")
    errors_path = newest_match("*/misplaced_notebook_data/data/raw/maisondelux_scraping_errors.csv")
    pd.read_csv(errors_path).to_csv(interim / "scraping_errors.csv", index=False, encoding="utf-8-sig")

    report = {
        "generated_at": now, "raw_rows": len(raw), "valid_unique_rows": len(clean),
        "rejected_or_warning_rows": len(rejected),
        "duplicate_rows": int(raw["deduplication_status"].ne("unique").sum()),
        "duplicate_methods": duplicate_counts,
        "sources": source_summary.fillna("unknown").to_dict("records"),
        "regions_with_listings": int(raw["region"].nunique()), "cities_with_listings": int(raw["city"].nunique()),
        "neighborhoods_with_listings": int(raw["neighborhood"].nunique()),
        "validation_status": {str(key): int(value) for key, value in raw["validation_status"].value_counts(dropna=False).items()},
        "validation_reasons": dict(reason_counts), "missing_value_rates": missing_rates,
        "explicit_unknown_rates": unknown_rates,
        "recovery_lineage": lineage,
        "price_per_m2_model_policy": "price_per_m2 is audit-only and forbidden as a price_mad model input",
    }
    report_dir = ROOT / "reports" / "data_quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "data_quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# MaisonDeLUX data quality report", "", f"Generated: {now}", "",
        "## Outcome", "",
        f"- Raw recovered rows: **{len(raw):,}**",
        f"- Valid unique rows: **{len(clean):,}** ({percentage(len(clean), len(raw))})",
        f"- Rejected or warning rows: **{len(rejected):,}**",
        f"- Confirmed duplicate rows: **{int(raw['deduplication_status'].ne('unique').sum()):,}**",
        f"- Sources: **{raw['source'].nunique():,}**; cities: **{raw['city'].nunique():,}**; neighborhoods: **{raw['neighborhood'].nunique():,}**", "",
        "`price_per_m2` is retained for validation and analysis only. It must never be a feature when predicting `price_mad`.", "",
        "## Validation reasons", "", "| Reason | Rows |", "|---|---:|",
        *[f"| `{reason}` | {count:,} |" for reason, count in reason_counts.most_common()], "",
        "## Missing-value rates", "", "| Field | Missing |", "|---|---:|",
        *[f"| `{field}` | {rate:.1%} |" for field, rate in sorted(missing_rates.items(), key=lambda item: item[1], reverse=True)], "",
        "## Explicit unknown rates", "", "Tri-state `unknown` values are not counted as nulls above; they are reported separately here.", "", "| Field | Unknown |", "|---|---:|",
        *[f"| `{field}` | {rate:.1%} |" for field, rate in unknown_rates.items()], "",
        "## Recovery inputs", "", "| Input | Rows | Role |", "|---|---:|---|",
        *[f"| `{item['path']}` | {item['rows']:,} | {item['role']} |" for item in lineage], "",
    ]
    (report_dir / "data_quality_report.md").write_text("\n".join(md), encoding="utf-8")
    return report


def build_historical_report(raw: pd.DataFrame) -> None:
    publication = pd.to_datetime(raw["publication_date"], errors="coerce", utc=True)
    counts = {str(year): int((publication.dt.year == year).sum()) for year in (2023, 2024, 2025, 2026)}
    counts["unknown"] = int(publication.isna().sum())
    lines = ["# Historical coverage", "", "Publication dates only; `scraped_at` is never substituted.", "", "| Year | Rows |", "|---|---:|", *[f"| {year} | {count:,} |" for year, count in counts.items()], "",
             "Live listing sites do not establish coverage of removed 2023–2025 listings. Unknown dates are preserved and reported explicitly."]
    (ROOT / "reports" / "scraping" / "historical_coverage_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_geographic_report(raw: pd.DataFrame) -> None:
    geo_dir = ROOT / "data" / "geographic"
    cities = json.loads((geo_dir / "morocco_cities.geojson").read_text(encoding="utf-8"))["features"]
    neighborhoods = json.loads((geo_dir / "morocco_neighborhoods.geojson").read_text(encoding="utf-8"))["features"]
    valid = raw[(raw["validation_status"] == "valid") & (raw["deduplication_status"] == "unique")]
    city_counts = valid.groupby(valid["city"].map(normalize_for_matching)).size().to_dict()
    neighborhood_counts = valid.groupby(valid["neighborhood"].map(normalize_for_matching)).size().to_dict()
    detail_rows = []
    for kind, features, counts in (("city_or_town", cities, city_counts), ("neighborhood_or_district", neighborhoods, neighborhood_counts)):
        assigned_names: set[str] = set()
        for feature in features:
            properties = feature["properties"]
            normalized_name = properties.get("normalized_name")
            count = int(counts.get(normalized_name, 0)) if normalized_name not in assigned_names else 0
            assigned_names.add(normalized_name)
            detail_rows.append({
                "feature_type": kind, "name": properties.get("name"), "parent_city": properties.get("parent_city"),
                "region": properties.get("region"), "latitude": properties.get("latitude"), "longitude": properties.get("longitude"),
                "has_coordinates": feature.get("geometry") is not None, "valid_listing_count": count,
                "modeling_coverage": "enough" if count >= 30 else "insufficient" if count else "zero",
            })
    detail = pd.DataFrame(detail_rows)
    detail.to_csv(ROOT / "reports" / "scraping" / "geographic_coverage_detail.csv", index=False, encoding="utf-8-sig")
    summary = detail.groupby(["feature_type", "modeling_coverage"]).size().unstack(fill_value=0).reset_index()
    region_summary = raw.groupby("region", dropna=False).agg(raw_rows=("listing_id", "size"), valid_rows=("validation_status", lambda series: int((series == "valid").sum()))).reset_index().sort_values("valid_rows", ascending=False)
    top_cities = raw.groupby("city", dropna=False).agg(raw_rows=("listing_id", "size"), valid_rows=("validation_status", lambda series: int((series == "valid").sum()))).reset_index().sort_values("valid_rows", ascending=False)
    lines = ["# Geographic coverage", "", "Geo-reference features with no listings remain explicit zero-coverage rows; no property observations were fabricated.", "", "## Reference coverage", "", *markdown_table(summary), "", "## Listing coverage by region", "", *markdown_table(region_summary, 20), "", "## Top listing cities", "", *markdown_table(top_cities, 30), "", "Full zero/insufficient/enough coverage is in `reports/scraping/geographic_coverage_detail.csv`. The modeling threshold is 30 valid unique listings."]
    (ROOT / "reports" / "scraping" / "geographic_coverage_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_source_report(raw: pd.DataFrame) -> None:
    audit_path = ROOT / "reports" / "scraping" / "source_policy_audit.json"
    policies = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else []
    source_counts = raw.groupby("source").agg(raw_rows=("listing_id", "size"), valid_rows=("validation_status", lambda series: int((series == "valid").sum())), cities=("city", "nunique")).reset_index()
    lines = ["# Source coverage and access policy", "", "Only sources that pass robots, access-policy and extraction-quality checks may be enabled for live acquisition.", "", "## Recovered data", "", *markdown_table(source_counts), "", "## Live adapter decisions", "", "| Source | Status | Robots | Terms | Pilot | Reason |", "|---|---|---|---|---|---|"]
    for item in policies:
        source = f"[{item.get('source')}]({item.get('base_url')})" if item.get('base_url') else item.get('source')
        robots = f"[{item.get('robots_status')}]({item.get('robots_url')})" if item.get('robots_url') else item.get('robots_status')
        terms = f"[policy]({item.get('terms_url')})" if item.get('terms_url') else "not publicly verified"
        lines.append(f"| {source} | {item.get('status')} | {robots} | {terms} | {item.get('pilot_status')} | {str(item.get('reason','')).replace('|','/')} |")
    if not policies:
        lines.append("| none | disabled | not audited in this run | not verified | not run | No source enabled without a completed legal/technical pilot. |")
    lines += ["", "Recovered data does not imply continuing permission to scrape its origin. Historical and recovery inputs are preserved separately from live adapter status."]
    (ROOT / "reports" / "scraping" / "source_coverage_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> dict[str, Any]:
    evidence_rows, lineage = load_inputs()
    rows = normalize_rows(evidence_rows)
    geography = MoroccoGeography(ROOT / "data" / "geographic")
    enrich_and_validate(rows, geography)
    duplicate_counts = mark_duplicates(rows)
    for row in rows:
        if row["deduplication_status"] != "unique":
            row["validation_status"] = "rejected"
            reasons = [reason for reason in row["validation_reasons"].split("|") if reason]
            reasons.append(row["deduplication_status"])
            row["validation_reasons"] = "|".join(dict.fromkeys(reasons))
    raw = frame_for(rows)
    clean = raw[(raw["validation_status"] == "valid") & (raw["deduplication_status"] == "unique")].copy()
    rejected = raw[~raw.index.isin(clean.index)].copy()
    write_frame(raw, ROOT / "data" / "raw" / "maisondelux_raw.csv", ROOT / "data" / "raw" / "maisondelux_raw.parquet")
    write_frame(raw, ROOT / "data" / "interim" / "maisondelux_recovered.csv", ROOT / "data" / "interim" / "maisondelux_recovered.parquet")
    write_frame(clean, ROOT / "data" / "processed" / "maisondelux_clean.csv", ROOT / "data" / "processed" / "maisondelux_clean.parquet")
    write_frame(rejected, ROOT / "data" / "processed" / "maisondelux_rejected.csv")
    report = build_reports(raw, clean, rejected, duplicate_counts, lineage)
    build_historical_report(raw)
    build_geographic_report(raw)
    build_source_report(raw)
    (ROOT / "data" / "interim" / "pipeline_state.json").write_text(json.dumps({"completed_at": datetime.now(timezone.utc).isoformat(), "status": "complete", "row_counts": {"raw": len(raw), "valid": len(clean), "rejected": len(rejected)}}, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recover-only", action="store_true", help="Retained for notebook/CLI compatibility; recovery is always the first stage.")
    parser.parse_args()
    report = run()
    print(json.dumps({key: report[key] for key in ("raw_rows", "valid_unique_rows", "rejected_or_warning_rows", "duplicate_rows")}, sort_keys=True))


if __name__ == "__main__":
    main()
