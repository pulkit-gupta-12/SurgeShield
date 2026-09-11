import { Settings as SettingsIcon, Database, Bell, Shield, Info } from 'lucide-react';

export default function Settings() {
  return (
    <div className="p-4 lg:p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">System configuration and preferences</p>
      </div>

      <div className="card card-pad space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Database className="w-4 h-4 text-slate-400" />
          <h3 className="section-title">Data Source</h3>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-700">Mock Data Layer</p>
            <p className="text-xs text-slate-400">Currently using deterministic mock data. Connect FastAPI backend to use real forecasts.</p>
          </div>
          <span className="badge bg-amber-100 text-amber-700">Active</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-700">API Endpoint</p>
            <p className="text-xs text-slate-400">Set VITE_API_URL in .env to connect backend</p>
          </div>
          <span className="badge bg-slate-100 text-slate-500">Not configured</span>
        </div>
      </div>

      <div className="card card-pad space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-4 h-4 text-slate-400" />
          <h3 className="section-title">System Parameters</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-slate-500">Reserve Capacity</p>
            <p className="text-sm font-semibold text-slate-900">60 units</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Districts</p>
            <p className="text-sm font-semibold text-slate-900">12</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Historical Months</p>
            <p className="text-sm font-semibold text-slate-900">36 (t=0–35)</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Forecast Horizon</p>
            <p className="text-sm font-semibold text-slate-900">6 (t=36–41)</p>
          </div>
        </div>
      </div>

      <div className="card card-pad">
        <div className="flex items-center gap-2 mb-2">
          <Info className="w-4 h-4 text-slate-400" />
          <h3 className="section-title">About SurgeShield</h3>
        </div>
        <p className="text-sm text-slate-600">
          SurgeShield is a decision-support system for healthcare capacity planning and surge response.
          It connects forecasting, risk estimation, constrained allocation, online surge detection,
          fairness and evaluation into one sequential decision system.
        </p>
        <p className="text-xs text-slate-400 mt-2">
          HC-05: District Health Surge Forecast and Allocation · Demo/Simulation mode
        </p>
      </div>
    </div>
  );
}
