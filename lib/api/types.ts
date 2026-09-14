export interface PredictPayload {
  surface_m2: number;
  bedrooms?: number | null;
  bathrooms?: number | null;
  region: string;
  city: string;
  neighborhood?: string;
  property_type: string;
  parking?: string;
  balcony?: string;
  sea_view?: string;
  furnished_status?: string;
}

export interface PredictResponse {
  estimated_price_mad: number;
  prix_min?: number;
  prix_max?: number;
  prix_par_m2?: number;
  ville?: string;
  quartier?: string;
  error?: string;
  model_version?: string;
}

export interface CitiesResponse {
  villes: string[];
}

export interface ApiStatusCheck {
  isAvailable: boolean;
  modelVersion?: string;
  message?: string;
}
