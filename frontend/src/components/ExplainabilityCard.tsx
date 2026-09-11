import { ProgressBar } from './ProgressBar';
import type { Allocation } from '../services/types';

interface ExplainabilityCardProps {
  allocation: Allocation;
}

export function ExplainabilityCard({ allocation }: ExplainabilityCardProps) {
  const factors = [
    { key: 'shortageRisk', label: 'Shortage Risk', color: '#dc2626' },
    { key: 'demandGap', label: 'Demand Gap', color: '#ea580c' },
    { key: 'surgeSignal', label: 'Surge Signal', color: '#2563eb' },
    { key: 'fairnessPriority', label: 'Fairness Priority', color: '#0d9488' },
  ];

  return (
    <div className="card card-pad">
      <h4 className="text-sm font-semibold text-slate-900 mb-1">
        Why did {allocation.districtId} receive {allocation.reserve} units?
      </h4>
      <p className="text-xs text-slate-500 mb-4">{allocation.reason}</p>
      <div className="space-y-3">
        {factors.map((f) => {
          const val = allocation.factors[f.key as keyof typeof allocation.factors];
          return (
            <ProgressBar
              key={f.key}
              label={f.label}
              value={Math.min(1, val)}
              color={f.color}
            />
          );
        })}
      </div>
    </div>
  );
}
