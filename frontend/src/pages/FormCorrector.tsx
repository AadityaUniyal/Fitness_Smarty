import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Camera, CameraOff, RefreshCw, Dumbbell, Loader2, AlertTriangle, CheckCircle2, Target, Move } from 'lucide-react';

const EXERCISES = [
  { id: 'squat', name: 'Squat', icon: '🦵', desc: 'Knee angle 90°, back straight', keyAngles: ['hip', 'knee'] },
  { id: 'pushup', name: 'Push-Up', icon: '💪', desc: 'Elbow 90°, body straight line', keyAngles: ['elbow', 'hip'] },
  { id: 'plank', name: 'Plank', icon: '📐', desc: 'Straight line head-to-ankles', keyAngles: ['shoulder', 'hip', 'ankle'] },
  { id: 'lunge', name: 'Lunge', icon: '🏃', desc: 'Front knee 90°, back knee near ground', keyAngles: ['front_knee', 'back_knee'] },
  { id: 'curl', name: 'Bicep Curl', icon: '💪', desc: 'Elbow 90° at peak, keep elbows in', keyAngles: ['elbow'] },
];

const EXERCISE_REPS = ['Squat', 'Push-Up', 'Plank', 'Lunge', 'Bicep Curl'];

interface Keypoint { x: number; y: number; score: number; name: string; }
interface Pose { keypoints: Keypoint[]; score: number; }

function angleBetween(a: { x: number; y: number }, b: { x: number; y: number }, c: { x: number; y: number }): number {
  const ab = Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
  const bc = Math.sqrt((b.x - c.x) ** 2 + (b.y - c.y) ** 2);
  const ac = Math.sqrt((a.x - c.x) ** 2 + (a.y - c.y) ** 2);
  return Math.acos((ab ** 2 + bc ** 2 - ac ** 2) / (2 * ab * bc)) * 180 / Math.PI;
}

const SKELETON_CONNECTIONS: [string, string][] = [
  ['left_shoulder', 'right_shoulder'], ['left_shoulder', 'left_elbow'], ['right_shoulder', 'right_elbow'],
  ['left_elbow', 'left_wrist'], ['right_elbow', 'right_wrist'], ['left_shoulder', 'left_hip'],
  ['right_shoulder', 'right_hip'], ['left_hip', 'right_hip'], ['left_hip', 'left_knee'],
  ['right_hip', 'right_knee'], ['left_knee', 'left_ankle'], ['right_knee', 'right_ankle'],
];

const KEYPOINT_MAP: Record<string, string> = {
  left_shoulder: 'left_shoulder', right_shoulder: 'right_shoulder', left_elbow: 'left_elbow',
  right_elbow: 'right_elbow', left_wrist: 'left_wrist', right_wrist: 'right_wrist',
  left_hip: 'left_hip', right_hip: 'right_hip', left_knee: 'left_knee',
  right_knee: 'right_knee', left_ankle: 'left_ankle', right_ankle: 'right_ankle',
};

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src; s.onload = () => resolve(); s.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(s);
  });
}

