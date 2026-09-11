import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend,
  ResponsiveContainer, ReferenceLine, Area, ComposedChart,
} from 'recharts';
import type { DistrictForecast } from '../services/types';

interface ForecastChartProps {
  forecast: DistrictForecast;
}

export function ForecastChart({ forecast }: ForecastChartProps) {
  const histData = forecast.history.map((h) => ({
    month: h.month,
    Actual: h.actual,
    Forecast: h.forecast,
    Capacity: h.capacity,
  }));

  const futureData = forecast.future.map((f) => ({
    month: f.month,
    Forecast: f.forecast,
    Lower: f.lower,
    Upper: f.upper,
    Capacity: forecast.history[0]?.capacity ?? 0,
  }));

  const combined = [
    ...histData.map((d) => ({ ...d, Lower: null as number | null, Upper: null as number | null })),
    ...futureData.map((d) => ({ ...d, Actual: null as number | null })),
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={combined} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <defs>
          <linearGradient id="confBand" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: '#64748b' }}
          label={{ value: 'Month', position: 'insideBottom', offset: -5, style: { fontSize: 11, fill: '#94a3b8' } }}
        />
        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
        <RTooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
          labelStyle={{ fontWeight: 600 }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area dataKey="Upper" stroke="none" fill="url(#confBand)" name="Upper bound" />
        <Area dataKey="Lower" stroke="none" fill="#ffffff" name="Lower bound" />
        <ReferenceLine x={35} stroke="#cbd5e1" strokeDasharray="4 4" label={{ value: 'Now', style: { fontSize: 10, fill: '#94a3b8' } }} />
        <Line dataKey="Actual" stroke="#0d9488" strokeWidth={2} dot={false} name="Actual" connectNulls={false} />
        <Line dataKey="Forecast" stroke="#2563eb" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Forecast" connectNulls />
        <Line dataKey="Capacity" stroke="#dc2626" strokeWidth={1.5} dot={false} name="Capacity" strokeDasharray="2 2" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
