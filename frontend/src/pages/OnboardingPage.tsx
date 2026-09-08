import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, ChevronRight, ChevronLeft, Check, User, Target, Utensils, Activity, Heart } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { PageFrame, InfoCard } from '../components/PageFrame';
import { use3DTilt } from '../hooks/use3DTilt';

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
    femmecareEnabled: boolean;
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
    const { user, updateProfile } = useAuth();
    const [step, setStep] = useState(0);
    const [saving, setSaving] = useState(false);
    const [profile, setProfile] = useState<Profile>({
        name: '', age: '', gender: 'Male', weight: '', height: '',
        activityLevel: 'moderate', goal: 'athletic', dietaryRestrictions: [], targetWeight: '',
        femmecareEnabled: false
    });

    const wizardTilt = use3DTilt<HTMLDivElement>({ maxTilt: 5, scale: 1.005 });

    const totalSteps = 4;
    const progress = ((step + 1) / totalSteps) * 100;
    const displayUser = user;

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

    const handleFinish = async () => {
        setSaving(true);
        const femmecareEnabled = profile.gender === 'Female' || profile.femmecareEnabled;
        const fullProfile = {
            ...profile,
            femmecareEnabled,
            name: profile.name || displayUser?.full_name || displayUser?.name || 'Athlete',
            dailyCalorieGoal: profile.goal === 'weight_loss' ? 1800 : profile.goal === 'muscle_gain' ? 2800 : 2200,
        };
        localStorage.setItem('smarty_profile', JSON.stringify(fullProfile));
        try {
            await updateProfile({
                full_name: profile.name || displayUser?.full_name || displayUser?.name,
                age: profile.age ? parseInt(profile.age) : undefined,
                weight_kg: profile.weight ? parseFloat(profile.weight) : undefined,
                height_cm: profile.height ? parseFloat(profile.height) : undefined,
                gender: profile.gender,
                activity_level: profile.activityLevel,
                primary_goal: profile.goal,
                femmecare_enabled: femmecareEnabled,
            } as any);
        } catch {}
        setSaving(false);
        navigate('/dashboard');
    };

    const steps = [
        {
            icon: User,
            title: 'About You',
            subtitle: 'Let us personalize your fitness profile',
            content: (
                <div className="space-y-5">
                    <div>
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Full Name</label>
                        <input
                            type="text"
                            value={profile.name}
                            onChange={e => update('name', e.target.value)}
                            placeholder={displayUser?.full_name || displayUser?.name || 'Enter your name'}
                            className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-semibold text-white focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-500"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Age</label>
                            <input type="number" value={profile.age} onChange={e => update('age', e.target.value)} placeholder="25"
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-semibold text-white focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-500" />
                        </div>
                        <div>
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Biological Sex</label>
                            <select value={profile.gender} onChange={e => update('gender', e.target.value)}
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-semibold focus:outline-none focus:border-emerald-500/50 transition text-white">
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Weight (kg)</label>
                            <input type="number" value={profile.weight} onChange={e => update('weight', e.target.value)} placeholder="70"
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-semibold text-white focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-500" />
                        </div>
                        <div>
                            <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Height (cm)</label>
                            <input type="number" value={profile.height} onChange={e => update('height', e.target.value)} placeholder="175"
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-semibold text-white focus:outline-none focus:border-emerald-500/50 transition placeholder:text-slate-500" />
                        </div>
                    </div>
                    {profile.gender === 'Female' && (
                        <div className="p-4 bg-pink-500/10 border border-pink-500/20 rounded-2xl flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <Heart className="text-pink-400" size={20} />
                                <div>
                                    <p className="text-xs font-black text-pink-300">FemmeCare Cycle Syncing</p>
                                    <p className="text-[10px] text-slate-400">Align workout load and diet with your hormonal cycle</p>
                                </div>
                            </div>
                            <input
                                type="checkbox"
                                checked={profile.femmecareEnabled}
                                onChange={e => update('femmecareEnabled', e.target.checked)}
                                className="w-5 h-5 accent-pink-500 rounded cursor-pointer"
                            />
                        </div>
                    )}
                </div>
            )
        },
        {
            icon: Target,
            title: 'Primary Goal',
            subtitle: 'What is your main target for the next 90 days?',
            content: (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {GOALS.map(g => {
                        const selected = profile.goal === g.id;
                        return (
                            <button
                                key={g.id}
                                onClick={() => update('goal', g.id)}
                                className={`p-5 rounded-2xl border transition-all text-left card-3d ${selected
                                    ? 'bg-emerald-500/10 border-emerald-500 text-white shadow-lg shadow-emerald-500/10'
                                    : 'bg-slate-900 border-white/10 text-slate-400 hover:border-white/20'}`}
                            >
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-2xl">{g.emoji}</span>
                                    {selected && <Check size={18} className="text-emerald-400" />}
                                </div>
                                <h4 className="font-black text-white text-base italic">{g.label}</h4>
                                <p className="text-xs text-slate-400 mt-1">{g.desc}</p>
                            </button>
                        );
                    })}
                </div>
            )
        },
        {
            icon: Activity,
            title: 'Activity Level',
            subtitle: 'How active are you in your current routine?',
            content: (
                <div className="space-y-3">
                    {ACTIVITY_LEVELS.map(a => {
                        const selected = profile.activityLevel === a.id;
                        return (
                            <button
                                key={a.id}
                                onClick={() => update('activityLevel', a.id)}
                                className={`w-full p-4 rounded-2xl border transition-all text-left flex items-center justify-between ${selected
                                    ? 'bg-emerald-500/10 border-emerald-500 text-white shadow-md'
                                    : 'bg-slate-900 border-white/10 text-slate-400 hover:border-white/20'}`}
                            >
                                <div>
                                    <p className="font-black text-white text-sm">{a.label}</p>
                                    <p className="text-xs text-slate-400">{a.desc}</p>
                                </div>
                                {selected && <Check size={18} className="text-emerald-400" />}
                            </button>
                        );
                    })}
                </div>
            )
        },
        {
            icon: Utensils,
            title: 'Diet & Fuel',
            subtitle: 'Select any dietary preferences or restrictions',
            content: (
                <div className="space-y-4">
                    <div className="flex flex-wrap gap-2.5">
                        {DIET_OPTIONS.map(d => {
                            const selected = d === 'None'
                                ? profile.dietaryRestrictions.length === 0
                                : profile.dietaryRestrictions.includes(d);
                            return (
                                <button
                                    key={d}
                                    onClick={() => toggleDiet(d)}
                                    className={`px-5 py-3 rounded-2xl text-xs font-black uppercase tracking-wider border transition-all ${selected
                                        ? 'bg-emerald-500 text-slate-950 border-emerald-500 shadow-md'
                                        : 'bg-slate-900 border-white/10 text-slate-400 hover:border-white/20'}`}
                                >
                                    {d}
                                </button>
                            );
                        })}
                    </div>
                </div>
            )
        }
    ];

    const currentStep = steps[step];
    const isFemaleTone = profile.gender === 'Female' || profile.femmecareEnabled;

    return (
        <div className="min-h-screen bg-[#020617] text-white p-4 md:p-8 lg:p-10 flex flex-col justify-center">
            <div className="max-w-4xl mx-auto w-full">
                <PageFrame
                    eyebrow="Profile Calibration"
                    title="Welcome to SMARTY"
                    subtitle="Let's build your personalized training profile"
                    tone={isFemaleTone ? 'pink' : 'emerald'}
                >
                    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr] items-start mt-6">
                        {/* Step Card with 3D Tilt */}
                        <div 
                            ref={wizardTilt.ref as any}
                            style={wizardTilt.style}
                            onMouseMove={wizardTilt.onMouseMove as any}
                            onMouseLeave={wizardTilt.onMouseLeave as any}
                            className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-6 md:p-8 backdrop-blur-xl card-3d"
                        >
                            <div className="card-3d-shine" />
                            {/* Progress bar */}
                            <div className="mb-8">
                                <div className="flex items-center justify-between text-xs font-black uppercase tracking-widest text-slate-400 mb-2">
                                    <span>Step 0{step + 1} of 0{totalSteps}</span>
                                    <span>{Math.round(progress)}%</span>
                                </div>
                                <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden border border-white/5">
                                    <div
                                        className={`h-full ${isFemaleTone ? 'bg-pink-500' : 'bg-emerald-500'} transition-all duration-500 rounded-full`}
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                            </div>

                            {/* Step Header */}
                            <div className="flex items-center space-x-4 mb-6">
                                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${isFemaleTone ? 'bg-pink-500/10 text-pink-400 border border-pink-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
                                    <currentStep.icon size={22} />
                                </div>
                                <div>
                                    <h3 className="text-xl font-black italic uppercase tracking-tight text-white">{currentStep.title}</h3>
                                    <p className="text-xs text-slate-400">{currentStep.subtitle}</p>
                                </div>
                            </div>

                            {/* Step Content */}
                            <div className="min-h-[220px]">
                                {currentStep.content}
                            </div>

                            {/* Nav Controls */}
                            <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between">
                                <button
                                    onClick={() => setStep(s => Math.max(0, s - 1))}
                                    disabled={step === 0}
                                    className="flex items-center space-x-2 px-6 py-3 rounded-2xl bg-white/5 border border-white/10 text-slate-400 hover:text-white disabled:opacity-30 disabled:hover:text-slate-400 font-bold text-xs uppercase tracking-widest transition"
                                >
                                    <ChevronLeft size={16} />
                                    <span>Back</span>
                                </button>
                                {step < totalSteps - 1 ? (
                                    <button
                                        onClick={() => setStep(s => Math.min(totalSteps - 1, s + 1))}
                                        className={`flex items-center space-x-2 px-8 py-3 rounded-2xl font-black text-xs uppercase tracking-widest text-slate-950 ${isFemaleTone ? 'bg-pink-500 hover:bg-pink-400' : 'bg-emerald-500 hover:bg-emerald-400'} shadow-lg transition active:scale-95`}
                                    >
                                        <span>Next</span>
                                        <ChevronRight size={16} />
                                    </button>
                                ) : (
                                    <button
                                        onClick={handleFinish}
                                        disabled={saving}
                                        className={`flex items-center space-x-2 px-8 py-3 rounded-2xl font-black text-xs uppercase tracking-widest text-slate-950 ${isFemaleTone ? 'bg-pink-500 hover:bg-pink-400' : 'bg-emerald-500 hover:bg-emerald-400'} shadow-lg transition active:scale-95 disabled:opacity-50`}
                                    >
                                        <span>{saving ? 'Saving...' : 'Complete Profile'}</span>
                                        <Check size={16} />
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Side Info Cards */}
                        <div className="space-y-4">
                            <InfoCard
                                title="SMART ADAPTATION"
                                detail="Your profile is used to generate personalized calorie targets, macro splits, and customized daily workout protocols."
                                tone={isFemaleTone ? 'pink' : 'emerald'}
                            />
                            {profile.goal && (
                                <InfoCard
                                    title="SELECTED TARGET"
                                    detail={`Goal: ${GOALS.find(g => g.id === profile.goal)?.label || profile.goal}. Workout intensity will adjust automatically.`}
                                    tone={isFemaleTone ? 'pink' : 'emerald'}
                                />
                            )}
                        </div>
                    </div>
                </PageFrame>
            </div>
        </div>
    );
};

export default OnboardingPage;
