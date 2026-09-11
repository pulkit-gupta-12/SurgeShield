import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MapPin, Package, Calendar, TrendingUp, Building2, AlertTriangle,
  Activity, ArrowRight, BarChart3,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { KpiCard } from '../components/KpiCard';
import { RiskBadge, riskColor } from '../components/RiskBadge';
import { DistrictTable } from '../components/DistrictTable';
import { ProcessLoop } from '../components/ProcessLoop';
import { Tooltip } from '../components/Tooltip';
import {
  getKPIData, getAllForecasts, getAllocation, getSurgeAlerts, DISTRICTS,
} from '../services/mockData';
import { CURRENT_MONTH } from '../services/mockData';

export default function Dashboard() {
  const navigate = useNavigate();
  const kpi = getKPIData();
  const forecasts = getAllForecasts();
  const allocation = getAllocation('Surge Adaptive');
  const alerts = getSurgeAlerts();
  const activeAlerts = alerts.filter((a) => a.risk === 'Critical' || a.risk === 'High');

  // Forecast vs Capacity chart data — aggregate across districts
  const chartData = forecasts[0].future.map((_, i) => {
    const month = CURRENT_MONTH + i;
    const totalForecast = forecasts.reduce((s, f) => s + f.future[i].forecast, 0);
    const totalCapacity = DISTRICTS.reduce((s, d) => s + d.nominalCapacity, 0);
    return { month, forecast: totalForecast, capacity: totalCapacity };
  });

  // Allocation bar data
  const allocBarData = allocation.allocations.map((a) => ({
    district: a.districtId,
    units: a.reserve,
    risk: forecasts.find((f) => f.districtId === a.districtId)!.risk,
  }));

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Executive Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          District Health Surge Forecast & Allocation — decision support overview
        </p>
      </div>

      {/* Decision loop */}
      <ProcessLoop />

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <KpiCard icon={MapPin} label="Districts" value={kpi.districts} sublabel="Under monitoring" accent="blue" />
        <KpiCard icon={Package} label="Reserve Units" value={kpi.reserveUnits} sublabel="Available for allocation" accent="teal"
          tooltip="Additional capacity that can be temporarily assigned to districts." />
        <KpiCard icon={Calendar} label="Current Month" value={`t=${kpi.currentMonth}`} sublabel="Evaluation horizon" accent="slate" />
        <KpiCard icon={TrendingUp} label="Forecast Demand" value={kpi.totalForecastDemand} sublabel="Total across districts" accent="blue" />
        <KpiCard icon={Building2} label="Available Capacity" value={kpi.totalAvailableCapacity} sublabel="Nominal + reserve" accent="teal" />
        <KpiCard icon={AlertTriangle} label="Expected Shortage" value={kpi.expectedShortage} sublabel="Unmet demand (demo)" accent="red"
          tooltip="Demand exceeding available capacity after allocation." />
        <KpiCard icon={Activity} label="Reserve Utilization" value={`${Math.round(kpi.reserveUtilization * 100)}%`} sublabel="60 of 60 allocated" accent="amber" />
        <KpiCard icon={AlertTriangle} label="Active Alerts" value={activeAlerts.length} sublabel="Districts need attention" accent="orange" />
      </div>

      {/* Alert panel */}
      {activeAlerts.length > 0 && (
        <div className="card card-pad border-l-4 border-l-red-500">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="section-title">{activeAlerts.length} district{activeAlerts.length > 1 ? 's' : ''} require attention</h3>
              <div className="flex flex-wrap gap-2 mt-2">
                {activeAlerts.map((a) => (
                  <button
                    key={a.districtId}
                    onClick={() => navigate(`/districts/${a.districtId}`)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 rounded-md text-sm transition-colors"
                  >
                    <span className="font-semibold text-slate-900">{a.districtId}</span>
                    <RiskBadge risk={a.risk} />
                  </button>
                ))}
              </div>
            </div>
            <button onClick={() => navigate('/surge-monitor')} className="btn-primary whitespace-nowrap">
              View Surge Monitor <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Forecast vs Capacity chart + Allocation summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card card-pad">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="section-title">Forecast vs Capacity</h3>
              <p className="section-subtitle">Total demand forecast vs total nominal capacity — months 36–41</p>
            </div>
            <BarChart3 className="w-5 h-5 text-slate-300" />
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }}
                label={{ value: 'Month', position: 'insideBottom', offset: -5, style: { fontSize: 11, fill: '#94a3b8' } }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <RTooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <ReferenceLine y={kpi.totalAvailableCapacity - kpi.reserveUnits} stroke="#dc2626" strokeDasharray="2 2" name="Nominal capacity" />
              <Line dataKey="forecast" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} name="Forecast demand" />
              <Line dataKey="capacity" stroke="#0d9488" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Total capacity" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Recommended Reserve Allocation */}
        <div className="card card-pad">
          <h3 className="section-title">Recommended Reserve Allocation</h3>
          <p className="section-subtitle mb-4">
            {kpi.reserveUnits} units distributed across {kpi.districts} districts
            <Tooltip content="Reserve Units: Additional capacity that can be temporarily assigned to districts." />
          </p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {allocation.allocations
              .filter((a) => a.reserve > 0)
              .sort((a, b) => b.reserve - a.reserve)
              .map((a) => {
                const fc = forecasts.find((f) => f.districtId === a.districtId)!;
                return (
                  <div key={a.districtId} className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-600 w-8">{a.districtId}</span>
                    <div className="flex-1 h-5 bg-slate-100 rounded overflow-hidden">
                      <div
                        className="h-full rounded transition-all duration-500 flex items-center justify-end pr-1.5"
                        style={{ width: `${(a.reserve / kpi.reserveUnits) * 100}%`, backgroundColor: riskColor(fc.risk) }}
                      >
                        <span className="text-[10px] font-semibold text-white">{a.reserve}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-400">Policy: Surge Adaptive</span>
            <button onClick={() => navigate('/allocation')} className="text-brand-600 font-medium hover:underline">
              Open console →
            </button>
          </div>
        </div>
      </div>

      {/* District risk overview table */}
      <div className="card card-pad">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="section-title">District Risk Overview</h3>
            <p className="section-subtitle">Click any district to view detailed analysis</p>
          </div>
        </div>
        <DistrictTable forecasts={forecasts} allocations={allocation.allocations} showReserve />
      </div>
    </div>
  );
}
