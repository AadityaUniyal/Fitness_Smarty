import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, Dumbbell, Utensils, Camera, Footprints, Image, Moon, 
  CalendarDays, Bell, Watch, Move, Clock, TrendingUp, Activity, 
  Trophy, Heart, Calendar, Mic, Droplets, Brain, X 
} from 'lucide-react';

interface CommandItem {
  id: string;
  title: string;
  category: string;
  path: string;
  icon: React.ElementType;
  keywords: string[];
}

const COMMAND_ITEMS: CommandItem[] = [
  { id: 'dash', title: 'Dashboard & AI Coach', category: 'Navigation', path: '/dashboard', icon: TrendingUp, keywords: ['home', 'dashboard', 'coach', 'summary'] },
  { id: 'scanner', title: 'Food Scanner (Vision AI)', category: 'Nutrition', path: '/dashboard/food-scanner', icon: Camera, keywords: ['scan', 'food', 'meal', 'camera', 'yolo', 'gemini'] },
  { id: 'workout', title: 'Workout Assistant', category: 'Training', path: '/dashboard/workout', icon: Dumbbell, keywords: ['workout', 'exercise', 'gym', 'train', 'lift'] },
  { id: 'exercise-lib', title: 'Exercise Library', category: 'Training', path: '/dashboard/exercises', icon: Dumbbell, keywords: ['library', 'exercises', 'muscle', 'bench', 'squat'] },
  { id: 'quick-wk', title: 'Quick Workout', category: 'Training', path: '/dashboard/quick', icon: Dumbbell, keywords: ['quick', 'fast', 'hiit', 'burn', 'cardio'] },
  { id: 'activity', title: 'Activity Tracker', category: 'Analytics', path: '/dashboard/activity', icon: Footprints, keywords: ['activity', 'steps', 'running', 'gps', 'distance'] },
  { id: 'meal-plan', title: 'Meal Planner', category: 'Nutrition', path: '/dashboard/meal-planner', icon: CalendarDays, keywords: ['meal', 'plan', 'diet', 'macros', 'calories'] },
  { id: 'hydration', title: 'Hydration Hub', category: 'Health', path: '/dashboard/hydration', icon: Droplets, keywords: ['water', 'hydration', 'drink', 'ml', 'tracker'] },
  { id: 'femmecare', title: 'FemmeCare Female Health', category: 'Health', path: '/dashboard/femmecare', icon: Heart, keywords: ['female', 'period', 'cycle', 'menstrual', 'hormone'] },
  { id: 'form-coach', title: 'AI Form Coach', category: 'Training', path: '/dashboard/form-coach', icon: Move, keywords: ['form', 'posture', 'coach', 'pose', 'squat form'] },
  { id: 'progress', title: 'Progress & Biometrics', category: 'Analytics', path: '/dashboard/progress', icon: Activity, keywords: ['progress', 'weight', 'chart', 'body fat', 'bmi'] },
  { id: 'photos', title: 'Progress Photos', category: 'Analytics', path: '/dashboard/photos', icon: Image, keywords: ['photos', 'visual', 'body', 'physique'] },
  { id: 'sleep', title: 'Sleep Tracker', category: 'Health', path: '/dashboard/sleep', icon: Moon, keywords: ['sleep', 'rest', 'rem', 'recovery'] },
  { id: 'voice-coach', title: 'Voice AI Coach', category: 'AI Tools', path: '/dashboard/coach', icon: Mic, keywords: ['voice', 'chat', 'mic', 'audio', 'coach'] },
  { id: 'achievements', title: 'Achievements & Streaks', category: 'Gamification', path: '/dashboard/achievements', icon: Trophy, keywords: ['streak', 'badges', 'trophy', 'points', 'level'] },
];

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();

  const filteredItems = COMMAND_ITEMS.filter((item) => {
    const q = query.toLowerCase().trim();
    if (!q) return true;
    return (
      item.title.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      item.keywords.some((k) => k.toLowerCase().includes(q))
    );
  });

  const handleSelect = (item: CommandItem) => {
    setIsOpen(false);
    setQuery('');
    navigate(item.path);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      } else if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      } else if (isOpen) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredItems.length));
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % Math.max(1, filteredItems.length));
        } else if (e.key === 'Enter' && filteredItems[selectedIndex]) {
          e.preventDefault();
          handleSelect(filteredItems[selectedIndex]);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredItems]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[60] flex items-start justify-center pt-20 px-4 bg-slate-950/80 backdrop-blur-md fade-in"
      onClick={() => setIsOpen(false)}
      role="dialog"
      aria-modal="true"
      aria-label="Global Feature Search"
    >
      <div 
        className="w-full max-w-2xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden scale-in card-3d"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="card-3d-shine" />
        {/* Search Header */}
        <div className="flex items-center px-4 border-b border-white/10">
          <Search className="w-5 h-5 text-emerald-400 mr-3 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Search any feature, exercise, meal scanner or tool... (Cmd+K)"
            className="w-full py-4 bg-transparent text-slate-100 placeholder-slate-500 focus:outline-none text-base"
            autoFocus
          />
          {query && (
            <button 
              onClick={() => setQuery('')}
              className="text-slate-400 hover:text-slate-200 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 px-2 py-1 bg-slate-800 rounded border border-white/10 ml-2">
            ESC
          </span>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 space-y-1 custom-scrollbar">
          {filteredItems.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs uppercase font-bold tracking-widest">
              No matching features found for "{query}".
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between px-4 py-3 rounded-xl cursor-pointer transition-colors ${
                    isSelected ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 shadow-sm' : 'text-slate-300 hover:bg-slate-800/60 border border-transparent'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${isSelected ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-100">{item.title}</p>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{item.category}</p>
                    </div>
                  </div>
                  <span className="text-xs text-slate-500 font-bold uppercase tracking-widest">Jump &rarr;</span>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 bg-slate-950/60 border-t border-white/5 flex justify-between items-center text-[10px] text-slate-400 uppercase font-bold tracking-wider">
          <span>Navigation: <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-white/10 text-slate-300">↑↓</kbd> Select <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-white/10 text-slate-300">↵</kbd> Open</span>
          <span>SMARTY NAV</span>
        </div>
      </div>
    </div>
  );
};

export default CommandPalette;
