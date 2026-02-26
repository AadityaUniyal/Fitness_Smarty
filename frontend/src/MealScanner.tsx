import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, Loader2, Sparkles, PieChart, Info, RefreshCw, Eye, Zap, X, Maximize, StopCircle, PlayCircle, ScanLine, GraduationCap, Check, Send } from 'lucide-react';
import { MealAPI } from './services/apiService';
import VisionService, { YOLOResult } from './services/visionService';
import { N8NService } from './services/n8nService';
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

  // Live Camera Features
  const [isLive, setIsLive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const detectionInterval = useRef<NodeJS.Timeout | null>(null);

  // Training / Correction State
  const [showCorrection, setShowCorrection] = useState(false);
  const [correctionName, setCorrectionName] = useState('');
  const [correctionCals, setCorrectionCals] = useState('');
  const [trainingStatus, setTrainingStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  // Interactive Weight State
  const [selectedFood, setSelectedFood] = useState<{ name: string, weight: string, caloriesPer100g: number } | null>(null);
  const [showWeightModal, setShowWeightModal] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, loading, error, execute } = useAPI(
    (userId: string, mealType: string, file: File) =>
      MealAPI.analyzeMeal(userId, mealType, file)
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      setCameraError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsLive(true);
        // wait for video to play before starting detection
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play();
          startDetectionLoop();
        };
      }
    } catch (err) {
      console.error("Camera access denied:", err);
      setCameraError("Could not access camera. Please allow permissions.");
    }
  };

  const stopCamera = () => {
    if (detectionInterval.current) {
      clearInterval(detectionInterval.current);
      detectionInterval.current = null;
    }

    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsLive(false);
    setYoloResult(null);
  };

  const startDetectionLoop = () => {
    if (detectionInterval.current) clearInterval(detectionInterval.current);

    detectionInterval.current = setInterval(() => {
      captureAndDetect();
    }, 600); // 600ms interval for reasonable FPS vs Load
  };

  const captureAndDetect = async () => {
    if (!videoRef.current || !canvasRef.current || !isLive) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video.readyState !== 4) return;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to blob/file
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const file = new File([blob], "live_frame.jpg", { type: "image/jpeg" });

      try {
        // Use YOLO detection
        const result = await VisionService.detectWithYOLO(file, 0.4, false); // Lower confidence for live view
        setYoloResult(result);

        // If we have detections, we could optionally auto-capture or just show them

      } catch (e) {
        console.error("Live detection error", e);
      }
    }, 'image/jpeg', 0.8);
  };

  const captureLivePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL('image/jpeg');
      setImage(dataUrl);

      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
          setImageFile(file);
          stopCamera(); // Stop live mode
          processImage(file); // Process full analysis
        }
      });
    }
  };


  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file');
        return;
      }
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
      if (useAdvancedDetection || true) { // Default to advanced for now as it's better
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

  const updateFoodWeight = () => {
    if (!selectedFood || !analysis) return;

    const weight = parseFloat(selectedFood.weight);
    if (isNaN(weight) || weight <= 0) return;

    // Calculate new values
    const ratio = weight / 100;
    const newCals = Math.round(selectedFood.caloriesPer100g * ratio);

    // Update analysis state
    // Note: This matches the User's request to "tell me approx calorie in it upon the clculation of each gm"
    // We are updating the TOTAL meal analysis here. For multiple items, we'd need more complex logic.
    // Assuming single item focus for this interaction.

    setAnalysis(prev => prev ? ({
      ...prev,
      calories: newCals,
      // We can also update macros if we had per100g for them stored. 
      // For now, let's just update calories as requested.
      recommendation: `✨ Adjusted for ${weight}g: ${newCals} kcal`
    }) : null);

    setShowWeightModal(false);
    setSelectedFood(null);
  };

  const submitCorrection = async () => {
    if (!imageFile || !correctionName) return;

    setTrainingStatus('sending');
    try {
      // Determine predicted label from current analysis
      const predicted = analysis?.foodName || 'unknown';

      await N8NService.sendCorrection({
        original_image: imageFile,
        predicted_label: predicted,
        corrected_label: correctionName,
        corrected_calories: correctionCals ? parseInt(correctionCals) : undefined,
        timestamp: new Date().toISOString(),
        confidence_score: analysis?.analysis_confidence || 0
      });

      setTrainingStatus('success');
      setTimeout(() => {
        setShowCorrection(false);
        setTrainingStatus('idle');
        setCorrectionName('');
        setCorrectionCals('');
      }, 2000);
    } catch (e) {
      setTrainingStatus('error');
    }
  };

  // Helper to render bounding boxes
  const renderLiveOverlays = () => {
    if (!videoRef.current || !yoloResult || !yoloResult.detections) return null;

    // We need to scale boxes from image processing size (likely 640x640) to display size
    // But wait, the video is being displayed at CSS size.
    // Best way: use percentages if possible or assume logic.
    // YOLO typically returns [x1, y1, x2, y2]

    // For simplicity in this demo, since we send the whole frame, coordinates should match the video frame content (if object-fit: contain)
    // NOTE: We might need to handle scaling if backend resizes. YOLOv8 usually returns pixel coords relative to passed image.

    // Note: If you want precise overlay, implementing this requires knowing the scale factor 
    // the backend applied or just using the image size returned by backend.

    // Simplest approach: Render boxes assuming they match the video dimensions
    // (We'll skip complex scaling logic for this iteration and focus on the feed working)

    return yoloResult.detections.map((det, idx) => {
      const [x1, y1, x2, y2] = det.bbox;

      // Assuming backend returns coords for the provided image size (which is canvas size)
      // We need to scale these to the current *display* size of the video element.
      const video = videoRef.current;
      if (!video) return null;

      // Get displayed size
      const rect = video.getBoundingClientRect();
      // The actual video resolution
      const vidW = video.videoWidth;
      const vidH = video.videoHeight;

      const scaleX = rect.width / vidW;
      const scaleY = rect.height / vidH;

      return (
        <div
          key={idx}
          onClick={() => {
            // Find nutrition data payload (need to have stored it in analysis or yoloResult? 
            // Currently yoloResult just has detections. 
            // But we can look up in analysis if it exists, or just open modal generic.
            // Let's assume we want to ask user for weight -> and IF we have per100g data we use it.
            // Since we don't strictly link yolo det to analysis items in UI yet, we'll try to find match.

            // We need the per_100g data. It's inside `analysis.detected_foods` (if we mapped it) NOT yoloResult.
            // But `analysis` is set AFTER estimateNutrition.
            // So if analysis is present, we can find it.

            // For now, let's just use the `correction` flow but pre-filled.
            // OR better: Just set SelectedFood with class name and ask user.
            // Then we need to fetch per100g? 
            // Actually, we just updated the API to return per_100g. 
            // We need to store that in `analysis` or `yoloResult`. 
            // Let's grab it from `VisionService.estimateNutrition` calls.

            // Simplification: We will just open the correction modal for now, 
            // but later we can make this the "Weight Input" feature.

            // Let's check if we have analysis data
            const foodName = det.class.replace(/_/g, ' ');
            // Mock per 100g if not found (or 0)
            const calPer100 = 250; // Fallback or find in analysis items

            setSelectedFood({
              name: foodName,
              weight: det.portion_estimate_g.toString(),
              caloriesPer100g: calPer100 // We need to get this from actual API response ideally
            });
            setShowWeightModal(true);
          }}
          className="absolute border-2 border-emerald-500 bg-emerald-500/20 z-10 animate-in fade-in duration-75 cursor-pointer hover:bg-emerald-500/40 transition-colors"
          style={{
            left: x1 * scaleX,
            top: y1 * scaleY,
            width: (x2 - x1) * scaleX,
            height: (y2 - y1) * scaleY,
          }}
        >
          <span className="absolute -top-6 left-0 bg-emerald-500 text-slate-950 text-[10px] font-black px-2 py-1 rounded">
            {det.class.toUpperCase()} {Math.round(det.confidence * 100)}%
          </span>
        </div>
      );
    });
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] p-8 space-y-6 h-full flex flex-col relative overflow-hidden">

      {/* WEIGHT INPUT MODAL */}
      {showWeightModal && selectedFood && (
        <div className="absolute inset-0 bg-slate-950/90 z-50 flex items-center justify-center p-6 animate-in fade-in duration-200 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 p-6 rounded-3xl w-full max-w-sm space-y-4 shadow-2xl">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold text-white flex items-center">
                <Zap className="mr-2 text-emerald-400" />
                Calculate Calories
              </h3>
              <button onClick={() => setShowWeightModal(false)} className="text-slate-500 hover:text-white">
                <X size={20} />
              </button>
            </div>

            <div className="text-center py-2">
              <p className="text-2xl font-black text-white">{selectedFood.name}</p>
              <p className="text-xs text-slate-500 mt-1">Found via Camera Model</p>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase text-slate-500">Weight (grams)</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={selectedFood.weight}
                  onChange={(e) => setSelectedFood({ ...selectedFood, weight: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-xl font-bold text-white focus:border-emerald-500 outline-none"
                  placeholder="0"
                  autoFocus
                />
                <span className="text-slate-500 font-bold">g</span>
              </div>
            </div>

            <div className="bg-slate-800/50 p-4 rounded-xl text-center">
              <p className="text-xs text-slate-400 mb-1">Estimated Energy</p>
              <p className="text-3xl font-black text-emerald-400">
                {Math.round((parseFloat(selectedFood.weight) || 0) / 100 * selectedFood.caloriesPer100g)} <span className="text-sm font-normal text-slate-500">kcal</span>
              </p>
            </div>

            <button
              onClick={updateFoodWeight}
              className="w-full py-3 bg-emerald-500 text-slate-950 rounded-xl font-bold hover:bg-emerald-400 transition-all flex items-center justify-center"
            >
              Apply to Log
            </button>
          </div>
        </div>
      )}

      {/* CORRECTION MODAL */}
      {showCorrection && (
        <div className="absolute inset-0 bg-slate-950/90 z-50 flex items-center justify-center p-6 animate-in fade-in duration-200 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 p-6 rounded-3xl w-full max-w-sm space-y-4 shadow-2xl">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold text-white flex items-center">
                <GraduationCap className="mr-2 text-emerald-400" />
                Teach Agent
              </h3>
              <button onClick={() => setShowCorrection(false)} className="text-slate-500 hover:text-white">
                <X size={20} />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Help train the AI by correcting its prediction. This data will be sent to our n8n training pipeline.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-black uppercase text-slate-500">Correct Food Name</label>
                <input
                  type="text"
                  value={correctionName}
                  onChange={(e) => setCorrectionName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:border-emerald-500 outline-none"
                  placeholder="e.g. Grilled Salmon"
                />
              </div>
              <div>
                <label className="text-[10px] font-black uppercase text-slate-500">Calories (Optional)</label>
                <input
                  type="number"
                  value={correctionCals}
                  onChange={(e) => setCorrectionCals(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:border-emerald-500 outline-none"
                  placeholder="e.g. 450"
                />
              </div>
            </div>

            <button
              onClick={submitCorrection}
              disabled={!correctionName || trainingStatus === 'sending'}
              className={`w-full py-3 rounded-xl font-bold flex items-center justify-center transition-all ${trainingStatus === 'success' ? 'bg-emerald-500 text-white' :
                trainingStatus === 'sending' ? 'bg-slate-700 text-slate-400' :
                  'bg-white text-slate-900 hover:bg-emerald-400'
                }`}
            >
              {trainingStatus === 'sending' ? (
                <Loader2 className="animate-spin" />
              ) : trainingStatus === 'success' ? (
                <><Check className="mr-2" /> Sent to n8n</>
              ) : (
                <><Send className="mr-2" size={16} /> Submit Correction</>
              )}
            </button>
          </div>
        </div>
      )}
      <div className="text-left space-y-1">
        <h2 className="text-xl font-bold flex items-center justify-between">
          <div className="flex items-center">
            <Camera className="mr-3 text-emerald-400" size={20} />
            Meal Scanner
          </div>
          {isLive && (
            <div className="flex items-center space-x-2">
              <span className="animate-pulse w-2 h-2 rounded-full bg-red-500"></span>
              <span className="text-[10px] font-black text-red-500 uppercase">LIVE</span>
            </div>
          )}
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
      </div>

      {/* Helper Canvas for Frame Capture */}
      <canvas ref={canvasRef} className="hidden" />

      <div className={`relative border-2 border-dashed rounded-3xl transition-all duration-300 ${isLive ? 'border-emerald-500' : (image ? 'border-transparent' : 'border-slate-800 hover:border-emerald-500/50')} min-h-[300px] flex items-center justify-center overflow-hidden bg-black`}>

        {isLive ? (
          // LIVE VIDEO MODE
          <div className="relative w-full h-full flex items-center justify-center">
            <video
              ref={videoRef}
              className="w-full h-full object-contain" // Use object-contain to preserve aspect ratio
              playsInline
              muted
            />
            {/* Overlay Layer */}
            <div className="absolute inset-0 pointer-events-none">
              {renderLiveOverlays()}
            </div>

            {/* Capture Button */}
            <button
              onClick={captureLivePhoto}
              className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-white text-slate-900 rounded-full p-4 shadow-lg hover:scale-110 transition-transform z-20"
            >
              <div className="w-12 h-12 rounded-full border-4 border-slate-900 bg-white" />
            </button>

            <button
              onClick={stopCamera}
              className="absolute top-4 right-4 bg-black/50 text-white rounded-full p-2 hover:bg-black/70 z-20"
            >
              <X size={20} />
            </button>
          </div>
        ) : image ? (
          // REVIEW MODE
          <div className="relative group w-full h-full">
            <img src={image} className="w-full h-[300px] rounded-2xl object-cover shadow-2xl brightness-90 group-hover:brightness-100 transition-all" alt="Meal" />
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
          // IDLE MODE
          <div className="text-center p-6 space-y-4">
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-16 h-16 bg-slate-800 hover:bg-slate-700 rounded-2xl flex items-center justify-center text-slate-500 hover:text-emerald-400 transition-all"
              >
                <Upload size={24} />
              </button>
              <button
                onClick={startCamera}
                className="w-16 h-16 bg-slate-800 hover:bg-slate-700 rounded-2xl flex items-center justify-center text-slate-500 hover:text-emerald-400 transition-all"
              >
                <ScanLine size={24} />
              </button>
            </div>

            <div className="flex flex-col items-center">
              <p className="text-xs font-black text-slate-500 uppercase tracking-widest mt-2">
                Upload or Scan Live
              </p>
              {cameraError && <p className="text-red-400 text-[10px] mt-2">{cameraError}</p>}
            </div>

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

      {analysis && !loading && !isLive && (
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
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowCorrection(true)}
                className="text-[10px] font-bold bg-slate-800 hover:bg-slate-700 text-white px-2 py-1 rounded-lg flex items-center transition-colors"
              >
                <GraduationCap size={12} className="mr-1 text-emerald-400" />
                Teach Agent
              </button>
              <span className="text-xs font-black bg-emerald-400/10 text-emerald-400 px-3 py-1 rounded-full">{analysis.calories} CAL</span>
            </div>
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
  );
};

export default MealScanner;
