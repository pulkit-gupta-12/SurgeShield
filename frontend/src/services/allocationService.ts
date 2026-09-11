import { getAllocation } from './mockData';
import type { AllocationPolicy, AllocationResult } from './types';
import { mockDelay } from './api';

// GET /api/allocations?policy=Surge Adaptive
export async function getAllocationResult(policy: AllocationPolicy): Promise<AllocationResult> {
  return mockDelay(getAllocation(policy));
}
