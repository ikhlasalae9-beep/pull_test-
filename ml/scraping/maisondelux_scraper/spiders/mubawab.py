from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import urljoin, urlsplit

import scrapy


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[4]
SRC_DIR = REPO_ROOT / "ml" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_schema import SCHEMA_V3_COLUMNS, build_v3_record, canonicalize_url  # noqa: E402
from ..persistence import (  # noqa: E402
    identity_keys,
    load_identity_index,
    native_id_from_url,
)


# These are first-page, public city URLs. The four accented slugs are the
# canonical URLs returned by Mubawab; their former ASCII variants returned
# errors/404s and are intentionally absent.
CITY_SEEDS: tuple[tuple[str, str], ...] = (
    ("Casablanca", "https://www.mubawab.ma/fr/st/casablanca/appartements-a-vendre"),
    ("Marrakech", "https://www.mubawab.ma/fr/st/marrakech/appartements-a-vendre"),
    ("Tanger", "https://www.mubawab.ma/fr/st/tanger/appartements-a-vendre"),
    ("Rabat", "https://www.mubawab.ma/fr/st/rabat/appartements-a-vendre"),
    ("Agadir", "https://www.mubawab.ma/fr/st/agadir/appartements-a-vendre"),
    ("Fès", "https://www.mubawab.ma/fr/st/f%C3%A8s/appartements-a-vendre"),
    ("Kénitra", "https://www.mubawab.ma/fr/st/k%C3%A9nitra/appartements-a-vendre"),
    ("Salé", "https://www.mubawab.ma/fr/st/sal%C3%A9/appartements-a-vendre"),
    ("Temara", "https://www.mubawab.ma/fr/st/temara/appartements-a-vendre"),
    ("Mohammedia", "https://www.mubawab.ma/fr/st/mohammedia/appartements-a-vendre"),
    ("El Jadida", "https://www.mubawab.ma/fr/st/el-jadida/appartements-a-vendre"),
    ("Meknes", "https://www.mubawab.ma/fr/st/meknes/appartements-a-vendre"),
    ("Oujda", "https://www.mubawab.ma/fr/st/oujda/appartements-a-vendre"),
    ("Tétouan", "https://www.mubawab.ma/fr/st/t%C3%A9touan/appartements-a-vendre"),
)

PROPERTY_TYPES = {
    "apartment": "appartement",
    "house": "maison",
    "singlefamilyresidence": "maison",
    "residence": "maison",
    "villa": "villa",
    "land": "terrain",
    "office": "bureau",
}

AMENITY_LABELS = {
    "meuble": "furnished",
    "meublee": "furnished",
    "ascenseur": "elevator",
    "parking": "parking",
    "garage": "garage",
    "terrasse": "terrace",
    "balcon": "balcony",
    "jardin": "garden",
    "piscine": "pool",
    "securite": "security",
    "concierge": "concierge",
    "gardien": "concierge",
    "climatisation": "air_conditioning",
    "chauffage": "heating",
    "cheminee": "fireplace",
    "cuisine equipee": "equipped_kitchen",
    "double vitrage": "double_glazing",
    "vue sur mer": "sea_view",
    "vue mer": "sea_view",
    "vue sur les montagnes": "mountain_view",
    "vue montagne": "mountain_view",
    "titre foncier": "title_deed",
}

NOISE_LOCATION = {
    "ecoles",
    "hopitaux",
    "pharmacies",
    "restaurants",
    "supermarches",
    "voir la carte",
    "map",
    "carte",
}


@dataclass(frozen=True)
class ListingReference:
    native_id: str
    url: str
    source_page_url: str
    seed_index: int
    position_on_page: int
    seed_city: str


