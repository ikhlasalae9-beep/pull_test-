'use client';

import { useEffect } from 'react';

interface LocaleHandlerProps {
  locale: string;
  dir: 'rtl' | 'ltr';
}

export function LocaleHandler({ locale, dir }: LocaleHandlerProps) {
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = dir;
  }, [locale, dir]);

  return null;
}
