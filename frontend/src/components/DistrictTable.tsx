import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { RiskBadge } from './RiskBadge';
import type { DistrictForecast, Allocation } from '../services/types';
import { DISTRICTS } from '../services/mockData';

interface DistrictTableProps {
  forecasts: DistrictForecast[];
  allocations?: Allocation[];
  showReserve?: boolean;
  showAllocation?: boolean;
  showBenefit?: boolean;
  showReason?: boolean;
  compact?: boolean;
}

export function DistrictTable({
  forecasts, allocations, showReserve, showAllocation, showBenefit, showReason, compact,
}: DistrictTableProps) {
  const navigate = useNavigate();

  const getAlloc = (id: string) => allocations?.find((a) => a.districtId === id);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left">
            <th className="py-2.5 px-3 font-semibold text-slate-600">District</th>
            <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Forecast</th>
            <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Capacity</th>
            <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Gap</th>
            {!compact && <th className="py-2.5 px-3 font-semibold text-slate-600">Risk</th>}
            {showReserve && <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Reserve</th>}
            {showAllocation && <th className="py-2.5 px-3 font-semibold text-slate-600 text-right">Allocation</th>}
            {showBenefit && <th className="py-2.5 px-3 font-semibold text-slate-600">Benefit</th>}
            {showReason && <th className="py-2.5 px-3 font-semibold text-slate-600">Reason</th>}
            {!compact && <th className="py-2.5 px-3"></th>}
          </tr>
        </thead>
        <tbody>
          {forecasts.map((f) => {
            const d = DISTRICTS.find((x) => x.id === f.districtId)!;
            const gap = f.currentForecast - d.nominalCapacity;
            const alloc = getAlloc(f.districtId);
            return (
              <tr
                key={f.districtId}
                onClick={() => navigate(`/districts/${f.districtId}`)}
                className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
              >
                <td className="py-2.5 px-3">
                  <span className="font-semibold text-slate-900">{f.districtId}</span>
                  <span className="text-slate-400 ml-1.5 text-xs">{d.name}</span>
                </td>
                <td className="py-2.5 px-3 text-right tabular-nums text-slate-700">{f.currentForecast}</td>
                <td className="py-2.5 px-3 text-right tabular-nums text-slate-700">{d.nominalCapacity}</td>
                <td className={`py-2.5 px-3 text-right tabular-nums font-medium ${gap > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {gap > 0 ? `+${gap}` : gap}
                </td>
                {!compact && (
                  <td className="py-2.5 px-3"><RiskBadge risk={f.risk} /></td>
                )}
                {showReserve && (
                  <td className="py-2.5 px-3 text-right tabular-nums font-medium text-brand-600">
                    {alloc?.reserve ?? 0}
                  </td>
                )}
                {showAllocation && (
                  <td className="py-2.5 px-3 text-right tabular-nums font-medium text-brand-600">
                    {alloc?.reserve ?? 0}
                  </td>
                )}
                {showBenefit && (
                  <td className="py-2.5 px-3">
                    <span className={`badge ${
                      alloc?.expectedBenefit === 'High' ? 'bg-red-50 text-red-600' :
                      alloc?.expectedBenefit === 'Medium' ? 'bg-amber-50 text-amber-600' :
                      'bg-green-50 text-green-600'
                    }`}>
                      {alloc?.expectedBenefit ?? '—'}
                    </span>
                  </td>
                )}
                {showReason && (
                  <td className="py-2.5 px-3 text-xs text-slate-500">{alloc?.reason ?? '—'}</td>
                )}
                {!compact && (
                  <td className="py-2.5 px-3 text-right">
                    <ChevronRight className="w-4 h-4 text-slate-300" />
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