def clean(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def normalize_key(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip()


def walk_json(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk_json(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_json(value)


def _schema_type_names(value: Any) -> set[str]:
    values = value if isinstance(value, list) else [value]
    names = set()
    for item in values:
        if not isinstance(item, str):
            continue
        name = re.split(r"[/#:]", item)[-1]
        if name:
            names.add(name)
    return names


def _first_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return next((item for item in value if isinstance(item, dict)), {})
    return {}


def _scalar(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("value", value.get("@value"))
    return value


def find_real_estate_listing(response: scrapy.http.Response) -> dict[str, Any] | None:
    scripts = response.css('script[type="application/ld+json"]::text').getall()
    for raw in scripts:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        for obj in walk_json(parsed):
            if "RealEstateListing" in _schema_type_names(obj.get("@type")):
                return obj
    return None


def _property_type(offered: dict[str, Any]) -> str | None:
    candidates: list[str] = []
    for value in (offered.get("@type"), offered.get("additionalType")):
        candidates.extend(_schema_type_names(value))
    for candidate in candidates:
        normalized = normalize_key(candidate).replace(" ", "")
        if normalized in PROPERTY_TYPES:
            return PROPERTY_TYPES[normalized]
        for key, canonical in PROPERTY_TYPES.items():
            if key in normalized:
                return canonical
    return None


def _surface_m2(floor_size: Any) -> Any:
    if not isinstance(floor_size, dict):
        return _scalar(floor_size)
    unit = normalize_key(floor_size.get("unitCode") or floor_size.get("unitText"))
    if unit and unit not in {"mtr", "mtk", "m2", "m²", "square metre", "square meter"}:
        return None
    return _scalar(floor_size)


def jsonld_evidence(ld: dict[str, Any] | None) -> dict[str, Any]:
    """Extract primary evidence exclusively from RealEstateListing JSON-LD."""
    if not ld:
        return {}

    offered = _first_mapping(ld.get("itemOffered") or ld.get("mainEntity"))
    offer = _first_mapping(ld.get("offers"))
    price_spec = _first_mapping(offer.get("priceSpecification"))
    address = _first_mapping(offered.get("address") or ld.get("address"))
    seller = _first_mapping(ld.get("seller") or offer.get("seller") or ld.get("provider"))
    geo = _first_mapping(offered.get("geo") or ld.get("geo"))

    price = _scalar(offer.get("price"))
    if price in (None, ""):
        price = _scalar(price_spec.get("price"))
    currency = offer.get("priceCurrency") or price_spec.get("priceCurrency")

    seller_types = _schema_type_names(seller.get("@type"))
    seller_type = None
    if "RealEstateAgent" in seller_types:
        seller_type = "AGENCY"
    elif "Person" in seller_types:
        seller_type = "OWNER"

    evidence = {
        "title_raw": clean(ld.get("name") or ld.get("headline")),
        "description_raw": clean(ld.get("description")),
        "price_value": price,
        "currency": clean(currency),
        "city": clean(address.get("addressLocality")),
        "address_text": clean(address.get("streetAddress"))
        or clean(address.get("addressLocality")),
        "property_type": _property_type(offered),
        "surface_total_m2": _surface_m2(offered.get("floorSize")),
        "rooms": _scalar(offered.get("numberOfRooms")),
        "bedrooms": _scalar(offered.get("numberOfBedrooms")),
        "bathrooms": _scalar(
            offered.get("numberOfBathroomsTotal") or offered.get("numberOfBathrooms")
        ),
        "seller_type": seller_type,
        "seller_name": clean(seller.get("name")),
        "latitude": _scalar(geo.get("latitude")),
        "longitude": _scalar(geo.get("longitude")),
        "listing_date": clean(ld.get("datePosted") or ld.get("datePublished")),
    }
    return {key: value for key, value in evidence.items() if value not in (None, "")}


def _parse_floor(value: Any) -> int | None:
    text = normalize_key(value)
    if not text:
        return None
    if re.search(r"\b(?:rdc|rez de chaussee)\b", text):
        return 0
    match = re.search(r"\b(\d{1,2})(?:er|e|eme)?\b", text)
    return int(match.group(1)) if match else None


def _semantic_pairs(response: scrapy.http.Response) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for feature in response.css(".adMainFeature"):
        label = clean(" ".join(feature.css(".adMainFeatureContentLabel ::text").getall()))
        value = clean(" ".join(feature.css(".adMainFeatureContentValue ::text").getall()))
        if label and value:
            pairs[normalize_key(label)] = value
    return pairs


def extract_quartier(
    response: scrapy.http.Response,
    city: str | None,
) -> tuple[str | None, str | None]:
    if not city:
        return None, None

    city_re = re.escape(city)
    patterns = (
        re.compile(rf"^(.{{2,80}}?),\s*{city_re}$", re.I),
        re.compile(rf"^(.{{2,80}}?)\s+[àa]\s+{city_re}$", re.I),
    )
    candidates = response.css(
        "[class*='location']::text, [class*='address']::text, "
        ".breadcrumb *::text, [class*='breadcrumb'] *::text, "
        "h2::text, h3::text, h4::text, p::text, span::text, strong::text"
    ).getall()

    matches: list[tuple[str, str]] = []
    for candidate in candidates:
        text = clean(candidate)
        if not text or normalize_key(text) in NOISE_LOCATION:
            continue
        for pattern in patterns:
            match = pattern.match(text)
            if not match:
                continue
            quartier = clean(match.group(1))
            if quartier and normalize_key(quartier) not in NOISE_LOCATION:
                matches.append((text, quartier))
            break

    if matches:
        location, quartier = min(matches, key=lambda item: len(item[0]))
        return location, quartier
    return city, None


def extract_dom_evidence(
    response: scrapy.http.Response,
    city: str | None,
) -> dict[str, Any]:
    """Extract only explicitly labelled or semantically marked DOM evidence."""
    pairs = _semantic_pairs(response)
    location_raw, quartier = extract_quartier(response, city)
    evidence: dict[str, Any] = {
        "location_raw": location_raw,
        "quartier": quartier,
    }

    for label in ("etage du bien", "etage"):
        if label in pairs:
            evidence["floor"] = _parse_floor(pairs[label])
            break
    for label in ("nombre d'etages", "nombre de niveaux", "total etages"):
        if label in pairs:
            evidence["total_floors"] = _parse_floor(pairs[label])
            break
    for label in ("etat", "etat du bien", "condition"):
        if label in pairs:
            evidence["condition"] = clean(pairs[label])
            break

    amenity_labels: list[str] = []
    for feature in response.css(".adFeature"):
        values = [clean(value) for value in feature.css("p::text").getall()]
        label = next((value for value in values if value), None)
        if not label:
            continue
        amenity = AMENITY_LABELS.get(normalize_key(label))
        if amenity:
            evidence[amenity] = True
            amenity_labels.append(label)

    listing_date = clean(response.css("time::attr(datetime)").get())
    if not listing_date:
        listing_date = clean(
            response.css(
                'meta[property="article:published_time"]::attr(content), '
                'meta[itemprop="datePosted"]::attr(content), '
                'meta[itemprop="datePublished"]::attr(content)'
            ).get()
        )
    if listing_date:
        evidence["listing_date"] = listing_date

    if pairs:
        evidence["details_raw"] = " | ".join(
            f"{label}: {value}" for label, value in pairs.items()
        )
    if amenity_labels:
        evidence["attributes_raw"] = " | ".join(amenity_labels)

    return {key: value for key, value in evidence.items() if value not in (None, "")}


def canonical_listing_url(
    response: scrapy.http.Response,
    ld: dict[str, Any] | None,
    native_id: str,
) -> str:
    offer = _first_mapping(ld.get("offers")) if ld else {}
    candidates: Iterable[Any] = (
        ld.get("url") if ld else None,
        offer.get("url"),
        response.css('link[rel="canonical"]::attr(href)').get(),
        response.url,
    )
    for candidate in candidates:
        if not candidate:
            continue
        absolute = urljoin(response.url, str(candidate))
        host = (urlsplit(absolute).hostname or "").casefold()
        if host not in {"mubawab.ma", "www.mubawab.ma"}:
            continue
        if native_id_from_url(absolute) != native_id:
            continue
        canonical = canonicalize_url(absolute)
        if canonical:
            return canonical
    return canonicalize_url(response.url) or response.url


class MubawabSpider(scrapy.Spider):
    name = "mubawab"
    source_category = "appartements à vendre"

    def __init__(
        self,
        max_city_pages: int | str = len(CITY_SEEDS),
        max_listings: int | str = 20,
        output_path: str | None = None,
        failures_output: str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.max_city_pages = max(1, min(int(max_city_pages), len(CITY_SEEDS)))
        self.max_listings = max(1, int(max_listings))
        self.output_path = Path(output_path).resolve() if output_path else None
        self.failures_output = Path(failures_output).resolve() if failures_output else None
        existing, existing_rows = (
            load_identity_index(self.output_path) if self.output_path else (set(), 0)
        )
        self.seen_keys = set(existing)
        self.existing_rows = existing_rows
        self.selected_seeds = CITY_SEEDS[: self.max_city_pages]
        self.seed_responses_pending = len(self.selected_seeds)
        self.references_by_city: dict[str, list[ListingReference]] = {
            city: [] for city, _ in self.selected_seeds
        }
        self.details_scheduled = 0

    def _initial_requests(self) -> Iterator[scrapy.Request]:
        for seed_index, (city, url) in enumerate(self.selected_seeds, start=1):
            yield scrapy.Request(
                url,
                callback=self.parse_search,
                errback=self.errback_request,
                cb_kwargs={"seed_city": city, "seed_index": seed_index},
                meta={"stage": "search_page", "seed_city": city, "seed_index": seed_index},
                dont_filter=True,
            )

    async def start(self):
        for request in self._initial_requests():
            yield request

    def start_requests(self):
        yield from self._initial_requests()

    def parse_search(
        self,
        response: scrapy.http.Response,
        seed_city: str,
        seed_index: int,
    ):
        links = response.css(
            "div.listingBox::attr(linkref), "
            "li.listingBox::attr(linkref), "
            "h2.listingTit a::attr(href), "
            "a[href*='/a/']::attr(href)"
        ).getall()
        position = 0
        found = 0
        for href in links:
            absolute = urljoin(response.url, href)
            native_id = native_id_from_url(absolute)
            if not native_id:
                continue
            canonical = canonicalize_url(absolute) or absolute
            keys = identity_keys(native_id=native_id, url=canonical)
            if keys.intersection(self.seen_keys):
                self.crawler.stats.inc_value("resume/known_or_duplicate_links_skipped")
                continue

            self.seen_keys.update(keys)
            position += 1
            found += 1
            self.references_by_city[seed_city].append(
                ListingReference(
                    native_id=native_id,
                    url=canonical,
                    source_page_url=response.url,
                    seed_index=seed_index,
                    position_on_page=position,
                    seed_city=seed_city,
                )
            )

        self.logger.info(
            "Seed %s (%s): %s new ordinary listing URLs",
            seed_index,
            seed_city,
            found,
        )
        yield from self._finish_seed()

    def _finish_seed(self) -> Iterator[scrapy.Request]:
        self.seed_responses_pending = max(0, self.seed_responses_pending - 1)
        if self.seed_responses_pending or self.crawler.stats.get_value("rate_limit/http_429"):
            return
        yield from self._round_robin_detail_requests()

    def _round_robin_detail_requests(self) -> Iterator[scrapy.Request]:
        queues = {
            city: deque(references)
            for city, references in self.references_by_city.items()
        }
        while self.details_scheduled < self.max_listings:
            progressed = False
            for city, _ in self.selected_seeds:
                if self.details_scheduled >= self.max_listings:
                    break
                if not queues[city]:
                    continue
                progressed = True
                reference = queues[city].popleft()
                self.details_scheduled += 1
                yield scrapy.Request(
                    reference.url,
                    callback=self.parse_detail,
                    errback=self.errback_request,
                    cb_kwargs={"reference": reference},
                    meta={
                        "stage": "detail_page",
                        "native_id": reference.native_id,
                        "seed_city": reference.seed_city,
                    },
                )
            if not progressed:
                break
        self.crawler.stats.set_value("spider/detail_requests_scheduled", self.details_scheduled)

    def errback_request(self, failure):
        request = failure.request
        response = getattr(failure.value, "response", None)
        status = getattr(response, "status", None)
        stage = request.meta.get("stage", "request")
        self.crawler.stats.inc_value(f"failures/{stage}")
        self._append_failure(
            stage=stage,
            url=request.url,
            message=f"{failure.type.__name__}: {failure.value}",
            status=status,
        )
        self.logger.warning("%s failed for %s: %s", stage, request.url, failure.value)
        if stage == "search_page":
            yield from self._finish_seed()

    def _append_failure(
        self,
        *,
        stage: str,
        url: str,
        message: str,
        status: int | None,
    ) -> None:
        if not self.failures_output:
            return
        self.failures_output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "status": status,
            "url": url,
            "message": clean(message),
        }
        with self.failures_output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            handle.flush()

    def parse_detail(
        self,
        response: scrapy.http.Response,
        reference: ListingReference,
    ):
        ld = find_real_estate_listing(response)
        primary = jsonld_evidence(ld)
        dom = extract_dom_evidence(response, clean(primary.get("city")))

        if ld:
            self.crawler.stats.inc_value("jsonld/real_estate_listing_found")
        else:
            self.crawler.stats.inc_value("jsonld/real_estate_listing_missing")

        title_dom = clean(response.css("h1::text").get())
        meta_description = clean(response.css('meta[name="description"]::attr(content)').get())
        listing_url = canonical_listing_url(response, ld, reference.native_id)

        raw: dict[str, Any] = {
            "native_id": reference.native_id,
            "url": listing_url,
            "source": "mubawab.ma",
            "source_category": self.source_category,
            "source_page_url": reference.source_page_url,
            "search_page_number": reference.seed_index,
            "position_on_page": reference.position_on_page,
            "transaction_type": "SALE",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "title_raw": title_dom,
            "description_raw": meta_description,
            **dom,
            # JSON-LD is applied last so it always wins over fallback DOM values.
            **primary,
        }
        if raw.get("price_value") is not None and raw.get("currency"):
            raw["raw_price_text"] = f"{raw['price_value']} {raw['currency']}"

        record = build_v3_record(raw, source="mubawab.ma")
        ordered = {column: record.get(column) for column in SCHEMA_V3_COLUMNS}
        self.logger.info(
            "Parsed %s | validation=%s | eligible=%s | city=%s | JSON-LD=%s",
            ordered.get("listing_id"),
            ordered.get("validation_status"),
            ordered.get("model_eligible"),
            ordered.get("city"),
            bool(ld),
        )
        yield ordered


__all__ = [
    "CITY_SEEDS",
    "ListingReference",
    "MubawabSpider",
    "canonical_listing_url",
    "extract_dom_evidence",
    "find_real_estate_listing",
    "jsonld_evidence",
]
