import { getSurgeAlerts, getSurgeHistory, getObservedDemand, getDistrictForecast, CURRENT_MONTH } from './mockData';
import type { SurgeAlert } from './types';
import { apiGet, mockDelay } from './api';

// GET /api/surge-alerts
export async function getSurgeAlertsData(): Promise<SurgeAlert[]> {
  try {
    return await apiGet<SurgeAlert[]>('/api/surge-alerts');
  } catch (err) {
    console.warn('Surge alerts API failed, falling back to mock:', err);
    return mockDelay(getSurgeAlerts());
  }
}

// GET /api/surge-alerts/:districtId/history
export async function getSurgeHistoryData(districtId: string) {
  try {
    return await apiGet<any[]>(`/api/surge-alerts/${encodeURIComponent(districtId)}/history`);
  } catch (err) {
    console.warn(`Surge history API failed for ${districtId}, falling back to mock:`, err);
    return mockDelay(getSurgeHistory(districtId));
  }
}

// GET /api/surge-residuals/:districtId
export async function getResidualData(districtId: string) {
  try {
    return await apiGet<any>(`/api/surge-residuals/${encodeURIComponent(districtId)}`);
  } catch (err) {
    console.warn(`Surge residual API failed for ${districtId}, falling back to mock:`, err);
    const fc = getDistrictForecast(districtId);
    const history = fc.history.slice(-12);
    const observed = getObservedDemand(districtId, CURRENT_MONTH);
    return mockDelay({
      history: history.map((h) => ({
        month: h.month,
        actual: h.actual,
        forecast: h.forecast,
        residual: h.residual,
      })),
      currentObserved: observed,
      currentForecast: fc.currentForecast,
      currentResidual: observed - fc.currentForecast,
    });
  }
}
