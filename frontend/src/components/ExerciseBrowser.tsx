import React, { useState, useEffect } from 'react';
import { Dumbbell, Search, Filter, Loader2, Info, Heart, ChevronRight, Trophy, Calendar, Sparkles, X } from 'lucide-react';
import { ExerciseAPI } from '../services/apiService';
import { useAPI } from '../hooks/useAPI';

const FAV_KEY = 'smarty_exercise_favorites';

const loadFavorites = (): string[] => {
  try {
    return JSON.parse(localStorage.getItem(FAV_KEY) || '[]');
  } catch { return []; }
};

// SVG Stick-figure guides with inline CSS animations
const ExerciseStickFigure: React.FC<{ name: string; primaryMuscle: string; large?: boolean }> = ({ name, primaryMuscle, large = false }) => {
  const muscle = (primaryMuscle || '').toLowerCase();
  const lowerName = (name || '').toLowerCase();
  
  let animType = 'default';
  if (muscle.includes('chest') || lowerName.includes('press') || lowerName.includes('pushup')) {
    animType = 'press';
  } else if (muscle.includes('leg') || muscle.includes('quad') || muscle.includes('hamstring') || muscle.includes('glute') || lowerName.includes('squat') || lowerName.includes('lunge')) {
    animType = 'squat';
  } else if (muscle.includes('arm') || muscle.includes('bicep') || muscle.includes('tricep') || lowerName.includes('curl')) {
    animType = 'curl';
  } else if (muscle.includes('back') || lowerName.includes('row') || lowerName.includes('pull') || lowerName.includes('chin') || lowerName.includes('deadlift')) {
    animType = 'row';
  } else if (muscle.includes('shoulder') || lowerName.includes('overhead') || lowerName.includes('raise')) {
    animType = 'overhead';
  } else if (muscle.includes('core') || muscle.includes('abs') || lowerName.includes('crunch') || lowerName.includes('situp')) {
    animType = 'crunch';
  }

  const renderStyles = () => {
    switch (animType) {
      case 'press':
        return `
          @keyframes barPress {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-25px); }
          }
          @keyframes armPressL {
            0%, 100% { x2: 40; y2: 60; }
            50% { x2: 40; y2: 35; }
          }
          @keyframes armPressR {
            0%, 100% { x2: 80; y2: 60; }
            50% { x2: 80; y2: 35; }
          }
        `;
      case 'squat':
        return `
          @keyframes squatBody {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(20px) scaleY(0.8); transform-origin: bottom; }
          }
          @keyframes squatLegs {
            0%, 100% { d: path('M 45 80 L 60 110 L 60 140 M 75 80 L 60 110 L 60 140'); }
            50% { d: path('M 45 100 L 30 115 L 60 140 M 75 100 L 90 115 L 60 140'); }
          }
        `;
      case 'curl':
        return `
          @keyframes armCurl {
            0%, 100% { transform: rotate(0deg); transform-origin: 60px 55px; }
            50% { transform: rotate(-70deg); transform-origin: 60px 55px; }
          }
        `;
      case 'row':
        return `
          @keyframes rowPull {
            0%, 100% { transform: translateX(0px); }
            50% { transform: translateX(-15px); }
          }
          @keyframes armRow {
            0%, 100% { x2: 45; y2: 60; }
            50% { x2: 65; y2: 55; }
          }
        `;
      case 'overhead':
        return `
          @keyframes barOverhead {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-35px); }
          }
          @keyframes armsOverhead {
            0%, 100% { d: path('M 45 55 L 45 75 M 75 55 L 75 75'); }
            50% { d: path('M 45 20 L 45 75 M 75 20 L 75 75'); }
          }
        `;
      case 'crunch':
        return `
          @keyframes crunchTorso {
            0%, 100% { transform: rotate(0deg); transform-origin: 60px 80px; }
            50% { transform: rotate(-30deg); transform-origin: 60px 80px; }
          }
        `;
      default:
        return `
          @keyframes defaultBounce {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
          }
        `;
    }
  };

  const svgHeight = large ? 'h-48 md:h-56' : 'h-24';

  return (
    <div className={`w-full ${svgHeight} bg-slate-900/60 flex items-center justify-center relative overflow-hidden rounded-xl border border-white/5 group-hover:border-emerald-500/20 transition-all`}>
      <style>{renderStyles()}</style>
      <svg className="w-full h-full text-emerald-400" viewBox="0 0 120 120">
        {animType === 'press' && (
          <g>
            <line x1="20" y1="80" x2="100" y2="80" stroke="#475569" strokeWidth="4" strokeLinecap="round" />
            <line x1="30" y1="80" x2="30" y2="105" stroke="#475569" strokeWidth="4" />
            <line x1="90" y1="80" x2="90" y2="105" stroke="#475569" strokeWidth="4" />
            <line x1="40" y1="72" x2="80" y2="72" stroke="#f8fafc" strokeWidth="6" strokeLinecap="round" />
            <circle cx="85" cy="72" r="6" fill="#f8fafc" />
            <line x1="50" y1="72" x2="40" y2="60" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" style={{ animation: 'armPressL 1.6s infinite ease-in-out' }} />
            <line x1="70" y1="72" x2="80" y2="60" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" style={{ animation: 'armPressR 1.6s infinite ease-in-out' }} />
            <g style={{ animation: 'barPress 1.6s infinite ease-in-out' }}>
              <line x1="30" y1="50" x2="90" y2="50" stroke="#10b981" strokeWidth="3" />
              <rect x="22" y="42" width="8" height="16" rx="2" fill="#10b981" />
              <rect x="90" y="42" width="8" height="16" rx="2" fill="#10b981" />
            </g>
          </g>
        )}
        
        {animType === 'squat' && (
          <g>
            <line x1="20" y1="110" x2="100" y2="110" stroke="#475569" strokeWidth="3" />
            <g style={{ animation: 'squatBody 1.6s infinite ease-in-out' }}>
              <line x1="60" y1="55" x2="60" y2="80" stroke="#f8fafc" strokeWidth="6" strokeLinecap="round" />
              <circle cx="60" cy="45" r="7" fill="#f8fafc" />
              <line x1="60" y1="60" x2="85" y2="60" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            </g>
            <path stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" fill="none"
                  style={{ animation: 'squatLegs 1.6s infinite ease-in-out' }}
                  d="M 60 80 L 45 95 L 45 110 M 60 80 L 75 95 L 75 110" />
          </g>
        )}

        {animType === 'curl' && (
          <g>
            <line x1="20" y1="110" x2="100" y2="110" stroke="#475569" strokeWidth="2" />
            <line x1="60" y1="55" x2="60" y2="85" stroke="#f8fafc" strokeWidth="6" strokeLinecap="round" />
            <circle cx="60" cy="45" r="7" fill="#f8fafc" />
            <line x1="60" y1="85" x2="48" y2="110" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <line x1="60" y1="85" x2="72" y2="110" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <g style={{ animation: 'armCurl 1.4s infinite ease-in-out' }}>
              <line x1="60" y1="60" x2="75" y2="75" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
              <circle cx="78" cy="78" r="4.5" fill="#10b981" />
            </g>
          </g>
        )}

        {animType === 'row' && (
          <g>
            <line x1="20" y1="110" x2="100" y2="110" stroke="#475569" strokeWidth="2" />
            <g style={{ animation: 'rowPull 1.5s infinite ease-in-out' }}>
              <line x1="50" y1="55" x2="65" y2="80" stroke="#f8fafc" strokeWidth="6" strokeLinecap="round" />
              <circle cx="45" cy="47" r="7" fill="#f8fafc" />
              <line x1="55" y1="62" x2="45" y2="80" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round"
                    style={{ animation: 'armRow 1.5s infinite ease-in-out' }} />
            </g>
            <line x1="65" y1="80" x2="55" y2="110" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <line x1="65" y1="80" x2="75" y2="110" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
          </g>
        )}

        {animType === 'overhead' && (
          <g>
            <line x1="20" y1="110" x2="100" y2="110" stroke="#475569" strokeWidth="2" />
            <line x1="60" y1="55" x2="60" y2="85" stroke="#f8fafc" strokeWidth="6" strokeLinecap="round" />
            <circle cx="60" cy="45" r="7" fill="#f8fafc" />
            <line x1="60" y1="85" x2="48" y2="110" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <line x1="60" y1="85" x2="72" y2="110" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <path stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" fill="none"
                  style={{ animation: 'armsOverhead 1.5s infinite ease-in-out' }}
                  d="M 45 60 L 52 70 L 60 60 M 75 60 L 68 70 L 60 60" />
            <g style={{ animation: 'barOverhead 1.5s infinite ease-in-out' }}>
              <line x1="35" y1="52" x2="85" y2="52" stroke="#10b981" strokeWidth="3" />
              <rect x="27" y="44" width="8" height="16" rx="2" fill="#10b981" />
              <rect x="85" y="44" width="8" height="16" rx="2" fill="#10b981" />
            </g>
          </g>
        )}

        {animType === 'crunch' && (
          <g>
            <line x1="20" y1="90" x2="100" y2="90" stroke="#475569" strokeWidth="3" />
            <line x1="60" y1="90" x2="85" y2="70" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <line x1="85" y1="70" x2="95" y2="90" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <g style={{ animation: 'crunchTorso 1.4s infinite ease-in-out' }}>
              <line x1="60" y1="88" x2="25" y2="75" stroke="#f8fafc" strokeWidth="6" strokeLinecap="round" />
              <circle cx="20" cy="70" r="7" fill="#f8fafc" />
              <line x1="25" y1="75" x2="18" y2="68" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            </g>
          </g>
        )}

        {animType === 'default' && (
          <g style={{ animation: 'defaultBounce 1.4s infinite ease-in-out' }}>
            <circle cx="60" cy="40" r="10" fill="#f8fafc" />
            <line x1="60" y1="50" x2="60" y2="85" stroke="#f8fafc" strokeWidth="6" strokeLinecap="round" />
            <line x1="60" y1="60" x2="40" y2="75" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <line x1="60" y1="60" x2="80" y2="75" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <line x1="60" y1="85" x2="45" y2="110" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
            <line x1="60" y1="85" x2="75" y2="110" stroke="#f8fafc" strokeWidth="4" strokeLinecap="round" />
          </g>
        )}
      </svg>
    </div>
  );
};

