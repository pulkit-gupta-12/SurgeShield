import { Scale, TrendingUp, AlertTriangle, Users, Zap } from 'lucide-react';
import type { AllocationPolicy } from '../services/types';

interface PolicySelectorProps {
  selected: AllocationPolicy;
  onChange: (policy: AllocationPolicy) => void;
}

const policies: { name: AllocationPolicy; icon: typeof Scale; desc: string }[] = [
  { name: 'Equal Split', icon: Scale, desc: 'Distribute reserve equally across all districts' },
  { name: 'Forecast Only', icon: TrendingUp, desc: 'Allocate proportional to forecast demand gap' },
  { name: 'Risk Based', icon: AlertTriangle, desc: 'Prioritize districts with highest shortage risk' },
  { name: 'Fairness Aware', icon: Users, desc: 'Balance risk reduction with equitable service' },
  { name: 'Surge Adaptive', icon: Zap, desc: 'Re-allocate dynamically when surge is detected' },
];

export function PolicySelector({ selected, onChange }: PolicySelectorProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
      {policies.map((p) => {
        const isActive = p.name === selected;
        return (
          <button
            key={p.name}
            onClick={() => onChange(p.name)}
            className={`card card-pad text-left transition-all ${
              isActive
                ? 'border-brand-500 ring-2 ring-brand-200 bg-brand-50'
                : 'hover:border-slate-300 hover:shadow-md'
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${
              isActive ? 'bg-brand-100' : 'bg-slate-100'
            }`}>
              <p.icon className={`w-4 h-4 ${isActive ? 'text-brand-600' : 'text-slate-500'}`} />
            </div>
            <p className={`text-sm font-semibold ${isActive ? 'text-brand-700' : 'text-slate-700'}`}>
              {p.name}
            </p>
            <p className="text-xs text-slate-400 mt-1">{p.desc}</p>
          </button>
        );
      })}
    </div>
  );
}
