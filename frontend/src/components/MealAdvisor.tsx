
import React from 'react';
import { ShieldCheck, Target, AlertCircle, TrendingUp, Info } from 'lucide-react';

interface MealAdvisorProps {
    feedback: {
        grade: string;
        message: string;
        distribution: { protein: number; carbs: number; fats: number };
    } | null;
    strategy: {
        remaining: { calories: number; protein: number; carbs: number; fats: number };
        strategy: string;
        is_budget_critical: boolean;
    } | null;
}

const MealAdvisor: React.FC<MealAdvisorProps> = ({ feedback, strategy }) => {
    if (!feedback && !strategy) return null;

    const getGradeColor = (grade: string) => {
        switch (grade) {
            case 'A': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
            case 'B': return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';
            case 'C': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
            case 'D':
            case 'E': return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
            default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
        }
    };

    return (
        <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col lg:flex-row gap-6">
                {/* Meal Feedback Card */}
                {feedback && (
                    <div className="flex-1 glass-panel p-8 rounded-[2.5rem] border border-white/5 relative overflow-hidden">
                        <div className={`absolute top-0 right-0 px-6 py-4 rounded-bl-[2rem] font-black text-2xl border-l border-b ${getGradeColor(feedback.grade)}`}>
                            GRADE {feedback.grade}
                        </div>

                        <div className="flex items-center space-x-3 mb-6">
                            <ShieldCheck className="text-emerald-400" size={20} />
                            <h3 className="text-sm font-black text-white uppercase tracking-widest">Neural Meal Analysis</h3>
                        </div>

                        <p className="text-sm text-slate-300 font-medium leading-relaxed mb-8 italic">
                            "{feedback.message}"
                        </p>

                        <div className="grid grid-cols-3 gap-4">
                            {[
                                { label: 'Protein', pct: feedback.distribution.protein, color: 'blue' },
                                { label: 'Carbs', pct: feedback.distribution.carbs, color: 'amber' },
                                { label: 'Fats', pct: feedback.distribution.fats, color: 'purple' },
                            ].map(m => (
                                <div key={m.label} className="text-center">
                                    <p className="text-[9px] font-black text-slate-500 uppercase mb-1">{m.label}</p>
                                    <p className={`text-sm font-black text-${m.color}-400`}>{m.pct}%</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Path Correction Strategy */}
                {strategy && (
                    <div className="flex-1 glass-panel p-8 rounded-[2.5rem] border border-cyan-500/20 bg-cyan-500/5">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center space-x-3">
                                <TrendingUp className="text-cyan-400" size={20} />
                                <h3 className="text-sm font-black text-white uppercase tracking-widest">Day Strategy Adjustment</h3>
                            </div>
                            {strategy.is_budget_critical && (
                                <span className="flex items-center text-[8px] font-black text-rose-400 uppercase tracking-widest bg-rose-500/10 px-2 py-1 rounded-full border border-rose-500/20">
                                    <AlertCircle size={10} className="mr-1" /> Budget Critical
                                </span>
                            )}
                        </div>

                        <div className="bg-slate-950/50 border border-cyan-500/10 p-5 rounded-2xl mb-6">
                            <p className="text-xs text-cyan-300 font-bold leading-relaxed">
                                <span className="text-cyan-500 mr-2 uppercase tracking-tighter">Plan Correction:</span>
                                {strategy.strategy}
                            </p>
                        </div>

                        <div className="space-y-3">
                            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Remaining Targets</p>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="p-3 bg-slate-900 rounded-xl flex justify-between items-center">
                                    <span className="text-[8px] font-black text-slate-500 uppercase">Energy</span>
                                    <span className="text-xs font-black text-white italic">{strategy.remaining.calories} kcal</span>
                                </div>
                                <div className="p-3 bg-slate-900 rounded-xl flex justify-between items-center">
                                    <span className="text-[8px] font-black text-slate-500 uppercase">Protein</span>
                                    <span className="text-xs font-black text-white italic">{strategy.remaining.protein}g</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {!strategy?.is_budget_critical && (
                <div className="px-8 py-4 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl flex items-center space-x-3">
                    <Target className="text-emerald-400 shrink-0" size={14} />
                    <p className="text-[10px] text-emerald-300 font-black uppercase tracking-widest">Adaptive planning synced. Recommendations updated in the library below.</p>
                </div>
            )}
        </div>
    );
};

export default MealAdvisor;
