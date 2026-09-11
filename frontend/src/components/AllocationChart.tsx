import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, ResponsiveContainer, Cell,
} from 'recharts';
import type { Allocation } from '../services/types';
import { riskColor } from './RiskBadge';
import { getDistrictForecast } from '../services/mockData';

interface AllocationChartProps {
  allocations: Allocation[];
}

export function AllocationChart({ allocations }: AllocationChartProps) {
  const data = allocations.map((a) => ({
    district: a.districtId,
    allocation: a.reserve,
    risk: getDistrictForecast(a.districtId).risk,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} label={{ value: 'Reserve Units', position: 'insideBottom', offset: -5, style: { fontSize: 11, fill: '#94a3b8' } }} />
        <YAxis type="category" dataKey="district" tick={{ fontSize: 11, fill: '#64748b' }} width={40} />
        <RTooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
          formatter={(v: number) => [`${v} units`, 'Allocation']}
        />
        <Bar dataKey="allocation" radius={[0, 4, 4, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={riskColor(d.risk)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
