import React from 'react';
import type { Metadata } from 'next';
import '@/app/globals.css';

export const metadata: Metadata = {
  title: "MaisonDeLUX — L'intelligence prédictive de valorisation immobilière au Maroc",
  description: "Plateforme d'intelligence prédictive dédiée à la valorisation immobilière au Maroc. Modélisation multi-critères, calibrage géographique et rigueur statistique.",
  icons: {
    icon: [
      { url: '/brand/icons/maisondelux-app-blue.png', sizes: 'any', type: 'image/png' },
    ],
    apple: [
      { url: '/brand/icons/maisondelux-app-blue.png', sizes: '180x180', type: 'image/png' },
    ],
    shortcut: '/brand/icons/maisondelux-app-blue.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <link rel="icon" type="image/png" href="/brand/icons/maisondelux-app-blue.png" />
        <link rel="apple-touch-icon" href="/brand/icons/maisondelux-app-blue.png" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const theme = localStorage.getItem('maisondelux_theme');
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (theme === 'dark' || (!theme && prefersDark)) {
                  document.documentElement.classList.add('dark');
                  document.documentElement.setAttribute('data-theme', 'dark');
                } else {
                  document.documentElement.classList.remove('dark');
                  document.documentElement.setAttribute('data-theme', 'light');
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className="min-h-screen flex flex-col bg-slate-50 dark:bg-brand-navy-deep text-slate-900 dark:text-white transition-colors duration-200">
        {children}
      </body>
    </html>
  );
}
