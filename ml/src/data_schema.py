"""Deterministic parsing and validation shared by recovery and source adapters.

Missing values remain ``None``.  Price-per-square-metre is audit-only and is
explicitly forbidden from model feature matrices.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


AMENITIES = [
    "elevator", "parking", "garage", "terrace", "balcony", "garden", "pool",
    "furnished", "security", "concierge", "air_conditioning", "heating",
    "fireplace", "equipped_kitchen", "double_glazing", "sea_view",
    "mountain_view", "title_deed",
]
SCHEMA_V2_COLUMNS = [
    "listing_id", "listing_id_strategy", "source", "url", "scraped_at", "listing_date",
    "transaction_type", "transaction_parse_reason", "currency", "raw_price_text", "price",
    "price_parse_status", "price_parse_reason", "city", "quartier", "address_text", "latitude",
    "longitude", "location_parse_status", "property_type", "property_type_parse_status",
    "surface_total_m2", "surface_built_m2", "surface_land_m2", "surface_parse_status",
    "surface_parse_reason", "rooms", "bedrooms", "bathrooms", "floor", "total_floors",
    "construction_year", "condition", "new_construction", "renovated", *AMENITIES,
    "proximity_text", "validation_status", "validation_reasons", "model_eligible",
    "model_exclusion_reasons", "price_per_m2_audit", "quality_score", "title_raw",
    "description_raw", "location_raw", "details_raw", "attributes_raw",
]
SCHEMA_V3_COLUMNS = [
    "schema_version", "listing_id", "listing_id_strategy", "duplicate_group_key", "source",
    "source_category", "url", "source_page_url", "search_page_number", "position_on_page",
    "scraped_at", "listing_date", "transaction_type", "transaction_parse_status",
    "transaction_parse_reason", "currency", "raw_price_text", "price_value", "price_mad",
    "price", "price_parse_status", "price_parse_reason", "price_per_m2_audit", "city",
    "quartier", "address_text", "latitude", "longitude", "location_parse_status",
    "property_type", "property_type_parse_status", "surface_total_m2", "surface_built_m2",
    "surface_land_m2", "surface_parse_status", "surface_parse_reason", "rooms", "bedrooms",
    "bathrooms", "living_rooms", "kitchens", "floor", "total_floors", "construction_year",
    "condition", "new_construction", "renovated", "furnished", "elevator", "parking",
    "garage", "terrace", "balcony", "garden", "pool", "security", "concierge",
    "air_conditioning", "heating", "fireplace", "equipped_kitchen", "double_glazing",
    "sea_view", "mountain_view", "title_deed", "seller_type", "seller_name",
    "proximity_text", "title_raw", "description_raw", "details_raw", "location_raw",
    "attributes_raw", "validation_status", "validation_reasons", "model_eligible",
    "model_exclusion_reasons", "quality_score",
]
MODEL_FORBIDDEN_COLUMNS = {
    "price_mad", "price", "raw_price_text", "price_value", "price_per_m2",
    "price_per_m2_audit", "validation_status", "validation_reasons",
}

CITY_ALIASES = {
    "agadir": "Agadir", "beni mellal": "Béni Mellal", "berrechid": "Berrechid",
    "casablanca": "Casablanca", "casa": "Casablanca", "dar el beida": "Casablanca",
    "dakhla": "Dakhla", "el jadida": "El Jadida", "essaouira": "Essaouira",
    "fes": "Fès", "fez": "Fès", "kenitra": "Kénitra", "khemisset": "Khémisset",
    "khouribga": "Khouribga", "laayoune": "Laâyoune", "larache": "Larache",
    "marrakech": "Marrakech", "marrakesh": "Marrakech", "meknes": "Meknès",
    "mohammedia": "Mohammedia", "nador": "Nador", "ouarzazate": "Ouarzazate",
    "oujda": "Oujda", "rabat": "Rabat", "safi": "Safi", "sale": "Salé",
    "settat": "Settat", "tanger": "Tanger", "tangier": "Tanger", "tan tan": "Tan-Tan",
    "temara": "Témara", "tetouan": "Tétouan", "tiznit": "Tiznit",
}
GENERIC_NEIGHBORHOODS = {
    "", "accueil", "appartement", "appartements", "maroc", "publier une annonce",
    "vendre", "vendre a", "vente", "location", "immobilier",
}
PROPERTY_PATTERNS = [
    ("studio", r"\bstudio\b"), ("duplex", r"\bduplexe?\b"),
    ("villa", r"\bvilla\b"), ("maison", r"\bmaison\b"),
    ("terrain", r"\bterrain\b|\blot\b"), ("bureau", r"\bbureau\b|\boffice\b"),
    ("commerce", r"\bcommerce\b|\blocal commercial\b"),
    ("appartement", r"\bappartement(?:s)?\b|\bappart\b"),
]
AMENITY_PATTERNS = {
    "elevator": (r"\bascenseur\b|\blift\b|مصعد", r"sans ascenseur|pas d[' ]ascenseur"),
    "parking": (r"\bparking\b|place de voiture", r"sans parking|pas de parking"),
    "garage": (r"\bgarage\b|مراب", r"sans garage|pas de garage"),
    "terrace": (r"\bterrasse\b|rooftop|roof top", r"sans terrasse"),
    "balcony": (r"\bbalcon\b|شرفة", r"sans balcon"),
    "garden": (r"\bjardin\b|rez de jardin|حديقة", r"sans jardin"),
    "pool": (r"\bpiscine\b|مسبح", r"sans piscine"),
    "furnished": (r"\bmeubl[ée]\b|furnished|مفروش", r"non meuble|sans meubles?|vendu vide"),
    "security": (r"securis|securite|surveillance", r"sans securite"),
    "concierge": (r"\bconcierge\b|\bgardien\b", r"sans concierge|sans gardien"),
    "air_conditioning": (r"climatis|air conditionne", r"sans climatisation"),
    "heating": (r"\bchauffage\b", r"sans chauffage"),
    "fireplace": (r"\bcheminee\b", r"sans cheminee"),
    "equipped_kitchen": (r"cuisine equipee", r"cuisine non equipee"),
    "double_glazing": (r"double vitrage", r"sans double vitrage"),
    "sea_view": (r"vue (?:sur )?mer|front de mer|bord de mer", r"sans vue mer"),
    "mountain_view": (r"vue (?:sur )?(?:montagne|atlas)", r"sans vue montagne"),
    "title_deed": (r"titre foncier|titre individuel|melkia", r"sans titre|non titre"),
}


def normalize_for_matching(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", text).strip()


def clean_raw_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if text and text.casefold() not in {"nan", "none", "null", "<na>"} else None


def canonicalize_url(url: str | None) -> str | None:
    url = clean_raw_text(url)
    if not url:
        return None
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query) if not key.casefold().startswith("utm_") and key.casefold() not in {"fbclid", "gclid"}]
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/") or "/"
    return urlunsplit((parts.scheme.casefold() or "https", parts.netloc.casefold(), path, urlencode(query), ""))


def parse_price(value: Any, transaction_type: str | None = None) -> dict[str, Any]:
    raw = clean_raw_text(value)
    result = {"raw_price_text": raw, "price": None, "currency": None,
              "price_parse_status": "MISSING", "price_parse_reason": "missing"}
    if raw is None:
        return result
    text = normalize_for_matching(raw).replace("m²", "m2")
    if re.search(r"a consulter|sur demande|nous consulter|contact", text):
        result.update(price_parse_status="MISSING", price_parse_reason="price_on_request")
        return result
    if re.search(r"(?:/|par)\s*m2|m2", text) and re.search(r"dh|mad|eur", text):
        result.update(price_parse_status="INVALID", price_parse_reason="price_per_m2_not_total")
        return result
    currency = "EUR" if re.search(r"\beur\b|€", raw.casefold()) else "MAD" if re.search(r"\bdh?s?\b|\bmad\b", text) else None
    match = re.search(r"(?<!\d)(\d[\d\s\u00a0.,]*)(?:\s*)(million(?:s)?|mille|k|m)?", raw.casefold())
    if not match:
        result.update(currency=currency, price_parse_status="INVALID", price_parse_reason="unparseable")
        return result
    number_text = re.sub(r"[\s\u00a0]", "", match.group(1)).strip(".,")
    multiplier = 1.0
    marker = (match.group(2) or "").casefold()
    if marker.startswith("million") or marker == "m":
        multiplier = 1_000_000.0
    elif marker in {"mille", "k"}:
        multiplier = 1_000.0
    if multiplier > 1 and re.fullmatch(r"\d+[.,]\d+", number_text):
        number_text = number_text.replace(",", ".")
    else:
        number_text = number_text.replace(",", "").replace(".", "")
    try:
        parsed = float(number_text) * multiplier
    except ValueError:
        result.update(currency=currency, price_parse_status="INVALID", price_parse_reason="unparseable")
        return result
    if not (0 < parsed < 10_000_000_000):
        result.update(currency=currency, price_parse_status="INVALID", price_parse_reason="out_of_range")
        return result
    result.update(price=int(parsed) if parsed.is_integer() else parsed, currency=currency,
                  price_parse_status="PARSED" if currency else "WARNING",
                  price_parse_reason="ok" if currency else "currency_unknown")
    return result


def classify_transaction(title: Any = None, details: Any = None, url: Any = None, source_category: Any = None) -> dict[str, str]:
    text = normalize_for_matching(" ".join(filter(None, map(clean_raw_text, [title, details, url, source_category]))))
    sale = bool(re.search(r"\ba vendre\b|\bvente\b|\bacheter\b|\bachat\b|for sale", text))
    rent = bool(re.search(r"\ba louer\b|\blocation\b|\bloyer\b|par mois|mensuel|for rent", text))
    if sale and not rent:
        return {"transaction_type": "SALE", "transaction_parse_reason": "explicit_sale_signal"}
    if rent and not sale:
        return {"transaction_type": "RENT", "transaction_parse_reason": "explicit_rent_signal"}
    return {"transaction_type": "UNKNOWN", "transaction_parse_reason": "conflict" if sale and rent else "no_reliable_signal"}


def parse_surfaces(value: Any) -> dict[str, Any]:
    raw = clean_raw_text(value)
    result = {"surface_total_m2": None, "surface_built_m2": None, "surface_land_m2": None,
              "surface_parse_status": "MISSING", "surface_parse_reason": "missing"}
    if raw is None:
        return result
    text = normalize_for_matching(raw)
    matches = [(m.start(), float(m.group(1).replace(",", "."))) for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*m(?:2|²)\b", text)]
    if not matches:
        return result
    for position, number in matches:
        context = text[max(0, position - 35):position]
        if re.search(r"habitable|construite|bati|utile", context):
            result["surface_built_m2"] = number
        elif re.search(r"terrain|parcelle|foncier", context):
            result["surface_land_m2"] = number
        elif len(matches) == 1:
            result["surface_total_m2"] = number
    parsed_count = sum(result[key] is not None for key in ("surface_total_m2", "surface_built_m2", "surface_land_m2"))
    result.update(surface_parse_status="PARSED" if parsed_count else "WARNING",
                  surface_parse_reason="ok" if parsed_count else "multiple_unlabelled_surfaces")
    return result


def valid_neighborhood(value: Any) -> bool:
    normalized = normalize_for_matching(value)
    return bool(
        normalized and normalized not in GENERIC_NEIGHBORHOODS and len(normalized) >= 3
        and not re.search(r"publier|annonce|accueil|appartements?|\bvente\b|\bvendre\b|\bmaroc\b|\d+\s*m2", normalized)
    )


def parse_location(value: Any) -> dict[str, Any]:
    raw = clean_raw_text(value)
    result = {"quartier": None, "city": None, "address_text": raw, "location_parse_status": "MISSING"}
    if raw is None:
        return result
    parts = [part.strip() for part in re.split(r"[,|>]", raw) if part.strip()]
    city_index = None
    for index in range(len(parts) - 1, -1, -1):
        normalized = normalize_for_matching(parts[index])
        if normalized in CITY_ALIASES:
            result["city"] = CITY_ALIASES[normalized]
            city_index = index
            break
    if city_index is not None and city_index > 0 and valid_neighborhood(parts[city_index - 1]):
        result["quartier"] = parts[city_index - 1]
    elif len(parts) == 1 and normalize_for_matching(parts[0]) in CITY_ALIASES:
        result["city"] = CITY_ALIASES[normalize_for_matching(parts[0])]
    result["location_parse_status"] = "PARSED" if result["city"] and result["quartier"] else "CITY_ONLY" if result["city"] else "AMBIGUOUS"
    return result


def extract_amenities(value: Any) -> dict[str, bool | None]:
    text = normalize_for_matching(value)
    result: dict[str, bool | None] = {}
    for field, (positive, negative) in AMENITY_PATTERNS.items():
        result[field] = False if re.search(negative, text) else True if re.search(positive, text) else None
    return result


def _first_number(pattern: str, value: Any) -> int | None:
    match = re.search(pattern, normalize_for_matching(value))
    return int(match.group(1)) if match else None


def infer_property_type(*values: Any) -> tuple[str | None, str]:
    text = normalize_for_matching(" ".join(str(value) for value in values if value is not None))
    matches = [kind for kind, pattern in PROPERTY_PATTERNS if re.search(pattern, text)]
    return (matches[0], "PARSED") if len(set(matches)) == 1 else (None, "AMBIGUOUS" if matches else "MISSING")


def normalize_iso_date(value: Any) -> str | None:
    raw = clean_raw_text(value)
    if not raw:
        return None
    candidate = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def make_listing_id(source: str, native_id: Any = None, url: Any = None, title: Any = None,
                    location: Any = None, surface_m2: Any = None, price: Any = None) -> tuple[str, str]:
    source_key = normalize_for_matching(source).replace(" ", ".") or "unknown"
    native = clean_raw_text(native_id)
    if native:
        return f"{source_key}:native:{native}", "native_id"
    canonical = canonicalize_url(clean_raw_text(url))
    if canonical:
        digest = hashlib.sha256(canonical.encode()).hexdigest()[:24]
        return f"{source_key}:url:{digest}", "canonical_url"
    evidence = "|".join([source_key, normalize_for_matching(title), normalize_for_matching(location), str(surface_m2 or ""), str(price or "")])
    digest = hashlib.sha256(evidence.encode()).hexdigest()[:24]
    return f"{source_key}:content:{digest}", "content_fingerprint"


def _bool_or_none(value: Any) -> bool | None:
    if value is None or clean_raw_text(value) is None:
        return None
    if isinstance(value, bool):
        return value
    normalized = normalize_for_matching(value)
    if normalized in {"yes", "oui", "true", "1", "furnished", "meuble"}:
        return True
    if normalized in {"no", "non", "false", "0", "unfurnished", "non meuble"}:
        return False
    return None


def _validate(record: dict[str, Any]) -> tuple[str, str, bool, str, float]:
    reasons: list[str] = []
    model_reasons: list[str] = []
    price = record.get("price_mad", record.get("price"))
    surface = record.get("surface_total_m2")
    transaction = record.get("transaction_type")
    if transaction == "RENT":
        reasons.append("rental_listing")
        model_reasons.append("not_sale")
    elif transaction != "SALE":
        reasons.append("unknown_transaction")
        model_reasons.append("not_confirmed_sale")
    if price is None:
        reasons.append("missing_price")
        model_reasons.append("missing_target")
    elif not (50_000 <= float(price) <= 500_000_000):
        reasons.append("implausible_price")
        model_reasons.append("implausible_target")
    if surface is None:
        reasons.append("missing_surface")
        model_reasons.append("missing_surface")
    elif not (10 <= float(surface) <= 100_000):
        reasons.append("implausible_surface")
        model_reasons.append("implausible_surface")
    if not record.get("city"):
        reasons.append("missing_city")
        model_reasons.append("missing_city")
    if record.get("quartier") and not valid_neighborhood(record["quartier"]):
        reasons.append("invalid_neighborhood")
    price_per_m2 = round(float(price) / float(surface), 2) if price and surface and float(surface) > 0 else None
    if price_per_m2 is not None and record.get("property_type") in {"appartement", "studio", "villa", "maison", "duplex"} and not (1_000 <= price_per_m2 <= 150_000):
        reasons.append("price_per_m2_outlier")
        model_reasons.append("price_per_m2_outlier")
    for field, low, high in (("bedrooms", 0, 20), ("bathrooms", 0, 15), ("rooms", 0, 40)):
        value = record.get(field)
        if value is not None and not (low <= float(value) <= high):
            reasons.append(f"implausible_{field}")
    hard = {"rental_listing", "missing_price", "implausible_price", "missing_surface", "implausible_surface", "missing_city"}
    status = "INVALID" if hard.intersection(reasons) else "WARNING" if reasons else "VALID"
    quality = max(0.0, round(1.0 - 0.12 * len(set(reasons)), 2))
    return status, "|".join(dict.fromkeys(reasons)), not model_reasons, "|".join(dict.fromkeys(model_reasons)), price_per_m2


def build_v2_record(evidence: dict[str, Any], source: str | None = None) -> dict[str, Any]:
    if source:
        evidence = {**evidence, "source": source}
    title = clean_raw_text(evidence.get("title_raw"))
    description = clean_raw_text(evidence.get("description_raw"))
    details = clean_raw_text(evidence.get("details_raw"))
    location_raw = clean_raw_text(evidence.get("location_raw") or evidence.get("address_text"))
    transaction = {"transaction_type": str(evidence.get("transaction_type")).upper(), "transaction_parse_reason": "source_explicit"} if evidence.get("transaction_type") else classify_transaction(title, details, evidence.get("url"), evidence.get("source_category"))
    parsed_price = parse_price(evidence.get("raw_price_text"), transaction["transaction_type"])
    if evidence.get("price_value") is not None:
        parsed_price.update(price=evidence.get("price_value"), currency=evidence.get("currency") or "MAD", price_parse_status="PARSED", price_parse_reason="structured_value")
    parsed_surface = parse_surfaces(details or title)
    for field in ("surface_total_m2", "surface_built_m2", "surface_land_m2"):
        if evidence.get(field) is not None:
            parsed_surface[field] = evidence[field]
            parsed_surface.update(surface_parse_status="PARSED", surface_parse_reason="structured_value")
    location = parse_location(location_raw)
    for field in ("city", "quartier", "address_text"):
        if clean_raw_text(evidence.get(field)):
            location[field] = clean_raw_text(evidence[field])
    if location.get("city"):
        location["city"] = CITY_ALIASES.get(normalize_for_matching(location["city"]), location["city"])
        location["location_parse_status"] = "PARSED" if location.get("quartier") else "CITY_ONLY"
    property_type, property_status = infer_property_type(evidence.get("property_type"), title, details, evidence.get("source_category"))
    amenities = extract_amenities(" ".join(filter(None, [title, description, details])))
    for field in AMENITIES:
        if field in evidence:
            amenities[field] = _bool_or_none(evidence.get(field))
    surface_for_id = parsed_surface["surface_total_m2"]
    listing_id, strategy = make_listing_id(
        clean_raw_text(evidence.get("source")) or "mubawab.ma", evidence.get("native_id"),
        evidence.get("url"), title, location_raw, surface_for_id, parsed_price["price"],
    )
    record: dict[str, Any] = {
        "listing_id": listing_id, "listing_id_strategy": strategy,
        "source": clean_raw_text(evidence.get("source")) or "mubawab.ma",
        "url": canonicalize_url(evidence.get("url")),
        "scraped_at": normalize_iso_date(evidence.get("scraped_at")) or datetime.now(timezone.utc).isoformat(),
        "listing_date": normalize_iso_date(evidence.get("listing_date")),
        **transaction, **parsed_price, **location,
        "latitude": evidence.get("latitude"), "longitude": evidence.get("longitude"),
        "property_type": property_type, "property_type_parse_status": property_status,
        **parsed_surface,
        "rooms": evidence.get("rooms") if evidence.get("rooms") is not None else _first_number(r"(\d+)\s*(?:pieces?|rooms?)", details),
        "bedrooms": evidence.get("bedrooms") if evidence.get("bedrooms") is not None else _first_number(r"(\d+)\s*(?:chambres?|ch\b|bedrooms?)", details),
        "bathrooms": evidence.get("bathrooms") if evidence.get("bathrooms") is not None else _first_number(r"(\d+)\s*(?:salles? de bains?|sdb|bathrooms?)", details),
        "floor": evidence.get("floor"), "total_floors": evidence.get("total_floors"),
        "construction_year": evidence.get("construction_year"), "condition": clean_raw_text(evidence.get("condition")),
        "new_construction": _bool_or_none(evidence.get("new_construction")), "renovated": _bool_or_none(evidence.get("renovated")),
        **amenities, "proximity_text": clean_raw_text(evidence.get("proximity_text")),
        "title_raw": title, "description_raw": description, "location_raw": location_raw,
        "details_raw": details, "attributes_raw": clean_raw_text(evidence.get("attributes_raw")),
    }
    status, reasons, eligible, model_reasons, ppm2 = _validate(record)
    record.update(validation_status=status, validation_reasons=reasons, model_eligible=eligible,
                  model_exclusion_reasons=model_reasons, price_per_m2_audit=ppm2,
                  quality_score=max(0.0, round(1.0 - 0.12 * len([r for r in reasons.split("|") if r]), 2)))
    return {column: record.get(column) for column in SCHEMA_V2_COLUMNS}


def build_v3_record(evidence: dict[str, Any], source: str | None = None) -> dict[str, Any]:
    if source:
        evidence = {**evidence, "source": source}
    v2 = build_v2_record(evidence)
    price = v2.get("price")
    duplicate_basis = "|".join(normalize_for_matching(v2.get(field)) for field in ("city", "quartier", "property_type")) + f"|{v2.get('surface_total_m2')}|{price}|{v2.get('bedrooms')}"
    extra = {
        "schema_version": "3.1", "duplicate_group_key": hashlib.sha256(duplicate_basis.encode()).hexdigest()[:24],
        "source_category": clean_raw_text(evidence.get("source_category")),
        "source_page_url": canonicalize_url(evidence.get("source_page_url") or evidence.get("source_result_url")),
        "search_page_number": evidence.get("search_page_number") or evidence.get("source_page"),
        "position_on_page": evidence.get("position_on_page") or evidence.get("source_position"),
        "transaction_parse_status": evidence.get("transaction_parse_status") or ("PARSED" if v2.get("transaction_type") != "UNKNOWN" else "WARNING"),
        "price_value": evidence.get("price_value", price), "price_mad": price if v2.get("currency") in {None, "MAD"} else None,
        "living_rooms": evidence.get("living_rooms"), "kitchens": evidence.get("kitchens"),
        "seller_type": clean_raw_text(evidence.get("seller_type")), "seller_name": clean_raw_text(evidence.get("seller_name")),
    }
    combined = {**v2, **extra}
    return {column: combined.get(column) for column in SCHEMA_V3_COLUMNS}
