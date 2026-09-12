import { getAllocation } from './mockData';
import type { AllocationPolicy, AllocationResult } from './types';
import { apiGet, mockDelay } from './api';

// GET /api/allocations?policy=Surge Adaptive
export async function getAllocationResult(policy: AllocationPolicy): Promise<AllocationResult> {
  try {
    return await apiGet<AllocationResult>(`/api/allocations?policy=${encodeURIComponent(policy)}`);
  } catch (err) {
    console.warn(`Allocation API failed for ${policy}, falling back to mock:`, err);
    return mockDelay(getAllocation(policy));
  }
}
