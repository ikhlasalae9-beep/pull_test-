/**
 * Config-driven schema for the MaisonDeLUX property valuation engine.
 * Decoupled from the frontend UI so Alae's feature_schema.json can update fields cleanly.
 */

export type FieldType = 'number' | 'text' | 'select' | 'radio' | 'toggle';

export interface EstimatorOption {
  value: string;
  labelFr: string;
  labelAr: string;
  descriptionFr?: string;
  descriptionAr?: string;
  disabled?: boolean;
}

export interface EstimatorField {
  id: string;
  apiKey: string; // Key sent in API payload (e.g. 'Surface_m2')
  labelFr: string;
  labelAr: string;
  hintFr?: string;
  hintAr?: string;
  type: FieldType;
  step: 1 | 2 | 3;
  required: boolean;
  defaultValue?: any;
  placeholderFr?: string;
  placeholderAr?: string;
  min?: number;
  max?: number;
  stepValue?: number;
  unit?: string;
  options?: EstimatorOption[];
  allowUnknown?: boolean;
  unknownLabelFr?: string;
  unknownLabelAr?: string;
}

export interface EstimatorStepConfig {
  step: 1 | 2 | 3 | 4 | 5;
  titleFr: string;
  titleAr: string;
  subtitleFr: string;
  subtitleAr: string;
}

export const ESTIMATOR_STEPS: EstimatorStepConfig[] = [
  {
    step: 1,
    titleFr: 'Localisation',
    titleAr: 'الموقع الجغرافي',
    subtitleFr: 'Définissez la ville et le secteur géographique du bien',
    subtitleAr: 'حدد المدينة والمنطقة الجغرافية للعقار',
  },
  {
    step: 2,
    titleFr: 'Typologie du Bien',
    titleAr: 'نوع العقار',
    subtitleFr: 'Périmètre actuel de valorisation : Vente d\'appartements résidentiels',
    subtitleAr: 'نطاق التقييم الحالي: بيع الشقق السكنية',
  },
  {
    step: 3,
    titleFr: 'Caractéristiques',
    titleAr: 'المواصفات الهندسية',
    subtitleFr: 'Précisez la surface habitable et la distribution intérieure',
    subtitleAr: 'حدد المساحة السكنية والتوزيع الداخلي للغرف',
  },
  {
    step: 4,
    titleFr: 'Vérification',
    titleAr: 'مراجعة المعطيات',
    subtitleFr: 'Contrôlez les paramètres saisis avant transmission au moteur',
    subtitleAr: 'تحقق من البيانات المدخلة قبل الإرسال لمحرك التقييم',
  },
  {
    step: 5,
    titleFr: 'Résultat d\'Évaluation',
    titleAr: 'نتيجة التقييم',
    subtitleFr: 'Traitement prédictif et état de connexion du modèle',
    subtitleAr: 'المعالجة التنبؤية وحالة الاتصال بالنموذج',
  },
];

/**
 * Verified scope configuration:
 * Only 'appartement' for 'sale' is currently trained in clean data.
 * Other property types are explicitly marked as upcoming / out of current scope.
 */
export const PROPERTY_TYPES_CONFIG: EstimatorOption[] = [
  {
    value: 'appartement',
    labelFr: 'Appartement',
    labelAr: 'شقة',
    descriptionFr: 'Périmètre actuellement couvert par les données de modélisation.',
    descriptionAr: 'النطاق المدعوم حالياً ببيانات النمذجة المعتمدة.',
    disabled: false,
  },
  {
    value: 'villa',
    labelFr: 'Villa',
    labelAr: 'فيلا',
    descriptionFr: 'Modélisation en cours d\'enrichissement — indisponible pour le moment.',
    descriptionAr: 'قيد التطوير المعرفي — غير متاح حالياً.',
    disabled: true,
  },
  {
    value: 'duplex',
    labelFr: 'Duplex',
    labelAr: 'دوبلكس',
    descriptionFr: 'Modélisation en cours d\'enrichissement — indisponible pour le moment.',
    descriptionAr: 'قيد التطوير المعرفي — غير متاح حالياً.',
    disabled: true,
  },
  {
    value: 'studio',
    labelFr: 'Studio',
    labelAr: 'استوديو',
    descriptionFr: 'Modélisation en cours d\'enrichissement — indisponible pour le moment.',
    descriptionAr: 'قيد التطوير المعرفي — غير متاح حالياً.',
    disabled: true,
  },
];

