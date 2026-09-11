// ── Core domain types for SurgeShield ──────────────────────────────

export type RiskLevel = 'Low' | 'Medium' | 'High' | 'Critical';

export type AllocationPolicy =
  | 'Equal Split'
  | 'Forecast Only'
  | 'Risk Based'
  | 'Fairness Aware'
  | 'Surge Adaptive';

export type SimulationScenario =
  | 'Baseline'
  | 'Seasonal Peak'
  | 'Demand Growth'
  | 'Sudden Surge';

export type SurgeStage =
  | 'Normal'
  | 'Elevated'
  | 'Anomaly'
  | 'Confirmed Surge'
  | 'Response';

export interface District {
  id: string;
  name: string;
  region: string;
  population: number;
  nominalCapacity: number;
  baseDemand: number;
  trend: number;       // monthly trend slope
  seasonalityAmplitude: number;
  uncertainty: number; // std dev of noise
}

export interface DemandPoint {
  districtId: string;
  month: number;
  actual: number;
  forecast: number;
  capacity: number;
  reserve: number;
  residual: number;
}

export interface DistrictForecast {
  districtId: string;
  currentForecast: number;
  trend: number;
  seasonality: number;
  uncertainty: number;
  risk: RiskLevel;
  history: DemandPoint[];
  future: { month: number; forecast: number; lower: number; upper: number }[];
}

export interface Allocation {
  districtId: string;
  reserve: number;
  reason: string;
  expectedBenefit: 'Low' | 'Medium' | 'High';
  factors: {
    shortageRisk: number;
    demandGap: number;
    surgeSignal: number;
    fairnessPriority: number;
  };
}

export interface AllocationResult {
  policy: AllocationPolicy;
  totalReserve: number;
  allocations: Allocation[];
  totalUnmetDemand: number;
  serviceUtility: number;
  worstDistrictService: number;
  reserveUtilization: number;
}

export interface SurgeAlert {
  districtId: string;
  stage: SurgeStage;
  risk: RiskLevel;
  expectedDemand: number;
  observedDemand: number;
  deviation: number;
  confidence: 'Low' | 'Medium' | 'High';
  recommendedResponse: string;
  timestamp: string;
}

export interface PerformanceMetrics {
  forecastUtility: number | null;
  demandServiceUtility: number | null;
  worstDistrictService: number | null;
  compliance: {
    reserveConstraint: boolean;
    integerAllocations: boolean;
    noFutureLeakage: boolean;
    reproducibleConfig: boolean;
  };
  districtService: { districtId: string; service: number }[];
  unmetDemandTimeline: { month: number; demand: number; capacity: number; reserve: number; unmet: number }[];
}

export interface SimulationResult {
  policy: AllocationPolicy;
  totalUnmetDemand: number;
  serviceUtility: number;
  worstDistrictService: number;
  reserveUtilization: number;
  districtAllocations: { districtId: string; allocation: number; unmetDemand: number }[];
}

export interface KPIData {
  districts: number;
  reserveUnits: number;
  currentMonth: number;
  totalForecastDemand: number;
  totalAvailableCapacity: number;
  expectedShortage: number;
  reserveUtilization: number;
}