const ExerciseBrowser: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('');
  
  // Hevy-style multiple selections
  const [selectedMuscles, setSelectedMuscles] = useState<string[]>([]);
  const [selectedEquipments, setSelectedEquipments] = useState<string[]>([]);

  // Detailed Modal states
  const [expandedExercise, setExpandedExercise] = useState<any | null>(null);
  const [detailTab, setDetailTab] = useState<'instructions' | 'history' | 'pr'>('instructions');

  const [favorites, setFavorites] = useState<string[]>(loadFavorites);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  const { data: exercises, loading, execute: searchExercises } = useAPI(
    (params: any) => ExerciseAPI.searchExercises(params)
  );

  useEffect(() => {
    handleSearch();
  }, [searchQuery, selectedCategory, selectedDifficulty, selectedMuscles, selectedEquipments]);

  useEffect(() => {
    localStorage.setItem(FAV_KEY, JSON.stringify(favorites));
  }, [favorites]);

  const handleSearch = async () => {
    const params: any = {};
    if (searchQuery) params.name_query = searchQuery;
    if (selectedCategory) params.category = selectedCategory;
    if (selectedDifficulty) params.difficulty_level = selectedDifficulty;
    if (selectedMuscles.length > 0) params.muscle_groups = selectedMuscles;
    if (selectedEquipments.length > 0) params.equipment = selectedEquipments;
    params.limit = 50;
    await searchExercises(params);
  };

  const toggleFavorite = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setFavorites(prev =>
      prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]
    );
  };

  const toggleMuscleFilter = (muscle: string) => {
    setSelectedMuscles(prev =>
      prev.includes(muscle) ? prev.filter(m => m !== muscle) : [...prev, muscle]
    );
  };

  const toggleEquipmentFilter = (equip: string) => {
    setSelectedEquipments(prev =>
      prev.includes(equip) ? prev.filter(e => e !== equip) : [...prev, equip]
    );
  };

  const categories = ['Strength', 'Cardio', 'Flexibility', 'Balance', 'Plyometric'];
  const difficulties = ['Beginner', 'Intermediate', 'Advanced', 'Expert'];
  const muscleGroups = ['Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core', 'Full Body'];
  const equipments = ['Barbell', 'Dumbbell', 'Machine', 'Bodyweight', 'Cable', 'Kettlebell'];

  const displayExercises = showFavoritesOnly && exercises
    ? exercises.filter((ex: any) => favorites.includes(ex.id))
    : exercises;

  // Mock past history logs for Hevy-style preview
  const getMockHistory = (exerciseName: string) => {
    return [
      { date: '2026-06-12', sets: [
        { reps: 10, weight: 60 },
        { reps: 8, weight: 65 },
        { reps: 6, weight: 70 }
      ]},
      { date: '2026-06-05', sets: [
        { reps: 10, weight: 55 },
        { reps: 10, weight: 60 },
        { reps: 8, weight: 62.5 }
      ]},
      { date: '2026-05-29', sets: [
        { reps: 12, weight: 50 },
        { reps: 10, weight: 55 },
        { reps: 10, weight: 55 }
      ]}
    ];
  };

  // 1RM calculator helper using Epley formula
  const calculatePRs = (exerciseName: string) => {
    const history = getMockHistory(exerciseName);
    let maxWeight = 0;
    let maxReps = 0;
    let totalVolume = 0;

    history.forEach(session => {
      session.sets.forEach(set => {
        totalVolume += set.reps * set.weight;
        if (set.weight > maxWeight) {
          maxWeight = set.weight;
          maxReps = set.reps;
        }
      });
    });

    const estimated1RM = maxWeight * (1 + maxReps / 30);

    return {
      maxWeight: maxWeight,
      bestReps: maxReps,
      totalVolume: totalVolume,
      estimated1RM: Math.round(estimated1RM * 10) / 10
    };
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 text-white relative">
      {/* Sidebar Filter Layout (1/4 width on desktop) */}
      <aside className="lg:col-span-3 space-y-6 bg-slate-950/40 border border-white/5 p-6 rounded-[2rem] backdrop-blur-xl h-fit lg:sticky lg:top-8">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 mb-6">
            <Filter size={18} />
            <h4 className="font-black uppercase tracking-widest text-xs">Library Filters</h4>
          </div>
          <button 
            onClick={() => { setSelectedMuscles([]); setSelectedEquipments([]); setSelectedCategory(''); setSelectedDifficulty(''); }}
            className="text-[10px] font-black uppercase tracking-widest text-emerald-400/70 hover:text-emerald-400 underline mb-4 block"
          >
            Clear All Filters
          </button>
        </div>

        {/* Categories Select */}
        <div className="space-y-3">
          <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500">Category</label>
          <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-xs text-white focus:outline-none focus:border-emerald-500/50">
            <option value="">All Categories</option>
            {categories.map((cat) => <option key={cat} value={cat}>{cat}</option>)}
          </select>
        </div>

        {/* Difficulties Select */}
        <div className="space-y-3">
          <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500">Difficulty</label>
          <select value={selectedDifficulty} onChange={(e) => setSelectedDifficulty(e.target.value)}
            className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-xs text-white focus:outline-none focus:border-emerald-500/50">
            <option value="">All Difficulties</option>
            {difficulties.map((diff) => <option key={diff} value={diff}>{diff}</option>)}
          </select>
        </div>

        {/* Muscles Group Checkboxes */}
        <div className="space-y-3">
          <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500">Target Muscles</label>
          <div className="space-y-2.5 max-h-48 overflow-y-auto pr-2">
            {muscleGroups.map(muscle => {
              const checked = selectedMuscles.includes(muscle);
              return (
                <label key={muscle} className="flex items-center space-x-3 text-xs font-bold text-slate-300 cursor-pointer hover:text-white transition">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleMuscleFilter(muscle)}
                    className="w-4.5 h-4.5 border border-white/10 rounded bg-slate-900 text-emerald-500 focus:ring-0 focus:ring-offset-0 focus:outline-none"
                  />
                  <span>{muscle}</span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Equipment Checkboxes */}
        <div className="space-y-3 border-t border-white/5 pt-4">
          <label className="block text-[10px] font-black uppercase tracking-widest text-slate-500">Equipment</label>
          <div className="space-y-2.5 max-h-48 overflow-y-auto pr-2">
            {equipments.map(equip => {
              const checked = selectedEquipments.includes(equip);
              return (
                <label key={equip} className="flex items-center space-x-3 text-xs font-bold text-slate-300 cursor-pointer hover:text-white transition">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleEquipmentFilter(equip)}
                    className="w-4.5 h-4.5 border border-white/10 rounded bg-slate-900 text-emerald-500 focus:ring-0 focus:ring-offset-0 focus:outline-none"
                  />
                  <span>{equip}</span>
                </label>
              );
            })}
          </div>
        </div>
      </aside>

      {/* Exercises View (3/4 width on desktop) */}
      <main className="lg:col-span-9 space-y-6">
        {/* Sticky Header with Search */}
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-slate-950/20 p-5 rounded-[2rem] border border-white/5 backdrop-blur-xl">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search exercise catalogue..."
              className="w-full bg-slate-900 border border-white/10 rounded-2xl py-3.5 pl-12 pr-4 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-emerald-500/50 transition"
            />
          </div>

          <div className="flex space-x-2 shrink-0">
            {favorites.length > 0 && (
              <button 
                onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                className={`flex items-center space-x-2 px-4 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${
                  showFavoritesOnly 
                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' 
                    : 'bg-slate-900 border border-white/10 text-slate-400 hover:text-slate-200'
                }`}
              >
                <Heart size={14} className={showFavoritesOnly ? 'fill-rose-400 text-rose-400' : ''} />
                <span>Favorites ({favorites.length})</span>
              </button>
            )}
          </div>
        </div>

        {/* Exercises Grid */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="animate-spin text-emerald-400" size={40} />
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Querying database...</p>
          </div>
        ) : displayExercises && displayExercises.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 stagger-children">
            {displayExercises.map((exercise: any) => {
              const isFav = favorites.includes(exercise.id);
              const primaryMuscle = exercise.muscle_groups?.[0] || 'Full Body';
              return (
                <div 
                  key={exercise.id} 
                  onClick={() => { setExpandedExercise(exercise); setDetailTab('instructions'); }}
                  className="bg-slate-950/40 border border-white/5 rounded-3xl overflow-hidden hover:border-emerald-500/30 cursor-pointer transition-all duration-300 flex flex-col group card-hover"
                >
                  {/* stick figure preview */}
                  <div className="p-4 bg-slate-950/50">
                    <ExerciseStickFigure name={exercise.name} primaryMuscle={primaryMuscle} />
                  </div>

                  <div className="p-5 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start gap-2">
                        <h4 className="font-black italic text-lg text-white group-hover:text-emerald-400 transition-colors uppercase tracking-tight line-clamp-1">{exercise.name}</h4>
                        <button 
                          onClick={(e) => toggleFavorite(exercise.id, e)}
                          className={`p-2 rounded-xl transition-all shrink-0 ${
                            isFav ? 'text-rose-400 bg-rose-500/10' : 'text-slate-600 hover:text-rose-400 hover:bg-rose-500/5'
                          }`}
                        >
                          <Heart size={14} className={isFav ? 'fill-rose-400' : ''} />
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        <span className="text-[8px] font-black bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20 uppercase tracking-wider">{exercise.category}</span>
                        <span className="text-[8px] font-black bg-orange-500/10 text-orange-400 px-2 py-0.5 rounded border border-orange-500/20 uppercase tracking-wider">{exercise.difficulty_level}</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-slate-500">
                      <span>{primaryMuscle}</span>
                      <ChevronRight size={14} className="text-slate-600 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-24 text-center border border-white/5 bg-slate-950/40 rounded-[2rem] text-slate-500">
            <Dumbbell className="mx-auto mb-4 text-slate-700 animate-pulse" size={48} />
            <p className="text-sm font-bold uppercase tracking-widest">No exercises match filters</p>
            <p className="text-xs text-slate-600 mt-2">Try clearing search parameters or tags.</p>
          </div>
        )}
      </main>

      {/* Premium Detail Modal Overlay */}
      {expandedExercise && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-md" onClick={() => setExpandedExercise(null)} />
          
          <div className="relative w-full max-w-2xl bg-[#020617] border border-white/10 rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.6)] overflow-hidden z-10 flex flex-col max-h-[85vh]">
            <header className="p-6 border-b border-white/5 flex justify-between items-center bg-slate-950/40">
              <div>
                <h3 className="text-2xl font-black italic tracking-tighter text-white uppercase">{expandedExercise.name}</h3>
                <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-500 mt-1">
                  {expandedExercise.category} • {expandedExercise.difficulty_level}
                </p>
              </div>
              <button 
                onClick={() => setExpandedExercise(null)}
                className="w-10 h-10 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl flex items-center justify-center text-slate-400 hover:text-white transition"
              >
                <X size={18} />
              </button>
            </header>

            <div className="overflow-y-auto p-6 md:p-8 space-y-6 flex-1">
              {/* Large Animation Visual Guide */}
              <div className="bg-slate-950/60 p-4 rounded-2xl border border-white/5">
                <ExerciseStickFigure 
                  name={expandedExercise.name} 
                  primaryMuscle={expandedExercise.muscle_groups?.[0] || 'Full Body'} 
                  large={true} 
                />
              </div>

              {/* Hevy-style Tab Bar */}
              <div className="flex bg-slate-950 p-1.5 rounded-2xl border border-white/5">
                <button 
                  onClick={() => setDetailTab('instructions')}
                  className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
                    detailTab === 'instructions' ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.3)]' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  Instructions
                </button>
                <button 
                  onClick={() => setDetailTab('history')}
                  className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
                    detailTab === 'history' ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.3)]' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  History logs
                </button>
                <button 
                  onClick={() => setDetailTab('pr')}
                  className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
                    detailTab === 'pr' ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.3)]' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  PR Stats
                </button>
              </div>

              {/* Tab Contents */}
              <div className="space-y-4 min-h-[160px]">
                {detailTab === 'instructions' && (
                  <div className="space-y-4">
                    <div>
                      <h5 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Form Execution</h5>
                      <p className="text-sm text-slate-300 leading-relaxed font-medium bg-slate-950/30 p-4 rounded-xl border border-white/5">
                        {expandedExercise.instructions}
                      </p>
                    </div>
                    {expandedExercise.safety_notes && (
                      <div className="bg-orange-500/5 p-4 rounded-xl border border-orange-500/20">
                        <div className="flex items-center space-x-2 text-orange-400 mb-2">
                          <Info size={14} />
                          <h5 className="text-[10px] font-black uppercase tracking-widest">Safety Guidelines</h5>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed font-semibold">{expandedExercise.safety_notes}</p>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h5 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Target Muscles</h5>
                        <div className="flex flex-wrap gap-1.5">
                          {expandedExercise.muscle_groups?.map((m: string) => (
                            <span key={m} className="text-[9px] font-black bg-purple-500/10 text-purple-400 px-2.5 py-1 rounded border border-purple-500/20 uppercase tracking-wider">{m}</span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h5 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Equipment Required</h5>
                        <div className="flex flex-wrap gap-1.5">
                          {expandedExercise.equipment?.map((eq: string) => (
                            <span key={eq} className="text-[9px] font-black bg-slate-900 border border-white/10 text-slate-300 px-2.5 py-1 rounded uppercase tracking-wider">{eq}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {detailTab === 'history' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between text-slate-500 text-[10px] font-black uppercase tracking-widest">
                      <span>Past Session Dates</span>
                      <span>Sets Done</span>
                    </div>
                    <div className="space-y-3">
                      {getMockHistory(expandedExercise.name).map((log, idx) => (
                        <div key={idx} className="bg-slate-950/50 p-4 border border-white/5 rounded-2xl space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-black text-emerald-400 flex items-center">
                              <Calendar size={12} className="mr-1.5" /> {log.date}
                            </span>
                            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Completed</span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/5 text-center text-xs text-slate-300">
                            {log.sets.map((set, sIdx) => (
                              <div key={sIdx} className="bg-slate-900/40 p-2 rounded-lg">
                                <span className="block text-[8px] text-slate-600 font-bold uppercase mb-0.5">Set {sIdx + 1}</span>
                                <span className="font-bold">{set.reps} reps @ {set.weight}kg</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {detailTab === 'pr' && (
                  <div className="space-y-4">
                    {/* PR Stats Cards */}
                    {(() => {
                      const prs = calculatePRs(expandedExercise.name);
                      return (
                        <div className="space-y-4">
                          <div className="grid grid-cols-3 gap-4">
                            <div className="bg-slate-950 border border-white/5 p-4 rounded-2xl text-center relative group overflow-hidden">
                              <div className="absolute top-0 right-0 p-3 text-emerald-500/5 group-hover:text-emerald-500/10">
                                <Trophy size={48} />
                              </div>
                              <span className="block text-[8px] font-black uppercase tracking-widest text-slate-500 mb-1">Estimated 1RM</span>
                              <span className="text-2xl font-black italic text-emerald-400">{prs.estimated1RM} <span className="text-[10px] text-slate-500 not-italic">kg</span></span>
                            </div>
                            <div className="bg-slate-950 border border-white/5 p-4 rounded-2xl text-center relative group overflow-hidden">
                              <span className="block text-[8px] font-black uppercase tracking-widest text-slate-500 mb-1">Max Lift Weight</span>
                              <span className="text-2xl font-black italic text-white">{prs.maxWeight} <span className="text-[10px] text-slate-500 not-italic">kg</span></span>
                            </div>
                            <div className="bg-slate-950 border border-white/5 p-4 rounded-2xl text-center relative group overflow-hidden">
                              <span className="block text-[8px] font-black uppercase tracking-widest text-slate-500 mb-1">Total volume</span>
                              <span className="text-2xl font-black italic text-blue-400">{prs.totalVolume} <span className="text-[10px] text-slate-500 not-italic">kg</span></span>
                            </div>
                          </div>

                          <div className="bg-emerald-500/5 p-5 rounded-2xl border border-emerald-500/20 flex items-start space-x-4">
                            <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400">
                              <Sparkles size={18} />
                            </div>
                            <div>
                              <h5 className="text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-1">1-Rep Max Insight</h5>
                              <p className="text-xs text-slate-300 leading-relaxed font-medium">
                                Your estimated 1-Rep Max is calculated via Epley formula based on your best historical set: {prs.maxWeight}kg for {prs.bestReps} reps. Keep targeting heavy progressive overload!
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExerciseBrowser;
