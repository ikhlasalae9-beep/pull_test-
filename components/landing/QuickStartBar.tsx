'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { MapPin, Maximize2, ArrowRight, ArrowLeft } from 'lucide-react';
import { VERIFIED_CITIES } from '@/config/cities.config';
import { isRTL } from '@/lib/i18n/config';

interface QuickStartBarProps {
  locale: string;
  dict: any;
}

export function QuickStartBar({ locale, dict }: QuickStartBarProps) {
  const [selectedCity, setSelectedCity] = useState('Casablanca');
  const [surface, setSurface] = useState<number | ''>(95);
  const router = useRouter();
  const rtl = isRTL(locale);
  const ArrowIcon = rtl ? ArrowLeft : ArrowRight;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (selectedCity) params.set('ville', selectedCity);
    if (surface && surface > 0) params.set('surface', surface.toString());
    router.push(`/${locale}/estimation?${params.toString()}`);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-3xl bg-white dark:bg-brand-navy-surface border border-slate-200/90 dark:border-white/10 rounded-2xl p-2.5 sm:p-3 shadow-xl shadow-slate-900/5 dark:shadow-black/40 transition-colors"
    >
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-2.5 sm:gap-3 items-center">
        {/* City selection field */}
        <div className="sm:col-span-5 relative flex items-center px-3 py-2 sm:py-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-white/5">
          <MapPin className="w-4 h-4 text-brand-blue dark:text-blue-400 shrink-0 me-2.5" />
          <div className="flex-1 min-w-0">
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              {dict.hero.quickStart.cityLabel}
            </label>
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="w-full bg-transparent text-sm font-semibold text-slate-900 dark:text-white focus:outline-none cursor-pointer truncate"
            >
              {VERIFIED_CITIES.map((city) => (
                <option key={city.id} value={city.nameFr} className="text-slate-900 bg-white dark:bg-slate-800 dark:text-white">
                  {locale === 'ar' ? city.nameAr : city.nameFr}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Surface input field */}
        <div className="sm:col-span-4 relative flex items-center px-3 py-2 sm:py-2.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-white/5">
          <Maximize2 className="w-4 h-4 text-brand-blue dark:text-blue-400 shrink-0 me-2.5" />
          <div className="flex-1 min-w-0">
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              {dict.hero.quickStart.surfaceLabel}
            </label>
            <div className="flex items-baseline gap-1">
              <input
                type="number"
                min="20"
                max="800"
                value={surface}
                onChange={(e) => setSurface(e.target.value ? Number(e.target.value) : '')}
                placeholder="ex: 95"
                className="w-full bg-transparent text-sm font-semibold text-slate-900 dark:text-white focus:outline-none"
              />
              <span className="text-xs text-slate-400 font-medium">m²</span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="sm:col-span-3">
          <button
            type="submit"
            className="w-full h-full min-h-[48px] inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-brand-blue hover:bg-brand-blue-hover text-white text-sm font-semibold rounded-xl shadow-md shadow-blue-600/20 transition-all duration-150 active:scale-[0.98]"
          >
            <span>{dict.hero.quickStart.action}</span>
            <ArrowIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </form>
  );
}
