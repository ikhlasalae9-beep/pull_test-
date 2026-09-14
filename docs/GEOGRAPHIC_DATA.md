# Geographic reference data

`python -m ml.src.geography.build_reference` creates four map-ready layers:

- `morocco_regions.geojson` — 12 ADM1 polygons;
- `morocco_provinces.geojson` — 75 ADM2 polygons;
- `morocco_cities.geojson` — GeoNames populated places with coordinates and aliases;
- `morocco_neighborhoods.geojson` — only GeoNames features explicitly classified as populated-place sections/districts.

Region and province polygons come from [geoBoundaries gbOpen](https://www.geoboundaries.org/api.html). The Morocco metadata identifies an OpenStreetMap/Wambacher source, ODbL 1.0, a 2017 boundary vintage, and a 2023 build date. Populated places and aliases come from the daily [GeoNames Morocco dump](https://download.geonames.org/export/dump/MA.zip) under [CC BY 4.0](https://www.geonames.org/export/).

Every feature retains source, license, normalized name, alternative names, coordinates, region and (when a reliable nearby populated place exists) parent city. `geography_manifest.json` records the exact metadata and limitations.

The layers are geographic references, not price observations. Zero-listing features remain zero in `reports/scraping/geographic_coverage_detail.csv`. External boundary sources may encode disputed territories differently; they must not be silently merged with an official Moroccan hierarchy.
