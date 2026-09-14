"""Build attributed Morocco region, city and neighborhood GeoJSON layers."""
from __future__ import annotations

import argparse
import io
import json
import re
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from scipy.spatial import cKDTree
from shapely.geometry import Point, shape


GEONAMES_URL = "https://download.geonames.org/export/dump/MA.zip"
GEOBOUNDARIES_API = "https://www.geoboundaries.org/api/current/gbOpen/MAR/{level}/"
USER_AGENT = "MaisonDeLUX-geography/1.0 (open-data reference builder)"


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", text).strip()


def fetch_json(session: requests.Session, url: str) -> dict[str, Any]:
    response = session.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def boundary_layer(session: requests.Session, level: str) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = fetch_json(session, GEOBOUNDARIES_API.format(level=level))
    download_url = metadata.get("simplifiedGeometryGeoJSON") or metadata.get("gjDownloadURL")
    if not download_url:
        raise RuntimeError(f"geoBoundaries metadata did not provide a GeoJSON URL for {level}")
    layer = fetch_json(session, download_url)
    for feature in layer.get("features", []):
        properties = feature.setdefault("properties", {})
        source_name = properties.get("shapeName") or properties.get("name")
        properties.update({
            "name": source_name,
            "normalized_name": normalize_name(str(source_name or "")),
            "admin_level": level,
            "source": "geoBoundaries gbOpen (source: OpenStreetMap/Wambacher)",
            "source_url": metadata.get("boundarySourceURL") or GEOBOUNDARIES_API.format(level=level),
            "license": metadata.get("boundaryLicense"),
            "license_url": metadata.get("licenseSource"),
            "boundary_year": metadata.get("boundaryYearRepresented"),
        })
    return layer, metadata


def parse_geonames(content: bytes) -> list[dict[str, Any]]:
    columns = [
        "geonameid", "name", "asciiname", "alternatenames", "latitude", "longitude",
        "feature_class", "feature_code", "country_code", "cc2", "admin1_code", "admin2_code",
        "admin3_code", "admin4_code", "population", "elevation", "dem", "timezone", "modification_date",
    ]
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        file_name = next(name for name in archive.namelist() if name.upper() == "MA.TXT")
        lines = archive.read(file_name).decode("utf-8").splitlines()
    rows: list[dict[str, Any]] = []
    for line in lines:
        values = line.split("\t")
        if len(values) == len(columns):
            rows.append(dict(zip(columns, values)))
    return rows


def points_geojson(rows: list[dict[str, Any]], neighborhood: bool) -> dict[str, Any]:
    features = []
    for row in rows:
        is_neighborhood = row["feature_code"] in {"PPLX", "PPLQ", "ADMD"}
        if neighborhood != is_neighborhood:
            continue
        if row["feature_class"] != "P" and not is_neighborhood:
            continue
        alternate = [name for name in row["alternatenames"].split(",") if name]
        population = int(row["population"] or 0)
        features.append({
            "type": "Feature",
            "id": f"geonames:{row['geonameid']}",
            "geometry": {"type": "Point", "coordinates": [float(row["longitude"]), float(row["latitude"])]},
            "properties": {
                "geoname_id": row["geonameid"], "name": row["name"],
                "normalized_name": normalize_name(row["name"]), "ascii_name": row["asciiname"],
                "alternative_names": alternate, "feature_code": row["feature_code"],
                "population": population, "parent_city": None if not neighborhood else row["admin3_code"] or None,
                "region_code": row["admin1_code"] or None, "province_code": row["admin2_code"] or None,
                "latitude": float(row["latitude"]), "longitude": float(row["longitude"]),
                "source": "GeoNames", "source_url": "https://www.geonames.org/",
                "license": "Creative Commons Attribution 4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "modified_date": row["modification_date"],
            },
        })
    features.sort(key=lambda feature: (-int(feature["properties"].get("population") or 0), feature["properties"]["normalized_name"]))
    return {"type": "FeatureCollection", "features": features}


def enrich_hierarchy(regions: dict[str, Any], cities: dict[str, Any], neighborhoods: dict[str, Any]) -> None:
    region_shapes = [(shape(feature["geometry"]), feature["properties"].get("name")) for feature in regions.get("features", [])]
    for collection in (cities, neighborhoods):
        for feature in collection["features"]:
            lon, lat = feature["geometry"]["coordinates"]
            point = Point(lon, lat)
            feature["properties"]["region"] = next((name for geometry, name in region_shapes if geometry.covers(point)), None)

    parent_candidates = [
        feature for feature in cities["features"]
        if int(feature["properties"].get("population") or 0) >= 5_000
        or str(feature["properties"].get("feature_code") or "").startswith("PPLA")
    ]
    coordinates = [(feature["properties"]["latitude"], feature["properties"]["longitude"]) for feature in parent_candidates]
    if not coordinates:
        return
    tree = cKDTree(coordinates)
    for feature in neighborhoods["features"]:
        latitude = feature["properties"]["latitude"]
        longitude = feature["properties"]["longitude"]
        distance_degrees, index = tree.query((latitude, longitude), k=1)
        # Roughly 45 km at Moroccan latitudes; farther matches are left unknown.
        if float(distance_degrees) <= 0.45:
            parent = parent_candidates[int(index)]["properties"]
            feature["properties"]["parent_city"] = parent.get("name")
            feature["properties"]["parent_city_geoname_id"] = parent.get("geoname_id")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def build(output_dir: Path, external_dir: Path) -> dict[str, Any]:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    regions, region_meta = boundary_layer(session, "ADM1")
    provinces, province_meta = boundary_layer(session, "ADM2")
    response = session.get(GEONAMES_URL, timeout=120)
    response.raise_for_status()
    external_dir.mkdir(parents=True, exist_ok=True)
    (external_dir / "geonames_MA.zip").write_bytes(response.content)
    geonames_rows = parse_geonames(response.content)
    cities = points_geojson(geonames_rows, neighborhood=False)
    neighborhoods = points_geojson(geonames_rows, neighborhood=True)
    enrich_hierarchy(regions, cities, neighborhoods)
    write_json(output_dir / "morocco_regions.geojson", regions)
    write_json(output_dir / "morocco_provinces.geojson", provinces)
    write_json(output_dir / "morocco_cities.geojson", cities)
    write_json(output_dir / "morocco_neighborhoods.geojson", neighborhoods)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "layers": {
            "regions": len(regions.get("features", [])), "provinces_prefectures": len(provinces.get("features", [])),
            "cities_towns": len(cities["features"]), "neighborhoods_districts": len(neighborhoods["features"]),
        },
        "geoBoundaries": {"ADM1": region_meta, "ADM2": province_meta},
        "GeoNames": {"download_url": GEONAMES_URL, "license": "CC BY 4.0", "records_read": len(geonames_rows)},
        "limitations": [
            "Region and province geometries represent the source's 2017 boundary vintage.",
            "Neighborhood coverage contains only GeoNames features explicitly classified as populated-place sections or administrative divisions.",
            "No real-estate observations are fabricated for geographic features without listings.",
        ],
    }
    write_json(output_dir / "geography_manifest.json", manifest)
    return manifest


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=root / "data" / "geographic")
    parser.add_argument("--external-dir", type=Path, default=root / "data" / "external" / "geography_sources")
    args = parser.parse_args()
    manifest = build(args.output_dir, args.external_dir)
    print(json.dumps(manifest["layers"], sort_keys=True))


if __name__ == "__main__":
    main()
