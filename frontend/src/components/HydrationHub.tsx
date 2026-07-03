
import React, { useState, useEffect } from 'react';
import { Droplets, GlassWater, Plus, RotateCcw, Check } from 'lucide-react';

const TODAY_KEY = 'smarty_hydration_date';
const ML_KEY = 'smarty_hydration_ml';

const HydrationHub: React.FC = () => {
    const [ml, setMl] = useState(() => {
        const savedDate = localStorage.getItem(TODAY_KEY);
        const today = new Date().toDateString();
        if (savedDate !== today) {
            localStorage.setItem(TODAY_KEY, today);
            localStorage.setItem(ML_KEY, '0');
            return 0;
        }
        return Number(localStorage.getItem(ML_KEY) || 0);
    });
    const [confirmReset, setConfirmReset] = useState(false);
    const goal = 3000;
    const percentage = Math.min(100, (ml / goal) * 100);
    const liters = (ml / 1000).toFixed(1);
    const goalLiters = (goal / 1000).toFixed(1);

    useEffect(() => {
        localStorage.setItem(ML_KEY, ml.toString());
        localStorage.setItem(TODAY_KEY, new Date().toDateString());
    }, [ml]);

    const addWater = (amount: number) => {
        setMl(prev => prev + amount);
        setConfirmReset(false);
    };

    const handleReset = () => {
        if (confirmReset) {
            setMl(0);
            setConfirmReset(false);
        } else {
            setConfirmReset(true);
        }
    };

    return (
        <div className="p-6 bg-slate-900 border border-white/10 rounded-3xl relative overflow-hidden group">
            {/* Liquid Background Animation */}
            <div
                className="absolute bottom-0 left-0 w-full bg-blue-500/10 transition-all duration-1000 ease-out"
                style={{ height: `${percentage}%` }}
            />

            <div className="relative z-10">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <Droplets size={18} className="text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs font-black text-white uppercase tracking-widest leading-none">Hydration Hub</p>
                            <p className="text-[9px] text-slate-500 mt-1">
                                {liters}L / {goalLiters}L &bull; {ml}ml / {goal}ml
                            </p>
                        </div>
                    </div>

                    {/* Inline Reset Confirmation */}
                    {confirmReset ? (
                        <div className="flex items-center space-x-2">
                            <span className="text-[9px] text-rose-400 font-black uppercase">Reset?</span>
                            <button
                                onClick={handleReset}
                                className="p-1.5 bg-rose-500/20 hover:bg-rose-500/30 rounded-lg text-rose-400 transition"
                                title="Confirm reset"
                            >
                                <Check size={12} />
                            </button>
                            <button
                                onClick={() => setConfirmReset(false)}
                                className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-400 transition"
                                title="Cancel"
                            >
                                <Plus size={12} className="rotate-45" />
                            </button>
                        </div>
                    ) : (
                        <button onClick={handleReset} className="p-1.5 hover:bg-white/5 rounded-lg text-slate-600 hover:text-white transition">
                            <RotateCcw size={14} />
                        </button>
                    )}
                </div>

                <div className="flex flex-col items-center justify-center py-2">
                    <div className="relative w-20 h-20 border-4 border-slate-800 rounded-full flex items-center justify-center">
                        <span className="text-xl font-black text-white">{Math.round(percentage)}%</span>
                        <svg className="absolute inset-0 w-full h-full -rotate-90">
                            <circle
                                cx="40" cy="40" r="36"
                                fill="none" stroke="currentColor" strokeWidth="4"
                                className="text-blue-500"
                                strokeDasharray={226}
                                strokeDashoffset={226 - (226 * percentage) / 100}
                                style={{ transition: 'stroke-dashoffset 1s ease-out' }}
                            />
                        </svg>
                    </div>
                    {percentage >= 100 && (
                        <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest mt-2 animate-pulse">
                            🎯 Goal Reached!
                        </p>
                    )}
                </div>

                <div className="grid grid-cols-3 gap-1.5 mt-4">
                    <button
                        onClick={() => addWater(100)}
                        className="flex items-center justify-center space-x-1 py-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 text-[9px] font-black uppercase tracking-widest hover:bg-blue-500/20 transition"
                    >
                        <GlassWater size={11} />
                        <span>+100</span>
                    </button>
                    <button
                        onClick={() => addWater(250)}
                        className="flex items-center justify-center space-x-1 py-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 text-[9px] font-black uppercase tracking-widest hover:bg-blue-500/20 transition"
                    >
                        <GlassWater size={11} />
                        <span>+250</span>
                    </button>
                    <button
                        onClick={() => addWater(500)}
                        className="flex items-center justify-center space-x-1 py-2.5 bg-blue-500 text-slate-950 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-blue-400 transition"
                    >
                        <Plus size={11} />
                        <span>+500</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default HydrationHub;
