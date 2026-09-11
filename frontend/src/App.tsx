import { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import Dashboard from './pages/Dashboard';
import Forecast from './pages/Forecast';
import Allocation from './pages/Allocation';
import SurgeMonitor from './pages/SurgeMonitor';
import DistrictDetail from './pages/DistrictDetail';
import Performance from './pages/Performance';
import Simulation from './pages/Simulation';
import Settings from './pages/Settings';
import DistrictsList from './pages/DistrictsList';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/allocation" element={<Allocation />} />
            <Route path="/surge-monitor" element={<SurgeMonitor />} />
            <Route path="/districts" element={<DistrictsList />} />
            <Route path="/districts/:id" element={<DistrictDetail />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="/simulation" element={<Simulation />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
