import { getPerformanceMetrics } from './mockData';
import type { PerformanceMetrics } from './types';
import { mockDelay } from './api';

// GET /api/performance
export async function getPerformanceData(): Promise<PerformanceMetrics> {
  return mockDelay(getPerformanceMetrics());
}
