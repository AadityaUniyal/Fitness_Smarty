
import React, { useState, useEffect } from 'react';
import { Apple, Flame, Info, Loader2, Sparkles, Target, TrendingUp, CheckCircle2, AlertCircle, Search, Filter, FlaskConical, ChevronRight, Plus, PieChart } from 'lucide-react';
import MealScanner from './MealScanner';
import { getBodyTypeAdvice } from '../services/geminiService';
import { FoodAPI } from '../services/apiService';
import { useAPI } from '../hooks/useAPI';
import { BodyGoal, BodyTypeAdvice } from '../types';
import MealAdvisor from '../components/MealAdvisor';
import ManualFoodEntry from '../components/ManualFoodEntry';
import { fetchDailyProgress, logMealProgress } from '../services/apiService';
import { useCurrentUserId } from '../hooks/useCurrentUserId';

// ───────────────────────── Inline Donut Component ─────────────────────────
interface DailyDonutProps { proteinCal: number; carbCal: number; fatCal: number; totalCal: number; }
const DailyDonut: React.FC<DailyDonutProps> = ({ proteinCal, carbCal, fatCal, totalCal }) => {
  const total = proteinCal + carbCal + fatCal || 1;
  const proPct = Math.round((proteinCal / total) * 100);
  const carbPct = Math.round((carbCal / total) * 100);
  const fatPct = 100 - proPct - carbPct;
  const r = 52; const cx = 64; const cy = 64;
  const c = 2 * Math.PI * r;
  const arc = (start: number, pct: number, color: string) => (
    <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={14}
      strokeDasharray={`${(pct / 100) * c} ${c - (pct / 100) * c}`}
      strokeDashoffset={-(start / 100) * c + c * 0.25}
      style={{ transition: 'all 0.6s ease' }} />
  );
  return (
    <div className="flex items-center gap-6">
      <svg width={128} height={128}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1e293b" strokeWidth={14} />
        {arc(0, proPct, '#60a5fa')}
        {arc(proPct, carbPct, '#f59e0b')}
        {arc(proPct + carbPct, fatPct, '#a78bfa')}
      </svg>
      <div>
        <p className="text-2xl font-black text-white">{totalCal.toLocaleString()} <span className="text-sm font-bold text-slate-400">kcal</span></p>
        <p className="text-[9px] text-slate-500 uppercase tracking-widest font-black mb-3">logged today</p>
        {[
          { label: 'Protein', pct: proPct, color: 'bg-blue-400 text-blue-400' },
          { label: 'Carbs', pct: carbPct, color: 'bg-amber-400 text-amber-400' },
          { label: 'Fats', pct: fatPct, color: 'bg-purple-400 text-purple-400' },
        ].map(m => (
          <div key={m.label} className="flex items-center space-x-2 mb-1">
            <div className={`w-2.5 h-2.5 rounded-full ${m.color.split(' ')[0]}`} />
            <p className="text-xs font-black text-slate-400">{m.label} <span className={m.color.split(' ')[1]}>{m.pct}%</span></p>
          </div>
        ))}
      </div>
    </div>
  );
};

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─────────────────────── Main NutritionHub ────────────────────────────────
const nutritionColors: Record<string, { border: string; bg: string; text: string }> = {
  blue: { border: 'border-blue-500/20', bg: 'bg-blue-500/10', text: 'text-blue-400' },
  amber: { border: 'border-amber-500/20', bg: 'bg-amber-500/10', text: 'text-amber-400' },
  purple: { border: 'border-purple-500/20', bg: 'bg-purple-500/10', text: 'text-purple-400' },
  emerald: { border: 'border-emerald-500/20', bg: 'bg-emerald-500/10', text: 'text-emerald-400' },
  rose: { border: 'border-rose-500/20', bg: 'bg-rose-500/10', text: 'text-rose-400' },
  cyan: { border: 'border-cyan-500/20', bg: 'bg-cyan-500/10', text: 'text-cyan-400' },
  orange: { border: 'border-orange-500/20', bg: 'bg-orange-500/10', text: 'text-orange-400' },
};

