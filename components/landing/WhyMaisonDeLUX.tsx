'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Check, X, ShieldAlert, Binary, CheckCircle } from 'lucide-react';
import { isRTL } from '@/lib/i18n/config';

interface WhyMaisonDeLUXProps {
  locale: string;
  dict: any;
}

export function WhyMaisonDeLUX({ locale, dict }: WhyMaisonDeLUXProps) {
  const points = dict.whyMaisonDeLux.points || [];
  const rtl = isRTL(locale);

  return (
    <section
      id="pourquoi"
      className="min-h-auto lg:min-h-[100svh] flex flex-col justify-center py-16 sm:py-20 lg:py-10 scroll-mt-24 lg:scroll-mt-28 bg-white dark:bg-brand-navy transition-colors border-t border-slate-200/80 dark:border-white/5 relative"
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
            {dict.whyMaisonDeLux.badge}
          </span>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 dark:text-white leading-tight">
            {dict.whyMaisonDeLux.title}
          </h2>
          <p className="mt-2 text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl mx-auto">
            {dict.whyMaisonDeLux.subtitle}
          </p>
        </motion.div>

        {/* 2-Column Comparison Layout with Scroll Reveal */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10 items-center">
          {/* Left: Architectural Feature Points */}
          <div className="lg:col-span-6 space-y-3.5">
            {points.map((pt: any, idx: number) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: rtl ? 16 : -16 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '-8% 0px' }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="p-4.5 sm:p-5 rounded-2xl bg-slate-50/90 dark:bg-brand-navy-surface border border-slate-200/80 dark:border-white/10 shadow-xs hover:border-slate-300 dark:hover:border-white/20 transition-all"
              >
                <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white mb-1.5 flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded-lg bg-brand-blue/10 dark:bg-blue-400/10 text-brand-blue dark:text-blue-400 flex items-center justify-center text-xs font-bold shrink-0">
                    0{idx + 1}
                  </span>
                  {pt.title}
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed ps-8.5">
                  {pt.description}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Right: Structural Comparison Board */}
          <motion.div
            initial={{ opacity: 0, x: rtl ? -16 : 16 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-8% 0px' }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-6"
          >
            <div className="bg-slate-900 text-white rounded-2xl p-5 sm:p-6 shadow-xl border border-slate-800">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <span className="text-xs font-mono uppercase tracking-wider text-blue-400 font-semibold">
                  {locale === 'ar' ? 'مقارنة منهجية' : 'Matrice de différenciation'}
                </span>
                <Binary className="w-4 h-4 text-slate-500" />
              </div>

              <div className="mt-4 space-y-3.5">
                {/* Row 1 */}
                <div className="grid grid-cols-2 gap-4 pb-3 border-b border-slate-800/60">
                  <div className="space-y-1">
                    <span className="text-[11px] text-slate-400 uppercase font-semibold flex items-center gap-1.5">
                      <X className="w-3.5 h-3.5 text-rose-400" />
                      {locale === 'ar' ? 'تقدير سطحي' : 'Approche générique'}
                    </span>
                    <p className="text-xs text-slate-300">
                      {locale === 'ar' ? 'تطبيق متوسط سعري ثابت للمتر المربع' : 'Application d\'un prix moyen au m² uniforme'}
                    </p>
                  </div>
                  <div className="space-y-1 ps-2 border-s border-slate-800">
                    <span className="text-[11px] text-blue-400 uppercase font-semibold flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      {locale === 'ar' ? 'خوارزمية MaisonDeLUX' : 'MaisonDeLUX ML'}
                    </span>
                    <p className="text-xs text-slate-200 font-medium">
                      {locale === 'ar' ? 'تحليل متزامن للموقع والمواصفات الصافية' : 'Pondération simultanée surface, micro-secteur & standing'}
                    </p>
                  </div>
                </div>

                {/* Row 2 */}
                <div className="grid grid-cols-2 gap-4 pb-4 border-b border-slate-800/60">
                  <div className="space-y-1">
                    <span className="text-[11px] text-slate-400 uppercase font-semibold flex items-center gap-1.5">
                      <X className="w-3.5 h-3.5 text-rose-400" />
                      {locale === 'ar' ? 'بيانات غير مدققة' : 'Données brutes non filtrées'}
                    </span>
                    <p className="text-xs text-slate-300">
                      {locale === 'ar' ? 'تكرارات وأسعار مبالغ فيها أو شاذة' : 'Doublons, annonces erratiques, aberrations de prix'}
                    </p>
                  </div>
                  <div className="space-y-1 ps-2 border-s border-slate-800">
                    <span className="text-[11px] text-blue-400 uppercase font-semibold flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      {locale === 'ar' ? 'تصفية صارمة' : 'Pipeline audité'}
                    </span>
                    <p className="text-xs text-slate-200 font-medium">
                      {locale === 'ar' ? 'استبعاد منهجي للشواذ والأخطاء البيانية' : 'Élimination des outliers et contrôle strict de validité'}
                    </p>
                  </div>
                </div>

                {/* Row 3 */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="text-[11px] text-slate-400 uppercase font-semibold flex items-center gap-1.5">
                      <X className="w-3.5 h-3.5 text-rose-400" />
                      {locale === 'ar' ? 'إعلانات تجارية' : 'Biais commercial'}
                    </span>
                    <p className="text-xs text-slate-300">
                      {locale === 'ar' ? 'مبالغة في السعر لتحفيز الإعلان' : 'Surévaluation d\'appel ou incitation à la vente'}
                    </p>
                  </div>
                  <div className="space-y-1 ps-2 border-s border-slate-800">
                    <span className="text-[11px] text-blue-400 uppercase font-semibold flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      {locale === 'ar' ? 'حياد مطلق' : 'Indépendance totale'}
                    </span>
                    <p className="text-xs text-slate-200 font-medium">
                      {locale === 'ar' ? 'تقييم إحصائي مجرد بدون وساطة تجارية' : 'Calcul purement probabiliste et objectif'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
