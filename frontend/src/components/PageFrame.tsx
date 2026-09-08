import React from 'react';
import { use3DTilt } from '../hooks/use3DTilt';

type Tone = 'emerald' | 'pink' | 'cyan' | 'amber' | 'violet';

const toneMap: Record<Tone, { ring: string; glow: string; accent: string }> = {
  emerald: { ring: 'border-emerald-500/20', glow: 'shadow-[0_24px_90px_rgba(16,185,129,0.15)]', accent: 'text-emerald-400' },
  pink: { ring: 'border-pink-500/20', glow: 'shadow-[0_24px_90px_rgba(236,72,153,0.15)]', accent: 'text-pink-400' },
  cyan: { ring: 'border-cyan-500/20', glow: 'shadow-[0_24px_90px_rgba(34,211,238,0.15)]', accent: 'text-cyan-400' },
  amber: { ring: 'border-amber-500/20', glow: 'shadow-[0_24px_90px_rgba(245,158,11,0.15)]', accent: 'text-amber-400' },
  violet: { ring: 'border-violet-500/20', glow: 'shadow-[0_24px_90px_rgba(139,92,246,0.15)]', accent: 'text-violet-400' },
};

export const PageFrame: React.FC<{
  eyebrow?: string;
  title: string;
  subtitle?: string;
  tone?: Tone;
  rightSlot?: React.ReactNode;
  children?: React.ReactNode;
}> = ({ eyebrow, title, subtitle, tone = 'emerald', rightSlot, children }) => {
  const t = toneMap[tone];
  const frameTilt = use3DTilt<HTMLDivElement>({ maxTilt: 4, scale: 1.002 });

  return (
    <section 
      ref={frameTilt.ref as any}
      style={frameTilt.style}
      onMouseMove={frameTilt.onMouseMove as any}
      onMouseLeave={frameTilt.onMouseLeave as any}
      className={`premium-panel rounded-[2.5rem] ${t.ring} ${t.glow} overflow-hidden relative card-3d`}
    >
      <div className="card-3d-shine" />
      <div className={`absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-transparent ${tone === 'pink' ? 'via-pink-500/60' : tone === 'cyan' ? 'via-cyan-500/60' : tone === 'amber' ? 'via-amber-500/60' : tone === 'violet' ? 'via-violet-500/60' : 'via-emerald-500/60'} to-transparent`} />
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 p-6 md:p-8 card-3d-elevate-sm">
        <div className="space-y-2">
          {eyebrow && <p className={`text-[10px] font-black uppercase tracking-[0.35em] ${t.accent}`}>{eyebrow}</p>}
          <h1 className="text-3xl md:text-5xl font-black italic tracking-tighter text-white uppercase">{title}</h1>
          {subtitle && <p className="max-w-2xl text-sm text-slate-300 leading-relaxed font-medium">{subtitle}</p>}
        </div>
        {rightSlot && <div className="shrink-0">{rightSlot}</div>}
      </div>
      {children && <div className="px-6 md:px-8 pb-6 md:pb-8">{children}</div>}
    </section>
  );
};

export const InfoCard: React.FC<{
  title: string;
  detail?: string;
  tone?: Tone;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}> = ({ title, detail, tone = 'emerald', icon, children }) => {
  const t = toneMap[tone];
  const cardTilt = use3DTilt<HTMLDivElement>({ maxTilt: 6 });

  return (
    <div 
      ref={cardTilt.ref as any}
      style={cardTilt.style}
      onMouseMove={cardTilt.onMouseMove as any}
      onMouseLeave={cardTilt.onMouseLeave as any}
      className={`premium-panel rounded-3xl ${t.ring} p-5 relative overflow-hidden card-3d`}
    >
      <div className="card-3d-shine" />
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className={`text-[10px] font-black uppercase tracking-[0.3em] ${t.accent}`}>{title}</p>
          {detail && <p className="mt-2 text-xs font-semibold text-slate-300 leading-relaxed">{detail}</p>}
        </div>
        {icon}
      </div>
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
};
