"""Conservative, auditable repair of ``maisondelux_clean.csv``.

This module never downloads data and never mutates the source CSV.  It repairs
derived modeling fields, identifies high-confidence duplicate rows, audits
source batches, and removes only rows with an explicit exclusion reason.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit, urlunsplit

import numpy as np
import pandas as pd


TARGET = ["price_mad"]

SAFE_CANDIDATE_FEATURES = [
    "region",
    "city",
    "neighborhood_clean",
    "property_type_repaired",
    "surface_m2",
    "bedrooms",
    "bathrooms",
    "furnished_status",
    "parking",
    "balcony",
    "sea_view",
]

EXCLUDE_FROM_MODEL = [
    "price_per_m2",
    "price_per_m2_original",
    "price_per_m2_recomputed",
    "price_raw",
    "listing_id",
    "source_listing_id",
    "url",
    "canonical_url_repaired",
    "title_raw",
    "details_raw",
    "location_raw",
    "publication_date",
    "publication_date_status",
    "scraped_at",
    "source_record_path",
    "validation_status",
    "validation_reasons",
    "deduplication_status",
    "duplicate_of",
    "duplicate_status_repaired",
    "duplicate_group_id",
    "duplicate_match_level",
    "duplicate_keep",
    "batch_id",
    "batch_anomaly_status",
    "numeric_consistency_status",
    "outlier_decision",
    "outlier_reasons",
    "repair_exclusion_reason",
]

EXCLUSION_EXPLANATIONS = {
    "not_sale": "The transaction type is not a sale listing.",
    "invalid_price": "price_mad is missing, non-finite, or non-positive.",
    "invalid_surface": "surface_m2 is missing, non-finite, or non-positive.",
    "missing_city": "No usable city is present.",
    "missing_region": "No usable region can be retained or derived from the city.",
    "invalid_prior_validation": "The existing validation status is neither valid nor warning.",
    "confirmed_duplicate": "A higher-evidence row represents the same property observation.",
    "probable_parsing_error": "Numeric magnitude or consistency evidence indicates a probable error.",
}

REGION_BY_CITY = {
    "Tanger": "Tanger-Tétouan-Al Hoceïma",
    "Tétouan": "Tanger-Tétouan-Al Hoceïma",
    "Larache": "Tanger-Tétouan-Al Hoceïma",
    "Chefchaouen": "Tanger-Tétouan-Al Hoceïma",
    "Fnidek": "Tanger-Tétouan-Al Hoceïma",
    "Oujda": "L'Oriental",
    "Nador": "L'Oriental",
    "Fès": "Fès-Meknès",
    "Meknès": "Fès-Meknès",
    "Ifrane": "Fès-Meknès",
    "Rabat": "Rabat-Salé-Kénitra",
    "Salé": "Rabat-Salé-Kénitra",
    "Kénitra": "Rabat-Salé-Kénitra",
    "Témara": "Rabat-Salé-Kénitra",
    "Khémisset": "Rabat-Salé-Kénitra",
    "Béni Mellal": "Béni Mellal-Khénifra",
    "Khouribga": "Béni Mellal-Khénifra",
    "Casablanca": "Casablanca-Settat",
    "Settat": "Casablanca-Settat",
    "El Jadida": "Casablanca-Settat",
    "Mohammedia": "Casablanca-Settat",
    "Berrechid": "Casablanca-Settat",
    "Bouskoura": "Casablanca-Settat",
    "Bouznika": "Casablanca-Settat",
    "Marrakech": "Marrakech-Safi",
    "Safi": "Marrakech-Safi",
    "Essaouira": "Marrakech-Safi",
    "Ouarzazate": "Drâa-Tafilalet",
    "Agadir": "Souss-Massa",
    "Tiznit": "Souss-Massa",
    "Laâyoune": "Laâyoune-Sakia El Hamra",
}

PROPERTY_CATEGORIES = {
    "appartement",
    "studio",
    "duplex",
    "villa",
    "maison",
    "riad",
    "immeuble",
    "terrain",
    "bureau",
    "local_commercial",
    "magasin",
    "unknown",
}

NON_APPLICABLE_BEDROOM_TYPES = {"terrain", "bureau", "local_commercial", "magasin"}

PROMOTIONAL_NEIGHBORHOOD = re.compile(
    r"\b(?:a quelques minutes|quelques minutes|a seulement|seulement \d+|a pied|"
    r"l un des|l une des|dans un quartier|le quartier (?:anime|prise|recherche|dynamique|calme|vibrant|prestigieux)|"
    r"un quartier|au coeur|situe|situee|proche de|a proximite|pres de|deux pas|"
    r"magnifique|superbe|ideal|opportunite|prix exceptionnel|profitez|decouvrez|"
    r"votre agence|agence immobiliere|contactez|a vendre|a louer|vente|location|"
    r"l achat|la location|dispose|compose|beneficie|residence (?:calme|neuve|recherchee)|"
    r"emplacement (?:strategique|privilegie)|ceux qui veulent vivre|"
    r"points d interet|gare de|centre anime|projets immobiliers|beautiful|located|prime location)\b"
)

TRAILING_PREPOSITION = re.compile(r"\b(?:de|du|des|a|au|aux|dans|avec|sur|pres|vers)$")

LUXURY_OR_SPECIAL_SIGNAL = re.compile(
    r"\b(?:luxe|luxueux|prestige|prestigia|exceptionnel|penthouse|palais|haut standing|"
    r"villa|immeuble|terrain|riad traditionnel|riad authentique|maison d hotes)\b"
)


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value)


def _clean(value: Any) -> str | None:
    if _missing(value):
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def normalized_text(value: Any) -> str:
    text = _clean(value) or ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.casefold().replace("’", "'")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _url_slug(url: Any) -> str:
    if not _clean(url):
        return ""
    path = unquote(urlsplit(str(url)).path)
    parts = [part for part in path.split("/") if part]
    slug = parts[-1] if parts else ""
    return normalized_text(slug.replace("-", " "))


def canonical_url(url: Any) -> str | None:
    text = _clean(url)
    if not text:
        return None
    parsed = urlsplit(text)
    if not parsed.scheme or not parsed.netloc:
        return text.rstrip("/")
    return urlunsplit((parsed.scheme.casefold(), parsed.netloc.casefold(), parsed.path.rstrip("/"), "", ""))


def _property_evidence(row: pd.Series | dict[str, Any]) -> tuple[str, str, str]:
    title = normalized_text(row.get("title_raw"))
    slug = _url_slug(row.get("url"))
    details = normalized_text(row.get("details_raw"))
    location = normalized_text(row.get("location_raw"))
    primary = " ".join(part for part in (title, slug) if part)
    secondary = " ".join(part for part in (details, location) if part)
    return primary, secondary, title or slug


def classify_property_type(row: pd.Series | dict[str, Any]) -> tuple[str, str]:
    """Infer property type only from explicit text; return unknown when weak."""
    primary, secondary, strongest = _property_evidence(row)
    all_text = f"{primary} {secondary}".strip()
    if not all_text:
        return "unknown", "no_text_evidence"

    explicit_rules: list[tuple[str, str]] = [
        ("local_commercial", r"\b(?:local|locale) commercial(?:e)?\b|\blocal a usage commercial\b"),
        ("magasin", r"\bmagasins?\b|\bshop\b"),
        ("bureau", r"\bbureaux?\b|\boffice\b"),
        ("terrain", r"\bterrains?\b|\blot de terrain\b"),
        ("villa", r"\bvillas?\b"),
        ("maison", r"\bmaisons?\b|\bhouse\b"),
    ]

    building_strong = bool(re.search(
        r"^(?:vente )?immeuble\b|\bimmeuble (?:r\s*\+?\s*\d|a vendre|en vente|compose|complet|semi fini)\b",
        strongest,
    ))
    if building_strong:
        return "immeuble", "explicit_immeuble"

    for category, pattern in explicit_rules:
        if re.search(pattern, primary):
            return category, f"explicit_{category}"

    if re.search(r"\bduplex(?:es)?\b", primary):
        return "duplex", "explicit_duplex"
    if re.search(r"\bstudios?\b", primary):
        return "studio", "explicit_studio"

    apartment_signal = bool(re.search(r"\bappart(?:ement|ements|ements|s)?\b|\bapartment\b|\bapt\b", primary))
    protected_riad_location = bool(re.search(
        r"\b(?:hay|al|el|oulad|salam|essalam|zitoun|garden|atlas|sofia|oulfa|ahlan) riad\b|"
        r"\briad (?:al|el|oulad|salam|essalam|zitoun|garden|atlas|sofia|oulfa|ahlan)\b",
        all_text,
    ))
    riad_strong = bool(re.search(
        r"^(?:vente d un |vente |vend )?riad\b|\briad (?:traditionnel|authentique|a vendre|en vente|a renover|maison d hotes)\b",
        strongest,
    ))
    if riad_strong and (not apartment_signal or strongest.startswith("riad")):
        return "riad", "explicit_riad"
    if apartment_signal:
        return "appartement", "explicit_appartement"

    # Secondary text can rescue only unambiguous compound categories.  A bare
    # neighborhood/location word such as "Riad" is intentionally ignored.
    for category, pattern in explicit_rules[:4]:
        if re.search(pattern, secondary):
            return category, f"secondary_explicit_{category}"
    if riad_strong and not protected_riad_location:
        return "riad", "explicit_riad"
    return "unknown", "weak_or_ambiguous_evidence"


def validate_neighborhood(value: Any, city: Any = None) -> tuple[str | None, str, str | None]:
    text = _clean(value)
    if not text:
        return None, "invalid", "missing"
    key = normalized_text(text)
    city_key = normalized_text(city)
    tokens = key.split()
    reasons: list[str] = []
    if len(text) > 55:
        reasons.append("too_long")
    if not 1 <= len(tokens) <= 7:
        reasons.append("token_count")
    if city_key and key == city_key:
        reasons.append("same_as_city")
    if PROMOTIONAL_NEIGHBORHOOD.search(key):
        reasons.append("sentence_or_promotional_phrase")
    if re.search(r"[.!?;:•]", text) or "..." in text:
        reasons.append("sentence_punctuation")
    if re.search(r"\b\d+\s*(?:m2|metres?|minutes?)\b", key):
        reasons.append("measurement_or_travel_time")
    if TRAILING_PREPOSITION.search(key):
        reasons.append("trailing_preposition")
    if re.search(r"\b(?:appartement|studio|duplex|villa|maison|immeuble|terrain|bureau|magasin)\b", key):
        reasons.append("property_description")
    if reasons:
        return None, "invalid", "|".join(dict.fromkeys(reasons))
    return text, "valid", None


def _batch_id(path: Any) -> str:
    text = _clean(path) or "unknown"
    if text.startswith("git:HEAD:"):
        return "git_head_complete"
    if "misplaced_notebook_data" in text:
        return "recovery_misplaced_notebook"
    if "dangling_v3_tree" in text:
        return "recovery_dangling_v3"
    return Path(text.replace("\\", "/")).stem or "unknown"


def _json_counts(series: pd.Series, limit: int = 20) -> str:
    counts = series.fillna("<null>").astype(str).value_counts().head(limit)
    return json.dumps({str(k): int(v) for k, v in counts.items()}, ensure_ascii=False, sort_keys=True)


def audit_batches(frame: pd.DataFrame) -> pd.DataFrame:
    raw_fields = ["title_raw", "price_raw", "location_raw", "details_raw", "url", "source_listing_id"]
    records: list[dict[str, Any]] = []
    for path, group in frame.groupby("source_record_path", dropna=False):
        record: dict[str, Any] = {
            "source_record_path": path,
            "batch_id": group["batch_id"].iloc[0],
            "row_count": int(len(group)),
            "median_price_mad": float(group["price_mad"].median()),
            "median_surface_m2": float(group["surface_m2"].median()),
            "median_price_per_m2": float(group["price_per_m2"].median()),
            "p95_price_per_m2": float(group["price_per_m2"].quantile(0.95)),
            "p99_price_per_m2": float(group["price_per_m2"].quantile(0.99)),
            "property_type_distribution": _json_counts(group["property_type_repaired"]),
            "city_distribution": _json_counts(group["city"]),
        }
        for field in raw_fields:
            record[f"missing_{field}_percent"] = round(float(group[field].isna().mean() * 100), 2)
        records.append(record)
    audit = pd.DataFrame(records)
    reference_p95 = float(audit["p95_price_per_m2"].median()) if not audit.empty else 0.0
    audit["p95_to_batch_median_ratio"] = np.where(
        reference_p95 > 0,
        audit["p95_price_per_m2"] / reference_p95,
        1.0,
    )
    audit["batch_anomaly_status"] = np.where(
        (audit["row_count"] >= 100) & (audit["p95_to_batch_median_ratio"] >= 2.5),
        "suspicious_high_price_per_m2_tail",
        "not_flagged",
    )
    audit["batch_anomaly_reason"] = np.where(
        audit["batch_anomaly_status"].ne("not_flagged"),
        "The batch p95 price/m² is at least 2.5x the median batch p95; the batch is flagged, not removed wholesale.",
        "",
    )
    return audit.sort_values("row_count", ascending=False).reset_index(drop=True)


class _UnionFind:
    def __init__(self, values: Iterable[int]):
        self.parent = {int(value): int(value) for value in values}

    def find(self, value: int) -> int:
        value = int(value)
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        root_left, root_right = self.find(left), self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left

    def groups(self) -> list[list[int]]:
        result: dict[int, list[int]] = defaultdict(list)
        for value in self.parent:
            result[self.find(value)].append(value)
        return [members for members in result.values() if len(members) > 1]


def _union_duplicate_keys(
    frame: pd.DataFrame,
    union: _UnionFind,
    columns: list[str],
    valid_mask: pd.Series,
    levels: dict[int, set[str]],
    level: str,
) -> None:
    subset = frame.loc[valid_mask, columns].copy()
    duplicate_mask = subset.duplicated(columns, keep=False)
    for _, group in subset.loc[duplicate_mask].groupby(columns, dropna=False, sort=False):
        members = list(map(int, group.index))
        for member in members[1:]:
            union.union(members[0], member)
        for member in members:
            levels[member].add(level)


def _informative_title(value: str) -> bool:
    tokens = value.split()
    generic = {
        "appartement a vendre",
        "vente appartement",
        "bel appartement a vendre",
        "appartement en vente",
        "appartement",
    }
    return len(value) >= 20 and len(tokens) >= 4 and value not in generic


def _stable_group_id(prefix: str, frame: pd.DataFrame, members: list[int]) -> str:
    evidence = "|".join(sorted(frame.loc[members, "listing_id"].astype(str)))
    return f"{prefix}-{hashlib.sha1(evidence.encode('utf-8')).hexdigest()[:12]}"


def detect_duplicates(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = frame.copy()
    indices = list(map(int, result.index))
    confirmed = _UnionFind(indices)
    confirmed_levels: dict[int, set[str]] = defaultdict(set)

    id_valid = result["source"].notna() & result["source_listing_id"].notna()
    _union_duplicate_keys(
        result,
        confirmed,
        ["source", "source_listing_id_normalized"],
        id_valid,
        confirmed_levels,
        "A_source_and_native_id",
    )
    url_valid = result["canonical_url_repaired"].notna()
    _union_duplicate_keys(
        result,
        confirmed,
        ["canonical_url_repaired"],
        url_valid,
        confirmed_levels,
        "B_canonical_url",
    )

    fingerprint_columns = [
        "city",
        "neighborhood_clean",
        "surface_m2",
        "price_mad",
        "bedrooms",
        "bathrooms",
    ]
    fingerprint_valid = result[["city", "surface_m2", "price_mad"]].notna().all(axis=1)
    exact_title_valid = fingerprint_valid & result["normalized_title"].map(_informative_title)
    candidate = result.loc[exact_title_valid, fingerprint_columns + ["normalized_title", "batch_id"]]
    dup_candidate = candidate.duplicated(fingerprint_columns + ["normalized_title"], keep=False)
    for _, group in candidate.loc[dup_candidate].groupby(
        fingerprint_columns + ["normalized_title"], dropna=False, sort=False
    ):
        if group["batch_id"].nunique() < 2:
            continue
        members = list(map(int, group.index))
        for member in members[1:]:
            confirmed.union(members[0], member)
        for member in members:
            confirmed_levels[member].add("C_exact_fingerprint_and_title_cross_batch")

    result["duplicate_status_repaired"] = "unique"
    result["duplicate_group_id"] = pd.NA
    result["duplicate_match_level"] = pd.NA
    result["duplicate_keep"] = True
    confirmed_member_indices: set[int] = set()

    for members in confirmed.groups():
        if not any(confirmed_levels.get(member) for member in members):
            continue
        confirmed_member_indices.update(members)
        group_id = _stable_group_id("confirmed", result, members)
        quality = pd.DataFrame(index=members)
        quality["score"] = (
            result.loc[members, ["title_raw", "details_raw", "price_raw", "location_raw"]].notna().sum(axis=1) * 2
            + result.loc[members, ["url", "source_listing_id", "neighborhood_clean"]].notna().sum(axis=1)
        )
        quality["position"] = [-member for member in members]
        keeper = int(quality.sort_values(["score", "position"], ascending=False).index[0])
        levels = sorted(set().union(*(confirmed_levels.get(member, set()) for member in members)))
        result.loc[members, "duplicate_group_id"] = group_id
        result.loc[members, "duplicate_match_level"] = "|".join(levels)
        for member in members:
            if member != keeper:
                result.at[member, "duplicate_status_repaired"] = "confirmed_duplicate"
                result.at[member, "duplicate_keep"] = False

    possible = _UnionFind(index for index in indices if index not in confirmed_member_indices)
    possible_levels: dict[int, set[str]] = defaultdict(set)
    eligible = fingerprint_valid & ~result.index.to_series().isin(confirmed_member_indices)
    _union_duplicate_keys(
        result,
        possible,
        fingerprint_columns,
        eligible,
        possible_levels,
        "C_exact_structured_fingerprint",
    )

    # Level D: compare only tightly blocked rows.  Uncertain fuzzy matches are
    # retained and never promoted to confirmed duplicates.
    fuzzy_candidates = result.loc[
        ~result.index.to_series().isin(confirmed_member_indices)
        & result["normalized_title"].map(_informative_title)
        & result[["city", "price_mad", "surface_m2"]].notna().all(axis=1)
    ]
    for _, city_group in fuzzy_candidates.groupby("city", sort=False):
        ordered = city_group.sort_values("price_mad")
        rows = list(ordered.index)
        for position, left in enumerate(rows):
            left_price = float(result.at[left, "price_mad"])
            left_surface = float(result.at[left, "surface_m2"])
            left_title = str(result.at[left, "normalized_title"])
            for right in rows[position + 1:]:
                right_price = float(result.at[right, "price_mad"])
                if right_price > left_price * 1.02:
                    break
                if abs(right_price - left_price) / max(left_price, right_price) > 0.02:
                    continue
                right_surface = float(result.at[right, "surface_m2"])
                if abs(right_surface - left_surface) / max(left_surface, right_surface) > 0.03:
                    continue
                right_title = str(result.at[right, "normalized_title"])
                similarity = SequenceMatcher(None, left_title, right_title).ratio()
                if similarity < 0.96:
                    continue
                possible.union(int(left), int(right))
                possible_levels[int(left)].add("D_similar_title_close_price_surface_city")
                possible_levels[int(right)].add("D_similar_title_close_price_surface_city")

    for members in possible.groups():
        if not any(possible_levels.get(member) for member in members):
            continue
        group_id = _stable_group_id("possible", result, members)
        levels = sorted(set().union(*(possible_levels.get(member, set()) for member in members)))
        result.loc[members, "duplicate_status_repaired"] = "possible_duplicate"
        result.loc[members, "duplicate_group_id"] = group_id
        result.loc[members, "duplicate_match_level"] = "|".join(levels)

    member_columns = [
        "duplicate_group_id",
        "duplicate_status_repaired",
        "duplicate_match_level",
        "duplicate_keep",
        "listing_id",
        "source",
        "source_listing_id",
        "url",
        "city",
        "neighborhood_clean",
        "surface_m2",
        "price_mad",
        "bedrooms",
        "bathrooms",
        "title_raw",
        "source_record_path",
    ]
    members = result.loc[result["duplicate_group_id"].notna(), member_columns].copy()
    members = members.sort_values(["duplicate_group_id", "duplicate_keep"], ascending=[True, False])
    return result, members


def _is_finite_positive(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna() & np.isfinite(numeric) & numeric.gt(0)


def classify_outliers(frame: pd.DataFrame, batch_audit: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    expected_ppm = result["price_mad"] / result["surface_m2"]
    tolerance = np.maximum(5.0, expected_ppm.abs() * 0.01)
    difference = (result["price_per_m2"] - expected_ppm).abs()
    result["price_per_m2_original"] = result["price_per_m2"]
    result["price_per_m2_recomputed"] = expected_ppm.round(2)
    result["numeric_consistency_status"] = np.where(
        difference.le(tolerance), "consistent", "inconsistent"
    )

    suspicious_batches = set(
        batch_audit.loc[
            batch_audit["batch_anomaly_status"].ne("not_flagged"), "batch_id"
        ].astype(str)
    )
    reference_rows = result.loc[~result["batch_id"].isin(suspicious_batches), "price_per_m2"]
    reference_p99 = float(reference_rows.quantile(0.99)) if len(reference_rows) else 50_000.0
    probable_ppm_threshold = max(75_000.0, reference_p99 * 1.75)
    price_q99 = float(result["price_mad"].quantile(0.99))
    surface_q99 = float(result["surface_m2"].quantile(0.99))

    decisions: list[str] = []
    reasons_output: list[str] = []
    for _, row in result.iterrows():
        reasons: list[str] = []
        price = row.get("price_mad")
        surface = row.get("surface_m2")
        ppm = row.get("price_per_m2")
        bedrooms = row.get("bedrooms")
        bathrooms = row.get("bathrooms")
        if _missing(surface) or not np.isfinite(surface) or surface <= 0:
            reasons.append("invalid_surface")
        elif surface > max(500.0, surface_q99):
            reasons.append("surface_extreme")
        if _missing(price) or not np.isfinite(price) or price <= 0:
            reasons.append("invalid_price")
        elif price > price_q99:
            reasons.append("price_above_p99")
        if not _missing(bedrooms) and bedrooms > 8:
            reasons.append("bedrooms_above_8")
        if not _missing(bathrooms) and bathrooms > 8:
            reasons.append("bathrooms_above_8")
        if not _missing(ppm) and ppm > reference_p99:
            reasons.append("price_per_m2_above_reference_p99")
        if row.get("numeric_consistency_status") == "inconsistent":
            reasons.append("price_per_m2_math_mismatch")

        primary, secondary, _ = _property_evidence(row)
        luxury_or_special = (
            row.get("property_type_repaired") in {"villa", "riad", "immeuble", "terrain"}
            or bool(LUXURY_OR_SPECIAL_SIGNAL.search(f"{primary} {secondary}"))
        )
        probable_batch_magnitude = (
            str(row.get("batch_id")) in suspicious_batches
            and not _missing(ppm)
            and ppm >= probable_ppm_threshold
            and not luxury_or_special
        )
        if probable_batch_magnitude:
            reasons.append("suspicious_batch_high_price_per_m2")

        if "invalid_surface" in reasons or "invalid_price" in reasons or "price_per_m2_math_mismatch" in reasons:
            decision = "probable_error"
        elif probable_batch_magnitude:
            decision = "probable_error"
        elif reasons:
            decision = "valid_extreme" if luxury_or_special and ppm < probable_ppm_threshold else "uncertain"
        else:
            decision = "not_flagged"
        decisions.append(decision)
        reasons_output.append("|".join(dict.fromkeys(reasons)))

    result["outlier_decision"] = decisions
    result["outlier_reasons"] = reasons_output
    result.attrs["outlier_thresholds"] = {
        "reference_price_per_m2_p99": round(reference_p99, 2),
        "probable_batch_price_per_m2_threshold": round(probable_ppm_threshold, 2),
        "price_p99": round(price_q99, 2),
        "surface_p99": round(surface_q99, 2),
    }
    return result


def _normalize_source_id(value: Any) -> str | None:
    if _missing(value):
        return None
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return _clean(value)


def _exclusion_reasons(row: pd.Series) -> str:
    reasons: list[str] = []
    if normalized_text(row.get("transaction_type")) != "sale":
        reasons.append("not_sale")
    if not _is_finite_scalar_positive(row.get("price_mad")):
        reasons.append("invalid_price")
    if not _is_finite_scalar_positive(row.get("surface_m2")):
        reasons.append("invalid_surface")
    if not _clean(row.get("city")):
        reasons.append("missing_city")
    if not _clean(row.get("region")):
        reasons.append("missing_region")
    if normalized_text(row.get("validation_status")) not in {"valid", "warning"}:
        reasons.append("invalid_prior_validation")
    if row.get("duplicate_status_repaired") == "confirmed_duplicate" and not bool(row.get("duplicate_keep")):
        reasons.append("confirmed_duplicate")
    if row.get("outlier_decision") == "probable_error":
        reasons.append("probable_parsing_error")
    return "|".join(dict.fromkeys(reasons))


def _is_finite_scalar_positive(value: Any) -> bool:
    if _missing(value):
        return False
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0


@dataclass
class RepairResult:
    original: pd.DataFrame
    repaired: pd.DataFrame
    model_ready: pd.DataFrame
    exclusions: pd.DataFrame
    duplicate_groups: pd.DataFrame
    batch_audit: pd.DataFrame
    outlier_audit: pd.DataFrame
    neighborhood_rejections: pd.DataFrame
    report: dict[str, Any]
    paths: dict[str, Path]


def repair_dataset(original: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    frame = original.copy(deep=True).reset_index(drop=True)
    frame["property_type_original"] = frame["property_type"]
    property_results = frame.apply(classify_property_type, axis=1, result_type="expand")
    property_results.columns = ["property_type_repaired", "property_type_repair_evidence"]
    frame[property_results.columns] = property_results
    if not set(frame["property_type_repaired"].unique()).issubset(PROPERTY_CATEGORIES):
        raise AssertionError("property classifier produced an unsupported category")

    frame["neighborhood_original"] = frame["neighborhood"]
    neighborhood_results = frame.apply(
        lambda row: validate_neighborhood(row.get("neighborhood"), row.get("city")),
        axis=1,
        result_type="expand",
    )
    neighborhood_results.columns = [
        "neighborhood_clean",
        "neighborhood_validation_status",
        "neighborhood_rejection_reason",
    ]
    frame[neighborhood_results.columns] = neighborhood_results

    frame["region_original"] = frame["region"]
    repaired_region = frame["city"].map(REGION_BY_CITY)
    frame["region"] = repaired_region.fillna(frame["region_original"])
    frame["region_repair_status"] = np.where(
        frame["region"].eq(frame["region_original"]), "unchanged", "standardized_or_corrected"
    )

    frame["bedrooms_original"] = frame["bedrooms"]
    frame["bathrooms_original"] = frame["bathrooms"]
    non_applicable_bedrooms = frame["property_type_repaired"].isin(NON_APPLICABLE_BEDROOM_TYPES)
    frame.loc[non_applicable_bedrooms, "bedrooms"] = np.nan
    terrain = frame["property_type_repaired"].eq("terrain")
    commercial_zero_bath = (
        frame["property_type_repaired"].isin({"bureau", "local_commercial", "magasin"})
        & frame["bathrooms"].eq(0)
    )
    frame.loc[terrain | commercial_zero_bath, "bathrooms"] = np.nan

    frame["batch_id"] = frame["source_record_path"].map(_batch_id)
    frame["source_listing_id_normalized"] = frame["source_listing_id"].map(_normalize_source_id)
    frame["canonical_url_repaired"] = frame["url"].map(canonical_url)
    frame["normalized_title"] = frame["title_raw"].fillna("").map(normalized_text)

    batch_audit = audit_batches(frame)
    anomaly_by_batch = batch_audit.set_index("batch_id")["batch_anomaly_status"]
    frame["batch_anomaly_status"] = frame["batch_id"].map(anomaly_by_batch).fillna("not_flagged")
    frame, duplicate_groups = detect_duplicates(frame)
    frame = classify_outliers(frame, batch_audit)
    outlier_thresholds = dict(frame.attrs.get("outlier_thresholds", {}))
    frame["repair_exclusion_reason"] = frame.apply(_exclusion_reasons, axis=1)
    frame["is_model_ready"] = frame["repair_exclusion_reason"].eq("")

    neighborhood_rejections = frame.loc[
        frame["neighborhood_validation_status"].eq("invalid"),
        ["listing_id", "city", "neighborhood_original", "neighborhood_rejection_reason"],
    ].copy()
    outlier_audit = frame.loc[
        frame["outlier_decision"].ne("not_flagged"),
        [
            "listing_id",
            "outlier_decision",
            "outlier_reasons",
            "batch_id",
            "property_type_repaired",
            "city",
            "surface_m2",
            "price_mad",
            "price_per_m2",
            "bedrooms",
            "bathrooms",
            "title_raw",
            "price_raw",
            "url",
        ],
    ].copy()
    exclusions = frame.loc[
        ~frame["is_model_ready"],
        [
            "listing_id",
            "repair_exclusion_reason",
            "duplicate_group_id",
            "outlier_decision",
            "outlier_reasons",
            "source_record_path",
            "city",
            "property_type_repaired",
            "surface_m2",
            "price_mad",
            "price_per_m2",
            "title_raw",
            "price_raw",
            "url",
        ],
    ].copy()
    model_ready = frame.loc[frame["is_model_ready"]].copy().reset_index(drop=True)

    drop_internal = ["source_listing_id_normalized", "normalized_title"]
    model_ready = model_ready.drop(columns=drop_internal)
    frame = frame.drop(columns=drop_internal)
    return frame, {
        "model_ready": model_ready,
        "exclusions": exclusions,
        "duplicate_groups": duplicate_groups,
        "batch_audit": batch_audit,
        "outlier_audit": outlier_audit,
        "neighborhood_rejections": neighborhood_rejections,
        "outlier_thresholds": outlier_thresholds,
    }


def _percentiles(frame: pd.DataFrame, field: str) -> dict[str, float | None]:
    values = pd.to_numeric(frame[field], errors="coerce").dropna()
    if values.empty:
        return {key: None for key in ["min", "p01", "p05", "p25", "p50", "p75", "p95", "p99", "max"]}
    quantiles = values.quantile([0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99])
    return {
        "min": round(float(values.min()), 2),
        "p01": round(float(quantiles.loc[0.01]), 2),
        "p05": round(float(quantiles.loc[0.05]), 2),
        "p25": round(float(quantiles.loc[0.25]), 2),
        "p50": round(float(quantiles.loc[0.50]), 2),
        "p75": round(float(quantiles.loc[0.75]), 2),
        "p95": round(float(quantiles.loc[0.95]), 2),
        "p99": round(float(quantiles.loc[0.99]), 2),
        "max": round(float(values.max()), 2),
    }


def _missing_percent(frame: pd.DataFrame, fields: Iterable[str]) -> dict[str, float]:
    return {
        field: round(float(frame[field].isna().mean() * 100), 2)
        for field in fields
        if field in frame
    }


def _reason_counts(exclusions: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for value in exclusions["repair_exclusion_reason"].fillna(""):
        for reason in str(value).split("|"):
            if reason:
                counts[reason] += 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def build_quality_report(
    original: pd.DataFrame,
    repaired: pd.DataFrame,
    model_ready: pd.DataFrame,
    exclusions: pd.DataFrame,
    duplicate_groups: pd.DataFrame,
    batch_audit: pd.DataFrame,
    outlier_audit: pd.DataFrame,
    neighborhood_rejections: pd.DataFrame,
    outlier_thresholds: dict[str, Any],
    input_sha256: str,
) -> dict[str, Any]:
    city_counts = model_ready["city"].value_counts()
    city_coverage = [
        {
            "city": str(city),
            "listings": int(count),
            "percent": round(100 * int(count) / len(model_ready), 2),
            "low_sample": bool(count < 30),
        }
        for city, count in city_counts.items()
    ]
    changed_type = repaired["property_type_repaired"].ne(repaired["property_type_original"])
    confirmed_removed = int(
        repaired["duplicate_status_repaired"].eq("confirmed_duplicate").sum()
    )
    report = {
        "version": "model_ready_v1",
        "input": "data/processed/maisondelux_clean.csv",
        "input_sha256": input_sha256,
        "outputs": {
            "csv": "data/processed/maisondelux_model_ready_v1.csv",
            "parquet": "data/processed/maisondelux_model_ready_v1.parquet",
        },
        "summary": {
            "original_rows": int(len(original)),
            "final_model_ready_rows": int(len(model_ready)),
            "rows_removed": int(len(original) - len(model_ready)),
            "confirmed_duplicates_removed": confirmed_removed,
            "probable_parsing_errors_removed": int(
                repaired["outlier_decision"].eq("probable_error").sum()
            ),
            "possible_duplicates_retained": int(
                model_ready["duplicate_status_repaired"].eq("possible_duplicate").sum()
            ),
            "property_type_rows_changed": int(changed_type.sum()),
            "invalid_neighborhoods_detected": int(len(neighborhood_rejections)),
            "regions": int(model_ready["region"].nunique(dropna=True)),
            "cities": int(model_ready["city"].nunique(dropna=True)),
            "neighborhoods": int(model_ready["neighborhood_clean"].nunique(dropna=True)),
        },
        "exclusion_reason_counts": _reason_counts(exclusions),
        "exclusion_reason_explanations": EXCLUSION_EXPLANATIONS,
        "property_types_before": {
            str(k): int(v) for k, v in original["property_type"].fillna("<null>").value_counts().items()
        },
        "property_types_after": {
            str(k): int(v) for k, v in model_ready["property_type_repaired"].fillna("<null>").value_counts().items()
        },
        "property_type_evidence": {
            str(k): int(v)
            for k, v in repaired["property_type_repair_evidence"].fillna("<null>").value_counts().items()
        },
        "neighborhood_quality": {
            "valid_rows": int(repaired["neighborhood_validation_status"].eq("valid").sum()),
            "invalid_rows": int(repaired["neighborhood_validation_status"].eq("invalid").sum()),
            "rejection_reason_counts": {
                str(k): int(v)
                for k, v in neighborhood_rejections["neighborhood_rejection_reason"].value_counts().items()
            },
            "rejected_examples": neighborhood_rejections[
                ["city", "neighborhood_original", "neighborhood_rejection_reason"]
            ].drop_duplicates().head(30).to_dict("records"),
        },
        "duplicate_quality": {
            "confirmed_groups": int(
                duplicate_groups.loc[
                    duplicate_groups["duplicate_status_repaired"].isin(["unique", "confirmed_duplicate"]),
                    "duplicate_group_id",
                ].nunique()
            ),
            "confirmed_rows_removed": confirmed_removed,
            "possible_groups": int(
                duplicate_groups.loc[
                    duplicate_groups["duplicate_status_repaired"].eq("possible_duplicate"),
                    "duplicate_group_id",
                ].nunique()
            ),
            "possible_rows_retained": int(
                model_ready["duplicate_status_repaired"].eq("possible_duplicate").sum()
            ),
        },
        "batch_audit": batch_audit.replace({np.nan: None}).to_dict("records"),
        "outlier_decisions": {
            str(k): int(v) for k, v in repaired["outlier_decision"].value_counts().items()
        },
        "outlier_thresholds": outlier_thresholds,
        "missing_percent_final": _missing_percent(
            model_ready,
            [
                "price_mad",
                "surface_m2",
                "city",
                "region",
                "neighborhood_clean",
                "property_type_repaired",
                "bedrooms",
                "bathrooms",
                "url",
                "source_listing_id",
                "publication_date",
                "latitude",
                "longitude",
            ],
        ),
        "numeric_percentiles_final": {
            field: _percentiles(model_ready, field)
            for field in ["price_mad", "surface_m2", "price_per_m2"]
        },
        "geographic_coverage": {
            "regions": {
                str(k): int(v) for k, v in model_ready["region"].value_counts().items()
            },
            "cities": city_coverage,
            "low_sample_city_threshold": 30,
        },
        "feature_audit": {
            "target": TARGET,
            "safe_candidate_features": SAFE_CANDIDATE_FEATURES,
            "exclude_from_model": EXCLUDE_FROM_MODEL,
            "exclusion_rationale": {
                "target_leakage": ["price_per_m2", "price_per_m2_original", "price_per_m2_recomputed"],
                "raw_identifiers_or_traceability": ["listing_id", "source_listing_id", "url", "canonical_url_repaired", "source_record_path"],
                "unstructured_raw_evidence": ["title_raw", "details_raw", "location_raw", "price_raw"],
                "unavailable_or_temporal_provenance": ["publication_date", "publication_date_status", "scraped_at"],
                "quality_control_metadata": [
                    "validation_status", "validation_reasons", "deduplication_status", "duplicate_of",
                    "duplicate_status_repaired", "duplicate_group_id", "duplicate_match_level",
                    "duplicate_keep", "batch_id", "batch_anomaly_status", "numeric_consistency_status",
                    "outlier_decision", "outlier_reasons", "repair_exclusion_reason",
                ],
            },
        },
    }
    if report["summary"]["rows_removed"] != len(exclusions):
        raise AssertionError("row-removal reconciliation failed")
    return report


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def write_quality_report(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = report["summary"]
    summary_rows = [{"metric": key, "value": value} for key, value in summary.items()]
    exclusion_rows = [
        {
            "reason": reason,
            "rows": count,
            "explanation": report["exclusion_reason_explanations"].get(reason, ""),
        }
        for reason, count in report["exclusion_reason_counts"].items()
    ]
    batch_rows = [
        {
            "batch_id": row["batch_id"],
            "rows": row["row_count"],
            "median_ppm": round(row["median_price_per_m2"], 2),
            "p95_ppm": round(row["p95_price_per_m2"], 2),
            "p99_ppm": round(row["p99_price_per_m2"], 2),
            "status": row["batch_anomaly_status"],
        }
        for row in report["batch_audit"]
    ]
    lines = [
        "# MaisonDeLUX model-ready dataset v1",
        "",
        "The original CSV remains unchanged. Publication dates and coordinates were not fabricated.",
        "",
        "## Summary",
        "",
        *_markdown_table(summary_rows, ["metric", "value"]),
        "",
        "## Exclusions",
        "",
        *_markdown_table(exclusion_rows, ["reason", "rows", "explanation"]),
        "",
        "## Property types after repair",
        "",
        *_markdown_table(
            [{"property_type": key, "rows": value} for key, value in report["property_types_after"].items()],
            ["property_type", "rows"],
        ),
        "",
        "## Batch audit",
        "",
        *_markdown_table(batch_rows, ["batch_id", "rows", "median_ppm", "p95_ppm", "p99_ppm", "status"]),
        "",
        "## Missing values in final data",
        "",
        *_markdown_table(
            [{"field": key, "missing_percent": value} for key, value in report["missing_percent_final"].items()],
            ["field", "missing_percent"],
        ),
        "",
        "## Modeling feature policy",
        "",
        f"Target: `{', '.join(report['feature_audit']['target'])}`",
        "",
        "Safe candidates: " + ", ".join(f"`{item}`" for item in report["feature_audit"]["safe_candidate_features"]),
        "",
        "`price_per_m2` and both derived price/m² audit columns are excluded because they directly encode the target.",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_repair(project_root: Path) -> RepairResult:
    project_root = Path(project_root)
    input_path = project_root / "data" / "processed" / "maisondelux_clean.csv"
    output_csv = project_root / "data" / "processed" / "maisondelux_model_ready_v1.csv"
    output_parquet = project_root / "data" / "processed" / "maisondelux_model_ready_v1.parquet"
    report_dir = project_root / "reports" / "data_quality"
    paths = {
        "csv": output_csv,
        "parquet": output_parquet,
        "report_json": report_dir / "model_ready_v1_quality_report.json",
        "report_markdown": report_dir / "model_ready_v1_quality_report.md",
        "exclusions": report_dir / "model_ready_v1_exclusions.csv",
        "duplicate_groups": report_dir / "model_ready_v1_duplicate_groups.csv",
        "batch_audit": report_dir / "model_ready_v1_batch_audit.csv",
        "outlier_audit": report_dir / "model_ready_v1_outlier_audit.csv",
        "neighborhood_rejections": report_dir / "model_ready_v1_neighborhood_rejections.csv",
    }

    input_hash_before = _sha256(input_path)
    original = pd.read_csv(input_path, low_memory=False)
    repaired, artifacts = repair_dataset(original)
    model_ready = artifacts["model_ready"]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    model_ready.to_csv(output_csv, index=False, encoding="utf-8")
    model_ready.to_parquet(output_parquet, index=False)
    artifacts["exclusions"].to_csv(paths["exclusions"], index=False, encoding="utf-8")
    artifacts["duplicate_groups"].to_csv(paths["duplicate_groups"], index=False, encoding="utf-8")
    artifacts["batch_audit"].to_csv(paths["batch_audit"], index=False, encoding="utf-8")
    artifacts["outlier_audit"].to_csv(paths["outlier_audit"], index=False, encoding="utf-8")
    artifacts["neighborhood_rejections"].to_csv(
        paths["neighborhood_rejections"], index=False, encoding="utf-8"
    )

    if _sha256(input_path) != input_hash_before:
        raise AssertionError("source CSV changed during repair")
    csv_check = pd.read_csv(output_csv, low_memory=False)
    parquet_check = pd.read_parquet(output_parquet)
    if csv_check.shape != model_ready.shape or parquet_check.shape != model_ready.shape:
        raise AssertionError("saved output shape does not match the in-memory model-ready data")
    if not model_ready["repair_exclusion_reason"].eq("").all():
        raise AssertionError("model-ready data contains an excluded row")
    if not _is_finite_positive(model_ready["price_mad"]).all():
        raise AssertionError("model-ready data contains unusable prices")
    if not _is_finite_positive(model_ready["surface_m2"]).all():
        raise AssertionError("model-ready data contains unusable surfaces")
    if model_ready["city"].isna().any() or model_ready["region"].isna().any():
        raise AssertionError("model-ready data contains missing city/region")
    if model_ready["duplicate_status_repaired"].eq("confirmed_duplicate").any():
        raise AssertionError("model-ready data contains a confirmed duplicate row")
    if model_ready["outlier_decision"].eq("probable_error").any():
        raise AssertionError("model-ready data contains a probable numeric error")
    if "price_per_m2" in SAFE_CANDIDATE_FEATURES:
        raise AssertionError("price_per_m2 leakage entered the safe feature list")

    report = build_quality_report(
        original,
        repaired,
        model_ready,
        artifacts["exclusions"],
        artifacts["duplicate_groups"],
        artifacts["batch_audit"],
        artifacts["outlier_audit"],
        artifacts["neighborhood_rejections"],
        artifacts["outlier_thresholds"],
        input_hash_before,
    )
    report["output_sha256"] = {
        "csv": _sha256(output_csv),
        "parquet": _sha256(output_parquet),
    }
    write_quality_report(report, paths["report_json"], paths["report_markdown"])
    return RepairResult(
        original=original,
        repaired=repaired,
        model_ready=model_ready,
        exclusions=artifacts["exclusions"],
        duplicate_groups=artifacts["duplicate_groups"],
        batch_audit=artifacts["batch_audit"],
        outlier_audit=artifacts["outlier_audit"],
        neighborhood_rejections=artifacts["neighborhood_rejections"],
        report=report,
        paths=paths,
    )
