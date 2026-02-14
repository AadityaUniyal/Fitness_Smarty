import React, { useState, useEffect } from 'react';
import { Target, Plus, TrendingUp, Calendar, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { GoalsAPI, RecommendationsAPI } from '../services/apiService';
import { useAPI } from '../hooks/useAPI';

const GoalManager: React.FC = () => {
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [newGoal, setNewGoal] = useState({
    goal_type: 'weight_loss',
    target_value: 0,
    target_date: ''
  });

  const { data: goalsData, loading: loadingGoals, execute: fetchGoals } = useAPI(
    (userId: string) => GoalsAPI.getUserGoals(userId, true)
  );

  const { data: progress, execute: fetchProgress } = useAPI(
    (userId: string) => GoalsAPI.getProgress(userId)
  );

  const { data: recommendations, execute: fetchRecommendations } = useAPI(
    (userId: string) => RecommendationsAPI.getRecommendations(userId, { include_read: false })
  );

  const { loading: creating, execute: createGoal } = useAPI(
    (userId: string, goalData: any) => GoalsAPI.createGoal(userId, goalData)
  );

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    await fetchGoals('user-1');
    await fetchProgress('user-1');
    await fetchRecommendations('user-1');
  };

  const handleCreateGoal = async () => {
    if (!newGoal.target_value || !newGoal.target_date) {
      alert('Please fill in all fields');
      return;
    }

    const result = await createGoal('user-1', newGoal);
    if (result) {
      setShowAddGoal(false);
      setNewGoal({ goal_type: 'weight_loss', target_value: 0, target_date: '' });
      loadData();
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold flex items-center">
            <Target className="mr-3 text-emerald-400" />
            Goal Management
          </h3>
          <p className="text-sm text-slate-400 mt-1">Track your fitness objectives</p>
        </div>
        <button
          onClick={() => setShowAddGoal(!showAddGoal)}
          className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 px-6 py-3 rounded-xl font-black text-xs uppercase tracking-widest flex items-center space-x-2"
        >
          <Plus size={16} />
          <span>New Goal</span>
        </button>
      </div>

      {/* Add Goal Form */}
      {showAddGoal && (
        <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 space-y-4">
          <h4 className="font-bold text-white">Create New Goal</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">Goal Type</label>
              <select
                value={newGoal.goal_type}
                onChange={(e) => setNewGoal({ ...newGoal, goal_type: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
              >
                <option value="weight_loss">Weight Loss</option>
                <option value="weight_gain">Weight Gain</option>
                <option value="muscle_gain">Muscle Gain</option>
                <option value="body_fat_reduction">Body Fat Reduction</option>
                <option value="strength_increase">Strength Increase</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">Target Value</label>
              <input
                type="number"
                value={newGoal.target_value || ''}
                onChange={(e) => setNewGoal({ ...newGoal, target_value: Number(e.target.value) })}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
                placeholder="e.g., 75 (kg)"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 uppercase tracking-widest mb-2 block">Target Date</label>
              <input
                type="date"
                value={newGoal.target_date}
                onChange={(e) => setNewGoal({ ...newGoal, target_date: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleCreateGoal}
              disabled={creating}
              className="bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-700 text-slate-950 px-6 py-2 rounded-xl font-bold text-xs uppercase"
            >
              {creating ? 'Creating...' : 'Create Goal'}
            </button>
            <button
              onClick={() => setShowAddGoal(false)}
              className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded-xl font-bold text-xs uppercase"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Progress Overview */}
      {progress && (
        <div className="bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 p-6 rounded-2xl border border-emerald-500/20">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-bold text-white flex items-center">
              <TrendingUp className="mr-2 text-emerald-400" size={18} />
              Current Progress
            </h4>
            <span className={`text-xs font-black px-3 py-1 rounded-full ${
              progress.is_on_track 
                ? 'bg-emerald-500/20 text-emerald-400' 
                : 'bg-orange-500/20 text-orange-400'
            }`}>
              {progress.is_on_track ? 'On Track' : 'Needs Attention'}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-slate-500 uppercase">Goal Type</p>
              <p className="text-sm font-bold text-white capitalize">{progress.goal_type.replace('_', ' ')}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase">Progress</p>
              <p className="text-sm font-bold text-emerald-400">{progress.progress_percentage.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase">Current</p>
              <p className="text-sm font-bold text-white">{progress.current_value}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase">Target</p>
              <p className="text-sm font-bold text-cyan-400">{progress.target_value}</p>
            </div>
          </div>
          {progress.days_remaining && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-xs text-slate-400">
                <Calendar className="inline mr-1" size={12} />
                {progress.days_remaining} days remaining
              </p>
            </div>
          )}
        </div>
      )}

      {/* Active Goals List */}
      {loadingGoals ? (
        <div className="py-12 flex justify-center">
          <Loader2 className="animate-spin text-emerald-400" size={32} />
        </div>
      ) : goalsData && goalsData.goals.length > 0 ? (
        <div className="space-y-4">
          <h4 className="font-bold text-white">Active Goals</h4>
          {goalsData.goals.map((goal) => (
            <div key={goal.id} className="bg-slate-800/30 p-5 rounded-xl border border-slate-700/50">
              <div className="flex justify-between items-start">
                <div>
                  <h5 className="font-bold text-white capitalize">{goal.goal_type.replace('_', ' ')}</h5>
                  <p className="text-xs text-slate-500 mt-1">
                    Target: {goal.target_value} | Current: {goal.current_value}
                  </p>
                </div>
                {goal.is_active && (
                  <CheckCircle2 className="text-emerald-400" size={20} />
                )}
              </div>
              {goal.target_date && (
                <p className="text-xs text-slate-400 mt-3">
                  Due: {new Date(goal.target_date).toLocaleDateString()}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="py-12 text-center text-slate-500">
          <Target className="mx-auto mb-3 text-slate-700" size={40} />
          <p className="text-sm">No active goals. Create one to get started!</p>
        </div>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.recommendations.length > 0 && (
        <div className="space-y-4">
          <h4 className="font-bold text-white flex items-center">
            <AlertCircle className="mr-2 text-cyan-400" size={18} />
            Personalized Recommendations
          </h4>
          {recommendations.recommendations.slice(0, 3).map((rec) => (
            <div key={rec.id} className="bg-cyan-500/5 p-4 rounded-xl border border-cyan-500/20">
              <h5 className="font-bold text-cyan-400 text-sm">{rec.title}</h5>
              <p className="text-xs text-slate-400 mt-2">{rec.description}</p>
              <div className="flex items-center justify-between mt-3">
                <span className="text-[10px] text-slate-500 uppercase">{rec.recommendation_type}</span>
                <span className="text-[10px] text-cyan-400">
                  Confidence: {(rec.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GoalManager;
