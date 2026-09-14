import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | undefined | null, locale: string = 'fr'): string {
  if (amount === undefined || amount === null || isNaN(amount)) return '—';
  
  const formatted = Math.round(amount).toLocaleString(locale === 'ar' ? 'ar-MA' : 'fr-FR');
  if (locale === 'ar') {
    return `${formatted} درهم`;
  }
  return `${formatted} MAD`;
}

export function formatNumber(num: number | undefined | null, locale: string = 'fr'): string {
  if (num === undefined || num === null || isNaN(num)) return '—';
  return num.toLocaleString(locale === 'ar' ? 'ar-MA' : 'fr-FR');
}
