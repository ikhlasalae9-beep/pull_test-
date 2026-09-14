export interface EstimatorFormData {
  ville: string;
  quartier: string;
  type_bien: string;
  surface: number;
  chambres: number;
  salles_bain: number;
  [key: string]: any;
}

export interface EstimationApiResponse {
  prix_estime?: number;
  prix_min?: number;
  prix_max?: number;
  prix_par_m2?: number;
  ville?: string;
  quartier?: string;
  error?: string;
  model_version?: string;
}

export interface BackendModelMetadata {
  model_version?: string;
  created_on?: string;
  currency?: string;
  description?: string;
  cities?: string[];
  [key: string]: any;
}

export type EstimationStatus = 
  | 'idle'
  | 'submitting'
  | 'success'
  | 'offline_waiting'
  | 'error';
