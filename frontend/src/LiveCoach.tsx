
// Always use import {GoogleGenAI} from "@google/genai";
import { GoogleGenAI, LiveServerMessage, Modality, Type, Blob } from '@google/genai';
import { Activity, BrainCircuit, Camera, CameraOff, CheckCircle2, Info, Loader2, Play, Sparkles, Square, Zap, ShieldAlert, RefreshCw, Settings, Crosshair, Cloud } from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';
import { logBiomechanicalFault } from './api';

// --- ANATOMY MAP (Relative coordinates for HUD projection) ---
const ANATOMY_MAP: Record<string, { x: number; y: number; w: number; h: number }> = {
  spine: { x: 0.45, y: 0.25, w: 0.1, h: 0.45 },
  knees: { x: 0.35, y: 0.65, w: 0.3, h: 0.2 },
  shoulders: { x: 0.3, y: 0.15, w: 0.4, h: 0.15 },
  head: { x: 0.42, y: 0.02, w: 0.16, h: 0.18 },
  core: { x: 0.38, y: 0.4, w: 0.24, h: 0.25 }
};

interface HighlightData {
  status: 'optimal' | 'warning' | 'critical';
  feedback: string;
  lastUpdated: number;
}

// --- HUD Component ---
interface HUDOverlayProps {
  highlights: Record<string, HighlightData>;
}

const HUDOverlay: React.FC<HUDOverlayProps> = ({ highlights }) => {
  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none z-30 select-none" viewBox="0 0 100 100" preserveAspectRatio="none">
      <defs>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="0.8" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <linearGradient id="scanGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="white" stopOpacity="0" />
          <stop offset="50%" stopColor="white" stopOpacity="0.4" />
          <stop offset="100%" stopColor="white" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Aesthetic HUD Grids */}
      <line x1="50" y1="0" x2="50" y2="100" stroke="rgba(16,185,129,0.15)" strokeWidth="0.05" />
      <line x1="0" y1="50" x2="100" y2="50" stroke="rgba(16,185,129,0.15)" strokeWidth="0.05" />
      <circle cx="50" cy="50" r="40" stroke="rgba(16,185,129,0.1)" fill="none" strokeWidth="0.05" strokeDasharray="1 2" />

      {Object.entries(highlights).map(([part, data]) => {
        const box = ANATOMY_MAP[part];
        if (!box) return null;

        const color = data.status === 'optimal' ? '#10b981' : data.status === 'warning' ? '#f59e0b' : '#f43f5e';
        const x = box.x * 100;
        const y = box.y * 100;
        const w = box.w * 100;
        const h = box.h * 100;

        return (
          <g key={part} className="animate-in fade-in zoom-in duration-500">
            {/* Animated Bounding Box */}
            <rect 
              x={x} y={y} width={w} height={h} 
              fill={`${color}08`} 
              stroke={color} 
              strokeWidth="0.4" 
              strokeDasharray="2 1"
              filter="url(#glow)"
              className="animate-pulse"
            />
            
            {/* Tactical Corners */}
            <path d={`M ${x} ${y + 4} L ${x} ${y} L ${x + 4} ${y}`} stroke={color} strokeWidth="0.8" fill="none" />
            <path d={`M ${x + w - 4} ${y} L ${x + w} ${y} L ${x + w} ${y + 4}`} stroke={color} strokeWidth="0.8" fill="none" />
            <path d={`M ${x} ${y + h - 4} L ${x} ${y + h} L ${x + 4} ${y + h}`} stroke={color} strokeWidth="0.8" fill="none" />
            <path d={`M ${x + w - 4} ${y + h} L ${x + w} ${y + h} L ${x + w} ${y + h - 4}`} stroke={color} strokeWidth="0.8" fill="none" />

            {/* Vertically Moving Scanline */}
            <rect x={x} y={y} width={w} height="1.5" fill="url(#scanGradient)" className="animate-scan" style={{ animationDuration: '2s' }} />

            {/* Label HUD Element */}
            <g transform={`translate(${x}, ${y - 2})`}>
              <rect x="-0.5" y="-5" width={part.length * 3 + 12} height="5.5" fill="rgba(2,6,23,0.9)" rx="1.5" stroke={color} strokeWidth="0.1" />
              <text 
                x="1.5" y="-1.2"
                fill={color} 
                fontSize="3.2" 
                fontWeight="900" 
                className="uppercase tracking-[0.2em]"
                style={{ fontFamily: 'Space Grotesk' }}
              >
                {part}: {data.status}
              </text>
            </g>

            {/* Floating Feedback Panel */}
            <foreignObject x={x + w + 1.5} y={y} width="35" height="25">
              <div className="p-3 rounded-xl backdrop-blur-xl border-l-4 bg-slate-950/90 shadow-2xl" style={{ borderColor: color }}>
                 <p className="text-[8px] font-black text-white uppercase tracking-tighter mb-1 opacity-50">Diagnostic:</p>
                 <p className="text-[10px] font-bold text-slate-100 italic leading-tight">
                   {data.feedback}
                 </p>
              </div>
            </foreignObject>
          </g>
        );
      })}
    </svg>
  );
};

