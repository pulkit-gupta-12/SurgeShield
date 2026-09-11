import type { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  sublabel?: string;
  accent?: 'blue' | 'teal' | 'green' | 'amber' | 'orange' | 'red' | 'slate';
  tooltip?: string;
}

const accentMap = {
  blue:   { bg: 'bg-brand-50',  text: 'text-brand-600' },
  teal:   { bg: 'bg-teal-50',   text: 'text-teal-600' },
  green:  { bg: 'bg-green-50',  text: 'text-green-600' },
  amber:  { bg: 'bg-amber-50',  text: 'text-amber-600' },
  orange: { bg: 'bg-orange-50', text: 'text-orange-600' },
  red:    { bg: 'bg-red-50',    text: 'text-red-600' },
  slate:  { bg: 'bg-slate-100', text: 'text-slate-600' },
};

export function KpiCard({ icon: Icon, label, value, sublabel, accent = 'blue', tooltip }: KpiCardProps) {
  const a = accentMap[accent];
  return (
    <div className="card card-pad hover:shadow-md transition-shadow" title={tooltip}>
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
          <p className="mt-1 text-2xl font-bold text-slate-900 tabular-nums">{value}</p>
          {sublabel && <p className="mt-0.5 text-xs text-slate-400">{sublabel}</p>}
        </div>
        <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${a.bg}`}>
          <Icon className={`w-5 h-5 ${a.text}`} />
        </div>
      </div>
    </div>
  );
}
