'use client';

import React, { useState } from 'react';
import { neighborhoodOptions, OTHER_NEIGHBORHOOD } from '@/lib/estimation/locations';

export function NeighborhoodSelect({ city, value, onChange, locale }: {
  city: string; value: string; onChange: (value: string) => void; locale: string;
}) {
  const [query, setQuery] = useState('');
  const ar = locale === 'ar';
  const options = neighborhoodOptions(city, query);
  const fieldStyle = 'w-full px-4 py-3 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-white/10 rounded-xl text-base text-slate-900 dark:text-white';
  return (
    <div className="space-y-2">
      <label htmlFor="neighborhood-search" className="text-xs font-bold text-slate-700 dark:text-slate-300">
        {ar ? 'البحث في أحياء المدينة' : 'Rechercher parmi les quartiers de la ville'}
      </label>
      <input id="neighborhood-search" type="search" value={query} autoComplete="off"
        onChange={event => { setQuery(event.target.value); onChange(OTHER_NEIGHBORHOOD); }} className={fieldStyle}
        placeholder={ar ? 'ابحث ثم اختر الحي' : 'Rechercher, puis sélectionner un quartier'} />
      <label htmlFor="quartier" className="block text-xs font-bold uppercase text-slate-700 dark:text-slate-300">
        {ar ? 'الحي' : 'Quartier'}
      </label>
      <select id="quartier" value={options.some(option => option.value === value) ? value : OTHER_NEIGHBORHOOD}
        onChange={event => { onChange(event.target.value); setQuery(''); }} className={fieldStyle}
        aria-describedby="neighborhood-note">
        {options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
        <option value={OTHER_NEIGHBORHOOD}>{ar ? 'آخر / حي غير مدرج' : 'Autre / quartier non répertorié'}</option>
      </select>
      {query && options.length === 0 && <p className="text-xs text-slate-500">{ar ? 'لا يوجد حي مطابق.' : 'Aucun quartier correspondant.'}</p>}
      <p id="neighborhood-note" className="text-xs text-slate-500 dark:text-slate-400">
        {ar ? 'إذا لم يكن حيكم مدرجاً، فسيعتمد التقدير أكثر على المدينة وخصائص العقار.' : "Si votre quartier n'est pas répertorié, l'estimation reposera davantage sur la ville et les caractéristiques du bien."}
      </p>
    </div>
  );
}
