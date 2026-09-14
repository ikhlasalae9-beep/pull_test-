'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';

interface BrandLogoProps {
  locale?: string;
  className?: string;
  size?: 'default' | 'large' | 'compact';
}

export function BrandLogo({
  locale = 'fr',
  className = '',
  size = 'default',
}: BrandLogoProps) {
  // Using official horizontal logo asset with optimal clarity and presence
  // Light mode: native deep navy & primary blue
  // Dark mode: crisp luminous pure white inversion for luxury dark backgrounds
  const sizeClasses = {
    compact: 'h-8.5 w-40 sm:w-44',
    default: 'h-10 sm:h-11 md:h-12 w-48 sm:w-56 md:w-64',
    large: 'h-12 sm:h-14 w-56 sm:w-64 md:w-72',
  };

  return (
    <Link
      href={`/${locale}`}
      aria-label="MaisonDeLUX - Accueil"
      className={`inline-flex items-center group transition-all duration-200 hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue rounded-xl ${className}`}
    >
      <div className={`relative ${sizeClasses[size]} transition-all duration-200`}>
        <Image
          src="/brand/logo/maisondelux-logo-horizontal.png"
          alt="MaisonDeLUX"
          fill
          sizes="(max-width: 640px) 192px, (max-width: 768px) 224px, 256px"
          className="object-contain object-left rtl:object-right dark:brightness-0 dark:invert transition-all duration-200"
          priority
        />
      </div>
    </Link>
  );
}
