import { getSurgeAlerts, getSurgeHistory, getObservedDemand, getDistrictForecast, CURRENT_MONTH } from './mockData';
import type { SurgeAlert } from './types';
import { mockDelay } from './api';

// GET /api/surge-alerts
export async function getSurgeAlertsData(): Promise<SurgeAlert[]> {
  return mockDelay(getSurgeAlerts());
}

// GET /api/surge-alerts/:districtId/history
export async function getSurgeHistoryData(districtId: string) {
  return mockDelay(getSurgeHistory(districtId));
}

// GET /api/surge-residuals/:districtId
export async function getResidualData(districtId: string) {
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
