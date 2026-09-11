import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, TrendingUp, Scale, Activity, MapPin,
  Gauge, FlaskConical, Settings, Shield,
} from 'lucide-react';

const navItems = [
  { to: '/dashboard',     icon: LayoutDashboard, label: 'Overview' },
  { to: '/forecast',       icon: TrendingUp,      label: 'Forecasting' },
  { to: '/allocation',    icon: Scale,           label: 'Allocation' },
  { to: '/surge-monitor', icon: Activity,        label: 'Surge Monitor' },
  { to: '/districts',      icon: MapPin,          label: 'Districts' },
  { to: '/performance',   icon: Gauge,           label: 'Performance' },
  { to: '/simulation',     icon: FlaskConical,    label: 'What-If Simulator' },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div className="fixed inset-0 bg-slate-900/40 z-30 lg:hidden" onClick={onClose} />
      )}

      <aside className={`
        fixed lg:static inset-y-0 left-0 z-40
        w-64 bg-white border-r border-slate-200 flex flex-col
        transform transition-transform duration-200
        ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-slate-200">
          <div className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-slate-900 leading-tight tracking-tight">SURGESHIELD</p>
            <p className="text-[10px] text-slate-400 leading-tight">Forecast → Allocate → Adapt</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) => `
                flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors
                ${isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}
              `}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </NavLink>
          ))}
          <NavLink
            to="/settings"
            onClick={onClose}
            className={({ isActive }) => `
              flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors mt-4
              ${isActive
                ? 'bg-brand-50 text-brand-700'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}
            `}
          >
            <Settings className="w-4 h-4 flex-shrink-0" />
            Settings
          </NavLink>
        </nav>

        {/* Bottom section */}
        <div className="border-t border-slate-200 p-3 space-y-2">
          <div className="flex items-center gap-2 px-2 py-1.5">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs text-slate-600">System operational</span>
          </div>
          <div className="flex items-center gap-2 px-2 py-1.5 bg-amber-50 rounded-md">
            <span className="badge bg-amber-100 text-amber-700 text-[10px]">DEMO</span>
            <span className="text-[10px] text-slate-500">Simulation data</span>
          </div>
          <div className="flex items-center gap-2.5 px-2 py-2 hover:bg-slate-50 rounded-md cursor-pointer">
            <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 text-xs font-semibold">
              OP
            </div>
            <div>
              <p className="text-xs font-medium text-slate-700">Ops Planner</p>
              <p className="text-[10px] text-slate-400">Health Authority</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
