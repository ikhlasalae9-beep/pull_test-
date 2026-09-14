'use client';

import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FAQSectionProps {
  locale: string;
  dict: any;
}

export function FAQSection({ locale, dict }: FAQSectionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);
  const items = dict.faq.items || [];

  const toggle = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section
      id="faq"
      className="min-h-auto lg:min-h-[90svh] xl:min-h-[100svh] flex flex-col justify-center py-16 sm:py-20 lg:py-12 scroll-mt-24 lg:scroll-mt-28 bg-white dark:bg-brand-navy transition-colors border-t border-slate-200/80 dark:border-white/5 relative"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        {/* Section Header with Scroll Reveal */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-8% 0px' }}
          transition={{ duration: 0.5 }}
          className="text-center mb-8 lg:mb-10"
        >
          <span className="text-xs font-bold uppercase tracking-wider text-brand-blue dark:text-blue-400 mb-2 block">
            {dict.faq.badge}
          </span>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 dark:text-white leading-tight">
            {dict.faq.title}
          </h2>
          <p className="mt-2 text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-xl mx-auto">
            {dict.faq.subtitle}
          </p>
        </motion.div>

        {/* Accordion List with Scroll Reveal */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-8% 0px' }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="space-y-3 max-w-3xl mx-auto"
        >
          {items.map((item: any, idx: number) => {
            const isOpen = openIndex === idx;

            return (
              <div
                key={idx}
                className={`rounded-2xl border transition-colors overflow-hidden ${
                  isOpen
                    ? 'border-brand-blue/40 dark:border-blue-400/40 bg-slate-50/70 dark:bg-brand-navy-surface shadow-xs'
                    : 'border-slate-200/80 dark:border-white/10 bg-white dark:bg-brand-navy-surface/60 hover:border-slate-300 dark:hover:border-white/20'
                }`}
              >
                <button
                  type="button"
                  onClick={() => toggle(idx)}
                  className="w-full px-5 py-4 flex items-center justify-between text-start gap-4 focus:outline-none"
                  aria-expanded={isOpen}
                >
                  <span className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                    {item.question}
                  </span>
                  <ChevronDown
                    className={`w-4 h-4 text-slate-400 shrink-0 transition-transform duration-200 ${
                      isOpen ? 'rotate-180 text-brand-blue dark:text-blue-400' : ''
                    }`}
                  />
                </button>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                    >
                      <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed border-t border-slate-100 dark:border-white/5">
                        {item.answer}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
