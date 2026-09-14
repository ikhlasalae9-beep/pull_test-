import { PredictPayload, PredictResponse, CitiesResponse } from './types';


/**
 * Client for the MaisonDeLUX ML valuation backend.
 * Adheres strictly to the no-fake-data policy:
 * If the service is unreachable or offline, it reports service unavailability.
 * Never fabricates property prices.
 */
export async function predictProperty(
  payload: PredictPayload
): Promise<{ data?: PredictResponse; error?: string; isOffline?: boolean }> {
  let timeoutId: ReturnType<typeof setTimeout> | undefined;
  try {
    const controller = new AbortController();
    timeoutId = setTimeout(() => controller.abort(), 8000); // 8-second safety timeout

    const res = await fetch('/api/estimate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      return {
        error: errorData.error || `Erreur serveur (${res.status})`,
      };
    }

    const data: PredictResponse = await res.json();
    if (!Number.isFinite(data.estimated_price_mad) || data.estimated_price_mad <= 0) return { error: 'Réponse invalide du service.' };
    return { data };
  } catch (err: any) {
    // Connection refused, network error, or timeout
    return {
      isOffline: true,
      error: 'Le moteur d\'estimation est actuellement en cours de connexion.',
    };
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Fetch dynamic model metadata from the backend if available.
 * Returns null if the backend is not currently connected.
 */
export async function fetchModelMetadata(): Promise<{ model_version?: string; currency?: string } | null> {
  try {
    const res = await fetch('/api/metrics', {
      method: 'GET',
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    const data = await res.json();
    return {
      model_version: data.model_version,
      currency: data.currency,
    };
  } catch {
    return null;
  }
}

/**
 * Fetch available cities from backend if online, otherwise null.
 */
export async function fetchApiCities(): Promise<string[] | null> {
  try {
    const res = await fetch('/api/villes', {
      method: 'GET',
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    const data: CitiesResponse = await res.json();
    return data.villes || null;
  } catch {
    return null;
  }
}
