import React from 'react';
import Link from 'next/link';
import { BrandLogo } from '@/components/common/BrandLogo';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';
import { NAV_LINKS } from '@/config/navigation.config';

interface FooterProps {
  locale: string;
  dict: any;
}

export function Footer({ locale, dict }: FooterProps) {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-slate-200/80 dark:border-white/10 bg-white/50 dark:bg-brand-navy-deep/60 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 sm:py-16">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 lg:gap-14 mb-12">
          {/* Brand description column */}
          <div className="md:col-span-5 space-y-4">
            <BrandLogo locale={locale} />
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm leading-relaxed">
              {dict.footer.brandDescription}
            </p>
            <div className="pt-2">
              <span className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200/60 dark:border-slate-700/60">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                {dict.footer.dataSource}
              </span>
            </div>
          </div>

          {/* Navigation column */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
              {dict.footer.navigationTitle}
            </h4>
            <ul className="space-y-2.5 text-sm text-slate-500 dark:text-slate-400">
              {NAV_LINKS.map((link) => {
                const label = locale === 'ar' ? link.labelAr : link.labelFr;
                return (
                  <li key={link.href}>
                    <a
                      href={link.href}
                      className="hover:text-brand-blue dark:hover:text-blue-400 transition-colors"
                    >
                      {label}
                    </a>
                  </li>
                );
              })}
              <li>
                <Link
                  href={`/${locale}/estimation`}
                  className="font-medium text-brand-blue dark:text-blue-400 hover:underline"
                >
                  {dict.common.estimateCta}
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal / Methodological note */}
          <div className="md:col-span-4 space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
              {dict.footer.legalTitle}
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              {dict.footer.legalNote}
            </p>
            <div className="pt-3 flex items-center gap-3">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {dict.footer.localeSwitch} :
              </span>
              <LanguageSwitcher currentLocale={locale} />
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-slate-200/60 dark:border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500 dark:text-slate-500">
          <p>
            © {currentYear} {dict.common.brandName} · {dict.common.allRightsReserved}
          </p>
          <div className="flex items-center gap-6">
            <span>Royaume du Maroc</span>
            <span>·</span>
            <span>Rigueur Statistique</span>
            <span>·</span>
            <span>Architecture & Données</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
