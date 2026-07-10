
import React, { useState, useEffect } from 'react';
import { User, Ruler, Weight, Activity, Save, Sparkles, Target, Droplets, BrainCircuit, Flame } from 'lucide-react';
import { UserProfileAPI } from '../services/apiService';
import { useAPI } from '../hooks/useAPI';
import { BioProfile } from '../types';
import GoalManager from '../components/GoalManager';

const ACTIVITY_MULTIPLIERS: Record<string, number> = {
  'Sedentary': 1.2, 'Light': 1.375, 'Moderate': 1.55, 'Active': 1.725, 'Elite': 1.9
};

const computeTDEE = (profile: BioProfile) => {
  const w = profile.weight || 70;
  const h = profile.height || 170;
  const a = profile.age || 30;
  const isMale = profile.gender === 'Male';
  // Mifflin-St Jeor
  const bmr = isMale
    ? 10 * w + 6.25 * h - 5 * a + 5
    : 10 * w + 6.25 * h - 5 * a - 161;
  const mult = ACTIVITY_MULTIPLIERS[profile.activityLevel] || 1.55;
  const tdee = Math.round(bmr * mult);
  return { bmr: Math.round(bmr), tdee };
};

const getMacroTargets = (tdee: number, goal: string) => {
  let calAdjustment = 0;
  if (goal === 'Slim/Weight Loss' || goal === 'weight_loss') calAdjustment = -500;
  else if (goal === 'Bulking/Mass' || goal === 'muscle_gain' || goal === 'Muscle Gain') calAdjustment = 300;
  else if (goal === 'Athletic/Tone') calAdjustment = 0;
  else calAdjustment = 0;
  const targetCals = Math.max(1200, tdee + calAdjustment);
  return {
    calories: targetCals,
    protein: Math.round(targetCals * 0.3 / 4),
    carbs: Math.round(targetCals * 0.4 / 4),
    fats: Math.round(targetCals * 0.3 / 9),
  };
};

