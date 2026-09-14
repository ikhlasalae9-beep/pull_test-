'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Database, FileText, AlertCircle } from 'lucide-react';

interface TrustMethodologyProps {
  locale: string;
  dict: any;
}

export function TrustMethodology({ locale, dict }: TrustMethodologyProps) {
  const pillars = dict.trust.pillars || [];
  const icons = [
    <Database key="1" className="w-4.5 h-4.5 text-brand-blue dark:text-blue-400" />,
    <FileText key="2" className="w-4.5 h-4.5 text-brand-blue dark:text-blue-400" />,
    <ShieldCheck key="3" className="w-4.5 h-4.5 text-brand-blue dark:text-blue-400" />,
  ];

  return (
    <section
      id="methodologie"
      className="min-h-auto lg:min-h-[100svh] flex flex-col justify-center py-16 sm:py-20 lg:py-10 scroll-mt-24 lg:scroll-mt-28 bg-slate-50/70 dark:bg-brand-navy-deep/70 transition-colors border-t border-slate-200/80 dark:border-white/5 relative"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        {/* Section Header with Scroll Reveal */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-8% 0px' }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl mb-6 lg:mb-8"
        >
          <span className="text-xs font-bold uppercase tracking-wider text-brand-blue dark:text-blue-400 mb-2 block">
            {dict.trust.badge}
          </span>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 dark:text-white leading-[1.15]">
            {dict.trust.title}
          </h2>
          <p className="mt-2 text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed">
            {dict.trust.subtitle}
          </p>
        </motion.div>

        {/* Pillars Grid with Staggered Scroll Reveal */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 lg:gap-6">
          {pillars.map((p: any, idx: number) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-8% 0px' }}
              transition={{ duration: 0.5, delay: idx * 0.1 }}
              className="bg-white dark:bg-brand-navy-surface border border-slate-200/80 dark:border-white/10 rounded-2xl p-5 sm:p-6 flex flex-col justify-between shadow-xs hover:border-brand-blue/30 dark:hover:border-blue-400/30 transition-all"
            >
              <div>
                <div className="w-9 h-9 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4 border border-slate-200/40 dark:border-white/5">
                  {icons[idx] || <ShieldCheck className="w-4 h-4 text-brand-blue dark:text-blue-400" />}
                </div>

                <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">
                  {p.title}
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  {p.description}
                </p>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 dark:border-white/5 flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                <span>Principe 0{idx + 1}</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Responsible Transparency Disclaimer Card with Scroll Reveal */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-8% 0px' }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-6 lg:mt-7 p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-900 dark:text-amber-200 flex items-start gap-3.5"
        >
          <AlertCircle className="w-4.5 h-4.5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm leading-relaxed">
            <strong className="font-semibold block mb-0.5">
              {locale === 'ar' ? 'بيان الشفافية والمسؤولية المهنية' : 'Engagement de rigueur et transparence'}
            </strong>
            <p className="text-amber-800 dark:text-amber-300/90 text-xs sm:text-[13px]">
              {locale === 'ar'
                ? 'التقديرات المقدمة ذات طبيعة إحصائية استرشادية، وتخضع لنطاق البيانات المعتمدة لقطاع الشقق السكنية. يهدف المحرك لتقديم قراءة رقمية محايدة تدعم اتخاذ القرار دون أن تلغي دور التوثيق القانوني والخبرة العقارية الميدانية.'
                : 'Les estimations générées sont de nature probabiliste et statistique, circonscrites au jeu de données audité du segment des appartements. Elles constituent une aide à la décision neutre et ne sauraient remplacer une visite sur site ou l\'expertise légale d\'un notaire.'}
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
