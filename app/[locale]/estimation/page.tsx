import React, { Suspense } from 'react';
import type { Metadata } from 'next';
import { getDictionary } from '@/lib/i18n/getDictionary';
import { EstimatorShell } from '@/components/estimation/EstimatorShell';

interface EstimationPageProps {
  params: {
    locale: string;
  };
}

export async function generateMetadata({
  params,
}: EstimationPageProps): Promise<Metadata> {
  const dict = getDictionary(params.locale);

  return {
    title: `${dict.estimation.pageTitle} — ${dict.common.brandName}`,
    description: dict.estimation.pageSubtitle,
  };
}

export default function EstimationPage({ params }: EstimationPageProps) {
  const { locale } = params;
  const dict = getDictionary(locale);

  return (
    <div className="py-12 sm:py-16 lg:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50/50 dark:bg-brand-navy-deep min-h-[calc(100vh-72px)] flex flex-col items-center justify-center transition-colors">
      <Suspense
        fallback={
          <div className="w-full max-w-3xl py-20 text-center text-slate-500 font-medium">
            Chargement de l&apos;estimateur...
          </div>
        }
      >
        <EstimatorShell locale={locale} dict={dict} />
      </Suspense>
    </div>
  );
}
