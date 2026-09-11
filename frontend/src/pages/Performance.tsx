import {
  BarChart3, TrendingUp, Gauge, Shield, CheckCircle, Clock,
  Award, AlertCircle,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, Legend,
  ResponsiveContainer, Cell, ComposedChart, Line,
} from 'recharts';
import { MetricCard } from '../components/MetricCard';
import { ProgressBar } from '../components/ProgressBar';
import { Tooltip } from '../components/Tooltip';
import { getPerformanceMetrics, DISTRICTS } from '../services/mockData';
import { riskColor } from '../components/RiskBadge';
import { getDistrictForecast } from '../services/mockData';

export default function Performance() {
  const metrics = getPerformanceMetrics();

  const worstDistrict = metrics.districtService.reduce(
    (min, d) => d.service < min.service ? d : min,
    metrics.districtService[0],
  );

  const districtServiceData = metrics.districtService.map((d) => {
    const fc = getDistrictForecast(d.districtId);
    return {
      district: d.districtId,
      service: Math.round(d.service * 1000) / 10,
      risk: fc.risk,
    };
  });

  const unmetData = metrics.unmetDemandTimeline;

  const complianceChecks = [
    { label: 'Reserve constraint respected', passed: metrics.compliance.reserveConstraint, desc: 'Total allocation ≤ 60 units' },
    { label: 'Integer allocations', passed: metrics.compliance.integerAllocations, desc: 'All allocations are whole numbers' },
    { label: 'No future information leakage', passed: metrics.compliance.noFutureLeakage, desc: 'Forecast uses only past data' },
    { label: 'Reproducible configuration', passed: metrics.compliance.reproducibleConfig, desc: 'Deterministic results' },
  ];

  const timelineSteps = [
    'Month 36', 'Allocation', 'Actual demand', 'Evaluation',
    'Month 37', 'Allocation', 'Actual demand', 'Evaluation',
    '...',
  ];

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Performance & Evaluation</h1>
        <p className="text-sm text-slate-500 mt-1">
          HC-05 evaluation metrics — forecast utility, service, compliance
        </p>
      </div>

      {/* Main metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          icon={TrendingUp}
          label="Forecast Utility"
          value={null}
          tooltip="Measures forecast quality according to the competition metric."
          isDemo
        />
        <MetricCard
          icon={Gauge}
          label="Demand-Service Utility"
          value={metrics.demandServiceUtility !== null ? `${(metrics.demandServiceUtility * 100).toFixed(1)}%` : null}
          progress={metrics.demandServiceUtility ?? undefined}
          isDemo
        />
        <MetricCard
          icon={Award}
          label="Worst-District Service"
          value={metrics.worstDistrictService !== null ? `${(metrics.worstDistrictService * 100).toFixed(1)}%` : null}
          tooltip="Uworst: Service score of the worst-performing district."
          progress={metrics.worstDistrictService ?? undefined}
          isDemo
        />
      </div>

      {/* District service chart */}
      <div className="card card-pad">
        <h3 className="section-title mb-1">District Service Levels</h3>
        <p className="section-subtitle mb-4">
          Service score per district — worst performer highlighted
          <Tooltip content="Service level = min(1, effective capacity / observed demand). Lower bars indicate worse service." />
        </p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={districtServiceData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="district" tick={{ fontSize: 11, fill: '#64748b' }} />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} domain={[0, 100]} />
            <RTooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
              formatter={(v: number) => [`${v}%`, 'Service level']}
            />
            <Bar dataKey="service" radius={[4, 4, 0, 0]}>
              {districtServiceData.map((d, i) => (
                <Cell key={i} fill={d.district === worstDistrict.districtId ? '#dc2626' : d.service < 90 ? '#ea580c' : d.service < 95 ? '#ca8a04' : '#16a34a'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-3 flex items-center gap-2 text-sm">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="text-slate-600">
            Worst district: <span className="font-semibold text-red-600">{worstDistrict.districtId}</span> at {worstDistrict.service.toFixed(1)}% service
          </span>
        </div>
      </div>

      {/* Unmet demand chart */}
      <div className="card card-pad">
        <h3 className="section-title mb-1">Unmet Demand Timeline</h3>
        <p className="section-subtitle mb-4">
          Demand vs capacity vs reserve vs unmet demand — evaluation horizon
        </p>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={unmetData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }}
              label={{ value: 'Month', position: 'insideBottom', offset: -5, style: { fontSize: 11, fill: '#94a3b8' } }} />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
            <RTooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="demand" fill="#2563eb" name="Demand" radius={[3, 3, 0, 0]} />
            <Bar dataKey="capacity" fill="#0d9488" name="Capacity" radius={[3, 3, 0, 0]} />
            <Bar dataKey="reserve" fill="#ca8a04" name="Reserve" radius={[3, 3, 0, 0]} />
            <Bar dataKey="unmet" fill="#dc2626" name="Unmet" radius={[3, 3, 0, 0]} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Compliance panel */}
      <div className="card card-pad">
        <div className="flex items-center gap-2 mb-1">
          <Shield className="w-4 h-4 text-green-600" />
          <h3 className="section-title">Compliance Checks</h3>
        </div>
        <p className="section-subtitle mb-4">
          Design checks — not competition-certified results
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {complianceChecks.map((c) => (
            <div key={c.label} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
              <CheckCircle className={`w-5 h-5 flex-shrink-0 ${c.passed ? 'text-green-600' : 'text-red-500'}`} />
              <div>
                <p className="text-sm font-medium text-slate-800">{c.label}</p>
                <p className="text-xs text-slate-400">{c.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Evaluation timeline */}
      <div className="card card-pad">
        <div className="flex items-center gap-2 mb-1">
          <Clock className="w-4 h-4 text-slate-400" />
          <h3 className="section-title">Evaluation Timeline</h3>
        </div>
        <p className="section-subtitle mb-4">
          Sequential monthly evaluation: allocate → observe → evaluate → repeat
        </p>
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {timelineSteps.map((step, i) => (
            <div key={i} className="flex items-center gap-1 flex-shrink-0">
              <div className={`px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap ${
                step.startsWith('Month') ? 'bg-brand-50 text-brand-700' :
                step === 'Allocation' ? 'bg-teal-50 text-teal-700' :
                step === 'Actual demand' ? 'bg-amber-50 text-amber-700' :
                step === 'Evaluation' ? 'bg-green-50 text-green-700' :
                'bg-slate-100 text-slate-400'
              }`}>
                {step}
              </div>
              {i < timelineSteps.length - 1 && <span className="text-slate-300">→</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Runtime / reproducibility */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card card-pad">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-slate-400" />
            <h4 className="text-sm font-semibold text-slate-700">Runtime</h4>
          </div>
          <p className="text-sm text-slate-500">
            Awaiting backend connection. Runtime and resource usage will be reported here once the Python pipeline is connected.
          </p>
          <span className="badge bg-blue-50 text-blue-600 mt-2">Demo</span>
        </div>
        <div className="card card-pad">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="w-4 h-4 text-slate-400" />
            <h4 className="text-sm font-semibold text-slate-700">Reproducibility</h4>
          </div>
          <p className="text-sm text-slate-500">
            Mock data is deterministic (seeded). Backend will use fixed random seeds for full reproducibility.
          </p>
          <span className="badge bg-green-50 text-green-600 mt-2">Verified</span>
        </div>
      </div>
    </div>
  );
}
