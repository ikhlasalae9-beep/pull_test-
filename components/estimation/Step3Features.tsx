'use client';

import React from 'react';
import { Sliders } from 'lucide-react';
import { DynamicField } from './DynamicField';
import { ESTIMATOR_FIELDS } from '@/config/estimator.config';
import { EstimatorFormData } from '@/types/estimator';

interface Step3FeaturesProps {
  formData: EstimatorFormData;
  updateForm: (key: string, value: any) => void;
  locale: string;
  dict: any;
}

export function Step3Features({ formData, updateForm, locale, dict }: Step3FeaturesProps) {
  const stepFields = ESTIMATOR_FIELDS.filter((f) => f.step === 3);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-white/5 mb-6">
        <Sliders className="w-5 h-5 text-brand-blue dark:text-blue-400 shrink-0" />
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
          {locale === 'ar'
            ? 'حدد المواصفات الفنية والمساحة الصافية بدقة لمساعدة الخوارزمية على ضبط التقييم التقديري.'
            : 'Précisez les dimensions et la configuration du bien pour permettre une estimation fine.'}
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
      </div>
    </div>
  );
}
