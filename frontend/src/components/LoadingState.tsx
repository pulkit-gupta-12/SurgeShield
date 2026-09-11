import { Loader2 } from 'lucide-react';

export function LoadingState({ label = 'Loading...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
      <span className="ml-2 text-sm text-slate-500">{label}</span>
    </div>
  );
}
