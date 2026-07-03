import React, { useState, useEffect, useCallback } from 'react';
import { CalendarDays, Plus, X, Trash2, Check, Search, ChevronLeft, ChevronRight, Utensils, Apple, Beef, Fish, Milk, Wheat, Coffee, Sparkles, Loader2 } from 'lucide-react';
import { FoodAPI, FoodItem, FoodCategory } from '../services/apiService';

const STORAGE_KEY = 'smarty_meal_plan';
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const MEAL_SLOTS = ['breakfast', 'lunch', 'dinner', 'snack'];
const MEAL_COLORS: Record<string, string> = {
  breakfast: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  lunch: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  dinner: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
  snack: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
};
const MEAL_ICONS: Record<string, string> = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '✨' };

interface PlannedMeal {
  foodId: number;
  name: string;
  serving: string;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
}

type WeekPlan = Record<string, Record<string, PlannedMeal[]>>;

const DEFAULT_FOODS: FoodCategory[] = [
  { id: 1, name: 'Protein', items: [
    { id: 1, name: 'Grilled Chicken Breast', category_id: 1, serving_size: '150g', calories: 247, protein: 38, carbs: 0, fats: 9, is_elite: false },
    { id: 2, name: 'Salmon Fillet', category_id: 1, serving_size: '150g', calories: 280, protein: 32, carbs: 0, fats: 16, is_elite: false },
    { id: 3, name: 'Lean Beef Steak', category_id: 1, serving_size: '150g', calories: 260, protein: 40, carbs: 0, fats: 10, is_elite: false },
    { id: 4, name: 'Eggs (2)', category_id: 1, serving_size: '2 eggs', calories: 140, protein: 12, carbs: 1, fats: 10, is_elite: false },
    { id: 5, name: 'Tofu', category_id: 1, serving_size: '150g', calories: 120, protein: 14, carbs: 4, fats: 6, is_elite: false },
    { id: 6, name: 'Greek Yogurt', category_id: 1, serving_size: '200g', calories: 146, protein: 20, carbs: 8, fats: 4, is_elite: false },
    { id: 7, name: 'Whey Protein Shake', category_id: 1, serving_size: '1 scoop', calories: 120, protein: 25, carbs: 3, fats: 1, is_elite: true },
    { id: 8, name: 'Turkey Breast', category_id: 1, serving_size: '150g', calories: 180, protein: 34, carbs: 0, fats: 4, is_elite: false },
    { id: 9, name: 'Shrimp', category_id: 1, serving_size: '150g', calories: 150, protein: 31, carbs: 1, fats: 2, is_elite: false },
    { id: 10, name: 'Cottage Cheese', category_id: 1, serving_size: '200g', calories: 190, protein: 22, carbs: 8, fats: 8, is_elite: false },
  ]},
  { id: 2, name: 'Carbs & Grains', items: [
    { id: 20, name: 'Brown Rice', category_id: 2, serving_size: '1 cup', calories: 216, protein: 5, carbs: 45, fats: 2, is_elite: false },
    { id: 21, name: 'Quinoa', category_id: 2, serving_size: '1 cup', calories: 222, protein: 8, carbs: 39, fats: 4, is_elite: false },
    { id: 22, name: 'Oats', category_id: 2, serving_size: '½ cup', calories: 150, protein: 5, carbs: 27, fats: 3, is_elite: false },
    { id: 23, name: 'Sweet Potato', category_id: 2, serving_size: '1 medium', calories: 103, protein: 2, carbs: 24, fats: 0, is_elite: false },
    { id: 24, name: 'Whole Wheat Pasta', category_id: 2, serving_size: '1 cup', calories: 174, protein: 7, carbs: 37, fats: 1, is_elite: false },
    { id: 25, name: 'Sourdough Bread', category_id: 2, serving_size: '2 slices', calories: 160, protein: 6, carbs: 32, fats: 2, is_elite: false },
    { id: 26, name: 'White Rice', category_id: 2, serving_size: '1 cup', calories: 205, protein: 4, carbs: 45, fats: 0, is_elite: false },
    { id: 27, name: 'Wheat Tortilla', category_id: 2, serving_size: '1 large', calories: 130, protein: 4, carbs: 22, fats: 3, is_elite: false },
  ]},
  { id: 3, name: 'Fruits & Veggies', items: [
    { id: 30, name: 'Banana', category_id: 3, serving_size: '1 medium', calories: 105, protein: 1, carbs: 27, fats: 0, is_elite: false },
    { id: 31, name: 'Apple', category_id: 3, serving_size: '1 medium', calories: 95, protein: 0, carbs: 25, fats: 0, is_elite: false },
    { id: 32, name: 'Blueberries', category_id: 3, serving_size: '1 cup', calories: 84, protein: 1, carbs: 21, fats: 0, is_elite: false },
    { id: 33, name: 'Spinach', category_id: 3, serving_size: '3 cups', calories: 21, protein: 3, carbs: 3, fats: 0, is_elite: false },
    { id: 34, name: 'Broccoli', category_id: 3, serving_size: '1 cup', calories: 55, protein: 4, carbs: 11, fats: 1, is_elite: false },
    { id: 35, name: 'Avocado', category_id: 3, serving_size: '½ fruit', calories: 120, protein: 1, carbs: 6, fats: 11, is_elite: false },
    { id: 36, name: 'Mixed Salad Greens', category_id: 3, serving_size: '2 cups', calories: 20, protein: 2, carbs: 4, fats: 0, is_elite: false },
    { id: 37, name: 'Bell Peppers', category_id: 3, serving_size: '1 cup', calories: 30, protein: 1, carbs: 7, fats: 0, is_elite: false },
    { id: 38, name: 'Strawberries', category_id: 3, serving_size: '1 cup', calories: 56, protein: 1, carbs: 13, fats: 0, is_elite: false },
  ]},
  { id: 4, name: 'Healthy Fats', items: [
    { id: 40, name: 'Almonds', category_id: 4, serving_size: '¼ cup', calories: 207, protein: 7, carbs: 8, fats: 18, is_elite: false },
    { id: 41, name: 'Olive Oil', category_id: 4, serving_size: '1 tbsp', calories: 119, protein: 0, carbs: 0, fats: 14, is_elite: false },
    { id: 42, name: 'Peanut Butter', category_id: 4, serving_size: '2 tbsp', calories: 188, protein: 8, carbs: 7, fats: 16, is_elite: false },
    { id: 43, name: 'Chia Seeds', category_id: 4, serving_size: '1 tbsp', calories: 58, protein: 2, carbs: 5, fats: 4, is_elite: false },
    { id: 44, name: 'Walnuts', category_id: 4, serving_size: '¼ cup', calories: 185, protein: 4, carbs: 4, fats: 18, is_elite: false },
  ]},
  { id: 5, name: 'Dairy & Alternatives', items: [
    { id: 50, name: 'Whole Milk', category_id: 5, serving_size: '1 cup', calories: 149, protein: 8, carbs: 12, fats: 8, is_elite: false },
    { id: 51, name: 'Almond Milk', category_id: 5, serving_size: '1 cup', calories: 39, protein: 1, carbs: 2, fats: 3, is_elite: false },
    { id: 52, name: 'Cheddar Cheese', category_id: 5, serving_size: '30g', calories: 113, protein: 7, carbs: 0, fats: 9, is_elite: false },
    { id: 53, name: 'Mozzarella', category_id: 5, serving_size: '30g', calories: 85, protein: 6, carbs: 1, fats: 6, is_elite: false },
  ]},
  { id: 6, name: 'Snacks & Treats', items: [
    { id: 60, name: 'Dark Chocolate', category_id: 6, serving_size: '30g', calories: 170, protein: 2, carbs: 13, fats: 12, is_elite: false },
    { id: 61, name: 'Rice Cakes', category_id: 6, serving_size: '2 cakes', calories: 70, protein: 1, carbs: 15, fats: 1, is_elite: false },
    { id: 62, name: 'Protein Bar', category_id: 6, serving_size: '1 bar', calories: 200, protein: 20, carbs: 25, fats: 6, is_elite: true },
    { id: 63, name: 'Trail Mix', category_id: 6, serving_size: '¼ cup', calories: 175, protein: 5, carbs: 16, fats: 12, is_elite: false },
    { id: 64, name: 'Granola', category_id: 6, serving_size: '½ cup', calories: 210, protein: 5, carbs: 36, fats: 6, is_elite: false },
  ]},
  { id: 7, name: 'Beverages', items: [
    { id: 70, name: 'Black Coffee', category_id: 7, serving_size: '1 cup', calories: 2, protein: 0, carbs: 0, fats: 0, is_elite: false },
    { id: 71, name: 'Green Tea', category_id: 7, serving_size: '1 cup', calories: 1, protein: 0, carbs: 0, fats: 0, is_elite: false },
    { id: 72, name: 'Orange Juice', category_id: 7, serving_size: '1 cup', calories: 112, protein: 2, carbs: 26, fats: 0, is_elite: false },
  ]},
];

