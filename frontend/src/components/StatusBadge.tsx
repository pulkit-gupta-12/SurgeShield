type StatusType = 'active' | 'idle' | 'warning' | 'demo';

const styles: Record<StatusType, { bg: string; text: string; label: string }> = {
  active:  { bg: 'bg-green-100', text: 'text-green-700', label: 'Active' },
  idle:    { bg: 'bg-slate-100', text: 'text-slate-600', label: 'Idle' },
  warning: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Warning' },
  demo:    { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Demo' },
};

export function StatusBadge({ status, label }: { status: StatusType; label?: string }) {
  const s = styles[status];
  return (
    <span className={`badge ${s.bg} ${s.text}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      {label ?? s.label}
    </span>
  );
}
