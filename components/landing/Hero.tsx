'use client';

import React, { useState, useEffect } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { ShieldCheck, Compass, ArrowRight, ArrowLeft } from 'lucide-react';
import { QuickStartBar } from './QuickStartBar';
import { isRTL } from '@/lib/i18n/config';

interface HeroProps {
  locale: string;
  dict: any;
}

export function Hero({ locale, dict }: HeroProps) {
  const rtl = isRTL(locale);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(media.matches);
  }, []);

  const { scrollY } = useScroll();
  // Low-intensity, architectural parallax
  const backgroundY = useTransform(scrollY, [0, 600], [0, reducedMotion ? 0 : 35]);
  const subtleGlowY = useTransform(scrollY, [0, 600], [0, reducedMotion ? 0 : 50]);

  return (
    <section className="relative overflow-hidden min-h-[100svh] flex flex-col justify-center pt-24 pb-12 sm:pt-28 sm:pb-16 bg-gradient-to-b from-slate-50/50 via-white to-slate-50/30 dark:from-brand-navy-deep dark:via-brand-navy dark:to-brand-navy-deep transition-colors">
      {/* Subtle architectural background accents with gentle parallax */}
      <motion.div
        style={{ y: backgroundY }}
        className="absolute inset-0 pointer-events-none opacity-40 dark:opacity-20 will-change-transform"
      >
        <div className="absolute top-0 start-1/2 -translate-x-1/2 w-full max-w-7xl h-full border-x border-slate-200/50 dark:border-white/5" />
        <div className="absolute top-1/4 start-0 w-full border-t border-slate-200/40 dark:border-white/5" />
      </motion.div>

      {/* Ambient Blue Accent Glow */}
      <motion.div
        style={{ y: subtleGlowY }}
        className="absolute top-10 start-1/2 -translate-x-1/2 w-[550px] h-[350px] bg-blue-500/8 dark:bg-blue-500/12 rounded-full blur-3xl pointer-events-none will-change-transform"
      />

      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center z-10">
        {/* Architectural Badge */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-brand-blue/8 text-brand-blue dark:bg-blue-500/15 dark:text-blue-300 border border-brand-blue/15 dark:border-blue-400/20 mb-8"
        >
          <Compass className="w-3.5 h-3.5" />
          <span>{dict.hero.badge}</span>
        </motion.div>

        {/* Hero Title */}
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white max-w-4xl mx-auto leading-[1.12]"
        >
          {dict.hero.title}
        </motion.h1>

        {/* Hero Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-6 text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto font-normal leading-relaxed"
        >
          {dict.hero.subtitle}
        </motion.p>

        {/* Interactive QuickStart Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-10 sm:mt-12 flex justify-center"
        >
          <QuickStartBar locale={locale} dict={dict} />
        </motion.div>

        {/* Trust Badges Bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-xs text-slate-500 dark:text-slate-400 font-medium"
        >
          <span className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-brand-blue dark:text-blue-400" />
            Modélisation multi-critères
          </span>
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-600" />
            Données de marché auditées
          </span>
          <span className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-600" />
            Accès direct sans inscription
          </span>
        </motion.div>
      </div>
    </section>
  );
}
