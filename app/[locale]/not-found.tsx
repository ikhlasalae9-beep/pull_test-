import React from 'react';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="py-24 text-center px-4">
      <span className="text-xs font-mono uppercase tracking-widest text-brand-blue dark:text-blue-400 block mb-2">
        Erreur 404
      </span>
      <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white mb-4">
        Page introuvable
      </h1>
      <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-8 text-sm">
        La ressource demandée n&apos;existe pas ou a été déplacée.
      </p>
      <Link
        href="/fr"
        className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl bg-brand-blue hover:bg-brand-blue-hover text-white text-sm font-semibold transition-colors"
      >
        Retour à l&apos;accueil
      </Link>
    </div>
  );
}
