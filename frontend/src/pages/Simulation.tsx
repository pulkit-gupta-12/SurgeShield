import { useState } from 'react';
import { Play, FlaskConical, RotateCcw, Download } from 'lucide-react';
import { KpiCard } from '../components/KpiCard';
import { PolicySelector } from '../components/PolicySelector';
import { SimulationComparison } from '../components/SimulationComparison';
import { Tooltip } from '../components/Tooltip';
import { getSimulationResults } from '../services/mockData';
import type { SimulationScenario, SimulationResult, AllocationPolicy } from '../services/types';
import { Package, AlertTriangle, Award, Activity } from 'lucide-react';

const scenarios: { name: SimulationScenario; desc: string }[] = [
  { name: 'Baseline',      desc: 'Normal seasonal demand' },
  { name: 'Seasonal Peak', desc: '+15% demand increase' },
  { name: 'Demand Growth', desc: '+25% demand increase' },
  { name: 'Sudden Surge',  desc: '+35% demand surge' },
];

export default function Simulation() {
  const [scenario, setScenario] = useState<SimulationScenario>('Baseline');
  const [results, setResults] = useState<SimulationResult[]>(getSimulationResults('Baseline'));
  const [running, setRunning] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<AllocationPolicy>('Surge Adaptive');

  const runSimulation = () => {
    setRunning(true);
    setTimeout(() => {
      setResults(getSimulationResults(scenario));
      setRunning(false);
    }, 400);
  };

  const selected = results.find((r) => r.policy === selectedPolicy) ?? results[0];

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">What-If Allocation Simulator</h1>
        <p className="text-sm text-slate-500 mt-1">
          Compare allocation policies under different demand scenarios
          <Tooltip content="This is a UI prototype. Backend simulation will be connected later — results shown are mock/demo." />
        </p>
      </div>

      {/* Scenario selector */}
      <div>
        <h3 className="section-title mb-3">Scenario</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {scenarios.map((s) => (
            <button
              key={s.name}
              onClick={() => setScenario(s.name)}
              className={`card card-pad text-left transition-all ${
                scenario === s.name
                  ? 'border-brand-500 ring-2 ring-brand-200 bg-brand-50'
                  : 'hover:border-slate-300 hover:shadow-md'
              }`}
            >
              <p className={`text-sm font-semibold ${scenario === s.name ? 'text-brand-700' : 'text-slate-700'}`}>
                {s.name}
              </p>
              <p className="text-xs text-slate-400 mt-1">{s.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Policy selector */}
      <div>
        <h3 className="section-title mb-3">Allocation Policy</h3>
        <PolicySelector selected={selectedPolicy} onChange={setSelectedPolicy} />
      </div>

      {/* Run button */}
      <div className="flex items-center gap-3">
        <button onClick={runSimulation} disabled={running} className="btn-primary">
          {running ? <RotateCcw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {running ? 'Running...' : 'Run Simulation'}
        </button>
        <span className="badge bg-amber-50 text-amber-600">SIMULATION</span>
        <span className="text-xs text-slate-400">Scenario: {scenario} · Policy: {selectedPolicy}</span>
      </div>

      {/* Selected policy results */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard icon={AlertTriangle} label="Unmet Demand" value={selected.totalUnmetDemand} sublabel="units (demo)" accent="red" />
        <KpiCard icon={Activity} label="Service Utility" value={`${(selected.serviceUtility * 100).toFixed(1)}%`} sublabel="demand served" accent="green" />
        <KpiCard icon={Award} label="Worst District" value={`${(selected.worstDistrictService * 100).toFixed(1)}%`} sublabel="service level" accent="amber"
          tooltip="Uworst: Service score of the worst-performing district." />
        <KpiCard icon={Package} label="Reserve Used" value={`${selected.reserveUtilization * 100}%`} sublabel="60 of 60" accent="teal" />
      </div>

      {/* Comparison charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SimulationComparison results={results} metric="totalUnmetDemand" title="Unmet Demand by Policy" />
        <SimulationComparison results={results} metric="serviceUtility" title="Service Utility by Policy" />
      </div>
      <SimulationComparison results={results} metric="worstDistrictService" title="Worst-District Service by Policy" />

      {/* Comparison table */}
      <div className="card card-pad">
        <h3 className="section-title mb-1">Policy Comparison Table</h3>
        <p className="section-subtitle mb-4">All policies under scenario: {scenario}</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left">
                <th className="py-2.5 px-3 font-semibold text-slate-600">Policy</th>
                <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Unmet Demand</th>
                <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Service Utility</th>
                <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Worst District</th>
                <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Reserve Util.</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr
                  key={r.policy}
                  className={`border-b border-slate-100 cursor-pointer transition-colors ${
                    r.policy === selectedPolicy ? 'bg-brand-50' : 'hover:bg-slate-50'
                  }`}
                  onClick={() => setSelectedPolicy(r.policy)}
                >
                  <td className="py-2.5 px-3 font-medium text-slate-900">{r.policy}</td>
                  <td className="py-2.5 px-3 text-right tabular-nums text-red-600 font-medium">{r.totalUnmetDemand}</td>
                  <td className="py-2.5 px-3 text-right tabular-nums text-green-600 font-medium">{(r.serviceUtility * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-right tabular-nums text-amber-600 font-medium">{(r.worstDistrictService * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-right tabular-nums text-slate-600">{(r.reserveUtilization * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Per-district allocation for selected policy */}
      <div className="card card-pad">
        <h3 className="section-title mb-1">Per-District Allocation — {selectedPolicy}</h3>
        <p className="section-subtitle mb-4">Scenario: {scenario}</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left">
                <th className="py-2.5 px-3 font-semibold text-slate-600">District</th>
                <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Allocation</th>
                <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Unmet Demand</th>
              </tr>
            </thead>
            <tbody>
              {selected.districtAllocations.map((a) => (
                <tr key={a.districtId} className="border-b border-slate-100">
                  <td className="py-2.5 px-3 font-medium text-slate-700">{a.districtId}</td>
                  <td className="py-2.5 px-3 text-right tabular-nums text-brand-600 font-medium">{a.allocation}</td>
                  <td className={`py-2.5 px-3 text-right tabular-nums ${a.unmetDemand > 0 ? 'text-red-600 font-medium' : 'text-green-600'}`}>
                    {a.unmetDemand > 0 ? a.unmetDemand : '0'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
