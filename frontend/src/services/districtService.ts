import { DISTRICTS, getDistrictDetail, getDistrictForecast, getAllForecasts } from './mockData';
import type { District, DistrictForecast } from './types';
import { apiGet, mockDelay } from './api';

// GET /api/districts
export async function getDistricts(): Promise<District[]> {
  try {
    return await apiGet<District[]>('/api/districts');
  } catch (err) {
    console.warn('Districts API call failed, falling back to mock:', err);
    return mockDelay(DISTRICTS);
  }
}

// GET /api/districts/:id
export async function getDistrict(id: string): Promise<District | null> {
  try {
    return await apiGet<District>(`/api/districts/${encodeURIComponent(id)}`);
  } catch (err) {
    console.warn(`District API call failed for ${id}, falling back to mock:`, err);
    return mockDelay(DISTRICTS.find((d) => d.id === id) ?? null);
  }
}

// GET /api/districts/:id/forecast
export async function getDistrictForecastData(id: string): Promise<DistrictForecast | null> {
  try {
    return await apiGet<DistrictForecast>(`/api/forecasts/${encodeURIComponent(id)}`);
  } catch (err) {
    console.warn(`District forecast API failed for ${id}, falling back to mock:`, err);
    return mockDelay(getDistrictForecast(id));
  }
}

// GET /api/forecasts
export async function getAllDistrictForecasts(): Promise<DistrictForecast[]> {
  try {
    return await apiGet<DistrictForecast[]>('/api/forecasts');
  } catch (err) {
    console.warn('Forecasts API failed, falling back to mock:', err);
    return mockDelay(getAllForecasts());
  }
}

// GET /api/districts/:id/detail
export async function getDistrictDetailData(id: string) {
  try {
    return await apiGet<any>(`/api/districts/${encodeURIComponent(id)}/detail`);
  } catch (err) {
    console.warn(`District detail API failed for ${id}, falling back to mock:`, err);
    return mockDelay(getDistrictDetail(id));
  }
}
