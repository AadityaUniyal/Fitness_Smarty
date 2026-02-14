import React, { useState, useEffect } from 'react';
import { History, Calendar, TrendingUp, Loader2 } from 'lucide-react';
import { MealAPI } from '../services/apiService';
import { useAPI } from '../hooks/useAPI';

const MealHistory: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  
  const { data: history, loading, execute: fetchHistory } = useAPI(
    (userId: string, params: any) => MealAPI.getMealHistory(userId, params)
  );

  const { data: dailySummary, execute: fetchSummary } = useAPI(
    (userId: string, date: string) => MealAPI.getDailySummary(userId, date)
  );

  useEffect(() => {
    loadData();
  }, [selectedDate]);

  const loadData = async () => {
    await fetchHistory('user-1', {
      start_date: selectedDate,
      end_date: selectedDate,
      limit: 20
    });
    await fetchSummary('user-1', selectedDate);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold flex items-center">
          <History className="mr-3 text-cyan-400" size={20} />
          Meal History
        </h3>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-xs text-slate-300"
        />
      </div>

      {dailySummary && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-slate-800/50 p-4 rounded-xl text-center">
            <p className="text-[10px] font-black text-slate-500 uppercase">Total Calories</p>
            <p className="text-lg font-bold text-emerald-400">{dailySummary.total_calories}</p>
          </div>
          <div className="bg-slate-800/50 p-4 rounded-xl text-center">
            <p className="text-[10px] font-black text-slate-500 uppercase">Protein</p>
            <p className="text-lg font-bold text-blue-400">{dailySummary.total_protein_g}g</p>
          </div>
          <div className="bg-slate-800/50 p-4 rounded-xl text-center">
            <p className="text-[10px] font-black text-slate-500 uppercase">Carbs</p>
            <p className="text-lg font-bold text-orange-400">{dailySummary.total_carbs_g}g</p>
          </div>
          <div className="bg-slate-800/50 p-4 rounded-xl text-center">
            <p className="text-[10px] font-black text-slate-500 uppercase">Fats</p>
            <p className="text-lg font-bold text-purple-400">{dailySummary.total_fat_g}g</p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="py-12 flex justify-center">
          <Loader2 className="animate-spin text-cyan-400" size={32} />
        </div>
      ) : history && history.meals.length > 0 ? (
        <div className="space-y-3">
          {history.meals.map((meal) => (
            <div key={meal.meal_log_id} className="bg-slate-800/30 p-4 rounded-xl border border-slate-700/50 hover:border-cyan-500/30 transition-all">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-bold text-white capitalize">{meal.meal_type}</p>
                  <p className="text-xs text-slate-500">{new Date(meal.logged_at).toLocaleTimeString()}</p>
                </div>
                <span className="text-xs font-black bg-cyan-400/10 text-cyan-400 px-3 py-1 rounded-full">
                  {meal.total_calories} CAL
                </span>
              </div>
              <div className="mt-3 flex gap-4 text-xs">
                <span className="text-blue-400">P: {meal.total_protein_g}g</span>
                <span className="text-orange-400">C: {meal.total_carbs_g}g</span>
                <span className="text-purple-400">F: {meal.total_fat_g}g</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-12 text-center text-slate-500">
          <p className="text-sm">No meals logged for this date</p>
        </div>
      )}
    </div>
  );
};

export default MealHistory;