export const ESTIMATOR_FIELDS: EstimatorField[] = [
  // Step 1: Localisation
  {
    id: 'ville',
    apiKey: 'ville',
    labelFr: 'Ville',
    labelAr: 'المدينة',
    hintFr: 'Sélectionnez une agglomération couverte par le référentiel de données.',
    hintAr: 'اختر مدينة مدرجة في السجل المعتمد للبيانات.',
    type: 'select',
    step: 1,
    required: true,
    defaultValue: 'Casablanca',
  },
  {
    id: 'quartier',
    apiKey: 'quartier',
    labelFr: 'Quartier ou Secteur',
    labelAr: 'الحي أو المنطقة',
    placeholderFr: 'Ex : Guéliz, Maârif, Agdal, Malabata...',
    placeholderAr: 'مثال: المعاريف، جيليز، أكدال، مالاباطا...',
    hintFr: 'Sélectionnez un quartier de la ville ou Autre.',
    hintAr: 'أدخل اسم الحي بدقة أو اتركه فارغاً إذا لم يكن محدداً.',
    type: 'select',
    step: 1,
    required: false,
    defaultValue: '',
    allowUnknown: true,
    unknownLabelFr: 'Quartier non renseigné',
    unknownLabelAr: 'الحي غير محدد',
  },

  // Step 2: Property Type
  {
    id: 'type_bien',
    apiKey: 'type_bien',
    labelFr: 'Typologie du bien',
    labelAr: 'نوع العقار',
    type: 'radio',
    step: 2,
    required: true,
    defaultValue: 'appartement',
    options: PROPERTY_TYPES_CONFIG,
  },

  // Step 3: Features
  {
    id: 'surface',
    apiKey: 'surface',
    labelFr: 'Surface habitable',
    labelAr: 'المساحة السكنية',
    hintFr: 'Surface nette en mètres carrés (m²).',
    hintAr: 'المساحة الصافية بالأمتار المربعة (م²).',
    type: 'number',
    step: 3,
    required: true,
    defaultValue: 85,
    min: 0.01,
    stepValue: 0.01,
    unit: 'm²',
  },
  {
    id: 'chambres',
    apiKey: 'chambres',
    labelFr: 'Chambres à coucher',
    labelAr: 'غرف النوم',
    type: 'number',
    step: 3,
    required: true,
    defaultValue: 2,
    min: 1,
    max: 10,
    allowUnknown: true,
  },
  {
    id: 'salles_bain',
    apiKey: 'salles_bain',
    labelFr: 'Salles de bain',
    labelAr: 'حمامات',
    type: 'number',
    step: 3,
    required: false,
    defaultValue: 1,
    min: 1,
    max: 6,
    allowUnknown: true,
  },
  { id: 'parking', apiKey: 'parking', labelFr: 'Parking', labelAr: 'موقف سيارات', type: 'select', step: 3, required: false, defaultValue: 'unknown', options: [
    { value: 'unknown', labelFr: 'Non renseigné', labelAr: 'غير محدد' },
    { value: 'yes', labelFr: 'Oui', labelAr: 'نعم' },
    { value: 'no', labelFr: 'Non', labelAr: 'لا' },
  ] },
  { id: 'balcony', apiKey: 'balcony', labelFr: 'Balcon', labelAr: 'شرفة', type: 'select', step: 3, required: false, defaultValue: 'unknown', options: [
    { value: 'unknown', labelFr: 'Non renseigné', labelAr: 'غير محدد' },
    { value: 'yes', labelFr: 'Oui', labelAr: 'نعم' },
    { value: 'no', labelFr: 'Non', labelAr: 'لا' },
  ] },
  { id: 'sea_view', apiKey: 'sea_view', labelFr: 'Vue sur mer', labelAr: 'إطلالة بحرية', type: 'select', step: 3, required: false, defaultValue: 'unknown', options: [
    { value: 'unknown', labelFr: 'Non renseigné', labelAr: 'غير محدد' },
    { value: 'yes', labelFr: 'Oui', labelAr: 'نعم' },
    { value: 'no', labelFr: 'Non', labelAr: 'لا' },
  ] },
  { id: 'furnished_status', apiKey: 'furnished_status', labelFr: 'Ameublement', labelAr: 'التأثيث', type: 'select', step: 3, required: false, defaultValue: 'unknown', options: [
    { value: 'unknown', labelFr: 'Non renseigné', labelAr: 'غير محدد' },
    { value: 'furnished', labelFr: 'Oui', labelAr: 'نعم' },
    { value: 'unfurnished', labelFr: 'Non', labelAr: 'لا' },
  ] },
];
