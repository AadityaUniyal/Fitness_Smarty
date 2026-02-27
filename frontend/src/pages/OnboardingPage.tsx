import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, ChevronRight, ChevronLeft, Check, User, Target, Utensils, Activity } from 'lucide-react';

interface Profile {
    name: string;
    age: string;
    gender: string;
    weight: string;
    height: string;
    activityLevel: string;
    goal: string;
    dietaryRestrictions: string[];
    targetWeight?: string;
}

const GOALS = [
    { id: 'weight_loss', label: 'Weight Loss', desc: 'Burn fat, slim down, feel lighter', emoji: '🔥', color: 'orange' },
    { id: 'muscle_gain', label: 'Muscle Gain', desc: 'Build mass, increase strength', emoji: '💪', color: 'blue' },
    { id: 'athletic', label: 'Athletic / Tone', desc: 'Increase stamina and athleticism', emoji: '⚡', color: 'emerald' },
    { id: 'maintenance', label: 'Maintenance', desc: 'Stay fit, healthy lifestyle', emoji: '🎯', color: 'purple' },
];

const ACTIVITY_LEVELS = [
    { id: 'sedentary', label: 'Sedentary', desc: 'Desk job, little to no exercise' },
    { id: 'light', label: 'Lightly Active', desc: '1–3 days/week exercise' },
    { id: 'moderate', label: 'Moderately Active', desc: '3–5 days/week exercise' },
    { id: 'very_active', label: 'Very Active', desc: '6–7 days/week hard exercise' },
    { id: 'athlete', label: 'Athlete', desc: 'Twice daily / elite training' },
];

const DIET_OPTIONS = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Keto', 'Intermittent Fasting', 'Dairy-Free', 'High-Protein', 'None'];

