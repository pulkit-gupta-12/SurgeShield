import { DISTRICTS, getDistrictDetail, getDistrictForecast, getAllForecasts } from './mockData';
import type { District, DistrictForecast } from './types';
import { mockDelay } from './api';

// GET /api/districts
export async function getDistricts(): Promise<District[]> {
  return mockDelay(DISTRICTS);
}

// GET /api/districts/:id
export async function getDistrict(id: string): Promise<District | null> {
  return mockDelay(DISTRICTS.find((d) => d.id === id) ?? null);
}

// GET /api/districts/:id/forecast
export async function getDistrictForecastData(id: string): Promise<DistrictForecast | null> {
  return mockDelay(getDistrictForecast(id));
}

// GET /api/forecasts
export async function getAllDistrictForecasts(): Promise<DistrictForecast[]> {
  return mockDelay(getAllForecasts());
}

// GET /api/districts/:id/detail
export async function getDistrictDetailData(id: string) {
  return mockDelay(getDistrictDetail(id));
}
