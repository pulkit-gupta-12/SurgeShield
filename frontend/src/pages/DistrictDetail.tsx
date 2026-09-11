import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, TrendingUp, Building2, Package, Shield, AlertTriangle,
  Activity, BarChart3, History, Info,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { RiskBadge, riskColor } from '../components/RiskBadge';
import { ProgressBar } from '../components/ProgressBar';
import { ExplainabilityCard } from '../components/ExplainabilityCard';
import { Tooltip } from '../components/Tooltip';
import {
  getDistrictDetail, getSurgeHistory, getDistrictForecast, DISTRICTS,
} from '../services/mockData';

export default function DistrictDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const detail = id ? getDistrictDetail(id) : null;

  if (!detail) {
    return (
      <div className="p-6">
        <p className="text-slate-500">District not found.</p>
        <button onClick={() => navigate('/dashboard')} className="btn-secondary mt-4">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>
      </div>
    );
  }

  const { district: d, forecast: fc, allocation: alloc } = detail;
  const surgeHistory = getSurgeHistory(d.id);

  // Demand history chart data
  const chartData = [
    ...fc.history.map((h) => ({
      month: h.month,
      Actual: h.actual,
      Forecast: h.forecast,
      Capacity: d.nominalCapacity,
    })),
    ...fc.future.map((f) => ({
      month: f.month,
      Forecast: f.forecast,
      Capacity: d.nominalCapacity,
      Actual: null as number | null,
    })),
  ];

  // Capacity breakdown
  const effectiveCapacity = d.nominalCapacity + alloc.reserve;
  const capacityBreakdown = [
    { name: 'Nominal', value: d.nominalCapacity, color: '#0d9488' },
    { name: 'Reserve', value: alloc.reserve, color: '#2563eb' },
    { name: 'Unmet', value: detail.unmetDemand, color: '#dc2626' },
    { name: 'Surplus', value: Math.max(0, effectiveCapacity - detail.observed), color: '#16a34a' },
  ];

  const riskFactors = [
    { label: 'Demand Trend', value: Math.min(1, d.trend / 1.0), color: '#ea580c' },
    { label: 'Seasonal Effect', value: Math.min(1, d.seasonalityAmplitude / 20), color: '#0d9488' },
    { label: 'Capacity Gap', value: Math.min(1, Math.max(0, fc.currentForecast - d.nominalCapacity) / 40), color: '#dc2626' },
    { label: 'Recent Residual', value: Math.min(1, Math.abs(surgeHistory[surgeHistory.length - 1]?.residual ?? 0) / 20), color: '#ca8a04' },
    { label: 'Surge Signal', value: detail.observed - fc.currentForecast > 20 ? 1 : 0.2, color: '#2563eb' },
  ];

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      {/* Back + header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/dashboard')} className="p-2 hover:bg-slate-100 rounded-md">
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">District {d.id}</h1>
            <RiskBadge risk={detail.risk} size="md" />
          </div>
          <p className="text-sm text-slate-500 mt-0.5">
            {d.name} · {d.region} region · Population {d.population.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {[
          { icon: TrendingUp, label: 'Forecast', value: fc.currentForecast, color: 'text-brand-600' },
          { icon: Building2, label: 'Capacity', value: d.nominalCapacity, color: 'text-teal-600' },
          { icon: Package, label: 'Reserve', value: alloc.reserve, color: 'text-blue-600' },
          { icon: Shield, label: 'Eff. Capacity', value: effectiveCapacity, color: 'text-teal-600' },
          { icon: AlertTriangle, label: 'Shortage Risk', value: `${Math.round(detail.shortageProbability * 100)}%`, color: 'text-red-600' },
          { icon: Activity, label: 'Service Level', value: `${Math.round(detail.serviceLevel * 100)}%`, color: 'text-green-600' },
          { icon: BarChart3, label: 'Unmet Demand', value: detail.unmetDemand, color: 'text-red-600' },
        ].map((m) => (
          <div key={m.label} className="card card-pad">
            <div className="flex items-center gap-1.5 mb-1">
              <m.icon className={`w-3.5 h-3.5 ${m.color}`} />
              <p className="text-[10px] text-slate-500 uppercase tracking-wide">{m.label}</p>
            </div>
            <p className={`text-lg font-bold tabular-nums ${m.color}`}>{m.value}</p>
          </div>
        ))}
      </div>

      {/* Demand history chart */}
      <div className="card card-pad">
        <h3 className="section-title mb-1">Demand History & Forecast</h3>
        <p className="section-subtitle mb-4">
          Historical actuals (t=0–35) vs forecast (t=36–41) vs nominal capacity
        </p>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }}
              label={{ value: 'Month', position: 'insideBottom', offset: -5, style: { fontSize: 11, fill: '#94a3b8' } }} />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
            <RTooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <ReferenceLine x={35} stroke="#cbd5e1" strokeDasharray="4 4" label={{ value: 'Now', style: { fontSize: 10, fill: '#94a3b8' } }} />
            <Line dataKey="Actual" stroke="#0d9488" strokeWidth={2} dot={false} name="Actual" connectNulls={false} />
            <Line dataKey="Forecast" stroke="#2563eb" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Forecast" connectNulls />
            <Line dataKey="Capacity" stroke="#dc2626" strokeWidth={1.5} dot={false} strokeDasharray="2 2" name="Capacity" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Capacity breakdown */}
        <div className="card card-pad">
          <h3 className="section-title mb-1">Capacity Breakdown</h3>
          <p className="section-subtitle mb-4">Effective capacity = nominal + reserve allocation</p>
          <div className="space-y-3">
            {capacityBreakdown.map((c) => (
              <div key={c.name} className="flex items-center gap-3">
                <span className="text-xs font-medium text-slate-600 w-16">{c.name}</span>
                <div className="flex-1 h-6 bg-slate-100 rounded overflow-hidden">
                  <div
                    className="h-full rounded transition-all duration-500 flex items-center justify-end pr-2"
                    style={{
                      width: `${Math.max(2, (c.value / Math.max(...capacityBreakdown.map((x) => x.value))) * 100)}%`,
                      backgroundColor: c.color,
                    }}
                  >
                    <span className="text-[10px] font-semibold text-white">{c.value}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-sm">
            <span className="text-slate-500">Observed Demand</span>
            <span className="font-semibold text-slate-900 tabular-nums">{detail.observed}</span>
          </div>
        </div>

        {/* Risk panel */}
        <div className="card card-pad">
          <h3 className="section-title mb-1">Risk Analysis</h3>
          <p className="section-subtitle mb-4">
            Shortage probability and contributing risk factors
            <Tooltip content="Shortage Probability: likelihood that demand exceeds effective capacity." />
          </p>
          <div className="mb-4">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-slate-600">Shortage Probability</span>
              <span className="text-sm font-semibold text-slate-900">{Math.round(detail.shortageProbability * 100)}%</span>
            </div>
            <ProgressBar value={detail.shortageProbability} color={riskColor(detail.risk)} showValue={false} />
          </div>
          <div className="space-y-3">
            {riskFactors.map((f) => (
              <ProgressBar key={f.label} label={f.label} value={f.value} color={f.color} />
            ))}
          </div>
        </div>
      </div>

      {/* Surge history */}
      <div className="card card-pad">
        <div className="flex items-center gap-2 mb-3">
          <History className="w-4 h-4 text-slate-400" />
          <h3 className="section-title">Surge History — Last 12 Months</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left">
                <th className="py-2 px-3 font-semibold text-slate-600">Month</th>
                <th className="py-2 px-3 font-semibold text-slate-600 text-right">Actual</th>
                <th className="py-2 px-3 font-semibold text-slate-600 text-right">Forecast</th>
                <th className="py-2 px-3 font-semibold text-slate-600 text-right">Residual</th>
                <th className="py-2 px-3 font-semibold text-slate-600">Status</th>
              </tr>
            </thead>
            <tbody>
              {surgeHistory.map((h) => (
                <tr key={h.month} className="border-b border-slate-100">
                  <td className="py-2 px-3 font-medium text-slate-700">t={h.month}</td>
                  <td className="py-2 px-3 text-right tabular-nums text-slate-700">{h.actual}</td>
                  <td className="py-2 px-3 text-right tabular-nums text-slate-500">{h.forecast}</td>
                  <td className={`py-2 px-3 text-right tabular-nums font-medium ${h.residual > 10 ? 'text-red-600' : h.residual < -10 ? 'text-blue-600' : 'text-slate-500'}`}>
                    {h.residual > 0 ? '+' : ''}{h.residual}
                  </td>
                  <td className="py-2 px-3">
                    {h.isAnomaly ? (
                      <span className="badge bg-red-50 text-red-600">Anomaly</span>
                    ) : (
                      <span className="badge bg-green-50 text-green-600">Normal</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Allocation explanation */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Info className="w-4 h-4 text-slate-400" />
          <h3 className="section-title">Allocation Explanation</h3>
        </div>
        <ExplainabilityCard allocation={alloc} />
      </div>

      {/* Navigation buttons */}
      <div className="flex gap-3">
        <button onClick={() => navigate('/dashboard')} className="btn-secondary">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>
        <button onClick={() => navigate('/surge-monitor')} className="btn-secondary">
          View Surge Monitor
        </button>
        <button onClick={() => navigate('/allocation')} className="btn-primary">
          Open Allocation Console
        </button>
      </div>
    </div>
  );
}
