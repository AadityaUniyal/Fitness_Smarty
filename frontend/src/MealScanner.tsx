
import React, { useState, useRef } from 'react';
import { Camera, Upload, Loader2, Sparkles, PieChart, Info, RefreshCw, Eye, Zap } from 'lucide-react';
import { MealAPI } from './services/apiService';
import VisionService, { YOLOResult } from './services/visionService';
import { useAPI } from './hooks/useAPI';
import { MealAnalysis } from './types';

const MealScanner: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<MealAnalysis | null>(null);
  const [mealType, setMealType] = useState<'breakfast' | 'lunch' | 'dinner' | 'snack'>('lunch');
  const [showHistory, setShowHistory] = useState(false);

  // YOLOv8 features
  const [useAdvancedDetection, setUseAdvancedDetection] = useState(false);
  const [yoloResult, setYoloResult] = useState<YOLOResult | null>(null);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, loading, error, execute } = useAPI(
    (userId: string, mealType: string, file: File) =>
      MealAPI.analyzeMeal(userId, mealType, file)
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file');
        return;
      }
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('Image size must be less than 10MB');
        return;
      }

      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImage(reader.result as string);
        processImage(file);
      };
      reader.readAsDataURL(file);
    }
  };

  const processImage = async (file: File) => {
    setAnalysis(null);
    setYoloResult(null);

    try {
      if (useAdvancedDetection) {
        // Use YOLOv8 + Hybrid Detection
        const yolo = await VisionService.detectWithYOLO(file, 0.5, true);
        setYoloResult(yolo);

        // Also get nutrition estimate
        const nutrition = await VisionService.estimateNutrition({ detections: yolo.detections });

        // Convert to MealAnalysis format
        const foodNames = yolo.detections.map(d => d.class.replace(/_/g, ' ')).join(', ');
        setAnalysis({
          meal_log_id: String(Date.now()),  // Convert to string
          foodName: foodNames || 'Unknown',
          calories: nutrition.calories,
          protein: nutrition.protein_g,
          carbs: nutrition.carbs_g,
          fats: nutrition.fat_g,
          recommendation: `✨ Advanced Detection: Found ${yolo.total_foods} items with ${yolo.model_used === 'yolov8' ? 'YOLOv8' : 'mock'}`,
          detected_foods: yolo.detections.map(d => ({
            food_id: `yolo_${d.class}`,  // Add food_id
            name: d.class.replace(/_/g, ' '),
            estimated_quantity_g: d.portion_estimate_g,
            confidence_score: d.confidence  // Rename to confidence_score
          })),
          analysis_confidence: yolo.detections.length > 0 ? yolo.detections.reduce((sum, d) => sum + d.confidence, 0) / yolo.detections.length : 0.5
        });
      } else {
        // Use standard Gemini detection
        const result = await execute('user-1', mealType, file);
        if (result) {
          setAnalysis({
            meal_log_id: result.meal_log_id,
            foodName: result.detected_foods.map(f => f.name).join(', ') || 'Unknown',
            calories: result.total_calories,
            protein: result.total_protein_g,
            carbs: result.total_carbs_g,
            fats: result.total_fat_g,
            recommendation: result.recommendations[0] || 'Meal logged successfully',
            detected_foods: result.detected_foods,
            analysis_confidence: result.analysis_confidence
          });
        }
      }
    } catch (err) {
      console.error('Meal analysis failed:', err);
    }
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] p-8 space-y-6 h-full flex flex-col">
      <div className="text-left space-y-1">
        <h2 className="text-xl font-bold flex items-center">
          <Camera className="mr-3 text-emerald-400" size={20} />
          Meal Scanner
        </h2>
        <p className="text-xs text-slate-500">Instant macro breakdown from a single photo.</p>
      </div>

      {/* Meal Type Selection */}
      <div className="flex gap-2">
        {(['breakfast', 'lunch', 'dinner', 'snack'] as const).map((type) => (
          <button
            key={type}
            onClick={() => setMealType(type)}
            className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${mealType === type
              ? 'bg-emerald-500 text-slate-950'
              : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
          >
            {type}
          </button>
        ))}
        <div className={`relative border-2 border-dashed rounded-3xl transition-all duration-300 ${image ? 'border-transparent' : 'border-slate-800 hover:border-emerald-500/50'
          } min-h-[220px] flex items-center justify-center overflow-hidden`}>
          {image ? (
            <div className="relative group w-full h-full">
              <img src={image} className="w-full h-[220px] rounded-2xl object-cover shadow-2xl brightness-90 group-hover:brightness-100 transition-all" alt="Meal" />
              <button
                onClick={() => { setImage(null); setAnalysis(null); }}
                className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
              >
                <div className="bg-slate-950 p-4 rounded-full text-white shadow-xl">
                  <RefreshCw size={24} />
                </div>
              </button>
            </div>
          ) : (
            <div className="text-center p-6 space-y-4">
              <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto text-slate-500">
                <Upload size={24} />
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-xs font-black uppercase tracking-widest px-6 py-3 rounded-xl transition-all shadow-lg shadow-emerald-500/10 mx-auto"
              >
                Scan My Meal
              </button>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="hidden"
              />
            </div>
          )}
        </div>

        {loading && (
          <div className="py-8 flex flex-col items-center space-y-3">
            <Loader2 size={32} className="text-emerald-400 animate-spin" />
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Identifying macros...</p>
          </div>
        )}

        {error && (
          <div className="py-4 px-6 bg-red-500/10 border border-red-500/20 rounded-2xl">
            <p className="text-xs text-red-400">{error}</p>
          </div>
        )}

        {analysis && !loading && (
          <div className="space-y-4 animate-in fade-in zoom-in-95 duration-300">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-emerald-400">{analysis.foodName}</h3>
                {analysis.analysis_confidence && (
                  <p className="text-[10px] text-slate-500 mt-1">
                    Confidence: {(analysis.analysis_confidence * 100).toFixed(0)}%
                  </p>
                )}
              </div>
              <span className="text-xs font-black bg-emerald-400/10 text-emerald-400 px-3 py-1 rounded-full">{analysis.calories} CAL</span>
            </div>

            {/* Detected Foods List */}
            {analysis.detected_foods && analysis.detected_foods.length > 0 && (
              <div className="space-y-2">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Detected Items</p>
                {analysis.detected_foods.map((food, idx) => (
                  <div key={idx} className="flex justify-between items-center bg-slate-800/30 p-2 rounded-lg">
                    <span className="text-xs text-slate-300">{food.name}</span>
                    <span className="text-[10px] text-slate-500">{food.estimated_quantity_g}g</span>
                  </div>
                ))}
              </div>
            )}

            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'PRO', val: analysis.protein, color: 'text-blue-400' },
                { label: 'CARB', val: analysis.carbs, color: 'text-orange-400' },
                { label: 'FAT', val: analysis.fats, color: 'text-purple-400' },
              ].map((m, i) => (
                <div key={i} className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/30 text-center">
                  <p className="text-[10px] font-black text-slate-500">{m.label}</p>
                  <p className={`text-sm font-bold ${m.color}`}>{m.val}g</p>
                </div>
              ))}
            </div>

            <div className="bg-emerald-500/5 p-4 rounded-2xl border border-emerald-500/10">
              <p className="text-[10px] text-emerald-400/80 italic leading-relaxed">
                "{analysis.recommendation}"
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MealScanner;
