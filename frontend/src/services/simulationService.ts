import { getSimulationResults } from './mockData';
import type { SimulationScenario, SimulationResult } from './types';
import { apiPost, mockDelay } from './api';

// POST /api/simulation { scenario }
export async function runSimulation(scenario: SimulationScenario): Promise<SimulationResult[]> {
  try {
    return await apiPost<SimulationResult[]>('/api/simulation', { scenario });
  } catch (err) {
    console.warn(`Simulation API failed for ${scenario}, falling back to mock:`, err);
    return mockDelay(getSimulationResults(scenario), 200);
  }
}
