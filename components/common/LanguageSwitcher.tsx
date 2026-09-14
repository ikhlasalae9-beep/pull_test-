'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Globe } from 'lucide-react';

interface LanguageSwitcherProps {
  currentLocale: string;
  className?: string;
  showIcon?: boolean;
}

export function LanguageSwitcher({
  currentLocale,
  className = '',
  showIcon = true,
}: LanguageSwitcherProps) {
  const pathname = usePathname() || `/${currentLocale}`;
  const router = useRouter();

  const switchLanguage = (targetLocale: string) => {
    if (targetLocale === currentLocale) return;

    let newPath = pathname;
    if (pathname.startsWith(`/${currentLocale}`)) {
      newPath = pathname.replace(`/${currentLocale}`, `/${targetLocale}`);
    } else {
      newPath = `/${targetLocale}${pathname}`;
    }

    router.push(newPath);
  };

  return (
    <div
      role="group"
      aria-label="Sélection de la langue"
      className={`inline-flex items-center rounded-full p-0.5 bg-slate-100/80 dark:bg-white/6 border border-slate-200/80 dark:border-white/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.6)] dark:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)] backdrop-blur-md text-xs font-semibold ${className}`}
    >
      {showIcon && (
        <span className="ps-2 pe-1 text-slate-400 dark:text-slate-500 select-none flex items-center">
          <Globe className="w-3.5 h-3.5" />
        </span>
      )}

      <button
        type="button"
        onClick={() => switchLanguage('fr')}
        aria-pressed={currentLocale === 'fr'}
        className={`px-2.5 py-1 rounded-full transition-all duration-200 ${
          currentLocale === 'fr'
            ? 'bg-white dark:bg-white/15 text-brand-navy dark:text-white font-bold shadow-xs border border-slate-200/60 dark:border-white/10'
            : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
        }`}
      >
        FR
      </button>

      <button
        type="button"
        onClick={() => switchLanguage('ar')}
        aria-pressed={currentLocale === 'ar'}
        className={`px-2.5 py-1 rounded-full transition-all duration-200 font-arabic ${
          currentLocale === 'ar'
            ? 'bg-white dark:bg-white/15 text-brand-navy dark:text-white font-bold shadow-xs border border-slate-200/60 dark:border-white/10'
            : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
        }`}
      >
        العربية
      </button>
    </div>
  );
}