const NutritionHub: React.FC = () => {
  const [selectedGoal, setSelectedGoal] = useState<BodyGoal>(BodyGoal.SLIM);
  const [advice, setAdvice] = useState<BodyTypeAdvice | null>(null);
  const [loadingAdvice, setLoadingAdvice] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCatId, setSelectedCatId] = useState<number | null>(null);
  const [categories, setCategories] = useState<any[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [goalFoods, setGoalFoods] = useState<any[]>([]);
  const [loadingGoalFoods, setLoadingGoalFoods] = useState(false);

  // Daily macro summary from server progress
  const [dailyMacros, setDailyMacros] = useState({ cal: 0, protein: 0, carbs: 0, fat: 0 });
  const userId = useCurrentUserId();

  const computeDailyMacros = async () => {
    const progress = await fetchDailyProgress(userId);
    setDailyMacros({
      cal: Math.round(progress?.calories?.consumed || 0),
      protein: Math.round(progress?.protein?.consumed || 0),
      carbs: Math.round(progress?.carbs?.consumed || 0),
      fat: Math.round(progress?.fats?.consumed || 0),
    });
  };

  const { data: foodData, loading: loadingLibrary, execute: searchFood } = useAPI(
    (query?: string, categoryId?: number) => FoodAPI.searchFood(query, categoryId)
  );
  const { execute: loadLibrary } = useAPI(() => FoodAPI.getFoodLibrary());

  const fetchAdvice = async (goal: BodyGoal) => {
    setLoadingAdvice(true);
    try { const data = await getBodyTypeAdvice(goal); setAdvice(data); }
    catch (err) { console.error(err); }
    finally { setLoadingAdvice(false); }
  };

  const loadInitialData = async () => {
    const cats = await loadLibrary();
    if (cats) setCategories(cats);
    handleSearch('', null);
  };

  const handleSearch = async (query: string, catId: number | null) => {
    const results = await searchFood(query || undefined, catId || undefined);
    if (results) setSearchResults(results);
  };

  const handleManualFoodSave = (foodData: any) => {
    setShowManualEntry(false);
    alert('Food entry saved locally. Backend integration pending.');
  };

  const fetchGoalFoods = async (goal: BodyGoal) => {
    setLoadingGoalFoods(true);
    // Map BodyGoal enum values to backend goal keys
    const goalMap: Record<string, string> = {
      'Slim/Weight Loss': 'fat_loss',
      'Muscle Gain': 'muscle_gain',
      'Athletic': 'athletic',
      'Maintenance': 'maintenance',
    };
    const backendGoal = goalMap[goal] || 'athletic';
    try {
      const res = await fetch(`${API_BASE}/api/food/goal/${backendGoal}?limit=12`);
      if (res.ok) {
        const data = await res.json();
        setGoalFoods(data.foods || []);
      }
    } catch { /* fallback: show nothing */ }
    finally { setLoadingGoalFoods(false); }
  };

  useEffect(() => { fetchAdvice(selectedGoal); fetchGoalFoods(selectedGoal); }, [selectedGoal]);
  useEffect(() => { loadInitialData(); computeDailyMacros(); }, []);
  useEffect(() => {
    const timer = setTimeout(() => handleSearch(searchQuery, selectedCatId), 300);
    return () => clearTimeout(timer);
  }, [searchQuery, selectedCatId]);

  // Recompute every time user returns to this tab
  useEffect(() => {
    const handler = () => computeDailyMacros();
    window.addEventListener('focus', handler);
    return () => window.removeEventListener('focus', handler);
  }, []);

  // Per-gram logging state
  const [loggingFood, setLoggingFood] = useState<any | null>(null);
  const [logGrams, setLogGrams] = useState<number>(100);
  const [isLogging, setIsLogging] = useState(false);

  // Strategy & Feedback
  const [advisorData, setAdvisorData] = useState<{ feedback: any, strategy: any } | null>(null);

  const fetchDailyStrategy = async (lastMealMacros?: any) => {
    try {
      // Goals map for TDEE (mocked logic or fetched from profile)
      const targets = { calories: 2200, protein: 160, carbs: 240, fats: 60 };

      const res = await fetch(`${API_BASE}/api/recommendations/daily-strategy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          consumed: dailyMacros,
          targets,
          goal: selectedGoal,
          last_meal: lastMealMacros,
          time_of_day: new Date().getHours() < 12 ? 'breakfast' : 'lunch'
        })
      });
      const data = await res.json();
      setAdvisorData({ feedback: data.last_meal_feedback, strategy: data.strategy });
    } catch (e) {
      console.error("Strategy sync failed", e);
    }
  };

  const handleLogFood = async (food: any, grams: number) => {
    setIsLogging(true);
    try {
      const res = await fetch(`${API_BASE}/api/recommendations/calculate-food-calories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: [{ food_id: food.id, grams: grams }] })
      });
      const summary = await res.json();

      const logEntry = {
        timestamp: new Date().toISOString(),
        mealName: food.name,
        totalCalories: summary.calories,
        totalProtein: summary.protein_g,
        totalCarbs: summary.carbs_g,
        totalFat: summary.fat_g,
        grams: grams,
        items: [{
          name: food.name,
          protein_g: summary.protein_g,
          carbs_g: summary.carbs_g,
          fat_g: summary.fat_g
        }]
      };

      await logMealProgress(userId);
      await computeDailyMacros();
      await fetchDailyStrategy({
        calories: summary.calories,
        protein: summary.protein_g,
        carbs: summary.carbs_g,
        fats: summary.fat_g
      });

      setLoggingFood(null);
      alert(`${food.name} (${grams}g) logged to server!`);
    } catch (e) {
      console.error(e);
      alert('Failed to log food macros.');
    } finally {
      setIsLogging(false);
    }
  };

  return (
    <div className="space-y-12 animate-in fade-in duration-500 pb-20">
      {/* Logging Modal */}
      {loggingFood && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-md p-8 rounded-[2.5rem] border border-cyan-500/30 animate-in zoom-in-95 duration-300">
            <h3 className="text-2xl font-black text-white uppercase italic tracking-tighter mb-2">Precision Logging</h3>
            <p className="text-[10px] font-black text-cyan-400 uppercase tracking-widest mb-6">Asset: {loggingFood.name}</p>

            <div className="space-y-4 mb-8">
              <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest">Quantity (Grams)</label>
              <div className="relative">
                <input
                  type="number"
                  value={logGrams}
                  onChange={(e) => setLogGrams(Math.max(1, parseInt(e.target.value) || 0))}
                  className="w-full bg-slate-900 border border-white/10 rounded-2xl py-6 px-8 text-3xl font-black text-emerald-400 focus:outline-none focus:border-emerald-500 transition-all"
                />
                <span className="absolute right-8 top-1/2 -translate-y-1/2 text-slate-500 font-black uppercase text-xs">g</span>
              </div>
              <div className="flex justify-between px-2">
                <button onClick={() => setLogGrams(prev => Math.max(1, prev - 50))} className="text-[10px] font-black text-slate-600 hover:text-white transition">-50G</button>
                <button onClick={() => setLogGrams(prev => prev + 50)} className="text-[10px] font-black text-slate-600 hover:text-white transition">+50G</button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setLoggingFood(null)}
                className="py-4 bg-slate-900 border border-white/5 text-slate-500 rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-slate-800 transition"
              >
                Abort
              </button>
              <button
                onClick={() => handleLogFood(loggingFood, logGrams)}
                disabled={isLogging}
                className="py-4 bg-cyan-500 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-[0_5px_20px_rgba(6,182,212,0.3)] hover:bg-cyan-400 transition flex items-center justify-center space-x-2"
              >
                {isLogging ? <Loader2 className="animate-spin" size={16} /> : <CheckCircle2 size={16} />}
                <span>{isLogging ? 'Calculating...' : 'Confirm Entry'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Neural Advisor & Course Correction ── */}
      {(advisorData?.feedback || advisorData?.strategy) && (
        <MealAdvisor feedback={advisorData.feedback} strategy={advisorData.strategy} />
      )}

      {/* ── Daily Macro Summary ── */}
      <div className="bg-slate-900/60 border border-cyan-500/20 p-6 rounded-[2.5rem] space-y-4">
        <div className="flex items-center space-x-3">
          <PieChart size={18} className="text-cyan-400" />
          <h3 className="text-lg font-black text-white uppercase tracking-widest">Today's Macro Breakdown</h3>
          <button onClick={computeDailyMacros} className="ml-auto text-[9px] font-black uppercase tracking-widest text-slate-500 hover:text-cyan-400 transition">Refresh</button>
        </div>
        {dailyMacros.cal === 0 ? (
          <p className="text-slate-600 text-sm font-black uppercase tracking-widest">No meals logged today. Scan a meal to begin!</p>
        ) : (
          <DailyDonut
            proteinCal={dailyMacros.protein * 4}
            carbCal={dailyMacros.carbs * 4}
            fatCal={dailyMacros.fat * 9}
            totalCal={dailyMacros.cal}
          />
        )}
        <div className="grid grid-cols-3 gap-3 pt-2">
          {[
            { label: 'Protein', val: dailyMacros.protein + 'g', color: 'blue' },
            { label: 'Carbs', val: dailyMacros.carbs + 'g', color: 'amber' },
            { label: 'Fats', val: dailyMacros.fat + 'g', color: 'purple' },
          ].map(m => {
            const nc = nutritionColors[m.color as keyof typeof nutritionColors] || nutritionColors.emerald;
            return (
              <div key={m.label} className={`text-center p-3 ${nc.bg} ${nc.border} rounded-2xl`}>
                <p className={`text-lg font-black ${nc.text}`}>{m.val}</p>
                <p className="text-[8px] font-black uppercase tracking-widest text-slate-600">{m.label}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-[2.5rem] space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold text-white flex items-center">
                  <Target className="mr-3 text-emerald-400" />
                  Bio-Strategic Advice
                </h3>
                <p className="text-slate-400 mt-1">AI-derived nutrient distribution for your profile.</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              {Object.values(BodyGoal).map((goal) => (
                <button
                  key={goal}
                  onClick={() => setSelectedGoal(goal)}
                  className={`px-6 py-2.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all border ${selectedGoal === goal
                    ? 'bg-emerald-500 border-emerald-400 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                >
                  {goal}
                </button>
              ))}
            </div>

            {loadingAdvice ? (
              <div className="py-12 flex flex-col items-center space-y-4">
                <Loader2 className="animate-spin text-emerald-400" size={40} />
                <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Analyzing Biofuel Pathways...</p>
              </div>
            ) : advice && (
              <div className="space-y-6 animate-in slide-in-from-bottom-2 duration-300">
                <div className="bg-slate-800/30 p-6 rounded-3xl border border-slate-700/50">
                  <h4 className="text-xl font-black text-emerald-400 italic tracking-tighter uppercase">{advice.title}</h4>
                  <p className="text-slate-400 mt-2 leading-relaxed text-sm font-medium">{advice.description}</p>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  {[
                    { label: 'Protein', value: advice.recommendedMacros.protein, color: 'text-blue-400' },
                    { label: 'Carbs', value: advice.recommendedMacros.carbs, color: 'text-orange-400' },
                    { label: 'Fats', value: advice.recommendedMacros.fats, color: 'text-purple-400' },
                  ].map((m, i) => (
                    <div key={i} className="bg-slate-900/50 p-4 rounded-2xl border border-slate-800 text-center">
                      <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{m.label}</p>
                      <p className={`text-lg font-black ${m.color} italic tracking-tighter`}>{m.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-8">
          <MealScanner />
        </div>
      </div>

      {/* ── Goal-Based Food Recommendations ── */}
      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <Target size={18} className="text-emerald-400" />
          <h3 className="text-lg font-black text-white uppercase tracking-widest">Foods For Your Goal</h3>
          <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-[9px] font-black text-emerald-400 uppercase tracking-widest">{selectedGoal}</span>
        </div>
        {loadingGoalFoods ? (
          <div className="flex space-x-4 overflow-hidden">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="w-36 h-28 shrink-0 bg-slate-900/60 rounded-2xl animate-pulse border border-white/5" />
            ))}
          </div>
        ) : goalFoods.length > 0 ? (
          <div className="flex space-x-4 overflow-x-auto pb-2 scrollbar-hide">
            {goalFoods.map(f => (
              <div key={f.id} className="shrink-0 w-40 p-4 bg-slate-900/80 border border-white/10 rounded-2xl hover:border-emerald-500/30 transition-all group">
                <p className="text-[9px] font-black text-emerald-400 uppercase tracking-widest mb-1 truncate">{f.category || 'Food'}</p>
                <p className="text-xs font-black text-white italic leading-tight mb-3 line-clamp-2 group-hover:text-emerald-300 transition">{f.name}</p>
                <div className="flex justify-between text-[8px] font-black text-slate-500 uppercase mb-3">
                  <span className="text-orange-400">{f.calories} kcal</span>
                  <span className="text-blue-400">{f.protein_g}g P</span>
                </div>
                <button
                  onClick={() => { setLoggingFood(f); setLogGrams(100); }}
                  className="w-full py-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-[7px] font-black uppercase tracking-widest hover:bg-emerald-500 hover:text-slate-950 transition-all"
                >
                  Log Entry
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-600 text-xs font-black uppercase tracking-widest">No foods tagged for this goal yet.</p>
        )}
      </div>
      {/* NEW SECTION: Biofuel Library Search & Filter */}
      <div className="space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h3 className="text-3xl font-black text-white italic tracking-tighter flex items-center">
              <FlaskConical className="mr-3 text-cyan-400" /> BIOFUEL REPOSITORY
            </h3>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mt-1">Neural Database Query Interface</p>
          </div>

          <div className="flex gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-600" size={18} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="SEARCH ASSET LIBRARY..."
                className="w-full bg-slate-950 border border-white/10 rounded-2xl py-4 pl-14 pr-6 text-[10px] font-black tracking-widest text-cyan-400 placeholder:text-slate-800 focus:outline-none focus:border-cyan-500/50 transition-all focus:ring-4 focus:ring-cyan-500/5 uppercase"
              />
            </div>
            <button
              onClick={() => setShowManualEntry(!showManualEntry)}
              className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 px-6 py-3 rounded-xl font-black text-xs uppercase tracking-widest flex items-center space-x-2"
            >
              <Plus size={16} />
              <span>Manual Entry</span>
            </button>
          </div>
        </div>

        {/* Manual Food Entry Form */}
        {showManualEntry && (
          <ManualFoodEntry
            onSave={handleManualFoodSave}
            onCancel={() => setShowManualEntry(false)}
          />
        )}

        {/* Category Filters */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCatId(null)}
            className={`px-5 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border ${selectedCatId === null
              ? 'bg-cyan-500 border-cyan-400 text-slate-950 shadow-[0_0_10px_rgba(34,211,238,0.3)]'
              : 'bg-slate-900 border-white/5 text-slate-500 hover:text-slate-300'
              }`}
          >
            All Protocols
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCatId(cat.id)}
              className={`px-5 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border ${selectedCatId === cat.id
                ? 'bg-cyan-500 border-cyan-400 text-slate-950 shadow-[0_0_10px_rgba(34,211,238,0.3)]'
                : 'bg-slate-900 border-white/5 text-slate-500 hover:text-slate-300'
                }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Results Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {loadingLibrary ? (
            Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="bg-slate-900/40 border border-white/5 rounded-3xl h-48 animate-pulse"></div>
            ))
          ) : searchResults.length > 0 ? (
            searchResults.map((food) => (
              <div key={food.id} className="glass-panel p-6 rounded-[2rem] border border-white/5 group hover:border-cyan-500/30 transition-all cursor-default flex flex-col justify-between hover:scale-[1.02]">
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">{food.serving_size}</p>
                    {food.is_elite && (
                      <Sparkles size={14} className="text-cyan-400 animate-pulse" />
                    )}
                  </div>
                  <h4 className="text-sm font-black text-white uppercase italic group-hover:text-cyan-400 transition-colors">{food.name}</h4>
                </div>

                <div className="mt-6 space-y-4">
                  <div className="flex justify-between items-end">
                    <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Kcal</span>
                    <span className="text-xs font-black text-white italic">{food.calories}</span>
                  </div>
                  <div className="w-full bg-slate-950 h-1 rounded-full overflow-hidden">
                    <div className="bg-cyan-500 h-full" style={{ width: `${Math.min((food.protein / 30) * 100, 100)}%` }}></div>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-center">
                      <p className="text-[7px] font-black text-slate-600 uppercase">Pro</p>
                      <p className="text-[10px] font-black text-blue-400">{food.protein}g</p>
                    </div>
                    <div className="text-center">
                      <p className="text-[7px] font-black text-slate-600 uppercase">Crb</p>
                      <p className="text-[10px] font-black text-orange-400">{food.carbs}g</p>
                    </div>
                    <div className="text-center">
                      <p className="text-[7px] font-black text-slate-600 uppercase">Fat</p>
                      <p className="text-[10px] font-black text-purple-400">{food.fats}g</p>
                    </div>
                  </div>

                  <button
                    onClick={(e) => { e.stopPropagation(); setLoggingFood(food); setLogGrams(100); }}
                    className="w-full mt-4 py-3 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-xl font-black text-[8px] uppercase tracking-widest hover:bg-cyan-500 hover:text-slate-950 transition-all opacity-0 group-hover:opacity-100 transform translate-y-2 group-hover:translate-y-0"
                  >
                    Log Asset Unit
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full py-20 text-center space-y-4 glass-panel rounded-[3rem] border border-white/5">
              <Info className="mx-auto text-slate-700" size={40} />
              <p className="text-xs font-black text-slate-600 uppercase tracking-[0.3em]">No Assets Found Matching Query</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NutritionHub;
