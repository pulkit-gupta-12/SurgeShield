import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number | null;
  suffix?: string;
  progress?: number; // 0..1
  tooltip?: string;
  isDemo?: boolean;
}

export function MetricCard({ icon: Icon, label, value, suffix, progress, tooltip, isDemo }: MetricCardProps) {
  return (
    <div className="card card-pad" title={tooltip}>
      <div className="flex items-center gap-3 mb-3">
        <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center">
          <Icon className="w-4.5 h-4.5 text-brand-600" />
        </div>
        <p className="text-sm font-medium text-slate-600">{label}</p>
      </div>
      <div className="flex items-baseline gap-2">
        {value === null ? (
          <span className="text-lg font-semibold text-slate-400">Awaiting evaluation</span>
        ) : (
          <span className="text-2xl font-bold text-slate-900 tabular-nums">
            {value}
            {suffix && <span className="text-base font-normal text-slate-400 ml-1">{suffix}</span>}
          </span>
        )}
        {isDemo && (
          <span className="badge bg-blue-50 text-blue-600 text-[10px]">Demo</span>
        )}
      </div>
      {progress !== undefined && (
        <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, progress * 100)}%` }}
          />
        </div>
      )}
    </div>
  );
}
