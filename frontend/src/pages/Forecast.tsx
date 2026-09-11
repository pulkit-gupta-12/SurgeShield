import { useState } from 'react';
import {
  TrendingUp, BarChart3, AlertTriangle, Calendar, Activity,
  ArrowUp, ArrowDown, Waves,
} from 'lucide-react';
import { KpiCard } from '../components/KpiCard';
import { RiskBadge } from '../components/RiskBadge';
import { ForecastChart } from '../components/ForecastChart';
import { DistrictCard } from '../components/DistrictCard';
import { Tooltip } from '../components/Tooltip';
import { getAllForecasts, DISTRICTS, CURRENT_MONTH, FORECAST_MONTHS } from '../services/mockData';

export default function Forecast() {
  const forecasts = getAllForecasts();
  const [selectedId, setSelectedId] = useState('D2');
  const selected = forecasts.find((f) => f.districtId === selectedId)!;
  const district = DISTRICTS.find((d) => d.id === selectedId)!;

  const totalForecast = forecasts.reduce((s, f) => s + f.currentForecast, 0);
  const avgForecast = Math.round(totalForecast / forecasts.length);
  const highest = forecasts.reduce((max, f) => f.currentForecast > max.currentForecast ? f : max);

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Forecasting</h1>
        <p className="text-sm text-slate-500 mt-1">
          Seasonal + Trend baseline forecasting across 12 districts
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard icon={BarChart3} label="Forecast Utility" value="—" sublabel="Awaiting evaluation" accent="slate"
          tooltip="Measures forecast quality according to the competition metric." />
        <KpiCard icon={TrendingUp} label="Avg Forecast Demand" value={avgForecast} sublabel="Per district" accent="blue" />
        <KpiCard icon={AlertTriangle} label="Highest Forecast" value={`${highest.districtId}`} sublabel={`${highest.currentForecast} units`} accent="red" />
        <KpiCard icon={Calendar} label="Forecast Horizon" value={`${FORECAST_MONTHS} mo`} sublabel={`t=${CURRENT_MONTH}–${CURRENT_MONTH + FORECAST_MONTHS - 1}`} accent="teal" />
      </div>

      {/* Main chart */}
      <div className="card card-pad">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
          <div>
            <h3 className="section-title">Historical Demand vs Forecast — {selectedId}</h3>
            <p className="section-subtitle">{district.name} · {district.region} region · Capacity: {district.nominalCapacity}</p>
          </div>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="input w-auto min-w-[140px]"
          >
            {DISTRICTS.map((d) => (
              <option key={d.id} value={d.id}>{d.id} — {d.name}</option>
            ))}
          </select>
        </div>
        <ForecastChart forecast={selected} />
      </div>

      {/* Forecast info cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="card card-pad">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-4 h-4 text-brand-500" />
            <p className="text-xs text-slate-500">Forecast</p>
          </div>
          <p className="text-xl font-bold text-slate-900 tabular-nums">{selected.currentForecast}</p>
          <p className="text-xs text-slate-400">units for t={CURRENT_MONTH}</p>
        </div>
        <div className="card card-pad">
          <div className="flex items-center gap-2 mb-1">
            <ArrowUp className="w-4 h-4 text-orange-500" />
            <p className="text-xs text-slate-500">Trend</p>
          </div>
          <p className="text-xl font-bold text-slate-900 tabular-nums">+{selected.trend}/mo</p>
          <p className="text-xs text-slate-400">monthly slope</p>
        </div>
        <div className="card card-pad">
          <div className="flex items-center gap-2 mb-1">
            <Waves className="w-4 h-4 text-teal-500" />
            <p className="text-xs text-slate-500">Seasonality</p>
          </div>
          <p className="text-xl font-bold text-slate-900 tabular-nums">±{selected.seasonality}</p>
          <p className="text-xs text-slate-400">amplitude</p>
        </div>
        <div className="card card-pad">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-4 h-4 text-amber-500" />
            <p className="text-xs text-slate-500">Uncertainty</p>
          </div>
          <p className="text-xl font-bold text-slate-900 tabular-nums">±{selected.uncertainty}</p>
          <p className="text-xs text-slate-400">std dev</p>
        </div>
        <div className="card card-pad">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <p className="text-xs text-slate-500">Risk</p>
          </div>
          <div className="mt-1"><RiskBadge risk={selected.risk} size="md" /></div>
        </div>
      </div>

      {/* 12-district mini overview */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="section-title">All 12 Districts — Forecast Overview</h3>
          <span className="text-xs text-slate-400">
            Forecast model: Seasonal + Trend baseline
            <Tooltip content="A baseline forecasting approach using trend and seasonal decomposition. Not a trained ML model." />
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {forecasts.map((f) => (
            <DistrictCard key={f.districtId} forecast={f} />
          ))}
        </div>
      </div>
    </div>
  );
}