const OnboardingPage: React.FC = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(0);
    const [profile, setProfile] = useState<Profile>({
        name: '', age: '', gender: 'Male', weight: '', height: '',
        activityLevel: 'moderate', goal: 'athletic', dietaryRestrictions: [], targetWeight: ''
    });

    const totalSteps = 4;
    const progress = ((step + 1) / totalSteps) * 100;
    const user = JSON.parse(localStorage.getItem('smarty_user') || '{}');

    const update = (field: keyof Profile, value: any) => setProfile(p => ({ ...p, [field]: value }));

    const toggleDiet = (d: string) => {
        if (d === 'None') { update('dietaryRestrictions', []); return; }
        setProfile(p => ({
            ...p,
            dietaryRestrictions: p.dietaryRestrictions.includes(d)
                ? p.dietaryRestrictions.filter(x => x !== d)
                : [...p.dietaryRestrictions, d]
        }));
    };

    const handleFinish = () => {
        const fullProfile = {
            ...profile,
            name: profile.name || user?.name || 'Operator',
            dailyCalorieGoal: profile.goal === 'weight_loss' ? 1800 : profile.goal === 'muscle_gain' ? 2800 : 2200,
        };
        localStorage.setItem('smarty_profile', JSON.stringify(fullProfile));
        navigate('/dashboard');
    };

    const steps = [
        {
            icon: User,
            title: 'About You',
            subtitle: "Let's build your neural identity",
            content: (
                <div className="space-y-5">
                    <div>
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Full Name</label>
                        <input
                            type="text"
                            value={profile.name}
                            onChange={e => update('name', e.target.value)}
                            placeholder={user?.name || 'Enter your name'}
                            className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-600"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Age</label>
                            <input type="number" value={profile.age} onChange={e => update('age', e.target.value)} placeholder="25"
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-600" />
                        </div>
                        <div>
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Gender</label>
                            <select value={profile.gender} onChange={e => update('gender', e.target.value)}
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm focus:outline-none focus:border-emerald-500/50 transition text-white">
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Weight (kg)</label>
                            <input type="number" value={profile.weight} onChange={e => update('weight', e.target.value)} placeholder="70"
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-600" />
                        </div>
                        <div>
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Height (cm)</label>
                            <input type="number" value={profile.height} onChange={e => update('height', e.target.value)} placeholder="175"
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-600" />
                        </div>
                    </div>
                </div>
            ),
        },
        {
            icon: Target,
            title: 'Your Fitness Goal',
            subtitle: 'This shapes all your AI recommendations',
            content: (
                <div className="space-y-3">
                    {GOALS.map(g => (
                        <button key={g.id} onClick={() => update('goal', g.id)}
                            className={`w-full flex items-center space-x-5 p-5 rounded-2xl border transition-all text-left ${profile.goal === g.id
                                ? 'bg-emerald-500/10 border-emerald-500/50 text-white'
                                : 'bg-slate-900 border-white/10 text-slate-400 hover:border-white/20'}`}>
                            <span className="text-3xl">{g.emoji}</span>
                            <div className="flex-1">
                                <p className="font-black text-sm">{g.label}</p>
                                <p className="text-xs text-slate-500 mt-0.5">{g.desc}</p>
                            </div>
                            {profile.goal === g.id && <Check size={18} className="text-emerald-400 shrink-0" />}
                        </button>
                    ))}
                    {profile.goal === 'weight_loss' && (
                        <div className="mt-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Target Weight (kg) — Optional</label>
                            <input type="number" value={profile.targetWeight} onChange={e => update('targetWeight', e.target.value)} placeholder="e.g. 65"
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-600" />
                        </div>
                    )}
                </div>
            ),
        },
        {
            icon: Activity,
            title: 'Activity Level',
            subtitle: 'How active is your current lifestyle?',
            content: (
                <div className="space-y-3">
                    {ACTIVITY_LEVELS.map(a => (
                        <button key={a.id} onClick={() => update('activityLevel', a.id)}
                            className={`w-full flex items-center space-x-4 p-5 rounded-2xl border transition-all text-left ${profile.activityLevel === a.id
                                ? 'bg-emerald-500/10 border-emerald-500/50 text-white'
                                : 'bg-slate-900 border-white/10 text-slate-400 hover:border-white/20'}`}>
                            <div className="flex-1">
                                <p className="font-black text-sm">{a.label}</p>
                                <p className="text-xs text-slate-500 mt-0.5">{a.desc}</p>
                            </div>
                            {profile.activityLevel === a.id && <Check size={18} className="text-emerald-400 shrink-0" />}
                        </button>
                    ))}
                </div>
            ),
        },
        {
            icon: Utensils,
            title: 'Diet & Restrictions',
            subtitle: 'Select all that apply (optional)',
            content: (
                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                        {DIET_OPTIONS.map(d => (
                            <button key={d} onClick={() => toggleDiet(d)}
                                className={`px-5 py-4 rounded-2xl border text-sm font-black transition-all ${profile.dietaryRestrictions.includes(d) || (d === 'None' && profile.dietaryRestrictions.length === 0)
                                    ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400'
                                    : 'bg-slate-900 border-white/10 text-slate-500 hover:border-white/20'}`}>
                                {d}
                            </button>
                        ))}
                    </div>
                    <div className="p-5 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl mt-4">
                        <p className="text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-2">Ready to Start!</p>
                        <p className="text-sm text-slate-400">Based on your goal of <span className="text-white font-black">{GOALS.find(g => g.id === profile.goal)?.label}</span>, Smarty AI will create your personalised daily plan.</p>
                    </div>
                </div>
            ),
        },
    ];

    const currentStep = steps[step];

    return (
        <div className="min-h-screen bg-[#020617] text-white flex items-center justify-center p-6">
            <div className="absolute top-1/3 left-1/2 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl -translate-x-1/2" />

            <div className="relative z-10 w-full max-w-lg">
                {/* Header */}
                <div className="flex items-center space-x-4 mb-10">
                    <div className="w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.4)] rotate-3">
                        <Zap size={26} className="fill-slate-950 text-slate-950" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-black italic text-white">SMARTY <span className="text-emerald-400">AI</span></h1>
                        <p className="text-[8px] font-black uppercase tracking-widest text-slate-500">Neural Calibration</p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-8">
                    <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">
                        <span>Step {step + 1} of {totalSteps}</span>
                        <span>{Math.round(progress)}% complete</span>
                    </div>
                    <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                            style={{ width: `${progress}%` }} />
                    </div>
                </div>

                {/* Card */}
                <div className="bg-slate-900/60 border border-white/10 rounded-3xl p-8 backdrop-blur-xl">
                    <div className="flex items-center space-x-4 mb-6">
                        <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center">
                            <currentStep.icon size={22} className="text-emerald-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black italic text-white tracking-tight">{currentStep.title}</h2>
                            <p className="text-xs text-slate-500">{currentStep.subtitle}</p>
                        </div>
                    </div>
                    <div className="max-h-[50vh] overflow-y-auto pr-1 space-y-1">
                        {currentStep.content}
                    </div>
                </div>

                {/* Navigation */}
                <div className="flex items-center justify-between mt-6">
                    <button
                        onClick={() => step > 0 ? setStep(s => s - 1) : navigate('/')}
                        className="flex items-center space-x-2 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-slate-400 font-black text-[10px] uppercase tracking-widest transition-all"
                    >
                        <ChevronLeft size={16} />
                        <span>{step === 0 ? 'Back to Login' : 'Previous'}</span>
                    </button>

                    {step < totalSteps - 1 ? (
                        <button
                            onClick={() => setStep(s => s + 1)}
                            className="flex items-center space-x-2 px-8 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-[10px] uppercase tracking-widest rounded-2xl shadow-[0_8px_20px_rgba(16,185,129,0.3)] transition-all"
                        >
                            <span>Continue</span>
                            <ChevronRight size={16} />
                        </button>
                    ) : (
                        <button
                            onClick={handleFinish}
                            className="flex items-center space-x-2 px-8 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-[10px] uppercase tracking-widest rounded-2xl shadow-[0_8px_20px_rgba(16,185,129,0.3)] transition-all"
                        >
                            <Check size={16} />
                            <span>Launch Smarty AI</span>
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OnboardingPage;
