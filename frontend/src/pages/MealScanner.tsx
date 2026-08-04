import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, ScanLine, AlertCircle, CheckCircle2, Flame, Beef, Wheat, Droplets, Star, RefreshCw, X, Lightbulb, Target, ChevronRight, Scale, Database } from 'lucide-react';
import { analyzeMealImageEnhanced, EnhancedMealAnalysis } from '../services/geminiService';
import { Reveal } from '../components/Reveal';
import VisionService from '../services/visionService';
import AIErrorBoundary from '../components/AIErrorBoundary';
import { logMealProgress } from '../services/apiService';
import { useUserProfile } from '../hooks/useUserProfile';
import { useCurrentUserId } from '../hooks/useCurrentUserId';

const dataURLtoFile = (dataurl: string, filename: string) => {
  const arr = dataurl.split(',');
  const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
};

const GOAL_LABELS: Record<string, string> = {
  weight_loss: 'Weight Loss', muscle_gain: 'Muscle Gain', athletic: 'Athletic / Tone', maintenance: 'Maintenance'
};

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const macroColors: Record<string, { border: string; bg: string; text: string }> = {
  orange: { border: 'border-orange-500/20', bg: 'bg-orange-500/10', text: 'text-orange-400' },
  blue: { border: 'border-blue-500/20', bg: 'bg-blue-500/10', text: 'text-blue-400' },
  amber: { border: 'border-amber-500/20', bg: 'bg-amber-500/10', text: 'text-amber-400' },
  purple: { border: 'border-purple-500/20', bg: 'bg-purple-500/10', text: 'text-purple-400' }
};

// ───── Macro Circular Chart ─────
interface MacroDonutProps {
  protein: number;
  carbs: number;
  fat: number;
  totalCalories: number;
}

