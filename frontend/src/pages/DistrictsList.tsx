import { MapPin } from 'lucide-react';
import { DistrictCard } from '../components/DistrictCard';
import { getAllForecasts, DISTRICTS } from '../services/mockData';

export default function DistrictsList() {
  const forecasts = getAllForecasts();

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Districts</h1>
        <p className="text-sm text-slate-500 mt-1">
          {DISTRICTS.length} districts under monitoring — click any card for detailed analysis
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {forecasts.map((f) => (
          <DistrictCard key={f.districtId} forecast={f} />
        ))}
      </div>
    </div>
  );
}
