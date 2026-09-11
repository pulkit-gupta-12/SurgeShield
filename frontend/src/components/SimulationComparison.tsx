import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, ResponsiveContainer, Cell,
} from 'recharts';
import type { SimulationResult } from '../services/types';

interface SimulationComparisonProps {
  results: SimulationResult[];
  metric: 'totalUnmetDemand' | 'serviceUtility' | 'worstDistrictService';
  title: string;
}

const policyColors: Record<string, string> = {
  'Equal Split': '#64748b',
  'Forecast Only': '#0d9488',
  'Risk Based': '#ea580c',
  'Fairness Aware': '#2563eb',
  'Surge Adaptive': '#dc2626',
};

export function SimulationComparison({ results, metric, title }: SimulationComparisonProps) {
  const data = results.map((r) => ({
    policy: r.policy,
    value: metric === 'totalUnmetDemand' ? r.totalUnmetDemand : Math.round(r[metric] * 1000) / 10,
  }));

  return (
    <div className="card card-pad">
      <h4 className="text-sm font-semibold text-slate-900 mb-3">{title}</h4>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="policy" tick={{ fontSize: 10, fill: '#64748b' }} angle={-20} textAnchor="end" height={50} />
          <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
          <RTooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
            formatter={(v: number) => metric === 'totalUnmetDemand' ? [`${v} units`, title] : [`${v}%`, title]}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={policyColors[d.policy] ?? '#2563eb'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
