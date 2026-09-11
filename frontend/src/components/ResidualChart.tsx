import {
  ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts';

interface ResidualChartProps {
  data: { month: number; actual: number; forecast: number; residual: number }[];
  currentResidual?: number;
  currentMonth?: number;
}

export function ResidualChart({ data, currentResidual, currentMonth }: ResidualChartProps) {
  const combined = [
    ...data,
    ...(currentResidual !== undefined && currentMonth !== undefined
      ? [{ month: currentMonth, actual: 0, forecast: 0, residual: currentResidual }]
      : []),
  ];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={combined} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: '#64748b' }}
          label={{ value: 'Month', position: 'insideBottom', offset: -5, style: { fontSize: 11, fill: '#94a3b8' } }}
        />
        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
        <RTooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <ReferenceLine y={0} stroke="#cbd5e1" />
        <Bar dataKey="residual" name="Residual" radius={[3, 3, 0, 0]}>
          {combined.map((d, i) => (
            <Cell key={i} fill={d.residual > 15 ? '#dc2626' : d.residual > 5 ? '#ea580c' : d.residual < -10 ? '#3b82f6' : '#cbd5e1'} />
          ))}
        </Bar>
      </ComposedChart>
    </ResponsiveContainer>
  );
}


