import type { Locale } from './config';
import fr from '@/messages/fr.json';
import ar from '@/messages/ar.json';

const dictionaries = {
  fr,
  ar,
};

export function getDictionary(locale: string = 'fr') {
  return dictionaries[(locale as Locale)] || dictionaries.fr;
}

export type Dictionary = typeof fr;
