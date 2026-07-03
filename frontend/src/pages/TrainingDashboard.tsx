import React, { useState, useEffect } from 'react';
import { Brain, Activity, Target, Users, RefreshCw, Server, HardDrive, Zap, Loader2, CheckCircle2, XCircle, Clock, BarChart3, TrendingUp, Layers, GitBranch } from 'lucide-react';
import { TrainingAPI, TrainingStatus } from '../services/apiService';
import { Reveal } from '../components/Reveal';

interface ModelCard {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  bgClass: string;
  borderClass: string;
  textClass: string;
  endpoint: string;
  trained: boolean;
  sizeKb: number;
  metrics: string;
  trainAction: () => Promise<any>;
}

const TrainingDashboard: React.FC = () => {
  const [status, setStatus] = useState<TrainingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [trainingIds, setTrainingIds] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<Record<string, any>>({});
  const [error, setError] = useState('');

  const fetchStatus = async () => {
    try {
      const s = await TrainingAPI.getStatus();
      setStatus(s);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStatus(); }, []);

  const models: ModelCard[] = [
    {
      id: 'recommendation', label: 'Recommendation NN',
      icon: <Brain size={22} />, color: 'emerald',
      bgClass: 'bg-emerald-500/10', borderClass: 'border-emerald-500/20', textClass: 'text-emerald-400',
      endpoint: 'recommendation',
      trained: status?.trained_models?.some(m => m.name === 'model') ?? false,
      sizeKb: status?.trained_models?.find(m => m.name === 'model')?.size_kb ?? 0,
      metrics: 'Binary classifier — good/bad meal prediction',
      trainAction: async () => TrainingAPI.trainRecommendation(50),
    },
    {
      id: 'detector', label: 'YOLO Food Detector',
      icon: <Target size={22} />, color: 'orange',
      bgClass: 'bg-orange-500/10', borderClass: 'border-orange-500/20', textClass: 'text-orange-400',
      endpoint: 'detector',
      trained: status?.trained_models?.some(m => m.name === 'yolov8_food') ?? false,
      sizeKb: status?.trained_models?.find(m => m.name === 'yolov8_food')?.size_kb ?? 0,
      metrics: 'Object detection — mAP50, mAP50-95',
      trainAction: async () => TrainingAPI.trainDetector(undefined, 50),
    },
    {
      id: 'classifier', label: 'Health Classifier',
      icon: <Activity size={22} />, color: 'purple',
      bgClass: 'bg-purple-500/10', borderClass: 'border-purple-500/20', textClass: 'text-purple-400',
      endpoint: 'classifier',
      trained: status?.trained_models?.some(m => m.name === 'resnet50_food_health') ?? false,
      sizeKb: status?.trained_models?.find(m => m.name === 'resnet50_food_health')?.size_kb ?? 0,
      metrics: 'ResNet50 — healthy vs unhealthy food',
      trainAction: async () => TrainingAPI.trainClassifier(undefined, 30),
    },
    {
      id: 'clusters', label: 'User Clusters',
      icon: <Users size={22} />, color: 'cyan',
      bgClass: 'bg-cyan-500/10', borderClass: 'border-cyan-500/20', textClass: 'text-cyan-400',
      endpoint: 'clusters',
      trained: status?.trained_models?.some(m => m.name === 'kmeans') ?? false,
      sizeKb: status?.trained_models?.find(m => m.name === 'kmeans')?.size_kb ?? 0,
      metrics: 'K-means/GMM — user archetypes',
      trainAction: async () => TrainingAPI.clusterUsers(undefined, 'kmeans'),
    },
    {
      id: 'lstm', label: 'LSTM Weight Predictor',
      icon: <TrendingUp size={22} />, color: 'rose',
      bgClass: 'bg-rose-500/10', borderClass: 'border-rose-500/20', textClass: 'text-rose-400',
      endpoint: 'lstm',
      trained: status?.trained_models?.some(m => m.name === 'lstm_weight') ?? false,
      sizeKb: status?.trained_models?.find(m => m.name === 'lstm_weight')?.size_kb ?? 0,
      metrics: 'Time-series forecasting — weight trends',
      trainAction: async () => TrainingAPI.trainLSTM(100),
    },
    {
      id: 'dqn', label: 'DQN Meal Sequencer',
      icon: <Layers size={22} />, color: 'amber',
      bgClass: 'bg-amber-500/10', borderClass: 'border-amber-500/20', textClass: 'text-amber-400',
      endpoint: 'dqn',
      trained: status?.trained_models?.some(m => m.name === 'dqn_meal') ?? false,
      sizeKb: status?.trained_models?.find(m => m.name === 'dqn_meal')?.size_kb ?? 0,
      metrics: 'Deep RL — optimal meal sequencing',
      trainAction: async () => TrainingAPI.trainDQN(500),
    },
    {
      id: 'qlearning', label: 'Q-Learning Habit Former',
      icon: <GitBranch size={22} />, color: 'violet',
      bgClass: 'bg-violet-500/10', borderClass: 'border-violet-500/20', textClass: 'text-violet-400',
      endpoint: 'qlearning',
      trained: status?.trained_models?.some(m => m.name === 'qlearning_habits') ?? false,
      sizeKb: status?.trained_models?.find(m => m.name === 'qlearning_habits')?.size_kb ?? 0,
      metrics: 'Tabular RL — habit formation strategy',
      trainAction: async () => TrainingAPI.trainQLearning(1000),
    },
  ];

  const handleTrain = async (model: ModelCard) => {
    setTrainingIds(prev => new Set(prev).add(model.id));
    setResults(prev => ({ ...prev, [model.id]: null }));
    try {
      const result = await model.trainAction();
      setResults(prev => ({ ...prev, [model.id]: result }));
    } catch (err: any) {
      setResults(prev => ({ ...prev, [model.id]: { status: 'error', message: err.message } }));
    } finally {
      setTrainingIds(prev => { const next = new Set(prev); next.delete(model.id); return next; });
      fetchStatus();
    }
  };

  const isTraining = (id: string) => trainingIds.has(id);
  const getResult = (id: string) => results[id];

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <Reveal>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 rounded-3xl flex items-center justify-center text-indigo-400">
              <Brain size={32} />
            </div>
            <div>
              <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Training Pipeline</h2>
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Manage datasets, train models, track performance</p>
            </div>
          </div>
          <button onClick={fetchStatus} disabled={loading}
            className="flex items-center space-x-2 px-5 py-3 bg-white/5 border border-white/10 rounded-2xl text-slate-400 font-black text-[10px] uppercase tracking-widest hover:bg-white/10 transition">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </Reveal>

      {error && (
        <div className="p-5 bg-rose-500/10 border border-rose-500/20 rounded-2xl">
          <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Backend offline — showing estimates</p>
          <p className="text-xs text-slate-500 mt-1">{error}</p>
        </div>
      )}

      {/* Stats row */}
      <Reveal delay={100}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <Server size={16} className="text-indigo-400 mb-2" />
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Datasets</p>
            <p className="text-2xl font-black text-white mt-1">{status?.datasets?.total_datasets ?? 0}</p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <HardDrive size={16} className="text-emerald-400 mb-2" />
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Total Samples</p>
            <p className="text-2xl font-black text-emerald-400 mt-1">{status?.datasets?.total_samples?.toLocaleString() ?? 0}</p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <BarChart3 size={16} className="text-amber-400 mb-2" />
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Trained Models</p>
            <p className="text-2xl font-black text-amber-400 mt-1">{status?.trained_models?.length ?? 0}</p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <Zap size={16} className="text-cyan-400 mb-2" />
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Pipeline</p>
            <p className="text-2xl font-black text-cyan-400 mt-1">
              {status?.trained_models?.length ? `${Math.round(status.trained_models.reduce((s, m) => s + m.size_kb, 0))} KB` : 'Empty'}
            </p>
          </div>
        </div>
      </Reveal>

      {/* Model cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {models.map((model, i) => {
          const training = isTraining(model.id);
          const result = getResult(model.id);
          const resultStatus = result?.status || (model.trained ? 'trained' : 'untrained');
          return (
            <Reveal key={model.id} delay={100 + i * 80}>
              <div className={`glass-panel p-6 rounded-[2.5rem] border transition-all ${training ? 'border-indigo-500/30' : 'border-white/5 hover:border-white/10'}`}>
                <div className="flex items-start justify-between mb-5">
                  <div className="flex items-center space-x-4">
                    <div className={`w-12 h-12 ${model.bgClass} border ${model.borderClass} rounded-2xl flex items-center justify-center ${model.textClass}`}>
                      {model.icon}
                    </div>
                    <div>
                      <p className="text-sm font-black text-white">{model.label}</p>
                      <p className="text-[9px] text-slate-500 mt-0.5">{model.metrics}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {training && <Loader2 size={16} className="animate-spin text-indigo-400" />}
                    {resultStatus === 'success' && <CheckCircle2 size={16} className="text-emerald-400" />}
                    {resultStatus === 'error' && <XCircle size={16} className="text-rose-400" />}
                    {model.trained && !training && !result && <CheckCircle2 size={16} className="text-emerald-400/50" />}
                  </div>
                </div>

                <div className="flex items-center space-x-4 text-[9px] font-black text-slate-600 uppercase tracking-widest mb-5">
                  <span className="flex items-center space-x-1"><HardDrive size={12} /><span>{model.sizeKb > 0 ? `${model.sizeKb.toFixed(1)} KB` : 'No weights'}</span></span>
                  <span className="flex items-center space-x-1"><Clock size={12} /><span>{model.trained ? 'Trained' : 'Untrained'}</span></span>
                </div>

                <button onClick={() => handleTrain(model)} disabled={training}
                  className={`w-full py-3.5 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all flex items-center justify-center space-x-2 ${
                    training
                      ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                      : {
                          emerald: 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 border border-emerald-500/20',
                          orange: 'bg-orange-500 hover:bg-orange-400 text-slate-950 border border-orange-500/20',
                          purple: 'bg-purple-500 hover:bg-purple-400 text-slate-950 border border-purple-500/20',
                          cyan: 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 border border-cyan-500/20',
                        }[model.color]
                  }`}>
                  {training ? <><Loader2 size={14} className="animate-spin" /><span>Training...</span></> : <><Zap size={14} /><span>Train Model</span></>}
                </button>

                {result && result.status === 'success' && (
                  <div className="mt-4 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl">
                    <p className="text-[9px] font-black text-emerald-400 uppercase tracking-widest mb-2">Training Complete</p>
                    <div className="grid grid-cols-2 gap-2 text-[10px]">
                      {Object.entries(result).filter(([k]) => !['status', 'model_path', 'note'].includes(k)).map(([k, v]) => (
                        <div key={k} className="flex justify-between text-slate-400">
                          <span className="text-slate-600">{k.replace(/_/g, ' ')}</span>
                          <span className="font-black text-white">{typeof v === 'number' ? (v as number).toFixed(3) : String(v)}</span>
                        </div>
                      ))}
                    </div>
                    {result.model_path && <p className="text-[8px] text-slate-600 mt-2 truncate">Model: {result.model_path}</p>}
                  </div>
                )}

                {result && result.status === 'error' && (
                  <div className="mt-4 p-4 bg-rose-500/5 border border-rose-500/20 rounded-2xl">
                    <p className="text-[9px] font-black text-rose-400 uppercase tracking-widest">{result.message || 'Training failed'}</p>
                  </div>
                )}
              </div>
            </Reveal>
          );
        })}
      </div>

      {/* Datasets */}
      {status?.datasets?.datasets && status.datasets.datasets.length > 0 && (
        <Reveal delay={400}>
          <div className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
            <div className="p-6 border-b border-white/5">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Registered Datasets</p>
            </div>
            <div className="divide-y divide-white/5">
              {status.datasets.datasets.map((name: string) => (
                <div key={name} className="flex items-center justify-between p-5 hover:bg-white/[0.02] transition-colors">
                  <div className="flex items-center space-x-4">
                    <HardDrive size={16} className="text-slate-600" />
                    <p className="text-sm font-black text-white">{name}</p>
                  </div>
                  <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Registered</span>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      )}
    </div>
  );
};

export default TrainingDashboard;
