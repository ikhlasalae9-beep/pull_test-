'use client';

import React from 'react';
import { motion, useScroll, useSpring } from 'framer-motion';
import { isRTL } from '@/lib/i18n/config';

interface ScrollProgressProps {
  locale?: string;
}

export function ScrollProgress({ locale = 'fr' }: ScrollProgressProps) {
  const { scrollYProgress } = useScroll();
  const rtl = isRTL(locale);

  // Buttery-smooth spring physics for the progress bar
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 24,
    restDelta: 0.001,
  });

  return (
    <div className="fixed top-0 inset-x-0 h-[2.5px] z-[70] pointer-events-none">
      <motion.div
        style={{
          scaleX,
          transformOrigin: rtl ? 'right' : 'left',
        }}
        className="w-full h-full bg-gradient-to-r from-blue-700 via-blue-500 to-sky-400 shadow-[0_0_8px_rgba(29,78,216,0.6)]"
      />
    </div>
  );
}
