import { getAllForecasts, getDistrictForecast } from './mockData';
import type { DistrictForecast } from './types';
import { apiGet, API_BASE_URL, mockDelay } from './api';

// GET /api/forecasts
export async function getForecasts(model: string = 'harmonic_regression'): Promise<DistrictForecast[]> {
  if (API_BASE_URL) {
    try {
      return await apiGet<DistrictForecast[]>(`/api/forecasts?model=${encodeURIComponent(model)}`);
    } catch (err) {
      console.warn('API call failed, falling back to mock forecasts:', err);
    }
  }
  return mockDelay(getAllForecasts());
}

// GET /api/forecasts/:districtId
export async function getForecast(districtId: string, model: string = 'harmonic_regression'): Promise<DistrictForecast | null> {
  if (API_BASE_URL) {
    try {
      return await apiGet<DistrictForecast>(`/api/forecasts/${encodeURIComponent(districtId)}?model=${encodeURIComponent(model)}`);
    } catch (err) {
      console.warn(`API call failed for ${districtId}, falling back to mock data:`, err);
    }
  }
  return mockDelay(getDistrictForecast(districtId));
}
