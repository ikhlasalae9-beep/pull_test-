import React from 'react';
import { getDictionary } from '@/lib/i18n/getDictionary';
import { Hero } from '@/components/landing/Hero';
import { LocationExplorer } from '@/components/landing/LocationExplorer';
import { HowItWorks } from '@/components/landing/HowItWorks';
import { WhyMaisonDeLUX } from '@/components/landing/WhyMaisonDeLUX';
import { TrustMethodology } from '@/components/landing/TrustMethodology';
import { FAQSection } from '@/components/landing/FAQSection';

interface LandingPageProps {
  params: {
    locale: string;
  };
}

export default function LandingPage({ params }: LandingPageProps) {
  const { locale } = params;
  const dict = getDictionary(locale);

  return (
    <div className="flex flex-col">
      {/* 1. Hero Section: "Quelle est la valeur de votre bien ?" + Quick-Start */}
      <Hero locale={locale} dict={dict} />

      {/* 2. Location Explorer: "Où se trouve votre bien ?" + Morocco SVG Map */}
      <LocationExplorer locale={locale} dict={dict} />

      {/* 3. How It Works: Asymmetric 3-step editorial process */}
      <HowItWorks locale={locale} dict={dict} />

      {/* 4. Why MaisonDeLUX: Structured multi-variable valuation vs. generic guesses */}
      <WhyMaisonDeLUX locale={locale} dict={dict} />

      {/* 5. Trust & Methodology: Transparent data ethics & model boundaries */}
      <TrustMethodology locale={locale} dict={dict} />

      {/* 6. FAQ Section: Collapsible accordion */}
      <FAQSection locale={locale} dict={dict} />
    </div>
  );
}
