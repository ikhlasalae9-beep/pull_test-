'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { VERIFIED_CITIES, VerifiedCity, REGIONS_TRANSLATIONS } from '@/config/cities.config';

interface MoroccoMapPreviewProps {
  selectedCityId: string;
  onSelectCity: (city: VerifiedCity) => void;
  locale: string;
}

interface GeoFeature {
  type: string;
  properties: {
    cartodb_id: number;
    region: string;
  };
  geometry: {
    type: 'Polygon' | 'MultiPolygon';
    coordinates: any;
  };
}

interface GeoJsonData {
  type: string;
  features: GeoFeature[];
}

// Bounding box for Morocco from maroc.geojson
const BOUNDS = {
  minLon: -17.099815,
  maxLon: -1.014839,
  minLat: 20.783042,
  maxLat: 35.930099,
};

const SVG_WIDTH = 500;
const SVG_HEIGHT = 550;
const PADDING = 20;

function mercatorY(lat: number): number {
  const rad = (lat * Math.PI) / 180;
  return Math.log(Math.tan(Math.PI / 4 + rad / 2));
}

const MIN_MERC = mercatorY(BOUNDS.minLat);
const MAX_MERC = mercatorY(BOUNDS.maxLat);

function projectCoordinate([lon, lat]: [number, number]): [number, number] {
  const plotWidth = SVG_WIDTH - PADDING * 2;
  const plotHeight = SVG_HEIGHT - PADDING * 2;

  const x = PADDING + ((lon - BOUNDS.minLon) / (BOUNDS.maxLon - BOUNDS.minLon)) * plotWidth;
  const y = PADDING + plotHeight - ((mercatorY(lat) - MIN_MERC) / (MAX_MERC - MIN_MERC)) * plotHeight;

  return [Math.round(x * 10) / 10, Math.round(y * 10) / 10];
}

function ringToPath(ring: [number, number][]): string {
  return ring
    .map((pt, i) => {
      const [x, y] = projectCoordinate(pt);
      return (i === 0 ? 'M' : 'L') + x + ',' + y;
    })
    .join(' ') + ' Z';
}

function geometryToPath(geom: GeoFeature['geometry']): string {
  if (geom.type === 'Polygon') {
    return geom.coordinates.map(ringToPath).join(' ');
  } else if (geom.type === 'MultiPolygon') {
    return geom.coordinates
      .map((poly: [number, number][][]) => poly.map(ringToPath).join(' '))
      .join(' ');
  }
  return '';
}

