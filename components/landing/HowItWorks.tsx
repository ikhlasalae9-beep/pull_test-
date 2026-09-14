'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layers, Cpu, TrendingUp, ShieldCheck, Building2, BarChart3, CheckCircle2 } from 'lucide-react';
import { isRTL } from '@/lib/i18n/config';

interface HowItWorksProps {
  locale: string;
  dict: any;
}

export function HowItWorks({ locale, dict }: HowItWorksProps) {
  const [activeStep, setActiveStep] = useState(0);
  const rtl = isRTL(locale);

  const steps = [
    {
      num: '01',
      title: dict.howItWorks.step1Title,
      desc: dict.howItWorks.step1Desc,
      icon: <Layers className="w-4.5 h-4.5" />,
      detail: locale === 'ar' ? 'المعايير الهندسية' : 'Paramètres intrinsèques',
      badge: locale === 'ar' ? 'المرحلة الأولى' : 'Étape Initiale',
    },
    {
      num: '02',
      title: dict.howItWorks.step2Title,
      desc: dict.howItWorks.step2Desc,
      icon: <Cpu className="w-4.5 h-4.5" />,
      detail: locale === 'ar' ? 'المطابقة الإحصائية' : 'Rapprochement statistique',
      badge: locale === 'ar' ? 'المرحلة التحليلية' : 'Calibrage ML',
    },
    {
      num: '03',
      title: dict.howItWorks.step3Title,
      desc: dict.howItWorks.step3Desc,
      icon: <TrendingUp className="w-4.5 h-4.5" />,
      detail: locale === 'ar' ? 'القيمة والمجال' : 'Valeur & Dispersion',
      badge: locale === 'ar' ? 'مخرجات النموذج' : 'Restitution Finale',
    },
  ];

  // Compact Laboratory Visual State Component
  const renderVisualState = (stepIdx: number) => {
    if (stepIdx === 0) {
      return (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold flex items-center gap-1.5 text-slate-900 dark:text-white">
              <Building2 className="w-4 h-4 text-brand-blue dark:text-blue-400" />
              {locale === 'ar' ? 'مخطط البيانات الأساسية' : 'Schéma des Attributs'}
            </span>
            <span className="font-mono text-[11px] text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {locale === 'ar' ? 'معتمد' : 'Vérifié'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200/60 dark:border-white/5">
              <span className="text-[10px] text-slate-400 block mb-0.5 uppercase tracking-wider">Typologie</span>
              <span className="font-bold text-slate-900 dark:text-white">Appartement</span>
            </div>
            <div className="p-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200/60 dark:border-white/5">
              <span className="text-[10px] text-slate-400 block mb-0.5 uppercase tracking-wider">Surface brute</span>
              <span className="font-bold text-slate-900 dark:text-white">95 m² habitables</span>
            </div>
            <div className="p-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200/60 dark:border-white/5">
              <span className="text-[10px] text-slate-400 block mb-0.5 uppercase tracking-wider">Distribution</span>
              <span className="font-bold text-slate-900 dark:text-white">3 ch. · 2 sdb</span>
            </div>
            <div className="p-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200/60 dark:border-white/5">
              <span className="text-[10px] text-slate-400 block mb-0.5 uppercase tracking-wider">Finition</span>
              <span className="font-bold text-slate-900 dark:text-white">Haut standing</span>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-900/40 text-[11px] text-blue-800 dark:text-blue-300 leading-relaxed">
            {locale === 'ar'
              ? 'استبعاد التخمينات الذاتية وتحديد الهيكل الهندسي الدقيق للعقار.'
              : 'Structuration univoque des vecteurs caractéristiques sans bruit descriptif.'}
          </div>
        </div>
      );
    }

    if (stepIdx === 1) {
      return (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold flex items-center gap-1.5 text-slate-900 dark:text-white">
              <Cpu className="w-4 h-4 text-brand-blue dark:text-blue-400" />
              {locale === 'ar' ? 'محرك المطابقة الإحصائية' : 'Moteur de Régression'}
            </span>
            <span className="font-mono text-[11px] text-brand-blue dark:text-blue-400 font-bold">
              Calibré
            </span>
          </div>

          <div className="space-y-2">
            <div className="p-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200/60 dark:border-white/5">
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-slate-600 dark:text-slate-300 font-medium">
                  {locale === 'ar' ? 'تنقية البيانات من القيم الشاذة' : 'Filtrage outliers & doublons'}
                </span>
                <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">100%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full w-full" />
              </div>
            </div>

            <div className="p-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200/60 dark:border-white/5">
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-slate-600 dark:text-slate-300 font-medium">
                  {locale === 'ar' ? 'تطابق السلسلة الزمنية للمدينة' : 'Corpus géographique audité'}
                </span>
                <span className="font-mono text-brand-blue dark:text-blue-400 font-bold">Actif</span>
              </div>
              <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-brand-blue rounded-full w-[92%]" />
              </div>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-100/80 dark:bg-slate-800/50 border border-slate-200/60 dark:border-white/5 text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed">
            {locale === 'ar'
              ? 'المطابقة الحصرية مع العقارات المماثلة الفعلية في نفس المدينة والحي.'
              : 'Aucune extrapolation hors territoire. Calibrage strict sur le corpus audité.'}
          </div>
        </div>
      );
    }

    // stepIdx === 2
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="font-semibold flex items-center gap-1.5 text-slate-900 dark:text-white">
            <BarChart3 className="w-4 h-4 text-brand-blue dark:text-blue-400" />
            {locale === 'ar' ? 'المؤشرات والفاصل الرياضي' : 'Restitution d\'Encadrement'}
          </span>
          <span className="font-mono text-[11px] text-blue-600 dark:text-blue-400 font-bold">
            MAD
          </span>
        </div>

        <div className="p-3 rounded-2xl bg-gradient-to-br from-brand-blue/10 via-transparent to-blue-500/5 border border-brand-blue/20 text-center space-y-1">
          <span className="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400 block font-semibold">
            {locale === 'ar' ? 'القيمة الإرشادية المحسوبة' : 'Estimation Indicative du Modèle'}
          </span>
          <div className="text-2xl font-black text-brand-navy dark:text-white">
            1 250 000 <span className="text-sm font-bold text-brand-blue">MAD</span>
          </div>
          <div className="pt-1.5 border-t border-slate-200/60 dark:border-white/10 flex justify-around text-[11px]">
            <div>
              <span className="text-[9px] text-slate-400 block uppercase">Fourchette basse</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">1 190 000 MAD</span>
            </div>
            <div>
              <span className="text-[9px] text-slate-400 block uppercase">Fourchette haute</span>
              <span className="font-bold text-slate-700 dark:text-slate-200">1 320 000 MAD</span>
            </div>
          </div>
        </div>

        <div className="p-2 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-900/40 text-[11px] text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span className="leading-relaxed">
            {locale === 'ar'
              ? 'إظهار النتائج بناءً على عقد البيانات الرسمي فقط.'
              : 'Encadrement basé uniquement sur les retours réels du moteur d\'inférence.'}
          </span>
        </div>
      </div>
    );
  };

  return (
    <section
      id="demarche"
      className="py-12 lg:py-16 scroll-mt-24 lg:scroll-mt-28 bg-slate-50/70 dark:bg-brand-navy-deep/80 transition-colors border-t border-slate-200/80 dark:border-white/5 relative overflow-hidden"
    >
      {/* Background Architectural Grid Accents */}
      <div className="absolute inset-0 pointer-events-none opacity-30 dark:opacity-15">
        <div className="max-w-7xl mx-auto h-full border-x border-slate-200/60 dark:border-white/5" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 w-full">
        {/* Section Heading */}
        <div className="max-w-3xl mb-8 lg:mb-10">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-blue dark:text-blue-400 mb-1.5 block">
            {dict.howItWorks.badge}
          </span>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 dark:text-white leading-tight">
            {dict.howItWorks.title}
          </h2>
          <p className="mt-2 text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl">
            {dict.howItWorks.subtitle}
          </p>
        </div>

        {/* 2-Column Desktop Viewport Composition (approx 0.8fr : 1.2fr) */}
        <div className="grid grid-cols-1 lg:grid-cols-[0.8fr_1.2fr] gap-8 lg:gap-14 items-center">
          {/* LEFT: Existing Laboratoire d'Évaluation Visual Panel */}
          <div className="order-2 lg:order-1">
            <div className="relative rounded-2xl p-5 sm:p-6 backdrop-blur-xl bg-white/90 dark:bg-[#0c1322]/90 border border-slate-200/90 dark:border-white/10 shadow-lg shadow-slate-900/5 dark:shadow-black/50 overflow-hidden flex flex-col justify-between min-h-[340px] lg:min-h-[360px]">
              {/* Ambient Glow */}
              <div className="absolute -top-20 -right-20 w-48 h-48 bg-blue-500/10 dark:bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />

              {/* Header with Interactive Tabs */}
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-white/5 pb-3 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-brand-blue animate-pulse" />
                    <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      {locale === 'ar' ? 'مختبر التقييم الرقمي' : 'Laboratoire d\'Évaluation'}
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-blue/10 text-brand-blue dark:text-blue-300 border border-brand-blue/20">
                    {steps[activeStep].badge}
                  </span>
                </div>

                {/* Tab selector pills */}
                <div className="flex items-center gap-1.5 p-1 bg-slate-100/70 dark:bg-white/5 rounded-xl mb-3">
                  {steps.map((st, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setActiveStep(i)}
                      className={`flex-1 py-1 px-2 rounded-lg text-[11px] font-semibold transition-all duration-200 flex items-center justify-center gap-1.5 ${
                        activeStep === i
                          ? 'bg-white dark:bg-brand-navy text-brand-blue dark:text-blue-300 shadow-xs border border-slate-200/60 dark:border-white/10'
                          : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
                      }`}
                    >
                      <span className="font-mono text-[10px]">{st.num}</span>
                      <span className="truncate">
                        {st.num === '01'
                          ? (locale === 'ar' ? 'البيانات' : 'Attributs')
                          : st.num === '02'
                          ? (locale === 'ar' ? 'النمذجة' : 'Calibrage')
                          : (locale === 'ar' ? 'النتيجة' : 'Résultat')}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic State Preview */}
              <div className="my-auto py-2">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={`visual-${activeStep}`}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.25, ease: 'easeOut' }}
                  >
                    {renderVisualState(activeStep)}
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* Bottom Telemetry Bar */}
              <div className="border-t border-slate-100 dark:border-white/5 pt-3 flex items-center justify-between text-xs text-slate-400">
                <span className="text-[11px] font-mono">
                  {locale === 'ar' ? `المرحلة 0${activeStep + 1} من 03` : `Étape 0${activeStep + 1} / 03`}
                </span>
                <div className="flex items-center gap-1">
                  {steps.map((_, i) => (
                    <span
                      key={i}
                      className={`h-1.5 rounded-full transition-all duration-300 ${
                        activeStep === i
                          ? 'w-5 bg-brand-blue'
                          : 'w-1.5 bg-slate-200 dark:bg-slate-700'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT: Compact Vertical Timeline (All 3 steps visible, NO cards) */}
          <div className="order-1 lg:order-2 flex flex-col justify-center">
            {steps.map((step, idx) => {
              const isCurrent = activeStep === idx;
              const isStep1 = idx === 0;

              return (
                <div key={step.num} className="group">
                  {/* Step Row (Unboxed, pure typography & timeline rhythm) */}
                  <div
                    onClick={() => setActiveStep(idx)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setActiveStep(idx);
                      }
                    }}
                    className="cursor-pointer text-start transition-colors duration-150 focus:outline-none"
                  >
                    {/* Header Row: Number + Title + Subtle Blue Accent (on Step 01) */}
                    <div className="flex items-center gap-3 sm:gap-4">
                      <span
                        className={`font-mono font-black text-2xl sm:text-3xl shrink-0 w-8 sm:w-9 transition-colors ${
                          isStep1 || isCurrent
                            ? 'text-brand-blue dark:text-blue-400'
                            : 'text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-300'
                        }`}
                      >
                        {step.num}
                      </span>

                      <h3
                        className={`transition-colors ${
                          isStep1
                            ? 'text-base sm:text-lg font-extrabold text-slate-900 dark:text-white'
                            : isCurrent
                            ? 'text-base sm:text-lg font-bold text-slate-900 dark:text-white'
                            : 'text-base sm:text-lg font-bold text-slate-800 dark:text-slate-200 group-hover:text-brand-blue dark:group-hover:text-blue-300'
                        }`}
                      >
                        {step.title}
                      </h3>

                      {isStep1 && (
                        <span className="ms-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-50 dark:bg-blue-950/60 text-brand-blue dark:text-blue-300 border border-blue-200/80 dark:border-blue-800/40">
                          {step.badge}
                        </span>
                      )}
                    </div>

                    {/* Description: Indented under title */}
                    <p
                      className={`ps-[44px] sm:ps-[52px] mt-1 text-xs sm:text-sm leading-relaxed max-w-xl transition-colors ${
                        isStep1 || isCurrent
                          ? 'text-slate-700 dark:text-slate-300 font-medium'
                          : 'text-slate-500 dark:text-slate-400'
                      }`}
                    >
                      {step.desc}
                    </p>
                  </div>

                  {/* Vertical Connector Line between steps */}
                  {idx < steps.length - 1 && (
                    <div className="ps-[15px] sm:ps-[17px] my-2.5 sm:my-3">
                      <div
                        className={`w-[2px] h-7 sm:h-8 rounded-full ${
                          isStep1
                            ? 'bg-gradient-to-b from-brand-blue/60 via-slate-300 to-slate-200 dark:from-blue-400/60 dark:via-white/20 dark:to-white/10'
                            : 'bg-slate-200 dark:bg-white/15'
                        }`}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
