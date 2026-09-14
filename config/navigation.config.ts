export interface NavLink {
  href: string;
  labelFr: string;
  labelAr: string;
}

export const NAV_LINKS: NavLink[] = [
  {
    href: '#explorer',
    labelFr: 'Territoires',
    labelAr: 'المناطق الجغرافية',
  },
  {
    href: '#demarche',
    labelFr: 'Démarche',
    labelAr: 'منهجية العمل',
  },
  {
    href: '#pourquoi',
    labelFr: 'Pourquoi MaisonDeLUX',
    labelAr: 'لماذا MaisonDeLUX',
  },
  {
    href: '#methodologie',
    labelFr: 'Transparence & Données',
    labelAr: 'الشفافية والبيانات',
  },
  {
    href: '#faq',
    labelFr: 'Questions fréquentes',
    labelAr: 'الأسئلة الشائعة',
  },
];
