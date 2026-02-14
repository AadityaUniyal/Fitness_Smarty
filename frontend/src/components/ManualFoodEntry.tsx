import React, { useState } from 'react';
import { Plus, Save, X } from 'lucide-react';

interface ManualFoodEntryProps {
  onSave: (foodData: any) => void;
  onCancel: () => void;
}

const ManualFoodEntry: React.FC<ManualFoodEntryProps> = ({ onSave, onCancel }) => {
  const [foodData, setFoodData] = useState({
    name: '',
    serving_size: '',
    calories: 0,
    protein: 0,
    carbs: 0,
    fats: 0
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!foodData.name || !foodData.serving_size) {
      alert('Please fill in food name and serving size');
      return;
    }
    onSave(foodData);
  };

  return (
    <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <h4 className="font-bold text-white flex items-center">
          <Plus className="mr-2 text-emerald-400" size={18} />
          Manual Food Entry
        </h4>
        <button
          onClick={onCancel}
          className="text-slate-500 hover:text-white transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">
              Food Name
            </label>
            <input
              type="text"
              value={foodData.name}
              onChange={(e) => setFoodData({ ...foodData, name: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
              placeholder="e.g., Grilled Chicken Breast"
            />
          </div>

          <div>
            <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">
              Serving Size
            </label>
            <input
              type="text"
              value={foodData.serving_size}
              onChange={(e) => setFoodData({ ...foodData, serving_size: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
              placeholder="e.g., 100g, 1 cup"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">
              Calories
            </label>
            <input
              type="number"
              value={foodData.calories || ''}
              onChange={(e) => setFoodData({ ...foodData, calories: Number(e.target.value) })}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
              placeholder="0"
            />
          </div>

          <div>
            <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">
              Protein (g)
            </label>
            <input
              type="number"
              value={foodData.protein || ''}
              onChange={(e) => setFoodData({ ...foodData, protein: Number(e.target.value) })}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
              placeholder="0"
            />
          </div>

          <div>
            <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">
              Carbs (g)
            </label>
            <input
              type="number"
              value={foodData.carbs || ''}
              onChange={(e) => setFoodData({ ...foodData, carbs: Number(e.target.value) })}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
              placeholder="0"
            />
          </div>

          <div>
            <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">
              Fats (g)
            </label>
            <input
              type="number"
              value={foodData.fats || ''}
              onChange={(e) => setFoodData({ ...foodData, fats: Number(e.target.value) })}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
              placeholder="0"
            />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 px-6 py-3 rounded-xl font-bold text-xs uppercase flex items-center space-x-2"
          >
            <Save size={16} />
            <span>Save Food</span>
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-3 rounded-xl font-bold text-xs uppercase"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default ManualFoodEntry;
