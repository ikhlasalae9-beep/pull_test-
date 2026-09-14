'use client';

import React from 'react';
import { NeighborhoodSelect } from './NeighborhoodSelect';
import { MapPin } from 'lucide-react';
import { DynamicField } from './DynamicField';
import { ESTIMATOR_FIELDS } from '@/config/estimator.config';
import { EstimatorFormData } from '@/types/estimator';

interface Step1LocationProps {
  formData: EstimatorFormData;
  updateForm: (key: string, value: any) => void;
  locale: string;
  dict: any;
}

export function Step1Location({ formData, updateForm, locale, dict }: Step1LocationProps) {
  const stepFields = ESTIMATOR_FIELDS.filter((f) => f.step === 1 && f.id !== 'quartier');

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-white/5 mb-6">
        <MapPin className="w-5 h-5 text-brand-blue dark:text-blue-400 shrink-0" />
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
          {locale === 'ar'
            ? 'يرجى تحديد المدينة الجغرافية لعقاركم. تؤثر دقة الموقع الحضري بشكل مباشر على المعايرة الإحصائية للقيمة.'
            : 'Indiquez l\'implantation de votre bien. La localisation constitue le facteur déterminant de pondération du modèle.'}
        </p>
      </div>

      <div className="space-y-5">
        {stepFields.map((field) => (
          <DynamicField
            key={field.id}
            field={field}
            value={formData[field.id]}
            onChange={(val) => updateForm(field.id, val)}
            locale={locale}
            dict={dict}
          />
        ))}
        <NeighborhoodSelect key={formData.ville} city={formData.ville} value={formData.quartier}
          onChange={value => updateForm('quartier', value)} locale={locale} />
      </div>
    </div>
  );
}
