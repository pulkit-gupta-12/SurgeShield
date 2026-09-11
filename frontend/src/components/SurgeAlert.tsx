import { AlertTriangle, ArrowRight } from 'lucide-react';
import { RiskBadge, riskColor } from './RiskBadge';
import type { SurgeAlert as SurgeAlertType } from '../services/types';

interface SurgeAlertProps {
  alert: SurgeAlertType;
}

const stageColors: Record<string, string> = {
  Normal: '#16a34a',
  Elevated: '#ca8a04',
  Anomaly: '#ea580c',
  'Confirmed Surge': '#dc2626',
  Response: '#2563eb',
};

export function SurgeAlertCard({ alert }: SurgeAlertProps) {
  const color = riskColor(alert.risk);
  const stageColor = stageColors[alert.stage] ?? '#64748b';

  return (
    <div className="card card-pad border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-slate-900">{alert.districtId}</span>
            <RiskBadge risk={alert.risk} size="md" />
          </div>
          <p className="text-xs text-slate-400 mt-0.5">{alert.timestamp}</p>
        </div>
        <div className="flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4" style={{ color }} />
          <span className="text-xs font-semibold" style={{ color: stageColor }}>{alert.stage}</span>
        </div>
      </div>

      {/* Risk bar */}
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-3">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: alert.risk === 'Critical' ? '100%' : alert.risk === 'High' ? '75%' : alert.risk === 'Medium' ? '50%' : '25%',
            backgroundColor: color,
          }}
        />
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-xs text-slate-400">Expected</p>
          <p className="font-medium tabular-nums text-slate-700">{alert.expectedDemand}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Observed</p>
          <p className="font-medium tabular-nums text-slate-900">{alert.observedDemand}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Deviation</p>
          <p className="font-medium tabular-nums" style={{ color: alert.deviation > 10 ? '#dc2626' : '#64748b' }}>
            {alert.deviation > 0 ? '+' : ''}{alert.deviation}
          </p>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-100">
        <p className="text-xs text-slate-400">Recommended response</p>
        <p className="text-sm text-slate-700 mt-0.5 flex items-center gap-1">
          {alert.recommendedResponse}
          <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
        </p>
      </div>
    </div>
  );
}
