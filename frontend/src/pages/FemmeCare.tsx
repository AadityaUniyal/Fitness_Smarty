
import React, { useState, useEffect } from 'react';
import {
    Heart, Calendar, Zap, Moon, Thermometer, Flower2, ClipboardList,
    Info, CheckCircle2,
    Sparkles, Utensils, ChevronDown, ChevronUp
} from 'lucide-react';
import {
    PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';
import { fetchFemmeCareAdvice, logPeriod } from '../services/api';

interface PeriodLog {
    start_date: string;
    symptoms: string[];
    mood: string;
    flow_intensity: string;
}

const MOODS = ['Happy', 'Neutral', 'Anxious', 'Fatigued', 'Irritable', 'Energetic'];
const FLOWS = ['Light', 'Medium', 'Heavy'];
const SYMPTOMS_OPTIONS = ['Cramps', 'Bloating', 'Headache', 'Back Pain', 'Mood Swings', 'Fatigue', 'Nausea'];

const CYCLE_LENGTH = 28;

const computeCycleDay = (): number => {
    try {
        const logs: PeriodLog[] = JSON.parse(localStorage.getItem('smarty_period_log') || '[]');
        if (!logs.length) return 14; // default: mid-cycle
        const sorted = [...logs].sort((a, b) => new Date(b.start_date).getTime() - new Date(a.start_date).getTime());
        const lastStart = new Date(sorted[0].start_date);
        const now = new Date();
        const diffDays = Math.floor((now.getTime() - lastStart.getTime()) / (1000 * 60 * 60 * 24));
        return Math.max(1, Math.min(CYCLE_LENGTH, (diffDays % CYCLE_LENGTH) + 1));
    } catch {
        return 14;
    }
};

const FemmeCare: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [advice, setAdvice] = useState<any>(null);
    const [showLogModal, setShowLogModal] = useState(false);
    const [logDate, setLogDate] = useState(new Date().toISOString().split('T')[0]);
    const [logMood, setLogMood] = useState('Neutral');
    const [logFlow, setLogFlow] = useState('Medium');
    const [logSymptoms, setLogSymptoms] = useState<string[]>([]);
    const [saving, setSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [cycleDay, setCycleDay] = useState(computeCycleDay);
    const [expandedExercise, setExpandedExercise] = useState<number | null>(null);
    const user = JSON.parse(localStorage.getItem('smarty_user') || '{}');

    // UI Toggles State
    const [localOnlyMode, setLocalOnlyMode] = useState(false);
    const [menopauseMode, setMenopauseMode] = useState(false);
    const [pregnancyMode, setPregnancyMode] = useState(false);

    const loadData = async () => {
        setLoading(true);
        const data = await fetchFemmeCareAdvice(user.id || 'anonymous');
        setAdvice(data);
        if (data?.user_profile) {
            setLocalOnlyMode(!!data.user_profile.local_only);
            setMenopauseMode(!!data.user_profile.menopause_mode);
            setPregnancyMode(!!data.user_profile.pregnancy_mode);
        }
        setLoading(false);
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleToggleSetting = async (key: 'local_only' | 'menopause_mode' | 'pregnancy_mode', val: boolean) => {
        if (key === 'local_only') setLocalOnlyMode(val);
        if (key === 'menopause_mode') setMenopauseMode(val);
        if (key === 'pregnancy_mode') setPregnancyMode(val);

        // Update local settings copy
        const currentSettings = {
            local_only: key === 'local_only' ? val : localOnlyMode,
            menopause_mode: key === 'menopause_mode' ? val : menopauseMode,
            pregnancy_mode: key === 'pregnancy_mode' ? val : pregnancyMode,
            femmecare_enabled: true
        };

        // Submit settings change to backend
        try {
            const { updateFemmeCareSettings } = await import('../services/api');
            await updateFemmeCareSettings(user.id || 'anonymous', currentSettings);
            // Refresh insights and recommendations
            const data = await fetchFemmeCareAdvice(user.id || 'anonymous');
            setAdvice(data);
        } catch (e) {
            console.error("Failed to update FemmeCare settings:", e);
        }
    };

    const toggleSymptom = (s: string) => {
        setLogSymptoms(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);
    };

    const handleLogPeriod = async () => {
        setSaving(true);
        const entry: PeriodLog = {
            start_date: new Date(logDate).toISOString(),
            symptoms: logSymptoms,
            mood: logMood,
            flow_intensity: logFlow,
        };

        // Save to localStorage
        const prev: PeriodLog[] = JSON.parse(localStorage.getItem('smarty_period_log') || '[]');
        localStorage.setItem('smarty_period_log', JSON.stringify([entry, ...prev].slice(0, 24)));

        // Submit to backend ONLY if localOnlyMode is false
        if (!localOnlyMode) {
            await logPeriod(user.id || 'anonymous', entry);
        }

        // Recompute cycle day
        setCycleDay(computeCycleDay());

        setSaving(false);
        setSaveSuccess(true);
        setTimeout(() => {
            setSaveSuccess(false);
            setShowLogModal(false);
            loadData();
        }, 1200);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="relative">
                    <div className="w-16 h-16 border-4 border-pink-500/20 border-t-pink-500 rounded-full animate-spin"></div>
                    <Heart className="absolute inset-0 m-auto text-pink-500 animate-pulse" size={20} />
                </div>
            </div>
        );
    }

    const currentCycleLimit = advice?.learned_cycle_length || CYCLE_LENGTH;
    const data = [
        { name: 'Completed', value: cycleDay },
        { name: 'Remaining', value: Math.max(0, currentCycleLimit - cycleDay) },
    ];
    const COLORS = ['#db2777', '#fbcfe8'];

    const phaseColors: Record<string, string> = {
        'Menstrual': 'text-rose-400 bg-rose-400/10 border-rose-400/20',
        'Follicular': 'text-pink-400 bg-pink-400/10 border-pink-400/20',
        'Ovulatory': 'text-purple-400 bg-purple-400/10 border-purple-400/20',
        'Luteal': 'text-fuchsia-400 bg-fuchsia-400/10 border-fuchsia-400/20',
        'all': 'text-slate-400 bg-slate-400/10 border-slate-400/20'
    };

    return (
        <div className="space-y-8 pb-10">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <div className="flex items-center space-x-2 mb-2">
                        <Heart size={16} className="text-pink-500 fill-pink-500" />
                        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-pink-500/80">FemmeCare Module</span>
                    </div>
                    <h1 className="text-4xl font-black text-white italic tracking-tighter">
                        AURA <span className="text-pink-500">PINK</span>
                    </h1>
                    <p className="text-slate-400 text-sm mt-1">Bio-synchronized training and nutrition for peak hormonal health.</p>
                    
                    {/* Mode Toggle Controls */}
                    <div className="flex flex-wrap gap-4 mt-4">
                        <label className="flex items-center space-x-2 bg-slate-900 border border-white/5 px-4 py-2 rounded-xl cursor-pointer hover:border-pink-500/30">
                            <input 
                                type="checkbox" 
                                checked={menopauseMode} 
                                onChange={(e) => handleToggleSetting('menopause_mode', e.target.checked)} 
                                className="accent-pink-600 rounded" 
                            />
                            <span className="text-[10px] font-black text-white uppercase tracking-wider">Menopause Mode</span>
                        </label>
                        
                        <label className="flex items-center space-x-2 bg-slate-900 border border-white/5 px-4 py-2 rounded-xl cursor-pointer hover:border-pink-500/30">
                            <input 
                                type="checkbox" 
                                checked={pregnancyMode} 
                                onChange={(e) => handleToggleSetting('pregnancy_mode', e.target.checked)} 
                                className="accent-pink-600 rounded" 
                            />
                            <span className="text-[10px] font-black text-white uppercase tracking-wider">Pregnancy Safe Mode</span>
                        </label>
                        
                        <label className="flex items-center space-x-2 bg-slate-900 border border-white/5 px-4 py-2 rounded-xl cursor-pointer hover:border-pink-500/30">
                            <input 
                                type="checkbox" 
                                checked={localOnlyMode} 
                                onChange={(e) => handleToggleSetting('local_only', e.target.checked)} 
                                className="accent-pink-600 rounded" 
                            />
                            <span className="text-[10px] font-black text-white uppercase tracking-wider">Local-Only (Private Storage)</span>
                        </label>
                    </div>

                    <div className="mt-4 p-4 bg-pink-500/10 border border-pink-500/20 rounded-2xl flex items-start gap-3 max-w-2xl">
                        <Info size={16} className="text-pink-400 shrink-0 mt-0.5" />
                        <p className="text-[11px] text-pink-300 leading-relaxed font-semibold">
                            <span className="font-bold uppercase tracking-wider text-pink-400">General Wellness Guidance:</span> This module provides educational insights and cycle-synced tips based on general physiological patterns. It does not constitute medical advice, diagnosis, or treatment. It is not a substitute for advice from a doctor, gynecologist, or registered dietitian. Always consult a healthcare professional before changing your training, nutrition, or medical routine.
                        </p>
                    </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3 items-stretch">
                    {!menopauseMode && (
                        <>
                            <button
                                onClick={() => {
                                    const feedUrl = `${window.location.origin}/api/female/calendar-feed/${user.id || 'anonymous'}`;
                                    navigator.clipboard.writeText(feedUrl);
                                    alert("Google Calendar Sync URL copied to clipboard!\n\nTo link with Google:\n1. Open calendar.google.com\n2. Next to 'Other calendars' click '+' then 'From URL'\n3. Paste this link.");
                                }}
                                className="px-5 py-3 bg-slate-900 border border-pink-500/20 hover:border-pink-500/40 text-pink-400 rounded-2xl font-black uppercase tracking-widest text-xs flex items-center justify-center space-x-2 transition-all"
                            >
                                <Calendar size={16} />
                                <span>Copy Google Cal Link</span>
                            </button>
                            <button
                                onClick={() => { setShowLogModal(true); setSaveSuccess(false); }}
                                className="px-6 py-3 bg-pink-600 hover:bg-pink-500 text-white rounded-2xl font-black uppercase tracking-widest text-xs flex items-center justify-center space-x-2 transition-all shadow-[0_0_20px_rgba(219,39,119,0.3)] hover:scale-105 active:scale-95"
                            >
                                <Calendar size={16} />
                                <span>Log New Cycle</span>
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Cycle Overview */}
                <div className="lg:col-span-1 bg-gradient-to-br from-pink-950/20 to-slate-900/40 border border-pink-500/20 rounded-[2.5rem] p-8 relative overflow-hidden group">
                    <div className="absolute -top-20 -right-20 w-40 h-40 bg-pink-500/10 blur-[80px] rounded-full group-hover:bg-pink-500/20 transition-all duration-700" />

                    <h2 className="text-lg font-black text-white mb-8 flex items-center space-x-3">
                        <Sparkles size={20} className="text-pink-400" />
                        <span>Cycle Status</span>
                    </h2>

                    <div className="h-64 relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={data}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={80}
                                    outerRadius={100}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                    startAngle={90}
                                    endAngle={-270}
                                >
                                    {data.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                            </PieChart>
                        </ResponsiveContainer>
                    <div className="h-64 relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={data}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={80}
                                    outerRadius={100}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                    startAngle={90}
                                    endAngle={-270}
                                >
                                    {data.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Day</span>
                            <span className="text-5xl font-black text-white italic">{menopauseMode ? "—" : cycleDay}</span>
                            <span className="text-[10px] font-black uppercase tracking-widest text-pink-500">of {menopauseMode ? "—" : currentCycleLimit}</span>
                        </div>
                    </div>

                    <div className={`mt-8 px-4 py-3 rounded-2xl border text-center ${phaseColors[advice?.phase || 'all']}`}>
                        <span className="text-xs font-black uppercase tracking-widest">{advice?.phase || 'Tracking'} Phase</span>
                    </div>

                    {/* Rolling Statistics Display */}
                    {advice?.cycle_history_stats && (
                        <div className="mt-6 p-4 bg-white/5 border border-white/10 rounded-2xl space-y-2">
                            <h3 className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Rolling Stats Insights</h3>
                            <div className="flex justify-between text-xs text-slate-300">
                                <span>Average Length:</span>
                                <span className="font-bold text-pink-400">{advice.cycle_history_stats.average_cycle_length} Days</span>
                            </div>
                            <div className="flex justify-between text-xs text-slate-300">
                                <span>Variance (Std Dev):</span>
                                <span className="font-bold text-pink-400">±{advice.cycle_history_stats.std_dev_days} Days</span>
                            </div>
                        </div>
                    )}

                    {/* Outlier Alert Banner */}
                    {advice?.anomaly_warning && (
                        <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[10px] rounded-xl leading-relaxed font-semibold">
                            ⚠️ {advice.anomaly_warning}
                        </div>
                    )}

                    {/* Period log history */}
                    <div className="mt-5 space-y-2">
                        {(() => {
                            const logs: PeriodLog[] = JSON.parse(localStorage.getItem('smarty_period_log') || '[]');
                            if (!logs.length) return (
                                <p className="text-[9px] text-slate-600 text-center italic">No cycle logs yet. Log your first cycle above.</p>
                            );
                            return logs.slice(0, 2).map((log, i) => (
                                <div key={i} className="flex items-center justify-between px-3 py-2 bg-pink-500/5 rounded-xl border border-pink-500/10">
                                    <span className="text-[9px] font-black text-slate-400 uppercase">
                                        {new Date(log.start_date).toLocaleDateString()}
                                    </span>
                                    <span className="text-[9px] text-pink-400 font-black">{log.flow_intensity} Flow</span>
                                </div>
                            ));
                        })()}
                    </div>
                </div>


                {/* Phase Advice */}
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-slate-950/40 border border-white/5 rounded-[2.5rem] p-8 flex flex-col md:flex-row gap-8">
                        <div className="flex-1 space-y-6">
                            <h2 className="text-xl font-black text-white flex items-center space-x-3 italic">
                                <Flower2 size={24} className="text-pink-500" />
                                <span>PHASE INSIGHTS</span>
                            </h2>

                            <div className="space-y-4">
                                <div className="flex gap-4">
                                    <div className="w-10 h-10 rounded-xl bg-pink-500/10 flex items-center justify-center shrink-0 border border-pink-500/10">
                                        <Zap size={18} className="text-pink-400" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-pink-500 uppercase tracking-widest mb-1">Training Strategy</p>
                                        <p className="text-sm text-slate-200 font-medium leading-relaxed">{advice?.advice?.training}</p>
                                    </div>
                                </div>

                                <div className="flex gap-4">
                                    <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0 border border-emerald-500/10">
                                        <Utensils size={18} className="text-emerald-400" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-1">Nutrition Protocol</p>
                                        <p className="text-sm text-slate-200 font-medium leading-relaxed">{advice?.advice?.nutrition}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="w-full md:w-48 p-6 bg-white/5 rounded-3xl border border-white/10 flex flex-col items-center justify-center text-center">
                            <Thermometer size={32} className="text-pink-500 mb-2" />
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Efficiency Cap</p>
                            <p className="text-2xl font-black text-white italic">{advice?.advice?.intensity_limit}</p>
                            <div className="mt-4 w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-pink-500"
                                    style={{ width: advice?.advice?.intensity_limit === 'Maximum' ? '100%' : advice?.advice?.intensity_limit === 'High' ? '75%' : advice?.advice?.intensity_limit === 'Moderate' ? '50%' : '25%' }}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-slate-900/40 p-6 rounded-3xl border border-white/5">
                            <div className="flex items-center space-x-3 mb-4">
                                <Moon size={18} className="text-blue-400" />
                                <span className="text-xs font-black text-white uppercase tracking-widest">Biological Context</span>
                            </div>
                            <p className="text-xs text-slate-400 leading-relaxed font-medium">
                                {advice?.advice?.bio_context}
                            </p>
                        </div>
                        <div className="bg-slate-900/40 p-6 rounded-3xl border border-white/5">
                            <div className="flex items-center space-x-3 mb-4">
                                <ClipboardList size={18} className="text-emerald-400" />
                                <span className="text-xs font-black text-white uppercase tracking-widest">Key Focus</span>
                            </div>
                            <p className="text-xs text-slate-400 leading-relaxed font-medium">
                                {advice?.advice?.focus}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Exercises Section */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-black text-white italic tracking-tight">SPECIALIZED WORKOUTS</h2>
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-3 py-1 border border-white/10 rounded-lg bg-white/5">Synced for {advice?.phase}</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {advice?.recommended_exercises && advice.recommended_exercises.length > 0 ? advice.recommended_exercises.map((ex: any, idx: number) => (
                        <div
                            key={ex.id || idx}
                            className="bg-slate-950/40 border border-white/5 hover:border-pink-500/30 rounded-3xl p-6 transition-all group relative overflow-hidden cursor-pointer"
                            onClick={() => setExpandedExercise(expandedExercise === idx ? null : idx)}
                        >
                            <div className="absolute top-0 right-0 w-24 h-24 bg-pink-500/5 -mr-8 -mt-8 rounded-full blur-2xl group-hover:bg-pink-500/10 transition-all" />

                            <div className="flex items-start justify-between mb-4">
                                <div className="w-12 h-12 bg-pink-500/10 rounded-2xl flex items-center justify-center border border-pink-500/10 shadow-inner group-hover:scale-110 transition-transform">
                                    <DumbbellIcon className="text-pink-400" size={24} />
                                </div>
                                <div className="flex flex-col items-end">
                                    <span className="text-[8px] font-black text-slate-500 uppercase tracking-tighter mb-1">Est. Burn</span>
                                    <span className="text-sm font-black text-pink-400">{ex.calories_per_min} <span className="text-[10px] opacity-70">C/M</span></span>
                                </div>
                            </div>

                            <h3 className="text-lg font-black text-white mb-2 leading-tight uppercase group-hover:text-pink-400 transition-colors">{ex.name}</h3>

                            {expandedExercise === idx && ex.description && (
                                <p className="text-xs text-slate-400 mb-3 font-medium leading-relaxed animate-in fade-in duration-300">
                                    {ex.description}
                                </p>
                            )}
                            {!ex.description || expandedExercise !== idx ? (
                                <p className="text-xs text-slate-500 mb-4 font-medium line-clamp-1 italic">
                                    {ex.description || 'Click for details.'}
                                </p>
                            ) : null}

                            <div className="flex flex-wrap gap-2 pt-4 border-t border-white/5 items-center justify-between">
                                <div className="flex flex-wrap gap-2">
                                    <span className="text-[8px] font-black uppercase px-2 py-1 bg-white/5 rounded-md text-slate-300 border border-white/10">{ex.muscle || ex.targeted_muscle}</span>
                                    <span className="text-[8px] font-black uppercase px-2 py-1 bg-white/5 rounded-md text-slate-300 border border-white/10">{ex.difficulty}</span>
                                    <span className="text-[8px] font-black uppercase px-2 py-1 bg-white/5 rounded-md text-slate-300 border border-white/10">{ex.equipment}</span>
                                </div>
                                {expandedExercise === idx ? <ChevronUp size={14} className="text-pink-400" /> : <ChevronDown size={14} className="text-slate-600" />}
                            </div>
                        </div>
                    )) : (
                        Array.from({ length: 3 }).map((_, i) => (
                            <div key={i} className="h-48 rounded-3xl bg-white/5 border border-white/5 animate-pulse" />
                        ))
                    )}
                </div>
            </div>

            {/* Log Modal */}
            {showLogModal && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setShowLogModal(false)} />
                    <div className="bg-slate-900 border border-pink-500/30 rounded-[2.5rem] p-8 w-full max-w-md relative z-10 shadow-2xl max-h-[90vh] overflow-y-auto">
                        <h2 className="text-2xl font-black text-white italic mb-6">LOG CYCLE START</h2>

                        <div className="space-y-5">
                            {/* Date */}
                            <div>
                                <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Start Date</label>
                                <input
                                    type="date"
                                    value={logDate}
                                    onChange={(e) => setLogDate(e.target.value)}
                                    className="w-full bg-slate-950/50 border border-white/10 rounded-2xl px-5 py-4 text-white focus:outline-none focus:border-pink-500/50 transition-colors"
                                />
                            </div>

                            {/* Mood */}
                            <div>
                                <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Mood</label>
                                <div className="flex flex-wrap gap-2">
                                    {MOODS.map(m => (
                                        <button
                                            key={m}
                                            onClick={() => setLogMood(m)}
                                            className={`px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all ${logMood === m ? 'bg-pink-600 border-pink-600 text-white' : 'bg-slate-950/50 border-white/10 text-slate-400 hover:border-pink-500/30'}`}
                                        >
                                            {m}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Flow Intensity */}
                            <div>
                                <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Flow Intensity</label>
                                <div className="flex gap-2">
                                    {FLOWS.map(f => (
                                        <button
                                            key={f}
                                            onClick={() => setLogFlow(f)}
                                            className={`flex-1 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all ${logFlow === f ? 'bg-pink-600 border-pink-600 text-white' : 'bg-slate-950/50 border-white/10 text-slate-400 hover:border-pink-500/30'}`}
                                        >
                                            {f}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Symptoms */}
                            <div>
                                <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Symptoms <span className="text-slate-600">(optional)</span></label>
                                <div className="flex flex-wrap gap-2">
                                    {SYMPTOMS_OPTIONS.map(s => (
                                        <button
                                            key={s}
                                            onClick={() => toggleSymptom(s)}
                                            className={`px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all ${logSymptoms.includes(s) ? 'bg-rose-600/30 border-rose-500/50 text-rose-300' : 'bg-slate-950/50 border-white/10 text-slate-400 hover:border-rose-500/30'}`}
                                        >
                                            {s}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Info note */}
                            <div className="p-4 bg-pink-500/10 border border-pink-500/20 rounded-2xl flex gap-4">
                                <div className="w-10 h-10 rounded-xl bg-pink-500/20 flex items-center justify-center shrink-0">
                                    <Info size={18} className="text-pink-400" />
                                </div>
                                <p className="text-xs text-pink-300 leading-relaxed">
                                    Logging your cycle helps the <span className="font-black">SMARTY AI</span> calibrate your training and nutrition plans for bio-compatibility.
                                </p>
                            </div>

                            <div className="flex gap-4">
                                <button
                                    onClick={() => setShowLogModal(false)}
                                    className="flex-1 py-4 bg-white/5 hover:bg-white/10 text-slate-400 rounded-2xl font-black uppercase tracking-widest text-xs transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleLogPeriod}
                                    disabled={saving || saveSuccess}
                                    className={`flex-1 py-4 rounded-2xl font-black uppercase tracking-widest text-xs transition-all flex items-center justify-center space-x-2 ${saveSuccess ? 'bg-emerald-600 text-white' : 'bg-pink-600 hover:bg-pink-500 text-white shadow-[0_0_20px_rgba(219,39,119,0.3)]'}`}
                                >
                                    {saveSuccess ? (
                                        <><CheckCircle2 size={16} /><span>Saved!</span></>
                                    ) : saving ? (
                                        <span>Saving...</span>
                                    ) : (
                                        <span>Save Entry</span>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const DumbbellIcon = ({ className, size }: { className?: string, size?: number }) => (
    <svg
        width={size || 24}
        height={size || 24}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <path d="m6.5 6.5 11 11" />
        <path d="m6.5 17.5 11-11" />
        <path d="m14 3 7 7" />
        <path d="m3 14 7 7" />
        <path d="m18 10 3-3" />
        <path d="m3 17 3-3" />
        <path d="m14 18 3 3" />
        <path d="m3 6 3 3" />
        <path d="m10 3 4 4" />
        <path d="m17 10 4 4" />
        <path d="m3 10 4-4" />
        <path d="m10 17 4 4" />
    </svg>
);

export default FemmeCare;
