import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, CheckCircle, Layers, MapPin, Info } from 'lucide-react';
import { KpiCard } from '../components/KpiCard';
import { DistrictTable } from '../components/DistrictTable';
import { AllocationChart } from '../components/AllocationChart';
import { PolicySelector } from '../components/PolicySelector';
import { ExplainabilityCard } from '../components/ExplainabilityCard';
import { Tooltip } from '../components/Tooltip';
import { getAllocation, getAllForecasts } from '../services/mockData';
import type { AllocationPolicy } from '../services/types';

export default function Allocation() {
  const navigate = useNavigate();
  const [policy, setPolicy] = useState<AllocationPolicy>('Surge Adaptive');
  const allocation = getAllocation(policy);
  const forecasts = getAllForecasts();
  const topAllocation = [...allocation.allocations].sort((a, b) => b.reserve - a.reserve)[0];

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reserve Allocation Console</h1>
        <p className="text-sm text-slate-500 mt-1">
          Distribute {allocation.totalReserve} reserve units across 12 districts based on forecast risk
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard icon={Package} label="Total Reserve" value={allocation.totalReserve} sublabel="Available units" accent="teal" />
        <KpiCard icon={CheckCircle} label="Allocated" value={allocation.allocations.reduce((s, a) => s + a.reserve, 0)} sublabel="Fully distributed" accent="green" />
        <KpiCard icon={Layers} label="Remaining" value={0} sublabel="All units assigned" accent="amber" />
        <KpiCard icon={MapPin} label="Districts Served" value={12} sublabel="All districts" accent="blue" />
      </div>

      {/* Policy selector */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <h3 className="section-title">Allocation Policy</h3>
          <span className="badge bg-amber-50 text-amber-600 text-[10px]">SIMULATION</span>
          <Tooltip content="Changing the policy updates the mock allocation. Backend allocation logic will be connected later." />
        </div>
        <PolicySelector selected={policy} onChange={setPolicy} />
      </div>

      {/* Allocation chart + Explainability */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card card-pad">
          <h3 className="section-title mb-1">Reserve Allocation by District</h3>
          <p className="section-subtitle mb-4">Policy: {policy} — color indicates risk level</p>
          <AllocationChart allocations={allocation.allocations} />
        </div>
        <div className="space-y-4">
          <div className="card card-pad bg-brand-50 border-brand-200">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-4 h-4 text-brand-600" />
              <h4 className="text-sm font-semibold text-brand-700">Why this allocation?</h4>
            </div>
            <p className="text-xs text-slate-600">
              {topAllocation && (
                <>District {topAllocation.districtId} received {topAllocation.reserve} reserve units because its predicted shortage risk and expected unmet-demand reduction were highest.</>
              )}
            </p>
          </div>
          {topAllocation && (
            <ExplainabilityCard allocation={topAllocation} />
          )}
        </div>
      </div>

      {/* Allocation table */}
      <div className="card card-pad">
        <h3 className="section-title mb-1">Allocation Detail</h3>
        <p className="section-subtitle mb-4">
          Per-district allocation with expected benefit and reasoning — click a row for details
        </p>
        <DistrictTable
          forecasts={forecasts}
          allocations={allocation.allocations}
          showAllocation
          showBenefit
          showReason
        />
      </div>

      {/* Outcome summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card card-pad text-center">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Total Unmet Demand</p>
          <p className="text-2xl font-bold text-red-600 tabular-nums mt-1">{allocation.totalUnmetDemand}</p>
          <p className="text-xs text-slate-400 mt-0.5">units (demo)</p>
        </div>
        <div className="card card-pad text-center">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Service Utility</p>
          <p className="text-2xl font-bold text-green-600 tabular-nums mt-1">{(allocation.serviceUtility * 100).toFixed(1)}%</p>
          <p className="text-xs text-slate-400 mt-0.5">demand served (demo)</p>
        </div>
        <div className="card card-pad text-center">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Worst District</p>
          <p className="text-2xl font-bold text-amber-600 tabular-nums mt-1">{(allocation.worstDistrictService * 100).toFixed(1)}%</p>
          <p className="text-xs text-slate-400 mt-0.5">service level (demo)
            <Tooltip content="Uworst: Service score of the worst-performing district." />
          </p>
        </div>
      </div>
    </div>
  );
}
