interface ProgressBarProps {
  value: number; // 0..1
  label?: string;
  color?: string;
  showValue?: boolean;
  height?: 'sm' | 'md';
}

export function ProgressBar({ value, label, color = '#2563eb', showValue = true, height = 'md' }: ProgressBarProps) {
  const h = height === 'sm' ? 'h-1.5' : 'h-2.5';
  return (
    <div>
      {label && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-slate-600">{label}</span>
          {showValue && <span className="text-xs font-medium text-slate-900 tabular-nums">{Math.round(value * 100)}%</span>}
        </div>
      )}
      <div className={`${h} bg-slate-100 rounded-full overflow-hidden`}>
        <div
          className={`h-full rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(100, Math.max(0, value * 100))}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