const FormCorrector: React.FC = () => {
  const [cameraActive, setCameraActive] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [modelLoading, setModelLoading] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);
  const [selectedExercise, setSelectedExercise] = useState(EXERCISES[0]);
  const [feedback, setFeedback] = useState<string[]>(['Select exercise and start camera']);
  const [repCount, setRepCount] = useState(0);
  const [lastFeedback, setLastFeedback] = useState<'good' | 'bad' | null>(null);
  const [frameRate, setFrameRate] = useState(0);
  const [isDetecting, setIsDetecting] = useState(false);
  const [lowPowerMode, setLowPowerMode] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const detectorRef = useRef<any>(null);
  const animRef = useRef<number>(0);
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(Date.now());
  const lastDetectionTimeRef = useRef(0);
  const prevAnglesRef = useRef<{ knee?: number; hip?: number; elbow?: number }>({});
  const poseStateRef = useRef<'up' | 'down'>('up');


  useEffect(() => {
    return () => {
      stopCamera();
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, []);

  const loadModel = useCallback(async () => {
    setModelLoading(true);
    setModelError(null);
    try {
      await Promise.race([
        Promise.all([
          (window as any).tf?.ready?.(),
          new Promise<void>(r => {
            const check = () => {
              if ((window as any)?.poseDetection?.createDetector) { r(); return; }
              setTimeout(check, 200);
            };
            check();
          }),
        ]),
        new Promise((_, rej) => setTimeout(() => rej(new Error('Model load timed out')), 30000)),
      ]);
      const detector = await (window as any).poseDetection.createDetector(
        (window as any).poseDetection.SupportedModels.MoveNet,
        { modelType: (window as any).poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
      );
      if (!detector) throw new Error('Failed to create pose detector');
      detectorRef.current = detector;
      setModelLoaded(true);
      setModelError(null);
    } catch (e: any) {
      setModelError(e.message || 'Model load failed');
      setModelLoaded(false);
    }
    setModelLoading(false);
  }, []);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraActive(true);
      loadModel();
      requestAnimationFrame(drawLoop);
    } catch {
      setCameraActive(false);
    }
  }, [loadModel]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraActive(false);
    setIsDetecting(false);
  }, []);

  const drawLoop = useCallback(() => {
    frameCountRef.current++;
    const now = Date.now();
    if (now - lastTimeRef.current >= 1000) {
      setFrameRate(frameCountRef.current);
      frameCountRef.current = 0;
      lastTimeRef.current = now;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) {
      animRef.current = requestAnimationFrame(drawLoop);
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) { animRef.current = requestAnimationFrame(drawLoop); return; }

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (modelLoaded && detectorRef.current) {
      runPoseDetection(video, ctx);
    } else {
      drawGuideOverlay(ctx, canvas.width, canvas.height);
    }

    animRef.current = requestAnimationFrame(drawLoop);
  }, [modelLoaded]);

  const runPoseDetection = async (video: HTMLVideoElement, ctx: CanvasRenderingContext2D) => {
    try {
      if (lowPowerMode) {
        const now = Date.now();
        if (now - lastDetectionTimeRef.current < 150) {
          // Skip frame processing to save battery, but render helper text
          ctx.fillStyle = 'rgba(16,185,129,0.5)';
          ctx.font = '10px sans-serif';
          ctx.fillText('Low Power Mode: Throttling Tracking (6.6 FPS)', 20, 20);
          return;
        }
        lastDetectionTimeRef.current = now;
      }
      const poses: Pose[] = await detectorRef.current.estimatePoses(video);
      if (poses.length > 0 && poses[0].score > 0.3) {
        setIsDetecting(true);
        const kp = poses[0].keypoints;
        drawSkeleton(ctx, kp);
        analyzeForm(kp);
      } else {
        setIsDetecting(false);
        ctx.fillStyle = 'rgba(255,255,255,0.3)';
        ctx.font = '14px sans-serif';
        ctx.fillText('No pose detected — stand in frame', 20, 30);
      }
    } catch {
      setIsDetecting(false);
    }
  };

  const drawSkeleton = (ctx: CanvasRenderingContext2D, keypoints: Keypoint[]) => {
    const kpMap: Record<string, Keypoint> = {};
    keypoints.forEach(k => {
      const key = k.name?.toLowerCase().replace(/ /g, '_');
      if (key) kpMap[key] = k;
    });

    SKELETON_CONNECTIONS.forEach(([from, to]) => {
      const a = kpMap[from]; const b = kpMap[to];
      if (a && b && a.score > 0.3 && b.score > 0.3) {
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = 'rgba(16,185,129,0.7)'; ctx.lineWidth = 3; ctx.stroke();
      }
    });

    keypoints.forEach(k => {
      if (k.score > 0.3) {
        ctx.beginPath(); ctx.arc(k.x, k.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#10b981'; ctx.fill();
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();
      }
    });
  };

  const drawGuideOverlay = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    ctx.fillStyle = 'rgba(255,255,255,0.06)';
    ctx.font = '11px sans-serif';
    ctx.fillText(`Guide: ${selectedExercise.name}`, 20, 30);
    ctx.fillText(selectedExercise.desc, 20, 48);

    const cx = w / 2, cy = h / 2;
    ctx.strokeStyle = 'rgba(16,185,129,0.2)';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);

    if (selectedExercise.id === 'squat') {
      ctx.beginPath(); ctx.moveTo(cx - 30, cy - 80); ctx.lineTo(cx - 30, cy + 40);
      ctx.lineTo(cx + 50, cy + 40); ctx.lineTo(cx + 50, cy - 80);
      ctx.stroke();
      ctx.beginPath(); ctx.arc(cx + 10, cy + 40, 40, 0, Math.PI);
      ctx.strokeStyle = 'rgba(245,158,11,0.3)'; ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.15)';
      ctx.font = '9px sans-serif'; ctx.fillText('← Keep knees behind toes →', cx - 70, cy + 70);
    } else if (selectedExercise.id === 'pushup') {
      ctx.beginPath(); ctx.moveTo(cx - 60, cy - 80); ctx.lineTo(cx + 60, cy + 80);
      ctx.strokeStyle = 'rgba(239,68,68,0.3)'; ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx - 60, cy + 80); ctx.lineTo(cx + 60, cy - 80);
      ctx.strokeStyle = 'rgba(16,185,129,0.2)'; ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.15)';
      ctx.font = '9px sans-serif'; ctx.fillText('← Keep body straight →', cx - 60, cy + 5);
    } else if (selectedExercise.id === 'plank') {
      ctx.beginPath(); ctx.moveTo(cx - 80, cy - 60); ctx.lineTo(cx + 80, cy - 60);
      ctx.strokeStyle = 'rgba(16,185,129,0.3)'; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.15)';
      ctx.font = '9px sans-serif'; ctx.fillText('← Straight line head to heels →', cx - 80, cy - 40);
    } else if (selectedExercise.id === 'lunge') {
      ctx.beginPath(); ctx.moveTo(cx - 50, cy - 60); ctx.lineTo(cx - 50, cy + 20);
      ctx.lineTo(cx + 50, cy + 20); ctx.lineTo(cx + 50, cy - 60);
      ctx.strokeStyle = 'rgba(245,158,11,0.3)'; ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.15)';
      ctx.font = '9px sans-serif'; ctx.fillText('← Front knee 90° over ankle →', cx - 70, cy + 50);
    } else if (selectedExercise.id === 'curl') {
      ctx.beginPath(); ctx.arc(cx, cy - 30, 40, Math.PI * 1.2, Math.PI * 1.8);
      ctx.strokeStyle = 'rgba(16,185,129,0.3)'; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.15)';
      ctx.font = '9px sans-serif'; ctx.fillText('← Elbows in, full range →', cx - 55, cy + 20);
    }
    ctx.setLineDash([]);
  };

  const analyzeForm = (keypoints: Keypoint[]) => {
    const kpMap: Record<string, Keypoint> = {};
    keypoints.forEach(k => {
      const key = k.name?.toLowerCase().replace(/ /g, '_');
      if (key) kpMap[key] = k;
    });

    const msgs: string[] = [];
    let good = true;

    const leftHip = kpMap['left_hip']; const rightHip = kpMap['right_hip'];
    const leftKnee = kpMap['left_knee']; const rightKnee = kpMap['right_knee'];
    const leftAnkle = kpMap['left_ankle']; const rightAnkle = kpMap['right_ankle'];
    const leftShoulder = kpMap['left_shoulder']; const rightShoulder = kpMap['right_shoulder'];
    const leftElbow = kpMap['left_elbow']; const rightElbow = kpMap['right_elbow'];
    const leftWrist = kpMap['left_wrist']; const rightWrist = kpMap['right_wrist'];

    if (selectedExercise.id === 'squat' && leftHip && leftKnee && leftAnkle) {
      const kneeAngle = angleBetween(leftHip, leftKnee, leftAnkle);
      prevAnglesRef.current.knee = kneeAngle;
      
      // State transition check for rep count
      if (poseStateRef.current === 'up' && kneeAngle < 100) {
        poseStateRef.current = 'down';
      } else if (poseStateRef.current === 'down' && kneeAngle > 145) {
        poseStateRef.current = 'up';
        setRepCount(prev => prev + 1);
      }

      if (kneeAngle > 100) { msgs.push('Go deeper — bend knees more'); good = false; }
      else if (kneeAngle < 70) { msgs.push('Don\'t go too deep — control the range'); good = false; }
      else { msgs.push('Good squat depth!'); }
    }

    if (selectedExercise.id === 'pushup' && leftShoulder && leftElbow && leftWrist) {
      const elbowAngle = angleBetween(leftShoulder, leftElbow, leftWrist);
      prevAnglesRef.current.elbow = elbowAngle;

      // State transition check for rep count
      if (poseStateRef.current === 'up' && elbowAngle < 100) {
        poseStateRef.current = 'down';
      } else if (poseStateRef.current === 'down' && elbowAngle > 140) {
        poseStateRef.current = 'up';
        setRepCount(prev => prev + 1);
      }

      if (elbowAngle > 110) { msgs.push('Go lower — elbows need 90°'); good = false; }
      else if (elbowAngle > 70 && elbowAngle <= 110) { msgs.push('Perfect push-up depth!'); }
      else { msgs.push('Coming back up — good control'); }
    }

    if (selectedExercise.id === 'plank' && leftShoulder && leftHip && leftAnkle) {
      const hipAngle = angleBetween(leftShoulder, leftHip, leftAnkle);
      if (Math.abs(hipAngle - 180) > 15) {
        msgs.push(hipAngle > 180 ? 'Hips too high — lower them' : 'Hips sagging — tighten core');
        good = false;
      } else { msgs.push('Great plank alignment!'); }
    }

    if (selectedExercise.id === 'lunge' && leftHip && leftKnee && leftAnkle && rightHip && rightKnee && rightAnkle) {
      const frontKnee = angleBetween(leftHip, leftKnee, leftAnkle);
      if (frontKnee > 100) { msgs.push('Front knee too shallow — bend deeper'); good = false; }
      else if (frontKnee < 60) { msgs.push('Front knee past toes — adjust stance'); good = false; }
      else { msgs.push('Good lunge position!'); }
    }

    if (selectedExercise.id === 'curl' && leftShoulder && leftElbow && leftWrist) {
      const elbowAngle = angleBetween(leftShoulder, leftElbow, leftWrist);
      prevAnglesRef.current.elbow = elbowAngle;

      // State transition check for rep count
      if (poseStateRef.current === 'up' && elbowAngle < 75) {
        poseStateRef.current = 'down';
      } else if (poseStateRef.current === 'down' && elbowAngle > 140) {
        poseStateRef.current = 'up';
        setRepCount(prev => prev + 1);
      }

      if (elbowAngle > 150) { msgs.push('Full extension — good range'); }
      else if (elbowAngle < 50) { msgs.push('Peak contraction — squeeze!'); }
      else { msgs.push('Controlled movement — keep elbows fixed'); }
    }

    if (msgs.length === 0) msgs.push('Stand in frame to begin analysis');
    setFeedback(msgs);
    setLastFeedback(good ? 'good' : 'bad');
  };


  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className={`w-16 h-16 rounded-3xl flex items-center justify-center transition-colors ${
            cameraActive ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400' : 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-400'
          }`}>
            {cameraActive ? <Camera size={32} /> : <Target size={32} />}
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Form Coach</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
              {cameraActive ? (isDetecting ? 'Pose detected' : 'Waiting for pose') : 'Camera off'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setLowPowerMode(!lowPowerMode)}
            className={`flex items-center space-x-2 px-5 py-3 rounded-2xl font-black text-[10px] uppercase tracking-widest transition ${
              lowPowerMode
                ? 'bg-yellow-500 hover:bg-yellow-400 text-slate-950 shadow-yellow-500/20'
                : 'bg-slate-900 hover:bg-slate-800 text-slate-400 border border-white/5'
            }`}
          >
            <span>{lowPowerMode ? 'Low Power ON' : 'Low Power OFF'}</span>
          </button>
          <button onClick={cameraActive ? stopCamera : startCamera}
            className={`flex items-center space-x-2 px-5 py-3 rounded-2xl font-black text-[10px] uppercase tracking-widest transition ${
              cameraActive
                ? 'bg-rose-500 hover:bg-rose-400 text-slate-950'
                : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950'
            }`}>
            {cameraActive ? <CameraOff size={14} /> : <Camera size={14} />}
            <span>{cameraActive ? 'Stop Camera' : 'Start Camera'}</span>
          </button>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Camera / Canvas */}
        <div className="flex-1 min-w-0">
          <div className={`relative rounded-[2.5rem] overflow-hidden bg-slate-950 border transition-all ${
            cameraActive ? 'border-emerald-500/20' : 'border-white/5'
          }`}>
            <video ref={videoRef} autoPlay playsInline muted className="w-full aspect-video object-cover scale-x-[-1]" />
            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
            {!cameraActive && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80">
                <div className="text-center">
                  <Move size={48} className="mx-auto text-slate-700 mb-4" />
                  <p className="text-lg font-black text-slate-500 uppercase tracking-wider">Camera Off</p>
                  <p className="text-[10px] font-black text-slate-600 mt-2 uppercase tracking-widest">Enable camera for pose analysis</p>
                </div>
              </div>
            )}
            {modelLoading && cameraActive && (
              <div className="absolute top-4 left-4 flex items-center space-x-2 px-3 py-2 bg-slate-950/80 rounded-xl border border-white/10">
                <Loader2 size={12} className="animate-spin text-emerald-400" />
                <span className="text-[8px] text-emerald-400 font-black uppercase tracking-widest">Loading AI model...</span>
              </div>
            )}
            {modelError && cameraActive && (
              <div className="absolute top-4 left-4 flex items-center space-x-2 px-3 py-2 bg-amber-500/10 rounded-xl border border-amber-500/20">
                <AlertTriangle size={12} className="text-amber-400" />
                <span className="text-[7px] text-amber-400 font-black uppercase tracking-widest">Guide overlay mode</span>
              </div>
            )}
            {cameraActive && (
              <div className="absolute bottom-4 right-4 px-2 py-1 bg-slate-950/70 rounded-lg border border-white/5">
                <span className="text-[7px] text-slate-600 font-black">{frameRate} FPS</span>
              </div>
            )}
          </div>
        </div>

        {/* Side panel */}
        <div className="w-72 shrink-0 space-y-4">
          {/* Exercise selector */}
          <div className="glass-panel rounded-[2rem] border border-white/5 p-4 space-y-2">
            <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest mb-3">Exercise</p>
            {EXERCISES.map(ex => (
              <button key={ex.id} onClick={() => { setSelectedExercise(ex); setFeedback([`Selected: ${ex.name}`]); setRepCount(0); }}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-left transition-all border ${
                  selectedExercise.id === ex.id
                    ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-400'
                    : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-400'
                }`}>
                <span className="text-lg">{ex.icon}</span>
                <div>
                  <p className="text-[9px] font-black">{ex.name}</p>
                  <p className="text-[7px] text-slate-600 font-black uppercase tracking-widest">{ex.desc.slice(0, 30)}...</p>
                </div>
              </button>
            ))}
          </div>

          {/* Rep Counter Card */}
          <div className="glass-panel rounded-[2rem] border border-white/5 p-5 text-center bg-gradient-to-br from-slate-900 to-slate-950">
            <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest mb-1">Rep Counter</p>
            <div className="text-5xl font-black text-emerald-400 italic my-2">{repCount}</div>
            <p className="text-[7px] text-slate-400 font-bold uppercase tracking-wider">Completed Reps</p>
          </div>

          {/* Feedback */}
          <div className="glass-panel rounded-[2rem] border border-white/5 p-5 space-y-3">

            <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">Form Feedback</p>
            <div className="space-y-2">
              {feedback.map((msg, i) => (
                <div key={i} className={`flex items-start space-x-2 text-[9px] font-black leading-relaxed ${
                  msg.includes('Good') || msg.includes('Perfect') || msg.includes('Great')
                    ? 'text-emerald-400' : msg.includes('Go lower') || msg.includes('bend more') || msg.includes('too high') || msg.includes('sagging') || msg.includes('too shallow') || msg.includes('past toes')
                    ? 'text-amber-400' : 'text-slate-400'
                }`}>
                  <span className="mt-0.5 shrink-0">
                    {msg.includes('Good') || msg.includes('Perfect') || msg.includes('Great') ? '✓' : '→'}
                  </span>
                  <span>{msg}</span>
                </div>
              ))}
            </div>
            {isDetecting && (
              <div className="flex items-center space-x-2 pt-2 border-t border-white/5">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[7px] text-emerald-500 font-black uppercase tracking-widest">Live</span>
              </div>
            )}
          </div>

          {/* Tips */}
          <div className="glass-panel rounded-[2rem] border border-white/5 p-5">
            <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest mb-2">Tips</p>
            <ul className="space-y-1.5">
              <li className="flex items-start space-x-2 text-[8px] text-slate-600">
                <span className="text-emerald-500 mt-0.5">•</span>
                <span>Stand 2m from camera</span>
              </li>
              <li className="flex items-start space-x-2 text-[8px] text-slate-600">
                <span className="text-emerald-500 mt-0.5">•</span>
                <span>Wear contrasting clothing</span>
              </li>
              <li className="flex items-start space-x-2 text-[8px] text-slate-600">
                <span className="text-emerald-500 mt-0.5">•</span>
                <span>Ensure good lighting</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FormCorrector;
