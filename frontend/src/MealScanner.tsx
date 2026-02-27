import React, { useState, useRef, useCallback } from 'react';
import { Camera, Upload, ScanLine, AlertCircle, CheckCircle2, Flame, Beef, Wheat, Droplets, Star, RefreshCw, X, Lightbulb, Target, ChevronRight } from 'lucide-react';
import { analyzeMealImageEnhanced, EnhancedMealAnalysis } from './geminiService';

const GOAL_LABELS: Record<string, string> = {
  weight_loss: 'Weight Loss', muscle_gain: 'Muscle Gain', athletic: 'Athletic / Tone', maintenance: 'Maintenance'
};

const FoodScannerPage: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<EnhancedMealAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mealType, setMealType] = useState<'breakfast' | 'lunch' | 'dinner' | 'snack'>('lunch');
  const [cameraMode, setCameraMode] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const profile = JSON.parse(localStorage.getItem('smarty_profile') || '{}');
  const userGoal = profile.goal ? GOAL_LABELS[profile.goal] || profile.goal : undefined;
  const dailyCalGoal = profile.dailyCalorieGoal || 2200;

  // Load today's calorie total from logged meals
  const getCaloriesLogged = () => {
    const today = new Date().toDateString();
    const logs = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]');
    return logs.filter((l: any) => new Date(l.timestamp).toDateString() === today)
      .reduce((sum: number, l: any) => sum + (l.totalCalories || 0), 0);
  };
  const caloriesLogged = getCaloriesLogged();
  const caloriesRemaining = dailyCalGoal - caloriesLogged;

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      streamRef.current = stream;
      if (videoRef.current) { videoRef.current.srcObject = stream; }
      setCameraMode(true);
    } catch (e) {
      setError('Camera access denied. Please allow camera permissions or upload an image.');
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    setCameraMode(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const ctx = canvasRef.current.getContext('2d')!;
    canvasRef.current.width = videoRef.current.videoWidth;
    canvasRef.current.height = videoRef.current.videoHeight;
    ctx.drawImage(videoRef.current, 0, 0);
    const dataUrl = canvasRef.current.toDataURL('image/jpeg', 0.85);
    setImage(dataUrl);
    stopCamera();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = ev => setImage(ev.target?.result as string);
    reader.readAsDataURL(file);
  };

  const analyzeImage = async () => {
    if (!image) return;
    setLoading(true);
    setError('');
    setAnalysis(null);
    try {
      const base64 = image.split(',')[1];
      const result = await analyzeMealImageEnhanced(base64, userGoal ? `${userGoal} goal` : undefined, caloriesRemaining);
      setAnalysis(result);
      // Log to localStorage
      const log = { ...result, mealType, timestamp: new Date().toISOString() };
      const prev = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]');
      localStorage.setItem('smarty_meal_logs', JSON.stringify([log, ...prev].slice(0, 50)));
    } catch (e: any) {
      if (e.message?.includes('No Gemini API key')) {
        setError('Please set your VITE_GEMINI_API_KEY in the .env file to use AI food detection.');
      } else {
        setError('Analysis failed. Please try again with a clearer image.');
      }
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setImage(null); setAnalysis(null); setError(''); stopCamera(); };

  const goalColor = analysis?.goalAlignment === 'good' ? 'emerald' : analysis?.goalAlignment === 'over' ? 'rose' : 'amber';
  const goalIcon = analysis?.goalAlignment === 'good' ? CheckCircle2 : AlertCircle;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-black italic tracking-tighter text-white">
          AI Food <span className="text-emerald-400">Scanner</span>
        </h1>
        <p className="text-slate-400 text-sm mt-2">
          Snap a photo of your meal — Gemini AI detects every food item, calculates macros, and recommends based on your goal.
        </p>
      </div>

      {/* Status Bar */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-4 bg-slate-900 border border-white/10 rounded-2xl text-center">
          <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Daily Goal</p>
          <p className="text-xl font-black text-white mt-1">{dailyCalGoal.toLocaleString()}</p>
          <p className="text-[9px] text-slate-600">kcal</p>
        </div>
        <div className="p-4 bg-slate-900 border border-white/10 rounded-2xl text-center">
          <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Logged Today</p>
          <p className="text-xl font-black text-emerald-400 mt-1">{caloriesLogged.toLocaleString()}</p>
          <p className="text-[9px] text-slate-600">kcal</p>
        </div>
        <div className={`p-4 bg-slate-900 border rounded-2xl text-center ${caloriesRemaining < 0 ? 'border-rose-500/30' : 'border-white/10'}`}>
          <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Remaining</p>
          <p className={`text-xl font-black mt-1 ${caloriesRemaining < 0 ? 'text-rose-400' : 'text-white'}`}>{Math.abs(caloriesRemaining).toLocaleString()}</p>
          <p className="text-[9px] text-slate-600">{caloriesRemaining < 0 ? 'over' : 'kcal left'}</p>
        </div>
      </div>

      {/* Meal Type */}
      <div className="flex space-x-2">
        {(['breakfast', 'lunch', 'dinner', 'snack'] as const).map(t => (
          <button key={t} onClick={() => setMealType(t)}
            className={`px-5 py-2.5 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ${mealType === t
              ? 'bg-emerald-500 text-slate-950 shadow-[0_4px_15px_rgba(16,185,129,0.3)]'
              : 'bg-slate-800 text-slate-500 hover:bg-slate-700'}`}>
            {t}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Camera / Upload Panel */}
        <div className="space-y-4">
          <div className="relative bg-slate-900 border border-white/10 rounded-3xl overflow-hidden aspect-video flex items-center justify-center">
            {cameraMode ? (
              <>
                <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                <div className="absolute inset-0 border-[3px] border-emerald-500/40 rounded-3xl pointer-events-none" />
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
                  <button onClick={capturePhoto} className="w-16 h-16 bg-white rounded-full border-4 border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.5)] active:scale-95 transition-transform" />
                </div>
                <button onClick={stopCamera} className="absolute top-3 right-3 p-2 bg-slate-900/80 rounded-xl text-slate-400 hover:text-white">
                  <X size={16} />
                </button>
              </>
            ) : image ? (
              <>
                <img src={image} alt="Food" className="w-full h-full object-cover" />
                <button onClick={reset} className="absolute top-3 right-3 p-2 bg-slate-900/80 rounded-xl text-slate-400 hover:text-rose-400 transition">
                  <X size={16} />
                </button>
              </>
            ) : (
              <div className="flex flex-col items-center space-y-4 p-8">
                <div className="w-20 h-20 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl flex items-center justify-center">
                  <Camera size={36} className="text-emerald-400" />
                </div>
                <p className="text-slate-500 text-sm text-center">Take a photo or upload your meal image</p>
              </div>
            )}
          </div>
          <canvas ref={canvasRef} className="hidden" />

          <div className="grid grid-cols-2 gap-3">
            <button onClick={startCamera}
              className="flex items-center justify-center space-x-2 py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-[10px] uppercase tracking-widest rounded-2xl transition-all shadow-[0_6px_20px_rgba(16,185,129,0.25)]">
              <Camera size={16} />
              <span>Open Camera</span>
            </button>
            <button onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center space-x-2 py-4 bg-slate-800 hover:bg-slate-700 text-slate-300 font-black text-[10px] uppercase tracking-widest rounded-2xl transition-all border border-white/10">
              <Upload size={16} />
              <span>Upload Photo</span>
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileUpload} />
          </div>

          {image && !analysis && (
            <button onClick={analyzeImage} disabled={loading}
              className="w-full flex items-center justify-center space-x-3 py-4 bg-gradient-to-r from-emerald-500 to-cyan-500 disabled:from-slate-700 disabled:to-slate-700 text-slate-950 font-black text-sm uppercase tracking-widest rounded-2xl transition-all shadow-[0_8px_25px_rgba(16,185,129,0.3)] disabled:shadow-none">
              {loading ? (
                <>
                  <ScanLine size={18} className="animate-pulse" />
                  <span>Analyzing with Gemini AI...</span>
                </>
              ) : (
                <>
                  <ScanLine size={18} />
                  <span>Analyze Meal</span>
                  <ChevronRight size={18} />
                </>
              )}
            </button>
          )}

          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-start space-x-3">
              <AlertCircle size={16} className="text-rose-400 shrink-0 mt-0.5" />
              <p className="text-rose-300 text-xs">{error}</p>
            </div>
          )}
        </div>

        {/* Results Panel */}
        <div className="space-y-4">
          {!analysis && !loading && (
            <div className="h-full flex items-center justify-center p-8 bg-slate-900/50 border border-white/5 rounded-3xl">
              <div className="text-center space-y-3">
                <ScanLine size={48} className="text-slate-700 mx-auto" />
                <p className="text-slate-600 text-sm">Meal analysis results will appear here</p>
                {userGoal && (
                  <div className="flex items-center space-x-2 justify-center">
                    <Target size={14} className="text-emerald-400" />
                    <p className="text-emerald-400 text-[10px] font-black uppercase tracking-widest">Tailored for: {userGoal}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {loading && (
            <div className="h-full flex items-center justify-center p-8 bg-slate-900/50 border border-white/5 rounded-3xl">
              <div className="text-center space-y-4">
                <div className="relative mx-auto w-16 h-16">
                  <div className="absolute inset-0 border-2 border-emerald-500/20 rounded-full" />
                  <div className="absolute inset-0 border-2 border-transparent border-t-emerald-500 rounded-full animate-spin" />
                </div>
                <p className="text-slate-400 text-sm">Gemini AI is analyzing your meal...</p>
                <p className="text-slate-600 text-xs">Detecting food items, calculating macros...</p>
              </div>
            </div>
          )}

          {analysis && (
            <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
              {/* Goal Alignment Banner */}
              <div className={`p-4 bg-${goalColor}-500/10 border border-${goalColor}-500/30 rounded-2xl flex items-start space-x-3`}>
                <div className={`mt-0.5 text-${goalColor}-400`}>{React.createElement(goalIcon, { size: 18 })}</div>
                <div>
                  <p className={`text-xs font-black uppercase tracking-widest text-${goalColor}-400 mb-1`}>
                    {analysis.goalAlignment === 'good' ? '✓ Goal-Aligned Meal' : analysis.goalAlignment === 'over' ? '⚠ Over Calorie Budget' : '↓ Under Target'}
                  </p>
                  <p className="text-slate-300 text-xs leading-relaxed">{analysis.recommendation}</p>
                </div>
              </div>

              {/* Meal Name + Rating */}
              <div className="p-5 bg-slate-900 border border-white/10 rounded-2xl flex items-center justify-between">
                <div>
                  <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Detected Meal</p>
                  <p className="text-lg font-black text-white mt-1">{analysis.mealName}</p>
                  <p className="text-[10px] text-slate-500">{mealType} • {new Date().toLocaleDateString()}</p>
                </div>
                <div className="flex items-center space-x-1 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
                  <Star size={14} className="text-amber-400 fill-amber-400" />
                  <span className="text-lg font-black text-amber-400">{analysis.mealRating}</span>
                  <span className="text-xs text-slate-500">/10</span>
                </div>
              </div>

              {/* Total Macros */}
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: 'Calories', value: analysis.totalCalories, unit: 'kcal', icon: Flame, color: 'orange' },
                  { label: 'Protein', value: analysis.totalProtein, unit: 'g', icon: Beef, color: 'blue' },
                  { label: 'Carbs', value: analysis.totalCarbs, unit: 'g', icon: Wheat, color: 'amber' },
                  { label: 'Fats', value: analysis.totalFats, unit: 'g', icon: Droplets, color: 'purple' },
                ].map(m => (
                  <div key={m.label} className={`p-3 bg-${m.color}-500/10 border border-${m.color}-500/20 rounded-2xl text-center`}>
                    <m.icon size={14} className={`text-${m.color}-400 mx-auto mb-1`} />
                    <p className={`text-base font-black text-${m.color}-400`}>{m.value}</p>
                    <p className="text-[8px] font-black uppercase tracking-widest text-slate-600">{m.label}</p>
                  </div>
                ))}
              </div>

              {/* Food Items */}
              <div className="space-y-2">
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Detected Items ({analysis.items.length})</p>
                {analysis.items.map((item, i) => (
                  <div key={i} className="flex items-center space-x-3 p-3 bg-slate-800/60 border border-white/5 rounded-xl">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${item.isHealthy ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-black text-white truncate">{item.name}</p>
                      <p className="text-[9px] text-slate-500">{item.portion}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-black text-amber-400">{item.calories} kcal</p>
                      <p className="text-[9px] text-slate-500">P{item.protein}g C{item.carbs}g F{item.fats}g</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Health Tips */}
              {analysis.healthTips.length > 0 && (
                <div className="p-4 bg-slate-900 border border-white/10 rounded-2xl space-y-2">
                  <div className="flex items-center space-x-2 mb-3">
                    <Lightbulb size={14} className="text-amber-400" />
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">AI Tips</p>
                  </div>
                  {analysis.healthTips.map((tip, i) => (
                    <p key={i} className="text-xs text-slate-400 pl-3 border-l border-emerald-500/30">{tip}</p>
                  ))}
                </div>
              )}

              {/* Alternatives */}
              {analysis.alternatives.length > 0 && (
                <div className="p-4 bg-slate-900 border border-white/10 rounded-2xl">
                  <p className="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-3">Healthier Alternatives</p>
                  <div className="flex flex-wrap gap-2">
                    {analysis.alternatives.map((alt, i) => (
                      <span key={i} className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-black rounded-xl">{alt}</span>
                    ))}
                  </div>
                </div>
              )}

              <button onClick={reset} className="w-full flex items-center justify-center space-x-2 py-3 bg-slate-800 hover:bg-slate-700 text-slate-400 font-black text-[10px] uppercase tracking-widest rounded-xl transition-all border border-white/5">
                <RefreshCw size={14} />
                <span>Scan Another Meal</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FoodScannerPage;
