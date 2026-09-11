// ── Centralized deterministic mock data for SurgeShield ──────────────
// All values are DEMO / SIMULATION data — not validated model results.
// Replace mockXxx functions with FastAPI calls later without touching the UI.

import type {
  District,
  DemandPoint,
  DistrictForecast,
  AllocationResult,
  SurgeAlert,
  PerformanceMetrics,
  SimulationResult,
  AllocationPolicy,
  SimulationScenario,
  RiskLevel,
  KPIData,
  Allocation,
} from './types';

// ── Deterministic pseudo-random (seeded) ────────────────────────────
function seededRandom(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

// ── 12 Districts with HC-05-style parameters ────────────────────────
export const DISTRICTS: District[] = [
  { id: 'D0',  name: 'Northgate',   region: 'North',    population: 320000, nominalCapacity: 108, baseDemand: 105, trend: 0.4, seasonalityAmplitude: 12, uncertainty: 5 },
  { id: 'D1',  name: 'Riverside',  region: 'South',    population: 280000, nominalCapacity: 88,  baseDemand: 85,  trend: 0.2, seasonalityAmplitude: 8,  uncertainty: 4 },
  { id: 'D2',  name: 'Eastfield',  region: 'East',     population: 410000, nominalCapacity: 108, baseDemand: 115, trend: 0.9, seasonalityAmplitude: 15, uncertainty: 7 },
  { id: 'D3',  name: 'Westport',   region: 'West',     population: 250000, nominalCapacity: 95,  baseDemand: 90,  trend: 0.3, seasonalityAmplitude: 10, uncertainty: 4 },
  { id: 'D4',  name: 'Central',    region: 'Central',  population: 360000, nominalCapacity: 100, baseDemand: 98,  trend: 0.5, seasonalityAmplitude: 11, uncertainty: 5 },
  { id: 'D5',  name: 'Highland',   region: 'North',    population: 290000, nominalCapacity: 109, baseDemand: 102, trend: 0.6, seasonalityAmplitude: 13, uncertainty: 6 },
  { id: 'D6',  name: 'Bayview',    region: 'South',    population: 310000, nominalCapacity: 92,  baseDemand: 88,  trend: 0.1, seasonalityAmplitude: 9,  uncertainty: 4 },
  { id: 'D7',  name: 'Pinecrest',  region: 'East',     population: 270000, nominalCapacity: 85,  baseDemand: 80,  trend: 0.2, seasonalityAmplitude: 7,  uncertainty: 3 },
  { id: 'D8',  name: 'Lakeside',  region: 'West',     population: 340000, nominalCapacity: 110, baseDemand: 104, trend: 0.4, seasonalityAmplitude: 12, uncertainty: 5 },
  { id: 'D9',  name: 'Southgate',  region: 'South',    population: 390000, nominalCapacity: 115, baseDemand: 120, trend: 0.8, seasonalityAmplitude: 14, uncertainty: 6 },
  { id: 'D10', name: 'Fairmont',   region: 'Central',  population: 260000, nominalCapacity: 90,  baseDemand: 86,  trend: 0.3, seasonalityAmplitude: 10, uncertainty: 4 },
  { id: 'D11', name: 'Cliffside',  region: 'East',     population: 300000, nominalCapacity: 98,  baseDemand: 94,  trend: 0.5, seasonalityAmplitude: 11, uncertainty: 5 },
];

export const RESERVE_CAPACITY = 60;
export const HISTORICAL_MONTHS = 36; // t=0..35
export const FORECAST_MONTHS = 6;   // t=36..41
export const CURRENT_MONTH = 36;

// ── Seasonal component ──────────────────────────────────────────────
function seasonal(month: number, amplitude: number): number {
  return amplitude * Math.sin((2 * Math.PI * (month % 12)) / 12);
}

// ── Generate historical demand for a district ───────────────────────
function generateHistory(d: District): DemandPoint[] {
  const rand = seededRandom(d.id.charCodeAt(1) * 1000);
  const points: DemandPoint[] = [];
  for (let t = 0; t < HISTORICAL_MONTHS; t++) {
    const trendComponent = d.trend * t;
    const seasonalComponent = seasonal(t, d.seasonalityAmplitude);
    const noise = (rand() - 0.5) * 2 * d.uncertainty;
    const actual = Math.max(0, Math.round(d.baseDemand + trendComponent + seasonalComponent + noise));
    const forecast = Math.round(d.baseDemand + trendComponent + seasonalComponent);
    const capacity = d.nominalCapacity;
    const reserve = 0;
    const residual = actual - forecast;
    points.push({ districtId: d.id, month: t, actual, forecast, capacity, reserve, residual });
  }
  return points;
}

// ── Generate future forecast for a district ─────────────────────────
function generateFuture(d: District): DistrictForecast['future'] {
  const future: DistrictForecast['future'] = [];
  for (let t = HISTORICAL_MONTHS; t < HISTORICAL_MONTHS + FORECAST_MONTHS; t++) {
    const trendComponent = d.trend * t;
    const seasonalComponent = seasonal(t, d.seasonalityAmplitude);
    const forecast = Math.round(d.baseDemand + trendComponent + seasonalComponent);
    const margin = Math.round(d.uncertainty * 2);
    future.push({ month: t, forecast, lower: forecast - margin, upper: forecast + margin });
  }
  return future;
}

// ── Risk classification ─────────────────────────────────────────────
function classifyRisk(forecast: number, capacity: number): RiskLevel {
  const gap = forecast - capacity;
  if (gap >= 30) return 'Critical';
  if (gap >= 15) return 'High';
  if (gap >= 5) return 'Medium';
  return 'Low';
}

// ── Forecast per district ──────────────────────────────────────────
const _forecastCache: Record<string, DistrictForecast> = {};

export function getDistrictForecast(districtId: string): DistrictForecast {
  if (_forecastCache[districtId]) return _forecastCache[districtId];
  const d = DISTRICTS.find((x) => x.id === districtId)!;
  const history = generateHistory(d);
  const future = generateFuture(d);
  const currentForecast = future[0].forecast;
  const lastHistory = history[history.length - 1];
  const risk = classifyRisk(currentForecast, d.nominalCapacity);
  const fc: DistrictForecast = {
    districtId,
    currentForecast,
    trend: d.trend,
    seasonality: d.seasonalityAmplitude,
    uncertainty: d.uncertainty,
    risk,
    history,
    future,
  };
  _forecastCache[districtId] = fc;
  return fc;
}

export function getAllForecasts(): DistrictForecast[] {
  return DISTRICTS.map((d) => getDistrictForecast(d.id));
}

// ── Surge scenario: D2 and D9 have +35 surge at month 36 ────────────
const SURGE_DISTRICTS = ['D2', 'D9'];
const SURGE_MAGNITUDE = 35;

export function getObservedDemand(districtId: string, month: number): number {
  const fc = getDistrictForecast(districtId);
  if (month >= HISTORICAL_MONTHS && SURGE_DISTRICTS.includes(districtId)) {
    return fc.future[month - HISTORICAL_MONTHS].forecast + SURGE_MAGNITUDE;
  }
  if (month >= HISTORICAL_MONTHS) {
    return fc.future[month - HISTORICAL_MONTHS].forecast;
  }
  return fc.history[month]?.actual ?? fc.currentForecast;
}

// ── Allocation logic (mock, deterministic) ──────────────────────────
const ALLOCATION_REASONS: Record<string, string> = {
  Critical: 'High shortage probability',
  High: 'Surge signal detected',
  Medium: 'Persistent demand pressure',
  Low: 'Low shortage risk',
};

function riskWeight(risk: RiskLevel): number {
  switch (risk) {
    case 'Critical': return 4;
    case 'High': return 3;
    case 'Medium': return 2;
    case 'Low': return 1;
  }
}

export function getAllocation(policy: AllocationPolicy): AllocationResult {
  const forecasts = getAllForecasts();
  let allocations: Allocation[] = [];

  switch (policy) {
    case 'Equal Split': {
      const per = RESERVE_CAPACITY / DISTRICTS.length;
      allocations = DISTRICTS.map((d) => {
        const fc = getDistrictForecast(d.id);
        return {
          districtId: d.id,
          reserve: per,
          reason: 'Equal distribution',
          expectedBenefit: fc.risk === 'Low' ? 'Low' : fc.risk === 'Medium' ? 'Medium' : 'High',
          factors: {
            shortageRisk: riskWeight(fc.risk) / 4,
            demandGap: Math.max(0, fc.currentForecast - d.nominalCapacity) / 40,
            surgeSignal: SURGE_DISTRICTS.includes(d.id) ? 1 : 0,
            fairnessPriority: 0.5,
          },
        };
      });
      break;
    }
    case 'Forecast Only': {
      const totalGap = forecasts.reduce((sum, f) => sum + Math.max(0, f.currentForecast - DISTRICTS.find((d) => d.id === f.districtId)!.nominalCapacity), 0);
      allocations = DISTRICTS.map((d) => {
        const fc = getDistrictForecast(d.id);
        const gap = Math.max(0, fc.currentForecast - d.nominalCapacity);
        const reserve = totalGap > 0 ? (gap / totalGap) * RESERVE_CAPACITY : 0;
        return {
          districtId: d.id,
          reserve,
          reason: gap > 0 ? 'Demand gap proportional' : 'No gap detected',
          expectedBenefit: gap > 20 ? 'High' : gap > 10 ? 'Medium' : 'Low',
          factors: {
            shortageRisk: riskWeight(fc.risk) / 4,
            demandGap: gap / 40,
            surgeSignal: 0,
            fairnessPriority: 0,
          },
        };
      });
      break;
    }
    case 'Risk Based':
    case 'Fairness Aware':
    case 'Surge Adaptive': {
      const weights = DISTRICTS.map((d) => {
        const fc = getDistrictForecast(d.id);
        const gap = Math.max(0, fc.currentForecast - d.nominalCapacity);
        let w = riskWeight(fc.risk) * gap;
        if (policy === 'Surge Adaptive' && SURGE_DISTRICTS.includes(d.id)) {
          w *= 1.8;
        }
        if (policy === 'Fairness Aware') {
          w = w * 0.7 + gap * 0.3;
        }
        return { districtId: d.id, weight: w, fc, gap };
      });
      const totalWeight = weights.reduce((s, w) => s + w.weight, 0) || 1;
      allocations = weights.map((w) => ({
        districtId: w.districtId,
        reserve: (w.weight / totalWeight) * RESERVE_CAPACITY,
        reason: ALLOCATION_REASONS[w.fc.risk] || 'Risk-based allocation',
        expectedBenefit: w.fc.risk === 'Critical' || w.fc.risk === 'High' ? 'High' : w.fc.risk === 'Medium' ? 'Medium' : 'Low',
        factors: {
          shortageRisk: riskWeight(w.fc.risk) / 4,
          demandGap: w.gap / 40,
          surgeSignal: SURGE_DISTRICTS.includes(w.districtId) ? 1 : 0,
          fairnessPriority: policy === 'Fairness Aware' ? 0.8 : 0.4,
        },
      }));
      break;
    }
  }

  // Round to integers while preserving total
  const rawAllocations = allocations.map((a) => ({ ...a, reserve: a.reserve }));
  let allocated = rawAllocations.map((a) => Math.floor(a.reserve));
  let remainder = RESERVE_CAPACITY - allocated.reduce((s, v) => s + v, 0);
  // Distribute remainder to highest-risk districts
  const order = rawAllocations
    .map((a, i) => ({ i, risk: riskWeight(getDistrictForecast(a.districtId).risk) }))
    .sort((a, b) => b.risk - a.risk);
  for (let i = 0; i < remainder && i < order.length; i++) {
    allocated[order[i].i] += 1;
  }

  const finalAllocations = rawAllocations.map((a, i) => ({ ...a, reserve: allocated[i] }));

  // Compute mock outcomes
  const totalUnmetDemand = computeUnmetDemand(finalAllocations);
  const serviceUtility = computeServiceUtility(finalAllocations);
  const worstDistrictService = computeWorstDistrictService(finalAllocations);

  return {
    policy,
    totalReserve: RESERVE_CAPACITY,
    allocations: finalAllocations,
    totalUnmetDemand,
    serviceUtility,
    worstDistrictService,
    reserveUtilization: 1.0,
  };
}

function computeUnmetDemand(allocations: Allocation[]): number {
  return allocations.reduce((sum, a) => {
    const d = DISTRICTS.find((x) => x.id === a.districtId)!;
    const observed = getObservedDemand(a.districtId, CURRENT_MONTH);
    const effectiveCapacity = d.nominalCapacity + a.reserve;
    return sum + Math.max(0, observed - effectiveCapacity);
  }, 0);
}

function computeServiceUtility(allocations: Allocation[]): number {
  const totalDemand = allocations.reduce((sum, a) => sum + getObservedDemand(a.districtId, CURRENT_MONTH), 0);
  const totalUnmet = computeUnmetDemand(allocations);
  return totalDemand > 0 ? 1 - totalUnmet / totalDemand : 1;
}

function computeWorstDistrictService(allocations: Allocation[]): number {
  let worst = 1;
  for (const a of allocations) {
    const d = DISTRICTS.find((x) => x.id === a.districtId)!;
    const observed = getObservedDemand(a.districtId, CURRENT_MONTH);
    const effectiveCapacity = d.nominalCapacity + a.reserve;
    const service = observed > 0 ? Math.min(1, effectiveCapacity / observed) : 1;
    if (service < worst) worst = service;
  }
  return worst;
}

// ── Surge alerts ────────────────────────────────────────────────────
export function getSurgeAlerts(): SurgeAlert[] {
  const alerts: SurgeAlert[] = [];
  for (const d of DISTRICTS) {
    const fc = getDistrictForecast(d.id);
    if (SURGE_DISTRICTS.includes(d.id)) {
      const expected = fc.currentForecast;
      const observed = expected + SURGE_MAGNITUDE;
      alerts.push({
        districtId: d.id,
        stage: 'Confirmed Surge',
        risk: fc.risk,
        expectedDemand: expected,
        observedDemand: observed,
        deviation: SURGE_MAGNITUDE,
        confidence: 'High',
        recommendedResponse: 'Increase reserve priority immediately',
        timestamp: `Month ${CURRENT_MONTH}`,
      });
    } else if (fc.risk === 'High' || fc.risk === 'Critical') {
      alerts.push({
        districtId: d.id,
        stage: 'Elevated',
        risk: fc.risk,
        expectedDemand: fc.currentForecast,
        observedDemand: fc.currentForecast + 2,
        deviation: 2,
        confidence: 'Medium',
        recommendedResponse: 'Monitor closely',
        timestamp: `Month ${CURRENT_MONTH}`,
      });
    } else if (fc.risk === 'Medium') {
      alerts.push({
        districtId: d.id,
        stage: 'Normal',
        risk: fc.risk,
        expectedDemand: fc.currentForecast,
        observedDemand: fc.currentForecast,
        deviation: 0,
        confidence: 'Low',
        recommendedResponse: 'No action needed',
        timestamp: `Month ${CURRENT_MONTH}`,
      });
    }
  }
  return alerts.sort((a, b) => riskWeight(b.risk) - riskWeight(a.risk));
}

// ── KPI data ────────────────────────────────────────────────────────
export function getKPIData(): KPIData {
  const forecasts = getAllForecasts();
  const totalForecastDemand = forecasts.reduce((s, f) => s + f.currentForecast, 0);
  const totalAvailableCapacity = DISTRICTS.reduce((s, d) => s + d.nominalCapacity, 0) + RESERVE_CAPACITY;
  const allocation = getAllocation('Surge Adaptive');
  const totalUnmet = allocation.totalUnmetDemand;
  return {
    districts: DISTRICTS.length,
    reserveUnits: RESERVE_CAPACITY,
    currentMonth: CURRENT_MONTH,
    totalForecastDemand,
    totalAvailableCapacity,
    expectedShortage: totalUnmet,
    reserveUtilization: 1.0,
  };
}

// ── Performance metrics (demo / awaiting evaluation) ────────────────
export function getPerformanceMetrics(): PerformanceMetrics {
  const allocation = getAllocation('Surge Adaptive');
  const districtService = DISTRICTS.map((d) => {
    const a = allocation.allocations.find((x) => x.districtId === d.id)!;
    const observed = getObservedDemand(d.id, CURRENT_MONTH);
    const effectiveCapacity = d.nominalCapacity + a.reserve;
    return {
      districtId: d.id,
      service: observed > 0 ? Math.min(1, effectiveCapacity / observed) : 1,
    };
  });

  const unmetDemandTimeline = Array.from({ length: FORECAST_MONTHS }, (_, i) => {
    const month = HISTORICAL_MONTHS + i;
    const demand = DISTRICTS.reduce((s, d) => s + getObservedDemand(d.id, month), 0);
    const capacity = DISTRICTS.reduce((s, d) => s + d.nominalCapacity, 0);
    const reserve = RESERVE_CAPACITY;
    const unmet = Math.max(0, demand - capacity - reserve);
    return { month, demand, capacity, reserve, unmet };
  });

  return {
    forecastUtility: null,
    demandServiceUtility: allocation.serviceUtility,
    worstDistrictService: allocation.worstDistrictService,
    compliance: {
      reserveConstraint: true,
      integerAllocations: true,
      noFutureLeakage: true,
      reproducibleConfig: true,
    },
    districtService,
    unmetDemandTimeline,
  };
}

// ── Simulation results per policy ──────────────────────────────────
export function getSimulationResults(
  scenario: SimulationScenario = 'Baseline',
): SimulationResult[] {
  const policies: AllocationPolicy[] = [
    'Equal Split',
    'Forecast Only',
    'Risk Based',
    'Fairness Aware',
    'Surge Adaptive',
  ];

  return policies.map((policy) => {
    const alloc = getAllocation(policy);
    const scenarioMultiplier =
      scenario === 'Seasonal Peak' ? 1.15 :
      scenario === 'Demand Growth' ? 1.25 :
      scenario === 'Sudden Surge' ? 1.35 :
      1.0;

    const adjustedUnmet = Math.round(alloc.totalUnmetDemand * scenarioMultiplier);
    const adjustedService = Math.max(0, alloc.serviceUtility - (scenarioMultiplier - 1) * 0.3);

    return {
      policy,
      totalUnmetDemand: adjustedUnmet,
      serviceUtility: adjustedService,
      worstDistrictService: Math.max(0, alloc.worstDistrictService - (scenarioMultiplier - 1) * 0.2),
      reserveUtilization: 1.0,
      districtAllocations: alloc.allocations.map((a) => ({
        districtId: a.districtId,
        allocation: a.reserve,
        unmetDemand: Math.max(0, Math.round(
          getObservedDemand(a.districtId, CURRENT_MONTH) * scenarioMultiplier -
          DISTRICTS.find((d) => d.id === a.districtId)!.nominalCapacity -
          a.reserve,
        )),
      })),
    };
  });
}

// ── District detail helper ──────────────────────────────────────────
export function getDistrictDetail(districtId: string) {
  const d = DISTRICTS.find((x) => x.id === districtId);
  if (!d) return null;
  const fc = getDistrictForecast(districtId);
  const alloc = getAllocation('Surge Adaptive').allocations.find((a) => a.districtId === districtId)!;
  const observed = getObservedDemand(districtId, CURRENT_MONTH);
  const effectiveCapacity = d.nominalCapacity + alloc.reserve;
  const unmetDemand = Math.max(0, observed - effectiveCapacity);
  const serviceLevel = observed > 0 ? Math.min(1, effectiveCapacity / observed) : 1;
  const shortageProbability = Math.min(1, Math.max(0, (fc.currentForecast - d.nominalCapacity + fc.uncertainty * 2) / 40));

  return {
    district: d,
    forecast: fc,
    allocation: alloc,
    observed,
    effectiveCapacity,
    unmetDemand,
    serviceLevel,
    shortageProbability,
    risk: fc.risk,
  };
}

// ── Surge history per district ──────────────────────────────────────
export function getSurgeHistory(districtId: string) {
  const fc = getDistrictForecast(districtId);
  const history = fc.history.slice(-12);
  return history.map((h) => ({
    month: h.month,
    actual: h.actual,
    forecast: h.forecast,
    residual: h.residual,
    isAnomaly: Math.abs(h.residual) > fc.uncertainty * 2.5,
  }));
}