// --- Utilities ---
function decode(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

function encode(bytes: Uint8Array) {
  let binary = '';
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

async function decodeAudioData(
  data: Uint8Array,
  ctx: AudioContext,
  sampleRate: number,
  numChannels: number,
): Promise<AudioBuffer> {
  const dataInt16 = new Int16Array(data.buffer);
  const frameCount = dataInt16.length / numChannels;
  const buffer = ctx.createBuffer(numChannels, frameCount, sampleRate);

  for (let channel = 0; channel < numChannels; channel++) {
    const channelData = buffer.getChannelData(channel);
    for (let i = 0; i < frameCount; i++) {
      channelData[i] = dataInt16[i * numChannels + channel] / 32768.0;
    }
  }
  return buffer;
}

const LiveCoach: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [hasCamera, setHasCamera] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [transcription, setTranscription] = useState('Neural core ready for link...');
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  
  const [highlights, setHighlights] = useState<Record<string, HighlightData>>({});

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sessionPromiseRef = useRef<Promise<any> | null>(null);
  const frameIntervalRef = useRef<number | null>(null);
  
  const inputAudioContextRef = useRef<AudioContext | null>(null);
  const outputAudioContextRef = useRef<AudioContext | null>(null);
  const nextStartTimeRef = useRef<number>(0);
  const audioSourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);

  // Auto-expire highlights
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setHighlights(prev => {
        const next = { ...prev };
        let changed = false;
        for (const part in next) {
          if (now - next[part].lastUpdated > 7000) {
            delete next[part];
            changed = true;
          }
        }
        return changed ? next : prev;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleCamera = async () => {
    setPermissionDenied(false);
    if (hasCamera) {
      stopCamera();
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: true });
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setHasCamera(true);
      } catch (err: any) {
        console.error("Camera access failed:", err);
        setPermissionDenied(true);
      }
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setHasCamera(false);
  };

  const startSession = async () => {
    if (!hasCamera) return;
    setLoading(true);
    setIsActive(true);
    setTranscription('SYNCHRONIZING NEURAL UPLINK...');

    inputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({sampleRate: 16000});
    outputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({sampleRate: 24000});

    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

    const sessionPromise = ai.live.connect({
      model: 'gemini-2.5-flash-native-audio-preview-12-2025',
      callbacks: {
        onopen: () => {
          setLoading(false);
          setTranscription('NEURAL LINK SECURED. MONITORING BIOMECHANICS.');
          
          if (streamRef.current) {
            const source = inputAudioContextRef.current!.createMediaStreamSource(streamRef.current);
            scriptProcessorRef.current = inputAudioContextRef.current!.createScriptProcessor(4096, 1, 1);
            
            scriptProcessorRef.current.onaudioprocess = (e) => {
              const inputData = e.inputBuffer.getChannelData(0);
              const pcmBlob = createBlob(inputData);
              sessionPromise.then((session) => {
                session.sendRealtimeInput({ media: pcmBlob });
              });
            };
            source.connect(scriptProcessorRef.current);
            scriptProcessorRef.current.connect(inputAudioContextRef.current!.destination);
          }

          if (videoRef.current && canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            frameIntervalRef.current = window.setInterval(() => {
              if (videoRef.current && canvasRef.current && ctx && videoRef.current.readyState >= 2) {
                canvasRef.current.width = 640;
                canvasRef.current.height = 360;
                ctx.drawImage(videoRef.current, 0, 0, 640, 360);
                canvasRef.current.toBlob((blob) => {
                  if (blob) {
                    const reader = new FileReader();
                    reader.onloadend = () => {
                      const base64Data = (reader.result as string).split(',')[1];
                      sessionPromise.then((session) => {
                        session.sendRealtimeInput({
                          media: { data: base64Data, mimeType: 'image/jpeg' }
                        });
                      });
                    };
                    reader.readAsDataURL(blob);
                  }
                }, 'image/jpeg', 0.5);
              }
            }, 1000);
          }
        },
        onmessage: async (message: LiveServerMessage) => {
          if (message.serverContent?.modelTurn) {
            const audioData = message.serverContent.modelTurn.parts[0]?.inlineData?.data;
            if (audioData && outputAudioContextRef.current) {
              const audioBuffer = await decodeAudioData(
                decode(audioData),
                outputAudioContextRef.current,
                24000,
                1
              );
              const source = outputAudioContextRef.current.createBufferSource();
              source.buffer = audioBuffer;
              source.connect(outputAudioContextRef.current.destination);
              
              nextStartTimeRef.current = Math.max(nextStartTimeRef.current, outputAudioContextRef.current.currentTime);
              source.start(nextStartTimeRef.current);
              nextStartTimeRef.current += audioBuffer.duration;
              audioSourcesRef.current.add(source);
              source.onended = () => audioSourcesRef.current.delete(source);
            }
          }

          if (message.toolCall) {
            for (const fc of message.toolCall.functionCalls) {
              if (fc.name === 'updateAnatomyHighlight') {
                const args = fc.args as any;
                setHighlights(prev => ({
                  ...prev,
                  [args.part]: {
                    status: args.status,
                    feedback: args.feedback,
                    lastUpdated: Date.now()
                  }
                }));

                // Persistence logic to Neural Core
                if (args.status !== 'optimal') {
                  setSyncing(true);
                  logBiomechanicalFault({
                    part: args.part,
                    status: args.status,
                    feedback: args.feedback
                  }).finally(() => {
                    setTimeout(() => setSyncing(false), 2000);
                  });
                }

                sessionPromise.then(s => s.sendToolResponse({
                  functionResponses: [{ id: fc.id, name: fc.name, response: { result: "HUD LAYER UPDATED & PERSISTED" } }]
                }));
              }
            }
          }

          if (message.serverContent?.interrupted) {
            audioSourcesRef.current.forEach(s => s.stop());
            audioSourcesRef.current.clear();
            nextStartTimeRef.current = 0;
          }
        },
        onerror: (e) => {
          console.error(e);
          setTranscription('LINK FAILURE. RE-ESTABLISHING...');
        },
        onclose: () => stopSession()
      },
      config: {
        responseModalities: [Modality.AUDIO],
        speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } } },
        systemInstruction: `You are the Smarty AI Neural Form Analyst. 
        Analyze the user's biomechanics via the live camera feed. 
        When you identify form errors (e.g., knee collapse, back rounding) or perfect form, use the 'updateAnatomyHighlight' tool to tag body parts.
        Available parts: spine, knees, shoulders, head, core.
        Provide professional, data-driven, and supportive voice feedback.`,
        tools: [{
          functionDeclarations: [{
            name: 'updateAnatomyHighlight',
            description: 'Triggers a tactical HUD highlight on a specific body part for visual form feedback.',
            parameters: {
              type: Type.OBJECT,
              properties: {
                part: { type: Type.STRING, enum: ['spine', 'knees', 'shoulders', 'head', 'core'] },
                status: { type: Type.STRING, enum: ['optimal', 'warning', 'critical'] },
                feedback: { type: Type.STRING, description: 'Brief corrective cue' }
              },
              required: ['part', 'status', 'feedback']
            }
          }]
        }]
      }
    });

    sessionPromiseRef.current = sessionPromise;
  };

  const stopSession = () => {
    setIsActive(false);
    setLoading(false);
    setTranscription('Uplink terminated.');
    
    if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
    if (scriptProcessorRef.current) scriptProcessorRef.current.disconnect();
    if (inputAudioContextRef.current) inputAudioContextRef.current.close();
    if (outputAudioContextRef.current) outputAudioContextRef.current.close();
    
    sessionPromiseRef.current?.then((s: any) => s.close());
    sessionPromiseRef.current = null;
    audioSourcesRef.current.forEach(s => s.stop());
    audioSourcesRef.current.clear();
    setHighlights({});
  };

  function createBlob(data: Float32Array): Blob {
    const l = data.length;
    const int16 = new Int16Array(l);
    for (let i = 0; i < l; i++) {
      int16[i] = data[i] * 32768;
    }
    return {
      data: encode(new Uint8Array(int16.buffer)),
      mimeType: 'audio/pcm;rate=16000',
    };
  }

  return (
    <div className="max-w-7xl mx-auto space-y-10 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center justify-center text-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.2)]">
            <Activity size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white">NEURAL VISION HUB</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.4em] text-emerald-500/80">Active Biomechanical Analysis System</p>
          </div>
        </div>
        <div className="flex space-x-4">
          <button 
            onClick={toggleCamera}
            className={`px-8 py-4 rounded-2xl flex items-center space-x-3 transition-all font-black text-[10px] uppercase tracking-widest border ${
              hasCamera ? 'bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20' : 'bg-emerald-500 text-slate-950 shadow-xl shadow-emerald-500/20 hover:scale-105'
            }`}
          >
            {hasCamera ? <CameraOff size={18} /> : <Camera size={18} />}
            <span>{hasCamera ? 'Offline Sensor' : 'Online Sensor'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        <div className="lg:col-span-8 relative rounded-[3.5rem] overflow-hidden bg-slate-950 border border-white/10 aspect-video group shadow-2xl">
          {permissionDenied ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center space-y-6 bg-slate-900/80 backdrop-blur-3xl z-50">
              <ShieldAlert size={64} className="text-rose-500 animate-bounce" />
              <div className="text-center space-y-3 px-10">
                <h3 className="text-2xl font-black italic text-white uppercase tracking-tighter">Sensor Authorization Denied</h3>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-relaxed max-w-sm mx-auto">
                  Neural link requires optical access. Update browser permissions in site settings to re-initialize the link.
                </p>
              </div>
              <div className="flex space-x-4">
                <button 
                  onClick={toggleCamera}
                  className="bg-emerald-500 text-slate-950 px-8 py-3 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] shadow-lg shadow-emerald-500/20 hover:scale-105 transition-all"
                >
                  <RefreshCw size={14} className="inline mr-2" /> Retry Link
                </button>
              </div>
            </div>
          ) : !hasCamera ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center space-y-6">
              <div className="w-24 h-24 bg-slate-900 rounded-[2rem] flex items-center justify-center text-slate-800 animate-pulse border border-white/5">
                <Crosshair size={48} />
              </div>
              <p className="text-[10px] font-black text-slate-600 uppercase tracking-[0.5em]">Optical Input: Pending Initialization</p>
            </div>
          ) : (
            <>
              <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover grayscale opacity-40 transition-all group-hover:grayscale-0 group-hover:opacity-70" />
              <canvas ref={canvasRef} className="hidden" />
              <HUDOverlay highlights={highlights} />
              
              <div className="absolute top-10 left-10 flex flex-col space-y-4 z-40">
                <div className="flex items-center space-x-3 bg-slate-950/80 backdrop-blur-xl px-5 py-2.5 rounded-2xl border border-emerald-500/30">
                   <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></div>
                   <span className="text-[9px] font-black text-emerald-400 uppercase tracking-[0.2em]">Kinetic Scan: Active</span>
                </div>
                {syncing && (
                  <div className="flex items-center space-x-3 bg-cyan-500/20 backdrop-blur-xl px-5 py-2.5 rounded-2xl border border-cyan-500/30 animate-in fade-in zoom-in duration-300">
                    <Cloud size={14} className="text-cyan-400 animate-pulse" />
                    <span className="text-[9px] font-black text-cyan-400 uppercase tracking-[0.2em]">Neural Core Synced</span>
                  </div>
                )}
                {Object.keys(highlights).some(k => highlights[k].status !== 'optimal') && (
                   <div className="flex items-center space-x-3 bg-rose-500/20 backdrop-blur-xl px-5 py-2.5 rounded-2xl border border-rose-500/30 animate-pulse">
                      <span className="text-[9px] font-black text-rose-400 uppercase tracking-[0.2em]">Bio-Fault Detected</span>
                   </div>
                )}
              </div>
            </>
          )}
        </div>

        <div className="lg:col-span-4 space-y-8 flex flex-col">
          <div className="glass-panel p-10 rounded-[3rem] border border-white/5 space-y-8 relative overflow-hidden flex-1 flex flex-col justify-between">
            <div className="space-y-8">
              <div className="flex items-center space-x-4">
                <div className="w-14 h-14 bg-emerald-500/10 rounded-2xl flex items-center justify-center text-emerald-500 border border-emerald-500/20 shadow-inner">
                  <BrainCircuit size={28} />
                </div>
                <div>
                  <h4 className="text-xl font-black text-white uppercase italic tracking-tighter leading-none">NEURAL ORACLE</h4>
                  <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Live Subconscious Logic Stream</p>
                </div>
              </div>

              <div className="p-8 bg-slate-950/80 rounded-[2rem] border border-white/5 min-h-[220px] flex items-center justify-center relative">
                <div className="absolute inset-0 opacity-5 pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle, #10b981 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
                {loading ? (
                  <div className="flex flex-col items-center justify-center space-y-5">
                    <div className="relative">
                      <Loader2 className="animate-spin text-emerald-500" size={48} />
                      <Sparkles className="absolute -top-1 -right-1 text-emerald-400 animate-pulse" size={16} />
                    </div>
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em] animate-pulse">Syncing Neurons...</p>
                  </div>
                ) : (
                  <p className="text-sm text-slate-100 leading-relaxed font-bold italic text-center px-4">
                    "{transcription}"
                  </p>
                )}
              </div>
            </div>

            <button 
              onClick={isActive ? stopSession : startSession}
              disabled={!hasCamera || loading || permissionDenied}
              className={`w-full py-7 rounded-[2rem] transition-all flex items-center justify-center space-x-4 font-black uppercase tracking-[0.25em] text-[10px] group relative overflow-hidden ${
                isActive 
                  ? 'bg-rose-500/10 border border-rose-500/20 text-rose-500 hover:bg-rose-500/20' 
                  : 'bg-emerald-500 text-slate-950 shadow-2xl shadow-emerald-500/30 hover:scale-[1.02] active:scale-95 disabled:bg-slate-800 disabled:text-slate-600 disabled:shadow-none'
              }`}
            >
              {isActive ? <Square size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
              <span>{isActive ? 'Disconnect Uplink' : 'Activate Live Link'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveCoach;
