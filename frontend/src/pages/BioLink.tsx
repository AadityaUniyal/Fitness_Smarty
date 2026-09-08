import React, { useState, useEffect } from 'react';
import { User, Ruler, Weight, Activity, Save, Sparkles, Target, Droplets, BrainCircuit, Flame } from 'lucide-react';
import { UserProfileAPI } from '../services/apiService';
import { useAPI } from '../hooks/useAPI';
import { BioProfile } from '../types';
import GoalManager from '../components/GoalManager';
import { useUserProfile } from '../hooks/useUserProfile';
import { useCurrentUserId } from '../hooks/useCurrentUserId';
import { PageFrame } from '../components/PageFrame';

const ACTIVITY_MULTIPLIERS: Record<string, number> = {
  'Sedentary': 1.2, 'Light': 1.375, 'Moderate': 1.55, 'Active': 1.725, 'Elite': 1.9
};

const computeTDEE = (profile: BioProfile) => {
  const w = profile.weight || 70;
  const h = profile.height || 170;
  const a = profile.age || 30;
  const isMale = profile.gender === 'Male';
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
  const { profile: userProfile } = useUserProfile();
  const userId = useCurrentUserId();
  const [profile, setProfile] = useState<BioProfile>({
    age: 28,
    gender: 'Male',
    weight: 82,
    height: 182,
    activityLevel: 'Active',
    goal: 'Athletic/Tone'
  });

  const [saved, setSaved] = useState(false);
  
  const { execute: saveProfile } = useAPI(
    (uId: string, profileData: any) => 
      UserProfileAPI.updateProfile(uId, profileData)
  );

  const { execute: loadProfile } = useAPI(
    (uId: string) => UserProfileAPI.getProfile(uId)
  );

  useEffect(() => {
    if (userProfile && (userProfile.gender || userProfile.weight || userProfile.height)) {
      setProfile({
        age: userProfile.age || 28,
        gender: userProfile.gender || 'Male',
        weight: userProfile.weight || userProfile.weight_kg || 82,
        height: userProfile.height || userProfile.height_cm || 182,
        activityLevel: userProfile.activityLevel || userProfile.activity_level || 'Active',
        goal: userProfile.goal || userProfile.primary_goal || 'Athletic/Tone',
      });
      return;
    }
    const loadExistingProfile = async () => {
      const result = await loadProfile(String(userId));
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
  }, [userProfile, userId]);

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
      localStorage.setItem('smarty_profile', JSON.stringify(updatedProfile));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      saveProfile(String(userId), {
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
    <div className="max-w-5xl mx-auto space-y-8">
      <PageFrame
        eyebrow="Biometric Profile"
        title="Bio-Link Calibration"
        subtitle="Synchronize your biological metrics to personalize calorie targets and macro splits."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-6">
          <div className="space-y-5">
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center">
                <Ruler size={14} className="mr-2" /> Height (cm)
              </label>
              <input 
                type="number" 
                value={profile.height}
                onChange={(e) => setProfile({...profile, height: Number(e.target.value)})}
                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-black tracking-widest text-emerald-400 focus:border-emerald-500/50 outline-none transition-all"
              />
            </div>

            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center">
                <Weight size={14} className="mr-2" /> Weight (kg)
              </label>
              <input 
                type="number" 
                value={profile.weight}
                onChange={(e) => setProfile({...profile, weight: Number(e.target.value)})}
                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-black tracking-widest text-emerald-400 focus:border-emerald-500/50 outline-none transition-all"
              />
            </div>

            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center">
                <Activity size={14} className="mr-2" /> Activity Level
              </label>
              <select 
                value={profile.activityLevel}
                onChange={(e) => setProfile({...profile, activityLevel: e.target.value as any})}
                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-bold tracking-widest text-white focus:border-emerald-500/50 outline-none transition-all"
              >
                <option>Sedentary</option>
                <option>Light</option>
                <option>Moderate</option>
                <option>Active</option>
                <option>Elite</option>
              </select>
            </div>
          </div>

          <div className="space-y-5">
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center">
                <User size={14} className="mr-2" /> Gender
              </label>
              <select
                value={profile.gender}
                onChange={(e) => setProfile({...profile, gender: e.target.value as any})}
                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-bold tracking-widest text-white focus:border-emerald-500/50 outline-none transition-all"
              >
                <option>Male</option>
                <option>Female</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center">
                <User size={14} className="mr-2" /> Age
              </label>
              <input 
                type="number" 
                value={profile.age}
                onChange={(e) => setProfile({...profile, age: Number(e.target.value)})}
                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-black tracking-widest text-emerald-400 focus:border-emerald-500/50 outline-none transition-all"
              />
            </div>

            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center">
                <Target size={14} className="mr-2" /> Primary Goal
              </label>
              <select
                value={profile.goal}
                onChange={(e) => setProfile({...profile, goal: e.target.value as any})}
                className="w-full bg-slate-900 border border-white/10 rounded-2xl px-6 py-4 text-sm font-bold tracking-widest text-white focus:border-emerald-500/50 outline-none transition-all"
              >
                <option value="weight_loss">Weight Loss</option>
                <option value="muscle_gain">Muscle Gain</option>
                <option value="athletic">Athletic / Tone</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </div>
          </div>
        </div>

        {/* Calculated Metrics Ribbon */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-white/5">
          <div className="p-4 bg-slate-900/80 border border-white/10 rounded-2xl">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 block">BMR</span>
            <span className="text-xl font-black italic text-white mt-1 block">{bmr} <span className="text-xs text-slate-400 font-normal">kcal</span></span>
          </div>
          <div className="p-4 bg-slate-900/80 border border-white/10 rounded-2xl">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 block">TDEE</span>
            <span className="text-xl font-black italic text-emerald-400 mt-1 block">{tdee} <span className="text-xs text-slate-400 font-normal">kcal</span></span>
          </div>
          <div className="p-4 bg-slate-900/80 border border-white/10 rounded-2xl">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 block">BMI Score</span>
            <span className="text-xl font-black italic text-white mt-1 block">{bmi || '--'} {bmiLabel && <span className={`text-xs font-bold ${bmiLabel.color}`}>({bmiLabel.label})</span>}</span>
          </div>
          <div className="p-4 bg-slate-900/80 border border-white/10 rounded-2xl">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 block">Calorie Target</span>
            <span className="text-xl font-black italic text-cyan-400 mt-1 block">{macros.calories} <span className="text-xs text-slate-400 font-normal">kcal</span></span>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-end">
          <button
            onClick={handleSave}
            className="flex items-center space-x-2 px-8 py-3.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs uppercase tracking-widest rounded-2xl shadow-lg shadow-emerald-500/20 transition active:scale-95"
          >
            <Save size={16} />
            <span>{saved ? 'Calibrated & Saved!' : 'Save Calibration'}</span>
          </button>
        </div>
      </PageFrame>

      {/* Goal Management Section */}
      <div className="glass-panel p-8 rounded-[2.5rem] border border-white/10">
        <GoalManager />
      </div>
    </div>
  );
};

export default BioLink;
