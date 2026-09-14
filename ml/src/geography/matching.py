"""Deterministic city/region enrichment using the geographic reference layers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import Point, shape

from ml.src.data_schema import CITY_ALIASES, normalize_for_matching


class MoroccoGeography:
    def __init__(self, directory: Path):
        self.directory = directory
        self.regions = json.loads((directory / "morocco_regions.geojson").read_text(encoding="utf-8"))["features"]
        self.cities = json.loads((directory / "morocco_cities.geojson").read_text(encoding="utf-8"))["features"]
        self.city_index: dict[str, list[dict[str, Any]]] = {}
        for feature in self.cities:
            properties = feature["properties"]
            names = [properties.get("name"), properties.get("ascii_name"), *(properties.get("alternative_names") or [])]
            for name in names:
                if name:
                    self.city_index.setdefault(normalize_for_matching(name), []).append(feature)

    def region_for_point(self, latitude: float, longitude: float) -> str | None:
        point = Point(float(longitude), float(latitude))
        for feature in self.regions:
            if shape(feature["geometry"]).covers(point):
                return feature["properties"].get("name")
        return None

    def enrich(self, city: Any, latitude: Any = None, longitude: Any = None) -> dict[str, Any]:
        if latitude is not None and longitude is not None:
            return {"city": city, "latitude": float(latitude), "longitude": float(longitude),
                    "region": self.region_for_point(float(latitude), float(longitude)), "geography_match": "source_coordinates"}
        normalized = normalize_for_matching(city)
        canonical = CITY_ALIASES.get(normalized)
        candidates = self.city_index.get(normalize_for_matching(canonical or city), [])
        if not candidates:
            return {"city": canonical or city, "latitude": None, "longitude": None, "region": None, "geography_match": "unmatched"}
        feature = max(candidates, key=lambda item: int(item["properties"].get("population") or 0))
        lon, lat = feature["geometry"]["coordinates"]
        return {"city": canonical or feature["properties"]["name"], "latitude": lat, "longitude": lon,
                "region": self.region_for_point(lat, lon), "geography_match": "geonames_city_centroid"}
