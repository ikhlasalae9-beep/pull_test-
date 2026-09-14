'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Search, MapPin, ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { VERIFIED_CITIES, VerifiedCity } from '@/config/cities.config';
import { MoroccoMapPreview } from './MoroccoMapPreview';
import { isRTL } from '@/lib/i18n/config';

interface LocationExplorerProps {
  locale: string;
  dict: any;
}

export function LocationExplorer({ locale, dict }: LocationExplorerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCity, setSelectedCity] = useState<VerifiedCity>(VERIFIED_CITIES[0]);
  const rtl = isRTL(locale);
  const ArrowIcon = rtl ? ArrowLeft : ArrowRight;

  const filteredCities = VERIFIED_CITIES.filter((city) => {
    const q = searchQuery.toLowerCase();
    return (
      city.nameFr.toLowerCase().includes(q) ||
      city.nameAr.includes(q) ||
      city.regionFr.toLowerCase().includes(q) ||
      city.regionAr.includes(q)
    );
  });

  return (
    <section
      id="explorer"
      className="min-h-auto lg:min-h-[100svh] flex flex-col justify-center py-16 sm:py-20 lg:py-8 scroll-mt-24 lg:scroll-mt-28 bg-white dark:bg-brand-navy transition-colors border-t border-slate-200/80 dark:border-white/5 relative"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        {/* Section Header with Scroll Reveal */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-8% 0px' }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl mx-auto text-center mb-6 lg:mb-8"
        >
          <span className="text-xs font-bold uppercase tracking-wider text-brand-blue dark:text-blue-400 mb-2 block">
            {dict.explorer.badge}
          </span>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 dark:text-white leading-tight">
            {dict.explorer.title}
          </h2>
          <p className="mt-2 text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            {dict.explorer.subtitle}
          </p>
        </motion.div>

        {/* Explorer Layout: List + Architectural Map with Scroll Reveal */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10 items-center">
          {/* Left Column: Search & City Cards */}
          <motion.div
            initial={{ opacity: 0, x: rtl ? 16 : -16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-8% 0px' }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-6 space-y-3.5"
          >
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute start-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={dict.explorer.searchPlaceholder}
                className="w-full ps-10 pe-4 py-2.5 bg-slate-50 dark:bg-brand-navy-surface border border-slate-200 dark:border-white/10 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-brand-blue transition-colors shadow-xs"
              />
            </div>

            {/* City Selection Scroll List */}
            <div className="space-y-2 max-h-[250px] sm:max-h-[280px] lg:max-h-[290px] xl:max-h-[320px] overflow-y-auto pe-1">
              {filteredCities.length === 0 ? (
                <div className="p-8 text-center text-sm text-slate-500 bg-slate-50 dark:bg-slate-900/40 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
                  {dict.explorer.noResults}
                </div>
              ) : (
                filteredCities.map((city) => {
                  const isSelected = city.id === selectedCity.id;
                  const cityName = locale === 'ar' ? city.nameAr : city.nameFr;
                  const regionName = locale === 'ar' ? city.regionAr : city.regionFr;

                  return (
                    <div
                      key={city.id}
                      onClick={() => setSelectedCity(city)}
                      className={`group p-3 sm:p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                        isSelected
                          ? 'bg-brand-blue/5 dark:bg-blue-500/10 border-brand-blue dark:border-blue-400/50 shadow-xs'
                          : 'bg-white dark:bg-brand-navy-surface border-slate-200/80 dark:border-white/5 hover:border-slate-300 dark:hover:border-white/15'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                            isSelected
                              ? 'bg-brand-blue text-white'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 group-hover:text-brand-blue'
                          }`}
                        >
                          <MapPin className="w-3.5 h-3.5" />
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-sm font-bold text-slate-900 dark:text-white truncate">
                            {cityName}
                          </h4>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                            {regionName}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {city.hasActiveModelCoverage && (
                          <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>{dict.explorer.activeNotice}</span>
                          </span>
                        )}
                        <Link
                          href={`/${locale}/estimation?ville=${encodeURIComponent(city.nameFr)}`}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-brand-blue hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                          title={dict.explorer.estimateInCity}
                        >
                          <ArrowIcon className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Selected City Quick Action */}
            <div className="pt-1">
              <Link
                href={`/${locale}/estimation?ville=${encodeURIComponent(selectedCity.nameFr)}`}
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-brand-blue hover:bg-brand-blue-hover text-white text-xs sm:text-sm font-semibold transition-all shadow-md shadow-blue-600/15"
              >
                <span>
                  {dict.explorer.estimateInCity} :{' '}
                  {locale === 'ar' ? selectedCity.nameAr : selectedCity.nameFr}
                </span>
                <ArrowIcon className="w-3.5 h-3.5" />
              </Link>
            </div>
          </motion.div>

          {/* Right Column: Architectural Interactive Map with Scroll Reveal */}
          <motion.div
            initial={{ opacity: 0, x: rtl ? -16 : 16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-8% 0px' }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-6 flex justify-center"
          >
            <MoroccoMapPreview
              selectedCityId={selectedCity.id}
              onSelectCity={(city) => setSelectedCity(city)}
              locale={locale}
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