const BioLink: React.FC = () => {
  const [profile, setProfile] = useState<BioProfile>({
    age: 28,
    gender: 'Male',
    weight: 82,
    height: 182,
    activityLevel: 'Active',
    goal: 'Athletic/Tone'
  });

  const [saved, setSaved] = useState(false);
  
  const { data: profileData, loading, error, execute: saveProfile } = useAPI(
    (userId: string, profileData: any) => 
      UserProfileAPI.updateProfile(userId, profileData)
  );

  const { execute: loadProfile } = useAPI(
    (userId: string) => UserProfileAPI.getProfile(userId)
  );

  useEffect(() => {
    const savedProfile = localStorage.getItem('smarty_profile');
    if (savedProfile) {
      try {
        const parsed = JSON.parse(savedProfile);
        if (parsed.gender) {
          setProfile(parsed);
          return;
        }
      } catch {}
    }
    // Load from backend
    const loadExistingProfile = async () => {
      const result = await loadProfile('user-1');
      if (result) {
        setProfile({
          age: result.age || 28,
          gender: result.gender || 'Male',
          weight: result.weight_kg || 82,
          height: result.height_cm || 182,
          activityLevel: result.activity_level || 'Active',
          goal: result.primary_goal || 'Athletic/Tone'
        });
      }
    };
    loadExistingProfile();
  }, []);

  const { bmr, tdee } = computeTDEE(profile);
  const macros = getMacroTargets(tdee, profile.goal);

  const handleSave = async () => {
    try {
      const updatedProfile = {
        ...profile,
        dailyCalorieGoal: macros.calories,
        calorieGoal: macros.calories,
        proteinGoal: macros.protein,
        carbsGoal: macros.carbs,
        fatsGoal: macros.fats,
      };
      // Always save to localStorage first so app works offline
      localStorage.setItem('smarty_profile', JSON.stringify(updatedProfile));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      // Also sync to backend (non-blocking)
      saveProfile('user-1', {
        age: profile.age,
        weight_kg: profile.weight,
        height_cm: profile.height,
        activity_level: profile.activityLevel,
        primary_goal: profile.goal,
        dietary_restrictions: [],
        allergies: []
      }).catch(err => console.warn('Backend sync failed (offline mode ok):', err));
    } catch (err) {
      console.error('Failed to save profile:', err);
    }
  };

  const bmi = profile.height > 0 ? (profile.weight / Math.pow(profile.height / 100, 2)).toFixed(1) : null;
  const bmiLabel = bmi
    ? Number(bmi) < 18.5 ? { label: 'Underweight', color: 'text-blue-400' }
    : Number(bmi) < 25 ? { label: 'Healthy', color: 'text-emerald-400' }
    : Number(bmi) < 30 ? { label: 'Overweight', color: 'text-amber-400' }
    : { label: 'Obese', color: 'text-rose-400' }
    : null;

  return (
    <div className="max-w-4xl mx-auto space-y-10 animate-in fade-in duration-700">
      <div className="flex items-center space-x-6">
        <div className="w-20 h-20 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl flex items-center justify-center text-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.1)]">
          <User size={40} />
        </div>
        <div>
          <h2 className="text-4xl font-black italic tracking-tighter text-white">BIO-LINK CALIBRATION</h2>
          <p className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-500">Synchronize Biological Constants</p>
        </div>
      </div>

      <div className="glass-panel p-10 rounded-[3rem] border border-white/5 relative overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="space-y-6">
            <div className="space-y-3">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1 flex items-center">
                <Ruler size={14} className="mr-2" /> Height (cm)
              </label>
              <input 
                type="number" 
                value={profile.height}
                onChange={(e) => setProfile({...profile, height: Number(e.target.value)})}
                className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest text-emerald-400 focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all uppercase"
              />
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1 flex items-center">
                <Weight size={14} className="mr-2" /> Weight (kg)
              </label>
              <input 
                type="number" 
                value={profile.weight}
                onChange={(e) => setProfile({...profile, weight: Number(e.target.value)})}
                className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest text-emerald-400 focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all uppercase"
              />
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1 flex items-center">
                <Activity size={14} className="mr-2" /> Activity Level
              </label>
              <select 
                value={profile.activityLevel}
                onChange={(e) => setProfile({...profile, activityLevel: e.target.value as any})}
                className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest text-emerald-400 focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all uppercase"
              >
                <option>Sedentary</option>
                <option>Light</option>
                <option>Moderate</option>
                <option>Active</option>
                <option>Elite</option>
              </select>
            </div>
          </div>

          <div className="space-y-6">
             <div className="space-y-3">
               <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1 flex items-center">
                 <User size={14} className="mr-2" /> Gender
               </label>
               <select
                 value={profile.gender}
                 onChange={(e) => setProfile({...profile, gender: e.target.value as any})}
                 className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest text-emerald-400 focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all uppercase"
               >
                 <option>Male</option>
                 <option>Female</option>
               </select>
             </div>

             <div className="space-y-3">
               <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1 flex items-center">
                 <User size={14} className="mr-2" /> Age
               </label>
              <input 
                type="number" 
                value={profile.age}
                onChange={(e) => setProfile({...profile, age: Number(e.target.value)})}
                className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest text-emerald-400 focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all uppercase"
              />
            </div>

            <div className="space-y-3">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1 flex items-center">
                <Sparkles size={14} className="mr-2" /> Primary Goal
              </label>
              <select 
                value={profile.goal}
                onChange={(e) => setProfile({...profile, goal: e.target.value})}
                className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest text-emerald-400 focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all uppercase"
              >
                <option>Slim/Weight Loss</option>
                <option>Athletic/Tone</option>
                <option>Bulking/Mass</option>
                <option>Maintenance</option>
              </select>
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-4 items-center justify-center">
          {bmi && bmiLabel && (
            <div className="px-6 py-3 bg-slate-950 border border-white/10 rounded-2xl flex items-center space-x-3">
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">BMI</span>
              <span className={`text-xl font-black italic ${bmiLabel.color}`}>{bmi}</span>
              <span className={`text-[9px] font-black uppercase tracking-widest ${bmiLabel.color}`}>{bmiLabel.label}</span>
            </div>
          )}
          <div className="px-6 py-3 bg-slate-950 border border-white/10 rounded-2xl flex items-center space-x-3">
            <Flame size={16} className="text-orange-400" />
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">BMR</span>
            <span className="text-lg font-black text-orange-400">{bmr}</span>
            <span className="text-[8px] text-slate-600">kcal</span>
            <span className="text-slate-700 mx-1">|</span>
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">TDEE</span>
            <span className="text-lg font-black text-emerald-400">{tdee}</span>
            <span className="text-[8px] text-slate-600">kcal</span>
          </div>
          {macros && (
            <div className="px-6 py-3 bg-slate-950 border border-emerald-500/20 rounded-2xl flex items-center space-x-4">
              <BrainCircuit size={16} className="text-emerald-400" />
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Macros</span>
              <span className="text-xs text-white"><span className="text-amber-400">{macros.calories}</span> kcal</span>
              <span className="text-slate-700">|</span>
              <span className="text-xs"><span className="text-blue-400">P</span> <span className="text-white">{macros.protein}g</span></span>
              <span className="text-xs"><span className="text-amber-400">C</span> <span className="text-white">{macros.carbs}g</span></span>
              <span className="text-xs"><span className="text-purple-400">F</span> <span className="text-white">{macros.fats}g</span></span>
            </div>
          )}
          <button
            onClick={handleSave}
            disabled={loading}
            className="bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-slate-950 px-12 py-5 rounded-4xl font-black text-xs uppercase tracking-widest shadow-xl shadow-emerald-500/20 transition-all flex items-center space-x-3 active:scale-95"
          >
            {saved ? <Sparkles size={18} /> : <Save size={18} />}
            <span>{loading ? 'SYNCING...' : saved ? '✓ BIO-DATA SYNCED' : 'COMMIT TO NEURAL CORE'}</span>
          </button>
        </div>

        {error && (
          <div className="mt-6 py-4 px-6 bg-red-500/10 border border-red-500/20 rounded-2xl text-center">
            <p className="text-xs text-red-400">{error}</p>
          </div>
        )}
      </div>

      {/* Goal Management Section */}
      <div className="glass-panel p-10 rounded-[3rem] border border-white/5">
        <GoalManager />
      </div>
    </div>
  );
};

export default BioLink;
