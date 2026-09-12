import { getPerformanceMetrics } from './mockData';
import type { PerformanceMetrics } from './types';
import { apiGet, mockDelay } from './api';

// GET /api/performance
export async function getPerformanceData(): Promise<PerformanceMetrics> {
  try {
    return await apiGet<PerformanceMetrics>('/api/performance');
  } catch (err) {
    console.warn('Performance API failed, falling back to mock:', err);
    return mockDelay(getPerformanceMetrics());
  }
}
