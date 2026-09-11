import { getAllForecasts, getDistrictForecast } from './mockData';
import type { DistrictForecast } from './types';
import { mockDelay } from './api';

// GET /api/forecasts
export async function getForecasts(): Promise<DistrictForecast[]> {
  return mockDelay(getAllForecasts());
}

// GET /api/forecasts/:districtId
export async function getForecast(districtId: string): Promise<DistrictForecast | null> {
  return mockDelay(getDistrictForecast(districtId));
}
