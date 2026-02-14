
import React, { useState, useEffect } from 'react';
import { User, Ruler, Weight, Activity, Save, Sparkles, Target } from 'lucide-react';
import { UserProfileAPI } from './services/apiService';
import { useAPI } from './hooks/useAPI';
import { BioProfile } from './types';
import GoalManager from './components/GoalManager';

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
    // Load existing profile on mount
    const loadExistingProfile = async () => {
      const result = await loadProfile('user-1');
      if (result) {
        setProfile({
          age: result.age || 28,
          gender: 'Male', // Not in backend schema
          weight: result.weight_kg || 82,
          height: result.height_cm || 182,
          activityLevel: result.activity_level || 'Active',
          goal: result.primary_goal || 'Athletic/Tone'
        });
      }
    };
    loadExistingProfile();
  }, []);

  const handleSave = async () => {
    try {
      await saveProfile('user-1', {
        age: profile.age,
        weight_kg: profile.weight,
        height_cm: profile.height,
        activity_level: profile.activityLevel,
        primary_goal: profile.goal,
        dietary_restrictions: [],
        allergies: []
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to save profile:', err);
    }
  };

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
                <option>Active</option>
                <option>Elite</option>
              </select>
            </div>
          </div>

          <div className="space-y-6">
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

        <div className="mt-12 flex justify-center">
          <button 
            onClick={handleSave}
            disabled={loading}
            className="bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-slate-950 px-12 py-5 rounded-[2rem] font-black text-xs uppercase tracking-widest shadow-xl shadow-emerald-500/20 transition-all flex items-center space-x-3 active:scale-95"
          >
            {saved ? <Sparkles size={18} /> : <Save size={18} />}
            <span>{loading ? 'SYNCING...' : saved ? 'BIO-DATA SYNCED' : 'COMMIT TO NEURAL CORE'}</span>
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
