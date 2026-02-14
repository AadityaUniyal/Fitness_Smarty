import React, { useState, useEffect } from 'react';
import { Dumbbell, Search, Filter, Loader2, Info, Target, Trophy, Wrench } from 'lucide-react';
import { ExerciseAPI } from '../services/apiService';
import { useAPI } from '../hooks/useAPI';

const ExerciseBrowser: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('');
  const [selectedMuscleGroup, setSelectedMuscleGroup] = useState<string>('');
  const [expandedExercise, setExpandedExercise] = useState<string | null>(null);

  const { data: exercises, loading, execute: searchExercises } = useAPI(
    (params: any) => ExerciseAPI.searchExercises(params)
  );

  useEffect(() => {
    handleSearch();
  }, [searchQuery, selectedCategory, selectedDifficulty, selectedMuscleGroup]);

  const handleSearch = async () => {
    const params: any = {};
    if (searchQuery) params.name_query = searchQuery;
    if (selectedCategory) params.category = selectedCategory;
    if (selectedDifficulty) params.difficulty_level = selectedDifficulty;
    if (selectedMuscleGroup) params.muscle_groups = [selectedMuscleGroup];
    params.limit = 50;

    await searchExercises(params);
  };

  const categories = ['Strength', 'Cardio', 'Flexibility', 'Balance', 'Plyometric'];
  const difficulties = ['Beginner', 'Intermediate', 'Advanced', 'Expert'];
  const muscleGroups = ['Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core', 'Full Body'];

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search exercises..."
            className="w-full bg-slate-900 border border-slate-700 rounded-xl py-3 pl-12 pr-4 text-sm text-white placeholder:text-slate-600"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-slate-500" />
            <span className="text-xs text-slate-500 uppercase tracking-widest">Filters:</span>
          </div>
          
          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Difficulty Filter */}
          <select
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
          >
            <option value="">All Difficulties</option>
            {difficulties.map((diff) => (
              <option key={diff} value={diff}>{diff}</option>
            ))}
          </select>

          {/* Muscle Group Filter */}
          <select
            value={selectedMuscleGroup}
            onChange={(e) => setSelectedMuscleGroup(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white"
          >
            <option value="">All Muscle Groups</option>
            {muscleGroups.map((muscle) => (
              <option key={muscle} value={muscle}>{muscle}</option>
            ))}
          </select>

          {(selectedCategory || selectedDifficulty || selectedMuscleGroup) && (
            <button
              onClick={() => {
                setSelectedCategory('');
                setSelectedDifficulty('');
                setSelectedMuscleGroup('');
              }}
              className="text-xs text-emerald-400 hover:text-emerald-300 underline"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="py-12 flex justify-center">
          <Loader2 className="animate-spin text-emerald-400" size={32} />
        </div>
      ) : exercises && exercises.length > 0 ? (
        <div className="space-y-3">
          {exercises.map((exercise) => (
            <div
              key={exercise.id}
              className="bg-slate-800/30 border border-slate-700/50 rounded-xl overflow-hidden hover:border-emerald-500/30 transition-all"
            >
              <div
                onClick={() => setExpandedExercise(expandedExercise === exercise.id ? null : exercise.id)}
                className="p-5 cursor-pointer"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-bold text-white text-lg">{exercise.name}</h4>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="text-[10px] font-black bg-cyan-500/10 text-cyan-400 px-2 py-1 rounded uppercase">
                        {exercise.category}
                      </span>
                      <span className="text-[10px] font-black bg-orange-500/10 text-orange-400 px-2 py-1 rounded uppercase">
                        {exercise.difficulty_level}
                      </span>
                      {exercise.muscle_groups.slice(0, 2).map((muscle, idx) => (
                        <span key={idx} className="text-[10px] font-black bg-purple-500/10 text-purple-400 px-2 py-1 rounded uppercase">
                          {muscle}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button className="text-slate-500 hover:text-emerald-400 transition-colors">
                    <Info size={20} />
                  </button>
                </div>
              </div>

              {expandedExercise === exercise.id && (
                <div className="border-t border-slate-700/50 p-5 bg-slate-900/30 space-y-4">
                  <div>
                    <h5 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2">Instructions</h5>
                    <p className="text-sm text-slate-300 leading-relaxed">{exercise.instructions}</p>
                  </div>

                  {exercise.safety_notes && (
                    <div className="bg-orange-500/5 p-4 rounded-xl border border-orange-500/20">
                      <h5 className="text-xs font-black text-orange-400 uppercase tracking-widest mb-2">Safety Notes</h5>
                      <p className="text-sm text-slate-300 leading-relaxed">{exercise.safety_notes}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h5 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2">Target Muscles</h5>
                      <div className="flex flex-wrap gap-1">
                        {exercise.muscle_groups.map((muscle, idx) => (
                          <span key={idx} className="text-xs bg-purple-500/10 text-purple-400 px-2 py-1 rounded">
                            {muscle}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h5 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-2">Equipment</h5>
                      <div className="flex flex-wrap gap-1">
                        {exercise.equipment.map((equip, idx) => (
                          <span key={idx} className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                            {equip}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="py-12 text-center text-slate-500">
          <Dumbbell className="mx-auto mb-3 text-slate-700" size={40} />
          <p className="text-sm">No exercises found matching your criteria</p>
        </div>
      )}
    </div>
  );
};

export default ExerciseBrowser;