export function MoroccoMapPreview({
  selectedCityId,
  onSelectCity,
  locale,
}: MoroccoMapPreviewProps) {
  const [geoData, setGeoData] = useState<GeoJsonData | null>(null);
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);
  const [hoveredCity, setHoveredCity] = useState<VerifiedCity | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Find currently selected city object
  const currentSelectedCity = useMemo(
    () => VERIFIED_CITIES.find((c) => c.id === selectedCityId) || VERIFIED_CITIES[0],
    [selectedCityId]
  );

  // Load GeoJSON locally from public/maps/maroc.geojson
  useEffect(() => {
    let isMounted = true;
    fetch('/maps/maroc.geojson')
      .then((res) => {
        if (!res.ok) throw new Error('Impossible de charger maroc.geojson');
        return res.json();
      })
      .then((data: GeoJsonData) => {
        if (isMounted) {
          setGeoData(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error('Erreur chargement GeoJSON:', err);
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Compute SVG paths for each region
  const regionPaths = useMemo(() => {
    if (!geoData) return [];
    return geoData.features.map((feature) => ({
      id: feature.properties.cartodb_id,
      regionKey: feature.properties.region,
      path: geometryToPath(feature.geometry),
    }));
  }, [geoData]);

  return (
    <div className="relative w-full max-h-[420px] lg:max-h-[440px] xl:max-h-[480px] aspect-[5/5.2] max-w-md xl:max-w-lg mx-auto bg-slate-50/50 dark:bg-slate-900/40 rounded-2xl border border-slate-200/80 dark:border-white/10 p-3 sm:p-4.5 flex flex-col items-center justify-between overflow-hidden shadow-xs">
      {/* Background Architectural Grid */}
      <div className="absolute inset-0 pointer-events-none opacity-40 dark:opacity-20">
        <svg width="100%" height="100%">
          <defs>
            <pattern id="archGrid" width="24" height="24" patternUnits="userSpaceOnUse">
              <path d="M 24 0 L 0 0 0 24" fill="none" className="stroke-slate-200/80 dark:stroke-white/10" strokeWidth="0.6" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#archGrid)" />
        </svg>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-3 z-10">
          <div className="w-8 h-8 rounded-full border-2 border-brand-blue/20 border-t-brand-blue animate-spin" />
          <span className="text-xs text-slate-500 font-medium">
            {locale === 'ar' ? 'جارٍ تحميل الخريطة الجغرافية...' : 'Chargement de la géométrie régionale...'}
          </span>
        </div>
      ) : (
        <div className="relative w-full h-full z-10 flex items-center justify-center">
          <svg
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
            className="w-full h-full select-none"
            aria-label="Carte des 12 régions du Maroc"
            role="region"
          >
            {/* Layer 1: Geographic Regions (12 Real GeoJSON MultiPolygons) */}
            <g className="regions-layer">
              {regionPaths.map(({ id, regionKey, path }) => {
                const isRegionSelected = currentSelectedCity.regionKey === regionKey;
                const isRegionHovered = hoveredRegion === regionKey;
                const regionName =
                  REGIONS_TRANSLATIONS[regionKey]
                    ? locale === 'ar'
                      ? REGIONS_TRANSLATIONS[regionKey].nameAr
                      : REGIONS_TRANSLATIONS[regionKey].nameFr
                    : regionKey;

                return (
                  <path
                    key={id}
                    d={path}
                    tabIndex={0}
                    role="button"
                    aria-label={`Région ${regionName}`}
                    onMouseEnter={() => setHoveredRegion(regionKey)}
                    onMouseLeave={() => setHoveredRegion(null)}
                    onFocus={() => setHoveredRegion(regionKey)}
                    onBlur={() => setHoveredRegion(null)}
                    className={`transition-all duration-200 cursor-pointer outline-none ${
                      isRegionSelected
                        ? 'fill-brand-blue/15 dark:fill-blue-500/20 stroke-brand-blue dark:stroke-blue-400 stroke-[1.2]'
                        : isRegionHovered
                        ? 'fill-brand-blue/8 dark:fill-blue-500/12 stroke-slate-400 dark:stroke-slate-500 stroke-[1]'
                        : 'fill-slate-100/90 dark:fill-slate-800/60 stroke-slate-300 dark:stroke-slate-700/80 stroke-[0.8]'
                    }`}
                  />
                );
              })}
            </g>

            {/* Layer 2: Verified City Markers (Layered Strictly Above Regions) */}
            <g className="cities-layer">
              {VERIFIED_CITIES.map((city) => {
                const [cx, cy] = projectCoordinate(city.coordinates);
                const isCitySelected = city.id === currentSelectedCity.id;
                const isCityHovered = hoveredCity?.id === city.id;
                const cityName = locale === 'ar' ? city.nameAr : city.nameFr;

                return (
                  <g
                    key={city.id}
                    className="cursor-pointer group"
                    onClick={() => onSelectCity(city)}
                    onMouseEnter={() => {
                      setHoveredCity(city);
                      setHoveredRegion(city.regionKey);
                    }}
                    onMouseLeave={() => {
                      setHoveredCity(null);
                      setHoveredRegion(null);
                    }}
                    tabIndex={0}
                    role="button"
                    aria-label={`Ville ${cityName}`}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onSelectCity(city);
                      }
                    }}
                  >
                    {/* Outer animated ripple on selected city */}
                    {isCitySelected && (
                      <circle
                        cx={cx}
                        cy={cy}
                        r="12"
                        className="fill-brand-blue/20 stroke-brand-blue animate-ping opacity-75"
                        strokeWidth="1"
                      />
                    )}

                    {/* Outer halo */}
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isCitySelected ? 8 : isCityHovered ? 6.5 : 5}
                      className={`transition-all duration-150 ${
                        isCitySelected
                          ? 'fill-brand-blue stroke-white dark:stroke-brand-navy'
                          : isCityHovered
                          ? 'fill-blue-600 stroke-white dark:stroke-brand-navy'
                          : 'fill-slate-700 dark:fill-slate-300 stroke-white dark:stroke-brand-navy group-hover:fill-brand-blue'
                      }`}
                      strokeWidth="1.5"
                    />

                    {/* Inner core */}
                    {isCitySelected && (
                      <circle cx={cx} cy={cy} r="2.5" className="fill-white" />
                    )}

                    {/* City label */}
                    <text
                      x={cx + (locale === 'ar' ? -8 : 8)}
                      y={cy + 3}
                      textAnchor={locale === 'ar' ? 'end' : 'start'}
                      className={`text-[9.5px] font-bold select-none pointer-events-none transition-colors ${
                        isCitySelected
                          ? 'fill-brand-blue dark:fill-blue-400 font-extrabold'
                          : 'fill-slate-700 dark:fill-slate-300 group-hover:fill-brand-blue dark:group-hover:fill-blue-400'
                      }`}
                    >
                      {cityName}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>
      )}

      {/* Floating Bottom Status Bar */}
      <div className="w-full pt-3 mt-1 border-t border-slate-200/60 dark:border-white/5 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 z-10">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-brand-blue" />
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            {hoveredRegion
              ? REGIONS_TRANSLATIONS[hoveredRegion]
                ? locale === 'ar'
                  ? REGIONS_TRANSLATIONS[hoveredRegion].nameAr
                  : REGIONS_TRANSLATIONS[hoveredRegion].nameFr
                : hoveredRegion
              : currentSelectedCity.regionFr}
          </span>
        </div>
        <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
          GeoJSON · 12 Régions
        </span>
      </div>
    </div>
  );
}
