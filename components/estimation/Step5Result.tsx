'use client';

import React from 'react';
import { CheckCircle, AlertTriangle, RefreshCw, ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-react';
import { PredictResponse } from '@/lib/api/types';
import { EstimatorFormData } from '@/types/estimator';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { Button } from '@/components/common/Button';
import { isRTL } from '@/lib/i18n/config';

interface Step5ResultProps {
  prediction: PredictResponse | null;
  isSubmitting: boolean;
  isOffline: boolean;
  error?: string;
  formData: EstimatorFormData;
  onRetry: () => void;
  onReset: () => void;
  locale: string;
  dict: any;
}

export function Step5Result({
  prediction,
  isSubmitting,
  isOffline,
  error,
  formData,
  onRetry,
  onReset,
  locale,
  dict,
}: Step5ResultProps) {
  const d = dict.estimation.result;
  const rtl = isRTL(locale);
  const ArrowIcon = rtl ? ArrowLeft : ArrowRight;

  // 1. Loading State
  if (isSubmitting) {
    return (
      <div className="py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-brand-blue/10 dark:bg-blue-400/10 border border-brand-blue/20 flex items-center justify-center mx-auto text-brand-blue dark:text-blue-400 animate-pulse">
          <RefreshCw className="w-6 h-6 animate-spin" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          {dict.common.loading}
        </h3>
        <p className="text-xs sm:text-sm text-slate-500 max-w-sm mx-auto">
          {locale === 'ar'
            ? 'تتم معالجة مواصفات العقار عبر خوارزمية التقييم المطابقة للمنطقة.'
            : 'Rapprochement des caractéristiques du bien avec les séries statistiques locales.'}
        </p>
      </div>
    );
  }

  // 2. Offline / Connecting / Honest State (No Fake Estimation)
  if (isOffline || error) {
    return (
      <div className="p-8 sm:p-10 rounded-3xl bg-slate-50 dark:bg-brand-navy-surface border border-slate-200 dark:border-white/10 text-center space-y-6">
        <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto text-amber-600 dark:text-amber-400">
          <AlertTriangle className="w-7 h-7" />
        </div>

        <div className="space-y-2 max-w-md mx-auto">
          <h3 className="text-xl font-extrabold text-slate-900 dark:text-white">
            {d.offlineTitle}
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {d.offlineMessage}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 pt-2 font-mono">
            {error || 'Statut: API ML en attente de déploiement / calibrage'}
          </p>
        </div>

        <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            {d.retry}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
          >
            {dict.common.reset}
          </Button>
        </div>
      </div>
    );
  }

  // 3. Authentic Prediction State (From Real Backend API)
  if (prediction && prediction.estimated_price_mad !== undefined) {
    const hasRange = prediction.prix_min !== undefined && prediction.prix_max !== undefined;
    const hasPpm = prediction.prix_par_m2 !== undefined;
    const modelVersion = prediction.model_version;

    return (
      <div className="space-y-6">
        {/* Main Price Card */}
        <div className="p-8 sm:p-10 rounded-3xl bg-white dark:bg-brand-navy-surface border border-slate-200/90 dark:border-white/10 shadow-lg shadow-slate-900/5 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>{d.title}</span>
          </div>

          <div>
            <span className="text-xs uppercase tracking-wider font-semibold text-slate-400 block mb-1">
              {d.priceLabel}
            </span>
            <div className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 dark:text-white tracking-tight">
              {formatCurrency(prediction.estimated_price_mad, locale)}
            </div>
          </div>

          {/* Optional Range (Only if real API provides it) */}
          {hasRange && (
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-white/5 max-w-md mx-auto">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                {d.rangeLabel}
              </span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-200 font-mono">
                {formatCurrency(prediction.prix_min, locale)} — {formatCurrency(prediction.prix_max, locale)}
              </span>
            </div>
          )}

          {/* Metric Details (Only if available) */}
          <div className="pt-4 border-t border-slate-100 dark:border-white/5 flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-xs">
            {hasPpm && (
              <div>
                <span className="text-slate-400 block">{d.pricePerM2Label}</span>
                <span className="text-sm font-bold text-slate-800 dark:text-slate-200 font-mono">
                  {formatCurrency(prediction.prix_par_m2, locale)} / m²
                </span>
              </div>
            )}
            <div>
              <span className="text-slate-400 block">{dict.estimation.cityField}</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                {prediction.ville || formData.ville}
              </span>
            </div>
            {formData.quartier && (
              <div>
                <span className="text-slate-400 block">{dict.estimation.districtField}</span>
                <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                  {formData.quartier}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Dynamic Model Attribution (Never hard-coding "Phase 4") */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/40 border border-slate-200/60 dark:border-white/5 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-brand-blue dark:text-blue-400" />
            <span>
              {d.modelInfo} : {modelVersion ? `Modèle (${modelVersion})` : 'MaisonDeLUX Algorithmic Engine'}
            </span>
          </div>
          <span className="font-mono">Devise: MAD</span>
        </div>

        <p className="text-sm text-center text-slate-500">{locale === 'ar' ? 'تقدير إحصائي استرشادي، وليس تقييماً عقارياً رسمياً.' : 'Estimation statistique indicative, ne constituant pas une expertise immobilière officielle.'}</p>
        {/* Actions */}
        <div className="flex items-center justify-center gap-4 pt-2">
          <Button
            variant="outline"
            size="md"
            onClick={onReset}
          >
            {dict.common.reset}
          </Button>
        </div>
      </div>
    );
  }

  return null;
}
