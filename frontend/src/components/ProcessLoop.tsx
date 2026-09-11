import { TrendingUp, BarChart3, AlertTriangle, Send, Eye, Gauge, RefreshCw } from 'lucide-react';

const steps = [
  { icon: TrendingUp,  label: 'Past Demand',     desc: 'Historical data' },
  { icon: BarChart3,   label: 'Forecast',         desc: 'Predict future demand' },
  { icon: AlertTriangle, label: 'Shortage Risk', desc: 'Assess capacity gap' },
  { icon: Send,        label: 'Allocate Reserve', desc: 'Distribute 60 units' },
  { icon: Eye,         label: 'Actual Demand',    desc: 'Observed at month end' },
  { icon: Gauge,       label: 'Unmet Demand',     desc: 'Measure shortfall' },
  { icon: RefreshCw,   label: 'Detect Surge',     desc: 'Anomaly detection' },
];

export function ProcessLoop() {
  return (
    <div className="card card-pad">
      <h3 className="section-title mb-1">Decision Loop</h3>
      <p className="section-subtitle mb-4">SurgeShield connects forecasting, risk, allocation, detection & evaluation into one sequential system</p>
      <div className="flex flex-wrap items-center gap-1">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-1">
            <div className="flex flex-col items-center text-center px-2 py-2 rounded-lg hover:bg-slate-50 transition-colors min-w-[80px]">
              <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center mb-1">
                <step.icon className="w-4 h-4 text-brand-600" />
              </div>
              <span className="text-xs font-medium text-slate-700">{step.label}</span>
              <span className="text-[10px] text-slate-400">{step.desc}</span>
            </div>
            {i < steps.length - 1 && (
              <span className="text-slate-300 text-lg">→</span>
            )}
          </div>
        ))}
        <span className="text-slate-300 text-lg">↻</span>
      </div>
    </div>
  );
}
