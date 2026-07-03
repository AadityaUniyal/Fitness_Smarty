import React, { useState, useRef } from 'react';
import { Plus, Save, X, Camera, Sparkles, Loader2 } from 'lucide-react';
import { analyzeMealImage } from '../services/geminiService';

interface ManualFoodEntryProps {
  onSave: (foodData: any) => void;
  onCancel: () => void;
}

const ManualFoodEntry: React.FC<ManualFoodEntryProps> = ({ onSave, onCancel }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [foodData, setFoodData] = useState({
    name: '',
    serving_size: '1 portion',
    calories: 0,
    protein: 0,
    carbs: 0,
    fats: 0
  });

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) videoRef.current.srcObject = stream;
      setShowCamera(true);
    } catch (err) {
      alert("Camera access denied.");
    }
  };

  const captureAndAnalyze = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    canvasRef.current.width = videoRef.current.videoWidth;
    canvasRef.current.height = videoRef.current.videoHeight;
    ctx.drawImage(videoRef.current, 0, 0);

    const base64Image = canvasRef.current.toDataURL('image/jpeg').split(',')[1];

    // Stop camera
    const stream = videoRef.current.srcObject as MediaStream;
    stream.getTracks().forEach(track => track.stop());
    setShowCamera(false);

    setIsAnalyzing(true);
    try {
      const analysis = await analyzeMealImage(base64Image);
      setFoodData({
        name: analysis.foodName,
        serving_size: 'Analyzed Portion',
        calories: Math.round(analysis.calories),
        protein: Math.round(analysis.protein),
        carbs: Math.round(analysis.carbs),
        fats: Math.round(analysis.fats)
      });
    } catch (err) {
      alert("Vision analysis failed. Please enter manually.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!foodData.name || !foodData.serving_size) {
      alert('Please fill in food name and serving size');
      return;
    }
    onSave(foodData);
  };

  return (
    <div className="bg-slate-800/50 p-6 rounded-3xl border border-slate-700 shadow-2xl animate-in scale-in-95 duration-300">
      <div className="flex items-center justify-between mb-6">
        <h4 className="font-black text-white italic uppercase flex items-center tracking-tighter">
          <Plus className="mr-2 text-emerald-400" size={18} />
          Manual Food Entry
        </h4>
        <button
          onClick={onCancel}
          className="p-2 hover:bg-white/5 rounded-full text-slate-500 hover:text-white transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {showCamera ? (
        <div className="mb-6 relative rounded-2xl overflow-hidden aspect-video bg-black">
          <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
          <canvas ref={canvasRef} className="hidden" />
          <div className="absolute bottom-4 left-0 w-full flex justify-center px-4 gap-3">
            <button
              type="button"
              onClick={captureAndAnalyze}
              className="bg-emerald-500 text-slate-950 px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest flex items-center gap-2 hover:scale-105 transition"
            >
              <Sparkles size={14} /> Analyze Snap
            </button>
            <button
              type="button"
              onClick={() => {
                const stream = videoRef.current?.srcObject as MediaStream;
                stream?.getTracks().forEach(track => track.stop());
                setShowCamera(false);
              }}
              className="bg-slate-900/80 backdrop-blur-md text-white px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest border border-white/10"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={startCamera}
          className="w-full mb-6 py-8 border-2 border-dashed border-slate-700 rounded-2xl hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all group flex flex-col items-center justify-center space-y-2"
        >
          {isAnalyzing ? (
            <Loader2 className="animate-spin text-emerald-500" size={32} />
          ) : (
            <Camera className="text-slate-600 group-hover:text-emerald-500 transition-colors" size={32} />
          )}
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 group-hover:text-emerald-400">
            {isAnalyzing ? 'Neural Core Processing...' : 'Snap Food to Auto-Fill'}
          </span>
        </button>
      )}

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
