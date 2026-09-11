import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, AlertTriangle, ArrowRight, Eye, CheckCircle, Zap,
} from 'lucide-react';
import { KpiCard } from '../components/KpiCard';
import { RiskBadge, riskColor } from '../components/RiskBadge';
import { SurgeAlertCard } from '../components/SurgeAlert';
import { ResidualChart } from '../components/ResidualChart';
import { Tooltip } from '../components/Tooltip';
import {
  getSurgeAlerts, getDistrictForecast, getObservedDemand,
  getDistrictForecast as getFC, DISTRICTS, CURRENT_MONTH,
} from '../services/mockData';
import type { SurgeStage } from '../services/types';

const stages: { stage: SurgeStage; color: string }[] = [
  { stage: 'Normal',          color: '#16a34a' },
  { stage: 'Elevated',        color: '#ca8a04' },
  { stage: 'Anomaly',         color: '#ea580c' },
  { stage: 'Confirmed Surge', color: '#dc2626' },
  { stage: 'Response',        color: '#2563eb' },
];

export default function SurgeMonitor() {
  const navigate = useNavigate();
  const alerts = getSurgeAlerts();
  const [selectedDistrict, setSelectedDistrict] = useState('D2');
  const fc = getDistrictForecast(selectedDistrict);
  const expected = fc.currentForecast;
  const observed = getObservedDemand(selectedDistrict, CURRENT_MONTH);
  const deviation = observed - expected;

  // Residual data from last 12 historical months
  const residualData = fc.history.slice(-12).map((h) => ({
    month: h.month,
    actual: h.actual,
    forecast: h.forecast,
    residual: h.residual,
  }));

  const criticalCount = alerts.filter((a) => a.risk === 'Critical').length;
  const highCount = alerts.filter((a) => a.risk === 'High').length;
  const elevatedCount = alerts.filter((a) => a.stage === 'Elevated').length;

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Surge Monitor</h1>
        <p className="text-sm text-slate-500 mt-1">
          Detect unusual demand before it becomes a capacity crisis.
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard icon={AlertTriangle} label="Critical Alerts" value={criticalCount} sublabel="Confirmed surge" accent="red" />
        <KpiCard icon={Activity} label="High Risk" value={highCount} sublabel="Elevated demand" accent="orange" />
        <KpiCard icon={Eye} label="Monitoring" value={elevatedCount} sublabel="Under watch" accent="amber" />
        <KpiCard icon={CheckCircle} label="Normal" value={alerts.filter((a) => a.stage === 'Normal').length} sublabel="No anomaly" accent="green" />
      </div>

      {/* Current alerts */}
      <div>
        <h3 className="section-title mb-3">Current Alerts</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {alerts.filter((a) => a.risk !== 'Low').map((alert) => (
            <SurgeAlertCard key={alert.districtId} alert={alert} />
          ))}
        </div>
      </div>

      {/* Detection panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card card-pad">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="section-title">Detected Anomaly</h3>
              <p className="section-subtitle">
                Surge discovered from observed demand residuals — not known in advance
                <Tooltip content="The evaluation scenario hides surge location/timing. SurgeShield detects anomalies from residuals, not from prior knowledge." />
              </p>
            </div>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="input w-auto min-w-[120px]"
            >
              {DISTRICTS.map((d) => (
                <option key={d.id} value={d.id}>{d.id} — {d.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Expected Demand</p>
              <p className="text-lg font-semibold text-slate-700 tabular-nums">{expected}</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Observed Demand</p>
              <p className="text-lg font-semibold text-slate-900 tabular-nums">{observed}</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Deviation</p>
              <p className={`text-lg font-semibold tabular-nums ${deviation > 10 ? 'text-red-600' : deviation > 0 ? 'text-amber-600' : 'text-green-600'}`}>
                {deviation > 0 ? '+' : ''}{deviation}
              </p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Confidence</p>
              <p className="text-lg font-semibold text-slate-700">
                {Math.abs(deviation) > 20 ? 'High' : Math.abs(deviation) > 5 ? 'Medium' : 'Low'}
              </p>
            </div>
          </div>

          <div className="bg-brand-50 border border-brand-200 rounded-lg p-3">
            <p className="text-xs font-semibold text-brand-700 mb-1">Recommended Response</p>
            <p className="text-sm text-slate-700">
              {deviation > 20
                ? 'Increase reserve priority immediately — confirmed surge detected'
                : deviation > 5
                ? 'Monitor closely — elevated demand pattern'
                : 'No action needed — within expected range'}
            </p>
          </div>
        </div>

        {/* Residual chart */}
        <div className="card card-pad">
          <h3 className="section-title mb-1">Forecast vs Actual — Residuals</h3>
          <p className="section-subtitle mb-4">
            Residual = Actual − Forecast · positive spikes indicate surge
          </p>
          <ResidualChart data={residualData} currentResidual={deviation} currentMonth={CURRENT_MONTH} />
        </div>
      </div>

      {/* Surge timeline */}
      <div className="card card-pad">
        <h3 className="section-title mb-1">Surge Detection Timeline</h3>
        <p className="section-subtitle mb-4">From normal operation to confirmed response</p>
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {stages.map((s, i) => (
            <div key={s.stage} className="flex items-center gap-1 flex-shrink-0">
              <div
                className="flex flex-col items-center text-center px-3 py-3 rounded-lg min-w-[100px]"
                style={{
                  backgroundColor: i <= (deviation > 20 ? 3 : deviation > 5 ? 2 : deviation > 0 ? 1 : 0) ? `${s.color}15` : '#f8fafc',
                  border: i <= (deviation > 20 ? 3 : deviation > 5 ? 2 : deviation > 0 ? 1 : 0) ? `1px solid ${s.color}40` : '1px solid #e2e8f0',
                }}
              >
                <div className="w-7 h-7 rounded-full flex items-center justify-center mb-1" style={{ backgroundColor: s.color }}>
                  {i === 0 && <CheckCircle className="w-4 h-4 text-white" />}
                  {i === 1 && <Activity className="w-4 h-4 text-white" />}
                  {i === 2 && <AlertTriangle className="w-4 h-4 text-white" />}
                  {i === 3 && <AlertTriangle className="w-4 h-4 text-white" />}
                  {i === 4 && <Zap className="w-4 h-4 text-white" />}
                </div>
                <span className="text-xs font-medium" style={{ color: s.color }}>{s.stage}</span>
              </div>
              {i < stages.length - 1 && <ArrowRight className="w-4 h-4 text-slate-300 flex-shrink-0" />}
            </div>
          ))}
        </div>
      </div>

      {/* Recommended action */}
      {deviation > 10 && (
        <div className="card card-pad border-l-4 border-l-red-500 bg-red-50">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-red-700">Recommended Action</h3>
              <p className="text-sm text-slate-700 mt-1">
                Increase allocation priority for {selectedDistrict} — surge detected with +{deviation} deviation
              </p>
            </div>
            <button onClick={() => navigate('/allocation')} className="btn-primary whitespace-nowrap">
              Open Allocation Console <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
