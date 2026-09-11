import { useNavigate } from 'react-router-dom';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { RiskBadge } from './RiskBadge';
import type { DistrictForecast } from '../services/types';
import { DISTRICTS } from '../services/mockData';

interface DistrictCardProps {
  forecast: DistrictForecast;
}

export function DistrictCard({ forecast }: DistrictCardProps) {
  const navigate = useNavigate();
  const d = DISTRICTS.find((x) => x.id === forecast.districtId)!;
  const gap = forecast.currentForecast - d.nominalCapacity;
  const sparkData = forecast.history.slice(-12).map((h) => ({ v: h.actual }));

  return (
    <div
      onClick={() => navigate(`/districts/${forecast.districtId}`)}
      className="card card-pad hover:shadow-md hover:border-brand-300 cursor-pointer transition-all"
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="font-semibold text-slate-900">{forecast.districtId}</span>
          <span className="text-xs text-slate-400 ml-1">{d.name}</span>
        </div>
        <RiskBadge risk={forecast.risk} />
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs text-slate-400">Forecast / Capacity</p>
          <p className="text-sm font-medium tabular-nums">
            <span className="text-slate-900">{forecast.currentForecast}</span>
            <span className="text-slate-400"> / {d.nominalCapacity}</span>
          </p>
          <p className={`text-xs font-medium ${gap > 0 ? 'text-red-600' : 'text-green-600'}`}>
            Gap: {gap > 0 ? `+${gap}` : gap}
          </p>
        </div>
        <div className="w-20 h-12">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparkData}>
              <Line type="monotone" dataKey="v" stroke="#2563eb" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
