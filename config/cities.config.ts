/**
 * Verified cities configuration for MaisonDeLUX.
 * Directly derived from verified project data and geographic coverage audits.
 * Real geographic coordinates [longitude, latitude] extracted from verified data.
 * No speculative or fabricated cities or coordinates.
 */

export interface VerifiedCity {
  id: string;
  nameFr: string;
  nameAr: string;
  regionFr: string;
  regionAr: string;
  regionKey: string; // Matches region name in public/maps/maroc.geojson
  status: 'active' | 'referenced';
  hasActiveModelCoverage: boolean;
  coordinates: [number, number]; // [longitude, latitude]
}

export const VERIFIED_CITIES: VerifiedCity[] = [
  {
    id: 'casablanca',
    nameFr: 'Casablanca',
    nameAr: 'الدار البيضاء',
    regionFr: 'Casablanca-Settat',
    regionAr: 'الدار البيضاء - سطات',
    regionKey: 'Casablanca-Settat',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-7.61138, 33.58831],
  },
  {
    id: 'rabat',
    nameFr: 'Rabat',
    nameAr: 'الرباط',
    regionFr: 'Rabat-Salé-Kénitra',
    regionAr: 'الرباط - سلا - القنيطرة',
    regionKey: 'Rabat-Sale-Kenitra',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-6.83255, 34.01325],
  },
  {
    id: 'marrakech',
    nameFr: 'Marrakech',
    nameAr: 'مراكش',
    regionFr: 'Marrakech-Safi',
    regionAr: 'مراكش - آسفي',
    regionKey: 'Marrakech-Safi',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-7.99994, 31.63416],
  },
  {
    id: 'tanger',
    nameFr: 'Tanger',
    nameAr: 'طنجة',
    regionFr: 'Tanger-Tétouan-Al Hoceïma',
    regionAr: 'طنجة - تطوان - الحسيمة',
    regionKey: 'Tanger-Tetouan-Hoceima',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-5.79975, 35.76727],
  },
  {
    id: 'agadir',
    nameFr: 'Agadir',
    nameAr: 'أكادير',
    regionFr: 'Souss-Massa',
    regionAr: 'سوس - ماسة',
    regionKey: 'Souss Massa',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-9.59815, 30.42018],
  },
  {
    id: 'fes',
    nameFr: 'Fès',
    nameAr: 'فاس',
    regionFr: 'Fès-Meknès',
    regionAr: 'فاس - مكناس',
    regionKey: 'Fes-Meknes',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-5.00028, 34.03313],
  },
  {
    id: 'meknes',
    nameFr: 'Meknès',
    nameAr: 'مكناس',
    regionFr: 'Fès-Meknès',
    regionAr: 'فاس - مكناس',
    regionKey: 'Fes-Meknes',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-5.54727, 33.89352],
  },
  {
    id: 'kenitra',
    nameFr: 'Kénitra',
    nameAr: 'القنيطرة',
    regionFr: 'Rabat-Salé-Kénitra',
    regionAr: 'الرباط - سلا - القنيطرة',
    regionKey: 'Rabat-Sale-Kenitra',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-6.5802, 34.26101],
  },
  {
    id: 'sale',
    nameFr: 'Salé',
    nameAr: 'سلا',
    regionFr: 'Rabat-Salé-Kénitra',
    regionAr: 'الرباط - سلا - القنيطرة',
    regionKey: 'Rabat-Sale-Kenitra',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-6.79846, 34.0531],
  },
  {
    id: 'mohammedia',
    nameFr: 'Mohammedia',
    nameAr: 'المحمدية',
    regionFr: 'Casablanca-Settat',
    regionAr: 'الدار البيضاء - سطات',
    regionKey: 'Casablanca-Settat',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-7.38298, 33.68607],
  },
  {
    id: 'tetouan',
    nameFr: 'Tétouan',
    nameAr: 'تطوان',
    regionFr: 'Tanger-Tétouan-Al Hoceïma',
    regionAr: 'طنجة - تطوان - الحسيمة',
    regionKey: 'Tanger-Tetouan-Hoceima',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-5.36837, 35.57845],
  },
  {
    id: 'el-jadida',
    nameFr: 'El Jadida',
    nameAr: 'الجديدة',
    regionFr: 'Casablanca-Settat',
    regionAr: 'الدار البيضاء - سطات',
    regionKey: 'Casablanca-Settat',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-8.50882, 33.25682],
  },
  {
    id: 'temara',
    nameFr: 'Témara',
    nameAr: 'تمارة',
    regionFr: 'Rabat-Salé-Kénitra',
    regionAr: 'الرباط - سلا - القنيطرة',
    regionKey: 'Rabat-Sale-Kenitra',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-6.90656, 33.92866],
  },
  {
    id: 'essaouira',
    nameFr: 'Essaouira',
    nameAr: 'الصويرة',
    regionFr: 'Marrakech-Safi',
    regionAr: 'مراكش - آسفي',
    regionKey: 'Marrakech-Safi',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-9.77, 31.5125],
  },
  {
    id: 'oujda',
    nameFr: 'Oujda',
    nameAr: 'وجدة',
    regionFr: 'Oriental',
    regionAr: 'الشرق',
    regionKey: 'Oriental',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-1.90858, 34.68139],
  },
  {
    id: 'bouskoura',
    nameFr: 'Bouskoura',
    nameAr: 'بوسكورة',
    regionFr: 'Casablanca-Settat',
    regionAr: 'الدار البيضاء - سطات',
    regionKey: 'Casablanca-Settat',
    status: 'active',
    hasActiveModelCoverage: true,
    coordinates: [-7.65239, 33.44976],
  },
];

export const REGIONS_TRANSLATIONS: Record<string, { nameFr: string; nameAr: string }> = {
  'Tanger-Tetouan-Hoceima': {
    nameFr: 'Tanger-Tétouan-Al Hoceïma',
    nameAr: 'طنجة - تطوان - الحسيمة',
  },
  'Oriental': {
    nameFr: 'Oriental',
    nameAr: 'الشرق',
  },
  'Fes-Meknes': {
    nameFr: 'Fès-Meknès',
    nameAr: 'فاس - مكناس',
  },
  'Rabat-Sale-Kenitra': {
    nameFr: 'Rabat-Salé-Kénitra',
    nameAr: 'الرباط - سلا - القنيطرة',
  },
  'Beni Mellal-Khenifra': {
    nameFr: 'Béni Mellal-Khénifra',
    nameAr: 'بني ملال - خنيفرة',
  },
  'Casablanca-Settat': {
    nameFr: 'Casablanca-Settat',
    nameAr: 'الدار البيضاء - سطات',
  },
  'Marrakech-Safi': {
    nameFr: 'Marrakech-Safi',
    nameAr: 'مراكش - آسفي',
  },
  'Daraa-Tafilelt': {
    nameFr: 'Drâa-Tafilalet',
    nameAr: 'درعة - تافيلالت',
  },
  'Souss Massa': {
    nameFr: 'Souss-Massa',
    nameAr: 'سوس - ماسة',
  },
  'Guelmim-Oued Noun': {
    nameFr: 'Guelmim-Oued Noun',
    nameAr: 'كلميم - واد نون',
  },
  'Laayoune-Saguia Hamra': {
    nameFr: 'Laâyoune-Sakia El Hamra',
    nameAr: 'العيون - الساقية الحمراء',
  },
  'Dakhla-Oued Eddahab': {
    nameFr: 'Dakhla-Oued Ed-Dahab',
    nameAr: 'الداخلة - وادي الذهب',
  },
};
