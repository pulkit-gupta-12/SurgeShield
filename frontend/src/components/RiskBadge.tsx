import type { RiskLevel } from '../services/types';

const riskStyles: Record<RiskLevel, { bg: string; text: string; dot: string }> = {
  Low:      { bg: 'bg-risk-low-bg',      text: 'text-risk-low',      dot: 'bg-risk-low' },
  Medium:   { bg: 'bg-risk-medium-bg',   text: 'text-risk-medium',   dot: 'bg-risk-medium' },
  High:     { bg: 'bg-risk-high-bg',     text: 'text-risk-high',     dot: 'bg-risk-high' },
  Critical: { bg: 'bg-risk-critical-bg', text: 'text-risk-critical', dot: 'bg-risk-critical' },
};

export function RiskBadge({ risk, size = 'sm' }: { risk: RiskLevel; size?: 'sm' | 'md' }) {
  const s = riskStyles[risk];
  const padding = size === 'md' ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs';
  return (
    <span className={`badge ${s.bg} ${s.text} ${padding}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {risk}
    </span>
  );
}

export function riskColor(risk: RiskLevel): string {
  switch (risk) {
    case 'Low': return '#16a34a';
    case 'Medium': return '#ca8a04';
    case 'High': return '#ea580c';
    case 'Critical': return '#dc2626';
  }
}