const CATEGORY_ICONS: Record<number, React.ReactNode> = {
  1: <Beef size={14} />, 2: <Wheat size={14} />, 3: <Apple size={14} />,
  4: <Coffee size={14} />, 5: <Milk size={14} />, 6: <Utensils size={14} />, 7: <Coffee size={14} />,
};

const MealPlanner: React.FC = () => {
  const [weekPlan, setWeekPlan] = useState<WeekPlan>(() => {
    try { const saved = localStorage.getItem(STORAGE_KEY); if (saved) return JSON.parse(saved); } catch { }
    const empty: WeekPlan = {};
    DAYS.forEach(d => { empty[d] = {}; MEAL_SLOTS.forEach(s => { empty[d][s] = []; }); });
    return empty;
  });
  const [currentWeekOffset, setCurrentWeekOffset] = useState(0);
  const [foodLibrary, setFoodLibrary] = useState<FoodCategory[]>(DEFAULT_FOODS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [showFoodPanel, setShowFoodPanel] = useState(false);
  const [dragTarget, setDragTarget] = useState<{ day: string; slot: string } | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ day: string; slot: string; idx: number } | null>(null);
  const [activeDay, setActiveDay] = useState(DAYS[new Date().getDay() === 0 ? 6 : new Date().getDay() - 1]);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => { localStorage.setItem(STORAGE_KEY, JSON.stringify(weekPlan)); }, [weekPlan]);

  useEffect(() => {
    FoodAPI.getFoodLibrary().then(lib => { if (lib && lib.length > 0) setFoodLibrary(lib); }).catch(() => {});
  }, []);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2000);
  }, []);

  const getWeekDays = () => {
    const today = new Date();
    const start = new Date(today);
    start.setDate(start.getDate() + currentWeekOffset * 7 - ((today.getDay() + 6) % 7));
    return DAYS.map((_, i) => {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      return d;
    });
  };

  const weekDates = getWeekDays();

  const handleDragStart = (food: FoodItem) => (e: React.DragEvent) => {
    e.dataTransfer.setData('text/plain', JSON.stringify(food));
    e.dataTransfer.effectAllowed = 'copy';
  };

  const handleDragOver = (day: string, slot: string) => (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    setDragTarget({ day, slot });
  };

  const handleDragLeave = () => setDragTarget(null);

  const handleDrop = (day: string, slot: string) => (e: React.DragEvent) => {
    e.preventDefault();
    setDragTarget(null);
    try {
      const food: FoodItem = JSON.parse(e.dataTransfer.getData('text/plain'));
      setWeekPlan(prev => ({
        ...prev,
        [day]: { ...prev[day], [slot]: [...(prev[day][slot] || []), {
          foodId: food.id, name: food.name, serving: food.serving_size,
          calories: food.calories, protein: food.protein, carbs: food.carbs, fats: food.fats,
        }]},
      }));
      showToast(`Added ${food.name} to ${slot}`);
    } catch { }
  };

  const removeFood = (day: string, slot: string, idx: number) => {
    setWeekPlan(prev => ({
      ...prev,
      [day]: { ...prev[day], [slot]: prev[day][slot].filter((_, i) => i !== idx) },
    }));
  };

  const clearSlot = (day: string, slot: string) => {
    setWeekPlan(prev => ({ ...prev, [day]: { ...prev[day], [slot]: [] } }));
  };

  const clearDay = (day: string) => {
    setWeekPlan(prev => {
      const updated = { ...prev[day] };
      MEAL_SLOTS.forEach(s => { updated[s] = []; });
      return { ...prev, [day]: updated };
    });
    showToast(`Cleared ${day}`);
  };

  const [generating, setGenerating] = useState(false);

  const clearWeek = () => {
    const empty: WeekPlan = {};
    DAYS.forEach(d => { empty[d] = {}; MEAL_SLOTS.forEach(s => { empty[d][s] = []; }); });
    setWeekPlan(empty);
    showToast('Cleared entire week');
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const profile = JSON.parse(localStorage.getItem('smarty_profile') || '{}');
      const prefs = {
        week_start: weekDates[0].toISOString().split('T')[0],
        daily_calories: profile.dailyCalorieTarget || 2000,
        goal: profile.goal || profile.fitness_goal || 'general',
        dietary_preferences: profile.dietaryPreferences || profile.dietary_preferences || [],
        allergies: profile.allergies || [],
        exclude_foods: [],
      };
      const token = localStorage.getItem('smarty_access_token');
      let entries: { day_of_week: number; meal_slot: string; food_name: string; serving_size: string; calories: number; protein: number; carbs: number; fats: number }[] = [];
      if (token) {
        const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const res = await fetch(`${API_BASE}/api/meal-plans/generate`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify(prefs),
        });
        if (res.ok) {
          const plan = await res.json();
          entries = plan.entries || [];
        }
      }
      if (entries.length === 0) {
        const { generateWeeklyMealPlan } = await import('../services/geminiService');
        entries = await generateWeeklyMealPlan({
          goal: prefs.goal, dailyCalories: prefs.daily_calories,
          dietaryRestrictions: prefs.dietary_preferences, allergies: prefs.allergies,
        });
      }
      if (entries.length > 0) {
        const newPlan: WeekPlan = {};
        DAYS.forEach(d => { newPlan[d] = {}; MEAL_SLOTS.forEach(s => { newPlan[d][s] = []; }); });
        let counter = 0;
        for (const e of entries) {
          const day = DAYS[e.day_of_week];
          newPlan[day][e.meal_slot] = [...(newPlan[day][e.meal_slot] || []), {
            foodId: counter++, name: e.food_name, serving: e.serving_size || '1 serving',
            calories: e.calories || 0, protein: e.protein || 0, carbs: e.carbs || 0, fats: e.fats || 0,
          }];
        }
        setWeekPlan(newPlan);
        showToast('AI-generated meal plan ready!');
      }
    } catch (e) {
      console.error('Generate failed:', e);
      showToast('Generation failed, try again');
    } finally {
      setGenerating(false);
    }
  };

  const getTotals = (day: string) => {
    const meals = MEAL_SLOTS.flatMap(s => weekPlan[day]?.[s] || []);
    return {
      calories: meals.reduce((s, m) => s + m.calories, 0),
      protein: meals.reduce((s, m) => s + m.protein, 0),
      carbs: meals.reduce((s, m) => s + m.carbs, 0),
      fats: meals.reduce((s, m) => s + m.fats, 0),
      count: meals.length,
    };
  };

  const getWeeklyTotals = () => {
    const totals = DAYS.map(d => getTotals(d));
    return {
      calories: totals.reduce((s, t) => s + t.calories, 0),
      protein: totals.reduce((s, t) => s + t.protein, 0),
      carbs: totals.reduce((s, t) => s + t.carbs, 0),
      fats: totals.reduce((s, t) => s + t.fats, 0),
      meals: totals.reduce((s, t) => s + t.count, 0),
    };
  };

  const weekly = getWeeklyTotals();
  const filteredFoods = foodLibrary
    .filter(c => !selectedCategory || c.id === selectedCategory)
    .map(c => ({ ...c, items: c.items.filter(f =>
      !searchQuery || f.name.toLowerCase().includes(searchQuery.toLowerCase())
    ) }))
    .filter(c => c.items.length > 0);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Toast */}
      {toast && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-emerald-500/20 border border-emerald-500/30 rounded-2xl text-emerald-400 text-[10px] font-black uppercase tracking-widest backdrop-blur-xl animate-fade-in">
          {toast}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl flex items-center justify-center text-emerald-400">
            <CalendarDays size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Meal Planner</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Drag & drop to plan your week</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={handleGenerate} disabled={generating}
            className="flex items-center space-x-2 px-5 py-3 bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
            {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            <span>{generating ? 'Generating...' : 'Generate with AI'}</span>
          </button>
          <button onClick={() => setShowFoodPanel(!showFoodPanel)}
            className="flex items-center space-x-2 px-5 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
            <Utensils size={16} />
            <span>Food Library</span>
          </button>
          <button onClick={clearWeek}
            className="px-5 py-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-rose-500/20 transition">
            Clear Week
          </button>
        </div>
      </div>

      {/* Week summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Total Calories', value: weekly.calories, unit: 'kcal', color: 'text-emerald-400' },
          { label: 'Total Protein', value: weekly.protein, unit: 'g', color: 'text-amber-400' },
          { label: 'Total Carbs', value: weekly.carbs, unit: 'g', color: 'text-blue-400' },
          { label: 'Total Fats', value: weekly.fats, unit: 'g', color: 'text-rose-400' },
          { label: 'Meals Planned', value: weekly.meals, unit: '', color: 'text-indigo-400' },
        ].map((stat, i) => (
          <div key={i} className="glass-panel p-4 rounded-2xl border border-white/5">
            <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</p>
            <p className={`text-xl font-black ${stat.color} mt-0.5`}>{stat.value.toLocaleString()}<span className="text-xs text-slate-600 ml-1">{stat.unit}</span></p>
          </div>
        ))}
      </div>

      {/* Week navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button onClick={() => setCurrentWeekOffset(prev => prev - 1)}
            className="p-2 rounded-xl hover:bg-white/5 text-slate-500 hover:text-white transition">
            <ChevronLeft size={18} />
          </button>
          <span className="text-[11px] font-black text-slate-400 uppercase tracking-widest">
            {weekDates[0].toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} — {weekDates[6].toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </span>
          <button onClick={() => setCurrentWeekOffset(prev => prev + 1)}
            className="p-2 rounded-xl hover:bg-white/5 text-slate-500 hover:text-white transition">
            <ChevronRight size={18} />
          </button>
          {currentWeekOffset !== 0 && (
            <button onClick={() => setCurrentWeekOffset(0)}
              className="text-[9px] font-black text-emerald-500 uppercase tracking-widest hover:text-emerald-400 transition">
              Today
            </button>
          )}
        </div>
        {/* Day tabs */}
        <div className="flex space-x-1">
          {DAYS.map((d, i) => {
            const isToday = weekDates[i].toDateString() === new Date().toDateString();
            const isActive = activeDay === d;
            return (
              <button key={d} onClick={() => setActiveDay(d)}
                className={`px-3 py-2 rounded-xl text-[8px] font-black uppercase tracking-widest transition-all
                  ${isActive ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-600 hover:text-slate-400 border border-transparent'}
                  ${isToday && !isActive ? 'text-emerald-500/60' : ''}`}>
                {d.slice(0, 3)}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex gap-6">
        {/* Main weekly grid */}
        <div className="flex-1 min-w-0 space-y-4">
          {DAYS.map((day, dayIdx) => {
            const date = weekDates[dayIdx];
            const isActive = activeDay === day;
            if (!isActive) return null;
            const totals = getTotals(day);
            return (
              <div key={day} className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
                <div className="flex items-center justify-between p-5 border-b border-white/5 bg-white/[0.02]">
                  <div className="flex items-center space-x-4">
                    <span className="text-base font-black text-white">{day}</span>
                    <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">
                      {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                    {date.toDateString() === new Date().toDateString() && (
                      <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[8px] font-black uppercase tracking-widest rounded-full">Today</span>
                    )}
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-[9px] text-slate-500 font-black">{totals.calories.toLocaleString()} kcal</span>
                    <span className="text-[9px] text-amber-400 font-black">{totals.protein}g P</span>
                    <span className="text-[9px] text-blue-400 font-black">{totals.carbs}g C</span>
                    <span className="text-[9px] text-rose-400 font-black">{totals.fats}g F</span>
                    <button onClick={() => clearDay(day)}
                      className="p-1.5 rounded-lg hover:bg-rose-500/10 text-rose-400/50 hover:text-rose-400 transition" title="Clear day">
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4">
                  {MEAL_SLOTS.map(slot => {
                    const meals = weekPlan[day]?.[slot] || [];
                    const slotCals = meals.reduce((s, m) => s + m.calories, 0);
                    const slotProtein = meals.reduce((s, m) => s + m.protein, 0);
                    const isOver = dragTarget?.day === day && dragTarget?.slot === slot;
                    return (
                      <div key={slot}
                        onDragOver={handleDragOver(day, slot)}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop(day, slot)}
                        className={`rounded-2xl border-2 border-dashed p-3 min-h-[120px] transition-all ${
                          isOver ? 'border-emerald-400/50 bg-emerald-500/5' : 'border-white/5 hover:border-white/10'
                        } ${MEAL_COLORS[slot].split(' ').slice(1).join(' ')}`}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm">{MEAL_ICONS[slot]}</span>
                            <span className={`text-[9px] font-black uppercase tracking-widest ${MEAL_COLORS[slot].split(' ')[0]}`}>
                              {slot}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-[8px] text-slate-500 font-black">{slotCals > 0 ? `${slotCals} kcal` : ''}</span>
                            {meals.length > 0 && (
                              <button onClick={() => clearSlot(day, slot)}
                                className="p-1 rounded-md hover:bg-rose-500/10 text-rose-400/50 hover:text-rose-400 transition">
                                <X size={10} />
                              </button>
                            )}
                          </div>
                        </div>
                        {meals.length > 0 ? (
                          <div className="space-y-1.5">
                            {meals.map((meal, mi) => (
                              <div key={mi}
                                className="flex items-center justify-between group px-2.5 py-1.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] transition-all">
                                <div className="flex items-center space-x-2 min-w-0">
                                  <span className="text-[10px] font-black text-white truncate">{meal.name}</span>
                                  <span className="text-[7px] text-slate-600 whitespace-nowrap">{meal.serving}</span>
                                </div>
                                <div className="flex items-center space-x-2 shrink-0">
                                  <span className="text-[8px] text-slate-500 font-black">{meal.calories}cal</span>
                                  <button onClick={() => {
                                    if (deleteConfirm?.day === day && deleteConfirm?.slot === slot && deleteConfirm?.idx === mi) {
                                      removeFood(day, slot, mi);
                                      setDeleteConfirm(null);
                                    } else {
                                      setDeleteConfirm({ day, slot, idx: mi });
                                      setTimeout(() => setDeleteConfirm(null), 3000);
                                    }
                                  }}
                                    className="p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-rose-500/10 text-rose-400/60 hover:text-rose-400 transition">
                                    {deleteConfirm?.day === day && deleteConfirm?.slot === slot && deleteConfirm?.idx === mi
                                      ? <Check size={10} /> : <Trash2 size={10} />}
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-[9px] text-slate-600 font-black uppercase tracking-widest mt-4 text-center">
                            Drop food here
                          </p>
                        )}
                        {slotProtein > 0 && (
                          <p className="text-[7px] text-amber-400/60 font-black mt-2">{slotProtein}g protein</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Food Library Panel */}
        {showFoodPanel && (
          <div className="w-80 shrink-0 glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden h-[calc(100vh-220px)] sticky top-6">
            <div className="p-5 border-b border-white/5 space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Food Library</p>
                <button onClick={() => setShowFoodPanel(false)} className="p-1 rounded-lg hover:bg-white/5 text-slate-500">
                  <X size={14} />
                </button>
              </div>
              <div className="relative">
                <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
                <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search foods..."
                  className="w-full bg-slate-950 border border-white/10 rounded-xl pl-8 pr-3 py-2.5 text-[10px] text-white placeholder:text-slate-600 font-medium" />
              </div>
              <div className="flex flex-wrap gap-1.5">
                <button onClick={() => setSelectedCategory(null)}
                  className={`px-2.5 py-1 rounded-lg text-[7px] font-black uppercase tracking-widest transition-all
                    ${!selectedCategory ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-900 text-slate-500 border border-slate-800 hover:text-slate-400'}`}>
                  All
                </button>
                {foodLibrary.map(c => (
                  <button key={c.id} onClick={() => setSelectedCategory(selectedCategory === c.id ? null : c.id)}
                    className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[7px] font-black uppercase tracking-widest transition-all
                      ${selectedCategory === c.id ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-900 text-slate-500 border border-slate-800 hover:text-slate-400'}`}>
                    {CATEGORY_ICONS[c.id]}
                    <span>{c.name}</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="overflow-y-auto h-full pb-20">
              {filteredFoods.map(cat => (
                <div key={cat.id}>
                  <div className="px-5 py-2 border-b border-white/5 bg-white/[0.01]">
                    <p className="text-[8px] font-black text-slate-600 uppercase tracking-widest">{cat.name}</p>
                  </div>
                  <div>
                    {cat.items.map(food => (
                      <div key={food.id} draggable
                        onDragStart={handleDragStart(food)}
                        className="flex items-center justify-between px-5 py-3 hover:bg-white/[0.03] transition-colors cursor-grab active:cursor-grabbing border-b border-white/[0.02] group">
                        <div className="min-w-0 flex-1">
                          <p className="text-[10px] font-black text-white truncate">
                            {food.name}
                            {food.is_elite && <span className="ml-1.5 text-[7px] text-amber-500">ELITE</span>}
                          </p>
                          <div className="flex items-center space-x-3 mt-0.5">
                            <span className="text-[7px] text-slate-600">{food.serving_size}</span>
                            <span className="text-[7px] text-emerald-500 font-black">{food.calories} cal</span>
                            <span className="text-[7px] text-amber-500 font-black">{food.protein}g P</span>
                            <span className="text-[7px] text-blue-500 font-black">{food.carbs}g C</span>
                            <span className="text-[7px] text-rose-500 font-black">{food.fats}g F</span>
                          </div>
                        </div>
                        <div className="opacity-0 group-hover:opacity-100 transition p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 ml-2">
                          <Plus size={10} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {filteredFoods.length === 0 && (
                <div className="p-8 text-center">
                  <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">No foods found</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MealPlanner;
