'use client';

import React from 'react';
import { Home, Info } from 'lucide-react';
import { DynamicField } from './DynamicField';
import { ESTIMATOR_FIELDS } from '@/config/estimator.config';
import { EstimatorFormData } from '@/types/estimator';

interface Step2PropertyTypeProps {
  formData: EstimatorFormData;
  updateForm: (key: string, value: any) => void;
  locale: string;
  dict: any;
}

export function Step2PropertyType({ formData, updateForm, locale, dict }: Step2PropertyTypeProps) {
  const stepFields = ESTIMATOR_FIELDS.filter((f) => f.step === 2);

  return (
    <div className="space-y-6">
      {/* Scope banner */}
      <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-900 dark:text-blue-300 flex items-start gap-3.5">
        <Info className="w-5 h-5 text-brand-blue dark:text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs sm:text-sm leading-relaxed">
          <strong className="font-semibold block mb-0.5">
            {locale === 'ar' ? 'نطاق النموذج المفعل' : 'Périmètre actif de prédiction'}
          </strong>
          <p className="text-blue-800 dark:text-blue-200/90">
            {locale === 'ar'
              ? 'تغطي خوارزمية التقييم حالياً قطاع الشقق السكنية الموجهة للبيع. تتم مراجعة وتدقيق معطيات الفئات الأخرى لإدراجها في التحديثات القادمة.'
              : 'Le moteur algorithmique est actuellement restreint aux appartements résidentiels à la vente. Les modèles dédiés aux autres typologies sont en cours d\'audit pour garantir une précision équivalente.'}
          </p>
        </div>
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
