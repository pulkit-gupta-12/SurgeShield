import { useState, useEffect } from 'react';
import { Menu, Bell, Calendar, Shield, ChevronDown } from 'lucide-react';
import { CURRENT_MONTH, RESERVE_CAPACITY } from '../services/mockData';
import { apiGet } from '../services/api';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    apiGet<{ status: string }>('/api/health')
      .then((res) => {
        if (res?.status === 'ok') setIsLive(true);
      })
      .catch(() => setIsLive(false));
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-6 flex-shrink-0">
      <div className="flex items-center gap-3">
        <button onClick={onMenuClick} className="lg:hidden p-1.5 hover:bg-slate-100 rounded-md">
          <Menu className="w-5 h-5 text-slate-600" />
        </button>
        <div className="hidden sm:flex items-center gap-2">
          <span className="badge bg-brand-50 text-brand-700">
            <Shield className="w-3 h-3" />
            Surge Adaptive
          </span>
          <span className="text-slate-300">|</span>
          <span className="flex items-center gap-1.5 text-sm text-slate-600">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            Month {CURRENT_MONTH}
          </span>
          <span className="text-slate-300">|</span>
          <span className="flex items-center gap-1.5 text-sm text-slate-600">
            <span className="text-xs text-slate-400">Reserve:</span>
            <span className="font-semibold text-slate-900">{RESERVE_CAPACITY}</span>
            <span className="text-xs text-slate-400">units</span>
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {isLive ? (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 rounded-md border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-semibold text-emerald-700">LIVE API CONNECTED</span>
          </div>
        ) : (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 rounded-md border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span className="text-xs font-medium text-amber-700">MOCK FALLBACK LAYER</span>
          </div>
        )}
        <button className="relative p-1.5 hover:bg-slate-100 rounded-md">
          <Bell className="w-5 h-5 text-slate-600" />
          <span className="absolute top-1 right-1.5 w-2 h-2 rounded-full bg-red-500" />
        </button>
        <div className="flex items-center gap-2 cursor-pointer hover:bg-slate-50 px-2 py-1 rounded-md">
          <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 text-xs font-semibold">
            OP
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden sm:block" />
        </div>
      </div>
    </header>
  );
}
