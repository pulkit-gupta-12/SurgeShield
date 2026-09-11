import { getSimulationResults } from './mockData';
import type { SimulationScenario, SimulationResult } from './types';
import { mockDelay } from './api';

// POST /api/simulation { scenario }
export async function runSimulation(scenario: SimulationScenario): Promise<SimulationResult[]> {
  return mockDelay(getSimulationResults(scenario), 200);
}