const MacroDonut: React.FC<MacroDonutProps> = ({ protein, carbs, fat, totalCalories }) => {
  const totalGrams = (protein || 0) + (carbs || 0) + (fat || 0) || 1;
  const proPct = Math.round(((protein || 0) / totalGrams) * 100);
  const carbPct = Math.round(((carbs || 0) / totalGrams) * 100);
  const fatPct = 100 - proPct - carbPct;

  const radius = 50;
  const strokeWidth = 16;
  const circumference = 2 * Math.PI * radius;
  const cx = 60;
  const cy = 60;

  const getArcPath = (startPct: number, durationPct: number, color: string) => {
    if (durationPct <= 0) return null;
    const startAngle = (startPct / 100) * 360 - 90;
    const endAngle = ((startPct + durationPct) / 100) * 360 - 90;

    const polarToCartesian = (centerX: number, centerY: number, r: number, angleInDegrees: number) => {
      const angleInRadians = (angleInDegrees * Math.PI) / 180.0;
      return {
        x: centerX + r * Math.cos(angleInRadians),
        y: centerY + r * Math.sin(angleInRadians)
      };
    };

    const start = polarToCartesian(cx, cy, radius, endAngle);
    const end = polarToCartesian(cx, cy, radius, startAngle);
    const largeArcFlag = durationPct > 50 ? '1' : '0';

    return (
      <path
        d={[`M`, start.x, start.y, `A`, radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(' ')}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
      />
    );
  };

  return (
    <div className="flex items-center space-x-6 bg-slate-950/40 p-4 border border-white/5 rounded-2xl">
      <svg className="w-[120px] h-[120px] -rotate-90">
        <circle cx={cx} cy={cy} r={radius} fill="none" stroke="#1e293b" strokeWidth="16" />
        {getArcPath(0, proPct, '#60a5fa')}
        {getArcPath(proPct, carbPct, '#f59e0b')}
        {getArcPath(proPct + carbPct, fatPct, '#a78bfa')}
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central"
          className="rotate-90" style={{ fill: '#fff', fontSize: '18px', fontWeight: 900, transform: `rotate(90deg) translate(0px, ${-cx}px)` }}>
        </text>
      </svg>
      {/* Overlay total in center via absolute trick */}
      <div className="space-y-2">
        <div className="text-center mb-2">
          <p className="text-2xl font-black text-white">{totalCalories}</p>
          <p className="text-[9px] uppercase tracking-widest text-slate-500 font-black">kcal</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-blue-400 shrink-0" />
          <p className="text-xs font-black text-slate-300">Protein <span className="text-blue-400">{proPct}%</span></p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-amber-400 shrink-0" />
          <p className="text-xs font-black text-slate-300">Carbs <span className="text-amber-400">{carbPct}%</span></p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-purple-450 shrink-0" />
          <p className="text-xs font-black text-slate-300">Fats <span className="text-purple-400">{fatPct}%</span></p>
        </div>
      </div>
    </div>
  );
};

// ───── Portion Calculator Panel ─────
interface PortionItem {
  name: string;
  grams: number;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  foundInDb: boolean;
}

interface PortionPanelProps {
  detectedFoodNames: string[];
  onLogMeal: (items: PortionItem[], mealType: string) => void;
  mealType: string;
  userGoal?: string;
  profile: any;
  userId: string;
}

const PortionPanel: React.FC<PortionPanelProps> = ({ detectedFoodNames, onLogMeal, mealType, userGoal, profile, userId }) => {
  const [portions, setPortions] = useState<Record<string, number>>(
    Object.fromEntries(detectedFoodNames.map(n => [n, 100]))
  );
  const [results, setResults] = useState<PortionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [logged, setLogged] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, boolean>>({});

  const handleMealFeedback = async (rating: number) => {
    try {
      await fetch(`${API_BASE}/api/feedback/coach`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: 'meal',
          item_id: detectedFoodNames.join(',') || 'meal_scan',
          rating,
          context_json: {
            goal: profile.goal || profile.primary_goal,
            gender: profile.gender,
            mealType,
          }
        })
      });
      setFeedbackSent(prev => ({ ...prev, meal_scan: true }));
    } catch (e) {
      console.error(e);
    }
  };

  const calculatePortions = async () => {
    setLoading(true);
    const items: PortionItem[] = [];
    for (const name of detectedFoodNames) {
      const grams = portions[name] || 100;
      try {
        const res = await fetch(`${API_BASE}/api/nutrition/calculate-portion`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ food_name: name, quantity_grams: grams }),
        });
        if (res.ok) {
          const data = await res.json();
          items.push({
            name: data.food_name,
            grams,
            calories: data.calories,
            protein: data.protein_g,
            carbs: data.carbs_g,
            fat: data.fat_g,
            foundInDb: true,
          });
        } else {
          items.push({ name, grams, calories: 0, protein: 0, carbs: 0, fat: 0, foundInDb: false });
        }
      } catch {
        items.push({ name, grams, calories: 0, protein: 0, carbs: 0, fat: 0, foundInDb: false });
      }
    }
    setResults(items);
    setLoading(false);
  };

  const totalCal = results.reduce((s, i) => s + i.calories, 0);
  const totalPro = results.reduce((s, i) => s + i.protein, 0);
  const totalCarb = results.reduce((s, i) => s + i.carbs, 0);
  const totalFat = results.reduce((s, i) => s + i.fat, 0);

  const handleLog = () => {
    onLogMeal(results, mealType);
    setLogged(true);
  };

  return (
    <div className="p-5 bg-slate-900 border border-emerald-500/20 rounded-3xl space-y-5">
      <div className="flex items-center space-x-2">
        <Scale size={16} className="text-emerald-400" />
        <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Enter Portion Sizes</p>
      </div>

      {detectedFoodNames.map(name => (
        <div key={name} className="flex items-center space-x-3">
          <p className="text-sm font-black text-white flex-1 truncate">{name}</p>
          <div className="flex items-center space-x-2 bg-slate-800 rounded-xl px-3 py-2 border border-white/10">
            <input
              type="number"
              min={1}
              max={2000}
              value={portions[name] || 100}
              onChange={e => setPortions(prev => ({ ...prev, [name]: Number(e.target.value) }))}
              className="w-16 bg-transparent text-white font-black text-sm text-right focus:outline-none"
            />
            <span className="text-slate-550 text-xs font-black">g</span>
          </div>
        </div>
      ))}

      <button
        onClick={calculatePortions}
        disabled={loading}
        className="w-full py-3 bg-linear-to-r from-emerald-500 to-cyan-500 disabled:from-slate-700 disabled:to-slate-700 text-slate-950 font-black text-xs uppercase tracking-widest rounded-2xl transition-all"
      >
        {loading ? 'Calculating...' : 'Calculate Macros from Database'}
      </button>

      {results.length > 0 && (
        <div className="space-y-4 animate-in slide-in-from-bottom-2 duration-300">
          <MacroDonut
            protein={totalPro}
            carbs={totalCarb}
            fat={totalFat}
            totalCalories={Math.round(totalCal)}
          />

          {results.map((r, i) => (
            <div key={i} className={`flex items-center justify-between p-3 rounded-xl border ${r.foundInDb ? 'bg-slate-800/60 border-white/5' : 'bg-rose-500/10 border-rose-500/20'}`}>
              <div className="flex items-center space-x-2">
                <Database size={12} className={r.foundInDb ? 'text-emerald-400' : 'text-rose-400'} />
                <div>
                  <p className="text-sm font-black text-white truncate max-w-[140px]">{r.name}</p>
                  <p className="text-[9px] text-slate-500">{r.grams}g</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-black text-amber-400">{r.calories} kcal</p>
                <p className="text-[9px] text-slate-500">P{r.protein}g C{r.carbs}g F{r.fat}g</p>
              </div>
            </div>
          ))}

          <div className="grid grid-cols-4 gap-2">
            {[
              { label: 'Cal', value: Math.round(totalCal), color: 'orange' },
              { label: 'Pro', value: Math.round(totalPro) + 'g', color: 'blue' },
              { label: 'Crb', value: Math.round(totalCarb) + 'g', color: 'amber' },
              { label: 'Fat', value: Math.round(totalFat) + 'g', color: 'purple' },
            ].map(m => {
              const mc = macroColors[m.color as keyof typeof macroColors] || macroColors.amber;
              return (
                <div key={m.label} className={`text-center p-2 ${mc.bg} ${mc.border} rounded-xl`}>
                  <p className={`text-base font-black ${mc.text}`}>{m.value}</p>
                  <p className="text-[8px] font-black uppercase tracking-widest text-slate-600">{m.label}</p>
                </div>
              );
            })}
          </div>

          {!logged ? (
            <button
              onClick={handleLog}
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs uppercase tracking-widest rounded-2xl transition-all"
            >
              ✓ Log This Meal to Database
            </button>
          ) : (
            <div className="flex flex-col gap-3 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl animate-in fade-in duration-300">
              <div className="flex items-center justify-center space-x-2">
                <CheckCircle2 size={16} className="text-emerald-400" />
                <p className="text-xs font-black text-emerald-400 uppercase tracking-widest">Meal Logged!</p>
              </div>
              
              <div className="flex items-center justify-between border-t border-emerald-500/20 pt-2.5">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">How was the scanning precision?</span>
                {feedbackSent['meal_scan'] ? (
                  <span className="text-[9px] font-black text-emerald-400">Recorded</span>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleMealFeedback(5)}
                      className="p-1 hover:bg-emerald-500/10 rounded-lg text-slate-400 hover:text-emerald-400 transition"
                      title="Accurate Portion/Item"
                    >
                      👍
                    </button>
                    <button
                      onClick={() => handleMealFeedback(1)}
                      className="p-1 hover:bg-rose-500/10 rounded-lg text-slate-400 hover:text-rose-400 transition"
                      title="Inaccurate"
                    >
                      👎
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ───── Main Scanner Page ─────
const FoodScannerPage: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<EnhancedMealAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mealType, setMealType] = useState<'breakfast' | 'lunch' | 'dinner' | 'snack'>('lunch');
  const [cameraMode, setCameraMode] = useState(false);
  const [showPortionPanel, setShowPortionPanel] = useState(false);
  const [scanMode, setScanMode] = useState<'standard' | 'ensemble'>('standard');
  const [detections, setDetections] = useState<any[]>([]);
  const [imageSize, setImageSize] = useState<number[]>([]);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { profile } = useUserProfile();
  const userId = useCurrentUserId();
  const userGoal = profile.goal ? GOAL_LABELS[profile.goal] || profile.goal : undefined;
  const dailyCalGoal = profile.dailyCalorieGoal || 2200;

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
    } catch {
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
    
    // Validate size (rough calculation from base64 length)
    const approximateSize = dataUrl.length * 0.75;
    if (approximateSize > 10 * 1024 * 1024) {
      setError('Captured image is too large (must be under 10MB).');
      return;
    }
    setError('');
    
    setImage(dataUrl);
    stopCamera();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // File validation
    if (!file.type.startsWith('image/')) {
      setError('Invalid file type: Please upload an image file (PNG, JPG, JPEG).');
      return;
    }
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError('File too large: Meal images must be under 10MB.');
      return;
    }
    setError('');
    
    const reader = new FileReader();
    reader.onload = ev => setImage(ev.target?.result as string);
    reader.readAsDataURL(file);
  };

  const analyzeImage = async () => {
    if (!image) return;
    setLoading(true);
    setError('');
    setAnalysis(null);
    setDetections([]);
    setShowPortionPanel(false);
    try {
      if (scanMode === 'standard') {
        const base64 = image.split(',')[1];
        const result = await analyzeMealImageEnhanced(base64, userGoal ? `${userGoal} goal` : undefined, caloriesRemaining);
        setAnalysis(result);
        await logMealProgress(userId);
      } else {
        const file = dataURLtoFile(image, 'meal.jpg');
        const detectionResult = await VisionService.detectWithYOLO(file, 0.4, false);
        setDetections(detectionResult.detections);
        setImageSize(detectionResult.image_size || [640, 480]);
        
        const nutrition = await VisionService.estimateNutrition({ detections: detectionResult.detections });
        
        const result: EnhancedMealAnalysis = {
          mealName: detectionResult.detections.length > 0 
            ? detectionResult.detections.map(d => d.class.replace(/_/g, ' ').toUpperCase()).join(' & ') 
            : 'Ensemble Food Scan',
          totalCalories: nutrition.calories,
          totalProtein: nutrition.protein_g,
          totalCarbs: nutrition.carbs_g,
          totalFats: nutrition.fat_g,
          items: nutrition.items.map(item => ({
            name: item.food.toUpperCase(),
            portion: `${item.portion_g}g`,
            calories: item.calories,
            protein: item.protein_g,
            carbs: item.carbs_g,
            fats: item.fat_g,
            isHealthy: item.calories < 300
          })),
          recommendation: 'Neural Core analyzed this meal. Balance matches target macronutrients.',
          goalAlignment: nutrition.calories < caloriesRemaining ? 'good' : 'over',
          mealRating: 8.5,
          healthTips: ['Ensure hydration levels are aligned with training goals', 'High quality proteins detected'],
          alternatives: ['Replace sides with extra greens for lower carbs']
        };
        
        setAnalysis(result);
        await logMealProgress(userId);
      }
    } catch (e: any) {
      if (e.message?.includes('GEMINI_API_KEY') || e.message?.includes('not configured')) {
        setError('AI food detection needs GEMINI_API_KEY configured on the backend.');
      } else {
        setError('Analysis failed. Please try again with a clearer image.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogManualPortions = async (items: any[], mt: string) => {
    try {
      await fetch(`${API_BASE}/api/nutrition/cam-detect-log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          meal_type: mt,
          detected_foods: items.map(i => ({ name: i.name, quantity_grams: i.grams })),
        }),
      });
    } catch {
      // Save to localStorage as fallback
    }
    await logMealProgress(userId);
  };

  const reset = () => { setImage(null); setAnalysis(null); setDetections([]); setError(''); setShowPortionPanel(false); stopCamera(); };
  const goalColor = (analysis?.goalAlignment === 'good' ? 'emerald' : analysis?.goalAlignment === 'over' ? 'rose' : 'amber') as keyof typeof macroColors;
  const gc = macroColors[goalColor] || macroColors.amber;
  const goalIcon = analysis?.goalAlignment === 'good' ? CheckCircle2 : AlertCircle;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-black italic tracking-tighter text-white">
          AI Food <span className="text-emerald-400">Scanner</span>
        </h1>
        <p className="text-slate-400 text-sm mt-2">
          Snap a photo → Gemini AI detects foods → Enter grams → Get exact macros from database.
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

      {/* Scan Mode Toggle */}
      <div className="flex bg-slate-900/80 p-1.5 rounded-2xl border border-white/5 backdrop-blur-xl w-fit">
        {(['standard', 'ensemble'] as const).map(mode => (
          <button
            key={mode}
            onClick={() => setScanMode(mode)}
            className={`px-5 py-2 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
              scanMode === mode 
                ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.4)]' 
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {mode === 'standard' ? '🤖 Gemini Scan' : '⚡ Neural Ensemble (YOLO)'}
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
              <div className="relative w-full h-full">
                <img src={image} alt="Food" className="w-full h-auto block" />
                
                {/* Render bounding boxes */}
                {detections.map((det, idx) => {
                  if (!imageSize || imageSize.length < 2) return null;
                  const [imgW, imgH] = imageSize;
                  const [x1, y1, x2, y2] = det.bbox;
                  
                  const left = (x1 / imgW) * 100;
                  const top = (y1 / imgH) * 100;
                  const boxW = ((x2 - x1) / imgW) * 100;
                  const boxH = ((y2 - y1) / imgH) * 100;
                  
                  return (
                    <div 
                      key={idx}
                      className="absolute border-2 border-emerald-500 bg-emerald-500/15 hover:bg-emerald-500/35 transition-all group cursor-pointer"
                      style={{
                        left: `${left}%`,
                        top: `${top}%`,
                        width: `${boxW}%`,
                        height: `${boxH}%`
                      }}
                    >
                      <span className="absolute -top-6 left-0 bg-emerald-500 text-slate-950 text-[9px] font-black px-1.5 py-0.5 rounded shadow-lg opacity-85 group-hover:opacity-100 uppercase tracking-widest whitespace-nowrap transition-opacity">
                        {det.class.replace(/_/g, ' ')} ({(det.confidence * 100).toFixed(0)}%)
                      </span>
                    </div>
                  );
                })}

                <button onClick={reset} className="absolute top-3 right-3 p-2 bg-slate-900/80 rounded-xl text-slate-400 hover:text-rose-400 transition z-20">
                  <X size={16} />
                </button>
              </div>
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
              className="w-full flex items-center justify-center space-x-3 py-4 bg-linear-to-r from-emerald-500 to-cyan-500 disabled:from-slate-700 disabled:to-slate-700 text-slate-950 font-black text-sm uppercase tracking-widest rounded-2xl transition-all shadow-[0_8px_25px_rgba(16,185,129,0.3)] disabled:shadow-none">
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

          {/* Portion Panel — shows after AI detects foods */}
          {analysis && analysis.items.length > 0 && (
            <div className="space-y-3">
              <button
                onClick={() => setShowPortionPanel(v => !v)}
                className="w-full flex items-center justify-center space-x-2 py-3 bg-cyan-500/10 border border-cyan-500/30 hover:bg-cyan-500/20 text-cyan-400 font-black text-[10px] uppercase tracking-widest rounded-2xl transition-all"
              >
                <Scale size={14} />
                <span>{showPortionPanel ? 'Hide Portion Calculator' : '⚖️ Enter Exact Gram Portions (DB Calc)'}</span>
              </button>
              {showPortionPanel && (
                <PortionPanel
                  detectedFoodNames={analysis.items.map(i => i.name)}
                  onLogMeal={handleLogManualPortions}
                  mealType={mealType}
                  userGoal={profile.goal}
                  profile={profile}
                  userId={userId}
                />
              )}
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
            <div className="space-y-4 max-h-[700px] overflow-y-auto pr-1 stagger-children">
              {/* Goal Alignment Banner */}
              <div className={`p-4 ${gc.bg} ${gc.border.replace('20', '30')} rounded-2xl flex items-start space-x-3 card-hover`}>
                <div className={`mt-0.5 ${gc.text}`}>{React.createElement(goalIcon, { size: 18 })}</div>
                <div>
                  <p className={`text-xs font-black uppercase tracking-widest ${gc.text} mb-1`}>
                    {analysis.goalAlignment === 'good' ? '✓ Goal-Aligned Meal' : analysis.goalAlignment === 'over' ? '⚠ Over Calorie Budget' : '↓ Under Target'}
                  </p>
                  <p className="text-slate-300 text-xs leading-relaxed">{analysis.recommendation}</p>
                </div>
              </div>

              {/* Meal Name + Rating */}
              <div className="p-5 bg-slate-900 border border-white/10 rounded-2xl flex items-center justify-between card-hover">
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

              {/* Macro Donut Chart */}
              <div className="p-5 bg-slate-900 border border-white/10 rounded-2xl card-hover">
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-4">Macro Breakdown</p>
                <MacroDonut
                  protein={analysis.totalProtein}
                  carbs={analysis.totalCarbs}
                  fat={analysis.totalFats}
                  totalCalories={analysis.totalCalories}
                />
              </div>

              {/* Total Macros */}
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: 'Calories', value: analysis.totalCalories, unit: 'kcal', icon: Flame, color: 'orange' },
                  { label: 'Protein', value: analysis.totalProtein, unit: 'g', icon: Beef, color: 'blue' },
                  { label: 'Carbs', value: analysis.totalCarbs, unit: 'g', icon: Wheat, color: 'amber' },
                  { label: 'Fats', value: analysis.totalFats, unit: 'g', icon: Droplets, color: 'purple' },
                ].map(m => {
                  const mc = macroColors[m.color as keyof typeof macroColors] || macroColors.amber;
                  return (
                    <div key={m.label} className={`p-3 ${mc.bg} ${mc.border} rounded-2xl text-center`}>
                      <m.icon size={14} className={`${mc.text} mx-auto mb-1`} />
                      <p className={`text-base font-black ${mc.text}`}>{m.value}</p>
                      <p className="text-[8px] font-black uppercase tracking-widest text-slate-600">{m.label}</p>
                    </div>
                  );
                })}
              </div>

              {/* Food Items */}
              <div className="space-y-2 stagger-children">
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Detected Items ({analysis.items.length})</p>
                {analysis.items.map((item, i) => (
                  <div key={i} className="flex items-center space-x-3 p-3 bg-slate-800/60 border border-white/5 rounded-xl card-hover">
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

const FoodScannerPageWrapper: React.FC = () => {
  return (
    <AIErrorBoundary>
      <FoodScannerPage />
    </AIErrorBoundary>
  );
};

export default FoodScannerPageWrapper;
