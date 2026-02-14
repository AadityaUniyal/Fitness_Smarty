
import React, { useState, useEffect } from 'react';
import { Apple, Flame, Info, Loader2, Sparkles, Target, TrendingUp, CheckCircle2, AlertCircle, Search, Filter, FlaskConical, ChevronRight, Plus } from 'lucide-react';
import MealScanner from './MealScanner';
import { getBodyTypeAdvice } from './geminiService';
import { FoodAPI } from './services/apiService';
import { useAPI } from './hooks/useAPI';
import { BodyGoal, BodyTypeAdvice } from './types';
import ManualFoodEntry from './components/ManualFoodEntry';

const NutritionHub: React.FC = () => {
  const [selectedGoal, setSelectedGoal] = useState<BodyGoal>(BodyGoal.SLIM);
  const [advice, setAdvice] = useState<BodyTypeAdvice | null>(null);
  const [loadingAdvice, setLoadingAdvice] = useState(false);
  
  // Library Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCatId, setSelectedCatId] = useState<number | null>(null);
  const [categories, setCategories] = useState<any[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showManualEntry, setShowManualEntry] = useState(false);

  const { data: foodData, loading: loadingLibrary, execute: searchFood } = useAPI(
    (query?: string, categoryId?: number) => FoodAPI.searchFood(query, categoryId)
  );

  const { execute: loadLibrary } = useAPI(() => FoodAPI.getFoodLibrary());

  const fetchAdvice = async (goal: BodyGoal) => {
    setLoadingAdvice(true);
    try {
      const data = await getBodyTypeAdvice(goal);
      setAdvice(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingAdvice(false);
    }
  };

  const loadInitialData = async () => {
    const cats = await loadLibrary();
    if (cats) {
      setCategories(cats);
    }
    handleSearch('', null);
  };

  const handleSearch = async (query: string, catId: number | null) => {
    const results = await searchFood(query || undefined, catId || undefined);
    if (results) {
      setSearchResults(results);
    }
  };

  const handleManualFoodSave = (foodData: any) => {
    console.log('Manual food entry:', foodData);
    // In a real app, this would save to backend
    setShowManualEntry(false);
    alert('Food entry saved locally. Backend integration pending.');
  };

  useEffect(() => {
    fetchAdvice(selectedGoal);
  }, [selectedGoal]);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleSearch(searchQuery, selectedCatId);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, selectedCatId]);

  return (
    <div className="space-y-12 animate-in fade-in duration-500 pb-20">
      {/* Top Section: Goal Advice & Scanner */}
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
                  className={`px-6 py-2.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all border ${
                    selectedGoal === goal
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
            className={`px-5 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border ${
              selectedCatId === null
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
              className={`px-5 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border ${
                selectedCatId === cat.id
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
